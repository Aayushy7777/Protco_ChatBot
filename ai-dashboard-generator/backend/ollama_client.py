from __future__ import annotations

import json
import os
import re
from typing import Any, Dict, List

import httpx
from dotenv import load_dotenv

load_dotenv()

OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


def _strip_fences(text: str) -> str:
    t = (text or "").strip()
    t = re.sub(r"^```[a-zA-Z]*\s*", "", t)
    t = re.sub(r"\s*```$", "", t)
    return t.strip()


async def check_ollama() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            r = await client.get(f"{OLLAMA_BASE_URL}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


async def generate_insights(profile: Dict[str, Any]) -> List[str]:
    prompt = (
        "Given this dataset, generate exactly 3 one-sentence business insights with specific numbers. "
        "Return as JSON array [{\"insight\": \"...\"}]. Dataset:\n"
        f"{profile.get('context_text', '')}"
    )
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            r = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={"model": OLLAMA_MODEL, "prompt": prompt, "stream": False},
            )
            raw = (r.json() or {}).get("response", "")
            cleaned = _strip_fences(raw)
            match = re.search(r"\[[\s\S]*\]", cleaned)
            payload = json.loads(match.group(0) if match else cleaned)
            out = []
            if isinstance(payload, list):
                for x in payload[:3]:
                    if isinstance(x, dict) and x.get("insight"):
                        out.append(str(x["insight"]).strip())
            return out or ["Analysis complete. Ask questions below."]
    except Exception:
        return ["Analysis complete. Ask questions below."]


async def chat(message: str, context: str, history: List[Dict[str, str]]) -> str:
    system = (
        "You are a data analyst. Answer questions about this dataset. "
        "Use only the data provided. Be specific with numbers. "
        "Keep answers under 5 sentences. "
        f"Dataset context: {context}"
    )
    messages = (history or [])[-8:] + [{"role": "user", "content": message}]
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "system": system,
        "stream": False,
        # Stable defaults for better grounded answers.
        "options": {"temperature": 0.2, "top_p": 0.9, "num_ctx": 4096},
    }
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            r = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            data = r.json() or {}
            out = ((data.get("message") or {}).get("content") or "").strip()
            if out:
                return out
            # one retry with lower temperature for strictness
            payload["options"]["temperature"] = 0.0
            r2 = await client.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload)
            data2 = r2.json() or {}
            out2 = ((data2.get("message") or {}).get("content") or "").strip()
            return out2 or "No response."
    except Exception:
        return "Sorry, could not connect to Ollama. Make sure ollama serve is running."
