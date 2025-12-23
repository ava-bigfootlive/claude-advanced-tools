#!/usr/bin/env python3
"""
BigfootLive Simulation - Ava-like AI assistant demo.

Simulates how advanced tool use patterns could enhance
BigfootLive's existing Ava assistant with 90+ functions.

Run: python -m examples.bigfootlive_simulation
     ANTHROPIC_API_KEY=... python -m examples.bigfootlive_simulation --live

Features demonstrated:
- Phase 1: Tool examples for improved accuracy
- Phase 2: Tool search for reduced context
- Multi-turn conversation with tool execution
"""

import os
import sys
import argparse
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src import AdvancedToolClient, ToolRegistry, ToolSearchProvider
from src.client import MockToolClient
from tools import ALL_TOOLS


# Simulated tool handlers (would connect to real BigfootLive backend)
TOOL_HANDLERS = {
    "create_event": lambda input: {
        "success": True,
        "event_id": "new-event-123",
        "title": input.get("title"),
        "status": "scheduled",
        "stream_key": "sk_live_abc123xyz"
    },
    "start_event": lambda input: {
        "success": True,
        "event_id": input.get("event_id"),
        "status": "live",
        "viewer_count": 0,
        "stream_url": f"https://stream.bigfootlive.io/{input.get('event_id')}"
    },
    "get_viewer_stats": lambda input: {
        "event_id": input.get("event_id"),
        "current_viewers": 42,
        "peak_viewers": 128,
        "avg_watch_time": "12:34",
        "chat_messages": 256
    },
    "analyze_media": lambda input: {
        "media_id": input.get("media_id"),
        "analysis_types": input.get("analysis_types"),
        "status": "processing",
        "estimated_completion": "2 minutes"
    },
    "generate_marketing_copy": lambda input: {
        "variations": [
            "🎮 LIVE NOW: Epic gaming session! Join the fun! #gaming #live",
            "Don't miss tonight's stream - starting soon! 🔴",
            "Your weekly dose of gaming goodness is HERE! Tune in now! 🎮✨"
        ],
        "copy_type": input.get("copy_type"),
        "platform": input.get("platform", "generic")
    }
}


def default_handler(name):
    """Default handler for tools without specific implementation."""
    def handler(input):
        return {
            "tool": name,
            "status": "simulated",
            "input_received": input,
            "message": f"Tool '{name}' would be executed with the provided input"
        }
    return handler


def demo_mock_conversation():
    """Demonstrate a multi-turn conversation without API calls."""
    print("=" * 60)
    print("BigfootLive Ava Simulation (Mock Mode)")
    print("=" * 60)
    print("\nThis demo shows how Ava would use advanced tool patterns")
    print("without making actual API calls.")

    client = MockToolClient(use_tool_search=True, use_examples=True)
    client.register_tools(ALL_TOOLS)

    # Simulated conversation flow
    conversation = [
        {
            "user": "Hey Ava, I want to set up a gaming stream for tonight at 7pm",
            "expected_tools": ["create_event"],
            "mock_response": "I'll help you create a gaming stream! Let me set that up for 7pm tonight."
        },
        {
            "user": "Great! Can you also generate some promotional tweets?",
            "expected_tools": ["generate_marketing_copy"],
            "mock_response": "Here are some promotional tweets for your stream..."
        },
        {
            "user": "How many viewers did my last stream get?",
            "expected_tools": ["get_viewer_stats"],
            "mock_response": "Your last stream had 128 peak viewers with an average watch time of 12 minutes."
        }
    ]

    print("\n" + "-" * 40)
    print("Simulated Conversation:")
    print("-" * 40)

    for turn in conversation:
        print(f"\n👤 User: {turn['user']}")
        print(f"🔧 Expected tools: {turn['expected_tools']}")
        print(f"🤖 Ava: {turn['mock_response']}")

    # Show stats
    print("\n" + "-" * 40)
    print("Session Statistics:")
    print("-" * 40)

    savings = client.estimate_token_savings()
    print(f"\n  Tools registered: {len(client.registry)}")
    print(f"  Token savings: ~{savings['savings_percentage']}%")
    print(f"  Tool search: {'enabled' if client.use_tool_search else 'disabled'}")
    print(f"  Examples: {'enabled' if client.use_examples else 'disabled'}")


def demo_live_conversation(client):
    """Run an actual conversation with Claude API."""
    print("=" * 60)
    print("BigfootLive Ava Simulation (Live Mode)")
    print("=" * 60)
    print("\nThis demo makes real API calls to Claude.")

    # System prompt mimicking Ava's personality
    system_prompt = """You are Ava, the friendly AI assistant for BigfootLive -
a live streaming and video platform. You help creators manage their events,
analyze their content, and grow their audience.

Your personality:
- Friendly and supportive
- Knowledgeable about streaming and content creation
- Proactive with suggestions
- Concise but helpful

You have access to various tools for event management, media analysis,
and analytics. Use them to help creators succeed!

When you need to find the right tool, use the tool_search capability
to discover relevant tools for the task at hand."""

    # Build handlers dict
    handlers = {}
    for name in client.registry.tools:
        if name in TOOL_HANDLERS:
            handlers[name] = TOOL_HANDLERS[name]
        else:
            handlers[name] = default_handler(name)

    # Interactive conversation loop
    print("\nStarting interactive session. Type 'quit' to exit.")
    print("-" * 40)

    messages = []

    while True:
        try:
            user_input = input("\n👤 You: ").strip()
        except (EOFError, KeyboardInterrupt):
            break

        if user_input.lower() in ('quit', 'exit', 'q'):
            break

        if not user_input:
            continue

        # Add user message
        messages.append({"role": "user", "content": user_input})

        # Get response
        try:
            response = client.chat(
                messages=messages,
                system=system_prompt,
                tool_handlers=handlers
            )

            # Display response
            print(f"\n🤖 Ava: {response['content']}")

            # Show tool calls if any
            if response['tool_calls']:
                print(f"\n   🔧 Tools used: {[tc['name'] for tc in response['tool_calls']]}")

            # Add assistant response to history
            messages.append({
                "role": "assistant",
                "content": response['content']
            })

            # Show usage
            print(f"   📊 Tokens: {response['usage']['input_tokens']} in / {response['usage']['output_tokens']} out")

        except Exception as e:
            print(f"\n❌ Error: {e}")

    # Final stats
    print("\n" + "-" * 40)
    print("Session Complete!")
    print("-" * 40)
    stats = client.get_usage_stats()
    print(f"\n  Total requests: {stats['total_requests']}")
    print(f"  Total tokens: {stats['total_tokens']}")
    print(f"  Tools registered: {stats['registered_tools']}")


def demo_tool_discovery():
    """Show how tool discovery works with 30+ tools."""
    print("=" * 60)
    print("Tool Discovery Demo (30+ tools)")
    print("=" * 60)

    registry = ToolRegistry()
    registry.register_many(ALL_TOOLS)

    provider = ToolSearchProvider(registry, search_type="bm25")

    print(f"\nTotal tools available: {len(registry)}")
    print("\nThis simulates how Ava would discover tools:")

    # Sample queries a user might ask
    queries = [
        ("I want to go live", ["start_event", "create_event"]),
        ("analyze my video", ["analyze_media", "extract_highlights"]),
        ("how's my channel doing", ["get_viewer_stats", "growth_forecast"]),
        ("make a clip", ["create_clip", "extract_highlights"]),
        ("schedule my streams", ["suggest_schedule", "create_event"]),
    ]

    print("\n" + "-" * 40)
    for user_query, expected in queries:
        results = provider.search(user_query, max_results=3)
        found = [r['tool_name'] for r in results]

        # Check if expected tools were found
        matches = set(found) & set(expected)
        status = "✓" if matches else "○"

        print(f"\n{status} Query: '{user_query}'")
        print(f"  Found: {found}")
        print(f"  Expected: {expected}")


def main():
    """Run the BigfootLive simulation."""
    parser = argparse.ArgumentParser(
        description="BigfootLive Ava AI Assistant Simulation"
    )
    parser.add_argument(
        "--live",
        action="store_true",
        help="Use real Claude API (requires ANTHROPIC_API_KEY)"
    )
    parser.add_argument(
        "--no-examples",
        action="store_true",
        help="Disable input_examples (for comparison)"
    )
    parser.add_argument(
        "--no-search",
        action="store_true",
        help="Disable tool search (for comparison)"
    )
    args = parser.parse_args()

    print("\n" + "#" * 60)
    print("# BigfootLive Ava AI Assistant")
    print("# Advanced Tool Use Demonstration")
    print("#" * 60)

    if args.live:
        # Live mode with real API
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            print("\n❌ Error: ANTHROPIC_API_KEY environment variable required for live mode")
            print("   Set it with: export ANTHROPIC_API_KEY=your-key-here")
            sys.exit(1)

        client = AdvancedToolClient(
            api_key=api_key,
            use_tool_search=not args.no_search,
            use_examples=not args.no_examples
        )
        client.register_tools(ALL_TOOLS)

        demo_live_conversation(client)
    else:
        # Mock mode - no API calls
        demo_tool_discovery()
        print()
        demo_mock_conversation()

    print("\n" + "=" * 60)
    print("Simulation Complete!")
    print("=" * 60)
    print("\nTo run with real Claude API:")
    print("  ANTHROPIC_API_KEY=sk-... python -m examples.bigfootlive_simulation --live")


if __name__ == "__main__":
    main()
