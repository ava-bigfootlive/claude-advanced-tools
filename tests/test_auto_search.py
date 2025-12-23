"""Tests for auto search mode in AdvancedToolClient."""

import sys
import pytest
from unittest.mock import patch, MagicMock
from src.tool_registry import ToolRegistry
from src.embeddings import SemanticToolSearch, HybridToolSearch


# Sample tools for testing
SAMPLE_TOOLS = [
    {
        "name": "create_event",
        "description": "Create a new live streaming event with scheduling",
        "input_schema": {
            "type": "object",
            "properties": {"title": {"type": "string"}},
            "required": ["title"]
        }
    },
    {
        "name": "start_event",
        "description": "Start streaming for a scheduled event, go live",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": ["event_id"]
        }
    },
    {
        "name": "analyze_audience",
        "description": "Analyze viewer demographics and audience insights",
        "input_schema": {
            "type": "object",
            "properties": {"event_id": {"type": "string"}},
            "required": []
        }
    },
    {
        "name": "get_revenue_report",
        "description": "Get revenue and monetization report for earnings",
        "input_schema": {
            "type": "object",
            "properties": {"period": {"type": "string"}},
            "required": []
        }
    },
]


# Create a mock anthropic module once at import time
mock_anthropic = MagicMock()
mock_anthropic.Anthropic = MagicMock()
sys.modules['anthropic'] = mock_anthropic


# Import after mocking
from src.client import AdvancedToolClient


@pytest.fixture(scope="module")
def auto_client():
    """Create an AdvancedToolClient in auto mode (shared across module)."""
    client = AdvancedToolClient(
        api_key="fake-key",
        search_mode="auto"
    )
    client.register_tools(SAMPLE_TOOLS)
    return client


class TestAutoSearchModeDetection:
    """Test the _detect_search_mode method."""

    def test_detect_regex_with_wildcards(self, auto_client):
        """Test that queries with wildcards trigger regex mode."""
        assert auto_client._detect_search_mode("get_*") == "regex"
        assert auto_client._detect_search_mode("create*event") == "regex"
        assert auto_client._detect_search_mode("event?") == "regex"
        assert auto_client._detect_search_mode("[abc]_tool") == "regex"

    def test_detect_regex_with_special_chars(self, auto_client):
        """Test that queries with regex special chars trigger regex mode."""
        assert auto_client._detect_search_mode("^start") == "regex"
        assert auto_client._detect_search_mode("event$") == "regex"
        assert auto_client._detect_search_mode("a|b") == "regex"

    def test_detect_bm25_short_identifier(self, auto_client):
        """Test that short identifier-like queries use BM25."""
        assert auto_client._detect_search_mode("create event") == "bm25"
        assert auto_client._detect_search_mode("event") == "bm25"
        assert auto_client._detect_search_mode("analytics") == "bm25"

    def test_detect_semantic_conversational(self, auto_client):
        """Test that conversational queries use semantic search."""
        assert auto_client._detect_search_mode("I want to start broadcasting") == "semantic"
        assert auto_client._detect_search_mode("help me understand my viewers") == "semantic"
        assert auto_client._detect_search_mode("how do I go live") == "semantic"
        assert auto_client._detect_search_mode("can you show me the revenue") == "semantic"

    def test_detect_semantic_long_queries(self, auto_client):
        """Test that long queries (4+ words) use semantic search."""
        assert auto_client._detect_search_mode("create a new streaming event") == "semantic"
        assert auto_client._detect_search_mode("analyze the audience demographics data") == "semantic"

    def test_detect_hybrid_medium_queries(self, auto_client):
        """Test that medium-length uncertain queries use hybrid."""
        # 3 words, not clearly conversational or identifier-like
        assert auto_client._detect_search_mode("revenue report tool") == "hybrid"
        assert auto_client._detect_search_mode("streaming event status") == "hybrid"

    def test_detect_handles_empty_query(self, auto_client):
        """Test handling of empty or whitespace queries."""
        result = auto_client._detect_search_mode("")
        assert result in ("bm25", "hybrid")

        result = auto_client._detect_search_mode("   ")
        assert result in ("bm25", "hybrid")


class TestAutoSearchExecution:
    """Test that auto mode correctly routes to different search providers."""

    def test_auto_search_returns_results(self, auto_client):
        """Test that auto search returns valid results for various queries."""
        # Build indices first
        auto_client.semantic_search.build_index()
        auto_client.hybrid_search.build_indices()

        # Short keyword query → BM25
        results = auto_client.search_tools("create event", max_results=3)
        assert len(results) > 0
        assert all("tool_name" in r for r in results)

        # Conversational query → Semantic
        results = auto_client.search_tools("I want to go live", max_results=3)
        assert len(results) > 0
        assert all("tool_name" in r for r in results)

        # Pattern query → Regex
        results = auto_client.search_tools("*_event", max_results=3)
        assert isinstance(results, list)

    def test_auto_semantic_finds_conceptual_matches(self, auto_client):
        """Test that auto mode uses semantic for natural language."""
        auto_client.semantic_search.build_index()

        # This should trigger semantic mode and find start_event
        results = auto_client.search_tools("help me start broadcasting live")
        tool_names = [r["tool_name"] for r in results]

        # Semantic search should understand "broadcasting" relates to start_event
        assert "start_event" in tool_names

    def test_auto_bm25_for_direct_matches(self, auto_client):
        """Test that auto mode uses BM25 for direct keyword matches."""
        results = auto_client.search_tools("revenue", max_results=3)
        tool_names = [r["tool_name"] for r in results]

        assert "get_revenue_report" in tool_names

    def test_auto_regex_for_patterns(self, auto_client):
        """Test that auto mode uses regex for pattern queries."""
        # Use .* for regex wildcard (not * which is glob syntax)
        results = auto_client.search_tools(".*event.*", max_results=5)

        # Should find tools with "event" in the name
        tool_names = [r["tool_name"] for r in results]
        event_tools = [n for n in tool_names if "event" in n]
        assert len(event_tools) > 0


class TestAutoModeConfiguration:
    """Test auto mode configuration and state."""

    def test_auto_mode_initializes_all_providers(self, auto_client):
        """Test that auto mode initializes all search providers."""
        assert auto_client.search_provider is not None
        assert auto_client.semantic_search is not None
        assert auto_client.hybrid_search is not None

    def test_auto_mode_in_usage_stats(self, auto_client):
        """Test that auto mode is reported in usage stats."""
        stats = auto_client.get_usage_stats()
        assert stats["search_mode"] == "auto"

    def test_auto_mode_invalidates_all_providers(self):
        """Test that registering tools invalidates all search providers."""
        client = AdvancedToolClient(
            api_key="fake-key",
            search_mode="auto"
        )
        client.register_tools(SAMPLE_TOOLS)

        # Build indices
        client.semantic_search.build_index()
        client.hybrid_search.build_indices()

        # Register more tools - should invalidate
        client.register_tools([{
            "name": "new_tool",
            "description": "A new tool",
            "input_schema": {"type": "object", "properties": {}}
        }])

        # Semantic search should be invalidated (not initialized)
        assert not client.semantic_search._initialized
