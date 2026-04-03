from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import pandas as pd
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool
from langchain.tools import tool

from app.services.profiler import profile_to_prompt_context
from app.services.rag import get_retriever
from app.core.config import settings


# Module-level stores (active dataframe + its profile).
_dataframes: Dict[str, pd.DataFrame] = {}
_profiles: Dict[str, Dict[str, Any]] = {}


def register_dataframe(name: str, df: pd.DataFrame, profile: Dict[str, Any]) -> None:
    _dataframes[name] = df
    _profiles[name] = profile


def _format_valid_columns(profile: Dict[str, Any]) -> str:
    numeric_cols = list((profile.get("numeric_columns") or {}).keys())
    categorical_cols = list((profile.get("categorical_columns") or {}).keys())
    date_cols = list((profile.get("date_columns") or {}).keys())
    return json.dumps({"numeric": numeric_cols, "categorical": categorical_cols, "date": date_cols}, ensure_ascii=False)


def build_agent(
    active_file: str,
    profile: Dict[str, Any],
    chat_model_override: str | None = None,
) -> AgentExecutor:
    if active_file not in _dataframes:
        raise ValueError(f"Active file not registered: {active_file}")

    chat_model = chat_model_override or settings.CHAT_MODEL
    # Ollama commonly registers `llama3.1` as `llama3.1:8b`.
    # Keep backward compatibility with the config value.
    # If a large model is configured, switch to a smaller one for stability/speed.
    if chat_model in {"llama3.1", "llama3.1:8b", "llama3.1:latest"}:
        chat_model = "qwen2.5:7b"

    llm = ChatOllama(
        model=chat_model,
        temperature=0.1,
        base_url=settings.OLLAMA_BASE_URL,
        # Keep KV cache small to fit RAM-limited systems.
        num_ctx=1024,
        num_predict=256,
    )

    df = _dataframes[active_file]
    retriever = get_retriever(active_file)

    @tool
    def retrieve_data_context(query: str) -> str:
        """Retrieve relevant context snippets from the embedded dataset."""
        docs = retriever.get_relevant_documents(query)
        return "\n\n".join([d.page_content for d in docs]) if docs else "No relevant context found."

    @tool
    def compute_aggregation(column: str, operation: str) -> str:
        """Compute a numeric aggregation over one column."""
        if column not in df.columns:
            return json.dumps({"error": f"Unknown column: {column}"})
        numeric = pd.to_numeric(df[column], errors="coerce")
        op = (operation or "").lower()

        if op == "sum":
            return str(float(numeric.dropna().sum())) if numeric.notna().any() else "0"
        if op == "mean":
            return str(float(numeric.dropna().mean())) if numeric.notna().any() else "0"
        if op == "min":
            return str(float(numeric.dropna().min())) if numeric.notna().any() else "0"
        if op == "max":
            return str(float(numeric.dropna().max())) if numeric.notna().any() else "0"
        if op == "count":
            return str(int(numeric.notna().sum()))

        return json.dumps({"error": f"Unsupported operation: {operation}"})

    @tool
    def get_top_n(column: str, value_col: str, n: int) -> str:
        """Group by `column` and return top-n groups by SUM(`value_col`)."""
        if column not in df.columns or value_col not in df.columns:
            return json.dumps({"error": "Unknown column(s)"})
        numeric = pd.to_numeric(df[value_col], errors="coerce")
        work = df[[column]].copy()
        work[value_col] = numeric
        grouped = (
            work.dropna(subset=[value_col])
            .groupby(column, dropna=True)[value_col]
            .sum()
            .sort_values(ascending=False)
            .head(int(n))
        )
        out = [{"key": str(k), "value": float(v)} for k, v in grouped.items()]
        return json.dumps(out, ensure_ascii=False)

    tools = [retrieve_data_context, compute_aggregation, get_top_n]

    valid_cols_json = _format_valid_columns(profile)
    profile_context = profile_to_prompt_context(profile)

    system_prompt = f"""
You are a CSV data analyst.

DATA PROFILE CONTEXT:
{profile_context}

VALID COLUMN NAMES (use ONLY these exact strings):
{valid_cols_json}

RULES:
- Never mention quarter labels unless those exact quarter strings exist as actual data values.
- Use ONLY exact column names from the provided profile. Never invent columns.
- For chart requests, respond with a single fenced code block exactly like:
  ```chart
  {{...JSON...}}
  ```
- For table requests, respond with a single fenced code block exactly like:
  ```table
  {{...JSON...}}
  ```
- When writing insights that include Indian currency amounts:
  - always prefix with `₹`
  - format large numbers using Indian units (Cr/Lakh) where appropriate.
- If the user request is ambiguous, make the minimal computation needed using available columns.
"""
    # `ChatPromptTemplate` uses Python-style `.format()` under the hood.
    # Escape any literal `{...}` fragments inside the system prompt so they aren't
    # misinterpreted as template variables.
    system_prompt = system_prompt.replace("{", "{{").replace("}", "}}")

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )

    agent = create_tool_calling_agent(llm, tools, prompt)
    executor = AgentExecutor(
        agent=agent,
        tools=tools,
        max_iterations=5,
        handle_parsing_errors=True,
        verbose=False,
    )
    return executor


def parse_agent_response(raw: str) -> Dict[str, Any]:
    """
    Extract chart/table JSON from ```chart ...``` / ```table ...``` code blocks.
    """
    raw = raw or ""

    chart_config = None
    table_payload = None

    chart_match = re.search(r"```chart\s*([\s\S]*?)```", raw, flags=re.IGNORECASE)
    if chart_match:
        payload = chart_match.group(1).strip()
        try:
            chart_config = json.loads(payload)
        except Exception:
            chart_config = {"raw": payload}

    table_match = re.search(r"```table\s*([\s\S]*?)```", raw, flags=re.IGNORECASE)
    if table_match:
        payload = table_match.group(1).strip()
        try:
            table_payload = json.loads(payload)
        except Exception:
            table_payload = {"raw": payload}

    # Strip code blocks to get a human-readable answer.
    answer = re.sub(r"```(?:chart|table)[\s\S]*?```", "", raw, flags=re.IGNORECASE).strip()

    intent = "CHAT"
    table_data: List[Dict[str, Any]] = []
    table_columns: List[str] = []

    if chart_config is not None:
        intent = "CHART"
    elif table_payload is not None:
        intent = "TABLE"

    if table_payload and isinstance(table_payload, dict):
        # Expected: { "columns": [...], "rows": [...] }
        cols = table_payload.get("columns") or table_payload.get("table_columns") or []
        rows = table_payload.get("rows") or table_payload.get("table_data") or []
        table_columns = list(cols)
        table_data = list(rows) if isinstance(rows, list) else []

    return {
        "answer": answer,
        "chart_config": chart_config,
        "table_data": table_data,
        "table_columns": table_columns,
        "intent": intent,
    }


def _convert_conversation_history(conversation_history: List[Dict[str, Any]], limit: int = 10) -> List[Any]:
    """
    Convert [{role, content}, ...] into LangChain message objects.
    """
    history = conversation_history[-limit:] if conversation_history else []
    out: List[Any] = []
    for item in history:
        role = (item.get("role") or "").lower()
        content = item.get("content") or ""
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
    return out


__all__ = [
    "register_dataframe",
    "build_agent",
    "parse_agent_response",
]

