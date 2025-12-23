"""
Advanced Tool Client - Claude client with advanced tool use patterns.

Combines Phase 1 (Tool Examples) and Phase 2 (Tool Search) for
optimal tool use with reduced context and improved accuracy.

Search modes:
- bm25: Fast keyword-based ranking (default)
- regex: Simple pattern matching
- semantic: Embedding-based conceptual understanding
- hybrid: Combined BM25 + semantic for best results
- auto: Intelligent mode selection based on query characteristics
"""

import os
import re
import logging
from typing import Any, Literal
from dotenv import load_dotenv

from .tool_registry import ToolRegistry
from .tool_search import ToolSearchProvider

logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()


class AdvancedToolClient:
    """
    Claude client with advanced tool use patterns.

    Features:
    - Tool Use Examples: Improved accuracy with input_examples
    - Tool Search: Deferred loading for 85%+ token reduction
    - Automatic tool execution loop
    - Usage tracking and metrics

    Usage:
        client = AdvancedToolClient()
        client.register_tools(EVENT_TOOLS)
        response = client.chat([{"role": "user", "content": "Create event"}])
    """

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        use_tool_search: bool = True,
        use_examples: bool = True,
        search_mode: Literal["bm25", "regex", "semantic", "hybrid", "auto"] = "bm25"
    ):
        """
        Initialize the advanced tool client.

        Args:
            api_key: Anthropic API key (defaults to ANTHROPIC_API_KEY env var)
            model: Model to use (defaults to claude-sonnet-4-20250514)
            use_tool_search: Enable deferred loading with tool search
            use_examples: Include input_examples in tool definitions
            search_mode: Search algorithm for tool discovery:
                - bm25: Fast keyword-based ranking (default)
                - regex: Simple pattern matching
                - semantic: Embedding-based conceptual understanding
                - hybrid: Combined BM25 + semantic for best results
                - auto: Intelligent mode selection based on query
        """
        try:
            import anthropic
        except ImportError:
            raise ImportError("anthropic package required: pip install anthropic")

        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY required")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self.model = model or os.getenv("CLAUDE_MODEL", "claude-sonnet-4-20250514")

        self.registry = ToolRegistry()
        self.search_mode = search_mode
        self._init_search_provider()

        self.use_tool_search = use_tool_search
        self.use_examples = use_examples

        # Metrics
        self._total_requests = 0
        self._total_tokens = {"input": 0, "output": 0}
        self._tool_calls = []

    def _init_search_provider(self):
        """Initialize the appropriate search provider based on mode."""
        if self.search_mode in ("bm25", "regex"):
            self.search_provider = ToolSearchProvider(
                self.registry, search_type=self.search_mode
            )
            self.semantic_search = None
            self.hybrid_search = None
        elif self.search_mode == "semantic":
            from .embeddings import SemanticToolSearch
            self.search_provider = ToolSearchProvider(self.registry, search_type="bm25")
            self.semantic_search = SemanticToolSearch(self.registry)
            self.hybrid_search = None
        elif self.search_mode == "hybrid":
            from .embeddings import HybridToolSearch
            self.search_provider = ToolSearchProvider(self.registry, search_type="bm25")
            self.semantic_search = None
            self.hybrid_search = HybridToolSearch(self.registry)
        elif self.search_mode == "auto":
            # Auto mode needs all providers available for dynamic selection
            from .embeddings import SemanticToolSearch, HybridToolSearch
            self.search_provider = ToolSearchProvider(self.registry, search_type="bm25")
            self.semantic_search = SemanticToolSearch(self.registry)
            self.hybrid_search = HybridToolSearch(self.registry)

    def register_tools(self, tools: list[dict]):
        """
        Register tools with the registry.

        Args:
            tools: List of tool definitions
        """
        self.registry.register_many(tools)
        self.search_provider.invalidate_index()

        # Invalidate semantic/hybrid indices if using those modes
        if self.semantic_search:
            self.semantic_search.invalidate()
        if self.hybrid_search:
            self.hybrid_search.invalidate()

        logger.info(f"Registered {len(tools)} tools (search_mode={self.search_mode})")

    def _detect_search_mode(self, query: str) -> str:
        """
        Analyze query and determine the best search mode.

        Selection logic:
        - Contains regex patterns (*, ?, [, ^, $) → regex
        - Short (1-2 words), looks like function name → bm25
        - Longer, conversational phrasing → semantic
        - Uncertain/mixed → hybrid

        Args:
            query: The search query to analyze

        Returns:
            One of: "regex", "bm25", "semantic", "hybrid"
        """
        query = query.strip()

        # Check for regex/glob patterns
        regex_patterns = r'[\*\?\[\]\^\$\|\\]'
        if re.search(regex_patterns, query):
            logger.debug(f"Auto mode: regex (pattern chars detected)")
            return "regex"

        # Tokenize
        words = query.split()
        word_count = len(words)

        # Check if it looks like a function/tool name (snake_case, camelCase, etc)
        looks_like_identifier = bool(re.match(
            r'^[a-z][a-z0-9]*(_[a-z0-9]+)*$',  # snake_case
            query.lower().replace(" ", "_")
        )) or bool(re.match(
            r'^[a-z]+[A-Z][a-zA-Z0-9]*$',  # camelCase
            query
        ))

        # Short queries (1-2 words) that look like identifiers → BM25
        if word_count <= 2 and looks_like_identifier:
            logger.debug(f"Auto mode: bm25 (short identifier-like query)")
            return "bm25"

        # Check for conversational/natural language indicators
        conversational_patterns = [
            r'\b(i want|i need|help me|how do i|can you|please)\b',
            r'\b(what|when|where|who|why|which)\b',
            r'\b(to|the|a|an|for|with|from|about)\b',
        ]
        conversational_score = sum(
            1 for pattern in conversational_patterns
            if re.search(pattern, query.lower())
        )

        # Longer queries (4+ words) or conversational → semantic
        if word_count >= 4 or conversational_score >= 2:
            logger.debug(
                f"Auto mode: semantic (words={word_count}, "
                f"conversational_score={conversational_score})"
            )
            return "semantic"

        # Medium-length queries (3 words) or uncertain → hybrid
        logger.debug(f"Auto mode: hybrid (fallback for words={word_count})")
        return "hybrid"

    def search_tools(self, query: str, max_results: int = 5) -> list[dict]:
        """
        Search for tools using the configured search mode.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of tool_reference dicts with tool_name and optional score
        """
        # Determine effective search mode
        if self.search_mode == "auto":
            effective_mode = self._detect_search_mode(query)
        else:
            effective_mode = self.search_mode

        # Execute search with the determined mode
        if effective_mode == "semantic" and self.semantic_search:
            return self.semantic_search.search(query, top_k=max_results)
        elif effective_mode == "hybrid" and self.hybrid_search:
            return self.hybrid_search.search(query, top_k=max_results)
        elif effective_mode == "regex":
            # Use regex search via provider
            regex_provider = ToolSearchProvider(self.registry, search_type="regex")
            return regex_provider.search(query, max_results=max_results)
        else:
            # BM25 (default fallback)
            return self.search_provider.search(query, max_results=max_results)

    def _build_tools_payload(self) -> list[dict]:
        """Build tools list based on configuration."""
        if self.use_tool_search:
            # Phase 2: Deferred loading - only sends name + brief description
            # Full schemas loaded on-demand when tools are discovered
            return self.search_provider.build_tools_payload()
        else:
            # Traditional: Load all tools immediately (higher token usage)
            return self.registry.get_tools_for_api(
                include_examples=self.use_examples
            )

    def chat(
        self,
        messages: list[dict],
        system: str | None = None,
        max_tokens: int = 4096,
        max_tool_iterations: int = 10,
        tool_handlers: dict[str, callable] | None = None
    ) -> dict:
        """
        Send a chat request with advanced tool use.

        Args:
            messages: Conversation messages
            system: System prompt
            max_tokens: Maximum tokens in response
            max_tool_iterations: Max rounds of tool calling
            tool_handlers: Optional dict of {tool_name: handler_function}

        Returns:
            Response dict with content, stop_reason, usage, and tool_calls
        """
        self._total_requests += 1

        tools = self._build_tools_payload()
        current_messages = messages.copy()
        all_tool_calls = []

        for iteration in range(max_tool_iterations):
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                system=system or "You are a helpful assistant with access to various tools.",
                tools=tools,
                messages=current_messages
            )

            # Track usage
            self._total_tokens["input"] += response.usage.input_tokens
            self._total_tokens["output"] += response.usage.output_tokens

            # Check if we need to handle tool calls
            if response.stop_reason != "tool_use":
                # No more tool calls, return final response
                return self._format_response(response, all_tool_calls)

            # Process tool calls
            tool_uses = [
                block for block in response.content
                if block.type == "tool_use"
            ]

            if not tool_uses:
                return self._format_response(response, all_tool_calls)

            # Add assistant's response to messages
            current_messages.append({
                "role": "assistant",
                "content": response.content
            })

            # Execute tools and add results
            tool_results = []
            for tool_use in tool_uses:
                tool_name = tool_use.name
                tool_input = tool_use.input

                all_tool_calls.append({
                    "id": tool_use.id,
                    "name": tool_name,
                    "input": tool_input,
                    "iteration": iteration
                })

                # Execute handler if provided
                if tool_handlers and tool_name in tool_handlers:
                    try:
                        result = tool_handlers[tool_name](tool_input)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    # No handler - return placeholder
                    result = {
                        "status": "simulated",
                        "message": f"Tool '{tool_name}' executed with input: {tool_input}"
                    }

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use.id,
                    "content": str(result)
                })

            current_messages.append({
                "role": "user",
                "content": tool_results
            })

        # Max iterations reached
        logger.warning(f"Max tool iterations ({max_tool_iterations}) reached")
        return self._format_response(response, all_tool_calls)

    def _format_response(self, response, tool_calls: list) -> dict:
        """Format the response for return."""
        # Extract text content
        text_content = ""
        for block in response.content:
            if hasattr(block, "text"):
                text_content += block.text

        return {
            "content": text_content,
            "stop_reason": response.stop_reason,
            "usage": {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens
            },
            "tool_calls": tool_calls,
            "raw_content": response.content
        }

    def get_usage_stats(self) -> dict:
        """Get usage statistics."""
        return {
            "total_requests": self._total_requests,
            "total_tokens": self._total_tokens.copy(),
            "registered_tools": len(self.registry),
            "tool_search_enabled": self.use_tool_search,
            "examples_enabled": self.use_examples,
            "search_mode": self.search_mode
        }

    def estimate_token_savings(self) -> dict:
        """
        Estimate token savings from using tool search.

        Returns comparison of tokens with/without deferred loading.
        """
        # Rough estimate: each tool is ~150-250 tokens
        tools_count = len(self.registry)
        avg_tokens_per_tool = 200

        full_load_tokens = tools_count * avg_tokens_per_tool
        deferred_tokens = 500  # Meta-tool + minimal overhead

        savings = full_load_tokens - deferred_tokens
        savings_pct = (savings / full_load_tokens * 100) if full_load_tokens > 0 else 0

        return {
            "tools_count": tools_count,
            "estimated_full_load_tokens": full_load_tokens,
            "estimated_deferred_tokens": deferred_tokens,
            "estimated_savings": savings,
            "savings_percentage": round(savings_pct, 1)
        }
