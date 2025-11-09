"""MCP Tools Registry v2 with schema validation.

Enhanced tools registry with strict parameter validation and type safety.
Following Python Zen: Explicit is better than implicit.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.domain.interfaces.tool_client import ToolClientProtocol

logger = logging.getLogger(__name__)


class ToolCategory:
    """Tool category constants matching DialogMode."""

    TASK = "task"
    DATA = "data"
    REMINDERS = "reminders"
    IDLE = "idle"


@dataclass
class ToolParameter:
    """Tool parameter schema definition.

    Attributes:
        name: Parameter name
        type: Parameter type (string, integer, boolean, etc.)
        required: Whether parameter is required
        description: Parameter description
        default: Default value if optional
    """

    name: str
    type: str
    required: bool
    description: str
    default: Optional[Any] = None


@dataclass
class ToolSchema:
    """Tool schema definition with validation.

    Attributes:
        name: Tool name
        category: Tool category (TASK, DATA, REMINDERS, IDLE)
        parameters: List of tool parameters
        returns: Return type description
        description: Tool description
    """

    name: str
    category: str
    parameters: List[ToolParameter]
    returns: Dict[str, str]
    description: str


class MCPToolsRegistryV2:
    """Enhanced MCP tools registry with schema validation.

    Purpose:
        Discovers MCP tools and validates tool calls before execution.
        Provides type-safe tool schema definitions.

    Example:
        >>> from src.infrastructure.mcp.tools_registry_v2 import MCPToolsRegistryV2
        >>> from src.infrastructure.clients.mcp_client_adapter import MCPToolClientAdapter
        >>>
        >>> adapter = MCPToolClientAdapter(robust_client)
        >>> registry = MCPToolsRegistryV2(tool_client=adapter)
        >>> is_valid, error = await registry.validate_tool_call(
        ...     "create_task", {"title": "Test"}
        ... )
        >>> if is_valid:
        ...     result = await registry.call_tool("create_task", {"title": "Test"}, "user123")
    """

    def __init__(
        self,
        tool_client: ToolClientProtocol,
        strict_mode: bool = True,
    ) -> None:
        """Initialize registry v2.

        Args:
            tool_client: Tool client implementing domain protocol
            strict_mode: Enable strict parameter validation (default: True)
        """
        self.tool_client = tool_client
        self.strict_mode = strict_mode
        self._schemas: Dict[str, ToolSchema] = {}
        self._initialized = False

    async def _ensure_initialized(self) -> None:
        """Ensure schemas are loaded from tool client.

        Raises:
            Exception: If tool discovery fails
        """
        if self._initialized:
            return

        try:
            raw_tools = await self.tool_client.discover_tools()
            self._schemas = self._parse_schemas(raw_tools)
            self._initialized = True
            logger.debug(f"Initialized registry with {len(self._schemas)} tools")
        except Exception as e:
            logger.error(f"Failed to initialize registry: {e}", exc_info=True)
            raise

    def _parse_schemas(self, raw_tools: List[Dict[str, Any]]) -> Dict[str, ToolSchema]:
        """Parse raw tools into ToolSchema objects.

        Args:
            raw_tools: Raw tool dictionaries from MCP client

        Returns:
            Dictionary mapping tool names to ToolSchema objects
        """
        schemas = {}
        for tool in raw_tools:
            try:
                schema = self._parse_single_schema(tool)
                schemas[schema.name] = schema
            except Exception as e:
                logger.warning(
                    f"Failed to parse schema for tool {tool.get('name', 'unknown')}: {e}"
                )
        return schemas

    def _parse_single_schema(self, tool: Dict[str, Any]) -> ToolSchema:
        """Parse single tool into ToolSchema.

        Args:
            tool: Raw tool dictionary

        Returns:
            ToolSchema object

        Raises:
            ValueError: If tool structure is invalid
        """
        name = tool.get("name")
        if not name:
            raise ValueError("Tool name is required")

        description = tool.get("description", "")
        input_schema = tool.get("input_schema", {})

        # Extract category from tool name or description
        category = self._infer_category(name, description)

        # Parse parameters
        parameters = self._parse_parameters(input_schema)

        # Infer return type from description
        returns = self._infer_returns(description)

        return ToolSchema(
            name=name,
            category=category,
            parameters=parameters,
            returns=returns,
            description=description,
        )

    def _parse_parameters(self, input_schema: Dict[str, Any]) -> List[ToolParameter]:
        """Parse parameters from JSON schema.

        Args:
            input_schema: JSON schema dictionary

        Returns:
            List of ToolParameter objects
        """
        parameters = []
        properties = input_schema.get("properties", {})
        required = input_schema.get("required", [])

        for param_name, param_schema in properties.items():
            param_type = param_schema.get("type", "string")
            is_required = param_name in required
            description = param_schema.get("description", "")
            default = param_schema.get("default")

            param = ToolParameter(
                name=param_name,
                type=param_type,
                required=is_required,
                description=description,
                default=default,
            )
            parameters.append(param)

        return parameters

    def _infer_category(self, tool_name: str, description: str) -> str:
        """Infer tool category from name and description.

        Args:
            tool_name: Tool name
            description: Tool description

        Returns:
            Category string (TASK, DATA, REMINDERS, IDLE)
        """
        text_lower = (tool_name + " " + description).lower()

        if any(word in text_lower for word in ["task", "todo", "create_task"]):
            return ToolCategory.TASK
        if any(word in text_lower for word in ["data", "digest", "stats", "channel"]):
            return ToolCategory.DATA
        if any(word in text_lower for word in ["reminder", "remind", "alert"]):
            return ToolCategory.REMINDERS

        return ToolCategory.IDLE

    def _infer_returns(self, description: str) -> Dict[str, str]:
        """Infer return type from description.

        Args:
            description: Tool description

        Returns:
            Dictionary describing return type
        """
        # Default return type
        return {"type": "dict", "description": "Tool execution result"}

    async def validate_tool_call(
        self, tool_name: str, params: Dict[str, Any]
    ) -> Tuple[bool, Optional[str]]:
        """Validate tool call parameters.

        Args:
            tool_name: Name of tool to validate
            params: Parameters to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if parameters are valid
            - error_message: Error message if invalid, None if valid
        """
        await self._ensure_initialized()

        if tool_name not in self._schemas:
            return False, f"Tool '{tool_name}' not found"

        schema = self._schemas[tool_name]

        if not self.strict_mode:
            return True, None

        # Check required parameters
        missing = self._check_required_params(schema, params)
        if missing:
            return False, f"Missing required parameters: {', '.join(missing)}"

        # Validate parameter types
        type_error = self._validate_param_types(schema, params)
        if type_error:
            return False, type_error

        return True, None

    def _check_required_params(
        self, schema: ToolSchema, params: Dict[str, Any]
    ) -> List[str]:
        """Check for missing required parameters.

        Args:
            schema: Tool schema
            params: Provided parameters

        Returns:
            List of missing required parameter names
        """
        return [
            param.name
            for param in schema.parameters
            if param.required and param.name not in params
        ]

    def _validate_param_types(
        self, schema: ToolSchema, params: Dict[str, Any]
    ) -> Optional[str]:
        """Validate parameter types.

        Args:
            schema: Tool schema
            params: Provided parameters

        Returns:
            Error message if validation fails, None if valid
        """
        for param in schema.parameters:
            if param.name not in params:
                continue

            value = params[param.name]
            type_valid = self._validate_type(value, param.type)
            if not type_valid:
                return (
                    f"Parameter '{param.name}' has wrong type. "
                    f"Expected {param.type}, got {type(value).__name__}"
                )

        return None

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type matches expected type.

        Args:
            value: Value to validate
            expected_type: Expected type string

        Returns:
            True if type matches
        """
        type_mapping = {
            "string": str,
            "integer": int,
            "number": (int, float),
            "boolean": bool,
            "array": list,
            "object": dict,
        }

        python_type = type_mapping.get(expected_type.lower())
        if not python_type:
            return True  # Unknown type, skip validation

        if isinstance(python_type, tuple):
            return isinstance(value, python_type)

        return isinstance(value, python_type)

    async def call_tool(
        self, tool_name: str, params: Dict[str, Any], user_id: str
    ) -> Dict[str, Any]:
        """Call tool with validation.

        Args:
            tool_name: Name of tool to call
            params: Tool parameters
            user_id: User ID for tool execution

        Returns:
            Tool execution result

        Raises:
            ValueError: If validation fails
            Exception: If tool execution fails
        """
        # Validate first
        is_valid, error_msg = await self.validate_tool_call(tool_name, params)
        if not is_valid:
            raise ValueError(f"Tool call validation failed: {error_msg}")

        # Execute tool
        try:
            result = await self.tool_client.call_tool(
                tool_name=tool_name, arguments=params
            )
            logger.debug(f"Tool {tool_name} executed for user {user_id}")
            return result
        except Exception as e:
            logger.error(
                f"Tool {tool_name} execution failed: {e}",
                exc_info=True,
            )
            raise

    async def get_tool_schema(self, tool_name: str) -> Optional[ToolSchema]:
        """Get tool schema by name.

        Args:
            tool_name: Name of tool

        Returns:
            ToolSchema if found, None otherwise
        """
        await self._ensure_initialized()
        return self._schemas.get(tool_name)

    async def list_tools_by_category(self, category: str) -> List[ToolSchema]:
        """List all tools in a category.

        Args:
            category: Category name (TASK, DATA, REMINDERS, IDLE)

        Returns:
            List of ToolSchema objects
        """
        await self._ensure_initialized()
        return [
            schema for schema in self._schemas.values() if schema.category == category
        ]
