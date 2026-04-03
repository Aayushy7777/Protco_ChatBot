from __future__ import annotations

import json
import re
from typing import Any, Dict, Literal, Optional

from app.services.llm_router import get_intent_classifier_llm


Intent = Literal["SQL", "DASHBOARD", "TOP_N", "FILTER_BANK", "CHART", "TABLE", "CHAT"]


def quick_intent_heuristic(message: str) -> Optional[Intent]:
    m = (message or "").lower()
    if not m:
        return None
    if any(k in m for k in ["sql", "query", "postgres", "mysql", "snowflake", "bigquery"]):
        return "SQL"
    if "dashboard" in m or "make me dashboard" in m or "auto dashboard" in m:
        return "DASHBOARD"
    if re.search(r"\btop\s+\d+\b", m) and any(k in m for k in ["customer", "client", "party", "vendor"]):
        return "TOP_N"
    if "bank" in m and "through" in m:
        return "FILTER_BANK"
    return None


def classify_intent(message: str) -> Intent:
    """
    Deterministic intent classifier backed by llama3.1:8b (temp=0.0).
    Returns one of the Intent literals.
    """
    heuristic = quick_intent_heuristic(message)
    if heuristic:
        return heuristic

    llm = get_intent_classifier_llm()
    prompt = f"""
You are an intent classifier for a CSV analytics assistant.
Return JSON only with schema: {{"intent": "<one_of>"}}.

Allowed intents:
- SQL: user asks to generate SQL, queries, or database-like filtering/joins.
- DASHBOARD: user asks to generate a dashboard.
- TOP_N: top N customers/clients/vendors/parties.
- FILTER_BANK: customer payments through a specific bank.
- CHART: user explicitly requests a chart.
- TABLE: user explicitly requests a table/list.
- CHAT: everything else.

Message:
{message}
""".strip()

    res = llm.invoke(prompt)
    content = res.content if hasattr(res, "content") else str(res)
    try:
        data = json.loads(content)
        intent = str(data.get("intent") or "").upper()
        if intent in {"SQL", "DASHBOARD", "TOP_N", "FILTER_BANK", "CHART", "TABLE", "CHAT"}:
            return intent  # type: ignore[return-value]
    except Exception:
        pass
    return "CHAT"

