#!/usr/bin/env python3
"""Compare token usage with and without tool search.

The key insight: With defer_loading, Claude only sees tool NAMES and
brief descriptions initially. Full schemas are loaded on-demand when
Claude decides to use a specific tool via tool_reference.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src import ToolRegistry
from tools import ALL_TOOLS
import json

def estimate_tokens(text: str) -> int:
    """Rough token estimate (4 chars = 1 token)."""
    return len(text) // 4

def main():
    registry = ToolRegistry()
    registry.register_many(ALL_TOOLS)
    
    print(f"Registered tools: {len(registry)}\n")
    
    # ====== TRADITIONAL: Full tool definitions upfront ======
    full_tools = registry.get_tools_for_api(include_examples=True)
    full_json = json.dumps(full_tools, indent=2)
    full_tokens = estimate_tokens(full_json)
    
    # ====== DEFERRED: Only meta-tool + tool summaries ======
    # What Claude actually sees initially with defer_loading
    meta_tool = {
        "type": "tool_search_tool_bm25_20251119",
        "name": "tool_search"
    }
    
    # Minimal tool references (name + short description only)
    tool_summaries = [
        {
            "name": tool["name"],
            "description": tool["description"][:100] + "..." if len(tool["description"]) > 100 else tool["description"],
            "defer_loading": True
        }
        for tool in full_tools
    ]
    
    deferred_payload = [meta_tool] + tool_summaries
    deferred_json = json.dumps(deferred_payload, indent=2)
    deferred_tokens = estimate_tokens(deferred_json)
    
    # ====== WHEN TOOL IS USED: Single tool expansion ======
    # When Claude calls a tool, only THAT tool's full definition is loaded
    single_tool = full_tools[0]  # Example: one tool
    single_json = json.dumps(single_tool, indent=2)
    single_tokens = estimate_tokens(single_json)
    
    # Results
    print("=" * 60)
    print("TOKEN USAGE COMPARISON")
    print("=" * 60)
    
    print(f"\n📦 TRADITIONAL (all tools upfront):")
    print(f"   Tools sent: {len(full_tools)} complete definitions")
    print(f"   JSON size: {len(full_json):,} chars")
    print(f"   Est. tokens: ~{full_tokens:,}")
    
    print(f"\n🔍 DEFERRED (tool search pattern):")
    print(f"   Initial: meta-tool + {len(tool_summaries)} summaries")
    print(f"   JSON size: {len(deferred_json):,} chars")
    print(f"   Est. tokens: ~{deferred_tokens:,}")
    
    print(f"\n📌 PER-TOOL (when actually used):")
    print(f"   Each tool call adds: ~{single_tokens} tokens")
    
    savings = full_tokens - deferred_tokens
    pct = (savings / full_tokens * 100) if full_tokens > 0 else 0
    
    print(f"\n{'=' * 60}")
    print(f"💰 INITIAL CONTEXT SAVINGS: ~{savings:,} tokens ({pct:.1f}% reduction)")
    print(f"{'=' * 60}")
    
    print(f"\n💡 Break-even: If Claude uses <{savings // single_tokens} tools per request,")
    print(f"   deferred loading uses FEWER total tokens.")
    
    # Show example scenarios
    print(f"\n📊 SCENARIO COMPARISON (30 tools registered):")
    print(f"   {'Scenario':<30} {'Traditional':>12} {'Deferred':>12} {'Savings':>10}")
    print(f"   {'-'*30} {'-'*12} {'-'*12} {'-'*10}")
    
    for tools_used in [0, 1, 2, 3, 5, 10]:
        trad = full_tokens
        defer = deferred_tokens + (tools_used * single_tokens)
        save = trad - defer
        save_pct = (save / trad * 100) if trad > 0 else 0
        print(f"   Uses {tools_used} tool(s){' '*(21-len(str(tools_used)))} {trad:>10,}  {defer:>10,}  {save:>+8,} ({save_pct:+.0f}%)")

if __name__ == "__main__":
    main()
