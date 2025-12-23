"""
Tool Registry - Manages tool definitions with example validation.

Implements Phase 1: Tool Use Examples
- Registers tools with input_examples
- Validates examples against JSON schemas
- Formats tools for Claude API consumption
"""

from typing import Any
from jsonschema import validate, ValidationError
import logging

logger = logging.getLogger(__name__)


class ToolRegistry:
    """
    Registry for tool definitions with schema-validated examples.

    Each tool can include input_examples that demonstrate valid usage patterns.
    Examples are validated against the tool's input_schema to ensure correctness.
    """

    def __init__(self):
        self.tools: dict[str, dict] = {}
        self._validation_errors: list[str] = []

    def register(self, tool_def: dict) -> bool:
        """
        Register a tool and validate its examples against schema.

        Args:
            tool_def: Tool definition with name, description, input_schema,
                     and optional input_examples

        Returns:
            True if registration successful, False if validation failed

        Raises:
            ValueError: If tool definition is missing required fields
        """
        # Validate required fields
        required_fields = ["name", "description", "input_schema"]
        for field in required_fields:
            if field not in tool_def:
                raise ValueError(f"Tool definition missing required field: {field}")

        name = tool_def["name"]
        schema = tool_def["input_schema"]
        examples = tool_def.get("input_examples", [])

        # Validate each example against the schema
        for i, example in enumerate(examples):
            try:
                validate(instance=example, schema=schema)
            except ValidationError as e:
                error_msg = f"Tool '{name}' example {i} invalid: {e.message}"
                self._validation_errors.append(error_msg)
                logger.warning(error_msg)
                # Continue registration but log the error
                # In strict mode, you might want to raise instead

        self.tools[name] = tool_def
        logger.debug(f"Registered tool: {name} with {len(examples)} examples")
        return True

    def register_many(self, tools: list[dict]) -> int:
        """
        Register multiple tools at once.

        Args:
            tools: List of tool definitions

        Returns:
            Number of successfully registered tools
        """
        count = 0
        for tool in tools:
            try:
                if self.register(tool):
                    count += 1
            except ValueError as e:
                logger.error(f"Failed to register tool: {e}")
        return count

    def get_tool(self, name: str) -> dict | None:
        """Get a single tool by name."""
        return self.tools.get(name)

    def get_all_tools(self) -> list[dict]:
        """Get all registered tools."""
        return list(self.tools.values())

    def get_tools_for_api(
        self,
        include_examples: bool = True,
        tool_names: list[str] | None = None
    ) -> list[dict]:
        """
        Format tools for Claude API consumption.

        Args:
            include_examples: Whether to include input_examples in output
            tool_names: Optional list of specific tools to include

        Returns:
            List of tool definitions formatted for Claude API
        """
        result = []
        tools_to_process = (
            [self.tools[n] for n in tool_names if n in self.tools]
            if tool_names
            else self.tools.values()
        )

        for tool in tools_to_process:
            api_tool = {
                "name": tool["name"],
                "description": tool["description"],
                "input_schema": tool["input_schema"]
            }

            # Include examples if requested and available
            if include_examples and "input_examples" in tool:
                api_tool["input_examples"] = tool["input_examples"]

            result.append(api_tool)

        return result

    def get_deferred_tools(self, include_examples: bool = True) -> list[dict]:
        """
        Get tools formatted for deferred loading (Phase 2: Tool Search).

        Each tool is marked with defer_loading: true so it won't be loaded
        into context until discovered via tool search.

        Args:
            include_examples: Whether to include input_examples

        Returns:
            List of deferred tool definitions
        """
        deferred = []
        for tool in self.get_tools_for_api(include_examples=include_examples):
            deferred.append({
                **tool,
                "defer_loading": True
            })
        return deferred

    def search_tools(self, query: str) -> list[str]:
        """
        Simple substring search across tool names and descriptions.

        For production use, prefer ToolSearchProvider with BM25.

        Args:
            query: Search string

        Returns:
            List of matching tool names
        """
        query_lower = query.lower()
        matches = []
        for name, tool in self.tools.items():
            searchable = f"{name} {tool['description']}".lower()
            if query_lower in searchable:
                matches.append(name)
        return matches

    def get_validation_errors(self) -> list[str]:
        """Get list of validation errors encountered during registration."""
        return self._validation_errors.copy()

    def clear(self):
        """Clear all registered tools."""
        self.tools.clear()
        self._validation_errors.clear()

    def __len__(self) -> int:
        return len(self.tools)

    def __contains__(self, name: str) -> bool:
        return name in self.tools

    def __repr__(self) -> str:
        return f"ToolRegistry({len(self.tools)} tools)"


def create_tool_definition(
    name: str,
    description: str,
    properties: dict[str, dict],
    required: list[str] | None = None,
    examples: list[dict] | None = None
) -> dict:
    """
    Helper function to create a properly formatted tool definition.

    Args:
        name: Tool name (alphanumeric + underscore)
        description: What the tool does
        properties: JSON schema properties for input parameters
        required: List of required parameter names
        examples: List of example inputs

    Returns:
        Properly formatted tool definition dict
    """
    tool = {
        "name": name,
        "description": description,
        "input_schema": {
            "type": "object",
            "properties": properties,
            "required": required or []
        }
    }

    if examples:
        tool["input_examples"] = examples

    return tool
