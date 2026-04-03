from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import pandas as pd


def _read_csv_with_fallbacks(filepath: str) -> pd.DataFrame:
    df = pd.read_csv(filepath)
    unnamed_ratio = 0.0
    if len(df.columns) > 0:
        unnamed_ratio = sum(str(c).startswith("Unnamed") for c in df.columns) / float(len(df.columns))
    if unnamed_ratio > 0.6:
        best = df
        best_score = -1
        for hdr in [0, 1, 2]:
            try:
                candidate = pd.read_csv(filepath, header=hdr)
                score = sum(not str(c).startswith("Unnamed") for c in candidate.columns)
                if score > best_score:
                    best = candidate
                    best_score = score
            except Exception:
                continue
        return best
    return df


def read_file(filepath: str) -> pd.DataFrame:
    ext = Path(filepath).suffix.lower()
    if ext == ".csv":
        df = _read_csv_with_fallbacks(filepath)
    elif ext in {".xlsx", ".xls"}:
        raw = pd.read_excel(filepath, header=None)
        best_row = 0
        best_score = -1
        for i in range(min(8, len(raw))):
            row = raw.iloc[i]
            score = sum(1 for v in row if isinstance(v, str) and len(v.strip()) > 1)
            if score > best_score:
                best_score = score
                best_row = i
        df = pd.read_excel(filepath, header=best_row)
    else:
        raise ValueError("Unsupported file type. Use CSV/XLSX/XLS.")

    df = df.dropna(how="all").dropna(axis=1, how="all")
    df = df[[c for c in df.columns if not str(c).startswith("Unnamed")]]
    return df


def detect_types(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    for col in out.columns:
        numeric = pd.to_numeric(out[col], errors="coerce")
        if numeric.notna().mean() > 0.7:
            out[col] = numeric
            continue

        parsed = pd.to_datetime(out[col], errors="coerce")
        if parsed.notna().mean() > 0.6:
            out[col] = parsed
            continue

        out[col] = out[col].astype(str).str.strip().replace("nan", "")
    return out


def format_value(n: float) -> str:
    if n >= 10_000_000:
        return f"₹{n / 10_000_000:.2f}Cr"
    if n >= 100_000:
        return f"₹{n / 100_000:.2f}L"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(round(n, 2))


def build_context_text(profile: Dict[str, Any]) -> str:
    lines = [
        f"Filename: {profile.get('filename')}",
        f"Rows: {profile.get('rows')}",
        f"Columns: {', '.join(profile.get('columns', []))}",
        "",
        "Numeric stats:",
    ]

    for col, stats in (profile.get("numeric") or {}).items():
        lines.append(
            f"- {col}: min={stats.get('min')}, max={stats.get('max')}, mean={stats.get('mean')}, "
            f"sum={stats.get('sum')}, std={stats.get('std')}, median={stats.get('median')}, null_pct={stats.get('null_pct')}"
        )

    lines.append("")
    lines.append("Categorical stats:")
    for col, stats in (profile.get("categorical") or {}).items():
        top = stats.get("top_15") or {}
        top10 = list(top.items())[:10]
        top_text = ", ".join([f"{k}({v})" for k, v in top10])
        lines.append(f"- {col}: unique={stats.get('unique')}, null_pct={stats.get('null_pct')}, top={top_text}")

    lines.append("")
    lines.append("Date stats:")
    for col, stats in (profile.get("dates") or {}).items():
        lines.append(f"- {col}: min={stats.get('min')}, max={stats.get('max')}, range_days={stats.get('range_days')}")

    lines.append("")
    lines.append("Sample rows (first 3):")
    for row in (profile.get("sample") or [])[:3]:
        lines.append(json.dumps(row, ensure_ascii=False, default=str))

    return "\n".join(lines)


def build_profile(df: pd.DataFrame, filename: str) -> Dict[str, Any]:
    profile: Dict[str, Any] = {
        "filename": filename,
        "rows": int(len(df)),
        "columns": [str(c) for c in df.columns],
        "dtypes": {str(c): str(df[c].dtype) for c in df.columns},
        "sample": df.head(5).fillna("").to_dict(orient="records"),
        "numeric": {},
        "categorical": {},
        "dates": {},
        "auto": {},
        "context_text": "",
    }

    for col in df.columns:
        s = df[col]
        non_null = s.dropna()
        if len(non_null) == 0:
            continue
        if pd.api.types.is_numeric_dtype(s):
            profile["numeric"][str(col)] = {
                "min": float(non_null.min()),
                "max": float(non_null.max()),
                "mean": round(float(non_null.mean()), 2),
                "sum": round(float(non_null.sum()), 2),
                "std": round(float(non_null.std()), 2) if len(non_null) > 1 else 0.0,
                "median": round(float(non_null.median()), 2),
                "null_pct": round(float(s.isna().mean() * 100), 1),
            }
        elif pd.api.types.is_datetime64_any_dtype(s):
            mn, mx = non_null.min(), non_null.max()
            profile["dates"][str(col)] = {
                "min": str(mn.date()),
                "max": str(mx.date()),
                "range_days": int((mx - mn).days),
            }
        else:
            top = non_null.astype(str).value_counts().head(15).to_dict()
            profile["categorical"][str(col)] = {
                "unique": int(non_null.astype(str).nunique()),
                "top_15": {str(k): int(v) for k, v in top.items()},
                "null_pct": round(float(s.isna().mean() * 100), 1),
            }

    amount_kw = ["amount", "revenue", "total", "value", "price", "sales", "cost", "budget", "salary"]
    status_kw = ["status", "state", "stage", "phase", "progress"]
    category_kw = ["category", "type", "department", "project", "group", "team"]
    date_kw = ["date", "time", "start", "end", "created", "due", "deadline"]
    name_kw = ["name", "client", "customer", "employee", "person", "assigned"]

    for col in profile["columns"]:
        lc = col.lower()
        if any(k in lc for k in amount_kw) and col in profile["numeric"]:
            profile["auto"].setdefault("amount_col", col)
        if any(k in lc for k in status_kw):
            profile["auto"].setdefault("status_col", col)
        if any(k in lc for k in category_kw):
            profile["auto"].setdefault("category_col", col)
        if any(k in lc for k in date_kw) and col in profile["dates"]:
            profile["auto"].setdefault("date_col", col)
        if any(k in lc for k in name_kw) and col in profile["categorical"]:
            profile["auto"].setdefault("name_col", col)

    for col, stats in profile["numeric"].items():
        mn, mx = stats["min"], stats["max"]
        if mn >= 0 and mx <= 1:
            profile["auto"].setdefault("progress_col", col)
        elif mn >= 0 and mx <= 100:
            profile["auto"].setdefault("pct_col", col)

    profile["context_text"] = build_context_text(profile)
    return profile
