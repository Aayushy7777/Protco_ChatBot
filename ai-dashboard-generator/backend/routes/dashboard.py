from __future__ import annotations

from typing import Any, Dict

from fastapi import APIRouter, HTTPException

from utils.state import STATE


router = APIRouter()


@router.get("/dashboard")
async def get_dashboard() -> Dict[str, Any]:
    if not STATE.last_dashboard.get("charts"):
        raise HTTPException(status_code=404, detail="No dashboard generated yet.")
    return STATE.last_dashboard

