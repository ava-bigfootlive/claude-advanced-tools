"""Tests for ToolSearchProvider - Phase 2: Tool Search Tool."""

import pytest
from src.tool_registry import ToolRegistry
from src.tool_search import ToolSearchProvider, ToolSearchSimulator


# Sample tools for testing
SAMPLE_TOOLS = [
    {
        "name": "create_event",
        "description": "Create a new live streaming event with scheduling",
        "input_schema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "scheduled_start": {"type": "string"}
            },
            "required": ["title"]
        },
        "input_examples": [
            {"title": "Gaming Stream", "scheduled_start": "2025-01-15T19:00:00Z"}
        ]
    },
    {
        "name": "start_event",
        "description": "Start streaming for a scheduled event",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": ["event_id"]
        }
    },
    {
        "name": "stop_event",
        "description": "Stop a live stream and end the event",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": ["event_id"]
        }
    },
    {
        "name": "analyze_media",
        "description": "Analyze video content for highlights and insights",
        "input_schema": {
            "type": "object",
            "properties": {
                "media_id": {"type": "string"},
                "analysis_types": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["media_id"]
        }
    },
    {
        "name": "get_viewer_stats",
        "description": "Get viewer statistics and analytics for events",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": []
        }
    }
]


class TestToolSearchProvider:
    """Test cases for ToolSearchProvider class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()
        self.registry.register_many(SAMPLE_TOOLS)

    def test_get_meta_tool_bm25(self):
        """Test meta-tool definition for BM25 search."""
        provider = ToolSearchProvider(self.registry, search_type="bm25")
        meta_tool = provider.get_meta_tool()

        assert meta_tool["type"] == "tool_search_tool_bm25_20251119"
        assert meta_tool["name"] == "tool_search"

    def test_get_meta_tool_regex(self):
        """Test meta-tool definition for regex search."""
        provider = ToolSearchProvider(self.registry, search_type="regex")
        meta_tool = provider.get_meta_tool()

        assert meta_tool["type"] == "tool_search_tool_regex_20251119"
        assert meta_tool["name"] == "tool_search"

    def test_get_deferred_tools(self):
        """Test deferred tools are minimal stubs, not full definitions."""
        provider = ToolSearchProvider(self.registry)
        deferred = provider.get_deferred_tools()

        assert len(deferred) == 5
        for tool in deferred:
            assert tool["defer_loading"] is True
            assert "name" in tool
            assert "description" in tool
            # These should NOT be present - that's the whole point of deferred loading!
            assert "input_schema" not in tool
            assert "input_examples" not in tool

    def test_build_tools_payload(self):
        """Test complete tools payload structure - truly deferred (minimal stubs)."""
        provider = ToolSearchProvider(self.registry)
        payload = provider.build_tools_payload()

        # First item is meta-tool
        assert payload[0]["type"].startswith("tool_search_tool_")

        # Rest are deferred tools - should be MINIMAL stubs, not full definitions
        for tool in payload[1:]:
            assert tool["defer_loading"] is True
            assert "name" in tool
            assert "description" in tool
            # Critically: NO full input_schema - that's the whole point of deferred loading!
            assert "input_schema" not in tool
            assert "input_examples" not in tool

    def test_regex_search_basic(self):
        """Test regex search finds exact matches."""
        provider = ToolSearchProvider(self.registry, search_type="regex")

        results = provider.search("event", max_results=5)

        assert len(results) >= 3  # create_event, start_event, stop_event
        assert all(r["type"] == "tool_reference" for r in results)

    def test_regex_search_pattern(self):
        """Test regex search with pattern matching."""
        provider = ToolSearchProvider(self.registry, search_type="regex")

        results = provider.search("start|stop", max_results=5)

        tool_names = [r["tool_name"] for r in results]
        assert "start_event" in tool_names
        assert "stop_event" in tool_names

    def test_regex_search_invalid_pattern(self):
        """Test regex search handles invalid patterns."""
        provider = ToolSearchProvider(self.registry, search_type="regex")

        # Invalid regex should be escaped and still work
        results = provider.search("[invalid", max_results=5)

        # Should not raise, may return 0 results
        assert isinstance(results, list)

    def test_bm25_search_basic(self):
        """Test BM25 search returns ranked results."""
        provider = ToolSearchProvider(self.registry, search_type="bm25")

        results = provider.search("create event streaming", max_results=3)

        assert len(results) <= 3
        assert all(r["type"] == "tool_reference" for r in results)

    def test_bm25_search_relevance(self):
        """Test BM25 search ranks relevant tools higher."""
        provider = ToolSearchProvider(self.registry, search_type="bm25")

        results = provider.search("video analysis highlights", max_results=3)

        # analyze_media should be in results
        tool_names = [r["tool_name"] for r in results]
        assert "analyze_media" in tool_names

    def test_search_max_results(self):
        """Test max_results limit is respected."""
        provider = ToolSearchProvider(self.registry, search_type="bm25")

        results = provider.search("event", max_results=2)

        assert len(results) <= 2

    def test_search_no_results(self):
        """Test search with no matches returns empty list."""
        provider = ToolSearchProvider(self.registry, search_type="bm25")

        results = provider.search("xyznonexistent123", max_results=5)

        assert results == []

    def test_invalidate_index(self):
        """Test index invalidation."""
        provider = ToolSearchProvider(self.registry, search_type="bm25")

        # Build index by searching
        provider.search("event")
        assert provider._bm25_index is not None

        # Invalidate
        provider.invalidate_index()

        assert provider._bm25_index is None
        assert provider._tool_names_indexed == []

    def test_get_search_stats(self):
        """Test search statistics."""
        provider = ToolSearchProvider(self.registry, search_type="bm25")

        # Before search
        stats = provider.get_search_stats()
        assert stats["search_type"] == "bm25"
        assert stats["total_tools"] == 5
        assert stats["index_built"] is False

        # After search (builds index)
        provider.search("event")
        stats = provider.get_search_stats()
        assert stats["index_built"] is True
        assert stats["indexed_tools"] == 5


class TestToolSearchSimulator:
    """Test cases for ToolSearchSimulator class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()
        self.registry.register_many(SAMPLE_TOOLS)
        self.provider = ToolSearchProvider(self.registry, search_type="bm25")
        self.simulator = ToolSearchSimulator(self.provider)

    def test_simulate_search_call(self):
        """Test simulated search returns proper format."""
        result = self.simulator.simulate_search_call("create event")

        assert result["type"] == "tool_result"
        assert "tool_use_id" in result
        assert isinstance(result["content"], list)

    def test_expand_references(self):
        """Test expanding tool references to full definitions."""
        references = [
            {"type": "tool_reference", "tool_name": "create_event"},
            {"type": "tool_reference", "tool_name": "start_event"}
        ]

        expanded = self.simulator.expand_references(references)

        assert len(expanded) == 2
        assert expanded[0]["name"] == "create_event"
        assert "description" in expanded[0]
        assert "input_schema" in expanded[0]

    def test_expand_references_missing_tool(self):
        """Test expanding references with missing tools."""
        references = [
            {"type": "tool_reference", "tool_name": "nonexistent"},
            {"type": "tool_reference", "tool_name": "create_event"}
        ]

        expanded = self.simulator.expand_references(references)

        # Only valid tools are expanded
        assert len(expanded) == 1
        assert expanded[0]["name"] == "create_event"

    def test_search_history(self):
        """Test search history tracking."""
        self.simulator.simulate_search_call("event")
        self.simulator.simulate_search_call("video")

        history = self.simulator.get_history()

        assert len(history) == 2
        assert history[0]["query"] == "event"
        assert history[1]["query"] == "video"


class TestIntegration:
    """Integration tests for the complete tool search flow."""

    def test_full_workflow(self):
        """Test complete workflow from registration to search."""
        # 1. Register tools
        registry = ToolRegistry()
        registry.register_many(SAMPLE_TOOLS)

        # 2. Create search provider
        provider = ToolSearchProvider(registry, search_type="bm25")

        # 3. Build payload
        payload = provider.build_tools_payload()
        assert len(payload) == 6  # 1 meta + 5 tools

        # 4. Simulate search
        simulator = ToolSearchSimulator(provider)
        result = simulator.simulate_search_call("start streaming")

        # 5. Expand references
        expanded = simulator.expand_references(result["content"][:2])
        assert len(expanded) <= 2

        # 6. Verify tool details available
        for tool in expanded:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
