from __future__ import annotations

import asyncio
import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Dict, List

from dotenv import load_dotenv
from fastapi import FastAPI, File, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from pydantic import BaseModel, Field

from chat_agent import smart_chat_payload
from chart_builder import build_charts, build_kpis
from file_processor import build_profile, detect_types, read_file
from html_generator import generate_html
from ollama_client import check_ollama, generate_insights

load_dotenv()

app = FastAPI(title="AI Dashboard Generator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1")
os.makedirs(UPLOAD_DIR, exist_ok=True)

_session: Dict[str, Any] = {"datasets": {}, "active_file": None}


@app.get("/", response_class=HTMLResponse)
async def index() -> HTMLResponse:
    return HTMLResponse(
        """
<!DOCTYPE html>
<html><head><meta charset="UTF-8"/><meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>AI Dashboard Generator</title>
<style>
body{font-family:system-ui;background:#0f1117;color:#e2e8f0;display:flex;align-items:center;justify-content:center;height:100vh;margin:0}
.box{text-align:center;background:#1a1d2e;padding:32px;border-radius:14px;border:1px solid #2d3748;max-width:460px;width:92%}
h2{margin:0 0 8px 0}.muted{color:#64748b;font-size:13px;margin-bottom:18px}
input[type=file]{display:none}.btn{display:inline-block;padding:10px 18px;background:#4f46e5;border-radius:8px;cursor:pointer}
#status{margin-top:12px;color:#94a3b8;font-size:13px}.ok{color:#34d399}.bad{color:#f87171}.spin{display:inline-block;width:12px;height:12px;border:2px solid #64748b;border-top-color:transparent;border-radius:50%;animation:sp 0.8s linear infinite;margin-right:6px}
@keyframes sp{to{transform:rotate(360deg)}}
</style></head>
<body><div class="box">
<h2>AI Dashboard Generator</h2>
<div class="muted">Upload any CSV or Excel file</div>
<div id="ollama" class="muted">Checking Ollama status...</div>
<label class="btn">Choose Files<input id="fileInput" type="file" accept=".csv,.xlsx,.xls" multiple/></label>
<div id="status"></div>
</div>
<script>
async function health(){
  try{
    const r=await fetch('/api/health'); const d=await r.json();
    document.getElementById('ollama').innerHTML = d.ollama ? '<span class="ok">● Ollama ready</span>' : '<span class="bad">● Ollama offline</span>';
  }catch(e){ document.getElementById('ollama').innerHTML = '<span class="bad">● Ollama offline</span>'; }
}
document.getElementById('fileInput').addEventListener('change', async (e)=>{
  const files = Array.from(e.target.files || []);
  if(!files.length) return;
  const st=document.getElementById('status');
  st.innerHTML='<span class="spin"></span> Processing '+files.length+' file(s) ...';
  const fd=new FormData();
  files.forEach(f => fd.append('files', f));
  try{
    const r=await fetch('/upload',{method:'POST',body:fd}); const d=await r.json();
    if(d.success){
      const n = (d.uploaded || []).length;
      st.innerHTML='<span class="ok">Loaded '+n+' file(s). Redirecting...</span>';
      const target = (d.active_file || '');
      setTimeout(()=>location.href= target ? ('/dashboard?file='+encodeURIComponent(target)) : '/dashboard',800);
    }
    else { st.innerHTML='<span class="bad">Error: '+(d.error||'Upload failed')+'</span>'; }
  }catch(err){ st.innerHTML='<span class="bad">Error: '+err.message+'</span>'; }
});
health();
</script></body></html>
"""
    )


@app.post("/upload")
async def upload(files: List[UploadFile] = File(...)) -> JSONResponse:
    if not files:
        return JSONResponse({"success": False, "error": "No files provided."}, status_code=400)

    uploaded: List[Dict[str, Any]] = []
    errors: List[Dict[str, str]] = []
    last_ok_name: str | None = None

    for file in files:
        ext = Path(file.filename or "").suffix.lower()
        if ext not in {".csv", ".xlsx", ".xls"}:
            errors.append({"filename": file.filename or "unknown", "error": "Only CSV/XLSX/XLS files are supported."})
            continue

        path = os.path.join(UPLOAD_DIR, f"{uuid.uuid4().hex}{ext}")
        try:
            with open(path, "wb") as f:
                shutil.copyfileobj(file.file, f)
            df = read_file(path)
            df = detect_types(df)
            display_name = str(file.filename or f"uploaded_{uuid.uuid4().hex[:8]}{ext}")
            profile = build_profile(df, display_name)
            _session["datasets"][display_name] = {"df": df, "profile": profile}
            _session["active_file"] = display_name
            last_ok_name = display_name
            uploaded.append(
                {
                    "filename": display_name,
                    "rows": int(profile["rows"]),
                    "columns": [str(c) for c in profile["columns"]],
                }
            )
        except Exception as e:
            errors.append({"filename": file.filename or "unknown", "error": str(e)})

    if not uploaded:
        return JSONResponse({"success": False, "error": "All uploads failed.", "errors": errors}, status_code=400)

    return JSONResponse(
        {
            "success": True,
            "uploaded": uploaded,
            "errors": errors,
            "active_file": _session.get("active_file") or last_ok_name,
        }
    )


@app.get("/dashboard", response_class=HTMLResponse)
async def dashboard(file: str | None = None) -> HTMLResponse:
    datasets = _session.get("datasets") or {}
    if not datasets:
        return RedirectResponse(url="/")

    selected = file or _session.get("active_file")
    if selected not in datasets:
        selected = next(iter(datasets.keys()))
    _session["active_file"] = selected
    df = datasets[selected]["df"]
    profile = datasets[selected]["profile"]
    charts = build_charts(df, profile)
    kpis = build_kpis(df, profile)
    try:
        insights = await asyncio.wait_for(generate_insights(profile), timeout=10.0)
    except Exception:
        insights = ["Analysis complete. Ask questions below."]
    html = generate_html(profile, charts, kpis, insights)
    return HTMLResponse(html)


class ChatRequest(BaseModel):
    message: str
    history: List[Dict[str, str]] = Field(default_factory=list)
    active_file: str | None = None


@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest) -> JSONResponse:
    datasets = _session.get("datasets") or {}
    if not datasets:
        return JSONResponse({"reply": "No file loaded."})

    selected = req.active_file or _session.get("active_file")
    if selected not in datasets:
        selected = next(iter(datasets.keys()))
    _session["active_file"] = selected
    df = datasets[selected]["df"]
    profile = datasets[selected]["profile"]
    payload = await smart_chat_payload(req.message, profile, df, req.history)
    return JSONResponse(payload)


@app.get("/api/health")
async def health() -> JSONResponse:
    datasets = _session.get("datasets") or {}
    active_file = _session.get("active_file")
    active = active_file in datasets
    rows = int((datasets.get(active_file, {}).get("profile") or {}).get("rows", 0)) if active else 0
    return JSONResponse(
        {
            "ollama": await check_ollama(),
            "model": OLLAMA_MODEL,
            "session": "active" if active else "empty",
            "rows": rows,
            "active_file": active_file if active else None,
            "dataset_count": len(datasets),
        }
    )


@app.delete("/api/session")
async def clear_session() -> JSONResponse:
    _session["datasets"] = {}
    _session["active_file"] = None
    return JSONResponse({"cleared": True})
