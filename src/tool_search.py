"""
Tool Search Provider - Implements deferred tool loading with search.

Implements Phase 2: Tool Search Tool
- BM25 and regex-based tool discovery
- Deferred loading to reduce context tokens
- Returns tool_reference blocks for discovered tools
"""

from typing import Literal
import re
import logging

logger = logging.getLogger(__name__)


class ToolSearchProvider:
    """
    Implements Claude's Tool Search Tool pattern.

    Tools are registered with defer_loading=True and only expanded
    when discovered via search. This dramatically reduces initial
    context size (from ~15K tokens to ~2K for 90+ tools).

    Supports two search modes:
    - regex: Simple pattern matching (faster, less accurate)
    - bm25: BM25 ranking algorithm (better relevance)
    """

    def __init__(
        self,
        registry,  # ToolRegistry
        search_type: Literal["regex", "bm25"] = "bm25"
    ):
        """
        Initialize the search provider.

        Args:
            registry: ToolRegistry instance containing tool definitions
            search_type: Search algorithm to use ("regex" or "bm25")
        """
        self.registry = registry
        self.search_type = search_type
        self._bm25_index = None
        self._tool_names_indexed = []

    def get_meta_tool(self) -> dict:
        """
        Returns the tool_search meta-tool definition.

        This is the special tool type that enables deferred loading.
        Claude will use this tool to discover relevant tools on-demand.
        """
        return {
            "type": f"tool_search_tool_{self.search_type}_20251119",
            "name": "tool_search"
        }

    def get_deferred_tools(self) -> list[dict]:
        """
        Returns all tools as minimal stubs with defer_loading: true.

        These are just name + brief description - NOT full schemas.
        This is the key to achieving 90%+ token savings.
        """
        return self.registry.get_deferred_tools()

    def build_tools_payload(self) -> list[dict]:
        """
        Build the complete tools payload for Claude API.

        Returns:
            [meta_tool, deferred_stub_1, deferred_stub_2, ...]

        The meta_tool enables search, deferred stubs are minimal (name + description only).
        Full schemas are loaded on-demand when tools are discovered.
        """
        tools = [self.get_meta_tool()]
        tools.extend(self.get_deferred_tools())
        return tools

    def search(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Search tools by query. Returns tool_reference blocks.

        In production with Claude's built-in tool search, this is handled
        automatically. This implementation is for testing/simulation.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of tool_reference blocks
        """
        if self.search_type == "regex":
            return self._regex_search(query, max_results)
        else:
            return self._bm25_search(query, max_results)

    def _regex_search(self, pattern: str, max_results: int) -> list[dict]:
        """
        Simple regex matching on tool names and descriptions.

        Fast but less accurate than BM25. Good for exact matches.
        """
        matches = []

        # Compile regex, escaping if invalid
        try:
            regex = re.compile(pattern, re.IGNORECASE)
        except re.error:
            regex = re.compile(re.escape(pattern), re.IGNORECASE)

        for name, tool in self.registry.tools.items():
            searchable = f"{name} {tool['description']}"
            if regex.search(searchable):
                matches.append({
                    "type": "tool_reference",
                    "tool_name": name
                })
                if len(matches) >= max_results:
                    break

        logger.debug(f"Regex search '{pattern}' found {len(matches)} tools")
        return matches

    def _bm25_search(self, query: str, max_results: int) -> list[dict]:
        """
        BM25 ranking for better relevance.

        BM25 (Best Match 25) is a probabilistic ranking function that
        considers term frequency and document length for better results.
        """
        try:
            from rank_bm25 import BM25Okapi
        except ImportError:
            logger.warning("rank-bm25 not installed, falling back to regex")
            return self._regex_search(query, max_results)

        # Build or rebuild index if needed
        current_tools = list(self.registry.tools.keys())
        if self._bm25_index is None or current_tools != self._tool_names_indexed:
            self._build_bm25_index()

        if not self._tool_names_indexed:
            return []

        # Tokenize query and score
        query_tokens = query.lower().split()
        scores = self._bm25_index.get_scores(query_tokens)

        # Sort by score and return top matches
        ranked = sorted(
            zip(self._tool_names_indexed, scores),
            key=lambda x: x[1],
            reverse=True
        )

        results = [
            {"type": "tool_reference", "tool_name": name}
            for name, score in ranked[:max_results]
            if score > 0
        ]

        logger.debug(f"BM25 search '{query}' found {len(results)} tools")
        return results

    def _build_bm25_index(self):
        """Build BM25 index from current tool registry."""
        from rank_bm25 import BM25Okapi

        corpus = []
        self._tool_names_indexed = []

        for name, tool in self.registry.tools.items():
            # Combine name, description, and parameter names for indexing
            doc = f"{name} {tool['description']}"
            if "input_schema" in tool:
                props = tool["input_schema"].get("properties", {})
                doc += " " + " ".join(props.keys())

            corpus.append(doc.lower().split())
            self._tool_names_indexed.append(name)

        self._bm25_index = BM25Okapi(corpus)
        logger.debug(f"Built BM25 index with {len(corpus)} tools")

    def invalidate_index(self):
        """Force index rebuild on next search."""
        self._bm25_index = None
        self._tool_names_indexed = []

    def get_search_stats(self) -> dict:
        """Get statistics about the search provider."""
        return {
            "search_type": self.search_type,
            "total_tools": len(self.registry),
            "index_built": self._bm25_index is not None,
            "indexed_tools": len(self._tool_names_indexed)
        }


class ToolSearchSimulator:
    """
    Simulates Claude's tool search behavior for testing.

    In production, Claude handles tool search internally. This class
    lets you test the behavior without making API calls.
    """

    def __init__(self, provider: ToolSearchProvider):
        self.provider = provider
        self.search_history: list[dict] = []

    def simulate_search_call(self, query: str) -> dict:
        """
        Simulate a tool_use block for tool_search.

        Returns what Claude would return when calling tool_search.
        """
        results = self.provider.search(query)

        self.search_history.append({
            "query": query,
            "results": results
        })

        return {
            "type": "tool_result",
            "tool_use_id": f"sim_{len(self.search_history)}",
            "content": results
        }

    def expand_references(
        self,
        references: list[dict],
        include_examples: bool = True
    ) -> list[dict]:
        """
        Expand tool_reference blocks to full tool definitions.

        This simulates what the API does when Claude uses discovered tools.
        The full schema is only loaded now, after the tool is discovered.

        Args:
            references: List of tool_reference blocks from search
            include_examples: Whether to include input_examples in expansion

        Returns:
            List of full tool definitions for discovered tools
        """
        expanded = []
        for ref in references:
            if ref.get("type") == "tool_reference":
                tool_name = ref.get("tool_name")
                tool = self.provider.registry.get_full_tool(
                    tool_name,
                    include_examples=include_examples
                )
                if tool:
                    expanded.append(tool)
        return expanded

    def get_history(self) -> list[dict]:
        """Get search history for debugging."""
        return self.search_history.copy()
