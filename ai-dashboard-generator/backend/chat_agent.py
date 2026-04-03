from __future__ import annotations

import re
import sys
from pathlib import Path
from typing import Any, Dict, Optional

import pandas as pd
from langchain_core.messages import AIMessage, HumanMessage

from file_processor import format_value
from ollama_client import chat as ollama_chat

# Optional integration with previous backend agent stack.
_LEGACY_AGENT_AVAILABLE = False
try:
    here = Path(__file__).resolve()
    project_root = here.parent.parent.parent  # .../CSV CHAT AGENT
    legacy_backend = project_root / "BACKEND"
    if legacy_backend.exists() and str(legacy_backend) not in sys.path:
        sys.path.insert(0, str(legacy_backend))
    from app.services.agent import build_agent as legacy_build_agent  # type: ignore
    from app.services.agent import parse_agent_response as legacy_parse_response  # type: ignore
    from app.services.agent import register_dataframe as legacy_register_dataframe  # type: ignore

    _LEGACY_AGENT_AVAILABLE = True
except Exception:
    _LEGACY_AGENT_AVAILABLE = False


def _as_legacy_profile(profile: Dict[str, Any], df: pd.DataFrame) -> Dict[str, Any]:
    """
    Map new dashboard profile schema -> old BACKEND agent schema.
    """
    auto = profile.get("auto") or {}
    amount_col = auto.get("amount_col")
    name_col = auto.get("name_col")

    return {
        "source_file": profile.get("filename", "uploaded_file.csv"),
        "shape": [int(len(df)), int(len(df.columns))],
        "numeric_columns": profile.get("numeric") or {},
        "categorical_columns": profile.get("categorical") or {},
        "date_columns": profile.get("dates") or {},
        "sample_rows": profile.get("sample") or [],
        "auto_detected": {
            "revenue_column": amount_col,
            "client_column": name_col,
        },
    }


def _history_for_legacy(history: list[Dict[str, str]], limit: int = 10) -> list[Any]:
    out: list[Any] = []
    for item in (history or [])[-limit:]:
        role = str(item.get("role") or "").lower()
        content = str(item.get("content") or "")
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
    return out


def _table_to_markdown(columns: list[Any], rows: list[Any], max_rows: int = 20) -> str:
    cols = [str(c) for c in (columns or [])]
    if not cols or not isinstance(rows, list) or not rows:
        return ""
    header = "| " + " | ".join(cols) + " |"
    sep = "| " + " | ".join(["---"] * len(cols)) + " |"
    lines = [header, sep]
    for row in rows[:max_rows]:
        if isinstance(row, dict):
            lines.append("| " + " | ".join([str(row.get(c, "")) for c in cols]) + " |")
    return "\n".join(lines)


def _pick_name_col(profile: Dict[str, Any], df: pd.DataFrame) -> Optional[str]:
    auto = profile.get("auto") or {}
    name_col = auto.get("name_col")
    if name_col in df.columns:
        return name_col

    # fallback to most diverse categorical column
    cat = profile.get("categorical") or {}
    if not cat:
        return None
    best = max(cat.keys(), key=lambda c: int((cat.get(c) or {}).get("unique") or 0))
    return best if best in df.columns else None


def _pick_amount_col(profile: Dict[str, Any], df: pd.DataFrame) -> Optional[str]:
    auto = profile.get("auto") or {}
    amount_col = auto.get("amount_col")
    if amount_col in df.columns:
        return amount_col
    nums = list((profile.get("numeric") or {}).keys())
    return nums[0] if nums and nums[0] in df.columns else None


def _reply_customer_counts(df: pd.DataFrame, profile: Dict[str, Any]) -> Optional[str]:
    name_col = _pick_name_col(profile, df)
    if not name_col:
        return None
    counts = df[name_col].dropna().astype(str).str.strip()
    counts = counts[counts != ""].value_counts().head(50)
    if len(counts) == 0:
        return "I could not find valid customer names in the dataset."

    lines = [f"Customer-wise record counts from `{name_col}`:"]
    for customer, cnt in counts.items():
        lines.append(f"- {customer}: {int(cnt)}")
    lines.append(f"\nTotal unique customers: {int(df[name_col].dropna().astype(str).nunique())}")
    return "\n".join(lines)


def _customer_counts_table(df: pd.DataFrame, profile: Dict[str, Any], limit: int = 50) -> tuple[list[str], list[dict[str, Any]]]:
    name_col = _pick_name_col(profile, df)
    if not name_col:
        return [], []
    counts = df[name_col].dropna().astype(str).str.strip()
    counts = counts[counts != ""].value_counts().head(limit)
    rows = [{"Customer": str(k), "Count": int(v)} for k, v in counts.items()]
    return ["Customer", "Count"], rows


def _reply_top_customers(df: pd.DataFrame, profile: Dict[str, Any], n: int) -> Optional[str]:
    name_col = _pick_name_col(profile, df)
    amount_col = _pick_amount_col(profile, df)
    if not name_col or not amount_col:
        return None

    work = df[[name_col, amount_col]].copy()
    work[amount_col] = pd.to_numeric(work[amount_col], errors="coerce")
    work = work.dropna(subset=[name_col, amount_col])
    if len(work) == 0:
        return None

    top = work.groupby(name_col)[amount_col].sum().sort_values(ascending=False).head(max(1, n))
    lines = [f"Top {max(1, n)} customers by `{amount_col}`:"]
    for idx, (customer, value) in enumerate(top.items(), start=1):
        lines.append(f"{idx}. {customer} — {format_value(float(value))}")
    return "\n".join(lines)


def _top_customers_table(df: pd.DataFrame, profile: Dict[str, Any], n: int) -> tuple[list[str], list[dict[str, Any]], Optional[Dict[str, Any]]]:
    name_col = _pick_name_col(profile, df)
    amount_col = _pick_amount_col(profile, df)
    if not name_col or not amount_col:
        return [], [], None
    work = df[[name_col, amount_col]].copy()
    work[amount_col] = pd.to_numeric(work[amount_col], errors="coerce")
    work = work.dropna(subset=[name_col, amount_col])
    if len(work) == 0:
        return [], [], None
    top = work.groupby(name_col)[amount_col].sum().sort_values(ascending=False).head(max(1, n))
    rows = [{"Customer": str(k), "Value": round(float(v), 2)} for k, v in top.items()]
    chart = {
        "type": "horizontalBar",
        "title": f"Top {max(1, n)} customers by {amount_col}",
        "insight": f"{rows[0]['Customer']} leads with {format_value(float(rows[0]['Value']))}.",
        "data": {"labels": [r["Customer"] for r in rows], "values": [r["Value"] for r in rows]},
        "chartStyle": "horizontal",
    }
    return ["Customer", "Value"], rows, chart


def _aggregate_numeric(df: pd.DataFrame, profile: Dict[str, Any], op: str) -> Optional[str]:
    amount_col = _pick_amount_col(profile, df)
    if not amount_col:
        return None
    series = pd.to_numeric(df[amount_col], errors="coerce").dropna()
    if len(series) == 0:
        return None
    op_l = op.lower()
    if op_l == "sum":
        value = float(series.sum())
        return f"Total `{amount_col}` is {format_value(value)}."
    if op_l in {"avg", "mean", "average"}:
        value = float(series.mean())
        return f"Average `{amount_col}` is {format_value(value)}."
    if op_l == "max":
        value = float(series.max())
        return f"Maximum `{amount_col}` is {format_value(value)}."
    if op_l == "min":
        value = float(series.min())
        return f"Minimum `{amount_col}` is {format_value(value)}."
    return None


def _as_payload(
    reply: str,
    intent: str = "CHAT",
    chart_config: Optional[Dict[str, Any]] = None,
    table_columns: Optional[list[Any]] = None,
    table_data: Optional[list[Any]] = None,
) -> Dict[str, Any]:
    return {
        "reply": reply,
        "intent": intent,
        "chart_config": chart_config,
        "table_columns": table_columns or [],
        "table_data": table_data or [],
    }


async def smart_chat_payload(
    message: str, profile: Dict[str, Any], df: pd.DataFrame, history: list[Dict[str, str]]
) -> Dict[str, Any]:
    msg = (message or "").strip()
    msg_l = msg.lower()

    # Deterministic paths first (fast + reliable)
    if ("customer" in msg_l or "client" in msg_l) and any(k in msg_l for k in ["individually", "each", "wise", "count", "number"]):
        out = _reply_customer_counts(df, profile)
        if out:
            cols, rows = _customer_counts_table(df, profile)
            return _as_payload(out, intent="TABLE", table_columns=cols, table_data=rows)

    m = re.search(r"\btop\s+(\d+)\b", msg_l)
    if m and any(k in msg_l for k in ["customer", "client", "vendor", "party"]):
        out = _reply_top_customers(df, profile, int(m.group(1)))
        if out:
            cols, rows, chart = _top_customers_table(df, profile, int(m.group(1)))
            return _as_payload(out, intent="TABLE", table_columns=cols, table_data=rows, chart_config=chart)

    # quick aggregate intents for crisp answers
    if any(k in msg_l for k in ["total", "sum"]):
        agg = _aggregate_numeric(df, profile, "sum")
        if agg:
            return _as_payload(agg)
    if any(k in msg_l for k in ["average", "avg", "mean"]):
        agg = _aggregate_numeric(df, profile, "avg")
        if agg:
            return _as_payload(agg)
    if any(k in msg_l for k in ["maximum", "highest", "max"]):
        agg = _aggregate_numeric(df, profile, "max")
        if agg:
            return _as_payload(agg)
    if any(k in msg_l for k in ["minimum", "lowest", "min"]):
        agg = _aggregate_numeric(df, profile, "min")
        if agg:
            return _as_payload(agg)

    # Optional bridge to previous backend LangChain agent.
    if _LEGACY_AGENT_AVAILABLE:
        try:
            active_file = str(profile.get("filename") or "uploaded_file.csv")
            legacy_profile = _as_legacy_profile(profile, df)
            legacy_register_dataframe(active_file, df, legacy_profile)
            ex = legacy_build_agent(active_file=active_file, profile=legacy_profile)
            result = ex.invoke({"input": msg, "chat_history": _history_for_legacy(history)})
            raw = str(result.get("output") or "").strip()
            parsed = legacy_parse_response(raw)
            ans = str(parsed.get("answer") or "").strip()
            if ans or parsed.get("intent") in {"TABLE", "CHART"}:
                return _as_payload(
                    ans or "Generated result for your request.",
                    intent=str(parsed.get("intent") or "CHAT"),
                    chart_config=parsed.get("chart_config"),
                    table_columns=parsed.get("table_columns") or [],
                    table_data=parsed.get("table_data") or [],
                )
            # If agent returned structured output but empty answer, render readable fallback.
            if parsed.get("intent") == "TABLE":
                md = _table_to_markdown(parsed.get("table_columns") or [], parsed.get("table_data") or [])
                if md:
                    return _as_payload(
                        "Here is the table from your request:\n\n" + md,
                        intent="TABLE",
                        table_columns=parsed.get("table_columns") or [],
                        table_data=parsed.get("table_data") or [],
                    )
                return _as_payload("Table generated for your request.", intent="TABLE")
            if parsed.get("intent") == "CHART":
                cfg = parsed.get("chart_config") or {}
                title = str((cfg or {}).get("title") or "your chart")
                return _as_payload(f"Chart generated: {title}.", intent="CHART", chart_config=cfg)
        except Exception:
            pass

    # Fallback to Ollama contextual chat
    reply = await ollama_chat(msg, profile.get("context_text", ""), history)
    if reply.strip().lower() in {"", "no response.", "no response"}:
        # Safety fallback so users never get empty chat
        return _as_payload(
            "I could not generate a full answer from the model. "
            "Try asking with explicit columns (for example: "
            f"'top 5 by {_pick_amount_col(profile, df) or 'amount'} grouped by {_pick_name_col(profile, df) or 'name'}')."
        )
    return _as_payload(reply)


async def smart_chat(message: str, profile: Dict[str, Any], df: pd.DataFrame, history: list[Dict[str, str]]) -> str:
    return str((await smart_chat_payload(message, profile, df, history)).get("reply") or "")
