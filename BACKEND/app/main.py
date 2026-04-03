from __future__ import annotations

import logging
from pathlib import Path
from typing import Any, Dict

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.routes.chat import router as chat_router
from app.routes.dashboard import router as dashboard_router
from app.routes.upload import router as upload_router
from app.services.agent import _dataframes, _profiles


logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(chat_router)
app.include_router(dashboard_router)


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {
        "status": "ok",
        "models": {"chat": settings.CHAT_MODEL, "embed": settings.EMBED_MODEL},
    }


@app.get("/api/files")
def list_files() -> Dict[str, Any]:
    """
    List currently loaded in-memory files.
    (Frontend relies on this even though it wasn't part of the minimal spec.)
    """
    files = []
    for name, df in _dataframes.items():
        if df is None:
            continue
        files.append(
            {
                "name": name,
                "rows": int(getattr(df, "shape", (0, 0))[0]),
                "columns": int(getattr(df, "shape", (0, 0))[1]),
            }
        )
    return {"files": files}


@app.delete("/api/files/{filename}")
def delete_file(filename: str) -> Dict[str, Any]:
    if filename not in _dataframes:
        raise HTTPException(status_code=404, detail=f"File not loaded: {filename}")

    # Remove from in-memory stores
    _dataframes.pop(filename, None)
    _profiles.pop(filename, None)

    # Delete uploaded file from disk
    try:
        upload_path = Path(settings.UPLOAD_PATH) / filename
        if upload_path.exists():
            upload_path.unlink()
    except Exception:
        # Don't fail the whole request if cleanup on disk fails.
        logger.exception("Failed to delete uploaded file from disk")

    return {"deleted": filename}


@app.on_event("startup")
def _startup() -> None:
    Path(settings.UPLOAD_PATH).mkdir(parents=True, exist_ok=True)
    Path(settings.CHROMA_PATH).mkdir(parents=True, exist_ok=True)

