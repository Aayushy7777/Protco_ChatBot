"""
Dashboard generation prompt and utilities.
Used by RAG agent for intelligent chart recommendations.
"""

DASHBOARD_PROMPT = """You are a senior business intelligence analyst.
Given this dataset profile, generate exactly 8 chart configurations for an executive dashboard.

Dataset profile:
{context}

Return ONLY a valid JSON array. No markdown. No explanation.

Rules for chart selection:
1. ALWAYS include a "Revenue by company" bar chart if revenue/amount column exists
2. ALWAYS include a "Monthly trend" line chart if a date column exists  
3. ALWAYS include a "Top 10 clients by value" horizontal bar chart
4. ALWAYS include a "Quarter-wise comparison" grouped bar chart if quarter data exists
5. Include a pie chart for category/region distribution (max 8 slices)
6. Include a scatter plot only if 2 meaningful numeric correlations exist
7. Sort by business impact — revenue charts first, operational last
8. Every chart MUST have an "insight" field: one sentence saying what action this chart suggests

Each object must have:
- type: "bar" | "line" | "pie" | "scatter" | "area"
- title: clear business title (e.g. "Top 10 clients by revenue Q2")
- xKey: exact column name
- yKey: exact column name  
- insight: "Bhadra Electric accounts for 6.65% of total revenue — consider dedicated account manager"
- priority: 1–8
- chartStyle: "horizontal" | "vertical" | "stacked" (for bar charts)

Return JSON array now:"""


def get_dashboard_prompt(context: str) -> str:
    """Generate dashboard prompt with dataset context."""
    return DASHBOARD_PROMPT.format(context=context)
