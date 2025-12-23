#!/usr/bin/env python3
"""
Tool Search Demo - Demonstrates Phase 2: Tool Search Tool.

Shows how deferred loading with BM25/regex search dramatically
reduces context tokens while maintaining tool discovery.

Run: python -m examples.tool_search_demo
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import ToolRegistry, ToolSearchProvider
from src.tool_search import ToolSearchSimulator
from tools import ALL_TOOLS


def demo_search_types():
    """Compare regex vs BM25 search."""
    print("=" * 60)
    print("Phase 2: Tool Search - Comparison Demo")
    print("=" * 60)

    registry = ToolRegistry()
    registry.register_many(ALL_TOOLS)

    regex_provider = ToolSearchProvider(registry, search_type="regex")
    bm25_provider = ToolSearchProvider(registry, search_type="bm25")

    queries = [
        "create event",       # Direct match
        "start streaming",    # Synonym matching (BM25 should do better)
        "analytics",          # Category search
        "thumbnail",          # Specific feature
        "schedule",           # Multiple tool match
    ]

    print(f"\nTotal tools registered: {len(registry)}")
    print("\nSearch Comparison:")
    print("-" * 60)

    for query in queries:
        regex_results = regex_provider.search(query, max_results=3)
        bm25_results = bm25_provider.search(query, max_results=3)

        print(f"\nQuery: '{query}'")
        print(f"  Regex: {[r['tool_name'] for r in regex_results]}")
        print(f"  BM25:  {[r['tool_name'] for r in bm25_results]}")


def demo_deferred_loading():
    """Show deferred loading payload structure."""
    print("\n" + "=" * 60)
    print("Deferred Loading Payload Structure")
    print("=" * 60)

    registry = ToolRegistry()
    registry.register_many(ALL_TOOLS)

    provider = ToolSearchProvider(registry, search_type="bm25")

    # Build the payload that would be sent to Claude
    payload = provider.build_tools_payload(include_examples=True)

    print(f"\nPayload structure:")
    print(f"  Total items: {len(payload)}")
    print(f"  Meta-tool: 1 (tool_search)")
    print(f"  Deferred tools: {len(payload) - 1}")

    # Show meta-tool
    meta_tool = payload[0]
    print(f"\nMeta-tool:")
    print(f"  type: {meta_tool['type']}")
    print(f"  name: {meta_tool['name']}")

    # Show deferred tool structure
    print(f"\nDeferred tool structure (sample):")
    deferred_sample = payload[1]
    print(f"  name: {deferred_sample['name']}")
    print(f"  description: {deferred_sample['description'][:60]}...")
    print(f"  defer_loading: {deferred_sample.get('defer_loading')}")
    if 'input_examples' in deferred_sample:
        print(f"  input_examples: {len(deferred_sample['input_examples'])} examples")

    # Estimate token savings
    print("\n" + "-" * 40)
    print("Token Savings Estimate:")
    print("-" * 40)

    # Rough estimates
    avg_tokens_per_tool = 200
    meta_tool_tokens = 100
    deferred_overhead = 50  # Per tool when deferred

    full_load = len(registry) * avg_tokens_per_tool
    deferred_load = meta_tool_tokens + (len(registry) * deferred_overhead)
    savings = full_load - deferred_load
    savings_pct = (savings / full_load) * 100

    print(f"\n  Tools: {len(registry)}")
    print(f"  Full load: ~{full_load:,} tokens")
    print(f"  Deferred load: ~{deferred_load:,} tokens")
    print(f"  Savings: ~{savings:,} tokens ({savings_pct:.0f}%)")


def demo_search_simulator():
    """Simulate Claude's tool search behavior."""
    print("\n" + "=" * 60)
    print("Tool Search Simulator")
    print("=" * 60)

    registry = ToolRegistry()
    registry.register_many(ALL_TOOLS)

    provider = ToolSearchProvider(registry, search_type="bm25")
    simulator = ToolSearchSimulator(provider)

    print("\nSimulating how Claude would discover tools:")
    print("-" * 40)

    # User asks about creating an event
    print("\nUser: 'Help me create a live streaming event'")
    print("Claude: [Calls tool_search with query='create event streaming']")

    result = simulator.simulate_search_call("create event streaming")
    print(f"\nSearch results:")
    for ref in result['content'][:3]:
        print(f"  - {ref['tool_name']}")

    # Claude now has access to these tools
    expanded = simulator.expand_references(result['content'][:2])
    print(f"\nExpanded tool definitions:")
    for tool in expanded:
        print(f"  - {tool['name']}: {tool['description'][:50]}...")

    # Another search
    print("\n" + "-" * 40)
    print("\nUser: 'Can you analyze my video for highlights?'")
    print("Claude: [Calls tool_search with query='analyze video highlights']")

    result = simulator.simulate_search_call("analyze video highlights")
    print(f"\nSearch results:")
    for ref in result['content'][:3]:
        print(f"  - {ref['tool_name']}")

    # Show search history
    print("\n" + "-" * 40)
    print("Search history:")
    for i, entry in enumerate(simulator.get_history()):
        print(f"  {i+1}. '{entry['query']}' -> {len(entry['results'])} results")


def demo_semantic_search():
    """Demo semantic search (if sentence-transformers available)."""
    print("\n" + "=" * 60)
    print("Semantic Search (Optional Enhancement)")
    print("=" * 60)

    try:
        from src.embeddings import SemanticToolSearch, HybridToolSearch

        registry = ToolRegistry()
        registry.register_many(ALL_TOOLS)

        print("\nBuilding semantic index...")
        semantic = SemanticToolSearch(registry)
        semantic.build_index()

        stats = semantic.get_stats()
        print(f"\nSemantic search stats:")
        print(f"  Model: {stats['model_name']}")
        print(f"  Indexed tools: {stats['indexed_tools']}")
        print(f"  Embedding dimensions: {stats['embedding_dimensions']}")

        # Semantic vs keyword search
        queries = [
            "start broadcasting",     # BM25 might miss "start_event"
            "viewer engagement",      # Conceptual query
            "make a clip",            # Natural language
        ]

        print("\nSemantic Search Demo:")
        print("-" * 40)

        bm25_provider = ToolSearchProvider(registry, search_type="bm25")

        for query in queries:
            bm25_results = bm25_provider.search(query, max_results=3)
            semantic_results = semantic.search(query, top_k=3)

            print(f"\nQuery: '{query}'")
            print(f"  BM25: {[r['tool_name'] for r in bm25_results]}")
            print(f"  Semantic: {[r['tool_name'] for r in semantic_results]}")
            if semantic_results:
                scores = [f"{r['score']:.3f}" for r in semantic_results]
                print(f"  Scores: {scores}")

    except ImportError as e:
        print(f"\nSemantic search not available: {e}")
        print("Install with: pip install sentence-transformers")


def main():
    """Run all Phase 2 demos."""
    print("\n" + "#" * 60)
    print("# Claude Advanced Tools - Tool Search Demo (Phase 2)")
    print("#" * 60)

    demo_search_types()
    demo_deferred_loading()
    demo_search_simulator()
    demo_semantic_search()

    print("\n" + "=" * 60)
    print("Phase 2 Demo Complete!")
    print("=" * 60)
    print("\nKey takeaways:")
    print("  1. BM25 provides better relevance ranking than regex")
    print("  2. Deferred loading can save 80%+ tokens")
    print("  3. Semantic search understands intent beyond keywords")
    print("  4. tool_reference blocks enable on-demand tool expansion")


if __name__ == "__main__":
    main()
