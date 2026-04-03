from __future__ import annotations

import re
from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd
from pandas.api.types import is_datetime64_any_dtype, is_numeric_dtype


def _safe_json_value(v: Any) -> Any:
    """Convert numpy/pandas scalars into JSON-safe primitives."""
    if isinstance(v, (np.floating, np.float32, np.float64)):
        if np.isnan(v):
            return None
        return float(v)
    if isinstance(v, (np.integer, np.int32, np.int64)):
        return int(v)
    if isinstance(v, (pd.Timestamp,)):
        # Keep it stable and LLM-friendly
        return v.isoformat()
    if isinstance(v, (np.bool_, bool)):
        return bool(v)
    if v is None:
        return None
    # Pandas often uses NaN
    if isinstance(v, float) and np.isnan(v):
        return None
    return v


def _detect_domain(columns: List[str]) -> str:
    cols = [c.lower() for c in columns]
    rules = [
        (["invoice", "bill"], "invoice"),
        (["sales", "order", "revenue"], "sales"),
        (["employee", "salary"], "hr"),
        (["product", "sku", "inventory"], "inventory"),
    ]
    for keywords, domain in rules:
        if any(any(k in c for k in keywords) for c in cols):
            return domain
    return "general"


def _find_first_matching_column(columns: List[str], tokens: List[str]) -> str | None:
    for c in columns:
        cl = c.lower()
        if any(t in cl for t in tokens):
            return c
    return None


def _detect_time_granularity(date_ranges_days: List[Tuple[str, float]]) -> Dict[str, Any]:
    """
    date_ranges_days: list of (column, range_days)
    Picks the column with the largest range to decide granularity.
    """
    if not date_ranges_days:
        return {"time_granularity": None, "time_period": None}

    date_ranges_days = sorted(date_ranges_days, key=lambda x: x[1], reverse=True)
    best_col, best_days = date_ranges_days[0]
    if best_days <= 31:
        gran = "daily"
    elif best_days <= 93:
        gran = "weekly"
    elif best_days <= 366:
        gran = "monthly"
    else:
        gran = "quarterly"
    return {"time_granularity": gran, "time_period": best_col}


def profile_dataframe(df: pd.DataFrame, filename: str) -> Dict[str, Any]:
    """
    Profile a DataFrame and auto-detect:
    - column types (numeric/categorical/date)
    - domain, revenue column, client column
    - date range-derived granularity
    """
    shape = {"rows": int(df.shape[0]), "columns": int(df.shape[1])}
    columns = list(df.columns)

    domain = _detect_domain(columns)
    revenue_col = _find_first_matching_column(
        columns, ["amount", "revenue", "total", "value", "price", "sales"]
    )
    client_col = _find_first_matching_column(
        columns, ["client", "customer", "company", "party", "name", "vendor"]
    )

    numeric_columns: Dict[str, Any] = {}
    categorical_columns: Dict[str, Any] = {}
    date_columns: Dict[str, Any] = {}

    # Detect dates first (so we can exclude them from other types).
    # IMPORTANT: Do not attempt to parse numeric columns as dates, because
    # `pd.to_datetime(123)` becomes a 1970 timestamp and causes misclassification.
    date_candidates: List[Tuple[str, pd.Series, pd.Series]] = []
    for col in columns:
        s = df[col]
        # Only consider date parsing for non-numeric columns (strings/objects) or actual datetime dtypes.
        if is_numeric_dtype(s):
            continue
        if is_datetime64_any_dtype(s):
            parsed = pd.to_datetime(s, errors="coerce")
        else:
            parsed = pd.to_datetime(s.astype(str), errors="coerce", infer_datetime_format=True)
        non_null = int(s.notna().sum())
        parsed_non_null = int(parsed.notna().sum())
        if non_null == 0:
            continue
        # Treat as date if most values parse and we have at least a few.
        if parsed_non_null >= max(3, int(0.5 * non_null)) and parsed_non_null / non_null >= 0.8:
            date_candidates.append((col, s, parsed))

    # If we have multiple date columns, profile them all; granularity is based on longest range.
    date_ranges_days: List[Tuple[str, float]] = []
    for col, _, parsed in date_candidates:
        valid = parsed.dropna()
        if valid.empty:
            continue
        min_dt = valid.min()
        max_dt = valid.max()
        range_days = float((max_dt - min_dt).days)
        date_ranges_days.append((col, range_days))
        date_columns[col] = {
            "min": _safe_json_value(min_dt),
            "max": _safe_json_value(max_dt),
            "range_days": range_days,
            "null_pct": float(100.0 * (1.0 - (len(valid) / max(1, len(parsed))))),
        }

    gran = _detect_time_granularity(date_ranges_days)
    # Provide time_period as a friendly date span (not just the chosen date column name).
    chosen_date_col = None
    if date_ranges_days:
        chosen_date_col = sorted(date_ranges_days, key=lambda x: x[1], reverse=True)[0][0]
    time_period = None
    if chosen_date_col and chosen_date_col in date_columns:
        min_v = date_columns[chosen_date_col]["min"]
        max_v = date_columns[chosen_date_col]["max"]
        # If min/max are isoformat strings, keep them.
        time_period = {"min": min_v, "max": max_v}

    # Detect numeric columns among non-date candidates.
    date_col_names = set(date_columns.keys())
    for col in columns:
        if col in date_col_names:
            continue

        s = df[col]
        numeric = pd.to_numeric(s, errors="coerce")
        non_null = int(s.notna().sum())
        numeric_non_null = int(numeric.notna().sum())
        if non_null == 0:
            continue

        # If most values coerce to numbers, call it numeric.
        if numeric_non_null >= max(3, int(0.5 * non_null)) and numeric_non_null / non_null >= 0.8:
            valid = numeric.dropna()
            if valid.empty:
                continue
            numeric_columns[col] = {
                "min": _safe_json_value(valid.min()),
                "max": _safe_json_value(valid.max()),
                "mean": _safe_json_value(valid.mean()),
                "std": _safe_json_value(valid.std(ddof=1)),
                "sum": _safe_json_value(valid.sum()),
                "median": _safe_json_value(valid.median()),
                "null_pct": float(100.0 * (1.0 - (len(valid) / max(1, len(numeric))))),
            }
        else:
            # Everything else goes to categorical.
            vc = s.astype(str).where(s.notna(), other=np.nan)
            non_null_vc = vc.dropna()
            top = (
                non_null_vc.value_counts(dropna=True).head(10).to_dict()
                if len(non_null_vc) > 0
                else {}
            )
            categorical_columns[col] = {
                "unique_count": int(s.nunique(dropna=True)),
                "top_10_values": {k: _safe_json_value(v) for k, v in top.items()},
                "null_pct": float(100.0 * (1.0 - (int(s.notna().sum()) / max(1, len(s))))),
            }

    # Sample rows
    sample_rows = df.head(5).to_dict(orient="records")
    sample_rows = [
        {k: _safe_json_value(v) for k, v in row.items()}  # make JSON-safe
        for row in sample_rows
    ]

    # Auto-detected KPIs (best-effort).
    total_revenue = None
    if revenue_col and revenue_col in df.columns:
        rev_num = pd.to_numeric(df[revenue_col], errors="coerce")
        if rev_num.notna().any():
            total_revenue = _safe_json_value(rev_num.dropna().sum())

    total_clients = None
    if client_col and client_col in df.columns:
        total_clients = int(df[client_col].nunique(dropna=True))

    auto_detected = {
        "domain": domain,
        "revenue_column": revenue_col,
        "client_column": client_col,
        "time_granularity": gran.get("time_granularity"),
        "time_period": time_period,
        "total_revenue": total_revenue,
        "total_clients": total_clients,
    }

    return {
        "source_file": filename,
        "shape": shape,
        "numeric_columns": numeric_columns,
        "categorical_columns": categorical_columns,
        "date_columns": date_columns,
        "sample_rows": sample_rows,
        "auto_detected": auto_detected,
    }


def profile_to_prompt_context(profile: Dict[str, Any]) -> str:
    """
    Convert profile dict into clean text context for injection into the LLM system prompt.
    This must not mention quarter label tokens anywhere.
    """
    shape = profile.get("shape", {})
    auto = profile.get("auto_detected", {}) or {}

    lines: List[str] = []
    lines.append(f"Source file: {profile.get('source_file')}")
    lines.append(f"Shape: {shape.get('rows')} rows x {shape.get('columns')} columns")
    lines.append(
        "Auto-detected:"
    )
    lines.append(f"- domain: {auto.get('domain')}")
    lines.append(f"- revenue_column: {auto.get('revenue_column')}")
    lines.append(f"- client_column: {auto.get('client_column')}")
    if auto.get("time_granularity"):
        lines.append(f"- time_granularity: {auto.get('time_granularity')}")
    if auto.get("time_period"):
        lines.append(f"- time_period: {auto.get('time_period')}")
    if auto.get("total_revenue") is not None:
        lines.append(f"- total_revenue: {auto.get('total_revenue')}")
    if auto.get("total_clients") is not None:
        lines.append(f"- total_clients: {auto.get('total_clients')}")

    numeric = profile.get("numeric_columns", {}) or {}
    categorical = profile.get("categorical_columns", {}) or {}
    dates = profile.get("date_columns", {}) or {}

    lines.append("")
    lines.append("Numeric columns (use these for sums/averages):")
    if numeric:
        for col, stats in numeric.items():
            lines.append(
                f"- {col}: min={stats.get('min')}, max={stats.get('max')}, mean={stats.get('mean')}, "
                f"std={stats.get('std')}, sum={stats.get('sum')}, median={stats.get('median')}, "
                f"null_pct={stats.get('null_pct')}"
            )
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("Categorical columns (grouping dimensions like customer, category, status):")
    if categorical:
        for col, stats in categorical.items():
            top_vals = stats.get("top_10_values", {}) or {}
            # Keep prompt small: only show keys, not values for too many columns.
            top_items = list(top_vals.items())[:10]
            lines.append(
                f"- {col}: unique_count={stats.get('unique_count')}, null_pct={stats.get('null_pct')}, "
                f"top_10_values={top_items}"
            )
    else:
        lines.append("- (none)")

    lines.append("")
    lines.append("Date columns:")
    if dates:
        for col, stats in dates.items():
            lines.append(
                f"- {col}: min={stats.get('min')}, max={stats.get('max')}, range_days={stats.get('range_days')}, "
                f"null_pct={stats.get('null_pct')}"
            )
    else:
        lines.append("- (none)")

    lines.append("")
    # Provide only a compact sample of rows.
    sample = profile.get("sample_rows", []) or []
    lines.append("Sample rows (first few):")
    for row in sample[:3]:
        # Show up to 8 fields per row for prompt compactness
        keys = list(row.keys())[:8]
        compact = {k: row[k] for k in keys}
        lines.append(f"- {compact}")

    return "\n".join(lines)

