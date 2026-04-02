"""
ollama_manager.py
-----------------
Handles local Ollama model loading, switching, and inference.
Optimized for Lenovo Legion RTX 4070 (8GB VRAM).

Uses official ollama-python package.
"""

import asyncio
import json
import logging
from enum import Enum
from typing import AsyncGenerator
from ollama import AsyncClient, ResponseError

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"

class ModelRole(str, Enum):
    CHAT = "chat"
    SUMMARY = "summary"
    CHART = "chart"
    DASHBOARD = "dashboard"
    INTENT = "intent"

MODEL_MAP = {
    ModelRole.INTENT: "mistral:7b",
    ModelRole.CHART: "qwen2.5:7b",
    ModelRole.DASHBOARD: "qwen2.5-coder:7b",
    ModelRole.CHAT: "llama3.1:8b",
    ModelRole.SUMMARY: "llama3.1:8b",
}

# ── System prompts ──────────────────────────────────────────────────────────

SYSTEM_PROMPTS = {
    ModelRole.CHAT: """You are a helpful business analyst assistant.
The user is exploring company sales dashboard data.
Answer questions clearly and concisely. Format Indian currency using ₹ and Crores/Lakhs when appropriate.
Keep your answers brief and direct.""",

    ModelRole.SUMMARY: """You are a business analyst presenting to a CEO.
Write exactly 2 sentences of KEY BUSINESS INSIGHT the CEO must know based on the provided stats.
Be specific with numbers. Use ₹ and Cr/L formatting. No bullet points.""",

    ModelRole.CHART: """You are a data visualization assistant. Given a prompt and columns,
produce a valid JSON object for Recharts. Return ONLY the JSON, no markdown fences.
Schema context will be injected before each request.""",

    ModelRole.DASHBOARD: """You are an expert Data Engineer. Given a database schema,
identify key metrics and category columns to automatically generate a powerful dashboard config.
Return EXACTLY a JSON object with no markdown fences.""",

    ModelRole.INTENT: """You classify user intent. Respond with ONLY one word:
  - CHART   → user wants a graph or visualisation
  - TABLE   → user wants rows of data
  - STATS   → user wants summary statistics
  - CHAT    → general question, no data needed
No other output.""",
}

# ── OllamaManager ──────────────────────────────────────────────────────────

class OllamaManager:
    def __init__(self):
        self._active_model: str | None = None
        self._client = AsyncClient(host=OLLAMA_BASE_URL)

    async def switch_model(self, role: ModelRole) -> str:
        """
        Switch to the model for the given role.
        Unloads the previous model from VRAM first to free memory.
        """
        target = MODEL_MAP[role]
        if self._active_model == target:
            return target  # already loaded, nothing to do

        # Unload previous model from VRAM 
        if self._active_model:
            logger.info(f"Unloading {self._active_model} from VRAM...")
            try:
                await self._client.generate(model=self._active_model, prompt="", keep_alive=0)
            except Exception as e:
                logger.warning(f"Could not unload model cleanly: {e}")

        # The ollama client auto-pulls missing models organically or fails cleanly
        self._active_model = target
        logger.info(f"Active model: {target}")
        return target

    async def generate(
        self,
        role: ModelRole,
        user_prompt: str,
        schema_context: str = "",
        stream: bool = False,
        temp: float = None,
    ) -> str | AsyncGenerator[str, None]:
        """
        Run inference. Handles model switching automatically.
        Returns full string when stream=False, async generator when stream=True.
        """
        model = await self.switch_model(role)
        system = SYSTEM_PROMPTS[role]

        if role in (ModelRole.CHART, ModelRole.DASHBOARD) and schema_context:
            system = f"{system}\n\n--- CONTEXT ---\n{schema_context}\n---"

        messages = [
            {"role": "system", "content": system},
            {"role": "user",   "content": user_prompt},
        ]

        options = {
            "temperature": temp if temp is not None else (
                0.0 if role in (ModelRole.INTENT, ModelRole.CHART, ModelRole.DASHBOARD) 
                else 0.6 if role == ModelRole.CHAT 
                else 0.3 if role == ModelRole.SUMMARY 
                else 0.1
            ),
            "num_ctx": 8192,
        }

        if stream:
            return self._stream_response(model, messages, options)
        else:
            resp = await self._client.chat(model=model, messages=messages, options=options)
            return resp.message.content.strip()

    async def _stream_response(self, model: str, messages: list, options: dict) -> AsyncGenerator[str, None]:
        try:
            async for chunk in await self._client.chat(model=model, messages=messages, options=options, stream=True):
                token = chunk.message.content
                if token:
                    yield token
        except ResponseError as e:
            yield f"[Ollama Error: {e.error}]"
        except Exception as e:
            yield f"[Connection Error: {str(e)}]"

    async def health_check(self) -> dict:
        """Returns Ollama version and available models."""
        try:
            resp = await self._client.list()
            models = [m.model for m in resp.models]
            return {"status": "ok", "models": models}
        except Exception as e:
            return {"status": "error", "detail": str(e)}

# ── Module-level singleton ──────────────────────────────────────────────────

ollama = OllamaManager()
