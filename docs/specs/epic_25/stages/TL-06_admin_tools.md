# Stage TL-06: Admin Tools Only (No Public Commands)

**Epic**: EP25 - Personalised Butler  
**Stage**: TL-06  
**Duration**: 1 day  
**Owner**: Dev C  
**Dependencies**: TL-05  
**Status**: Pending

---

## Goal

Create internal admin CLI tool for profile and memory management (no public Telegram commands in MVP).

---

## Objectives

1. Implement CLI tool with list/show/reset/update commands
2. Add comprehensive error handling and logging
3. Write tests for CLI commands
4. Document CLI usage

---

## File Structure

```
scripts/tools/
└── profile_admin.py          # Admin CLI tool

docs/guides/
└── profile_admin_guide.md    # CLI usage documentation

tests/integration/tools/
├── __init__.py
└── test_profile_admin.py     # CLI tests
```

---

## Implementation Details

### 1. Admin CLI Tool

**File**: `scripts/tools/profile_admin.py`

**Requirements**:
- Click-based CLI interface
- Commands: list, show, reset, update
- Async MongoDB operations
- Structured logging
- Error handling

**Implementation**:

```python
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
from pathlib import Path

import click
from motor.motor_asyncio import AsyncIOMotorClient
from rich.console import Console
from rich.table import Table

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from src.infrastructure.config.settings import get_settings
from src.infrastructure.logging import get_logger
from src.infrastructure.personalization.factory import (
    create_personalized_use_cases
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
                console.print(f"[red]Profile not found for user_id: {user_id}[/red]")
                return
            
            # Get memory stats
            event_count = await db.user_memory.count_documents({"user_id": user_id})
            
            # Get recent events
            recent_events = await db.user_memory.find(
                {"user_id": user_id}
            ).sort("created_at", -1).limit(5).to_list(length=5)
            
            # Display profile
            console.print(f"\n[bold cyan]Profile for user_id: {user_id}[/bold cyan]")
            console.print(f"Persona: [green]{profile['persona']}[/green]")
            console.print(f"Language: [blue]{profile['language']}[/blue]")
            console.print(f"Tone: [magenta]{profile['tone']}[/magenta]")
            console.print(f"Preferred topics: {', '.join(profile.get('preferred_topics', []))}")
            
            if profile.get("memory_summary"):
                console.print(f"\n[bold]Memory Summary:[/bold]")
                console.print(f"{profile['memory_summary'][:200]}...")
            
            # Display memory stats
            console.print(f"\n[bold]Memory Stats:[/bold]")
            console.print(f"Total events: [yellow]{event_count}[/yellow]")
            
            if recent_events:
                console.print(f"\n[bold]Recent Events:[/bold]")
                for event in recent_events:
                    role = event["role"]
                    content = event["content"][:100]
                    created_at = event["created_at"]
                    console.print(f"  [{role}] {content}... ({created_at})")
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            logger.error(
                "Failed to show profile",
                extra={"user_id": user_id, "error": str(e)}
            )
        finally:
            client.close()
    
    asyncio.run(_show())


@cli.command()
@click.argument("user_id")
@click.confirmation_option(prompt="Are you sure you want to reset this user?")
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
            from src.infrastructure.personalization.profile_repository import (
                MongoUserProfileRepository
            )
            from src.infrastructure.personalization.memory_repository import (
                MongoUserMemoryRepository
            )
            from src.application.personalization.use_cases.reset_personalization import (
                ResetPersonalizationUseCase
            )
            from src.application.personalization.dtos import ResetPersonalizationInput
            
            profile_repo = MongoUserProfileRepository(client, settings.db_name)
            memory_repo = MongoUserMemoryRepository(client, settings.db_name)
            
            reset_use_case = ResetPersonalizationUseCase(
                profile_repo=profile_repo,
                memory_repo=memory_repo,
            )
            
            input_data = ResetPersonalizationInput(user_id=user_id)
            output = await reset_use_case.execute(input_data)
            
            if output.success:
                console.print(f"[green]✓ Reset complete for user_id: {user_id}[/green]")
                console.print(f"  Profile reset: {output.profile_reset}")
                console.print(f"  Memory deleted: {output.memory_deleted_count} events")
            else:
                console.print(f"[red]✗ Reset failed for user_id: {user_id}[/red]")
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            logger.error(
                "Failed to reset profile",
                extra={"user_id": user_id, "error": str(e)}
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
                console.print(f"[red]Profile not found for user_id: {user_id}[/red]")
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
            from datetime import datetime
            updates["updated_at"] = datetime.utcnow()
            
            await db.user_profiles.update_one(
                {"user_id": user_id},
                {"$set": updates}
            )
            
            console.print(f"[green]✓ Profile updated for user_id: {user_id}[/green]")
            for key, value in updates.items():
                if key != "updated_at":
                    console.print(f"  {key}: {value}")
            
        except Exception as e:
            console.print(f"[red]Error: {str(e)}[/red]")
            logger.error(
                "Failed to update profile",
                extra={"user_id": user_id, "error": str(e)}
            )
        finally:
            client.close()
    
    asyncio.run(_update())


if __name__ == "__main__":
    cli()
```

**Dependencies** (`requirements.txt` addition):
```
click>=8.1.0
rich>=13.0.0
```

---

### 2. CLI Usage Documentation

**File**: `docs/guides/profile_admin_guide.md`

```markdown
# Profile Admin CLI Guide

## Overview

Internal CLI tool for managing user personalization profiles and memory.

## Installation

```bash
# Install dependencies
pip install click rich

# Ensure MongoDB is accessible
# Set MONGODB_URL environment variable if needed
export MONGODB_URL="mongodb://admin:password@localhost:27017/butler?authSource=admin"
```

## Commands

### List All Profiles

Display summary of all user profiles in system.

```bash
python scripts/tools/profile_admin.py list
```

**Output**:
```
┏━━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━┓
┃ User ID   ┃ Persona               ┃ Language ┃ Tone  ┃ Has Summary ┃
┡━━━━━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━┩
│ 123456789 │ Alfred-style дворецкий│ ru       │ witty │ ✓           │
│ 987654321 │ Alfred-style дворецкий│ ru       │ witty │ ✗           │
└───────────┴───────────────────────┴──────────┴───────┴─────────────┘

Total profiles: 2
```

### Show Profile Details

Display detailed information about specific user's profile and memory.

```bash
python scripts/tools/profile_admin.py show <user_id>
```

**Example**:
```bash
python scripts/tools/profile_admin.py show 123456789
```

**Output**:
```
Profile for user_id: 123456789
Persona: Alfred-style дворецкий
Language: ru
Tone: witty
Preferred topics: Python, AI

Memory Summary:
User has been asking about Python programming and AI topics...

Memory Stats:
Total events: 42

Recent Events:
  [user] Hello, how are you? (2025-11-18 10:30:00)
  [assistant] Good day, sir. I trust the day finds you well... (2025-11-18 10:30:05)
```

### Reset Profile

Reset profile to defaults and delete all memory events.

```bash
python scripts/tools/profile_admin.py reset <user_id>
```

**Example**:
```bash
python scripts/tools/profile_admin.py reset 123456789
# Confirmation prompt: Are you sure you want to reset this user? [y/N]:
```

**Output**:
```
✓ Reset complete for user_id: 123456789
  Profile reset: True
  Memory deleted: 42 events
```

### Update Profile

Update specific profile settings without affecting memory.

```bash
python scripts/tools/profile_admin.py update <user_id> [OPTIONS]
```

**Options**:
- `--persona TEXT`: Update persona name
- `--tone TEXT`: Update tone (witty/formal/casual)
- `--language TEXT`: Update language (ru/en)

**Examples**:
```bash
# Update tone only
python scripts/tools/profile_admin.py update 123456789 --tone formal

# Update multiple settings
python scripts/tools/profile_admin.py update 123456789 --tone casual --language en
```

**Output**:
```
✓ Profile updated for user_id: 123456789
  tone: formal
```

## Common Use Cases

### Find User with Most Memory

```bash
# List all profiles and manually check event counts
python scripts/tools/profile_admin.py list
python scripts/tools/profile_admin.py show <user_id>
```

### Reset User After Bug

If a user reports strange behavior, reset their profile:

```bash
python scripts/tools/profile_admin.py reset <user_id>
```

### Change Persona for Testing

Test different personas for specific users:

```bash
python scripts/tools/profile_admin.py update <user_id> --persona "Jarvis-style AI assistant"
```

## Troubleshooting

### MongoDB Connection Error

```
Error: connection refused
```

**Solution**: Check MONGODB_URL environment variable and ensure MongoDB is running.

### Profile Not Found

```
Profile not found for user_id: 123
```

**Solution**: User hasn't interacted with bot yet. Profile will be auto-created on first interaction.

## Security Notes

- **No Public Access**: This is an internal tool only. Never expose to end users.
- **Audit Logging**: All admin actions are logged for security audit.
- **Confirmation Required**: Reset operation requires explicit confirmation.

## See Also

- Epic 25 Documentation: `docs/specs/epic_25/`
- Personalization Service: `src/application/personalization/`
```

---

## Testing Requirements

### CLI Tests

**File**: `tests/integration/tools/test_profile_admin.py`

```python
"""Integration tests for profile admin CLI."""

import pytest
from click.testing import CliRunner
from motor.motor_asyncio import AsyncIOMotorClient

from scripts.tools.profile_admin import cli


@pytest.fixture
async def mongo_client():
    """Provide test MongoDB client."""
    client = AsyncIOMotorClient("mongodb://localhost:27017")
    yield client
    await client.drop_database("butler_test")
    client.close()


@pytest.fixture
async def seed_test_data(mongo_client):
    """Seed test data."""
    db = mongo_client.butler_test
    await db.user_profiles.insert_one({
        "user_id": "test_123",
        "persona": "Alfred-style дворецкий",
        "language": "ru",
        "tone": "witty",
        "preferred_topics": [],
        "memory_summary": None,
        "created_at": "2025-11-18T10:00:00",
        "updated_at": "2025-11-18T10:00:00",
    })


def test_list_command(seed_test_data):
    """Test list command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    
    assert result.exit_code == 0
    assert "test_123" in result.output
    assert "Alfred-style дворецкий" in result.output


def test_show_command(seed_test_data):
    """Test show command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["show", "test_123"])
    
    assert result.exit_code == 0
    assert "test_123" in result.output
    assert "witty" in result.output


def test_reset_command_with_confirmation(seed_test_data):
    """Test reset command with confirmation."""
    runner = CliRunner()
    result = runner.invoke(cli, ["reset", "test_123"], input="y\n")
    
    assert result.exit_code == 0
    assert "Reset complete" in result.output


def test_update_command(seed_test_data):
    """Test update command."""
    runner = CliRunner()
    result = runner.invoke(cli, ["update", "test_123", "--tone", "formal"])
    
    assert result.exit_code == 0
    assert "Profile updated" in result.output
```

### Test Execution

```bash
# Integration tests
pytest tests/integration/tools/ -v

# Manual testing
python scripts/tools/profile_admin.py list
python scripts/tools/profile_admin.py show 123456789
```

---

## Acceptance Criteria

- [ ] CLI tool implemented with all commands
- [ ] Commands: list, show, reset, update
- [ ] Rich terminal output (tables, colors)
- [ ] Confirmation prompt for destructive operations
- [ ] Error handling with user-friendly messages
- [ ] Comprehensive logging
- [ ] CLI tests with ≥80% coverage
- [ ] Usage documentation complete

---

## Dependencies

- **Upstream**: TL-05 (bot integration)
- **Downstream**: TL-07 (testing & docs)

---

## Deliverables

- [ ] `scripts/tools/profile_admin.py`
- [ ] `docs/guides/profile_admin_guide.md`
- [ ] `tests/integration/tools/test_profile_admin.py`
- [ ] Requirements updated (click, rich)

---

## Next Steps

After completion:
1. Manual testing of all CLI commands
2. Documentation review
3. Code review with Tech Lead
4. Begin TL-07 (Testing, Observability, Docs)

---

**Status**: Pending  
**Estimated Effort**: 1 day  
**Priority**: Medium

