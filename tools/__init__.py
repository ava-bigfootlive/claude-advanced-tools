"""
Tool Library - Collection of tools for advanced tool use demonstrations.

Tools are organized by category and include input_examples for improved
accuracy (Phase 1). All tools can be loaded with deferred loading (Phase 2).

Categories:
- Event Tools: Live streaming event management
- Media Tools: Video/image analysis and processing
- Analytics Tools: Viewer analytics and predictions
- Content Tools: Content recommendations and marketing
- System Tools: Platform information and status
"""

from .event_tools import EVENT_TOOLS
from .media_tools import MEDIA_TOOLS
from .analytics_tools import ANALYTICS_TOOLS

# Combined tool set for easy registration
ALL_TOOLS = EVENT_TOOLS + MEDIA_TOOLS + ANALYTICS_TOOLS

__all__ = [
    "EVENT_TOOLS",
    "MEDIA_TOOLS",
    "ANALYTICS_TOOLS",
    "ALL_TOOLS"
]
