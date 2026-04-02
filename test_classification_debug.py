#!/usr/bin/env python3
"""
Verify the exact classification logic step by step.
"""

async def test_classify(message: str) -> str:
    m = message.lower()
    
    # ── Fast keyword-based rules (high confidence) ──
    stats_keywords = ["total ", "average ", "statistics", "how much", "how many", " sum ",                          " count ", "aggregate", "metrics", "median ", "maximum ", "minimum ",
                         "standard deviation", "variance"]
    
    chart_keywords = ["trend", "pattern", "distribution", "compare", "correlation",                          "dashboard", "analysis", "visualize", "graph", "chart", "plot"]
    
    table_keywords = ["show data", "display records", "show table", "raw data", "view records",
                         "show me the data", "display all"]
    
    print(f"Message: {message}")
    print(f"Lowercase: {m}\n")
    
    # Check STATS
    stats_matches = [kw for kw in stats_keywords if kw in m]
    print(f"STATS keyword matches: {stats_matches}")
    if any(kw in m for kw in stats_keywords):
        print("=> Returning: STATS")
        return "STATS"
    
    # Check CHART
    chart_matches = [kw for kw in chart_keywords if kw in m]
    print(f"CHART keyword matches: {chart_matches}")
    if any(kw in m for kw in chart_keywords):
        print("=> Returning: CHART")
        return "CHART"
    
    print("=> Returning: CHAT (fallback)")
    return "CHAT"

if __name__ == "__main__":
    import asyncio
    
    tests = [
        "What is the total amount and average payment value?",
        "Show me statistics on payment status",
        "Show me an analysis of payment distribution",
    ]
    
    for test_msg in tests:
        print("=" * 70)
        result = asyncio.run(test_classify(test_msg))
        print(f"RESULT: {result}\n")
