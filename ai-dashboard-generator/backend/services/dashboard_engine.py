from __future__ import annotations

import json
import re
from typing import Any, Dict, List

import pandas as pd
import plotly.express as px


def interpret_query(query: str) -> Dict[str, Any]:
    q = query.lower()
    return {
        "needs_dashboard": any(x in q for x in ["dashboard", "show", "visual", "chart", "trend", "compare"]),
        "needs_trend": any(x in q for x in ["trend", "over time", "monthly", "daily"]),
        "needs_top": any(x in q for x in ["top", "highest", "best"]),
        "needs_distribution": any(x in q for x in ["distribution", "share", "composition", "pie"]),
    }


def _pick_cols(schema: Dict[str, Any]) -> Dict[str, str | None]:
    numeric = schema.get("numeric") or []
    categorical = schema.get("categorical") or []
    dt = schema.get("datetime") or []
    return {
        "x_time": dt[0] if dt else None,
        "x_cat": categorical[0] if categorical else None,
        "y": numeric[0] if numeric else None,
    }


def generate_chart_config(query: str, schema: Dict[str, Any]) -> Dict[str, Any]:
    i = interpret_query(query)
    cols = _pick_cols(schema)
    charts: List[Dict[str, Any]] = []
    if i["needs_trend"] and cols["x_time"] and cols["y"]:
        charts.append({"type": "line", "x": cols["x_time"], "y": cols["y"], "title": f"{cols['y']} trend"})
    if i["needs_top"] and cols["x_cat"] and cols["y"]:
        charts.append({"type": "bar", "x": cols["x_cat"], "y": cols["y"], "title": f"Top {cols['x_cat']}"})
    if i["needs_distribution"] and cols["x_cat"] and cols["y"]:
        charts.append({"type": "pie", "x": cols["x_cat"], "y": cols["y"], "title": f"{cols['x_cat']} share"})
    if not charts and cols["x_cat"] and cols["y"]:
        charts = [{"type": "bar", "x": cols["x_cat"], "y": cols["y"], "title": f"{cols['y']} by {cols['x_cat']}"}]
    return {"charts": charts}


def create_plotly_charts(df: pd.DataFrame, config: Dict[str, Any]) -> Dict[str, Any]:
    out_charts = []
    insights = []
    for idx, c in enumerate(config.get("charts", []), start=1):
        ctype, x, y = c.get("type"), c.get("x"), c.get("y")
        if x not in df.columns or y not in df.columns:
            continue
        work = df[[x, y]].copy()
        work[y] = pd.to_numeric(work[y], errors="coerce")
        work = work.dropna(subset=[x, y])
        if len(work) == 0:
            continue

        if ctype == "line":
            g = work.groupby(x)[y].sum().reset_index().sort_values(x)
            fig = px.line(g, x=x, y=y, title=c.get("title"))
        elif ctype == "pie":
            g = work.groupby(x)[y].sum().reset_index().sort_values(y, ascending=False).head(8)
            fig = px.pie(g, names=x, values=y, title=c.get("title"))
        else:
            g = work.groupby(x)[y].sum().reset_index().sort_values(y, ascending=False).head(15)
            fig = px.bar(g, x=x, y=y, title=c.get("title"))

        out_charts.append(
            {
                "id": f"chart_{idx}",
                "type": ctype,
                "x": x,
                "y": y,
                "title": c.get("title"),
                "plotly_json": fig.to_json(),
            }
        )
        insights.append(f"{c.get('title')}: max {y} is {float(g[y].max()):.2f}.")

    return {"charts": out_charts, "layout": {"columns": 2}, "insights": insights}

