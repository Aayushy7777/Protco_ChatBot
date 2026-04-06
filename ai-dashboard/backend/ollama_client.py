import json
import os
import re
from typing import Any, Dict, List

import httpx

OLLAMA_BASE = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")


async def check_ollama() -> bool:
    try:
        async with httpx.AsyncClient(timeout=3) as c:
            r = await c.get(f"{OLLAMA_BASE}/api/tags")
            return r.status_code == 200
    except Exception:
        return False


async def chat(message: str, context: str, history: list) -> str:
    system = f"""You are an expert data analyst assistant.
Answer questions about this dataset concisely and accurately.
Use specific numbers from the data. Max 4 sentences.
Do not introduce quarter labels unless they exist in the data.
Use exact column names from the data.

Dataset context:
{context}"""

    messages: List[Dict[str, str]] = []
    for h in (history or [])[-8:]:
        messages.append(
            {
                "role": h.get("role", "user"),
                "content": h.get("content", ""),
            }
        )
    messages.append({"role": "user", "content": message})

    try:
        async with httpx.AsyncClient(timeout=60) as c:
            r = await c.post(
                f"{OLLAMA_BASE}/api/chat",
                json={
                    "model": MODEL,
                    "messages": messages,
                    "system": system,
                    "stream": False,
                },
            )
            data = r.json()
            return data["message"]["content"]
    except Exception as e:
        return (
            "Ollama is not responding. Make sure 'ollama serve' is running. "
            f"Error: {str(e)}"
        )


async def generate_insights(context: str) -> list[str]:
    prompt = f"""Given this dataset, write exactly 3 insights.
Each must be one sentence with a specific number.
Return ONLY a JSON array: [{{"insight":"..."}}]
No markdown, no explanation, just the JSON array.

{context}"""

    try:
        async with httpx.AsyncClient(timeout=30) as c:
            r = await c.post(
                f"{OLLAMA_BASE}/api/generate",
                json={"model": MODEL, "prompt": prompt, "stream": False},
            )
            raw = r.json().get("response", "")
            raw = re.sub(r"```json|```", "", raw).strip()
            match = re.search(r"\[.*\]", raw, re.DOTALL)
            if match:
                items = json.loads(match.group())
                return [i.get("insight", "") for i in items if i.get("insight")]
    except Exception:
        pass
    return ["Upload complete. Ask questions in the chat."]


async def generate_suggestions(profile: dict) -> list[str]:
    auto = profile.get("auto", {}) or {}
    suggestions: List[str] = []

    cat = auto.get("category_col")
    amt = auto.get("amount_col")
    status = auto.get("status_col")
    prog = auto.get("progress_col") or auto.get("pct_col")

    if status:
        suggestions.append(f"Which {cat or 'item'} is most behind?")
        top_status = list((profile.get("categorical", {}) or {}).get(status, {}).get("top_15", {}).keys())
        if top_status:
            suggestions.append(f"Show all {str(top_status[0]).lower()} items")

    if amt and cat:
        suggestions.append(f"What is the total {amt.replace('_',' ')}?")
        suggestions.append(f"Top 5 {cat.replace('_',' ')}s by {amt.replace('_',' ')}")

    if prog:
        suggestions.append("Who has completed all tasks?")
        suggestions.append("What are the longest tasks?")

    suggestions.append("Summarize this dataset")
    return suggestions[:6]

