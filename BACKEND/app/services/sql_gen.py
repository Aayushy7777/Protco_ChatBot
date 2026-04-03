from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

import pandas as pd

from app.services.llm_router import get_sql_llm


def _sql_identifier(name: str) -> str:
    # Basic safe quoting for SQL identifiers
    if re.match(r"^[A-Za-z_][A-Za-z0-9_]*$", name):
        return name
    return '"' + name.replace('"', '""') + '"'


def generate_sql_for_dataframe(
    question: str,
    df: pd.DataFrame,
    table_name: str = "data",
    dialect: str = "postgres",
) -> Dict[str, Any]:
    """
    Generate a SQL query for the loaded dataframe schema (conceptual table).
    Output is *only* SQL text plus a short rationale.
    """
    cols: List[str] = [str(c) for c in df.columns]
    col_list = "\n".join([f"- {c}" for c in cols])
    t = _sql_identifier(table_name)

    llm = get_sql_llm()
    prompt = f"""
You are a senior analytics engineer. Generate a single SQL query for {dialect}.

Constraints:
- Use ONLY these columns (exactly as written):\n{col_list}
- The table name is: {t}
- Return JSON only: {{"sql": "...", "rationale": "..."}}.
- Keep SQL simple and correct (use GROUP BY, ORDER BY, LIMIT when needed).

User request:
{question}
""".strip()

    res = llm.invoke(prompt)
    content = res.content if hasattr(res, "content") else str(res)

    # Try to parse JSON response; if not, extract SQL heuristically.
    try:
        data = json.loads(content)
        sql = (data.get("sql") or "").strip()
        rationale = (data.get("rationale") or "").strip()
        if sql:
            return {"sql": sql, "rationale": rationale, "dialect": dialect}
    except Exception:
        pass

    # Fallback: extract first SELECT ...; block
    m = re.search(r"(select[\s\S]+?;)", content, flags=re.IGNORECASE)
    sql = m.group(1).strip() if m else content.strip()
    return {"sql": sql, "rationale": "", "dialect": dialect}

