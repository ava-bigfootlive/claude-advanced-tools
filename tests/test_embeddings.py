"""Tests for SemanticToolSearch and HybridToolSearch."""

import tempfile
from pathlib import Path

import pytest
from src.tool_registry import ToolRegistry
from src.embeddings import SemanticToolSearch, HybridToolSearch


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
    {
        "name": "extract_highlights",
        "description": "Extract best moments and highlights from video content",
        "input_schema": {
            "type": "object",
            "properties": {"media_id": {"type": "string"}},
            "required": ["media_id"]
        }
    }
]


class TestSemanticToolSearch:
    """Test cases for SemanticToolSearch class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()
        self.registry.register_many(SAMPLE_TOOLS)
        self.search = SemanticToolSearch(self.registry)

    def test_build_index(self):
        """Test building the semantic index."""
        self.search.build_index()

        assert self.search.embeddings is not None
        assert len(self.search.tool_names) == 5
        assert self.search.embeddings.shape[0] == 5

    def test_search_returns_results(self):
        """Test that search returns results."""
        self.search.build_index()
        results = self.search.search("create event", top_k=3)

        assert len(results) <= 3
        assert all("tool_name" in r for r in results)
        assert all("score" in r for r in results)
        assert all(r["type"] == "tool_reference" for r in results)

    def test_search_relevance(self):
        """Test that semantic search returns relevant tools."""
        self.search.build_index()

        # Test conceptual matching
        results = self.search.search("start broadcasting", top_k=3)
        tool_names = [r["tool_name"] for r in results]
        assert "start_event" in tool_names

        # Test synonym understanding
        results = self.search.search("money earnings", top_k=3)
        tool_names = [r["tool_name"] for r in results]
        assert "get_revenue_report" in tool_names

    def test_search_scores_normalized(self):
        """Test that search scores are reasonable."""
        self.search.build_index()
        results = self.search.search("create event", top_k=5)

        # Scores should be between -1 and 1 (cosine similarity)
        for r in results:
            assert -1 <= r["score"] <= 1

    def test_search_top_k_limit(self):
        """Test that top_k parameter is respected."""
        self.search.build_index()

        results = self.search.search("event", top_k=2)
        assert len(results) <= 2

        results = self.search.search("event", top_k=10)
        assert len(results) <= 5  # Only 5 tools registered

    def test_invalidate(self):
        """Test index invalidation."""
        self.search.build_index()
        assert self.search.embeddings is not None

        self.search.invalidate()

        assert self.search.embeddings is None
        assert self.search.tool_names == []

    def test_auto_build_on_search(self):
        """Test that index is auto-built on first search."""
        # Don't call build_index explicitly
        results = self.search.search("event", top_k=3)

        assert len(results) > 0
        assert self.search.embeddings is not None


class TestHybridToolSearch:
    """Test cases for HybridToolSearch class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.registry = ToolRegistry()
        self.registry.register_many(SAMPLE_TOOLS)
        self.search = HybridToolSearch(self.registry)

    def test_build_indices(self):
        """Test building both indices."""
        self.search.build_indices()

        assert self.search.semantic_search.embeddings is not None
        assert self.search.bm25_search._bm25_index is not None

    def test_search_returns_results(self):
        """Test that hybrid search returns results."""
        self.search.build_indices()
        results = self.search.search("create event", top_k=3)

        assert len(results) <= 3
        assert all("tool_name" in r for r in results)
        assert all("score" in r for r in results)

    def test_search_combines_methods(self):
        """Test that hybrid search combines BM25 and semantic."""
        self.search.build_indices()

        # Query that benefits from both methods
        results = self.search.search("go live broadcast", top_k=3)

        tool_names = [r["tool_name"] for r in results]
        # Should find start_event through semantic understanding
        assert "start_event" in tool_names

    def test_weight_configuration(self):
        """Test different weight configurations."""
        # BM25-heavy
        bm25_heavy = HybridToolSearch(
            self.registry,
            bm25_weight=0.9,
            semantic_weight=0.1
        )
        bm25_heavy.build_indices()
        results_bm25 = bm25_heavy.search("event streaming", top_k=3)

        # Semantic-heavy
        semantic_heavy = HybridToolSearch(
            self.registry,
            bm25_weight=0.1,
            semantic_weight=0.9
        )
        semantic_heavy.build_indices()
        results_semantic = semantic_heavy.search("event streaming", top_k=3)

        # Results should differ based on weights
        # Just verify both return valid results
        assert len(results_bm25) > 0
        assert len(results_semantic) > 0

    def test_invalidate(self):
        """Test index invalidation."""
        self.search.build_indices()
        self.search.invalidate()

        assert self.search.semantic_search.embeddings is None

    def test_scores_positive(self):
        """Test that combined scores are positive."""
        self.search.build_indices()
        results = self.search.search("analyze audience", top_k=5)

        for r in results:
            assert r["score"] >= 0


class TestSemanticSearchEdgeCases:
    """Edge case tests for semantic search."""

    def test_empty_registry(self):
        """Test search with empty registry."""
        registry = ToolRegistry()
        search = SemanticToolSearch(registry)
        search.build_index()

        results = search.search("anything", top_k=3)
        assert results == []

    def test_single_tool(self):
        """Test search with only one tool."""
        registry = ToolRegistry()
        registry.register({
            "name": "only_tool",
            "description": "The only tool",
            "input_schema": {"type": "object", "properties": {}}
        })

        search = SemanticToolSearch(registry)
        results = search.search("tool", top_k=5)

        assert len(results) == 1
        assert results[0]["tool_name"] == "only_tool"

    def test_empty_query(self):
        """Test search with empty query."""
        registry = ToolRegistry()
        registry.register_many(SAMPLE_TOOLS)

        search = SemanticToolSearch(registry)
        search.build_index()

        # Empty query should still work
        results = search.search("", top_k=3)
        # May return results based on embedding of empty string
        assert isinstance(results, list)


class TestEmbeddingCache:
    """Test cases for embedding cache persistence."""

    def test_cache_saves_and_loads(self):
        """Test that embeddings are cached to disk."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = Path(tmp_dir)

            # First build - should compute and save
            registry = ToolRegistry()
            registry.register_many(SAMPLE_TOOLS)
            search1 = SemanticToolSearch(registry, cache_dir=cache_dir)
            search1.build_index()

            # Verify cache files exist
            embeddings_path, metadata_path = search1._get_cache_paths()
            assert embeddings_path.exists()
            assert metadata_path.exists()

            # Second search instance - should load from cache
            search2 = SemanticToolSearch(registry, cache_dir=cache_dir)
            search2.build_index()

            # Should have same embeddings
            assert search2.embeddings is not None
            assert len(search2.tool_names) == 5
            assert search2._initialized

    def test_cache_invalidation_on_tool_change(self):
        """Test that cache is invalidated when tools change."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = Path(tmp_dir)

            # Build with initial tools
            registry = ToolRegistry()
            registry.register_many(SAMPLE_TOOLS[:3])
            search1 = SemanticToolSearch(registry, cache_dir=cache_dir)
            search1.build_index()

            original_hash = search1._cache_hash

            # Register new tool
            registry.register({
                "name": "new_tool",
                "description": "A brand new tool",
                "input_schema": {"type": "object", "properties": {}}
            })

            # New search should detect change and rebuild
            search2 = SemanticToolSearch(registry, cache_dir=cache_dir)
            search2.build_index()

            # Hash should be different
            assert search2._cache_hash != original_hash
            assert len(search2.tool_names) == 4

    def test_cache_disabled(self):
        """Test that cache can be disabled."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = Path(tmp_dir)

            registry = ToolRegistry()
            registry.register_many(SAMPLE_TOOLS)
            search = SemanticToolSearch(
                registry,
                cache_dir=cache_dir,
                use_cache=False
            )
            search.build_index()

            # Cache files should not exist
            embeddings_path, metadata_path = search._get_cache_paths()
            assert not embeddings_path.exists()
            assert not metadata_path.exists()

    def test_invalidate_clears_cache(self):
        """Test that invalidate() removes cache files."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = Path(tmp_dir)

            registry = ToolRegistry()
            registry.register_many(SAMPLE_TOOLS)
            search = SemanticToolSearch(registry, cache_dir=cache_dir)
            search.build_index()

            # Cache should exist
            embeddings_path, metadata_path = search._get_cache_paths()
            assert embeddings_path.exists()
            assert metadata_path.exists()

            # Invalidate should clear cache
            search.invalidate()

            assert not embeddings_path.exists()
            assert not metadata_path.exists()

    def test_force_rebuild(self):
        """Test force_rebuild parameter bypasses cache."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = Path(tmp_dir)

            registry = ToolRegistry()
            registry.register_many(SAMPLE_TOOLS)

            # First build
            search = SemanticToolSearch(registry, cache_dir=cache_dir)
            search.build_index()

            # Force rebuild should recompute
            search.build_index(force_rebuild=True)

            # Should still work
            assert search.embeddings is not None
            assert len(search.tool_names) == 5

    def test_get_stats_includes_cache_info(self):
        """Test that get_stats includes cache information."""
        with tempfile.TemporaryDirectory() as tmp_dir:
            cache_dir = Path(tmp_dir)

            registry = ToolRegistry()
            registry.register_many(SAMPLE_TOOLS)
            search = SemanticToolSearch(registry, cache_dir=cache_dir)
            search.build_index()

            stats = search.get_stats()

            assert "cache_enabled" in stats
            assert "cache_dir" in stats
            assert "cache_exists" in stats
            assert "tools_hash" in stats
            assert stats["cache_enabled"] is True
            assert stats["cache_exists"] is True
            assert stats["tools_hash"] is not None
