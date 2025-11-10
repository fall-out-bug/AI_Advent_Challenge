"""Tests for CLI digest export utilities."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest

from src.application.dtos.digest_dtos import ChannelDigest
from src.domain.value_objects.summary_result import SummaryResult
from src.presentation.cli.backoffice.services import digest_exporter


@pytest.fixture()
def sample_digest() -> ChannelDigest:
    return ChannelDigest(
        channel_username="test_channel",
        channel_title="Test Channel",
        summary=SummaryResult(
            text="Summary text",
            sentences_count=1,
            method="direct",
        ),
        post_count=5,
        time_window_hours=24,
        tags=["news"],
        generated_at=datetime.fromisoformat("2025-11-09T11:00:00"),
    )


def test_render_digest_markdown(sample_digest: ChannelDigest) -> None:
    markdown = digest_exporter.render_digest_markdown(
        [sample_digest],
        {
            "generation_date": "2025-11-09T11:29:00Z",
            "hours": 24,
            "channel": None,
        },
    )

    assert "# Channel Digest" in markdown
    assert "@test_channel" in markdown
    assert "Posts processed: 5" in markdown
    assert "Test Channel" in markdown


@pytest.mark.asyncio()
async def test_export_digest_markdown(tmp_path: Path, sample_digest: ChannelDigest) -> None:
    destination = tmp_path / "digest.md"

    async def fake_fetcher(user_id: int, channel: str | None, hours: int):
        return [sample_digest]

    path = await digest_exporter.export_digest_to_file(
        user_id=1,
        hours=24,
        channel=None,
        output_path=destination,
        export_format="markdown",
        overwrite=False,
        digest_fetcher=fake_fetcher,
    )

    assert path == destination
    content = destination.read_text(encoding="utf-8")
    assert "Summary text" in content
    assert "@test_channel" in content


@pytest.mark.asyncio()
async def test_export_digest_pdf(tmp_path: Path, sample_digest: ChannelDigest) -> None:
    destination = tmp_path / "digest.pdf"

    async def fake_fetcher(user_id: int, channel: str | None, hours: int):
        return [sample_digest]

    rendered_markdown = "Sample markdown"

    def fake_renderer(_digests, _metadata):
        return rendered_markdown

    def fake_converter(markdown: str) -> bytes:
        assert markdown == rendered_markdown
        return b"%PDF-1.0"

    path = await digest_exporter.export_digest_to_file(
        user_id=1,
        hours=24,
        channel=None,
        output_path=destination,
        export_format="pdf",
        overwrite=False,
        digest_fetcher=fake_fetcher,
        markdown_renderer=fake_renderer,
        pdf_converter=fake_converter,
    )

    assert path == destination
    assert destination.read_bytes() == b"%PDF-1.0"


@pytest.mark.asyncio()
async def test_export_digest_overwrite_guard(tmp_path: Path, sample_digest: ChannelDigest) -> None:
    destination = tmp_path / "digest.md"
    destination.write_text("existing", encoding="utf-8")

    async def fake_fetcher(user_id: int, channel: str | None, hours: int):
        return [sample_digest]

    with pytest.raises(FileExistsError):
        await digest_exporter.export_digest_to_file(
            user_id=1,
            hours=24,
            channel=None,
            output_path=destination,
            export_format="markdown",
            overwrite=False,
            digest_fetcher=fake_fetcher,
        )
