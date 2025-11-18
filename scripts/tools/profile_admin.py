#!/usr/bin/env python3
"""Admin CLI tool for managing user profiles and memory.

Purpose:
    Internal tool for administrators to manage personalization.
    No public Telegram commands in MVP.

Usage:
    python scripts/tools/profile_admin.py list
    python scripts/tools/profile_admin.py show <user_id>
    python scripts/tools/profile_admin.py reset <user_id>
    python scripts/tools/profile_admin.py update <user_id> --persona "Custom" --tone witty
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

import click
from motor.motor_asyncio import AsyncIOMotorClient
from rich.console import Console
from rich.table import Table

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.application.personalization.dtos import ResetPersonalizationInput
from src.application.personalization.use_cases.reset_personalization import (
    ResetPersonalizationUseCase,
)
from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.memory_repository import (
    MongoUserMemoryRepository,
)
from src.infrastructure.personalization.profile_repository import (
    MongoUserProfileRepository,
)

logger = get_logger("profile_admin")
console = Console()


@click.group()
def cli():
    """Admin CLI for user profiles and memory.

    Purpose:
        Manage personalization settings and memory for users.

    Example:
        python scripts/tools/profile_admin.py list
    """
    pass


@cli.command()
def list():
    """List all user profiles.

    Purpose:
        Display summary of all user profiles in system.

    Example:
        python scripts/tools/profile_admin.py list
    """
    async def _list():
        settings = get_settings()
        client = AsyncIOMotorClient(settings.mongodb_url)

        try:
            db = client[settings.db_name]
            profiles = await db.user_profiles.find().to_list(length=1000)

            if not profiles:
                console.print("[yellow]No profiles found[/yellow]")
                return

            # Create table
            table = Table(title="User Profiles")
            table.add_column("User ID", style="cyan")
            table.add_column("Persona", style="green")
            table.add_column("Language", style="blue")
            table.add_column("Tone", style="magenta")
            table.add_column("Has Summary", style="yellow")

            for profile in profiles:
                table.add_row(
                    profile["user_id"],
                    profile["persona"],
                    profile["language"],
                    profile["tone"],
                    "✓" if profile.get("memory_summary") else "✗",
                )

            console.print(table)
            console.print(f"\n[green]Total profiles: {len(profiles)}[/green]")

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            logger.error("Failed to list profiles", extra={"error": str(e)})
        finally:
            client.close()

    asyncio.run(_list())


@cli.command()
@click.argument("user_id")
def show(user_id):
    """Show profile and memory stats for user.

    Purpose:
        Display detailed information about user's profile and memory.

    Args:
        user_id: User identifier.

    Example:
        python scripts/tools/profile_admin.py show 123456789
    """
    async def _show():
        settings = get_settings()
        client = AsyncIOMotorClient(settings.mongodb_url)

        try:
            db = client[settings.db_name]

            # Get profile
            profile = await db.user_profiles.find_one({"user_id": user_id})

            if not profile:
                console.print(
                    f"[red]Profile not found for user_id: {user_id}[/red]"
                )
                return

            # Get memory stats
            event_count = await db.user_memory.count_documents(
                {"user_id": user_id}
            )

            # Get recent events
            recent_events = (
                await db.user_memory.find({"user_id": user_id})
                .sort("created_at", -1)
                .limit(5)
                .to_list(length=5)
            )

            # Display profile
            console.print(
                f"\n[bold cyan]Profile for user_id: {user_id}[/bold cyan]"
            )
            console.print(f"Persona: [green]{profile['persona']}[/green]")
            console.print(f"Language: [blue]{profile['language']}[/blue]")
            console.print(f"Tone: [magenta]{profile['tone']}[/magenta]")
            preferred_topics = ", ".join(
                profile.get("preferred_topics", [])
            )
            console.print(f"Preferred topics: {preferred_topics}")

            if profile.get("memory_summary"):
                console.print(f"\n[bold]Memory Summary:[/bold]")
                summary = profile["memory_summary"]
                console.print(f"{summary[:200]}{'...' if len(summary) > 200 else ''}")

            # Display memory stats
            console.print(f"\n[bold]Memory Stats:[/bold]")
            console.print(f"Total events: [yellow]{event_count}[/yellow]")

            if recent_events:
                console.print(f"\n[bold]Recent Events:[/bold]")
                for event in recent_events:
                    role = event["role"]
                    content = event["content"][:100]
                    created_at = event.get("created_at", "N/A")
                    console.print(
                        f"  [{role}] {content}... ({created_at})"
                    )

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            logger.error(
                "Failed to show profile",
                extra={"user_id": user_id, "error": str(e)},
            )
        finally:
            client.close()

    asyncio.run(_show())


@cli.command()
@click.argument("user_id")
@click.confirmation_option(
    prompt="Are you sure you want to reset this user?"
)
def reset(user_id):
    """Reset profile and memory for user.

    Purpose:
        Delete all memory and reset profile to defaults.
        Requires confirmation.

    Args:
        user_id: User identifier.

    Example:
        python scripts/tools/profile_admin.py reset 123456789
    """
    async def _reset():
        settings = get_settings()
        client = AsyncIOMotorClient(settings.mongodb_url)

        try:
            # Use reset use case
            profile_repo = MongoUserProfileRepository(
                client, settings.db_name
            )
            memory_repo = MongoUserMemoryRepository(
                client, settings.db_name
            )

            reset_use_case = ResetPersonalizationUseCase(
                profile_repo=profile_repo,
                memory_repo=memory_repo,
            )

            input_data = ResetPersonalizationInput(user_id=user_id)
            output = await reset_use_case.execute(input_data)

            if output.success:
                console.print(
                    f"[green]✓ Reset complete for user_id: {user_id}[/green]"
                )
                console.print(f"  Profile reset: {output.profile_reset}")
                console.print(
                    f"  Memory deleted: {output.memory_deleted_count} events"
                )
            else:
                console.print(
                    f"[red]✗ Reset failed for user_id: {user_id}[/red]"
                )

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            logger.error(
                "Failed to reset profile",
                extra={"user_id": user_id, "error": str(e)},
            )
        finally:
            client.close()

    asyncio.run(_reset())


@cli.command()
@click.argument("user_id")
@click.option("--persona", help="Update persona name")
@click.option("--tone", help="Update tone (witty/formal/casual)")
@click.option("--language", help="Update language (ru/en)")
def update(user_id, persona, tone, language):
    """Update profile settings for user.

    Purpose:
        Modify profile settings without affecting memory.

    Args:
        user_id: User identifier.
        persona: New persona name (optional).
        tone: New tone (optional).
        language: New language (optional).

    Example:
        python scripts/tools/profile_admin.py update 123 --tone formal
    """
    async def _update():
        settings = get_settings()
        client = AsyncIOMotorClient(settings.mongodb_url)

        try:
            db = client[settings.db_name]

            # Get current profile
            profile_doc = await db.user_profiles.find_one({"user_id": user_id})

            if not profile_doc:
                console.print(
                    f"[red]Profile not found for user_id: {user_id}[/red]"
                )
                return

            # Build update
            updates = {}
            if persona:
                updates["persona"] = persona
            if tone:
                updates["tone"] = tone
            if language:
                updates["language"] = language

            if not updates:
                console.print("[yellow]No updates specified[/yellow]")
                return

            # Update profile
            updates["updated_at"] = datetime.utcnow()

            await db.user_profiles.update_one(
                {"user_id": user_id}, {"$set": updates}
            )

            console.print(
                f"[green]✓ Profile updated for user_id: {user_id}[/green]"
            )
            for key, value in updates.items():
                if key != "updated_at":
                    console.print(f"  {key}: {value}")

        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            logger.error(
                "Failed to update profile",
                extra={"user_id": user_id, "error": str(e)},
            )
        finally:
            client.close()

    asyncio.run(_update())


if __name__ == "__main__":
    cli()
