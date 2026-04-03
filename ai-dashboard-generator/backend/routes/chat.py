from __future__ import annotations

from typing import Any, Dict

import pandas as pd
from fastapi import APIRouter, HTTPException

from models.schemas import ChatRequest
from services.csv_processor import merge_on_common_columns
from services.dashboard_engine import create_plotly_charts, generate_chart_config, interpret_query
from services.llm_service import prompt_templates, query_llm
from services.vector_store import VectorStoreService
from utils.state import STATE


router = APIRouter()
vector_store = VectorStoreService()


def _analytical_answer(df: pd.DataFrame, schema: Dict[str, Any], query: str) -> str | None:
    q = query.lower()
    numeric = schema.get("numeric") or []
    cat = schema.get("categorical") or []
    if not numeric:
        return None
    y = numeric[0]
    s = pd.to_numeric(df[y], errors="coerce").dropna()
    if len(s) == 0:
        return None
    if "total" in q or "sum" in q:
        return f"Total {y}: {float(s.sum()):.2f}"
    if "mean" in q or "average" in q:
        return f"Average {y}: {float(s.mean()):.2f}"
    if "top" in q and cat:
        x = cat[0]
        g = df[[x, y]].copy()
        g[y] = pd.to_numeric(g[y], errors="coerce")
        g = g.dropna(subset=[x, y]).groupby(x)[y].sum().sort_values(ascending=False).head(5)
        lines = [f"Top 5 by {y} grouped by {x}:"]
        for k, v in g.items():
            lines.append(f"- {k}: {float(v):.2f}")
        return "\n".join(lines)
    return None


@router.post("/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    if not STATE.datasets:
        raise HTTPException(status_code=400, detail="Upload datasets first.")

    active = req.active_dataset if req.active_dataset in STATE.datasets else next(iter(STATE.datasets.keys()))
    query = req.query.strip()
    if not query:
        raise HTTPException(status_code=400, detail="Query is empty.")

    intent = interpret_query(query)

    # Dashboard mode
    if intent["needs_dashboard"]:
        df = STATE.datasets[active]
        schema = STATE.schemas[active]
        cfg = generate_chart_config(query, schema)
        dash = create_plotly_charts(df, cfg)
        STATE.last_dashboard = dash
        return {"mode": "dashboard", "response": "Dashboard generated.", "dashboard": dash}

    # Analytics mode
    analytic = _analytical_answer(STATE.datasets[active], STATE.schemas[active], query)
    if analytic:
        return {"mode": "analytical", "response": analytic}

    # Multi-dataset join capability
    if "join" in query.lower() and len(STATE.datasets) > 1:
        merged = merge_on_common_columns(STATE.datasets)
        if merged is not None:
            schema = {
                "columns": [str(c) for c in merged.columns],
                "row_count": int(len(merged)),
            }
            return {"mode": "analytical", "response": f"Joined dataset created with {schema['row_count']} rows.", "data": schema}

    # Semantic RAG mode
    hits = vector_store.similarity_search(active, query, k=6)
    context = "\n".join([h["text"] for h in hits])
    system = prompt_templates()["chat"] + f"\nDataset schema:\n{STATE.schemas[active]}\nRAG context:\n{context}"
    resp = await query_llm(system, query, req.history)
    return {"mode": "semantic", "response": resp}

