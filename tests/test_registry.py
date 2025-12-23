"""Tests for ToolRegistry - Phase 1: Tool Use Examples."""

import pytest
from src.tool_registry import ToolRegistry, create_tool_definition


class TestToolRegistry:
    """Test cases for ToolRegistry class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()

    def test_register_simple_tool(self):
        """Test registering a tool without examples."""
        tool = {
            "name": "test_tool",
            "description": "A test tool",
            "input_schema": {
                "type": "object",
                "properties": {
                    "param": {"type": "string"}
                },
                "required": ["param"]
            }
        }

        result = self.registry.register(tool)

        assert result is True
        assert "test_tool" in self.registry
        assert len(self.registry) == 1

    def test_register_tool_with_valid_examples(self):
        """Test registering a tool with valid input_examples."""
        tool = {
            "name": "greet",
            "description": "Greet a user",
            "input_schema": {
                "type": "object",
                "properties": {
                    "name": {"type": "string"},
                    "formal": {"type": "boolean"}
                },
                "required": ["name"]
            },
            "input_examples": [
                {"name": "Alice", "formal": True},
                {"name": "Bob"}
            ]
        }

        result = self.registry.register(tool)

        assert result is True
        assert len(self.registry.get_validation_errors()) == 0

    def test_register_tool_with_invalid_examples(self):
        """Test that invalid examples are logged but registration succeeds."""
        tool = {
            "name": "bad_example",
            "description": "Tool with bad example",
            "input_schema": {
                "type": "object",
                "properties": {
                    "count": {"type": "integer"}
                },
                "required": ["count"]
            },
            "input_examples": [
                {"count": "not an integer"}  # Invalid!
            ]
        }

        # Should still register but log validation error
        result = self.registry.register(tool)

        assert result is True
        errors = self.registry.get_validation_errors()
        assert len(errors) == 1
        assert "bad_example" in errors[0]

    def test_register_missing_required_field(self):
        """Test that missing required fields raise ValueError."""
        incomplete_tool = {
            "name": "incomplete",
            "description": "Missing input_schema"
        }

        with pytest.raises(ValueError, match="input_schema"):
            self.registry.register(incomplete_tool)

    def test_register_many(self):
        """Test batch registration of tools."""
        tools = [
            {
                "name": f"tool_{i}",
                "description": f"Tool number {i}",
                "input_schema": {"type": "object", "properties": {}}
            }
            for i in range(5)
        ]

        count = self.registry.register_many(tools)

        assert count == 5
        assert len(self.registry) == 5

    def test_get_tool(self):
        """Test retrieving a single tool."""
        tool = {
            "name": "findme",
            "description": "Find this tool",
            "input_schema": {"type": "object", "properties": {}}
        }
        self.registry.register(tool)

        found = self.registry.get_tool("findme")
        not_found = self.registry.get_tool("nothere")

        assert found is not None
        assert found["name"] == "findme"
        assert not_found is None

    def test_get_tools_for_api_with_examples(self):
        """Test API format includes examples when requested."""
        tool = {
            "name": "api_test",
            "description": "Test API format",
            "input_schema": {
                "type": "object",
                "properties": {"x": {"type": "integer"}},
                "required": []
            },
            "input_examples": [{"x": 42}]
        }
        self.registry.register(tool)

        with_examples = self.registry.get_tools_for_api(include_examples=True)
        without_examples = self.registry.get_tools_for_api(include_examples=False)

        assert "input_examples" in with_examples[0]
        assert "input_examples" not in without_examples[0]

    def test_get_deferred_tools(self):
        """Test deferred loading returns minimal stubs, not full definitions."""
        tool = {
            "name": "deferred_test",
            "description": "Test deferred loading with a much longer description to verify truncation",
            "input_schema": {
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"}
                }
            },
            "input_examples": [{"param1": "test", "param2": 42}]
        }
        self.registry.register(tool)

        deferred = self.registry.get_deferred_tools()

        assert len(deferred) == 1
        assert deferred[0]["defer_loading"] is True
        assert deferred[0]["name"] == "deferred_test"
        assert "description" in deferred[0]
        # Critical: NO full schema or examples - that's the whole point!
        assert "input_schema" not in deferred[0]
        assert "input_examples" not in deferred[0]

    def test_get_full_tool(self):
        """Test getting full tool definition for expansion."""
        tool = {
            "name": "expand_test",
            "description": "Test full tool retrieval",
            "input_schema": {"type": "object", "properties": {"x": {"type": "string"}}},
            "input_examples": [{"x": "example"}]
        }
        self.registry.register(tool)

        # Get with examples
        full = self.registry.get_full_tool("expand_test", include_examples=True)
        assert full["name"] == "expand_test"
        assert "input_schema" in full
        assert "input_examples" in full

        # Get without examples
        no_examples = self.registry.get_full_tool("expand_test", include_examples=False)
        assert "input_schema" in no_examples
        assert "input_examples" not in no_examples

        # Non-existent tool
        assert self.registry.get_full_tool("not_there") is None

    def test_search_tools(self):
        """Test simple tool search."""
        self.registry.register_many([
            {"name": "create_event", "description": "Create an event", "input_schema": {"type": "object", "properties": {}}},
            {"name": "delete_event", "description": "Delete an event", "input_schema": {"type": "object", "properties": {}}},
            {"name": "analyze_video", "description": "Analyze video content", "input_schema": {"type": "object", "properties": {}}}
        ])

        event_results = self.registry.search_tools("event")
        video_results = self.registry.search_tools("video")
        empty_results = self.registry.search_tools("nonexistent")

        assert len(event_results) == 2
        assert len(video_results) == 1
        assert len(empty_results) == 0

    def test_clear(self):
        """Test clearing the registry."""
        self.registry.register({
            "name": "temp",
            "description": "Temporary",
            "input_schema": {"type": "object", "properties": {}}
        })

        self.registry.clear()

        assert len(self.registry) == 0
        assert len(self.registry.get_validation_errors()) == 0


class TestCreateToolDefinition:
    """Test cases for the helper function."""

    def test_minimal_definition(self):
        """Test creating a minimal tool definition."""
        tool = create_tool_definition(
            name="minimal",
            description="A minimal tool",
            properties={}
        )

        assert tool["name"] == "minimal"
        assert tool["description"] == "A minimal tool"
        assert tool["input_schema"]["type"] == "object"
        assert "input_examples" not in tool

    def test_full_definition(self):
        """Test creating a complete tool definition."""
        tool = create_tool_definition(
            name="full",
            description="A full tool",
            properties={
                "param1": {"type": "string", "description": "First param"},
                "param2": {"type": "integer", "description": "Second param"}
            },
            required=["param1"],
            examples=[
                {"param1": "test", "param2": 42}
            ]
        )

        assert tool["name"] == "full"
        assert len(tool["input_schema"]["properties"]) == 2
        assert tool["input_schema"]["required"] == ["param1"]
        assert len(tool["input_examples"]) == 1
