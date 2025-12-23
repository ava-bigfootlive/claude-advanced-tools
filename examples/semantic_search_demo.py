#!/usr/bin/env python3
"""
Semantic Search Demo - Advanced Tool Discovery

Demonstrates semantic and hybrid search for conceptual tool matching.

Features:
- Semantic search using SentenceTransformer embeddings
- Hybrid search combining BM25 + semantic for best results
- Comparison across all search modes (bm25, regex, semantic, hybrid)

Usage:
    python -m examples.semantic_search_demo
"""

import sys
import time
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import ToolRegistry
from src.tool_search import ToolSearchProvider
from src.embeddings import SemanticToolSearch, HybridToolSearch
from tools import ALL_TOOLS


def print_header(title: str):
    """Print a formatted header."""
    print(f"\n{'='*60}")
    print(f"  {title}")
    print(f"{'='*60}\n")


def demo_search_comparison():
    """Compare different search modes on the same queries."""
    print_header("SEARCH MODE COMPARISON")

    # Register tools
    registry = ToolRegistry()
    registry.register_many(ALL_TOOLS)
    print(f"Registered {len(registry)} tools\n")

    # Initialize search providers
    bm25_provider = ToolSearchProvider(registry, search_type="bm25")
    semantic_search = SemanticToolSearch(registry)
    hybrid_search = HybridToolSearch(registry)

    # Build indices
    print("Building search indices...")
    semantic_search.build_index()
    hybrid_search.build_indices()
    print("Done.\n")

    # Test queries that benefit from semantic understanding
    test_queries = [
        # Conceptual queries (semantic excels)
        "I want to start broadcasting",
        "help me understand my viewers",
        "make my content more engaging",
        "automatically find the best moments",

        # Specific queries
        "create a new event",
        "get viewer statistics",

        # Ambiguous queries
        "go live",
        "money report",
    ]

    for query in test_queries:
        print(f"Query: \"{query}\"")
        print("-" * 50)

        # BM25 search
        bm25_results = bm25_provider.search(query, max_results=3)
        print("  BM25:")
        for r in bm25_results[:3]:
            print(f"    - {r['tool_name']}")

        # Semantic search
        semantic_results = semantic_search.search(query, top_k=3)
        print("  Semantic:")
        for r in semantic_results[:3]:
            print(f"    - {r['tool_name']} ({r.get('score', 0):.3f})")

        # Hybrid search
        hybrid_results = hybrid_search.search(query, top_k=3)
        print("  Hybrid:")
        for r in hybrid_results[:3]:
            print(f"    - {r['tool_name']} ({r.get('score', 0):.3f})")

        print()


def demo_semantic_advantages():
    """Show scenarios where semantic search outperforms keyword search."""
    print_header("SEMANTIC SEARCH ADVANTAGES")

    registry = ToolRegistry()
    registry.register_many(ALL_TOOLS)

    bm25_provider = ToolSearchProvider(registry, search_type="bm25")
    semantic_search = SemanticToolSearch(registry)
    semantic_search.build_index()

    # Queries where semantic understanding helps
    scenarios = [
        {
            "description": "User uses different terminology",
            "query": "broadcast my stream",
            "expected": "start_event",
        },
        {
            "description": "User describes intent, not action",
            "query": "make money from viewers",
            "expected": "get_revenue_report",
        },
        {
            "description": "User asks about concepts",
            "query": "who is watching my content",
            "expected": "analyze_audience",
        },
        {
            "description": "Synonyms and related terms",
            "query": "video highlights automatically",
            "expected": "extract_highlights",
        },
    ]

    for scenario in scenarios:
        print(f"\nScenario: {scenario['description']}")
        print(f"Query: \"{scenario['query']}\"")
        print(f"Expected: {scenario['expected']}")

        # BM25 results
        bm25_results = bm25_provider.search(scenario['query'], max_results=3)
        bm25_names = [r['tool_name'] for r in bm25_results]

        # Semantic results
        semantic_results = semantic_search.search(scenario['query'], top_k=3)
        semantic_names = [r['tool_name'] for r in semantic_results]

        print(f"  BM25 top 3: {bm25_names}")
        print(f"  Semantic top 3: {semantic_names}")

        # Check which found the expected tool
        bm25_found = scenario['expected'] in bm25_names
        semantic_found = scenario['expected'] in semantic_names

        if semantic_found and not bm25_found:
            print(f"  ✓ Semantic found '{scenario['expected']}', BM25 missed it")
        elif semantic_found and bm25_found:
            bm25_rank = bm25_names.index(scenario['expected']) + 1
            semantic_rank = semantic_names.index(scenario['expected']) + 1
            if semantic_rank < bm25_rank:
                print(f"  ✓ Semantic ranked higher ({semantic_rank}) vs BM25 ({bm25_rank})")
            else:
                print(f"  = Both found it (semantic: {semantic_rank}, bm25: {bm25_rank})")
        elif bm25_found:
            print(f"  BM25 found it, semantic missed")
        else:
            print(f"  Neither found '{scenario['expected']}' in top 3")


def demo_hybrid_search():
    """Demonstrate hybrid search combining BM25 and semantic."""
    print_header("HYBRID SEARCH DEMO")

    registry = ToolRegistry()
    registry.register_many(ALL_TOOLS)

    # Test different weight configurations
    weight_configs = [
        (0.3, 0.7, "Semantic-heavy (0.3 BM25, 0.7 Semantic)"),
        (0.5, 0.5, "Balanced (0.5 BM25, 0.5 Semantic)"),
        (0.7, 0.3, "BM25-heavy (0.7 BM25, 0.3 Semantic)"),
    ]

    query = "I want to understand my audience better"
    print(f"Query: \"{query}\"\n")

    for bm25_weight, semantic_weight, description in weight_configs:
        hybrid = HybridToolSearch(
            registry,
            bm25_weight=bm25_weight,
            semantic_weight=semantic_weight
        )
        hybrid.build_indices()

        results = hybrid.search(query, top_k=5)

        print(f"{description}:")
        for r in results:
            print(f"  - {r['tool_name']} ({r.get('score', 0):.3f})")
        print()


def demo_performance():
    """Compare search latency across modes."""
    print_header("PERFORMANCE COMPARISON")

    registry = ToolRegistry()
    registry.register_many(ALL_TOOLS)

    # Initialize all search providers
    bm25 = ToolSearchProvider(registry, search_type="bm25")
    regex = ToolSearchProvider(registry, search_type="regex")
    semantic = SemanticToolSearch(registry)
    hybrid = HybridToolSearch(registry)

    print("Building indices (one-time cost)...")
    start = time.time()
    semantic.build_index()
    print(f"  Semantic index: {time.time() - start:.3f}s")

    start = time.time()
    hybrid.build_indices()
    print(f"  Hybrid index: {time.time() - start:.3f}s")

    # Run searches
    queries = ["create event", "analyze video", "get statistics", "start streaming"]
    iterations = 10

    print(f"\nSearch latency ({iterations} iterations each):")

    for name, search_fn in [
        ("BM25", lambda q: bm25.search(q, max_results=5)),
        ("Regex", lambda q: regex.search(q, max_results=5)),
        ("Semantic", lambda q: semantic.search(q, top_k=5)),
        ("Hybrid", lambda q: hybrid.search(q, top_k=5)),
    ]:
        times = []
        for _ in range(iterations):
            for query in queries:
                start = time.time()
                search_fn(query)
                times.append(time.time() - start)

        avg_time = sum(times) / len(times)
        print(f"  {name}: {avg_time*1000:.2f}ms avg per query")


def demo_auto_search():
    """Demonstrate auto search mode that picks the best strategy."""
    print_header("AUTO SEARCH MODE DEMO")

    # Need to mock anthropic for demo since we don't have API key
    import sys
    from unittest.mock import MagicMock
    mock_anthropic = MagicMock()
    mock_anthropic.Anthropic = MagicMock()
    sys.modules['anthropic'] = mock_anthropic

    from src.client import AdvancedToolClient

    client = AdvancedToolClient(
        api_key="fake-key",
        search_mode="auto"
    )
    client.register_tools(ALL_TOOLS)

    # Build indices
    client.semantic_search.build_index()
    client.hybrid_search.build_indices()

    print("Auto mode intelligently picks the best search strategy:\n")

    test_cases = [
        # (query, expected_mode, description)
        ("create event", "bm25", "Short keyword → BM25 (fast exact match)"),
        (".*event.*", "regex", "Pattern with wildcards → Regex"),
        ("I want to start broadcasting live", "semantic", "Conversational → Semantic (understands intent)"),
        ("revenue report tool", "hybrid", "Medium uncertainty → Hybrid (best of both)"),
        ("help me understand my viewers", "semantic", "Natural language question → Semantic"),
    ]

    for query, expected_mode, description in test_cases:
        detected = client._detect_search_mode(query)
        results = client.search_tools(query, max_results=3)
        tool_names = [r["tool_name"] for r in results[:3]]

        status = "✓" if detected == expected_mode else "≠"
        print(f'{status} "{query}"')
        print(f"    {description}")
        print(f"    Detected: {detected}, Results: {tool_names}\n")


def main():
    """Run all semantic search demos."""
    print("\n" + "="*60)
    print("   SEMANTIC SEARCH DEMO")
    print("   Advanced Tool Discovery with Embeddings")
    print("="*60)

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        print("\nError: sentence-transformers not installed.")
        print("Install with: pip install sentence-transformers")
        sys.exit(1)

    demo_search_comparison()
    demo_semantic_advantages()
    demo_hybrid_search()
    demo_auto_search()
    demo_performance()

    print("\n" + "="*60)
    print("   Demo Complete!")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
