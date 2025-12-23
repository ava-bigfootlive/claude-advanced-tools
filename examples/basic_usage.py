#!/usr/bin/env python3
"""
Basic Usage - Demonstrates Phase 1: Tool Use Examples.

Shows how input_examples improve tool call accuracy by providing
Claude with concrete examples of valid inputs.

Run: python -m examples.basic_usage
"""

import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import ToolRegistry, AdvancedToolClient
from tools import EVENT_TOOLS


def demo_tool_registry():
    """Demonstrate tool registration with example validation."""
    print("=" * 60)
    print("Phase 1: Tool Use Examples - Registry Demo")
    print("=" * 60)

    registry = ToolRegistry()

    # Register event tools
    count = registry.register_many(EVENT_TOOLS)
    print(f"\nRegistered {count} event tools")

    # Show registered tools
    print("\nRegistered tools:")
    for name in registry.tools:
        tool = registry.tools[name]
        examples = tool.get("input_examples", [])
        print(f"  - {name}: {len(examples)} examples")

    # Show validation errors (if any)
    errors = registry.get_validation_errors()
    if errors:
        print(f"\nValidation errors: {len(errors)}")
        for error in errors:
            print(f"  ! {error}")
    else:
        print("\nAll examples validated successfully against schemas!")

    # Show API format
    print("\n" + "-" * 40)
    print("Sample tool formatted for Claude API:")
    print("-" * 40)

    api_tools = registry.get_tools_for_api(include_examples=True)
    sample = api_tools[0]  # create_event

    print(f"\nTool: {sample['name']}")
    print(f"Description: {sample['description'][:80]}...")
    print(f"\nInput Schema Properties:")
    for prop, details in list(sample['input_schema']['properties'].items())[:4]:
        print(f"  - {prop}: {details.get('type', 'object')}")
    print("  ...")

    if "input_examples" in sample:
        print(f"\nInput Examples ({len(sample['input_examples'])} total):")
        for i, example in enumerate(sample['input_examples'][:2]):
            print(f"\n  Example {i+1}:")
            for key, value in list(example.items())[:3]:
                print(f"    {key}: {value}")
            if len(example) > 3:
                print(f"    ... (+{len(example) - 3} more fields)")


def demo_tool_search():
    """Demonstrate simple tool search without deferred loading."""
    print("\n" + "=" * 60)
    print("Tool Search (Registry-based)")
    print("=" * 60)

    registry = ToolRegistry()
    registry.register_many(EVENT_TOOLS)

    queries = [
        "create",
        "stream",
        "notification",
    ]

    for query in queries:
        matches = registry.search_tools(query)
        print(f"\nSearch '{query}': {len(matches)} matches")
        for match in matches[:3]:
            print(f"  - {match}")


def demo_with_mock_client():
    """Demonstrate client usage without API calls."""
    print("\n" + "=" * 60)
    print("Mock Client Demo (no API calls)")
    print("=" * 60)

    from src.client import MockToolClient
    from tools import ALL_TOOLS

    client = MockToolClient(use_tool_search=True, use_examples=True)
    client.register_tools(ALL_TOOLS)

    print(f"\nClient configuration:")
    print(f"  Tool search enabled: {client.use_tool_search}")
    print(f"  Examples enabled: {client.use_examples}")
    print(f"  Total tools registered: {len(client.registry)}")

    # Show token savings estimate
    savings = client.estimate_token_savings()
    print(f"\nEstimated token savings with deferred loading:")
    print(f"  Tools count: {savings['tools_count']}")
    print(f"  Full load: ~{savings['estimated_full_load_tokens']:,} tokens")
    print(f"  Deferred: ~{savings['estimated_deferred_tokens']:,} tokens")
    print(f"  Savings: ~{savings['estimated_savings']:,} tokens ({savings['savings_percentage']}%)")

    # Simulate a chat (mock - no actual API call)
    messages = [{"role": "user", "content": "Create a gaming stream for tonight"}]
    response = client.chat(messages)

    print(f"\nMock response (simulated):")
    print(f"  Content: {response['content']}")
    print(f"  Stop reason: {response['stop_reason']}")

    # Show usage stats
    stats = client.get_usage_stats()
    print(f"\nUsage stats:")
    for key, value in stats.items():
        print(f"  {key}: {value}")


def main():
    """Run all demos."""
    print("\n" + "#" * 60)
    print("# Claude Advanced Tools - Basic Usage Demo")
    print("#" * 60)

    demo_tool_registry()
    demo_tool_search()
    demo_with_mock_client()

    print("\n" + "=" * 60)
    print("Demo complete!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Set ANTHROPIC_API_KEY in .env")
    print("  2. Run tool_search_demo.py for Phase 2 demo")
    print("  3. Run bigfootlive_simulation.py for full Ava-like demo")


if __name__ == "__main__":
    main()
