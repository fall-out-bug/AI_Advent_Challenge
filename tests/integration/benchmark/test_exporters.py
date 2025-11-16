"""Integration tests for benchmark exporter scripts."""

from __future__ import annotations

import json
import os
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

import pytest
from pymongo import MongoClient

from src.infrastructure.config.settings import get_settings

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _require_mongo_url() -> str:
    mongo_url = os.getenv("MONGODB_URL")
    if not mongo_url:
        pytest.skip("Requires MONGODB_URL environment variable")
    return mongo_url


@pytest.fixture()
def mongo_test_db(monkeypatch) -> MongoClient:
    """Provision isolated Mongo database for exporter tests."""

    mongo_url = _require_mongo_url()
    db_name = f"benchmark_test_{uuid4().hex}"
    monkeypatch.setenv("DB_NAME", db_name)
    get_settings.cache_clear()

    client = MongoClient(mongo_url)
    db = client[db_name]
    try:
        yield db
    finally:
        client.drop_database(db_name)
        get_settings.cache_clear()


def _run_exporter(script: str, output_path: Path, env: dict[str, str]) -> None:
    """Execute exporter script as subprocess."""

    cmd = [
        "python",
        str(PROJECT_ROOT / "scripts" / "quality" / "analysis" / script),
        "--hours",
        "720",
        "--limit",
        "10",
        "--output",
        str(output_path),
    ]
    subprocess.run(
        cmd,
        check=True,
        cwd=PROJECT_ROOT,
        env=env,
    )


@pytest.mark.requires_mongo
def test_export_digests_produces_expected_fields(tmp_path: Path, mongo_test_db) -> None:
    """Exported digest dataset contains required fields."""

    now = datetime.now(timezone.utc)
    mongo_test_db.digests.insert_many(
        [
            {
                "digest_id": "digest-1",
                "channel": "@integration_channel",
                "language": "ru",
                "summary_markdown": "- Пункт 1\n- Пункт 2",
                "posts": [
                    {"title": "A", "summary": "B", "text": "C"},
                    {"title": "D", "summary": "E", "text": "F"},
                ],
                "feature_flags": {"flag_one": True},
                "created_at": now,
                "latency_seconds": 123.4,
            },
            {
                "digest_id": "digest-2",
                "channel": "@integration_channel",
                "language": "ru",
                "summary_markdown": "- Пункт 3\n- Пункт 4",
                "posts": [{"title": "G", "summary": "H", "text": "I"}],
                "feature_flags": {"flag_two": True},
                "created_at": now,
                "latency_seconds": 98.7,
            },
        ]
    )

    output_file = tmp_path / "digests.jsonl"
    env = os.environ.copy()
    env["DB_NAME"] = mongo_test_db.name
    env["MONGODB_URL"] = _require_mongo_url()

    _run_exporter("export_digests.py", output_file, env)

    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        record = json.loads(line)
        assert record["channel"] == "@integration_channel"
        assert record["language"] == "ru"
        assert record["metadata"]["posts_count"] >= 1
        assert isinstance(record["metadata"]["feature_flags"], dict)
        assert record["latency_seconds"] > 0


@pytest.mark.requires_mongo
def test_export_review_reports_produces_expected_fields(
    tmp_path: Path, mongo_test_db
) -> None:
    """Exported review reports contain expected metadata."""

    now = datetime.now(timezone.utc)
    mongo_test_db.review_reports.insert_many(
        [
            {
                "report_id": "report-1",
                "assignment_id": "@integration_channel",
                "language": "ru",
                "created_at": now,
                "report": {
                    "synthesis": "Сводка отчёта.",
                    "passes": [
                        {
                            "pass_name": "pass_1",
                            "summary": "Проверка структуры.",
                            "recommendations": ["Добавить KPI"],
                            "findings": [{"title": "Наблюдение", "description": "Описание"}],
                        }
                    ],
                    "metadata": {
                        "llm_model": "gpt-4o-mini",
                        "feature_flags": {"structured_review": True},
                        "latency_seconds": 45.6,
                    },
                },
            },
            {
                "report_id": "report-2",
                "assignment_id": "@integration_channel",
                "language": "ru",
                "created_at": now,
                "report": {
                    "synthesis": "Второй отчёт.",
                    "passes": [
                        {
                            "pass_name": "pass_1",
                            "summary": "Контроль качества.",
                            "recommendations": [],
                            "findings": [],
                        }
                    ],
                    "metadata": {
                        "llm_model": "gpt-4o-mini",
                        "feature_flags": {"structured_review": True},
                        "latency_seconds": 30.0,
                    },
                },
            },
        ]
    )

    output_file = tmp_path / "review_reports.jsonl"
    env = os.environ.copy()
    env["DB_NAME"] = mongo_test_db.name
    env["MONGODB_URL"] = _require_mongo_url()

    _run_exporter("export_review_reports.py", output_file, env)

    lines = output_file.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2
    for line in lines:
        record = json.loads(line)
        assert record["channel"] == "@integration_channel"
        assert record["metadata"]["assignment_id"] == "@integration_channel"
        assert record["metadata"]["passes_count"] >= 1
        assert isinstance(record["metadata"]["feature_flags"], dict)
        assert record["latency_seconds"] >= 30.0

