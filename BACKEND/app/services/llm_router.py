from __future__ import annotations

from typing import Iterable, Optional

from langchain_ollama import ChatOllama

from app.core.config import settings


def _first_available_model(candidates: Iterable[str]) -> str:
    for m in candidates:
        if m and isinstance(m, str):
            return m
    raise ValueError("No model candidates provided.")


def get_intent_classifier_llm() -> ChatOllama:
    """
    Deterministic classifier model (temperature=0.0).
    """
    model = getattr(settings, "CLASSIFIER_MODEL", None) or settings.CHAT_MODEL
    return ChatOllama(
        model=model,
        temperature=0.0,
        base_url=settings.OLLAMA_BASE_URL,
        num_ctx=512,
        num_predict=96,
        format="json",
    )


def get_chat_llm(temperature: float = 0.7) -> ChatOllama:
    """
    Natural chat model (slightly higher temperature).
    """
    model = settings.CHAT_MODEL
    return ChatOllama(
        model=model,
        temperature=float(temperature),
        base_url=settings.OLLAMA_BASE_URL,
        num_ctx=1024,
        num_predict=256,
    )


def get_sql_llm() -> ChatOllama:
    """
    SQL generation / reasoning model (temperature=0.1), with safe fallbacks
    in case the requested model isn't present locally.
    """
    requested = getattr(settings, "SQL_MODEL", None) or "deepseek-r1:14b"
    model = _first_available_model(
        [
            requested,
            "deepseek-r1:8b",
            "qwen2.5-coder:7b",
            "qwen2.5:7b",
            "mistral:7b",
        ]
    )
    return ChatOllama(
        model=model,
        temperature=0.1,
        base_url=settings.OLLAMA_BASE_URL,
        num_ctx=1024,
        num_predict=320,
    )

