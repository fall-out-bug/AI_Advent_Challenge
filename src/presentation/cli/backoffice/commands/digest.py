"""Digest management commands for backoffice CLI."""

from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Any, Dict

import click

<<<<<<< HEAD
=======
from src.domain.services.channel_normalizer import ChannelNormalizer
>>>>>>> origin/master
from src.presentation.cli.backoffice.formatters import OutputFormat, format_output
from src.presentation.cli.backoffice.metrics import track_command
from src.presentation.cli.backoffice.services.digest_exporter import (
    export_digest_to_file,
)


@click.group(help="Channel digest commands.")
def digest() -> None:
    """Digest command group."""


@digest.command("run", help="Generate digest for channel(s).")
@click.option("--user-id", required=True, type=int, help="User identifier.")
@click.option("--channel", help="Specific channel username (optional).")
@click.option(
    "--hours",
    default=24,
    type=int,
    show_default=True,
    help="Time window in hours.",
)
@click.option(
    "--format",
    "content_format",
    type=click.Choice(["markdown", "json"], case_sensitive=False),
    default="markdown",
    show_default=True,
    help="Digest content format.",
)
@click.option("--json", "as_json", is_flag=True, help="Return output in JSON format.")
@track_command("digest_run")
def run_digest_command(
    user_id: int,
    channel: str | None,
    hours: int,
    content_format: str,
    as_json: bool,
) -> None:
    """Generate digest for a specific channel or all active channels."""
    asyncio.run(
        _run_digest(
            user_id=user_id,
            channel=channel,
            hours=hours,
            content_format=content_format.lower(),
            as_json=as_json,
        )
    )


async def _run_digest(
    user_id: int,
    channel: str | None,
    hours: int,
    content_format: str,
    as_json: bool,
) -> None:
    from src.application.use_cases.generate_channel_digest import (
        GenerateChannelDigestUseCase,
    )
    from src.application.use_cases.generate_channel_digest_by_name import (
        GenerateChannelDigestByNameUseCase,
    )

    try:
        if channel:
<<<<<<< HEAD
            use_case = GenerateChannelDigestByNameUseCase()
            digests = [
                await use_case.execute(
                    user_id=user_id, channel_username=channel, hours=hours
=======
            # Normalize channel username to canonical form (lowercase, without @ prefix) per E.1 policy
            normalizer = ChannelNormalizer()
            channel_username = normalizer.to_canonical_form(channel)

            use_case = GenerateChannelDigestByNameUseCase()
            digests = [
                await use_case.execute(
                    user_id=user_id, channel_username=channel_username, hours=hours
>>>>>>> origin/master
                )
            ]
        else:
            use_case = GenerateChannelDigestUseCase()
            digests = await use_case.execute(user_id=user_id, hours=hours)
    except Exception as exc:  # noqa: BLE001 - re-raised after logging
        if as_json:
            click.echo(
                format_output(
                    {"status": "error", "message": str(exc)}, OutputFormat.JSON
                )
            )
        else:
            click.echo(f"Failed to generate digest: {exc}")
        raise click.ClickException(str(exc))

    payload = [_serialise_digest(digest, content_format) for digest in digests]

    if not payload:
        message = "[]" if as_json else "No digests generated."
        click.echo(message)
        return

    fmt = OutputFormat.JSON if as_json else OutputFormat.TABLE
    click.echo(format_output(payload, fmt))


@digest.command("last", help="Show metadata for the last generated digest.")
@click.option("--user-id", required=True, type=int, help="User identifier.")
@click.option("--channel", required=True, help="Channel username.")
@click.option("--json", "as_json", is_flag=True, help="Return output in JSON format.")
@track_command("digest_last")
def last_digest_command(user_id: int, channel: str, as_json: bool) -> None:
    """Display metadata for the last digest generated for a channel."""
    asyncio.run(_show_last_digest(user_id=user_id, channel=channel, as_json=as_json))


async def _show_last_digest(user_id: int, channel: str, as_json: bool) -> None:
    from src.infrastructure.database.mongo import get_db

    db = await get_db()
    document = await db.channels.find_one(
        {"user_id": user_id, "channel_username": channel.lstrip("@")}
    )

    if not document:
        message = (
            format_output(
                {"status": "not_found", "channel": channel}, OutputFormat.JSON
            )
            if as_json
            else f"Channel '{channel}' not found for user {user_id}."
        )

        click.echo(message)
        raise click.ClickException("Channel not found.")

    payload: Dict[str, Any] = {
        "channel": document.get("channel_username", channel),
        "title": document.get("title"),
        "last_digest": document.get("last_digest"),
        "tags": document.get("tags", []),
        "active": document.get("active", True),
    }

    fmt = OutputFormat.JSON if as_json else OutputFormat.TABLE
    click.echo(format_output(payload, fmt))


@digest.command("export", help="Export digest to a file (PDF or Markdown).")
@click.option("--user-id", required=True, type=int, help="User identifier.")
@click.option("--channel", help="Specific channel username (optional).")
@click.option(
    "--hours",
    default=24,
    type=int,
    show_default=True,
    help="Time window in hours.",
)
@click.option(
    "--output",
    "output_path",
    type=click.Path(path_type=Path),
    help="Destination path for the exported file.",
)
@click.option(
    "--format",
    "export_format",
    type=click.Choice(["pdf", "markdown"], case_sensitive=False),
    default="pdf",
    show_default=True,
    help="Export format.",
)
@click.option(
    "--overwrite",
    is_flag=True,
    help="Overwrite destination file if it already exists.",
)
@track_command("digest_export")
def export_digest_command(
    user_id: int,
    channel: str | None,
    hours: int,
    output_path: Path | None,
    export_format: str,
    overwrite: bool,
) -> None:
    """Generate digest and export it to a file."""

    try:
        destination = asyncio.run(
            export_digest_to_file(
                user_id=user_id,
                hours=hours,
                channel=channel,
                output_path=output_path,
                export_format=export_format,
                overwrite=overwrite,
            )
        )
    except FileExistsError as exc:
        raise click.ClickException(str(exc)) from exc
    except Exception as exc:  # noqa: BLE001 - converted to CLI-friendly error
        raise click.ClickException(str(exc)) from exc

    click.echo(f"Digest saved to {destination}")


def _serialise_digest(digest, content_format: str) -> Dict[str, Any]:
    """Serialise ChannelDigest DTO to CLI-friendly representation."""
    summary = digest.summary
    record: Dict[str, Any] = {
        "channel": digest.channel_username,
        "title": digest.channel_title,
        "post_count": digest.post_count,
        "hours": digest.time_window_hours,
        "generated_at": digest.generated_at.isoformat(),
        "tags": digest.tags,
    }

    if content_format == "json":
        record["summary"] = {
            "text": summary.text,
            "sentences_count": summary.sentences_count,
            "method": summary.method,
            "confidence": summary.confidence,
            "metadata": summary.metadata,
        }
    else:
        record["summary"] = summary.text

    return record
