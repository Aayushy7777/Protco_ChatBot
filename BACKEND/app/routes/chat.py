from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from langchain_core.messages import AIMessage, HumanMessage

import pandas as pd

from app.services.agent import build_agent, parse_agent_response, _profiles, _dataframes
from app.services.intent import classify_intent
from app.services.sql_gen import generate_sql_for_dataframe


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    active_file: str = ""
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    all_files: List[str] = Field(default_factory=list)


def _convert_history(history: List[Dict[str, Any]], limit: int = 10) -> List[Any]:
    out: List[Any] = []
    tail = history[-limit:] if history else []
    for item in tail:
        role = (item.get("role") or "").lower()
        content = item.get("content") or ""
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
    return out


def _best_guess_client_and_value_cols(profile: Dict[str, Any], df: pd.DataFrame) -> Tuple[Optional[str], Optional[str]]:
    auto = profile.get("auto_detected") or {}
    client_col = auto.get("client_column")
    value_col = auto.get("revenue_column")

    if client_col not in df.columns:
        # fallback: most unique categorical column
        cat = profile.get("categorical_columns") or {}
        if cat:
            client_col = max(cat.keys(), key=lambda c: int(cat[c].get("unique_count") or 0))
        else:
            client_col = None

    if value_col not in df.columns:
        # fallback: numeric-like column with highest non-null ratio and sum
        best = None
        best_score = -1.0
        for c in df.columns:
            num = pd.to_numeric(df[c], errors="coerce")
            if num.notna().sum() < max(5, int(0.3 * len(df))):
                continue
            score = float(num.dropna().abs().sum())
            if score > best_score:
                best_score = score
                best = c
        value_col = best

    return client_col, value_col


def _top_n_table_and_chart(df: pd.DataFrame, client_col: str, value_col: str, n: int) -> Dict[str, Any]:
    work = df[[client_col, value_col]].copy()
    work[value_col] = pd.to_numeric(work[value_col], errors="coerce")
    work = work.dropna(subset=[client_col, value_col])
    series = (
        work.groupby(client_col, dropna=True)[value_col]
        .sum()
        .sort_values(ascending=False)
        .head(int(n))
    )
    rows = [{"Customer": str(k), "Value": float(v)} for k, v in series.items()]
    chart = {
        "type": "bar",
        "title": f"Top {int(n)} Customers",
        "xKey": "Customer",
        "yKey": "Value",
        "chartStyle": "horizontal",
        "data": {"labels": [r["Customer"] for r in rows], "values": [r["Value"] for r in rows]},
    }
    return {
        "answer": f"Top {int(n)} customers by {value_col}.",
        "intent": "TABLE",
        "table_columns": ["Customer", "Value"],
        "table_data": rows,
        # Also include a chart for the dashboard pinning behavior.
        "chart_config": chart,
    }


def _customers_by_bank(df: pd.DataFrame, profile: Dict[str, Any], bank_name: str) -> Optional[Dict[str, Any]]:
    # Find a likely bank column.
    bank_col = None
    for c in df.columns:
        if "bank" in str(c).lower():
            bank_col = c
            break
    if not bank_col:
        return None

    client_col, _ = _best_guess_client_and_value_cols(profile, df)
    if not client_col:
        return None

    mask = df[bank_col].astype(str).str.contains(bank_name, case=False, na=False)
    customers = (
        df.loc[mask, client_col]
        .dropna()
        .astype(str)
        .drop_duplicates()
        .head(200)
        .tolist()
    )
    rows = [{"Customer": c} for c in customers]
    return {
        "answer": f"Customers with payments through {bank_name.upper()} (from `{bank_col}`).",
        "intent": "TABLE",
        "table_columns": ["Customer"],
        "table_data": rows,
        "chart_config": None,
    }


@router.post("/api/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    try:
        message = (req.message or "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        active_file = req.active_file or (req.all_files[0] if req.all_files else "")
        if not active_file:
            raise HTTPException(status_code=400, detail="No active_file selected.")

        if active_file not in _profiles:
            raise HTTPException(status_code=404, detail=f"File not found in memory: {active_file}")

        profile = _profiles[active_file]
        df = _dataframes.get(active_file)
        if df is None:
            raise HTTPException(status_code=404, detail=f"File not found in memory: {active_file}")

        # --- Deterministic fast paths for common simple questions ---
        msg_l = message.lower()
        intent = classify_intent(message)

        # "top 5 customers/clients/parties/vendors"
        m = re.search(r"\btop\s+(\d+)\b", msg_l)
        if intent == "TOP_N" and m and any(k in msg_l for k in ["customer", "client", "party", "vendor"]):
            n = int(m.group(1))
            client_col, value_col = _best_guess_client_and_value_cols(profile, df)
            if client_col and value_col:
                return _top_n_table_and_chart(df, client_col, value_col, n)

        # "customers who does payment through hdfc bank"
        m2 = re.search(r"\bthrough\s+([a-z0-9 &_-]+?)\s+bank\b", msg_l)
        if intent == "FILTER_BANK" and m2:
            bank = m2.group(1).strip()
            out = _customers_by_bank(df, profile, bank_name=bank)
            if out:
                return out

        # SQL generation path
        if intent == "SQL":
            table_name = re.sub(r"[^A-Za-z0-9_]+", "_", active_file.rsplit(".", 1)[0]).strip("_") or "data"
            sql_out = generate_sql_for_dataframe(message, df=df, table_name=table_name, dialect="postgres")
            sql = sql_out.get("sql") or ""
            rationale = sql_out.get("rationale") or ""
            answer = "Here is a SQL query for your request:\n\n```sql\n" + sql.strip() + "\n```"
            if rationale:
                answer += "\n\n" + rationale.strip()
            return {
                "answer": answer,
                "chart_config": None,
                "table_data": [],
                "table_columns": [],
                "intent": "CHAT",
            }

        history_messages = _convert_history(req.conversation_history, limit=10)
        agent_executor = build_agent(active_file=active_file, profile=profile)

        try:
            result = agent_executor.invoke({"input": message, "chat_history": history_messages})
        except Exception as e:
            # Ollama can reject large models when RAM is insufficient.
            # Retry with a smaller fallback model so the app still works.
            msg = str(e).lower()
            if "requires more system memory" in msg:
                agent_executor = build_agent(
                    active_file=active_file,
                    profile=profile,
                    chat_model_override="mistral:7b",
                )
                result = agent_executor.invoke(
                    {"input": message, "chat_history": history_messages}
                )
            else:
                raise

        raw = result.get("output") if isinstance(result, dict) else str(result)
        parsed = parse_agent_response(raw)
        return parsed
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

