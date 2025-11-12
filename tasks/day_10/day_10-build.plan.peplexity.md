<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# Day 10: Advanced MCP Orchestration System - Technical Specification

## 🎯 Project Overview

**Objective**: Build a production-ready MCP-based development assistant system with StarCoder2-7B server and Mistral-7B intelligent agent for complete code development lifecycle.

**Architecture**:

```
┌─────────────────────┐    MCP Protocol    ┌──────────────────────┐
│   Mistral Agent     │◄──────────────────►│  StarCoder MCP       │
│   (Chat Interface)  │   JSON-RPC 2.0     │  Server (Docker)     │
│                     │                    │                      │
│ • Intent parsing    │                    │ • Code generation    │
│ • Tool discovery    │                    │ • Code review        │
│ • Chain execution   │                    │ • Test generation    │
│ • Context memory    │                    │ • Code formatting    │
│ • Clarification     │                    │ • Complexity analysis│
└─────────────────────┘                    │ • Task formalization │
                                           └──────────────────────┘
```


***

## 📦 Technical Stack

### MCP Server

- **Model**: StarCoder2-7B-Instruct (4-bit quantized, ~6-7GB VRAM)
- **Framework**: FastMCP (Python MCP SDK)
- **Runtime**: Docker container with NVIDIA GPU support
- **Transport**: stdio (local) with future HTTP support


### Agent Client

- **Model**: Mistral-7B-Instruct-v0.2 (4-bit quantized)
- **Framework**: Python async/await
- **Deployment**: Local process
- **MCP Client**: Python SDK stdio client


### Infrastructure

- Docker + docker-compose
- CUDA 11.8+ runtime
- Python 3.10+
- 16GB+ GPU VRAM recommended

***

## 📋 Component 1: StarCoder MCP Server

### 1.1 Core Tools Implementation

**File**: `mcp_server/src/server/starcoder_server.py`

```python
from mcp.server.fastmcp import FastMCP, Context
from transformers import AutoModelForCausalLM, AutoTokenizer
import logging

mcp = FastMCP(
    "StarCoder Development Assistant",
    instructions="""
    Production MCP server for code development tasks using StarCoder2-7B.
    Provides tools for task formalization, code generation, review, testing,
    formatting, and complexity analysis.
    """
)

# Tool 1: Task Formalization
@mcp.tool()
async def formalize_task(
    informal_request: str,
    context: str = "",
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Convert informal user request into structured development plan.

    Args:
        informal_request: Natural language description of task
        context: Additional context or constraints
        ctx: MCP context for logging

    Returns:
        {
            "formalized_description": str,
            "requirements": list[str],
            "steps": list[str],
            "estimated_complexity": str
        }
    """
    # Implementation with StarCoder
    pass

# Tool 2: Code Generation
@mcp.tool()
async def generate_code(
    description: str,
    language: str = "python",
    style: str = "pep8",
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Generate code based on description using StarCoder2-7B.

    Args:
        description: Clear description of code requirements
        language: Target programming language (default: python)
        style: Code style guide (default: pep8)
        ctx: MCP context

    Returns:
        {
            "code": str,
            "language": str,
            "explanation": str,
            "dependencies": list[str]
        }
    """
    pass

# Tool 3: Test Generation
@mcp.tool()
async def generate_tests(
    code: str,
    test_framework: str = "pytest",
    coverage_target: int = 80,
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Generate comprehensive tests for provided code.

    Args:
        code: Source code to generate tests for
        test_framework: Testing framework (pytest, unittest, etc.)
        coverage_target: Target coverage percentage
        ctx: MCP context

    Returns:
        {
            "test_code": str,
            "test_count": int,
            "coverage_estimate": int,
            "test_cases": list[str]
        }
    """
    pass

# Tool 4: Code Review
@mcp.tool()
async def review_code(
    code: str,
    style_guide: str = "pep8",
    focus_areas: list[str] = None,
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Perform comprehensive code review.

    Args:
        code: Code to review
        style_guide: Style guidelines to check against
        focus_areas: Specific areas to focus on (security, performance, etc.)
        ctx: MCP context

    Returns:
        {
            "overall_score": int,  # 0-100
            "issues": list[dict],
            "suggestions": list[str],
            "compliments": list[str],
            "refactored_code": str
        }
    """
    pass

# Tool 5: Code Formatting
@mcp.tool()
def format_code(
    code: str,
    formatter: str = "black",
    line_length: int = 100,
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Format code according to style guidelines.

    Args:
        code: Code to format
        formatter: Formatter to use (black, autopep8, etc.)
        line_length: Maximum line length
        ctx: MCP context

    Returns:
        {
            "formatted_code": str,
            "changes_made": int,
            "formatter_used": str
        }
    """
    pass

# Tool 6: Complexity Analysis
@mcp.tool()
def analyze_complexity(
    code: str,
    detailed: bool = True,
    ctx: Context | None = None
) -> dict[str, Any]:
    """
    Analyze code complexity metrics.

    Args:
        code: Code to analyze
        detailed: Include detailed analysis
        ctx: MCP context

    Returns:
        {
            "cyclomatic_complexity": int,
            "cognitive_complexity": int,
            "lines_of_code": int,
            "maintainability_index": float,
            "recommendations": list[str]
        }
    """
    pass
```


### 1.2 MCP Resources Implementation

**File**: `mcp_server/src/resources/prompts.py`

```python
@mcp.resource("prompts://python-developer")
def get_python_developer_prompt() -> str:
    """
    Specialized prompt for Python development tasks.
    Emphasizes Pythonic patterns, type hints, and best practices.
    """
    return """
    You are an expert Python developer specializing in:
    - Clean, Pythonic code following PEP 8
    - Type hints and static typing
    - Comprehensive docstrings (Google style)
    - Error handling and edge cases
    - Performance optimization
    - Modern Python 3.10+ features
    """

@mcp.resource("prompts://architect")
def get_architect_prompt() -> str:
    """System architecture and design-focused prompt."""
    return """
    You are a senior software architect focusing on:
    - SOLID principles and design patterns
    - Scalable system architecture
    - Clean Architecture layers
    - API design best practices
    - Performance and security considerations
    """

@mcp.resource("prompts://technical-writer")
def get_technical_writer_prompt() -> str:
    """Documentation and technical writing prompt."""
    return """
    You are a technical documentation specialist:
    - Clear, concise technical writing
    - Comprehensive API documentation
    - Usage examples and tutorials
    - Architecture diagrams
    - Troubleshooting guides
    """

@mcp.resource("config://coding-standards")
def get_coding_standards() -> str:
    """Coding standards and best practices configuration."""
    return json.dumps({
        "python": {
            "style": "pep8",
            "line_length": 100,
            "type_hints": "required",
            "docstrings": "google",
            "complexity_limit": 10
        }
    })

@mcp.resource("templates://project-structure")
def get_project_structure_template() -> str:
    """Standard project structure templates."""
    return """
    project/
    ├── src/
    │   ├── __init__.py
    │   ├── domain/
    │   ├── application/
    │   └── infrastructure/
    ├── tests/
    ├── docs/
    ├── pyproject.toml
    └── README.md
    """
```


### 1.3 Dynamic Prompts

**File**: `mcp_server/src/prompts/dynamic.py`

```python
@mcp.prompt("code-review")
def code_review_prompt(code: str, language: str, style: str) -> str:
    """Dynamic context-aware code review prompt."""
    return f"""
    Review this {language} code following {style} guidelines:

    Code:
    ```
    {code}
    ```

    Provide:
    1. Overall quality score (0-100)
    2. Issues found (categorized by severity)
    3. Improvement suggestions
    4. Security concerns
    5. Performance considerations
    """

@mcp.prompt("test-generation")
def test_generation_prompt(code: str, framework: str) -> str:
    """Dynamic test generation prompt."""
    return f"""
    Generate comprehensive {framework} tests for:

    {code}

    Include:
    - Unit tests for all functions
    - Edge case testing
    - Error handling tests
    - Integration tests where applicable
    - Mocking for external dependencies
    """
```


***

## 📋 Component 2: Mistral Agent Client

### 2.1 Chat Orchestrator

**File**: `mistral_agent/src/orchestrator/chat_orchestrator.py`

```python
import asyncio
from typing import Any
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

class ChatOrchestrator:
    """
    Main orchestrator for Mistral agent interacting with MCP server.
    Handles intent parsing, tool discovery, execution planning, and conversation.
    """

    def __init__(self, mcp_server_command: str, mcp_server_args: list[str]):
        self.server_params = StdioServerParameters(
            command=mcp_server_command,
            args=mcp_server_args
        )
        self.conversation_memory = []
        self.available_tools = {}
        self.available_resources = {}
        self.available_prompts = {}
        self.last_code = None
        self.last_tests = None
        self.last_review = None

    async def initialize(self):
        """Initialize connection and discover capabilities."""
        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Discover tools
                tools_response = await session.list_tools()
                self.available_tools = {
                    tool.name: tool for tool in tools_response.tools
                }

                # Discover resources
                resources_response = await session.list_resources()
                self.available_resources = {
                    res.uri: res for res in resources_response.resources
                }

                # Discover prompts
                prompts_response = await session.list_prompts()
                self.available_prompts = {
                    prompt.name: prompt for prompt in prompts_response.prompts
                }

    async def handle_user_message(self, message: str) -> str:
        """
        Process user message through complete workflow:
        1. Parse intent
        2. Ask clarifying questions if needed
        3. Generate execution plan
        4. Execute tool chain
        5. Return formatted response
        """
        # Add to conversation memory
        self.conversation_memory.append({"role": "user", "content": message})

        # Parse intent using Mistral
        intent = await self._parse_intent(message)

        # Check if clarification needed
        if intent.get("needs_clarification"):
            questions = await self._generate_clarifying_questions(intent)
            return questions

        # Generate execution plan
        plan = await self._generate_execution_plan(intent)

        # Execute tool chain
        results = await self._execute_plan(plan)

        # Format response
        response = await self._format_response(results)

        self.conversation_memory.append({"role": "assistant", "content": response})

        return response

    async def _parse_intent(self, message: str) -> dict[str, Any]:
        """
        Use Mistral to parse user intent and map to available tools.

        Returns:
            {
                "primary_goal": str,
                "tools_needed": list[str],
                "parameters": dict,
                "needs_clarification": bool,
                "unclear_aspects": list[str]
            }
        """
        # Build prompt with available tools
        tools_info = "\n".join([
            f"- {name}: {tool.description}"
            for name, tool in self.available_tools.items()
        ])

        prompt = f"""
        Available MCP tools:
        {tools_info}

        Conversation history:
        {self._format_history()}

        User request: "{message}"

        Analyze the request and respond with JSON:
        {{
            "primary_goal": "what user wants to achieve",
            "tools_needed": ["tool1", "tool2"],
            "parameters": {{}},
            "needs_clarification": false,
            "unclear_aspects": []
        }}

        Only return valid JSON, no explanations.
        """

        # Call local Mistral model
        intent_json = await self._call_mistral(prompt)
        return json.loads(intent_json)

    async def _generate_clarifying_questions(self, intent: dict) -> str:
        """Generate questions for unclear aspects."""
        unclear = intent.get("unclear_aspects", [])
        prompt = f"""
        User request has unclear aspects: {unclear}

        Generate 1-3 specific clarifying questions to help understand:
        - Exact requirements
        - Constraints or preferences
        - Expected behavior

        Be concise and specific.
        """
        return await self._call_mistral(prompt)

    async def _generate_execution_plan(self, intent: dict) -> list[dict]:
        """
        Generate step-by-step execution plan.

        Returns:
            [
                {"tool": "formalize_task", "args": {...}},
                {"tool": "generate_code", "args": {...}},
                {"tool": "review_code", "args": {...}}
            ]
        """
        tools_needed = intent.get("tools_needed", [])

        prompt = f"""
        User wants: {intent['primary_goal']}
        Available tools: {tools_needed}

        Create execution plan as JSON array:
        [
            {{"tool": "tool_name", "args": {{...}}}},
            ...
        ]

        Rules:
        - Use results from previous steps in subsequent steps
        - Reference previous results as: "{{prev_result}}"
        - Only return JSON array

        Conversation context:
        {self._format_history()}
        """

        plan_json = await self._call_mistral(prompt)
        return json.loads(plan_json)

    async def _execute_plan(self, plan: list[dict]) -> list[dict]:
        """Execute tool chain sequentially with state passing."""
        results = []

        async with stdio_client(self.server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                for step in plan:
                    tool_name = step["tool"]
                    args = step["args"]

                    # Substitute previous results
                    args = self._substitute_previous_results(args, results)

                    # Call tool
                    result = await session.call_tool(tool_name, args)

                    # Extract and store result
                    result_data = self._extract_result_data(result)
                    results.append({
                        "tool": tool_name,
                        "result": result_data
                    })

                    # Store in state for future reference
                    if tool_name == "generate_code":
                        self.last_code = result_data.get("code")
                    elif tool_name == "generate_tests":
                        self.last_tests = result_data.get("test_code")
                    elif tool_name == "review_code":
                        self.last_review = result_data

        return results

    async def _call_mistral(self, prompt: str) -> str:
        """Call local Mistral-7B model."""
        # Implementation with transformers or API
        pass

    def _format_history(self) -> str:
        """Format conversation history for context."""
        return "\n".join([
            f"{msg['role']}: {msg['content']}"
            for msg in self.conversation_memory[-5:]  # Last 5 messages
        ])

    def _substitute_previous_results(
        self, args: dict, results: list[dict]
    ) -> dict:
        """Substitute placeholders with actual results."""
        for key, value in args.items():
            if value == "{prev_result}" and results:
                # Use result from previous step
                prev_result = results[-1]["result"]
                if "code" in prev_result:
                    args[key] = prev_result["code"]
                elif "test_code" in prev_result:
                    args[key] = prev_result["test_code"]
        return args

    def _extract_result_data(self, mcp_result) -> dict:
        """Extract data from MCP result."""
        from mcp.types import TextContent
        result_data = {}
        for content in mcp_result.content:
            if isinstance(content, TextContent):
                try:
                    result_data = json.loads(content.text)
                except:
                    result_data = {"text": content.text}
        return result_data

    async def _format_response(self, results: list[dict]) -> str:
        """Format execution results for user."""
        prompt = f"""
        Execution results:
        {json.dumps(results, indent=2)}

        Format a clear, helpful response for the user summarizing:
        - What was done
        - Key results
        - Any recommendations or next steps

        Be concise but informative.
        """
        return await self._call_mistral(prompt)
```


***

## 📋 Component 3: Docker Infrastructure

### 3.1 MCP Server Dockerfile

**File**: `mcp_server/Dockerfile`

```dockerfile
FROM nvidia/cuda:11.8.0-runtime-ubuntu22.04

# Set environment
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1

# Install Python and dependencies
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3-pip \
    git \
    && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy requirements
COPY requirements.txt .

# Install Python packages
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/
COPY config/ ./config/

# Create directories
RUN mkdir -p /app/models /app/logs

# Expose MCP port
EXPOSE 8004

# Health check
HEALTHCHECK --interval=30s --timeout=10s --retries=3 \
    CMD python3 -c "import requests; requests.get('http://localhost:8004/health', timeout=5)"

# Run server
CMD ["python3", "src/server/starcoder_server.py"]
```


### 3.2 Requirements

**File**: `mcp_server/requirements.txt`

```txt
# MCP SDK
mcp>=1.0.0

# Model inference
transformers>=4.35.0
torch>=2.1.0
accelerate>=0.24.0
bitsandbytes>=0.41.0

# Utilities
pydantic>=2.0.0
pydantic-settings>=2.0.0
pyyaml>=6.0

# Code analysis
radon>=6.0.0
black>=23.0.0
pylint>=3.0.0

# Logging
python-json-logger>=2.0.0

# HTTP (future)
fastapi>=0.104.0
uvicorn>=0.24.0
```


### 3.3 Docker Compose

**File**: `docker-compose.yml`

```yaml
version: '3.8'

services:
  starcoder-mcp:
    build:
      context: ./mcp_server
      dockerfile: Dockerfile
    container_name: starcoder-mcp-day10
    ports:
      - "8004:8004"
    environment:
      - MODEL_NAME=starcoder2-7b-instruct
      - CUDA_VISIBLE_DEVICES=0
      - MAX_LENGTH=4096
      - DEVICE=cuda
      - LOG_LEVEL=INFO
    volumes:
      - ./mcp_server/models:/app/models
      - ./mcp_server/logs:/app/logs
      - ./mcp_server/config:/app/config
    deploy:
      resources:
        limits:
          memory: 20G
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "python3", "-c", "import requests; requests.get('http://localhost:8004/health')"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 60s
```


***

## 📋 Component 4: Configuration Files

### 4.1 Server Configuration

**File**: `mcp_server/config/server_config.yaml`

```yaml
server:
  name: "StarCoder Development Assistant"
  version: "1.0.0"
  host: "0.0.0.0"
  port: 8004
  transport: "stdio"  # Future: "http"

model:
  name: "bigcode/starcoder2-7b"
  revision: "main"
  device: "cuda"
  device_map: "auto"
  torch_dtype: "bfloat16"
  load_in_4bit: true
  max_length: 4096
  temperature: 0.1
  top_p: 0.95
  do_sample: true

tools:
  enabled:
    - formalize_task
    - generate_code
    - generate_tests
    - review_code
    - format_code
    - analyze_complexity

  # Tool-specific settings
  code_generation:
    max_new_tokens: 2048
    stop_sequences: ", "\n\n\n"]

  code_review:
    severity_levels: ["critical", "major", "minor", "info"]
    max_issues: 50

resources:
  prompts_dir: "./src/resources/prompts"
  templates_dir: "./src/resources/templates"
  cache_enabled: true

logging:
  level: "INFO"
  format: "json"
  file: "/app/logs/server.log"
  max_size: "100MB"
  backup_count: 5

performance:
  max_concurrent_requests: 5
  timeout_seconds: 60
  enable_gpu_optimization: true

# Future: horizontal scaling support
scaling:
  enabled: false
  replicas: 1
  load_balancer: "round-robin"
```


### 4.2 Agent Configuration

**File**: `mistral_agent/config/agent_config.yaml`

```yaml
agent:
  name: "Development Orchestrator"
  version: "1.0.0"
  model: "mistral-7b-instruct-v0.2"
  device: "cuda"
  load_in_4bit: true
  temperature: 0.2
  max_tokens: 2048
  top_p: 0.9

mcp:
  servers:
    - name: "starcoder"
      command: "python"
      args: ["mcp_server/src/server/starcoder_server.py"]
      timeout: 60
      retry_attempts: 3
      retry_delay: 5

conversation:
  memory_size: 10  # Keep last N messages
  context_window: 4000  # Max tokens for context
  save_sessions: true
  session_dir: "./sessions"

clarification:
  enabled: true
  max_questions: 3
  confidence_threshold: 0.7
  ask_when_ambiguous: true

planning:
  max_steps: 10
  allow_loops: false
  optimize_chains: true

logging:
  level: "INFO"
  file: "./logs/agent.log"
  console: true
```


***

## 📋 Component 5: Usage Examples \& Testing

### 5.1 Example Usage Script

**File**: `examples/demo_workflow.py`

```python
import asyncio
from mistral_agent.src.orchestrator.chat_orchestrator import ChatOrchestrator

async def main():
    """Demonstrate complete workflow."""

    # Initialize orchestrator
    orchestrator = ChatOrchestrator(
        mcp_server_command="python",
        mcp_server_args=["mcp_server/src/server/starcoder_server.py"]
    )

    await orchestrator.initialize()

    # Example 1: Simple code generation
    print("=" * 70)
    print("Example 1: Generate fibonacci function")
    print("=" * 70)
    response = await orchestrator.handle_user_message(
        "Create a function to calculate fibonacci numbers"
    )
    print(response)

    # Example 2: Code with tests
    print("\n" + "=" * 70)
    print("Example 2: Generate and test code")
    print("=" * 70)
    response = await orchestrator.handle_user_message(
        "Write tests for the fibonacci function"
    )
    print(response)

    # Example 3: Complex workflow
    print("\n" + "=" * 70)
    print("Example 3: Complete development cycle")
    print("=" * 70)
    response = await orchestrator.handle_user_message(
        "Create a REST API endpoint for user management, "
        "write tests, and review the code"
    )
    print(response)

if __name__ == "__main__":
    asyncio.run(main())
```


### 5.2 Interactive Chat

**File**: `mistral_agent/src/cli/interactive_chat.py`

```python
import asyncio
from mistral_agent.src.orchestrator.chat_orchestrator import ChatOrchestrator

async def interactive_chat():
    """Interactive chat loop."""

    orchestrator = ChatOrchestrator(
        mcp_server_command="python",
        mcp_server_args=["mcp_server/src/server/starcoder_server.py"]
    )

    await orchestrator.initialize()

    print("=" * 70)
    print("Development Assistant - Interactive Mode")
    print("=" * 70)
    print("Commands:")
    print("  /help    - Show available commands")
    print("  /tools   - List available MCP tools")
    print("  /history - Show conversation history")
    print("  /clear   - Clear conversation")
    print("  /exit    - Exit chat")
    print("=" * 70)

    while True:
        try:
            user_input = input("\nYou: ").strip()

            if not user_input:
                continue

            if user_input == "/exit":
                print("Goodbye!")
                break
            elif user_input == "/help":
                print_help()
                continue
            elif user_input == "/tools":
                print_tools(orchestrator.available_tools)
                continue
            elif user_input == "/history":
                print_history(orchestrator.conversation_memory)
                continue
            elif user_input == "/clear":
                orchestrator.conversation_memory.clear()
                print("Conversation cleared.")
                continue

            # Process message
            response = await orchestrator.handle_user_message(user_input)
            print(f"\nAssistant: {response}")

        except KeyboardInterrupt:
            print("\n\nGoodbye!")
            break
        except Exception as e:
            print(f"\nError: {e}")

def print_help():
    print("\nAvailable features:")
    print("- Generate code from descriptions")
    print("- Review and improve existing code")
    print("- Generate tests for code")
    print("- Format code according to standards")
    print("- Analyze code complexity")
    print("- Formalize task requirements")

def print_tools(tools: dict):
    print("\nAvailable MCP tools:")
    for name, tool in tools.items():
        print(f"- {name}: {tool.description}")

def print_history(history: list):
    print("\nConversation history:")
    for msg in history:
        role = msg["role"].capitalize()
        content = msg["content"][:100] + "..." if len(msg["content"]) > 100 else msg["content"]
        print(f"{role}: {content}")

if __name__ == "__main__":
    asyncio.run(interactive_chat())
```


***

## 📋 Component 6: Makefile for Development

**File**: `Makefile`

```makefile
.PHONY: help install install-dev setup-server setup-agent start-server start-agent \
        test test-server test-agent lint format clean docker-build docker-up docker-down \
        logs demo

help:
	@echo "Day 10: Advanced MCP Orchestration System"
	@echo ""
	@echo "Available commands:"
	@echo "  make install        - Install all dependencies"
	@echo "  make install-dev    - Install with dev dependencies"
	@echo "  make setup-server   - Setup MCP server"
	@echo "  make setup-agent    - Setup Mistral agent"
	@echo "  make start-server   - Start MCP server locally"
	@echo "  make start-agent    - Start agent CLI"
	@echo "  make test           - Run all tests"
	@echo "  make lint           - Run linters"
	@echo "  make format         - Format code"
	@echo "  make docker-build   - Build Docker images"
	@echo "  make docker-up      - Start Docker services"
	@echo "  make docker-down    - Stop Docker services"
	@echo "  make logs           - View Docker logs"
	@echo "  make demo           - Run demo workflow"
	@echo "  make clean          - Clean up"

install:
	cd mcp_server && pip install -r requirements.txt
	cd mistral_agent && pip install -r requirements.txt

install-dev:
	cd mcp_server && pip install -r requirements-dev.txt
	cd mistral_agent && pip install -r requirements-dev.txt

setup-server:
	mkdir -p mcp_server/models mcp_server/logs
	cd mcp_server && python scripts/download_model.py

setup-agent:
	mkdir -p mistral_agent/logs mistral_agent/sessions

start-server:
	cd mcp_server && python src/server/starcoder_server.py

start-agent:
	cd mistral_agent && python src/cli/interactive_chat.py

test:
	cd mcp_server && pytest tests/ -v --cov=src
	cd mistral_agent && pytest tests/ -v --cov=src

test-server:
	cd mcp_server && pytest tests/ -v

test-agent:
	cd mistral_agent && pytest tests/ -v

lint:
	cd mcp_server && flake8 src tests
	cd mistral_agent && flake8 src tests
	cd mcp_server && mypy src
	cd mistral_agent && mypy src

format:
	cd mcp_server && black src tests && isort src tests
	cd mistral_agent && black src tests && isort src tests

docker-build:
	docker-compose build

docker-up:
	docker-compose up -d
	@echo "Waiting for server to be ready..."
	@sleep 10
	docker-compose logs starcoder-mcp

docker-down:
	docker-compose down

logs:
	docker-compose logs -f starcoder-mcp

demo:
	python examples/demo_workflow.py

clean:
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name '*.pyc' -delete
	find . -type d -name .pytest_cache -exec rm -rf {} +
	find . -type d -name .mypy_cache -exec rm -rf {} +
	rm -rf mcp_server/logs/* mistral_agent/logs/*
```


***

## 📋 Success Criteria

### Functional Requirements

- [ ] MCP server exposes 6 tools, 5+ resources, 3+ prompts
- [ ] Agent discovers tools dynamically via tools/list
- [ ] Single-step workflows execute correctly
- [ ] Multi-step workflows with 3+ tool chains work
- [ ] Clarifying questions generated when needed
- [ ] Conversation memory persists across turns
- [ ] Session history saved to disk


### Technical Requirements

- [ ] Docker deployment functional
- [ ] StarCoder2-7B loads in <60s
- [ ] Tool execution completes in <30s
- [ ] Memory usage <16GB VRAM
- [ ] Agent responds in <5s
- [ ] 80%+ test coverage
- [ ] Type hints on all functions
- [ ] Comprehensive logging


### Performance Requirements

- [ ] Tool discovery: <200ms
- [ ] Intent parsing: <3s
- [ ] Code generation: <30s
- [ ] Concurrent requests: 3+
- [ ] No memory leaks after 100 requests


### Quality Requirements

- [ ] PEP 8 compliance
- [ ] All mypy checks passing
- [ ] No critical security issues
- [ ] Error handling comprehensive
- [ ] Documentation complete

***

## 🚀 Implementation Timeline

### Phase 1: Foundation (Day 1 - 8 hours)

- [ ] Setup project structure
- [ ] Implement 3 basic MCP tools (formalize, generate, review)
- [ ] Basic Docker setup
- [ ] Initial testing


### Phase 2: Complete MCP Server (Day 2 - 8 hours)

- [ ] Implement remaining 3 tools (test, format, analyze)
- [ ] Add resources and prompts
- [ ] Comprehensive error handling
- [ ] Docker optimization


### Phase 3: Mistral Agent (Day 3 - 10 hours)

- [ ] Core orchestrator implementation
- [ ] Intent parsing with Mistral
- [ ] MCP client integration
- [ ] Tool discovery and execution


### Phase 4: Advanced Features (Day 4 - 6 hours)

- [ ] Clarifying questions logic
- [ ] Multi-step workflow planning
- [ ] Conversation memory
- [ ] Session persistence


### Phase 5: Testing \& Polish (Day 5 - 4 hours)

- [ ] Comprehensive testing
- [ ] Documentation
- [ ] Demo examples
- [ ] Performance optimization

**Total Estimated Time**: 36 hours (5 working days)

***

## 📝 Notes

- **GPU**: 16GB VRAM sufficient for 4-bit quantized models
- **Sessions**: Saved as JSON in `mistral_agent/sessions/`
- **Auth**: Not required for local deployment
- **Monitoring**: Basic metrics via logging, expandable to Prometheus
- **Scaling**: Architecture supports future horizontal scaling

***

**Status**: Ready for implementation with Cursor AI assistance
