from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List

import pandas as pd


def load_csv(path: str) -> pd.DataFrame:
    df = pd.read_csv(path)
    return clean_data(df)


def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out = out.dropna(how="all").dropna(axis=1, how="all")
    out.columns = [str(c).strip() for c in out.columns]
    for col in out.columns:
        num = pd.to_numeric(out[col], errors="coerce")
        if num.notna().mean() >= 0.7:
            out[col] = num
            continue
        dt = pd.to_datetime(out[col], errors="coerce")
        if dt.notna().mean() >= 0.6:
            out[col] = dt
            continue
        out[col] = out[col].astype(str).fillna("").str.strip()
    return out


def detect_schema(df: pd.DataFrame) -> Dict[str, Any]:
    numeric, categorical, datetime = [], [], []
    for c in df.columns:
        s = df[c]
        if pd.api.types.is_numeric_dtype(s):
            numeric.append(c)
        elif pd.api.types.is_datetime64_any_dtype(s):
            datetime.append(c)
        else:
            categorical.append(c)

    summary: Dict[str, Any] = {
        "columns": [str(c) for c in df.columns],
        "row_count": int(len(df)),
        "numeric": numeric,
        "categorical": categorical,
        "datetime": datetime,
        "stats": {},
        "unique_values": {},
        "relationships": {},
    }

    for c in numeric:
        s = pd.to_numeric(df[c], errors="coerce").dropna()
        if len(s) == 0:
            continue
        summary["stats"][c] = {
            "mean": float(s.mean()),
            "median": float(s.median()),
            "min": float(s.min()),
            "max": float(s.max()),
            "sum": float(s.sum()),
        }

    for c in categorical:
        vc = df[c].astype(str).value_counts().head(20).to_dict()
        summary["unique_values"][c] = {str(k): int(v) for k, v in vc.items()}

    if len(numeric) >= 2:
        corr = df[numeric].corr(numeric_only=True).fillna(0.0).to_dict()
        summary["relationships"]["numeric_correlation"] = corr

    return summary


def merge_on_common_columns(dfs: Dict[str, pd.DataFrame]) -> pd.DataFrame | None:
    keys = list(dfs.keys())
    if len(keys) < 2:
        return None
    merged = dfs[keys[0]]
    for k in keys[1:]:
        common = [c for c in merged.columns if c in dfs[k].columns]
        if not common:
            continue
        merged = merged.merge(dfs[k], on=common[0], how="inner")
    return merged if len(merged.columns) > 0 else None

