"""MLflow training script."""

import mlflow

mlflow.set_experiment("test_experiment")
with mlflow.start_run():
    mlflow.log_param("alpha", 0.1)
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_model("model", "my_model")

