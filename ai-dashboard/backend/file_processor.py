from __future__ import annotations

import json
import re
from typing import Any, Dict, Optional

import numpy as np
import pandas as pd


def read_file(filepath: str) -> pd.DataFrame:
    """
    Read CSV/XLSX/XLS and aggressively clean headers/empties.
    """
    path = str(filepath)
    ext = path.split(".")[-1].lower()

    if ext in {"xlsx", "xls"}:
        # Read with header=None first, then score rows 0..7 for best header candidate.
        preview = pd.read_excel(path, header=None, engine=None)
        best_row = 0
        best_score = -1
        for i in range(0, min(8, len(preview))):
            row = preview.iloc[i]
            score = 0
            for v in row.values.tolist():
                if isinstance(v, str) and len(v.strip()) > 1:
                    score += 1
                elif pd.notna(v) and not isinstance(v, (float, int, np.number)):
                    # Non-null non-numeric values also often indicate headers.
                    score += 1
            if score > best_score:
                best_score = score
                best_row = i

        df = pd.read_excel(path, header=best_row, engine=None)
    elif ext == "csv":
        # Try default read; if many "Unnamed" cols, try skiprows 1..3.
        attempts = []
        for skip in [0, 1, 2, 3]:
            try:
                df_try = pd.read_csv(path, skiprows=skip if skip else None)
            except TypeError:
                df_try = pd.read_csv(path, skiprows=skip)
            except Exception:
                continue

            cols = [str(c) for c in df_try.columns]
            if not cols:
                continue
            unnamed = sum(1 for c in cols if c.strip().lower().startswith("unnamed"))
            ratio = unnamed / max(1, len(cols))
            attempts.append((ratio, skip, df_try))

        if not attempts:
            raise ValueError("Could not read CSV file")

        # Choose the first attempt that yields <= 50% unnamed, else best ratio.
        attempts.sort(key=lambda x: (x[0], x[1]))
        chosen = None
        for ratio, skip, df_try in attempts:
            if ratio <= 0.5:
                chosen = df_try
                break
        df = chosen if chosen is not None else attempts[0][2]
    else:
        raise ValueError(f"Unsupported file type: .{ext}")

    # Clean dataframe
    df = df.dropna(axis=0, how="all")
    df = df.dropna(axis=1, how="all")
    df = df.loc[:, [c for c in df.columns if not str(c).strip().lower().startswith("unnamed")]]
    df.columns = [str(c).strip() for c in df.columns]
    df = df.reset_index(drop=True)
    return df


def cast_column_types(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        s = df[col]
        non_null = s.notna().sum()
        if non_null == 0:
            continue

        # Step 1 — Try numeric
        converted = pd.to_numeric(s, errors="coerce")
        numeric_success = converted.notna().sum()
        if non_null > 0 and (numeric_success / non_null) >= 0.7:
            df[col] = converted.astype("float64")
            continue

        # Step 2 — Try datetime
        parsed = pd.to_datetime(s, errors="coerce")
        dt_success = parsed.notna().sum()
        if non_null > 0 and (dt_success / non_null) >= 0.6:
            df[col] = parsed
            continue

        # Step 3 — Keep as string
        df[col] = s.astype(str).str.strip()
        df[col] = df[col].replace({"nan": ""})

    return df


def detect_special_columns(df: pd.DataFrame) -> dict:
    cols = list(df.columns)
    lower = {c: str(c).lower() for c in cols}

    def is_numeric(c: str) -> bool:
        return pd.api.types.is_numeric_dtype(df[c])

    def is_dt(c: str) -> bool:
        return pd.api.types.is_datetime64_any_dtype(df[c])

    def is_str(c: str) -> bool:
        return pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c])

    out: Dict[str, Optional[str]] = {
        "amount_col": None,
        "status_col": None,
        "category_col": None,
        "date_col": None,
        "name_col": None,
        "progress_col": None,
        "pct_col": None,
    }

    amount_kw = ["amount", "revenue", "total", "value", "price", "sales", "cost", "budget", "salary", "fee", "income", "spend"]
    status_kw = ["status", "state", "stage", "phase", "condition"]
    category_kw = ["category", "type", "project", "department", "team", "group", "division", "section", "class", "segment"]
    date_kw = ["date", "time", "created", "updated", "start", "end", "due", "deadline", "period"]
    name_kw = ["name", "client", "customer", "employee", "person", "user", "vendor", "assigned", "assignee", "owner", "contact", "member"]
    pct_kw = ["progress", "pct", "percent", "completion", "complete", "done"]

    for c in cols:
        if out["amount_col"] is None and any(k in lower[c] for k in amount_kw) and is_numeric(c):
            out["amount_col"] = c

    for c in cols:
        if out["status_col"] is None and any(k in lower[c] for k in status_kw):
            try:
                if df[c].nunique(dropna=True) < 20:
                    out["status_col"] = c
            except Exception:
                pass

    for c in cols:
        if out["category_col"] is None and any(k in lower[c] for k in category_kw) and is_str(c):
            out["category_col"] = c

    # date_col: first datetime dtype, else keyword match
    for c in cols:
        if is_dt(c):
            out["date_col"] = c
            break
    if out["date_col"] is None:
        for c in cols:
            if any(k in lower[c] for k in date_kw):
                out["date_col"] = c
                break

    for c in cols:
        if out["name_col"] is None and any(k in lower[c] for k in name_kw):
            out["name_col"] = c
            break

    for c in cols:
        if out["progress_col"] is None and is_numeric(c):
            try:
                mx = float(pd.to_numeric(df[c], errors="coerce").max())
                if mx <= 1.0:
                    out["progress_col"] = c
                    break
            except Exception:
                pass

    for c in cols:
        if out["pct_col"] is None and is_numeric(c) and any(k in lower[c] for k in pct_kw):
            try:
                series = pd.to_numeric(df[c], errors="coerce")
                mx = float(series.max())
                mn = float(series.min())
                if mx <= 100 and mn >= 0:
                    out["pct_col"] = c
                    break
            except Exception:
                pass

    # Never return invalid column names
    for k, v in list(out.items()):
        if v is not None and v not in df.columns:
            out[k] = None

    return out


def detect_domain(df: pd.DataFrame) -> str:
    tokens = []
    for c in df.columns:
        tokens.append(str(c).lower())
    # Include first 10 cell values from each column
    for c in df.columns:
        s = df[c].head(10)
        for v in s.tolist():
            if pd.isna(v):
                continue
            tokens.append(str(v).lower())

    blob = " ".join(tokens)
    if re.search(r"\b(invoice|bill|receipt)\b", blob):
        return "invoice"
    if re.search(r"\b(sales|revenue|order)\b", blob):
        return "sales"
    if re.search(r"\b(employee|salary|payroll)\b", blob):
        return "hr"
    if re.search(r"\b(product|sku|inventory|stock)\b", blob):
        return "inventory"
    if re.search(r"\b(project|task|milestone|sprint)\b", blob):
        return "project"
    if re.search(r"\b(customer|client|crm|account)\b", blob):
        return "crm"
    return "general"


def format_number(n: float) -> str:
    try:
        n = float(n)
    except Exception:
        return str(n)
    if n >= 10_000_000:
        return f"₹{n/10_000_000:.2f}Cr"
    if n >= 100_000:
        return f"₹{n/100_000:.2f}L"
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n/1_000:.1f}K"
    return str(round(n, 2))


def build_kpis(
    df: pd.DataFrame,
    auto: dict,
    numeric: dict,
    categorical: dict,
    dates: dict,
) -> list:
    kpis = []
    category_col = auto.get("category_col")
    col_count = len(df.columns)

    # Always include first KPI
    detail = f"{col_count} columns"
    if category_col and category_col in df.columns:
        try:
            detail = f"across {df[category_col].nunique()} {category_col}s"
        except Exception:
            detail = f"{col_count} columns"

    kpis.append(
        {
            "label": "Total Records",
            "value": str(len(df)),
            "detail": detail,
            "color": "blue",
        }
    )

    status_col = auto.get("status_col")
    if status_col and status_col in df.columns and status_col in categorical:
        vc = pd.Series(df[status_col]).fillna("").astype(str).str.strip()
        counts = vc.value_counts().head(3)
        for status_value, count in counts.items():
            v = str(status_value).lower()
            color = "blue"
            if any(x in v for x in ["completed", "done", "complete", "finished", "success"]):
                color = "green"
            elif any(x in v for x in ["progress", "active", "running", "ongoing", "working"]):
                color = "amber"
            elif any(x in v for x in ["started", "pending", "todo", "new", "waiting", "not"]):
                color = "red"

            pct = round((count / max(1, len(df))) * 100, 1)
            if color == "green":
                detail_text = f"{pct}% completion rate"
            elif color == "amber":
                detail_text = f"{pct}% of all tasks"
            elif color == "red":
                detail_text = f"{pct}% need attention"
            else:
                detail_text = f"{pct}% of total"

            kpis.append(
                {
                    "label": str(status_value) if str(status_value) else status_col,
                    "value": str(int(count)),
                    "detail": detail_text,
                    "color": color,
                }
            )
            if len(kpis) >= 4:
                break

    amount_col = auto.get("amount_col")
    if amount_col and amount_col in numeric:
        total = numeric[amount_col]["sum"]
        avg = numeric[amount_col]["mean"]
        kpis.append(
            {
                "label": f"Total {amount_col.replace('_',' ').title()}",
                "value": format_number(total),
                "detail": f"avg {format_number(avg)} per record",
                "color": "purple",
            }
        )
    else:
        date_col = auto.get("date_col")
        if date_col and date_col in dates:
            info = dates[date_col]
            kpis.append(
                {
                    "label": "Date Range",
                    "value": f"{info['range_days']}d",
                    "detail": f"{info['min']} → {info['max']}",
                    "color": "purple",
                }
            )

    return kpis[:5]


def build_profile(df: pd.DataFrame, filename: str) -> dict:
    numeric: Dict[str, Any] = {}
    categorical: Dict[str, Any] = {}
    dates: Dict[str, Any] = {}

    for col in df.columns:
        s = df[col]
        if pd.api.types.is_numeric_dtype(s):
            series = pd.to_numeric(s, errors="coerce")
            if series.dropna().empty:
                continue
            numeric[col] = {
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": round(float(series.mean()), 2),
                "sum": round(float(series.sum()), 2),
                "std": round(float(series.std()), 2) if series.count() > 1 else 0.0,
                "median": round(float(series.median()), 2),
                "null_pct": round(series.isnull().mean() * 100, 1),
            }
        elif pd.api.types.is_datetime64_any_dtype(s):
            series = pd.to_datetime(s, errors="coerce")
            if series.dropna().empty:
                continue
            mn = series.min()
            mx = series.max()
            dates[col] = {
                "min": str(mn.date()),
                "max": str(mx.date()),
                "range_days": int((mx - mn).days),
            }
        else:
            series = s.fillna("").astype(str).str.strip()
            top = series.value_counts().head(15).to_dict()
            categorical[col] = {
                "unique_count": int(series.nunique()),
                "top_15": {str(k): int(v) for k, v in top.items()},
                "null_pct": round(df[col].isnull().mean() * 100, 1),
            }

    auto = detect_special_columns(df)
    auto["domain"] = detect_domain(df)

    filter_values: Dict[str, Any] = {}
    category_col = auto.get("category_col")
    if category_col and category_col in df.columns:
        series = df[category_col].fillna("").astype(str).str.strip()
        vals = series.value_counts().head(8).index.tolist()
        filter_values[category_col] = [str(v) for v in vals if str(v)]

    # Context text
    lines = []
    lines.append(f"File: {filename} | {len(df)} rows | {len(df.columns)} columns")
    lines.append(f"Domain: {auto.get('domain')}")
    if dates:
        # Pick widest date range
        best = None
        for c, info in dates.items():
            if best is None or info.get("range_days", 0) > best[1].get("range_days", 0):
                best = (c, info)
        if best:
            c, info = best
            lines.append(f"Date range: {info['min']} to {info['max']} ({info['range_days']} days)")

    for col, info in list(numeric.items())[:8]:
        lines.append(
            f"{col}: min={info['min']} max={info['max']} mean={info['mean']} total={info['sum']}"
        )

    for col, info in list(categorical.items())[:8]:
        top5 = list(info.get("top_15", {}).items())[:5]
        top5_txt = ", ".join([f"{k}({v})" for k, v in top5])
        lines.append(f"{col}: {info['unique_count']} unique. Top values: {top5_txt}")

    sample_rows = df.head(3).fillna("").to_dict(orient="records")
    lines.append("Sample rows: " + json.dumps(sample_rows, ensure_ascii=False, default=str))
    context_text = "\n".join(lines)

    profile = {
        "filename": filename,
        "rows": int(len(df)),
        "col_count": int(len(df.columns)),
        "columns": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "sample": df.head(5).fillna("").to_dict(orient="records"),
        "numeric": numeric,
        "categorical": categorical,
        "dates": dates,
        "auto": auto,
        "kpis": [],
        "filter_values": filter_values,
        "context_text": context_text,
    }

    profile["kpis"] = build_kpis(df, auto, numeric, categorical, dates)
    return profile

