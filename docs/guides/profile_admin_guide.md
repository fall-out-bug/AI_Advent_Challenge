# Profile Admin CLI Guide

## Overview

Internal CLI tool for managing user personalization profiles and memory.

## Installation

```bash
# Install dependencies (already in pyproject.toml)
poetry install

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

