"""MCP-aware agent implementation.

Following Python Zen:
- Simple is better than complex
- Explicit is better than implicit
- Readability counts
"""

import json
import logging
import time
from typing import Any, Dict, Optional

from shared_package.clients.unified_client import UnifiedModelClient

from src.domain.agents.builders.prompt_builder import PromptBuilder
from src.domain.agents.builders.response_builder import ResponseBuilder
from src.domain.agents.formatters.tool_result_formatter import ToolResultFormatter
from src.domain.agents.prompts import DECISION_ONLY_SYSTEM_PROMPT
from src.domain.agents.schemas import AgentRequest, AgentResponse, ToolMetadata
from src.domain.agents.services.channel_resolver import ChannelResolver
from src.domain.agents.tools_registry import TOOLS_SCHEMA
from src.domain.input_processing.russian_parser import RussianInputParser
from src.domain.parsers.tool_call_parser import ToolCallParser
from src.infrastructure.config.settings import get_settings
from src.infrastructure.llm.openai_chat_client import OpenAIChatClient
from src.presentation.mcp.client import MCPClientProtocol
from src.presentation.mcp.tools_registry import MCPToolsRegistry

try:
    from src.infrastructure.monitoring.agent_metrics import AgentMetrics, LLMMetrics

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False

logger = logging.getLogger(__name__)


class MCPAwareAgent:
    """Agent aware of MCP tools.

    Process user requests using LLM with awareness of available MCP tools.
    Automatically discovers tools and uses them based on LLM decisions.
    """

    # Default configuration constants
    DEFAULT_MODEL_NAME = "mistral-7b-instruct"
    DEFAULT_MAX_TOKENS = 2048
    DEFAULT_TEMPERATURE = 0.2

    def __init__(
        self,
        mcp_client: MCPClientProtocol,
        llm_client: UnifiedModelClient,
        model_name: str = DEFAULT_MODEL_NAME,
        max_tokens: int = DEFAULT_MAX_TOKENS,
        temperature: float = DEFAULT_TEMPERATURE,
    ):
        """Initialize MCP-aware agent.

        Args:
            mcp_client: MCP client for tool discovery and execution
            llm_client: LLM client for generating responses
            model_name: Model name to use
            max_tokens: Maximum tokens for generation
            temperature: Generation temperature
        """
        self.mcp_client = mcp_client
        self.llm_client = llm_client
        self.model_name = model_name
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.registry = MCPToolsRegistry(mcp_client)
        self.chat_client = OpenAIChatClient()
        self._tool_trace: list[str] = []
        self._formatter = ToolResultFormatter()
        self._channel_resolver = ChannelResolver(mcp_client)
        self._prompt_builder = PromptBuilder()

    async def process(self, request: AgentRequest) -> AgentResponse:
        """Process user request via 3-stage pipeline: decision → execution → formatting.

        Args:
            request: Agent request with user message.

        Returns:
            Agent response with result or error.
        """
        start_time = time.time()
        tokens_used = 0
        reasoning_parts: list[str] = []

        async def _run_flow(with_tools: list[ToolMetadata]) -> AgentResponse:
            # Reset tool trace for this request
            self._tool_trace = []
            # Stage 0: Parse Russian without model to aid fallback
            parsed_intent = None
            try:
                parsed_intent = self._parse_user_intent(request.message)
            except Exception:
                parsed_intent = None
            reasoning_parts.append(
                f"Parsed intent: {json.dumps(parsed_intent or {}, ensure_ascii=False)}"
            )

            # Stage 1a: Decision via DECISION_ONLY prompt (uses llm_client)
            reasoning_parts.append("Stage: decision (json parsing)")
            decision = await self._stage_decision(request)
            tool_calls = []
            if decision and isinstance(decision, dict):
                tool_calls = [
                    {
                        "id": "dec_json_1",
                        "type": "function",
                        "function": {
                            "name": decision.get("tool", ""),
                            "arguments": json.dumps(
                                decision.get("params", {}), ensure_ascii=False
                            ),
                        },
                    }
                ]

            # Stage 1b: If not decided, try function-calling client
            if not tool_calls:
                reasoning_parts.append("Stage: decision (function calling)")
                chat_resp = await self.chat_client.create_completion(
                    model=self.model_name,
                    messages=[
                        {"role": "system", "content": PromptBuilder.SYSTEM_PROMPT_EN},
                        {"role": "user", "content": request.message},
                    ],
                    tools=TOOLS_SCHEMA,
                    tool_choice="auto",
                    temperature=self.temperature,
                    max_tokens=min(256, self.max_tokens),
                )
                tool_calls = chat_resp.get("tool_calls", [])

            if not tool_calls and parsed_intent:
                tool_calls = [self._create_tool_call(parsed_intent)]

            if not tool_calls:
                # Legacy fallback to text-only
                prompt = self._prompt_builder.build_prompt(request, with_tools)
                llm_response = await self._call_llm(prompt)
                reasoning_parts.append(
                    "Fallback: no tool_calls; returned text response"
                )
                response = ResponseBuilder.build_text_response(llm_response)
                duration = time.time() - start_time
                response.reasoning = (
                    "\n".join(reasoning_parts) + f"\n\n⏱ {duration:.2f}s"
                )
                if METRICS_AVAILABLE:
                    AgentMetrics.record_request(
                        user_id=request.user_id,
                        success=response.success,
                        duration=duration,
                        tokens=tokens_used,
                    )
                return response

            call = tool_calls[0]
            fn_name = (
                call.get("function", {}).get("name", "")
                if isinstance(call, dict)
                else ""
            )
            raw_args = (
                call.get("function", {}).get("arguments")
                if isinstance(call, dict)
                else None
            )
            try:
                fn_args = (
                    json.loads(raw_args)
                    if isinstance(raw_args, str)
                    else (raw_args or {})
                )
            except json.JSONDecodeError:
                fn_args = {}
            reasoning_parts.append(
                f"Decision: tool={fn_name} params={json.dumps(fn_args, ensure_ascii=False)}"
            )

            # Stage 2: Execution
            reasoning_parts.append("Stage: execution")
            exec_result = await self._stage_execution(
                fn_name, fn_args, with_tools, request.user_id
            )
            if isinstance(exec_result, dict) and exec_result.get("error"):
                reasoning_parts.append(f"Execution error: {exec_result.get('error')}")
                duration = time.time() - start_time
                error_resp = ResponseBuilder.build_error_response(
                    exec_result.get("error", "Execution failed")
                )
                error_resp.reasoning = (
                    "\n".join(reasoning_parts) + f"\n\n⏱ {duration:.2f}s"
                )
                if METRICS_AVAILABLE:
                    AgentMetrics.record_request(
                        user_id=request.user_id,
                        success=False,
                        duration=duration,
                        tokens=tokens_used,
                    )
                return error_resp
            if METRICS_AVAILABLE:
                AgentMetrics.record_tool_use(fn_name, success=True)

            # Stage 3: Formatting
            reasoning_parts.append("Stage: formatting")
            text = self._stage_formatting(exec_result, fn_name)

            # Chunk long messages and append concise reasoning trace after summary
            final_text = ResponseBuilder.chunk_text(text)
            final_text += "\n\n---\nОтчёт агента:\n" + "\n".join(reasoning_parts[-10:])
            if self._tool_trace:
                final_text += "\n\n---\nTool trace:\n" + "\n".join(self._tool_trace)

            response = AgentResponse(
                success=True,
                text=final_text,
                tools_used=[fn_name],
                tokens_used=tokens_used,
                reasoning=None,
            )

            duration = time.time() - start_time
            reasoning_str = "\n".join(reasoning_parts) + f"\n\n⏱ {duration:.2f}s"
            if self._tool_trace:
                reasoning_str += "\n\n---\nTool trace:\n" + "\n".join(self._tool_trace)
            response.reasoning = reasoning_str

            if METRICS_AVAILABLE:
                AgentMetrics.record_request(
                    user_id=request.user_id,
                    success=True,
                    duration=duration,
                    tokens=tokens_used,
                )

            return response

        try:
            tools = await self.registry.discover_tools()
            return await _run_flow(tools)
        except Exception as e:
            logger.error(f"Tools discovery failed, continuing without schema: {e}")
            return await _run_flow([])

        except Exception as e:
            # Non-fatal for tests/fakes: continue without tool schemas
            logger.error(f"Tools discovery failed, continuing without schema: {e}")
            tools = []

    async def _call_llm(self, prompt: str) -> str:
        """Call LLM with prompt.

        Args:
            prompt: Input prompt

        Returns:
            LLM response text

        Raises:
            Exception: If LLM call fails
        """
        start_time = time.time()
        try:
            response = await self.llm_client.make_request(
                model_name=self.model_name,
                prompt=prompt,
                max_tokens=self.max_tokens,
                temperature=self.temperature,
            )

            duration = time.time() - start_time

            # Record metrics
            if METRICS_AVAILABLE:
                LLMMetrics.record_request(
                    model_name=self.model_name,
                    success=True,
                    duration=duration,
                    input_tokens=response.input_tokens,
                    output_tokens=response.response_tokens,
                )

            return response.response
        except Exception:
            duration = time.time() - start_time

            # Record error metrics
            if METRICS_AVAILABLE:
                LLMMetrics.record_request(
                    model_name=self.model_name, success=False, duration=duration
                )

            raise

    async def _stage_decision(self, request: AgentRequest) -> Optional[Dict[str, Any]]:
        """Stage 1: Ask model to produce JSON tool call and parse it robustly."""
        # Compose a concise decision-only prompt using existing client (string prompt)
        decision_prompt = (
            f"[SYSTEM]\n{DECISION_ONLY_SYSTEM_PROMPT}\n\n" f"[USER]\n{request.message}"
        )
        response_text = await self._call_llm(decision_prompt)
        # Clean artifacts that Mistral models echo back
        response_text = ToolCallParser._clean_text(response_text)
        # Remove common prompt echo artifacts
        import re

        artifacts = [
            r"<<SYS>>.*?<</SYS>>",
            r"\[SYSTEM\].*?\[/SYSTEM\]",
            r"\[SYSTEM\].*?\[USER\]",
            r"Ты — умный агент.*?ПРИМЕРЫ:",
        ]
        for pattern in artifacts:
            response_text = re.sub(
                pattern, "", response_text, flags=re.DOTALL | re.IGNORECASE
            )
        response_text = response_text.strip()
        # Keep a short raw trace in logs
        logger.debug("Decision raw (cleaned): %s", response_text[:200])
        settings = get_settings()
        if settings.parser_strict_mode:
            parsed = ToolCallParser.parse(response_text, strict=True)
        else:
            parsed = ToolCallParser.parse_with_fallback(
                response_text, max_attempts=max(1, settings.parser_max_attempts)
            )
        return parsed

    def _parse_user_intent(self, user_input: str) -> Optional[Dict[str, Any]]:
        """Parse Russian input without LLM to infer a likely tool call.

        Returns a minimal intent dict like {"action": "digest", "channel": str, "days": int}
        or {"action": "list_channels"}.
        """
        if RussianInputParser.parse_list_request(user_input):
            return {"action": "list_channels"}
        digest = RussianInputParser.parse_digest_request(user_input)
        if digest:
            digest["channel"] = RussianInputParser.normalize_channel_name(
                digest.get("channel", "")
            )
            return digest
        return None

    def _create_tool_call(self, intent: Dict[str, Any]) -> Dict[str, Any]:
        """Create a synthetic tool_call dict compatible with OpenAI format."""
        action = intent.get("action")
        if action == "digest":
            return {
                "id": "fallback_1",
                "type": "function",
                "function": {
                    "name": "get_channel_digest_by_name",
                    "arguments": json.dumps(
                        {
                            "channel_name": intent.get("channel", "onaboka"),
                            "days": intent.get("days", 3),
                        }
                    ),
                },
            }
        if action == "list_channels":
            return {
                "id": "fallback_2",
                "type": "function",
                "function": {"name": "list_channels", "arguments": json.dumps({})},
            }
        return {
            "id": "fallback_0",
            "type": "function",
            "function": {"name": "list_channels", "arguments": json.dumps({})},
        }

    async def _stage_execution(
        self,
        tool_name: str,
        tool_params: Dict[str, Any],
        tools: list[ToolMetadata],
        user_id: int,
    ) -> Dict[str, Any]:
        """Stage 2: Execute selected tool via MCP client.

        Normalizes parameters to match MCP tool schemas.
        """
        normalized: Dict[str, Any] = dict(tool_params or {})

        # Inject user_id where required
        if tool_name in {
            "get_channel_digest_by_name",
            "get_channel_digest",
            "add_channel",
            "list_channels",
        }:
            normalized["user_id"] = user_id

        # Map decision params → tool schemas
        if tool_name == "get_channel_digest_by_name":
            channel_username = normalized.pop("channel_username", None)
            channel_name = normalized.pop("channel_name", None)

            # Resolve channel using ChannelResolver service
            channel_hint = channel_name or channel_username
            if channel_hint:
                resolved_username = await self._channel_resolver.resolve(
                    str(channel_hint), user_id, trace_callback=self._trace
                )

                # Canonicalize non-ASCII usernames
                if resolved_username and any(ord(ch) > 127 for ch in resolved_username):
                    human_hint = channel_name or channel_username or resolved_username
                    candidates = (
                        self._channel_resolver._guess_usernames_from_human_name(
                            human_hint
                        )
                    )
                    for candidate in candidates:
                        try:
                            meta = await self.mcp_client.call_tool(
                                "get_channel_metadata",
                                {"channel_username": candidate, "user_id": user_id},
                            )
                            if meta and (meta.get("username") or meta.get("title")):
                                resolved_username = candidate
                                logger.info(
                                    f"Canonicalized username via metadata guess: {resolved_username}"
                                )
                                break
                        except Exception:
                            continue

                if not resolved_username:
                    sanitized = self._channel_resolver._sanitize_channel_hint(
                        channel_hint
                    )
                    logger.warning(f"Channel not found: {sanitized}")
                    return {
                        "error": f"Не удалось найти канал '{sanitized}'. Проверьте название или подпишитесь на канал через add_channel."
                    }

                normalized["channel_username"] = resolved_username

            # 4) convert days→hours if provided; default 72 hours
            days = normalized.pop("days", None)
            if days is not None and "hours" not in normalized:
                try:
                    normalized["hours"] = int(days) * 24
                except Exception:
                    pass
            normalized.setdefault("hours", 72)

            # 5) Check if channel has posts for requested window
            posts_window: Dict[str, Any] = {}
            try:
                posts_window = await self.mcp_client.call_tool(
                    "get_posts",
                    {
                        "channel_username": normalized["channel_username"],
                        "hours": normalized["hours"],
                        "user_id": user_id,
                    },
                )
                posts_count_check = (
                    int(posts_window.get("posts_count", 0))
                    if isinstance(posts_window, dict)
                    else 0
                )
                self._trace(
                    "get_posts",
                    "success",
                    f"{normalized['channel_username']} {normalized['hours']}h posts={posts_count_check}",
                )
            except Exception as e:
                logger.debug(f"get_posts failed: {e}")
                self._trace("get_posts", "error", str(e))
                posts_window = {}

            posts_count = (
                int(posts_window.get("posts_count", 0))
                if isinstance(posts_window, dict)
                else 0
            )

            # 6) If no posts, trigger collect_posts with dedupe (trust result, don't recheck)
            if posts_count == 0:
                try:
                    logger.info(
                        f"No posts found, triggering collection for {normalized['channel_username']}"
                    )
                    collect_res = await self.mcp_client.call_tool(
                        "collect_posts",
                        {
                            "channel_username": normalized["channel_username"],
                            "user_id": user_id,
                            "wait_for_completion": True,
                            "timeout_seconds": 30,
                            "hours": normalized["hours"],
                        },
                    )
                    if isinstance(collect_res, dict):
                        status = collect_res.get("status", "success")
                        cc = collect_res.get("collected_count", "?")
                        self._trace(
                            "collect_posts",
                            status,
                            f"{normalized['channel_username']} collected={cc}",
                        )
                    else:
                        self._trace(
                            "collect_posts", "success", normalized["channel_username"]
                        )
                except Exception as e:
                    logger.warning(f"collect_posts failed: {e}")
                    self._trace("collect_posts", "error", str(e))

            # 7) Try server-side digest first (preferred: may include summarization)
            result = await self.mcp_client.call_tool(
                "get_channel_digest_by_name", normalized
            )
            digests_count = (
                len(result.get("digests", [])) if isinstance(result, dict) else 0
            )
            self._trace(
                "get_channel_digest_by_name",
                "success",
                f"{normalized['channel_username']} {normalized['hours']}h digests={digests_count}",
            )

            # 8) If server returns no digests, attempt local summarization fallback
            if not (isinstance(result, dict) and result.get("digests")):
                try:
                    # Fetch posts after collection
                    posts_window = await self.mcp_client.call_tool(
                        "get_posts",
                        {
                            "channel_username": normalized["channel_username"],
                            "hours": normalized["hours"],
                            "user_id": user_id,
                        },
                    )
                    posts = (
                        posts_window.get("data", [])
                        if isinstance(posts_window, dict)
                        else []
                    )
                    self._trace(
                        "get_posts",
                        "success",
                        f"{normalized['channel_username']} {normalized['hours']}h (post-collect) posts={len(posts)}",
                    )
                    if posts:
                        text_blob = "\n\n---\n\n".join(
                            f"[{p.get('date','')}] {p.get('text','')}" for p in posts
                        )
                        summary_resp = await self.mcp_client.call_tool(
                            "generate_summary",
                            {
                                "posts_text": text_blob,
                                "posts_count": len(posts),
                                "channel_name": resolved_username,
                                "language": "ru",
                                "style": "bullet_points",
                            },
                        )
                        self._trace(
                            "generate_summary", "success", f"posts={len(posts)}"
                        )
                        result = {
                            "digests": [
                                {
                                    "channel": resolved_username,
                                    "post_count": len(posts),
                                    "summary": summary_resp.get("summary", ""),
                                }
                            ]
                        }
                except Exception as e:
                    logger.warning(f"Summarization fallback failed: {e}")
                    self._trace("generate_summary", "error", str(e))

            return result

        elif tool_name == "get_channel_digest":
            days = normalized.pop("days", None)
            if days is not None and "hours" not in normalized:
                try:
                    normalized["hours"] = int(days) * 24
                except Exception:
                    pass
            normalized.setdefault("hours", 24)

        elif tool_name == "add_channel":
            channel_username = normalized.pop(
                "channel_username", None
            ) or normalized.pop("channel_name", None)
            if channel_username:
                normalized["channel_username"] = channel_username.lstrip("@")

        # Validate against discovered tool schemas when possible
        if not self._validate_tool_params(tool_name, normalized, tools):
            return {"error": f"Invalid parameters for tool {tool_name}"}

        result = await self.mcp_client.call_tool(tool_name, normalized)
        # Add success status if missing for simpler assertions in tests
        if isinstance(result, dict) and "status" not in result:
            result = {"status": "success", **result}
        return result

    def _trace(self, tool_name: str, status: str, info: str = "") -> None:
        """Record tool call trace for debugging and reporting.

        Args:
            tool_name: Name of the tool that was called
            status: "success" or "error"
            info: Optional additional info (e.g., params or result summary)
        """
        try:
            line = f"{tool_name}: {status}"
            if info:
                line += f" ({info})"
            self._tool_trace.append(line)
        except Exception:
            # Best-effort; tracing must not break the flow
            pass

    def _stage_formatting(self, exec_result: Dict[str, Any], tool_name: str) -> str:
        """Stage 3: Format the execution result into user-facing text.

        Uses existing formatting rules; can be extended to call summarizer when needed.
        """
        # Reuse existing formatter to keep compatibility
        return self._format_tool_result(exec_result, tool_name)

    def _parse_response(self, response_text: str) -> Dict[str, Any]:
        """Parse LLM response to extract tool call or text.

        Args:
            response_text: Raw LLM response

        Returns:
            Parsed response dictionary
        """
        response_text = response_text.strip()

        # Remove prompt artifacts (common with mistral models)
        # Remove everything before first { if JSON is found
        json_start = response_text.find("{")
        if json_start > 0:
            # Check if there's a JSON object after this position
            json_end = response_text.rfind("}")
            if json_end > json_start:
                # Try to extract JSON
                json_candidate = response_text[json_start : json_end + 1]
                try:
                    parsed = json.loads(json_candidate)
                    if "tool" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    pass

        # Try to parse as JSON (tool call) - full string
        if response_text.startswith("{") and response_text.endswith("}"):
            try:
                parsed = json.loads(response_text)
                if "tool" in parsed:
                    return parsed
            except json.JSONDecodeError:
                pass

        # Try to find JSON object anywhere in response
        import re

        json_pattern = r'\{[^{}]*"tool"[^{}]*\}'
        matches = re.findall(json_pattern, response_text)
        if matches:
            for match in matches:
                try:
                    parsed = json.loads(match)
                    if "tool" in parsed:
                        return parsed
                except json.JSONDecodeError:
                    continue

        # Remove common prompt artifacts
        artifacts = [
            "[INST]",
            "<<SYS>>",
            "<</SYS>>",
            "[/INST]",
            "### Instruction",
            "### Response",
            "Available tools:",
            "Доступные инструменты:",
        ]
        cleaned = response_text
        for artifact in artifacts:
            # Remove artifact and everything before it if it appears early
            idx = cleaned.find(artifact)
            if idx < len(cleaned) * 0.3:  # Only if in first 30% of text
                cleaned = cleaned[idx + len(artifact) :].strip()

        # Return as text
        return {"text": cleaned}

    def _validate_tool_params(
        self, tool_name: str, args: Dict[str, Any], tools: list[ToolMetadata]
    ) -> bool:
        """Validate tool parameters against schema.

        Args:
            tool_name: Tool name
            args: Tool arguments
            tools: List of available tools

        Returns:
            True if valid, False otherwise
        """
        # If no schemas available, skip strict validation (tests/fakes)
        if not tools:
            return True
        tool = next((t for t in tools if t.name == tool_name), None)
        if not tool:
            return False

        schema = tool.input_schema
        required = schema.get("required", [])

        # Check required parameters
        for param in required:
            if param not in args:
                return False

        return True

    async def _execute_tool(
        self, parsed_response: Dict[str, Any], tools: list[ToolMetadata]
    ) -> Dict[str, Any]:
        """Execute tool call.

        Args:
            parsed_response: Parsed response with tool info
            tools: List of available tools

        Returns:
            Tool execution result

        Raises:
            ValueError: If tool not found or invalid parameters
        """
        tool_name = parsed_response["tool"]
        args = parsed_response.get("args", {})

        if not self._validate_tool_params(tool_name, args, tools):
            raise ValueError(f"Invalid parameters for tool {tool_name}")

        result = await self.mcp_client.call_tool(tool_name, args)
        return result

    def _format_tool_result(self, result: Dict[str, Any], tool_name: str) -> str:
        """Format tool result for user.

        Args:
            result: Tool execution result
            tool_name: Tool name

        Returns:
            Formatted text
        """
        return self._formatter.format(result, tool_name)
