from __future__ import annotations

import asyncio
import os
import shutil
from pathlib import Path

import pandas as pd
from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from chart_builder import build_charts
from dashboard_generator import generate_html
from file_processor import build_profile, cast_column_types, read_file
from mission_control_bridge import (
    complete_task,
    heartbeat_loop,
    log_activity,
    report_tokens,
    send_heartbeat,
)
from ollama_client import chat, check_ollama, generate_insights, generate_suggestions
from local_csv_chat import register_dataframe, chat_with_data

load_dotenv()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "../uploads")
os.makedirs(UPLOAD_DIR, exist_ok=True)

app = FastAPI(title="AI Dashboard Generator")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Session storage
_session = {
    "df": None,
    "profile": None,
    "charts": None,
    "dashboard_html": None,
}

FRONTEND_DIR = Path(__file__).resolve().parents[1] / "frontend"
app.mount("/frontend", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")


@app.on_event("startup")
async def startup_event():
    asyncio.create_task(heartbeat_loop())
    asyncio.create_task(
        log_activity(
            "agent_started",
            "AI Dashboard started on port 8011",
            {"model": os.getenv("OLLAMA_MODEL", "llama3.1"), "port": int(os.getenv("PORT", "8011"))},
        )
    )


@app.get("/", response_class=HTMLResponse)
async def index():
    index_path = FRONTEND_DIR / "index.html"
    if not index_path.exists():
        return HTMLResponse("<h3>Missing frontend/index.html</h3>", status_code=500)
    return HTMLResponse(index_path.read_text(encoding="utf-8"))


@app.post("/upload")
async def upload(file: UploadFile = File(...)):
    if not file.filename:
        return JSONResponse({"success": False, "error": "No file provided"}, status_code=400)

    ext = file.filename.split(".")[-1].lower()
    if ext not in {"csv", "xlsx", "xls"}:
        return JSONResponse({"success": False, "error": "Only CSV/Excel"}, status_code=400)

    safe_name = Path(file.filename).name
    filepath = os.path.join(UPLOAD_DIR, safe_name)

    with open(filepath, "wb") as f:
        shutil.copyfileobj(file.file, f)

    try:
        df = read_file(filepath)
        df = cast_column_types(df)
        
        # Register DataFrame for CSV chat module
        register_dataframe(df, file.filename)
        
        profile = build_profile(df, file.filename)
        charts = build_charts(df, profile)

        _session["df"] = df
        _session["profile"] = profile
        _session["charts"] = charts
        _session["dashboard_html"] = None

        asyncio.create_task(
            log_activity(
                "file_uploaded",
                f"File uploaded: {file.filename} ({profile.get('rows', 0)} rows)",
                {
                    "filename": file.filename,
                    "rows": profile.get("rows", 0),
                    "columns": list(profile.get("columns", [])),
                },
            )
        )

        return JSONResponse(
            {
                "success": True,
                "filename": file.filename,
                "rows": profile["rows"],
                "columns": profile["columns"],
                "kpis": profile["kpis"],
                "charts_count": len(charts),
            }
        )
    except Exception as e:
        return JSONResponse({"success": False, "error": str(e)}, status_code=500)


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard():
    if not _session.get("profile") or _session.get("df") is None:
        return HTMLResponse(
            "<script>window.location.href='/'</script><noscript><a href='/'>Go home</a></noscript>"
        )

    profile = _session["profile"]
    charts = _session.get("charts") or []
    df: pd.DataFrame = _session["df"]

    try:
        insights = await asyncio.wait_for(generate_insights(profile["context_text"]), timeout=15.0)
    except asyncio.TimeoutError:
        insights = ["Analysis complete. Ask questions in chat."]

    suggestions = await generate_suggestions(profile)

    html = generate_html(profile, charts, df, insights, suggestions)
    _session["dashboard_html"] = html
    return HTMLResponse(html)


class ChatRequest(BaseModel):
    message: str
    history: list = []


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    """Chat endpoint using local CSV data context with dynamic chart generation."""
    # Use new chat_with_data for accurate data-driven responses
    result = chat_with_data(req.message, req.history)
    
    # Log activity
    asyncio.create_task(
        log_activity(
            "chat_query",
            f"Chat query answered: {req.message[:60]}...",
            {
                "question": req.message,
                "data_used": result.get("data_used", False),
                "pre_computed": result.get("pre_computed", False),
                "chart_generated": result.get("chart") is not None,
            },
        )
    )
    
    # Report token usage
    asyncio.create_task(
        report_tokens(
            prompt_tokens=max(1, len(req.message) // 4),
            completion_tokens=max(1, len(result.get("answer", "")) // 4),
        )
    )
    
    return JSONResponse({
        "answer": result.get("answer", "Error"),
        "reply": result.get("answer", "Error"),  # For backwards compatibility
        "data_used": result.get("data_used", False),
        "error": result.get("error"),
        "chart": result.get("chart")  # Include chart config if generated
    })


@app.get("/api/health")
async def health():
    ollama_ok = await check_ollama()
    return JSONResponse(
        {
            "status": "ok",
            "ollama": ollama_ok,
            "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
            "file_loaded": _session["profile"] is not None,
            "filename": _session["profile"]["filename"] if _session["profile"] else None,
            "rows": _session["profile"]["rows"] if _session["profile"] else 0,
        }
    )


@app.get("/api/profile")
async def get_profile():
    if not _session.get("profile"):
        return JSONResponse({"error": "No file loaded"}, status_code=404)
    p = _session["profile"]
    return JSONResponse(
        {
            "success": True,
            "filename": p["filename"],
            "rows": p["rows"],
            "columns": p["columns"],
            "kpis": p["kpis"],
            "auto": p["auto"],
        }
    )


@app.post("/api/mc-task")
async def handle_mc_task(task: dict):
    task_id = task.get("id")
    task_type = task.get("type", "chat_query")
    payload = task.get("payload", {})
    await send_heartbeat("busy", f"Processing task: {task_type}")

    try:
        if task_type == "chat_query":
            if not _session.get("profile"):
                msg = "No file loaded. Please upload first."
                if task_id:
                    await complete_task(task_id, msg, "failed")
                return {"success": False, "error": msg}
            question = payload.get("question", "")
            reply = await chat(question, _session["profile"]["context_text"], [])
            if task_id:
                await complete_task(task_id, reply, "done")
            return {"success": True, "result": reply}

        if task_type == "generate_dashboard":
            if not _session.get("profile"):
                if task_id:
                    await complete_task(task_id, "No file loaded", "failed")
                return {"success": False, "error": "No file loaded"}
            dashboard_url = f"http://localhost:{os.getenv('PORT', '8011')}/dashboard"
            if task_id:
                await complete_task(task_id, f"Dashboard available at {dashboard_url}", "done")
            return {"success": True, "dashboard_url": dashboard_url}

        if task_type == "analyze_file":
            if not _session.get("profile"):
                if task_id:
                    await complete_task(task_id, "No file loaded", "failed")
                return {"success": False, "error": "No file loaded"}
            summary = _session["profile"].get("context_text", "No profile available")
            if task_id:
                await complete_task(task_id, summary, "done")
            return {"success": True, "profile": _session["profile"]}

        msg = f"Unknown task type: {task_type}"
        if task_id:
            await complete_task(task_id, msg, "failed")
        return {"success": False, "error": msg}
    finally:
        await send_heartbeat("active")


@app.get("/api/agent-status")
async def agent_status():
    p = _session.get("profile")
    return {
        "agent": os.getenv("MC_AGENT_NAME", "ai-dashboard-agent-v2"),
        "status": "active",
        "model": os.getenv("OLLAMA_MODEL", "llama3.1"),
        "endpoint": os.getenv("MC_AGENT_ENDPOINT", "http://localhost:8011"),
        "file_loaded": p is not None,
        "filename": p.get("filename") if p else None,
        "rows": p.get("rows", 0) if p else 0,
        "capabilities": [
            "file-analysis",
            "dashboard-generation",
            "natural-language-chat",
            "data-profiling",
        ],
    }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8011"))
    uvicorn.run(app, host="0.0.0.0", port=port)

