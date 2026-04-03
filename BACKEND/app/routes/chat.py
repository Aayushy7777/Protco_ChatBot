from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from langchain_core.messages import AIMessage, HumanMessage

from app.services.agent import build_agent, parse_agent_response, _profiles


router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    active_file: str = ""
    conversation_history: List[Dict[str, Any]] = Field(default_factory=list)
    all_files: List[str] = Field(default_factory=list)


def _convert_history(history: List[Dict[str, Any]], limit: int = 10) -> List[Any]:
    out: List[Any] = []
    tail = history[-limit:] if history else []
    for item in tail:
        role = (item.get("role") or "").lower()
        content = item.get("content") or ""
        if role == "user":
            out.append(HumanMessage(content=content))
        elif role == "assistant":
            out.append(AIMessage(content=content))
    return out


@router.post("/api/chat")
async def chat(req: ChatRequest) -> Dict[str, Any]:
    try:
        message = (req.message or "").strip()
        if not message:
            raise HTTPException(status_code=400, detail="Message cannot be empty.")

        active_file = req.active_file or (req.all_files[0] if req.all_files else "")
        if not active_file:
            raise HTTPException(status_code=400, detail="No active_file selected.")

        if active_file not in _profiles:
            raise HTTPException(status_code=404, detail=f"File not found in memory: {active_file}")

        profile = _profiles[active_file]

        history_messages = _convert_history(req.conversation_history, limit=10)
        agent_executor = build_agent(active_file=active_file, profile=profile)

        try:
            result = agent_executor.invoke({"input": message, "chat_history": history_messages})
        except Exception as e:
            # Ollama can reject large models when RAM is insufficient.
            # Retry with a smaller fallback model so the app still works.
            msg = str(e).lower()
            if "requires more system memory" in msg:
                agent_executor = build_agent(
                    active_file=active_file,
                    profile=profile,
                    chat_model_override="mistral:7b",
                )
                result = agent_executor.invoke(
                    {"input": message, "chat_history": history_messages}
                )
            else:
                raise

        raw = result.get("output") if isinstance(result, dict) else str(result)
        parsed = parse_agent_response(raw)
        return parsed
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

