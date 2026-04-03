"""
Dashboard generation prompt and utilities.
Used by RAG agent for intelligent chart recommendations.
"""

DASHBOARD_PROMPT = """You are a senior business intelligence analyst.

A dataset has been uploaded. Here is what was automatically detected:

{context}

Generate 6 chart configurations for a dashboard. 

STRICT RULES:
- Use ONLY the column names exactly as they appear above
- Do NOT mention Q1/Q2/Q3/Q4 unless those values exist in the data
- Choose chart type based on the data shape:
  * One category vs one number → bar (vertical or horizontal)
  * Trend over time → line or area
  * Share/composition → pie (max 8 slices)  
  * Two numbers vs each other → scatter
- For the time column use whatever grouping fits the detected date range
- Priority order: total revenue breakdown FIRST, trends SECOND, 
  distributions THIRD
- Every chart needs an "insight" field — one business sentence about 
  what this chart reveals

Return ONLY a valid JSON array, no markdown, no explanation:
[
  {{
    "type": "bar",
    "title": "Top 15 clients by total revenue value",
    "xKey": "<exact client column name from above>",
    "yKey": "<exact amount column name from above>",
    "chartStyle": "horizontal",
    "insight": "One sentence about what this reveals",
    "priority": 1
  }},
  ...
]"""


def get_dashboard_prompt(context: str) -> str:
    """Generate dashboard prompt with dataset context."""
    return DASHBOARD_PROMPT.format(context=context)
