# mlflow/train_model.py
import os, json, time
import pandas as pd
import numpy as np
import mlflow
import mlflow.sklearn
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import (
    accuracy_score,
    roc_auc_score,
    precision_score,
    recall_score,
    f1_score,
)
import redis

TRACKING_URI = os.getenv("MLFLOW_TRACKING_URI", "http://mlflow:5000")
os.environ.setdefault("MLFLOW_TRACKING_URI", TRACKING_URI)
# MinIO as artifact store
os.environ.setdefault("AWS_ACCESS_KEY_ID", os.getenv("AWS_ACCESS_KEY_ID", "minioadmin"))
os.environ.setdefault(
    "AWS_SECRET_ACCESS_KEY", os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
)
os.environ.setdefault(
    "MLFLOW_S3_ENDPOINT_URL", os.getenv("MLFLOW_S3_ENDPOINT_URL", "http://minio:9000")
)

TRAIN_PARQUET = os.getenv("TRAIN_PARQUET", "s3://features/train/events/")
TEST_PARQUET = os.getenv("TEST_PARQUET", "s3://raw/movielens/test/")  # labels only
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
MODEL_NAME = os.getenv("MODEL_NAME", "mlsd_hw3_model")

FEATURE_COLS = ["prev_count", "prev_avg", "prev_std", "recency"]


def read_parquet_df(path: str) -> pd.DataFrame:
    """
    Read Parquet from MinIO via s3fs/pyarrow with explicit endpoint and path-style addressing.
    """
    endpoint = os.getenv(
        "MLFLOW_S3_ENDPOINT_URL", "http://minio:9000"
    )  # мы уже так настраивали
    key = os.getenv("AWS_ACCESS_KEY_ID", "minioadmin")
    secret = os.getenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
    # s3fs storage_options → boto3 client
    storage_options = {
        "key": key,
        "secret": secret,
        "anon": False,
        "client_kwargs": {"endpoint_url": endpoint},
        # адресация как в spark.s3a.path.style.access=true
        "config_kwargs": {"s3": {"addressing_style": "path"}},
    }
    return pd.read_parquet(path, engine="pyarrow", storage_options=storage_options)


def load_train() -> tuple[pd.DataFrame, pd.Series]:
    df = read_parquet_df(TRAIN_PARQUET)
    df = df.dropna(subset=["label"]) if "label" in df.columns else df
    frac = float(os.getenv("TRAIN_SAMPLE_FRACTION", "1.0"))
    if frac < 1.0:
        # Deterministic sample by user_id hash to keep distribution stable
        import numpy as np

        mask_sample = (
            pd.util.hash_pandas_object(df["user_id"], index=False).astype("uint64")
            % 10_000
        ) < int(10_000 * frac)
        df = df[mask_sample]

    X = df[FEATURE_COLS].fillna(0.0).astype(float)
    y = df["label"].astype(int)
    # Drop cold-start rows with prev_count==0 from training to avoid degenerate examples (optional)
    mask = X["prev_count"] > 0
    return X[mask], y[mask]


def load_test_labels() -> pd.DataFrame:
    return (
        read_parquet_df(TEST_PARQUET)[["user_id", "label"]]
        if "label" in read_parquet_df(TEST_PARQUET).columns
        else read_parquet_df("s3://features/test/events/")[["user_id", "label"]]
    )


def load_test_features_from_redis() -> pd.DataFrame:
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)

    # 1) пробуем несколько распространённых паттернов ключей
    patterns = os.getenv(
        "REDIS_TEST_KEYS_PATTERNS", "mlsd:test:user:*,mlsd_hw3:test:user:*"
    ).split(",")

    rows = []
    for pattern in [p.strip() for p in patterns if p.strip()]:
        for k in r.scan_iter(match=pattern, count=5000):
            try:
                uid = int(k.split(":")[-1])
            except Exception:
                continue
            payload = r.get(k)
            if not payload:
                continue
            try:
                obj = json.loads(payload)
            except Exception:
                continue
            rows.append(
                {"user_id": uid, **{c: obj.get(c, np.nan) for c in FEATURE_COLS}}
            )

    if rows:
        df = pd.DataFrame(rows)
        df["__source"] = "redis"
        return df

    # 2) если из Redis ничего не нашли — НЕ падаем, а возвращаем fallback
    print(
        f"[WARN] No Redis features found with patterns {patterns} on {REDIS_HOST}:{REDIS_PORT}. "
        "Falling back to parquet features for test metrics."
    )
    try:
        df_fallback = read_parquet_df("s3://features/test/events/")[
            ["user_id"] + FEATURE_COLS
        ]
        df_fallback = df_fallback.drop_duplicates(subset=["user_id"]).reset_index(
            drop=True
        )
        df_fallback["__source"] = "parquet_fallback"
        return df_fallback
    except Exception as e:
        print("[ERROR] Parquet fallback for test features failed:", e)
        # Возвращаем пустой DF с нужными колонками — чтобы код ниже не падал
        return pd.DataFrame(columns=["user_id"] + FEATURE_COLS)


def train_and_log():
    mlflow.set_tracking_uri(TRACKING_URI)
    mlflow.set_experiment("mlsd_hw3")

    X_train, y_train = load_train()
    # Simple LR pipeline
    pipe = Pipeline(
        [
            ("scaler", StandardScaler(with_mean=True, with_std=True)),
            (
                "clf",
                LogisticRegression(
                    solver="saga", max_iter=2000, n_jobs=-1, random_state=42
                ),
            ),
        ]
    )

    with mlflow.start_run(run_name="lr_baseline"):
        pipe.fit(X_train, y_train)

        # Predictions on train
        p_train = pipe.predict_proba(X_train)[:, 1]
        y_pred_train = (p_train >= 0.5).astype(int)
        metrics_train = {
            "accuracy_train": float(accuracy_score(y_train, y_pred_train)),
            "roc_auc_train": float(roc_auc_score(y_train, p_train)),
            "precision_train": float(
                precision_score(y_train, y_pred_train, zero_division=0)
            ),
            "recall_train": float(recall_score(y_train, y_pred_train, zero_division=0)),
            "f1_train": float(f1_score(y_train, y_pred_train, zero_division=0)),
        }
        mlflow.log_metrics(metrics_train)

        # Test: features from Redis + labels from parquet
        X_test = load_test_features_from_redis()
        y_test_df = read_parquet_df("s3://features/test/events/")[["user_id", "label"]]
        df_eval = X_test.merge(y_test_df, on="user_id", how="inner")
        X_eval = df_eval[FEATURE_COLS].fillna(0.0).astype(float)
        y_eval = df_eval["label"].astype(int)

        if len(X_eval) > 0:
            p_test = pipe.predict_proba(X_eval)[:, 1]
            y_pred_test = (p_test >= 0.5).astype(int)
            metrics_test = {
                "accuracy_test": float(accuracy_score(y_eval, y_pred_test)),
                "roc_auc_test": float(roc_auc_score(y_eval, p_test)),
                "precision_test": float(
                    precision_score(y_eval, y_pred_test, zero_division=0)
                ),
                "recall_test": float(
                    recall_score(y_eval, y_pred_test, zero_division=0)
                ),
                "f1_test": float(f1_score(y_eval, y_pred_test, zero_division=0)),
            }
            mlflow.log_metrics(metrics_test)

        # Log model
        mlflow.sklearn.log_model(
            sk_model=pipe,
            artifact_path="model",
            registered_model_name=MODEL_NAME,
            input_example=X_train.head(5),
            signature=mlflow.models.infer_signature(
                X_train, pipe.predict_proba(X_train)[:, 1]
            ),
        )

        # Optional params
        mlflow.log_params(
            {"features": ",".join(FEATURE_COLS), "clf": "LogisticRegression(saga)"}
        )
        run = mlflow.active_run()
        print("Run ID:", run.info.run_id)

        # Transition latest to Production (best-effort; may require MLflow REST in real registry settings)
        try:
            client = mlflow.tracking.MlflowClient()
            mv = client.get_latest_versions(MODEL_NAME, stages=["None"])
            if mv:
                client.transition_model_version_stage(
                    MODEL_NAME,
                    mv[0].version,
                    stage="Production",
                    archive_existing_versions=True,
                )
        except Exception as e:
            print("Model stage transition skipped:", e)


if __name__ == "__main__":
    train_and_log()
