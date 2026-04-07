from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.agent import _dataframes, _profiles
from app.services.dashboard_gen import generate_dashboard


router = APIRouter()


def _build_kpi_cards(df: pd.DataFrame, profile: Dict[str, Any]) -> List[Dict[str, Any]]:
    auto = profile.get("auto_detected") or {}
    numeric_cols = profile.get("numeric_columns") or {}
    categorical_cols = profile.get("categorical_columns") or {}
    revenue_col = auto.get("revenue_column")
    client_col = auto.get("client_column")

    kpis: List[Dict[str, Any]] = []

    kpis.append({
        "title": "Total Records",
        "value": int(df.shape[0]),
        "unit": "",
        "trend": 0,
        "is_currency": False,
    })

    if revenue_col and revenue_col in df.columns:
        rev = pd.to_numeric(df[revenue_col], errors="coerce").dropna()
        if len(rev) > 0:
            kpis.append({
                "title": f"Total {revenue_col}",
                "value": float(rev.sum()),
                "unit": "",
                "trend": 0,
                "is_currency": True,
            })

    for col, stats in list(numeric_cols.items())[:2]:
        if col == revenue_col:
            continue
        num = pd.to_numeric(df[col], errors="coerce").dropna()
        if len(num) == 0:
            continue
        kpis.append({
            "title": f"Avg {col}",
            "value": float(num.mean()),
            "unit": "",
            "trend": 0,
            "is_currency": False,
        })
        if len(kpis) >= 5:
            break

    return kpis[:5]


def _build_category_values(df: pd.DataFrame, profile: Dict[str, Any]) -> List[str]:
    auto = profile.get("auto_detected") or {}
    client_col = auto.get("client_column")
    categorical_cols = list((profile.get("categorical_columns") or {}).keys())

    col = client_col if (client_col and client_col in df.columns) else (categorical_cols[0] if categorical_cols else None)
    if not col or col not in df.columns:
        return []

    vals = df[col].dropna().astype(str).unique().tolist()
    return sorted(vals)[:20]


class AutoDashboardRequest(BaseModel):
    filename: str


@router.post("/api/auto-dashboard")
async def auto_dashboard(req: AutoDashboardRequest) -> Dict[str, Any]:
    filename = req.filename
    if not filename:
        raise HTTPException(status_code=400, detail="filename is required")
    if filename not in _dataframes or filename not in _profiles:
        raise HTTPException(status_code=404, detail=f"File not loaded: {filename}")

    df = _dataframes[filename]
    profile = _profiles[filename]
    charts = generate_dashboard(df, profile)
    kpi_cards = _build_kpi_cards(df, profile)
    category_values = _build_category_values(df, profile)

    auto = profile.get("auto_detected") or {}
    revenue_col = auto.get("revenue_column") or "amount"
    client_col = auto.get("client_column") or "category"
    total_records = int(df.shape[0])
    ceo_summary = (
        f"Dataset has {total_records:,} records across {df.shape[1]} columns. "
        f"Key dimensions: {revenue_col}, {client_col}."
    )

    return {
        "charts": charts,
        "kpi_cards": kpi_cards,
        "category_values": category_values,
        "ceo_summary": ceo_summary,
    }


class FilterRequest(BaseModel):
    filters: Dict[str, Any] = Field(default_factory=dict)
    sort_col: Optional[str] = None
    sort_asc: bool = True
    limit: int = Field(default=200, le=2000)


@router.post("/api/files/{filename}/filter")
async def filter_file(
    filename: str,
    req: FilterRequest,
) -> Dict[str, Any]:
    if filename not in _dataframes:
        raise HTTPException(status_code=404, detail=f"File not loaded: {filename}")

    df = _dataframes[filename]
    if df is None or df.empty:
        return {"rows": [], "total": 0}

    out = df.copy()

    # Apply filters
    for col, rule in (req.filters or {}).items():
        if col not in out.columns:
            continue

        if isinstance(rule, dict):
            # Numeric range: {min, max}
            if "min" in rule or "max" in rule:
                num = pd.to_numeric(out[col], errors="coerce")
                if "min" in rule and rule["min"] is not None:
                    out = out[num >= float(rule["min"])]
                if "max" in rule and rule["max"] is not None:
                    out = out[num <= float(rule["max"])]
                continue

            # Categorical values: {values:[...]}
            if "values" in rule and isinstance(rule["values"], list):
                vals = rule["values"]
                out = out[out[col].isin(vals)]
                continue

        elif isinstance(rule, str):
            # Text search
            out = out[out[col].astype(str).str.contains(rule, case=False, na=False)]
            continue

    total = int(len(out))

    # Sort
    if req.sort_col and req.sort_col in out.columns:
        try:
            out = out.sort_values(by=req.sort_col, ascending=req.sort_asc)
        except Exception:
            pass

    # Paginate
    rows = out.head(req.limit).to_dict(orient="records")
    return {"rows": rows, "total": total}

