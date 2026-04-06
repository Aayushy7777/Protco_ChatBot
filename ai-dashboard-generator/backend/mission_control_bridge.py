import asyncio
import os
from typing import Optional

import httpx

MC_URL = os.getenv("MC_URL", "http://localhost:3000")
MC_API_KEY = os.getenv("MC_API_KEY", "")
AGENT_ID = os.getenv("MC_AGENT_ID", "")


async def send_heartbeat(status: str = "active", current_task: Optional[str] = None):
    if not MC_API_KEY or not AGENT_ID:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{MC_URL}/api/agents/{AGENT_ID}/heartbeat",
                headers={"Authorization": f"Bearer {MC_API_KEY}"},
                json={
                    "status": status,
                    "current_task": current_task,
                    "model": "llama3.1",
                    "endpoint": "http://localhost:8010",
                },
            )
    except Exception:
        pass  # Never crash if MC is offline


async def heartbeat_loop():
    while True:
        await send_heartbeat("active")
        await asyncio.sleep(30)  # every 30 seconds


async def poll_task_queue() -> dict | None:
    """Check if Mission Control has dispatched a task to us."""
    if not MC_API_KEY or not AGENT_ID:
        return None
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            r = await client.get(
                f"{MC_URL}/api/tasks/queue",
                headers={"Authorization": f"Bearer {MC_API_KEY}"},
                params={"agent": "ai-dashboard-agent"},
            )
            if r.status_code == 200:
                data = r.json()
                tasks = data.get("tasks", [])
                return tasks[0] if tasks else None
    except Exception:
        return None


async def complete_task(task_id: str, result: str, status: str = "done"):
    if not MC_API_KEY:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.put(
                f"{MC_URL}/api/tasks/{task_id}",
                headers={"Authorization": f"Bearer {MC_API_KEY}"},
                json={
                    "status": status,
                    "result": result,
                    "completed_by": "ai-dashboard-agent",
                },
            )
    except Exception:
        pass


async def log_activity(event_type: str, message: str, metadata: dict | None = None):
    if not MC_API_KEY:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{MC_URL}/api/activities",
                headers={"Authorization": f"Bearer {MC_API_KEY}"},
                json={
                    "agent": "ai-dashboard-agent",
                    "type": event_type,
                    "message": message,
                    "metadata": metadata or {},
                },
            )
    except Exception:
        pass


async def report_tokens(prompt_tokens: int, completion_tokens: int, model: str = "llama3.1"):
    if not MC_API_KEY:
        return
    try:
        async with httpx.AsyncClient(timeout=5) as client:
            await client.post(
                f"{MC_URL}/api/tokens",
                headers={"Authorization": f"Bearer {MC_API_KEY}"},
                json={
                    "agent": "ai-dashboard-agent",
                    "model": model,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "total_tokens": prompt_tokens + completion_tokens,
                },
            )
    except Exception:
        pass

