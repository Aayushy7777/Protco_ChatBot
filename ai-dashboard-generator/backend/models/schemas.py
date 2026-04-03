from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    uploaded_files: List[str]
    schemas: Dict[str, Dict[str, Any]]


class ChatRequest(BaseModel):
    query: str
    active_dataset: Optional[str] = None
    history: List[Dict[str, str]] = Field(default_factory=list)


class ChatResponse(BaseModel):
    mode: str
    response: str
    dashboard: Optional[Dict[str, Any]] = None
    data: Optional[Dict[str, Any]] = None

