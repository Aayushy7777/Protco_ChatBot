from __future__ import annotations

import json
import os
from typing import Any, Dict, List

import httpx


OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


def prompt_templates() -> Dict[str, str]:
    return {
        "chat": (
            "You are a data analyst assistant. Answer only from provided context and schema. "
            "Be concise and include numeric evidence."
        ),
        "dashboard": (
            "Generate dashboard chart plan as JSON with chart types line/bar/pie and exact columns. "
            "Return JSON only."
        ),
    }


async def query_llm(system: str, user: str, history: List[Dict[str, str]] | None = None) -> str:
    messages = (history or [])[-8:] + [{"role": "user", "content": user}]
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "system": system,
        "stream": False,
        "options": {"temperature": 0.2, "top_p": 0.9, "num_ctx": 4096},
    }
    async with httpx.AsyncClient(timeout=60) as client:
        r = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
        d = r.json() if r.content else {}
        return ((d.get("message") or {}).get("content") or "").strip()

