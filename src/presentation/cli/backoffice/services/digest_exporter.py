"""Utilities for exporting channel digests via the backoffice CLI."""

from __future__ import annotations

import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Awaitable, Callable, Sequence

from src.application.dtos.digest_dtos import ChannelDigest
from src.application.use_cases.generate_channel_digest import (
    GenerateChannelDigestUseCase,
)
from src.application.use_cases.generate_channel_digest_by_name import (
    GenerateChannelDigestByNameUseCase,
)
from src.infrastructure.logging import get_logger
from src.infrastructure.monitoring.prometheus_metrics import (
    pdf_file_size_bytes,
    pdf_generation_duration_seconds,
    pdf_generation_errors_total,
    pdf_pages_total,
)

logger = get_logger("cli.digest_exporter")

DigestFetcher = Callable[[int, str | None, int], Awaitable[Sequence[ChannelDigest]]]
MarkdownRenderer = Callable[[Sequence[ChannelDigest], dict], str]
PdfConverter = Callable[[str], bytes]


@dataclass(slots=True)
class ExportMetadata:
    """Metadata captured during digest export."""

    user_id: int
    channel: str | None
    hours: int
    generated_at: datetime

    @property
    def to_dict(self) -> dict:
        return {
            "user_id": self.user_id,
            "channel": self.channel,
            "hours": self.hours,
            "generation_date": self.generated_at.isoformat(),
        }


async def fetch_channel_digests(
    user_id: int,
    channel: str | None,
    hours: int,
) -> Sequence[ChannelDigest]:
    """Fetch digests for all channels or a specific one."""

    if channel:
        use_case = GenerateChannelDigestByNameUseCase()
        digest = await use_case.execute(
            user_id=user_id,
            channel_username=channel,
            hours=hours,
        )
        return [digest] if digest.post_count > 0 else []

    use_case = GenerateChannelDigestUseCase()
    return await use_case.execute(user_id=user_id, hours=hours)


def render_digest_markdown(
    digests: Sequence[ChannelDigest],
    metadata: dict,
) -> str:
    """Render markdown document for channel digests."""

    total_posts = sum(d.post_count for d in digests)
    lines: list[str] = ["# Channel Digest", ""]
    lines.append(f"Generated: {metadata.get('generation_date')}")
    lines.append(
        f"Channels: {len(digests)} | Total Posts: {total_posts} | Hours: {metadata.get('hours')}"
    )
    if metadata.get("channel"):
        lines.append(f"Filter: @{metadata['channel']}")
    lines.extend(["", "---", ""])

    for digest in digests:
        lines.append(f"## @{digest.channel_username}")
        if digest.channel_title:
            lines.append(f"**{digest.channel_title}**")
        lines.append("")
        lines.append(digest.summary.text)
        lines.append("")
        lines.append(f"*Posts processed: {digest.post_count}*")
        if digest.tags:
            lines.append(f"*Tags: {', '.join(digest.tags)}*")
        lines.extend(["", "---", ""])

    lines.append("*End of digest*")
    return "\n".join(lines)


def convert_markdown_to_pdf(markdown: str) -> bytes:
    """Convert markdown document to PDF bytes with styling and metrics."""

    start_time = time.time()
    try:
        import markdown as md
        from weasyprint import HTML
    except Exception as exc:  # pragma: no cover - import guard
        pdf_generation_errors_total.labels(error_type=type(exc).__name__).inc()
        raise

    html_content = md.markdown(markdown, extensions=["extra", "nl2br"])
    full_html = _HTML_TEMPLATE.format(content=html_content)

    try:
        pdf_bytes = HTML(string=full_html).write_pdf()
    except Exception as exc:  # pragma: no cover - delegated to weasyprint
        pdf_generation_errors_total.labels(error_type=type(exc).__name__).inc()
        raise

    duration = time.time() - start_time
    pdf_generation_duration_seconds.observe(duration)
    pdf_file_size_bytes.observe(len(pdf_bytes))
    estimated_pages = max(1, len(markdown) // 3000 + 1)
    pdf_pages_total.observe(estimated_pages)

    return pdf_bytes


async def export_digest_to_file(
    user_id: int,
    hours: int,
    channel: str | None,
    output_path: Path | None,
    export_format: str,
    overwrite: bool = False,
    digest_fetcher: DigestFetcher | None = None,
    markdown_renderer: MarkdownRenderer | None = None,
    pdf_converter: PdfConverter | None = None,
) -> Path:
    """Generate digest and write it to a file."""

    export_format = export_format.lower()
    if export_format not in {"pdf", "markdown"}:
        raise ValueError("export_format must be 'pdf' or 'markdown'")

    fetcher = digest_fetcher or fetch_channel_digests
    renderer = markdown_renderer or render_digest_markdown
    converter = pdf_converter or convert_markdown_to_pdf

    digests = await fetcher(user_id, channel, hours)
    if not digests:
        raise RuntimeError("No digest data available for the requested parameters.")

    metadata = ExportMetadata(
        user_id=user_id,
        channel=channel,
        hours=hours,
        generated_at=datetime.utcnow(),
    )

    markdown = renderer(digests, metadata.to_dict)
    destination = _resolve_output_path(output_path, export_format, metadata)

    if destination.exists() and not overwrite:
        raise FileExistsError(
            f"Destination '{destination}' already exists. Pass --overwrite to replace it."
        )

    destination.parent.mkdir(parents=True, exist_ok=True)

    if export_format == "markdown":
        destination.write_text(markdown, encoding="utf-8")
        logger.info("Digest markdown written", path=str(destination))
    else:
        pdf_bytes = converter(markdown)
        destination.write_bytes(pdf_bytes)
        logger.info(
            "Digest PDF written",
            path=str(destination),
            size=len(pdf_bytes),
            user_id=user_id,
            channel=channel,
        )

    return destination


def _resolve_output_path(
    output_path: Path | None,
    export_format: str,
    metadata: ExportMetadata,
) -> Path:
    if output_path is not None:
        return output_path

    timestamp = metadata.generated_at.strftime("%Y%m%d_%H%M%S")
    channel_slug = metadata.channel or "all"
    suffix = "pdf" if export_format == "pdf" else "md"
    filename = f"digest_{channel_slug}_{timestamp}.{suffix}"
    return Path.cwd() / filename


_DEFAULT_CSS = """
    @page {
        size: A4;
        margin: 2cm;
    }
    body {
        font-family: Arial, Helvetica, sans-serif;
        font-size: 12pt;
        line-height: 1.6;
        color: #333;
    }
    h1 {
        font-size: 24pt;
        font-weight: bold;
        margin-bottom: 1em;
        color: #000;
    }
    h2 {
        font-size: 18pt;
        font-weight: bold;
        margin-top: 1.5em;
        margin-bottom: 0.5em;
        color: #222;
        page-break-after: avoid;
    }
    p {
        margin-bottom: 1em;
    }
    strong {
        font-weight: bold;
    }
    em {
        font-style: italic;
    }
"""

_HTML_TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta charset=\"UTF-8\">
    <style>{css}</style>
</head>
<body>
    {content}
</body>
</html>
""".format(
    css=_DEFAULT_CSS, content="{content}"
)


__all__ = [
    "export_digest_to_file",
    "fetch_channel_digests",
    "render_digest_markdown",
    "convert_markdown_to_pdf",
]
