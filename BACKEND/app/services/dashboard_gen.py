from __future__ import annotations

import os
import json
import re
from typing import Any, Dict, List

import pandas as pd
from langchain_ollama import ChatOllama

from app.core.config import settings
from app.services.profiler import profile_to_prompt_context


def _extract_first_json_array(text: str) -> List[Dict[str, Any]]:
    # Non-greedy match so we take the first JSON array.
    match = re.search(r"(\[[\s\S]*?\])", text)
    if not match:
        return []
    arr = json.loads(match.group(1))
    if isinstance(arr, list):
        return arr
    if isinstance(arr, dict):
        # Be tolerant if the model returns an object wrapping the list.
        for key in ("charts", "data", "configs"):
            if key in arr and isinstance(arr[key], list):
                return arr[key]
    return []


def _map_to_frontend_fields(cfg: Dict[str, Any]) -> Dict[str, Any]:
    """
    Map the abstract chart config into fields expected by the existing chart renderer.
    """
    chart_type = None
    chart_style = cfg.get("chartStyle")
    chart_style_str = ""
    try:
        chart_style_str = json.dumps(chart_style, ensure_ascii=False).lower()
    except Exception:
        chart_style_str = str(chart_style).lower()

    if cfg.get("type") == "bar" and "horizontal" in chart_style_str:
        chart_type = "BAR_HORIZONTAL"
    elif cfg.get("type") == "area":
        chart_type = "LINE_AREA"
    elif cfg.get("type") == "pie":
        chart_type = "PIE"
    elif cfg.get("type") == "scatter":
        chart_type = "SCATTER"
    else:
        # Fallback: keep it generic
        chart_type = "BAR_VERTICAL"

    cfg["chartType"] = chart_type
    if cfg.get("insight") and not cfg.get("business_insight"):
        cfg["business_insight"] = cfg["insight"]
    return cfg


def generate_dashboard(df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Generate 6 chart configs, then enrich each with actual data from df.
    """
    def _pick_numeric_columns(min_ratio: float = 0.6, max_cols: int = 3) -> List[str]:
        numeric_candidates: List[tuple[str, float]] = []
        for c in df.columns:
            coerced = pd.to_numeric(df[c], errors="coerce")
            non_null = coerced.notna().sum()
            if len(df) == 0:
                continue
            ratio = float(non_null) / float(len(df))
            if ratio >= min_ratio:
                numeric_candidates.append((c, ratio))
        numeric_candidates.sort(key=lambda x: x[1], reverse=True)
        return [c for c, _ in numeric_candidates[:max_cols]]

    def _fallback_configs() -> List[Dict[str, Any]]:
        auto = profile.get("auto_detected") or {}
        revenue_col = auto.get("revenue_column") or None
        client_col = auto.get("client_column") or None
        date_cols = list((profile.get("date_columns") or {}).keys())
        cat_cols = list((profile.get("categorical_columns") or {}).keys())

        revenue_col = revenue_col if revenue_col in df.columns else (date_cols[0] if date_cols else None)
        if not revenue_col:
            return []

        # Pick additional numeric columns from the dataframe (not only from the profile).
        numeric_cols = _pick_numeric_columns()
        if revenue_col not in numeric_cols:
            numeric_cols = [revenue_col] + numeric_cols

        pick_date = date_cols[0] if date_cols else None
        pick_cat = client_col if client_col in df.columns else (cat_cols[0] if cat_cols else None)
        other_numeric = next((c for c in numeric_cols if c != revenue_col), None)

        configs: List[Dict[str, Any]] = []
        # 1) Bar horizontal: category/client + revenue
        if pick_cat and revenue_col:
            configs.append({
                "type": "bar",
                "title": "Top Clients by Revenue",
                "xKey": pick_cat,
                "yKey": revenue_col,
                "chartStyle": "horizontal",
                "insight": "Identify the highest contributing clients.",
                "priority": 1,
            })
        # 2) Pie: category share
        if pick_cat and revenue_col:
            configs.append({
                "type": "pie",
                "title": "Revenue Share",
                "xKey": pick_cat,
                "yKey": revenue_col,
                "chartStyle": "pie",
                "insight": "See how revenue is distributed across top groups.",
                "priority": 2,
            })

        # Add simple alternates to reach 6.
        # Use other categorical columns for the bar/pie.
        for c in cat_cols:
            if len(configs) >= 6:
                break
            if c == pick_cat:
                continue
            configs.append({
                "type": "bar",
                "title": f"Top {c} by Revenue",
                "xKey": c,
                "yKey": revenue_col,
                "chartStyle": "horizontal",
                "insight": f"Rank {c} by their revenue contribution.",
                "priority": 5,
            })

        # Ensure exactly up to 6.
        return configs[:6]

    # Fast deterministic mode: avoids expensive LLM generation for chart configs.
    # You can turn LLM generation back on by setting USE_DASHBOARD_LLM=1 in the backend env.
    use_llm = os.getenv("USE_DASHBOARD_LLM", "0") == "1"

    # Prefer smaller models for speed/stability; fall back to the configured model.
    model_candidates = [
        "qwen2.5:7b",
        "mistral:7b",
        "deepseek-r1:8b",
        settings.CHAT_MODEL,
    ]

    last_llm_err: Exception | None = None
    llm = None
    for model in model_candidates:
        try:
            llm = ChatOllama(
                model=model,
                temperature=0.1,
                base_url=settings.OLLAMA_BASE_URL,
                num_ctx=512,
                num_predict=128,
            )
            break
        except Exception as e:
            last_llm_err = e
            continue

    if llm is None:
        raise RuntimeError(f"Failed to initialize ChatOllama: {last_llm_err}")

    profile_context = profile_to_prompt_context(profile)
    numeric_cols = list((profile.get("numeric_columns") or {}).keys())
    categorical_cols = list((profile.get("categorical_columns") or {}).keys())
    date_cols = list((profile.get("date_columns") or {}).keys())

    prompt = f"""
You are generating chart configurations for a dashboard.

PROFILE:
{profile_context}

IMPORTANT:
- Use ONLY actual column names that appear in the profile above.
- Never use quarter labels unless those exact strings exist as actual data values.

Task:
Generate exactly 6 chart configs as a minified JSON array. Each config MUST include:
  type, title, xKey, yKey, chartStyle, insight, priority

Chart selection rules (choose best matches from the data shape):
- one category + one numeric → bar horizontal for rankings
- date + numeric → area chart for trends
- category share → pie (max 8 slices)
- two numerics → scatter

Priority:
- Use integers 1..6 (1 = highest).
- Ensure variety across the 6 charts.

Output constraints:
- Output JSON only (no markdown, no explanation).
"""

    if use_llm:
        response = llm.invoke(prompt)
        content = response.content if hasattr(response, "content") else str(response)
        configs = _extract_first_json_array(content)
        if not configs:
            configs = _fallback_configs()
    else:
        configs = _fallback_configs()

    enriched: List[Dict[str, Any]] = []
    for i, cfg in enumerate(configs):
        cfg = dict(cfg)
        xKey = cfg.get("xKey")
        yKey = cfg.get("yKey")
        chart_type = cfg.get("type")
        chartStyle = cfg.get("chartStyle")
        chart_style_str = ""
        try:
            chart_style_str = json.dumps(chartStyle, ensure_ascii=False).lower()
        except Exception:
            chart_style_str = str(chartStyle).lower()
        valid_keys = (
            bool(xKey)
            and bool(yKey)
            and xKey in df.columns
            and yKey in df.columns
        )

        # Enrich data per config type.
        if valid_keys and chart_type == "bar" and "horizontal" in chart_style_str:
            # bar horizontal (rankings)
            grouped = (
                df[[xKey, yKey]]
                .copy()
            )
            grouped[yKey] = pd.to_numeric(grouped[yKey], errors="coerce")
            grouped = grouped.dropna(subset=[yKey])
            series = (
                grouped.groupby(xKey)[yKey]
                .sum()
                .sort_values(ascending=False)
                .head(15)
            )
            data = {
                "labels": [str(k) for k in series.index.tolist()],
                "values": [float(v) for v in series.values.tolist()],
            }
            cfg["data"] = data

        elif valid_keys and chart_type == "area":
            # area/line trends (mean by xKey)
            work = df[[xKey, yKey]].copy()
            work[yKey] = pd.to_numeric(work[yKey], errors="coerce")
            work = work.dropna(subset=[xKey, yKey])
            # Sort by xKey when possible; if it's a datetime column it will sort.
            try:
                work = work.sort_values(by=xKey)
            except Exception:
                pass
            mean_series = work.groupby(xKey)[yKey].mean().sort_index()
            labels = [k.isoformat() if isinstance(k, (pd.Timestamp,)) else str(k) for k in mean_series.index.tolist()]
            cfg["data"] = {"labels": labels, "values": [float(v) for v in mean_series.values.tolist()]}

        elif valid_keys and chart_type == "pie":
            work = df[[xKey, yKey]].copy()
            work[yKey] = pd.to_numeric(work[yKey], errors="coerce")
            work = work.dropna(subset=[yKey])
            series = (
                work.groupby(xKey)[yKey]
                .sum()
                .sort_values(ascending=False)
                .head(8)
            )
            cfg["data"] = {
                "labels": [str(k) for k in series.index.tolist()],
                "values": [float(v) for v in series.values.tolist()],
            }

        elif valid_keys and chart_type == "scatter":
            # Two numerics.
            work = df[[xKey, yKey]].copy()
            work[xKey] = pd.to_numeric(work[xKey], errors="coerce")
            work[yKey] = pd.to_numeric(work[yKey], errors="coerce")
            work = work.dropna(subset=[xKey, yKey])
            sample = work.sample(n=min(200, len(work)), random_state=42) if len(work) > 0 else work
            points = [[float(r[xKey]), float(r[yKey])] for _, r in sample.iterrows()]
            cfg["data"] = {"x_label": xKey, "y_label": yKey, "data": points}

        else:
            # Unknown type or invalid keys: keep the config, but return empty data
            # so the frontend can still render the card (and we don't end up with 0 charts).
            cfg["data"] = cfg.get("data") or {}

        cfg["id"] = cfg.get("id") or f"chart_{i}_{xKey}_{yKey}"
        cfg["priority"] = int(cfg.get("priority") or 6)
        cfg = _map_to_frontend_fields(cfg)
        enriched.append(cfg)

    enriched.sort(key=lambda c: int(c.get("priority", 999)))
    # If the model returned fewer than 6, fill with deterministic fallbacks.
    if len(enriched) < 6:
        existing_ids = {c.get("id") for c in enriched}
        for fb_i, fb in enumerate(_fallback_configs()):
            fb = dict(fb)
            fb["id"] = fb.get("id") or f"fallback_{fb_i}"
            if fb.get("id") in existing_ids:
                continue
            fb = _map_to_frontend_fields(fb)
            enriched.append(fb)

    return enriched[:6]

