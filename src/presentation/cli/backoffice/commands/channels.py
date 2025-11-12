"""Channel management commands for backoffice CLI."""

from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Sequence

import click
from motor.core import AgnosticDatabase

from src.infrastructure.database.mongo import get_db
from src.presentation.cli.backoffice.formatters import OutputFormat, format_output
from src.presentation.cli.backoffice.formatters import OutputFormat, format_output
from src.presentation.cli.backoffice.metrics import track_command
from src.presentation.mcp.tools.channels.channel_management import (
    add_channel as mcp_add_channel,
)
from src.presentation.mcp.tools.channels.channel_management import (
    delete_channel as mcp_delete_channel,
)


@click.group(help="Channel subscription management commands.")
def channels() -> None:
    """Channel command group."""


@channels.command("list", help="List user channel subscriptions.")
@click.option("--user-id", required=True, type=int, help="User identifier.")
@click.option("--limit", default=100, type=int, show_default=True, help="Max channels.")
@click.option("--json", "as_json", is_flag=True, help="Return output in JSON format.")
@track_command("channels_list")
def list_channels_command(user_id: int, limit: int, as_json: bool) -> None:
    """List active channel subscriptions for a user."""
    asyncio.run(_list_channels(user_id=user_id, limit=limit, as_json=as_json))


async def _list_channels(user_id: int, limit: int, as_json: bool) -> None:
    db = await get_db()
    channels = await _fetch_channels(db, user_id=user_id, limit=limit)

    if not channels:
        message = "[]" if as_json else "No active channels found."
        click.echo(message)
        return

    output = format_output(channels, OutputFormat.JSON if as_json else OutputFormat.TABLE)
    click.echo(output)


async def _fetch_channels(db: AgnosticDatabase, user_id: int, limit: int) -> List[Dict[str, Any]]:
    cursor = (
        db.channels.find({"user_id": user_id, "active": True})
        .sort("subscribed_at", -1)
        .limit(max(limit, 1))
    )
    records = await cursor.to_list(length=limit)

    formatted: List[Dict[str, Any]] = []
    for record in records:
        formatted.append(
            {
                "id": str(record.get("_id", "")),
                "channel": record.get("channel_username", ""),
                "title": record.get("title", ""),
                "tags": record.get("tags", []),
                "active": record.get("active", True),
                "subscribed_at": record.get("subscribed_at"),
            }
        )
    return formatted


@channels.command("add", help="Subscribe user to a channel.")
@click.option("--user-id", required=True, type=int, help="User identifier.")
@click.option("--channel", required=True, help="Channel username or link.")
@click.option(
    "--tag",
    "tags",
    multiple=True,
    help="Optional tags to annotate subscription (repeatable).",
)
@click.option("--json", "as_json", is_flag=True, help="Return output in JSON format.")
@track_command("channels_add")
def add_channel_command(user_id: int, channel: str, tags: Sequence[str], as_json: bool) -> None:
    """Subscribe user to a channel."""
    asyncio.run(_add_channel(user_id=user_id, channel=channel, tags=tags, as_json=as_json))


async def _add_channel(
    user_id: int,
    channel: str,
    tags: Sequence[str],
    as_json: bool,
) -> None:
    result = await mcp_add_channel(
        user_id=user_id,
        channel_username=channel,
        tags=list(tags),
    )

    status = result.get("status", "unknown")
    output_payload: Dict[str, Any] = {
        "status": status,
        "channel": channel,
        "channel_id": result.get("channel_id"),
        "message": result.get("message"),
    }

    fmt = OutputFormat.JSON if as_json else OutputFormat.TABLE
    output = format_output(output_payload, fmt)

    if status == "error":
        if as_json:
            click.echo(output)
        else:
            click.echo(output or f"Failed to subscribe: {result.get('message', 'unknown error')}")
        raise click.ClickException(result.get("message", "Subscription failed"))

    click.echo(output or "Subscription successful.")


@channels.command("remove", help="Unsubscribe user from a channel.")
@click.option("--user-id", required=True, type=int, help="User identifier.")
@click.option(
    "--channel-id",
    required=True,
    help="Channel identifier (ObjectId) or MCP reference.",
)
@click.option("--json", "as_json", is_flag=True, help="Return output in JSON format.")
@track_command("channels_remove")
def remove_channel_command(user_id: int, channel_id: str, as_json: bool) -> None:
    """Unsubscribe a user from a channel."""
    asyncio.run(
        _remove_channel(
            user_id=user_id,
            channel_id=channel_id,
            as_json=as_json,
        )
    )


async def _remove_channel(user_id: int, channel_id: str, as_json: bool) -> None:
    result = await mcp_delete_channel(user_id=user_id, channel_id=channel_id)
    status = result.get("status", "unknown")
    fmt = OutputFormat.JSON if as_json else OutputFormat.TABLE
    output = format_output(result, fmt)

    if status != "deleted":
        if as_json:
            click.echo(output)
        else:
            click.echo(output or f"Channel not found: {channel_id}")
        raise click.ClickException("Channel not found or already removed")

    click.echo(output or "Channel removed.")
