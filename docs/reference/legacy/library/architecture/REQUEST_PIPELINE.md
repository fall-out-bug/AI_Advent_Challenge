# Request Processing Pipeline

## Overview

This document describes how user requests are processed in the Butler bot, including how the system decides between RAG, MCP tools, and regular chat.

## High-Level Flow

```
User Message
    ↓
ButlerHandler (butler_handler.py)
    ↓
[Optional] Personalized Reply (if enabled)
    ↓
[Optional] Special Command Interception (digest, subscribe, etc.)
    ↓
ButlerOrchestrator.handle_user_message()
    ↓
ModeClassifier.classify() → DialogMode
    ↓
Route to Handler:
    - TASK → TaskHandler
    - DATA → DataHandler (uses MCP tools)
    - HOMEWORK_REVIEW → HomeworkHandler (uses RAG via ReviewHomeworkUseCase)
    - IDLE → ChatHandler (direct LLM)
```

## 1. Entry Point: ButlerHandler

**File**: `src/presentation/bot/handlers/butler_handler.py`

The `ButlerHandler` is the main entry point for all user messages. It performs:

1. **Personalization Check** (if enabled):
   - If personalization is enabled, it may use `PersonalizedReplyUseCase` to generate a personalized response
   - This happens BEFORE mode classification

2. **Special Command Interception**:
   - Digest requests: Extracts channel name and hours, resolves channel via `ResolveChannelNameUseCase`, auto-subscribes if needed
   - Subscribe/Unsubscribe requests: Handled directly
   - These are intercepted BEFORE orchestrator to ensure proper channel resolution

3. **Orchestrator Delegation**:
   - If not intercepted, the message is passed to `ButlerOrchestrator.handle_user_message()`

## 2. Mode Classification

**File**: `src/application/services/mode_classifier.py`

The `ModeClassifier` determines which dialog mode to use:

### Classification Strategy

1. **Hybrid Intent Classifier** (if available):
   - Uses `HybridIntentClassifier` to classify intent
   - Maps intent to `DialogMode` via `_intent_to_dialog_mode()`

2. **Keyword Matching** (fast path):
   - **HOMEWORK_REVIEW**: Keywords like "покажи домашки", "сделай ревью", "review"
   - **DATA**: Keywords like "подписк", "канал", "дайджест", "digest", "subscription"
   - **TASK**: Keywords like "создай задачу", "create task", "tasks"

3. **LLM Classification** (fallback):
   - If keyword matching fails, uses LLM with a classification prompt
   - Prompt asks LLM to classify into: TASK, DATA, HOMEWORK_REVIEW, or IDLE

### Dialog Modes

- **TASK**: Task creation and management
- **DATA**: Channel digests, subscriptions, student stats, homework status
- **HOMEWORK_REVIEW**: Homework review and listing
- **IDLE**: General conversation

## 3. Handler Routing

**File**: `src/presentation/bot/orchestrator.py`

The `ButlerOrchestrator` routes messages to appropriate handlers based on `DialogMode`:

```python
self._handlers = {
    DialogMode.TASK: task_handler,
    DialogMode.DATA: data_handler,
    DialogMode.HOMEWORK_REVIEW: homework_handler,
    DialogMode.IDLE: chat_handler,
}
```

## 4. Handler Implementations

### 4.1. DATA Handler (MCP Tools)

**File**: `src/presentation/bot/handlers/data.py`

**Purpose**: Handles data collection requests (channel digests, subscriptions, stats)

**How it works**:
1. Uses `HybridIntentClassifier` (if available) to extract intent and entities
2. Routes to specific methods based on intent:
   - `DATA_DIGEST` → `_get_channel_digest_by_name()` or `_get_channels_digest()`
   - `DATA_SUBSCRIPTION_ADD` → `_subscribe_to_channel()`
   - `DATA_SUBSCRIPTION_REMOVE` → `_unsubscribe_by_name()`
   - `DATA_SUBSCRIPTION_LIST` → `_list_channels()`
   - `DATA_STATS` → `_get_student_stats()`
   - `DATA_HW_STATUS` → `_get_hw_status()`
3. **MCP Tools Used**:
   - `get_channel_digest_by_name`: Get digest for specific channel
   - `get_channels_digest`: Get digests for all channels
   - `add_channel`: Subscribe to channel
   - `delete_channel`: Unsubscribe from channel
   - `list_channels`: List user's subscriptions
   - `get_channel_metadata`: Get channel metadata for matching
4. Calls MCP tools via `ToolClientProtocol` (MCP client)
5. Formats and returns response

**Key Point**: DATA handler uses **MCP tools** (not RAG) to interact with MongoDB and Telegram API.

### 4.2. HOMEWORK_REVIEW Handler (RAG)

**File**: `src/presentation/bot/handlers/homework.py`

**Purpose**: Handles homework listing and review

**How it works**:
1. Routes based on message:
   - List request → `_handle_list()` → `ListHomeworkSubmissionsUseCase`
   - Review request → `_handle_review()` → `ReviewHomeworkUseCase`
2. **ReviewHomeworkUseCase** (RAG):
   - Uses RAG to retrieve relevant context from vector database
   - Generates review report using LLM with retrieved context
   - Returns markdown report
3. Formats response (list or markdown file)

**Key Point**: HOMEWORK_REVIEW handler uses **RAG** (Retrieval-Augmented Generation) via `ReviewHomeworkUseCase`.

### 4.3. TASK Handler

**File**: `src/presentation/bot/handlers/task.py`

**Purpose**: Handles task creation and management

**How it works**:
1. Uses `CreateTaskUseCase` to process task requests
2. Manages FSM (Finite State Machine) for multi-step task creation
3. Returns task creation result

**Key Point**: TASK handler uses **use cases** (not RAG, not MCP tools directly).

### 4.4. IDLE Handler (Chat)

**File**: `src/presentation/bot/handlers/chat.py`

**Purpose**: Handles general conversation

**How it works**:
1. Uses LLM directly with a simple chat prompt
2. No RAG, no MCP tools, just direct LLM generation
3. Cleans response to remove artifacts

**Key Point**: IDLE handler uses **direct LLM** (no RAG, no MCP tools).

## Decision Tree

```
User Message
    ↓
Is it a special command? (digest, subscribe, etc.)
    ├─ Yes → Handle directly in ButlerHandler
    └─ No → Continue
        ↓
ModeClassifier.classify()
    ↓
What mode?
    ├─ DATA → DataHandler → MCP Tools (MongoDB, Telegram API)
    ├─ HOMEWORK_REVIEW → HomeworkHandler → RAG (vector DB) → LLM
    ├─ TASK → TaskHandler → Use Cases (MongoDB via repositories)
    └─ IDLE → ChatHandler → Direct LLM (no retrieval, no tools)
```

## When to Use What?

### RAG (Retrieval-Augmented Generation)
- **Used in**: `HOMEWORK_REVIEW` mode
- **Purpose**: Retrieve relevant context from vector database for homework review
- **Implementation**: `ReviewHomeworkUseCase` uses embedding search to find relevant code/documentation

### MCP Tools
- **Used in**: `DATA` mode
- **Purpose**: Interact with external systems (MongoDB, Telegram API)
- **Implementation**: `DataHandler` calls MCP tools via `ToolClientProtocol`
- **Examples**: `get_channel_digest_by_name`, `add_channel`, `list_channels`

### Direct LLM
- **Used in**: `IDLE` mode (chat)
- **Purpose**: General conversation without retrieval or tools
- **Implementation**: `ChatHandler` calls LLM directly with simple prompt

### Use Cases (Domain Logic)
- **Used in**: `TASK` mode
- **Purpose**: Business logic for task management
- **Implementation**: `TaskHandler` uses `CreateTaskUseCase` which interacts with repositories

## Personalization Integration

If personalization is enabled:
1. `ButlerHandler` checks if personalization should be used
2. If yes, `PersonalizedReplyUseCase` is called BEFORE orchestrator
3. This allows personalized responses for any mode
4. Personalization uses:
   - User profile (persona, tone, language, interests)
   - User memory (conversation history)
   - LLM to generate personalized response

## Summary

- **RAG**: Used for homework review (retrieves context from vector DB)
- **MCP Tools**: Used for data operations (channel digests, subscriptions, stats)
- **Direct LLM**: Used for general chat (IDLE mode)
- **Use Cases**: Used for task management (domain logic)

The decision is made by `ModeClassifier` based on:
1. Hybrid intent classifier (if available)
2. Keyword matching (fast path)
3. LLM classification (fallback)
