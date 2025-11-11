"""Tests for embedding index CLI helpers."""

from __future__ import annotations

from pathlib import Path

import pytest

from src.presentation.cli.embedding_index import _resolve_mongo_url


def test_resolve_mongo_url_reads_credentials_from_infra_env(tmp_path, monkeypatch):
    """Ensure Mongo credentials and host details load from fallback env files.

    Purpose:
        Verify that the CLI no longer depends on manually exported environment
        variables by reading credentials from the shared infrastructure files.
    """

    home_dir = tmp_path / "home"
    infra_dir = home_dir / "work" / "infra"
    infra_dir.mkdir(parents=True)
    (infra_dir / "secrets").mkdir(parents=True)

    env_file = infra_dir / ".env.infra"
    env_file.write_text(
        "\n".join(
            [
                "MONGO_USER=pipeline_user",
                "MONGO_PASSWORD=pipeline_secret",
                "MONGO_HOST=192.168.10.20",
                "MONGO_PORT=27018",
                "MONGO_DATABASE=document_index",
                "MONGO_AUTHSRC=admin",
                "MONGO_AUTH_MECHANISM=SCRAM-SHA-1",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setenv("HOME", str(home_dir))
    monkeypatch.setattr(Path, "home", lambda: home_dir)
    for key in (
        "MONGO_USER",
        "MONGO_PASSWORD",
        "MONGO_HOST",
        "MONGO_PORT",
        "MONGO_DATABASE",
        "MONGO_AUTHSRC",
        "MONGO_AUTH_MECHANISM",
    ):
        monkeypatch.delenv(key, raising=False)

    url = _resolve_mongo_url("mongodb://localhost:27017")

    assert (
        url
        == "mongodb://pipeline_user:pipeline_secret@192.168.10.20:27018/document_index?"
        "authSource=admin&authMechanism=SCRAM-SHA-1"
    )
