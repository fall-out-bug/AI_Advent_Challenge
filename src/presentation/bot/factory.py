"""Factory for creating ButlerOrchestrator and all dependencies.

Following Clean Architecture: centralized dependency creation.
Following SOLID: Dependency Inversion Principle via factory pattern.
"""

import json
import os
from typing import List, Optional, Tuple

from motor.motor_asyncio import AsyncIOMotorDatabase

from src.application.orchestration.intent_orchestrator import IntentOrchestrator
from src.application.usecases.collect_data_usecase import CollectDataUseCase
from src.application.usecases.create_task_usecase import CreateTaskUseCase
from src.domain.agents.butler_orchestrator import ButlerOrchestrator
from src.domain.agents.handlers.chat_handler import ChatHandler
from src.domain.agents.handlers.data_handler import DataHandler
from src.domain.agents.handlers.homework_handler import HomeworkHandler
from src.domain.agents.handlers.reminders_handler import RemindersHandler
from src.domain.agents.handlers.task_handler import TaskHandler
from src.domain.agents.services.mode_classifier import ModeClassifier
from src.domain.intent import HybridIntentClassifier, LLMClassifier, RuleBasedClassifier
from src.infrastructure.cache.intent_cache import IntentCache
from src.infrastructure.clients.mcp_client_adapter import MCPToolClientAdapter
from src.infrastructure.clients.mcp_client_robust import RobustMCPClient
from src.infrastructure.clients.multi_mcp_client import MultiMCPClient
from src.infrastructure.config.settings import get_settings
from src.infrastructure.database.mongo import get_db
from src.infrastructure.hw_checker.client import HWCheckerClient
from src.infrastructure.llm.mistral_client import MistralClient
from src.infrastructure.logging import get_logger
from src.presentation.mcp.client import MCPClientProtocol, get_mcp_client

logger = get_logger("butler_factory")


async def create_butler_orchestrator(
    mongodb: Optional[AsyncIOMotorDatabase] = None,
) -> ButlerOrchestrator:
    """Create ButlerOrchestrator with all dependencies.

    Purpose:
        Initialize all infrastructure, application, and domain components
        required for ButlerOrchestrator to function.

    Args:
        mongodb: Optional MongoDB database instance. If None, will be created.

    Returns:
        Fully configured ButlerOrchestrator instance.

    Raises:
        RuntimeError: If critical dependencies cannot be initialized.

    Example:
        >>> orchestrator = await create_butler_orchestrator()
        >>> response = await orchestrator.handle_user_message(
        ...     user_id="123", message="Create task", session_id="456"
        ... )
    """
    try:
        # 1. Initialize MongoDB
        if mongodb is None:
            mongodb = await get_db()
        logger.info("MongoDB initialized")

        # 2. Initialize LLM Client (MistralClient)
        mistral_url = os.getenv("MISTRAL_API_URL", "http://localhost:8001")
        llm_client = MistralClient(base_url=mistral_url)
        logger.info(f"MistralClient initialized with URL: {mistral_url}")

        # 3. Initialize MCP Client Adapter (support multiple servers)
        mcp_clients = _create_mcp_clients()
        if len(mcp_clients) == 1:
            # Single server - use robust client directly
            base_mcp_client = mcp_clients[0][0]
            robust_mcp_client = RobustMCPClient(base_client=base_mcp_client)
            tool_client = MCPToolClientAdapter(robust_client=robust_mcp_client)
            logger.info("MCPToolClientAdapter initialized (single server)")
        else:
            # Multiple servers - use MultiMCPClient
            multi_client = MultiMCPClient(mcp_clients)
            robust_mcp_client = RobustMCPClient(base_client=multi_client)
            tool_client = MCPToolClientAdapter(robust_client=robust_mcp_client)
            logger.info(
                f"MCPToolClientAdapter initialized with {len(mcp_clients)} servers"
            )

        # 4. Initialize Intent Classification System (Hybrid: Rules + LLM + Cache)
        settings = get_settings()

        # Create rule-based classifier
        rule_classifier = RuleBasedClassifier()
        logger.info("RuleBasedClassifier initialized")

        # Create LLM classifier
        llm_classifier = LLMClassifier(
            llm_client=llm_client,
            model_name="mistral",
            timeout_seconds=settings.intent_llm_timeout_seconds,
            temperature=0.2,
        )
        logger.info("LLMClassifier initialized")

        # Create intent cache
        intent_cache = IntentCache(
            default_ttl_seconds=settings.intent_cache_ttl_seconds
        )
        logger.info("IntentCache initialized")

        # Create hybrid intent classifier
        hybrid_intent_classifier = HybridIntentClassifier(
            rule_classifier=rule_classifier,
            llm_classifier=llm_classifier,
            cache=intent_cache,
            confidence_threshold=settings.intent_confidence_threshold,
        )
        logger.info("HybridIntentClassifier initialized")

        # 5. Initialize Mode Classifier (uses hybrid system)
        mode_classifier = ModeClassifier(
            llm_client=llm_client,
            default_model="mistral",
            hybrid_classifier=hybrid_intent_classifier,
        )
        logger.info("ModeClassifier initialized")

        # 6. Initialize Use Cases
        intent_orchestrator = IntentOrchestrator(model_name="mistral")
        create_task_uc = CreateTaskUseCase(
            intent_orch=intent_orchestrator,
            tool_client=tool_client,
            mongodb=mongodb,
        )
        collect_data_uc = CollectDataUseCase(tool_client=tool_client)
        logger.info("Use cases initialized")

        # 6.5. Initialize HW Checker Client
        hw_checker_base_url = os.getenv(
            "HW_CHECKER_BASE_URL", "http://hw_checker-mcp-server-1:8005"
        )
        hw_checker_client = HWCheckerClient(base_url=hw_checker_base_url)
        logger.info(f"HWCheckerClient initialized with URL: {hw_checker_base_url}")

        # 7. Initialize Domain Handlers
        # Note: Handlers get user_id from context, not from initialization
        task_handler = TaskHandler(
            intent_orchestrator=intent_orchestrator,
            tool_client=tool_client,
            hybrid_classifier=hybrid_intent_classifier,
        )
        data_handler = DataHandler(
            tool_client=tool_client,
            hybrid_classifier=hybrid_intent_classifier,
            hw_checker_client=hw_checker_client,
        )
        reminders_handler = RemindersHandler(
            tool_client=tool_client,
            hybrid_classifier=hybrid_intent_classifier,
        )
        homework_handler = HomeworkHandler(
            hw_checker_client=hw_checker_client,
            tool_client=tool_client,
        )
        chat_handler = ChatHandler(
            llm_client=llm_client,
            default_model="mistral",
            hybrid_classifier=hybrid_intent_classifier,
        )
        logger.info("Domain handlers initialized")

        # 8. Create ButlerOrchestrator
        orchestrator = ButlerOrchestrator(
            mode_classifier=mode_classifier,
            task_handler=task_handler,
            data_handler=data_handler,
            reminders_handler=reminders_handler,
            homework_handler=homework_handler,
            chat_handler=chat_handler,
            mongodb=mongodb,
        )
        logger.info("ButlerOrchestrator created successfully")

        return orchestrator

    except Exception as e:
        logger.error(f"Failed to create ButlerOrchestrator: {e}", exc_info=True)
        raise RuntimeError(f"Failed to initialize ButlerOrchestrator: {e}") from e


def _parse_mcp_server_urls() -> List[str]:
    """Parse MCP server URLs from environment variables.

    Supports:
    - MCP_SERVER_URLS (comma-separated or JSON array): Multiple servers
    - MCP_SERVER_URL (single): Backward compatibility
    - Default: http://mcp-server:8004 (local server)

    Returns:
        List of MCP server URLs
    """
    # Try MCP_SERVER_URLS first (multiple servers)
    urls_str = os.getenv("MCP_SERVER_URLS")
    if urls_str:
        # Try JSON array first
        if urls_str.strip().startswith("["):
            try:
                urls = json.loads(urls_str)
                if isinstance(urls, list):
                    return [str(url) for url in urls if url]
            except json.JSONDecodeError:
                pass

        # Fallback to comma-separated
        urls = [url.strip() for url in urls_str.split(",") if url.strip()]
        if urls:
            return urls

    # Fallback to single MCP_SERVER_URL (backward compatibility)
    single_url = os.getenv("MCP_SERVER_URL")
    if single_url:
        return [single_url]

    # Default: local HTTP server (for development)
    # In production, MCP_SERVER_URL should be set via environment variable
    return ["http://localhost:8004"]


def _create_mcp_clients() -> List[Tuple[MCPClientProtocol, str]]:
    """Create MCP clients for all configured servers.

    Returns:
        List of (client, server_name) tuples.
        Server names are derived from URLs for logging.
    """
    urls = _parse_mcp_server_urls()
    clients: List[Tuple[MCPClientProtocol, str]] = []

    for url in urls:
        try:
            # Extract server name from URL
            if url and (url.startswith("http://") or url.startswith("https://")):
                # Extract hostname
                host_part = url.split("://", 1)[1].split("/")[0].split(":")[0]
                server_name = host_part.replace("-", "_")
                server_url = url
            else:
                # Use stdio for None or non-HTTP URLs
                server_name = "stdio_server"
                server_url = None

            client = get_mcp_client(server_url=server_url)
            clients.append((client, server_name))
            logger.debug(f"Created MCP client for {server_name} ({url or 'stdio'})")
        except Exception as e:
            logger.warning(f"Failed to create MCP client for {url or 'stdio'}: {e}")
            # Continue with other servers
            continue

    if not clients:
        raise RuntimeError(f"No MCP clients could be created from URLs: {urls}")

    return clients
