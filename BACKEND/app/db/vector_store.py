"""Minimal ChromaDB persistence helper.

The main RAG logic uses `langchain_community.vectorstores.Chroma` directly,
but this file exists to keep your backend folder structure consistent.
"""

from __future__ import annotations

from pathlib import Path

import chromadb

from app.core.config import settings


def get_chroma_client() -> chromadb.PersistentClient:
    Path(settings.CHROMA_PATH).mkdir(parents=True, exist_ok=True)
    return chromadb.PersistentClient(path=settings.CHROMA_PATH)

