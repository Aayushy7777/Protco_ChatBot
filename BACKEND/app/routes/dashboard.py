from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.agent import _dataframes, _profiles
from app.services.dashboard_gen import generate_dashboard


router = APIRouter()


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
    return {"charts": charts}


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

