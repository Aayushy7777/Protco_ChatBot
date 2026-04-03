"""
profiler.py
-----------
Auto-detects everything from a DataFrame: data types, time periods,
domains, revenue/client columns, and generates dynamic prompt context.
"""

import pandas as pd


def profile_dataframe(df: pd.DataFrame, filename: str = "") -> dict:
    """
    Profile a DataFrame and auto-detect patterns, domains, time periods, etc.
    Returns dict with schema, sample rows, and auto_detected insights.
    """
    profile = {
        "source_file": filename,
        "shape": {"rows": len(df), "columns": len(df.columns)},
        "columns": {},
        "sample_rows": df.head(5).fillna("").to_dict(orient="records"),
        "date_columns": {},
        "categorical_columns": {},
        "numeric_columns": {},
        "auto_detected": {},  # <-- everything discovered automatically
    }

    for col in df.columns:
        series = df[col]
        null_pct = round(series.isnull().mean() * 100, 2)

        # Auto-detect dates
        if series.dtype == object:
            try:
                parsed = pd.to_datetime(series, infer_datetime_format=True, errors="coerce")
                if parsed.notna().mean() > 0.6:
                    profile["date_columns"][col] = {
                        "min": str(parsed.min()),
                        "max": str(parsed.max()),
                        "range_days": (parsed.max() - parsed.min()).days,
                        "null_pct": null_pct,
                    }
                    # Auto-detect period from date range
                    days = (parsed.max() - parsed.min()).days
                    if days <= 31:
                        period = "single month"
                    elif days <= 93:
                        period = "single quarter"
                    elif days <= 186:
                        period = "half year"
                    elif days <= 366:
                        period = "full year"
                    else:
                        period = f"{round(days/365, 1)} years"
                    profile["auto_detected"]["time_period"] = period
                    profile["auto_detected"]["date_column"] = col
                    continue
            except Exception:
                pass

        if pd.api.types.is_numeric_dtype(series):
            profile["numeric_columns"][col] = {
                "dtype": str(series.dtype),
                "null_pct": null_pct,
                "min": round(float(series.min()), 4),
                "max": round(float(series.max()), 4),
                "mean": round(float(series.mean()), 4),
                "std": round(float(series.std()), 4),
                "median": round(float(series.median()), 4),
                "sum": round(float(series.sum()), 4),
            }
        else:
            top = series.value_counts().head(10).to_dict()
            profile["categorical_columns"][col] = {
                "null_pct": null_pct,
                "unique_count": int(series.nunique()),
                "top_values": {str(k): int(v) for k, v in top.items()},
            }

    # Auto-detect what kind of data this is
    col_names_lower = [c.lower() for c in df.columns]

    if any(w in col_names_lower for w in ["invoice", "bill", "receipt"]):
        profile["auto_detected"]["domain"] = "invoice"
    elif any(w in col_names_lower for w in ["sales", "order", "revenue"]):
        profile["auto_detected"]["domain"] = "sales"
    elif any(w in col_names_lower for w in ["employee", "salary", "payroll"]):
        profile["auto_detected"]["domain"] = "hr"
    elif any(w in col_names_lower for w in ["product", "sku", "inventory"]):
        profile["auto_detected"]["domain"] = "inventory"
    else:
        profile["auto_detected"]["domain"] = "general"

    # Auto-detect the most likely revenue/amount column
    amount_keywords = ["amount", "revenue", "total", "value", "price", "sales", "invoice"]
    for col in df.columns:
        if any(k in col.lower() for k in amount_keywords):
            if pd.api.types.is_numeric_dtype(df[col]):
                profile["auto_detected"]["revenue_column"] = col
                profile["auto_detected"]["total_revenue"] = round(
                    float(df[col].sum()), 2
                )
                break

    # Auto-detect the most likely client/company column
    client_keywords = ["client", "customer", "company", "party", "name", "vendor"]
    for col in df.columns:
        if any(k in col.lower() for k in client_keywords):
            profile["auto_detected"]["client_column"] = col
            profile["auto_detected"]["total_clients"] = int(df[col].nunique())
            break

    return profile


def profile_to_prompt_context(profile: dict) -> str:
    """
    Convert a profile dict to a plain-text context string for LLM prompts.
    Uses ONLY the auto-detected info, never hardcodes periods or column names.
    """
    auto = profile.get("auto_detected", {})
    lines = [
        f"File: {profile.get('source_file', 'uploaded file')}",
        f"Size: {profile['shape']['rows']} rows, "
        f"{profile['shape']['columns']} columns",
    ]

    if "domain" in auto:
        lines.append(f"Detected data type: {auto['domain']} data")

    if "time_period" in auto:
        lines.append(f"Time span: {auto['time_period']}")

    if "revenue_column" in auto and "total_revenue" in auto:
        lines.append(
            f"Total {auto['revenue_column']}: {auto['total_revenue']:,.2f}"
        )

    if "client_column" in auto and "total_clients" in auto:
        lines.append(
            f"Unique {auto['client_column']}s: {auto['total_clients']}"
        )

    if profile["date_columns"]:
        lines.append("\nDate columns:")
        for col, info in profile["date_columns"].items():
            lines.append(
                f"  - {col}: {info['min'][:10]} to {info['max'][:10]} "
                f"({info['range_days']} days)"
            )

    if profile["numeric_columns"]:
        lines.append("\nNumeric columns:")
        for col, info in profile["numeric_columns"].items():
            lines.append(
                f"  - {col}: min={info['min']}, max={info['max']}, "
                f"mean={info['mean']}, total={info['sum']}, "
                f"nulls={info['null_pct']}%"
            )

    if profile["categorical_columns"]:
        lines.append("\nCategorical columns:")
        for col, info in profile["categorical_columns"].items():
            top = ", ".join(
                [f"{k}({v})" for k, v in list(info["top_values"].items())[:5]]
            )
            lines.append(
                f"  - {col}: {info['unique_count']} unique. Top: {top}"
            )

    if profile["sample_rows"]:
        lines.append("\nSample rows:")
        for row in profile["sample_rows"][:3]:
            lines.append(f"  {row}")

    return "\n".join(lines)
