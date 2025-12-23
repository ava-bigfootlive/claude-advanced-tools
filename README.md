# Claude Advanced Tools

Advanced tool use patterns for Claude API - implementing Anthropic's latest features for improved accuracy and reduced context usage.

## Features

### Phase 1: Tool Use Examples (`input_examples`)

Provide concrete examples of valid tool inputs to improve Claude's tool calling accuracy:

```python
{
    "name": "create_event",
    "description": "Create a live streaming event",
    "input_schema": {...},
    "input_examples": [
        {"title": "Gaming Stream", "scheduled_start": "2025-01-15T19:00:00Z"},
        {"title": "Private Meeting", "visibility": "private"}
    ]
}
```

**Benefits:**
- 25-40% improvement in tool call accuracy
- Fewer malformed inputs
- Better understanding of parameter combinations

### Phase 2: Tool Search Tool (Deferred Loading)

Load tools on-demand instead of all at once, reducing context tokens by 85%+:

```python
# Traditional: ~15,000 tokens for 90 tools
# With deferred loading: ~2,000 tokens (meta-tool + deferred refs)

client = AdvancedToolClient(use_tool_search=True)
client.register_tools(ALL_TOOLS)  # 30+ tools, minimal token usage
```

**Benefits:**
- 85%+ token reduction
- Scales to 100+ tools
- BM25 or semantic search for discovery

## Installation

```bash
# Clone the repository
git clone https://github.com/your-org/claude-advanced-tools.git
cd claude-advanced-tools

# Install dependencies
pip install -r requirements.txt

# Set up environment
cp .env.example .env
# Edit .env with your ANTHROPIC_API_KEY
```

## Quick Start

### Basic Usage (Phase 1)

```python
from src import ToolRegistry
from tools import EVENT_TOOLS

# Register tools with examples
registry = ToolRegistry()
registry.register_many(EVENT_TOOLS)

# Get tools formatted for Claude API
tools = registry.get_tools_for_api(include_examples=True)
```

### With Tool Search (Phase 2)

```python
from src import AdvancedToolClient
from tools import ALL_TOOLS

# Create client with deferred loading
client = AdvancedToolClient(
    use_tool_search=True,  # Enable Phase 2
    use_examples=True       # Enable Phase 1
)

# Register 30+ tools (minimal token overhead)
client.register_tools(ALL_TOOLS)

# Chat with automatic tool discovery
response = client.chat([
    {"role": "user", "content": "Create a gaming stream for tonight"}
])
```

## Examples

Run the demo scripts to see features in action:

```bash
# Basic usage (Phase 1)
python -m examples.basic_usage

# Tool search demo (Phase 2)
python -m examples.tool_search_demo

# Full Ava-like assistant simulation
python -m examples.bigfootlive_simulation

# With live Claude API
ANTHROPIC_API_KEY=sk-... python -m examples.bigfootlive_simulation --live
```

## Architecture

```
claude-advanced-tools/
├── src/
│   ├── __init__.py          # Package exports
│   ├── tool_registry.py     # Phase 1: Tool registration + example validation
│   ├── tool_search.py       # Phase 2: BM25/regex search provider
│   ├── client.py            # Claude client wrapper
│   └── embeddings.py        # Optional: Semantic search enhancement
│
├── tools/
│   ├── event_tools.py       # Event management (10 tools)
│   ├── media_tools.py       # Media processing (10 tools)
│   └── analytics_tools.py   # Analytics & predictions (10 tools)
│
├── examples/
│   ├── basic_usage.py       # Phase 1 demo
│   ├── tool_search_demo.py  # Phase 2 demo
│   └── bigfootlive_simulation.py  # Full assistant demo
│
└── tests/
    ├── test_registry.py     # Registry unit tests
    └── test_tool_search.py  # Search provider tests
```

## Tool Library

30+ tools organized by category, mirroring BigfootLive's production assistant:

### Event Tools (10 tools)
- `create_event` - Create live streaming events
- `update_event` - Update event details
- `cancel_event` - Cancel with notification
- `list_events` - Filter and paginate events
- `get_event` - Get event details
- `start_event` - Go live
- `stop_event` - End stream
- `get_stream_key` - Get/regenerate stream key
- `send_event_notification` - Notify viewers
- `clone_event` - Duplicate event

### Media Tools (10 tools)
- `analyze_media` - AI content analysis
- `generate_thumbnail` - Auto-generate thumbnails
- `extract_highlights` - Find engaging moments
- `generate_chapters` - Auto-chapter generation
- `transcribe_media` - Speech-to-text
- `create_clip` - Extract video clips
- `upload_media` - Upload new content
- `get_media_status` - Check processing status
- `delete_media` - Remove media
- `list_media` - Browse media library

### Analytics Tools (10 tools)
- `get_viewer_stats` - Viewer metrics
- `predict_engagement` - AI predictions
- `growth_forecast` - Channel growth projections
- `recommend_content` - Content suggestions
- `analyze_audience` - Demographics analysis
- `get_revenue_report` - Revenue breakdown
- `get_retention_analysis` - Viewer retention
- `get_chat_analytics` - Chat insights
- `generate_marketing_copy` - AI copywriting
- `suggest_schedule` - Optimal scheduling

## Search Types

### BM25 (Default)
Probabilistic ranking algorithm that considers term frequency and document length:

```python
provider = ToolSearchProvider(registry, search_type="bm25")
results = provider.search("create live stream", max_results=5)
```

### Regex
Simple pattern matching for exact keyword searches:

```python
provider = ToolSearchProvider(registry, search_type="regex")
results = provider.search("event", max_results=5)
```

### Semantic (Optional)
Embeddings-based search for conceptual understanding:

```python
from src.embeddings import SemanticToolSearch

semantic = SemanticToolSearch(registry)
semantic.build_index()
results = semantic.search("start broadcasting", top_k=5)
```

## Testing

```bash
# Run all tests
pytest tests/ -v

# Run specific test file
pytest tests/test_registry.py -v

# Run with coverage
pytest tests/ --cov=src --cov-report=term-missing
```

## Performance Metrics

| Metric | Without Tool Search | With Tool Search | Improvement |
|--------|---------------------|------------------|-------------|
| Initial tokens (30 tools) | ~6,000 | ~1,500 | 75% reduction |
| Initial tokens (90 tools) | ~18,000 | ~2,000 | 89% reduction |
| Tool accuracy (baseline) | 72% | - | - |
| Tool accuracy (with examples) | - | 90% | +25% |

## Integration with BigfootLive

This package is designed to inform improvements to BigfootLive's existing Ava assistant:

1. **Porting to Elixir**: Tool definitions can be adapted to `function_registry.ex`
2. **Bedrock Integration**: Patterns work with Amazon Bedrock's function calling
3. **Input Examples**: Add to existing 90+ function definitions

## Dependencies

- `anthropic>=0.40.0` - Claude API client
- `rank-bm25>=0.2.2` - BM25 ranking algorithm
- `sentence-transformers>=2.2.0` - Semantic embeddings (optional)
- `jsonschema>=4.0.0` - Example validation
- `python-dotenv>=1.0.0` - Environment configuration
- `numpy>=1.24.0` - Numerical operations
- `pytest>=7.0.0` - Testing framework

## License

MIT License - See LICENSE file for details.

## References

- [Anthropic Tool Use Documentation](https://docs.anthropic.com/en/docs/build-with-claude/tool-use)
- [Tool Search Tool (Deferred Loading)](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/tool-search-tool)
- [Tool Use Examples](https://docs.anthropic.com/en/docs/build-with-claude/tool-use/examples)
