# Butler Agent API Documentation

## Overview

Butler Agent is a Telegram bot that processes natural language messages and routes them to appropriate handlers based on intent classification. The bot supports four dialog modes: TASK, DATA, REMINDERS, and IDLE.

**Telegram Interface:** Interactive bot via Telegram messages  
**Architecture:** Clean Architecture with domain, application, infrastructure, and presentation layers  
**State Management:** Finite State Machine (FSM) for conversation flow

## Dialog Modes

Butler Agent classifies user messages into one of four modes using LLM-based intent classification:

1. **TASK** - Task creation and management
2. **DATA** - Data collection (channel digests, student stats)
3. **REMINDERS** - Active reminders listing
4. **IDLE** - General conversation

### Mode Classification

Mode classification is performed by `ModeClassifier` service using Mistral-7B LLM. The classifier analyzes user messages and returns one of the four modes.

**Fallback:** If LLM is unavailable, the system defaults to `IDLE` mode for general conversation.

## TASK Mode

### Description

TASK mode handles task creation and management. Users can create tasks using natural language, and the system will parse the intent, request clarifications if needed, and create the task via MCP tools.

### Supported Operations

- **create_task**: Create a new task with title, description, and optional deadline
- **Task clarification flow**: System asks for missing information

### Example Conversations

#### Simple Task Creation

```
User: "Buy milk tomorrow"
Butler: "Task created successfully! Task ID: 507f1f77bcf86cd799439011"
```

#### Task Creation with Clarification

```
User: "Add a task"
Butler: "What would you like to name this task?"
User: "Meeting with team"
Butler: "Please provide a description for this task."
User: "Discuss project progress"
Butler: "Task created successfully! Task ID: 507f1f77bcf86cd799439011"
```

#### Task with Deadline

```
User: "Remind me to call John on Friday"
Butler: "Task created successfully! Title: Call John, Deadline: Friday, Task ID: 507f1f77bcf86cd799439011"
```

### MCP Tools Used

- `add_task`: Creates a new task in the system
- Parameters: `title` (required), `description` (optional), `deadline` (optional), `user_id` (required)

### Use Case: CreateTaskUseCase

**Location:** `src/application/usecases/create_task_usecase.py`

**Method:** `execute(user_id, message, context=None) -> TaskCreationResult`

**Parameters:**
- `user_id: int` - User identifier
- `message: str` - User message text
- `context: Optional[Dict[str, Any]]` - Dialog context data (optional)

**Returns:** `TaskCreationResult`

**TaskCreationResult Fields:**
- `created: bool` - Whether task was successfully created
- `task_id: Optional[str]` - Task ID if created successfully
- `clarification: Optional[str]` - Clarification question if more info needed
- `error: Optional[str]` - Error message if operation failed

**Example Usage:**
```python
from src.application.usecases import CreateTaskUseCase

use_case = CreateTaskUseCase(intent_orch, tool_client, mongodb)
result = await use_case.execute(
    user_id=123,
    message="Buy milk tomorrow",
    context={"previous_message": "..."}
)

if result.created:
    print(f"Task created: {result.task_id}")
elif result.clarification:
    print(f"Need clarification: {result.clarification}")
elif result.error:
    print(f"Error: {result.error}")
```

**Flow:**
1. Parse intent via `IntentOrchestrator`
2. Check if clarification is needed
3. If clarification needed, return `clarification` field
4. If complete, create task via MCP `add_task` tool
5. Return result with `task_id` on success

## DATA Mode

### Description

DATA mode handles data collection requests. Users can request channel digests or student statistics.

### Supported Operations

- **get_channels_digest**: Get digest of channel posts
- **get_student_stats**: Get student statistics for a teacher

### Example Conversations

#### Channel Digest Request

```
User: "Show me channel digests"
Butler: "📊 Channel Digest
        ────────────────
        • Python Channel: 5 new posts
          Summary: Discussion about async/await patterns...
        • JavaScript Channel: 3 new posts
          Summary: React hooks best practices..."
```

#### Student Stats Request

```
User: "What are the student statistics?"
Butler: "📈 Student Statistics
        ──────────────────
        Total Students: 25
        Active Students: 20
        Completion Rate: 80%
        Average Score: 85.5"
```

### MCP Tools Used

- `get_channel_digest`: Retrieves channel digest
  - Parameters: `user_id` (required)
  - Returns: List of channel digest dictionaries

- `get_student_stats`: Retrieves student statistics
  - Parameters: `teacher_id` (required)
  - Returns: Dictionary with statistics

### Use Case: CollectDataUseCase

**Location:** `src/application/usecases/collect_data_usecase.py`

**Methods:**

#### get_channels_digest(user_id)

**Parameters:**
- `user_id: int` - User identifier

**Returns:** `DigestResult`

**DigestResult Fields:**
- `digests: List[Dict[str, Any]]` - List of channel digest dictionaries
- `error: Optional[str]` - Error message if operation failed

**Example Usage:**
```python
from src.application.usecases import CollectDataUseCase

use_case = CollectDataUseCase(tool_client)
result = await use_case.get_channels_digest(user_id=123)

if result.digests:
    for digest in result.digests:
        print(f"Channel: {digest['channel_name']}, Posts: {digest['posts_count']}")
elif result.error:
    print(f"Error: {result.error}")
```

#### get_student_stats(teacher_id)

**Parameters:**
- `teacher_id: int` - Teacher identifier

**Returns:** `StatsResult`

**StatsResult Fields:**
- `stats: Dict[str, Any]` - Dictionary with student statistics
- `error: Optional[str]` - Error message if operation failed

**Example Usage:**
```python
from src.application.usecases import CollectDataUseCase

use_case = CollectDataUseCase(tool_client)
result = await use_case.get_student_stats(teacher_id=456)

if result.stats:
    print(f"Total students: {result.stats['total_students']}")
elif result.error:
    print(f"Error: {result.error}")
```

## REMINDERS Mode

### Description

REMINDERS mode handles listing and management of active reminders.

### Supported Operations

- **list_reminders**: List all active reminders for a user

### Example Conversations

#### List Active Reminders

```
User: "Show my reminders"
Butler: "🔔 Active Reminders
        ────────────────────
        1. Call John - Due: 2025-01-28 10:00
        2. Team meeting - Due: 2025-01-29 14:00
        3. Submit report - Due: 2025-01-30 17:00"
```

#### No Active Reminders

```
User: "What are my reminders?"
Butler: "No active reminders at the moment. You're all caught up! ✅"
```

### MCP Tools Used

- `get_active_reminders`: Lists active reminders
  - Parameters: `user_id` (required)
  - Returns: List of reminder dictionaries

## IDLE Mode

### Description

IDLE mode handles general conversation when no specific intent is detected or when the user engages in casual conversation.

### Behavior

- Uses LLM (Mistral-7B) to generate conversational responses
- Falls back to predefined responses if LLM unavailable
- Supports questions, greetings, and general chat

### Example Conversations

#### General Question

```
User: "Hello, how are you?"
Butler: "Hello! I'm doing well, thank you for asking. How can I help you today?"
```

#### Casual Conversation

```
User: "What's the weather like?"
Butler: "I don't have access to weather information, but I'd be happy to help you with tasks, reminders, or data collection. What would you like to do?"
```

#### Fallback Response (LLM Unavailable)

```
User: "Tell me a joke"
Butler: "I'm currently having trouble connecting to my language model. Please try again later, or I can help you with tasks, reminders, or data!"
```

## State Machine Reference

### DialogState Enum

**Location:** `src/domain/agents/state_machine.py`

**States:**
- `IDLE` - Initial/default state
- `TASK_CREATE_TITLE` - Task creation - collecting title
- `TASK_CREATE_DESC` - Task creation - collecting description
- `TASK_CONFIRM` - Task creation - confirmation
- `DATA_COLLECTING` - Data collection in progress
- `REMINDERS_LISTING` - Listing reminders

### DialogContext

**Location:** `src/domain/agents/state_machine.py`

**Structure:**
```python
@dataclass
class DialogContext:
    state: DialogState          # Current dialog state
    user_id: str                # User identifier
    session_id: str            # Session identifier
    data: Dict[str, Any]       # Context data storage
    step_count: int             # Step counter
```

**Methods:**
- `transition_to(new_state: DialogState)`: Transition to a new state
- `reset()`: Reset context to IDLE state
- `update_data(key: str, value: Any)`: Update context data
- `get_data(key: str, default: Any = None)`: Get context data value

### State Transitions

**IDLE → TASK_CREATE_TITLE:**
- Trigger: TASK mode detected
- Action: Begin task creation flow

**TASK_CREATE_TITLE → TASK_CREATE_DESC:**
- Trigger: Title received
- Action: Request description

**TASK_CREATE_DESC → TASK_CONFIRM:**
- Trigger: Description received
- Action: Confirm task creation

**TASK_CONFIRM → IDLE:**
- Trigger: Task confirmed/created
- Action: Return to idle state

**IDLE → DATA_COLLECTING:**
- Trigger: DATA mode detected
- Action: Begin data collection

**DATA_COLLECTING → IDLE:**
- Trigger: Data retrieved
- Action: Return to idle state

**IDLE → REMINDERS_LISTING:**
- Trigger: REMINDERS mode detected
- Action: List reminders

**REMINDERS_LISTING → IDLE:**
- Trigger: Reminders listed
- Action: Return to idle state

## Error Handling

### Error Types

Butler Agent handles errors gracefully at multiple levels:

1. **LLM Errors**: Connection timeouts, unavailable service
   - Fallback: Default to IDLE mode
   - User Message: "I'm having trouble processing your request. Let's try again."

2. **MCP Tool Errors**: Tool not found, invalid parameters
   - User Message: "Sorry, I encountered an error processing your request. Please try again later."

3. **Database Errors**: MongoDB connection failures
   - User Message: "I'm experiencing technical difficulties. Your data is safe, please try again in a moment."

4. **Handler Errors**: Unexpected exceptions in handlers
   - User Message: "Something went wrong. I'm here to help - please try rephrasing your request."

### Error Recovery Strategies

- **Automatic Recovery:**
  - Transient errors: Automatic retry with exponential backoff
  - LLM unavailable: Fallback to IDLE mode
  - Database errors: Context stored temporarily, saved when available

- **User Communication:**
  - All errors result in user-friendly messages
  - Technical details logged server-side
  - Users can retry without losing context

### Result Types Error Fields

All use case results include `error` field for error scenarios:

```python
# TaskCreationResult
result = TaskCreationResult(
    created=False,
    task_id=None,
    clarification=None,
    error="MCP tool 'add_task' not available"
)

# DigestResult
result = DigestResult(
    digests=[],
    error="Unable to fetch channel digests: Connection timeout"
)

# StatsResult
result = StatsResult(
    stats={},
    error="Student statistics not available for teacher ID 456"
)
```

## Telegram Commands

### `/start`

**Purpose:** Initialize the bot and send welcome message

**Response:**
```
Hello! I'm Butler, your personal assistant bot.

I can help you with:
• Tasks: Create and manage tasks
• Data: Get channel digests and student statistics
• Reminders: View your active reminders
• Chat: General conversation

Just send me a message and I'll help you!
```

### `/help`

**Purpose:** Display help information

**Response:**
```
Butler Bot Help
───────────────

Commands:
• /start - Start the bot
• /help - Show this help message
• /menu - Show menu options

Usage:
Just send me a message! I'll understand what you need:
• "Buy milk tomorrow" - Creates a task
• "Show channel digests" - Gets data
• "List my reminders" - Shows reminders
• "Hello" - General chat
```

### `/menu`

**Purpose:** Display menu options

**Response:**
```
📋 Menu Options
───────────────

1️⃣ Tasks
   Create and manage your tasks

2️⃣ Data
   Get channel digests and statistics

3️⃣ Reminders
   View active reminders

4️⃣ Chat
   General conversation

Just type what you need, and I'll help!
```

## Message Format

### Input Format

Users send plain text messages via Telegram. Butler Agent processes natural language and routes to appropriate handlers.

**Supported Input Types:**
- Natural language task descriptions
- Questions and commands
- Clarification responses
- General conversation

### Output Format

Butler Agent responses support Markdown formatting:

**Supported Markdown:**
- **Bold text**: `**text**`
- *Italic text*: `*text*`
- `Code blocks`: `` `code` ``
- Lists: `- item` or `• item`

**Example:**
```
**Task Created Successfully!** ✅

Task ID: `507f1f77bcf86cd799439011`
Title: Buy milk
Description: Purchase milk from store
Deadline: Tomorrow
```

**Message Length Limits:**
- Maximum: 4000 characters (Telegram limit)
- Long messages are truncated with "..." indicator

## ButlerOrchestrator API

### handle_user_message(user_id, message, session_id)

**Location:** `src/domain/agents/butler_orchestrator.py`

**Purpose:** Main entry point for message processing

**Parameters:**
- `user_id: str` - User identifier
- `message: str` - User message text
- `session_id: str` - Session identifier (format: `"{user_id}:{message_id}"`)

**Returns:** `str` - Response text to send to user

**Flow:**
1. Get or create dialog context from MongoDB
2. Classify message mode using `ModeClassifier`
3. Route to appropriate handler based on mode
4. Handler processes message and returns response
5. Save updated context to MongoDB
6. Return response text

**Example:**
```python
from src.domain.agents.butler_orchestrator import ButlerOrchestrator

orchestrator = ButlerOrchestrator(...)
response = await orchestrator.handle_user_message(
    user_id="123",
    message="Buy milk tomorrow",
    session_id="123:456"
)
print(response)  # "Task created successfully! Task ID: ..."
```

## Integration Examples

### Complete Task Creation Flow

```python
from src.presentation.bot.factory import create_butler_orchestrator

# Initialize orchestrator
orchestrator = await create_butler_orchestrator()

# User sends message
user_id = "123"
message = "Buy milk tomorrow"
session_id = f"{user_id}:{message.message_id}"

# Process message
response = await orchestrator.handle_user_message(
    user_id=user_id,
    message=message,
    session_id=session_id
)

# Send response to user
await bot.send_message(chat_id=user_id, text=response)
```

### Data Collection Flow

```python
from src.application.usecases import CollectDataUseCase
from src.infrastructure.clients.mcp_client_adapter import MCPToolClientAdapter

# Initialize use case
adapter = MCPToolClientAdapter(robust_client)
use_case = CollectDataUseCase(tool_client=adapter)

# Get channel digest
result = await use_case.get_channels_digest(user_id=123)
if result.digests:
    for digest in result.digests:
        print(f"{digest['channel_name']}: {digest['posts_count']} posts")
```

## Configuration

### Environment Variables

- `TELEGRAM_BOT_TOKEN`: Telegram bot token (required)
- `MONGODB_URL`: MongoDB connection string (default: `mongodb://localhost:27017`)
- `MISTRAL_API_URL`: Mistral API base URL (default: `http://localhost:8001`)

### Optional Configuration

- `LOG_LEVEL`: Logging level (default: `INFO`)
- `MISTRAL_TIMEOUT`: Mistral API timeout in seconds (default: `30`)
- `MISTRAL_MAX_RETRIES`: Maximum retry attempts (default: `3`)

## Testing

### Unit Tests

All components have comprehensive unit tests:
- Handler tests: `tests/unit/domain/agents/handlers/`
- Use case tests: `tests/unit/application/usecases/`
- Infrastructure tests: `tests/unit/infrastructure/`

### Integration Tests

Full workflow integration tests:
- `tests/integration/butler/test_full_message_flow.py`
- `tests/integration/butler/test_mode_transitions.py`

### E2E Tests

Complete Telegram bot workflows:
- `tests/e2e/telegram/test_butler_e2e.py`

**Run Tests:**
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/ -m e2e
```

## References

- [Architecture Documentation](ARCHITECTURE.md) - Detailed architecture overview
- [Deployment Guide](DEPLOYMENT.md) - Deployment instructions
- [Testing Documentation](TESTING.md) - Testing strategy and guidelines

