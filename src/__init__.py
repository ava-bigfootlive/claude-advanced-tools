"""
Claude Advanced Tools - Advanced tool use patterns for Claude API.

This package implements Anthropic's advanced tool use features:
- Tool Use Examples: input_examples for improved accuracy
- Tool Search Tool: Deferred loading with BM25/regex search
- Semantic Search: Custom embeddings-based tool discovery

Usage:
    from src import AdvancedToolClient, ToolRegistry
    from tools import EVENT_TOOLS, MEDIA_TOOLS

    client = AdvancedToolClient()
    client.register_tools(EVENT_TOOLS + MEDIA_TOOLS)
    response = client.chat([{"role": "user", "content": "Create a gaming event"}])
"""

from .tool_registry import ToolRegistry
from .tool_search import ToolSearchProvider
from .client import AdvancedToolClient

__version__ = "0.1.0"
__all__ = ["ToolRegistry", "ToolSearchProvider", "AdvancedToolClient"]
