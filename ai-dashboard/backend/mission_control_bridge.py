import asyncio
import os
from typing import Optional

import httpx

def _cfg():
    return {
        "MC_URL": os.getenv("MC_URL", "http://localhost:3000"),
        "MC_API_KEY": os.getenv("MC_API_KEY", ""),
        "AGENT_ID": os.getenv("MC_AGENT_ID", ""),
        "AGENT_NAME": os.getenv("MC_AGENT_NAME", "ai-dashboard-agent-v2"),
        "AGENT_ENDPOINT": os.getenv("MC_AGENT_ENDPOINT", "http://localhost:8011"),
        "MODEL": os.getenv("OLLAMA_MODEL", "llama3.1"),
    }


async def send_heartbeat(status: str = "active", current_task: Optional[str] = None):
    cfg = _cfg()
    if not cfg["MC_API_KEY"] or not cfg["AGENT_ID"]:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{cfg['MC_URL']}/api/agents/{cfg['AGENT_ID']}/heartbeat",
                headers={"Authorization": f"Bearer {cfg['MC_API_KEY']}"},
                json={
                    "status": status,
                    "current_task": current_task,
                    "model": cfg["MODEL"],
                    "endpoint": cfg["AGENT_ENDPOINT"],
                },
            )
    except Exception:
        pass


async def heartbeat_loop():
    while True:
        await send_heartbeat("active")
        await asyncio.sleep(30)


async def complete_task(task_id: str, result: str, status: str = "done"):
    cfg = _cfg()
    if not cfg["MC_API_KEY"]:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.put(
                f"{cfg['MC_URL']}/api/tasks/{task_id}",
                headers={"Authorization": f"Bearer {cfg['MC_API_KEY']}"},
                json={"status": status, "result": result, "completed_by": cfg["AGENT_NAME"]},
            )
    except Exception:
        pass


async def log_activity(event_type: str, message: str, metadata: dict | None = None):
    cfg = _cfg()
    if not cfg["MC_API_KEY"]:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{cfg['MC_URL']}/api/activities",
                headers={"Authorization": f"Bearer {cfg['MC_API_KEY']}"},
                json={
                    "agent": cfg["AGENT_NAME"],
                    "type": event_type,
                    "message": message,
                    "metadata": metadata or {},
                },
            )
    except Exception:
        pass


async def report_tokens(prompt_tokens: int, completion_tokens: int, model: str | None = None):
    cfg = _cfg()
    if not cfg["MC_API_KEY"]:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{cfg['MC_URL']}/api/tokens",
                headers={"Authorization": f"Bearer {cfg['MC_API_KEY']}"},
                json={
                    "agent": cfg["AGENT_NAME"],
                    "model": model or cfg["MODEL"],
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            )
    except Exception:
        pass

