"""
main.py
-------
FastAPI application for the CSV Chat Agent.

Routes:
  POST /api/upload              → upload one or more CSV files
  POST /api/chat                → send message, get AgentResponse
  GET  /api/files               → list uploaded files + metadata
  GET  /api/files/{name}/schema → column metadata for a file
  POST /api/files/{name}/filter → filter + sort rows
  POST /api/files/{name}/aggregate → aggregate data for a chart
  DELETE /api/files/{name}      → remove a file
  GET  /api/health              → Ollama + file store status

Run:
  pip install fastapi uvicorn pandas numpy httpx pydantic python-multipart
  uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""

import logging
import asyncio
from contextlib import asynccontextmanager
from typing import Annotated

from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import json
import pandas as pd

from ollama_manager import ollama, ModelRole
from csv_processor import (
    parse_csv, get_file, list_files, remove_file, clear_all,
    build_context, aggregate, time_series, apply_filters, _safe_json, format_kpi_metrics,
    auto_dashboard_config, detect_quarter_from_filename, get_category_values,
    ai_select_charts, prepare_chart_data
)
from profiler import profile_dataframe, profile_to_prompt_context
from agent import agent, AgentResponse, generate_ceo_summary

logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(name)s  %(message)s")
logger = logging.getLogger(__name__)


# ── Lifespan ──────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("CSV Chat Agent starting up...")
    health = await ollama.health_check()
    logger.info(f"Ollama status: {health}")
    yield
    logger.info("Shutting down...")


app = FastAPI(
    title="CSV Chat Agent API",
    version="1.0.0",
    description="Local AI chat agent for CSV analysis powered by Ollama",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:5174", "http://localhost:3000", "http://127.0.0.1:5173", "http://127.0.0.1:5174"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Exception handlers to ensure CORS headers on errors ──────────────────────

from fastapi import Request
from fastapi.responses import JSONResponse

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Credentials": "true",
        }
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    logger.exception(f"Unhandled exception: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
        headers={
            "Access-Control-Allow-Origin": "http://localhost:5173",
            "Access-Control-Allow-Credentials": "true",
        }
    )


# ── Request / Response schemas ────────────────────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    active_file: str = ""
    all_files: list[str] = []
    conversation_history: list[dict] = []
    conversation_id: str = ""
    session_id: str = ""
    active_quarter: str = "All"
    active_category: str = "All"
    stream: bool = False


class StreamChunk(BaseModel):
    status: str
    token: str | None = None
    chart: dict | None = None
    table: dict | None = None
    message: str | None = None
    step: int | None = None


class ChatResponse(BaseModel):
    intent: str
    answer: str
    chart_config: dict | None = None
    table_data: list[dict] = []
    table_columns: list[str] = []
    active_file: str = ""
    error: str | None = None


class FilterRequest(BaseModel):
    filters: dict = Field(default_factory=dict)
    sort_col: str | None = None
    sort_asc: bool = True
    limit: int = Field(default=200, le=2000)


class AggregateRequest(BaseModel):
    group_col: str
    value_col: str
    agg_func: str = "sum"
    top_n: int = Field(default=15, le=50)


class TimeSeriesRequest(BaseModel):
    date_col: str
    value_col: str
    freq: str = "M"      # M=monthly, Q=quarterly, Y=yearly
    agg_func: str = "sum"


# ── Upload ────────────────────────────────────────────────────────────────────

@app.post("/api/upload")
async def upload_files(files: list[UploadFile] = File(...)):
    """
    Upload one or more data files (CSV, XLSX, XLS).
    Returns schema and stats for each file.
    """
    results = []
    errors = []

    for f in files:
        # Check file extension (case-insensitive)
        if not f.filename.lower().endswith((".csv", ".xlsx", ".xls")):
            errors.append(f"{f.filename}: only .csv, .xlsx, and .xls files are supported")
            continue

        content = await f.read()
        if len(content) > 50 * 1024 * 1024:  # 50MB limit
            errors.append(f"{f.filename}: file too large (max 50MB)")
            continue

        try:
            csv_file = parse_csv(f.filename, content)
            
            # Profile the DataFrame to auto-detect everything
            profile = profile_dataframe(csv_file.df, filename=f.filename)
            auto = profile.get("auto_detected", {})
            
            results.append({
                "name": csv_file.name,
                "rows": csv_file.row_count,
                "columns": len(csv_file.columns),
                "numeric_cols": csv_file.numeric_cols,
                "categorical_cols": csv_file.categorical_cols,
                "datetime_cols": csv_file.datetime_cols,
                "schema": [
                    {
                        "name": c.name,
                        "dtype": c.dtype,
                        "nulls": c.nulls,
                        "unique": c.unique_count,
                        "min": c.min_val,
                        "max": c.max_val,
                        "mean": c.mean_val,
                        "top_values": c.top_values,
                    }
                    for c in csv_file.columns
                ],
                # Send auto-detected info to frontend
                "profile": profile_to_prompt_context(profile),
                "auto_detected": auto,
            })
        except Exception as e:
            logger.exception(f"Parse error: {f.filename}")
            errors.append(f"{f.filename}: {str(e)}")

    if not results and errors:
        raise HTTPException(status_code=400, detail="; ".join(errors))

    return {"uploaded": results, "errors": errors}


# ── Chat ──────────────────────────────────────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(req: ChatRequest):
    """
    Main chat endpoint. Routes message through intent classifier → LLM → response.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Message cannot be empty.")

    # Ensure file list is populated
    all_files = req.all_files or list_files()

    try:
        result = await agent.run(
            message=req.message,
            active_file=req.active_file,
            all_files=all_files,
            conversation_history=req.conversation_history,
            session_id=req.session_id,
            active_quarter=req.active_quarter,
            active_category=req.active_category,
        )
        return ChatResponse(
            intent=result.intent,
            answer=result.answer,
            chart_config=result.chart_config,
            table_data=result.table_data,
            table_columns=result.table_columns,
            active_file=result.active_file,
            error=result.error,
        )
    except Exception as e:
        logger.exception("Agent error")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/chat/stream")
async def chat_stream(req: ChatRequest):
    """
    **Streaming chat with token-by-token response + chart pinning.**
    
    Returns Server-Sent Events with:
    - status: classifying | loading | generating | token | chart | done | error
    - token: text chunk (for streaming)
    - chart: ECharts-compatible config (for chart responses)
    - message: status message
    """
    all_files = req.all_files or list_files()

    async def event_gen():
        try:
            filename = req.active_file if req.active_file in all_files else (all_files[0] if all_files else "")
            if not filename:
                yield f"data: {json.dumps({'status': 'error', 'message': 'No dataset selected'})}\n\n"
                return

            # Detect relevant file if multiple files exist
            if len(all_files) > 1:
                yield f"data: {json.dumps({'status': 'classifying', 'message': 'Detecting relevant file...'})}\n\n"
                filename = await agent._detect_relevant_file(req.message, all_files)

            # Classify intent
            yield f"data: {json.dumps({'status': 'classifying', 'message': 'Analyzing your question...'})}\n\n"
            intent = await agent._classify(req.message)
            
            # Load model
            yield f"data: {json.dumps({'status': 'loading', 'message': f'Processing {intent.lower()} request...'})}\n\n"
            
            # Generate response based on intent
            yield f"data: {json.dumps({'status': 'generating', 'message': 'Generating response...'})}\n\n"
            
            if intent == "CHART":
                result = await agent._handle_chart(req.message, filename, all_files, req.conversation_history)
                
                # Send chart data
                if result.chart_config:
                    chart_data = {
                        **result.chart_config,
                        'title': result.chart_config.get('title', ''),
                        'xKey': result.chart_config.get('xKey', ''),
                        'yKey': result.chart_config.get('yKey', ''),
                        'aggregation': result.chart_config.get('aggregation', 'sum'),
                        'chartType': result.chart_config.get('chartType', result.chart_config.get('type', 'bar')),
                    }
                    yield f"data: {json.dumps({'status': 'chart', 'chart': _safe_json(chart_data)})}\n\n"
                
                answer = result.answer
            elif intent == "TABLE":
                result = await agent._handle_table(req.message, filename, all_files, req.conversation_history)
                answer = result.answer
            elif intent == "STATS":
                result = await agent._handle_stats(req.message, filename, all_files, req.conversation_history)
                answer = result.answer
            elif intent == "DASHBOARD":
                result = await agent._handle_dashboard(req.message, filename, all_files, req.conversation_history)
                if result.dashboard_config:
                    for chart in result.dashboard_config.get("charts", []):
                        yield f"data: {json.dumps({'status': 'chart', 'chart': _safe_json(chart)})}\n\n"
                answer = result.answer
            else:
                result = await agent._handle_chat(req.message, filename, all_files, req.conversation_history)
                answer = result.answer
            
            # Stream the answer token by token
            # Split into reasonable chunks (words/sentences)
            import re
            tokens = re.findall(r'\S+\s*|\s+', answer)
            
            for token in tokens:
                if token.strip():  # Skip whitespace-only tokens
                    yield f"data: {json.dumps({'status': 'token', 'token': token})}\n\n"
                    await asyncio.sleep(0.02)  # Slight delay for better visual effect
            
            yield f"data: {json.dumps({'status': 'done'})}\n\n"
            
        except Exception as e:
            logger.exception("Stream error")
            yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(event_gen(), media_type="text/event-stream")


# ── File management ───────────────────────────────────────────────────────────

@app.get("/api/files")
async def get_files():
    """List all currently loaded CSV files with basic metadata."""
    files = []
    for name in list_files():
        f = get_file(name)
        if f:
            files.append({
                "name": f.name,
                "rows": f.row_count,
                "columns": len(f.columns),
                "numeric_cols": f.numeric_cols,
                "categorical_cols": f.categorical_cols,
            })
    return {"files": files}


@app.get("/api/files/{name}/schema")
async def get_schema(name: str):
    """Detailed column schema for a specific file."""
    f = get_file(name)
    if not f:
        raise HTTPException(status_code=404, detail=f"File '{name}' not found.")
    return {
        "name": f.name,
        "rows": f.row_count,
        "schema": [
            {
                "name": c.name, "dtype": c.dtype, "nulls": c.nulls,
                "unique": c.unique_count, "min": c.min_val, "max": c.max_val,
                "mean": c.mean_val, "sum": c.sum_val, "top_values": c.top_values,
            }
            for c in f.columns
        ],
    }


@app.post("/api/files/{name}/filter")
async def filter_rows(name: str, req: FilterRequest):
    """Apply filters + sort to a CSV file and return paginated rows."""
    f = get_file(name)
    if not f:
        raise HTTPException(status_code=404, detail=f"File '{name}' not found.")

    rows, total = apply_filters(
        name,
        filters=req.filters,
        sort_col=req.sort_col,
        sort_asc=req.sort_asc,
        limit=req.limit,
    )
    return {"rows": rows, "total": total, "returned": len(rows)}


@app.post("/api/files/{name}/aggregate")
async def aggregate_data(name: str, req: AggregateRequest):
    """Aggregate a numeric column by a categorical column."""
    f = get_file(name)
    if not f:
        raise HTTPException(status_code=404, detail=f"File '{name}' not found.")

    data = aggregate(name, req.group_col, req.value_col, req.agg_func, req.top_n)
    return {"data": data, "x_key": req.group_col, "y_key": req.value_col}


@app.post("/api/files/{name}/timeseries")
async def get_timeseries(name: str, req: TimeSeriesRequest):
    """Resample a numeric column over a datetime column."""
    f = get_file(name)
    if not f:
        raise HTTPException(status_code=404, detail=f"File '{name}' not found.")

    data = time_series(name, req.date_col, req.value_col, req.freq, req.agg_func)
    return {"data": data, "x_key": req.date_col, "y_key": req.value_col}


@app.delete("/api/files/{name}")
async def delete_file(name: str):
    """Remove a file from the in-memory store."""
    if not get_file(name):
        raise HTTPException(status_code=404, detail=f"File '{name}' not found.")
    remove_file(name)
    return {"deleted": name, "remaining": list_files()}


@app.delete("/api/files")
async def clear_files():
    """Remove all loaded files."""
    clear_all()
    return {"cleared": True}


# ── Dashboard presets ─────────────────────────────────────────────────────────

@app.get("/api/dashboard/presets")
async def dashboard_presets():
    """
    Returns suggested quick-start questions based on currently loaded files.
    If no files are loaded, returns generic suggestions.
    """
    files = list_files()
    if not files:
        return {"presets": [
            "Upload a CSV file to get started",
        ]}

    f = get_file(files[0])
    presets = []

    if f.numeric_cols:
        n = f.numeric_cols[0]
        presets.append({"label": f"Stats for {n}", "question": f"Give me summary statistics for {n}"})

    if f.categorical_cols and f.numeric_cols:
        c, n = f.categorical_cols[0], f.numeric_cols[0]
        presets.append({"label": f"Top {c} by {n}", "question": f"Show top 10 {c} by {n} as a bar chart"})
        presets.append({"label": f"{n} by {c} (pie)", "question": f"Show {n} breakdown by {c} as a pie chart"})

    if len(f.numeric_cols) >= 2:
        n1, n2 = f.numeric_cols[0], f.numeric_cols[1]
        presets.append({"label": f"{n1} vs {n2}", "question": f"Is there a correlation between {n1} and {n2}?"})

    if f.datetime_cols and f.numeric_cols:
        d, n = f.datetime_cols[0], f.numeric_cols[0]
        presets.append({"label": f"{n} trend", "question": f"Show monthly trend of {n} over {d} as a line chart"})

    presets.append({"label": "Any outliers?", "question": "Are there any outliers or anomalies in this data?"})

    return {"presets": presets, "active_file": files[0]}


# ── KPI Metrics ───────────────────────────────────────────────────────────────

@app.post("/api/kpi-metrics")
async def calculate_kpis(filename: str, filters: dict = None):
    """
    Calculate KPI metrics (sum, avg, count, etc.) for numeric columns.
    Optionally filters data before calculation.
    Returns formatted KPI card data.
    """
    f = get_file(filename)
    if not f:
        raise HTTPException(status_code=404, detail=f"File '{filename}' not found")

    df = f.df.copy()

    # Apply filters if provided
    if filters:
        for col, values in filters.items():
            if isinstance(values, list):
                df = df[df[col].isin(values)]
            else:
                df = df[df[col] == values]

    # Calculate metrics for each numeric column
    kpi_cards = []
    for col in f.numeric_cols:
        if col in df.columns:
            numeric_data = pd.to_numeric(df[col], errors='coerce').dropna()
            if len(numeric_data) > 0:
                raw_metrics = {
                    "sum": float(numeric_data.sum()),
                    "avg": float(numeric_data.mean()),
                    "min": float(numeric_data.min()),
                    "max": float(numeric_data.max()),
                    "count": int(len(numeric_data)),
                    "median": float(numeric_data.median()),
                }
                # Format as KPI card
                card = format_kpi_metrics(col, raw_metrics)
                kpi_cards.append(card)

    # Return KPI data structure
    return {
        "filename": filename,
        "row_count": len(df),
        "kpi_cards": kpi_cards,
        "filters_applied": filters or {},
    }



class AutoDashboardRequest(BaseModel):
    # New multi-file API: pass filenames list + quarter + category
    filenames: list[str] = Field(default_factory=list)
    quarter: str = "All"
    category: str = "All"
    # Legacy single-file support
    filename: str = ""
    filters: dict = Field(default_factory=dict)

@app.post("/api/auto-dashboard")
async def generate_auto_dashboard(req: AutoDashboardRequest):
    """
    Auto-detects columns and generates KPI cards and Chart configs.
    Supports multi-file merging across quarters.
    """
    try:
        logger.info(f"Dashboard request: filenames={req.filenames}, quarter={req.quarter}, category={req.category}")
        
        # Resolve filenames list (support legacy single filename)
        filenames = req.filenames
        if not filenames and req.filename:
            filenames = [req.filename]
        if not filenames:
            filenames = list_files()
        if not filenames:
            raise HTTPException(status_code=400, detail="No files uploaded yet.")
        
        logger.info(f"Resolved filenames: {filenames}")

        # Build combined DataFrame
        quarter = req.quarter or "All"
        category = req.category or "All"

        if quarter == "All":
            dfs = []
            for fname in filenames:
                f = get_file(fname)
                if not f:
                    continue
                d = f.df.copy()
                d["_quarter"] = detect_quarter_from_filename(fname) or "Unknown"
                dfs.append(d)
            if not dfs:
                raise HTTPException(status_code=404, detail="None of the requested files found.")
            combined_df = pd.concat(dfs, ignore_index=True)
        else:
            # Find the file matching the requested quarter
            quarter_file = next(
                (fn for fn in filenames if detect_quarter_from_filename(fn) == quarter),
                None
            )
            if not quarter_file:
                # Fallback: just use first available file
                quarter_file = filenames[0] if filenames else None
            if not quarter_file:
                raise HTTPException(status_code=404, detail=f"No file uploaded for {quarter}.")
            f = get_file(quarter_file)
            if not f:
                raise HTTPException(status_code=404, detail=f"File '{quarter_file}' not found.")
            combined_df = f.df.copy()

        # Generate dashboard config from combined DataFrame
        config = auto_dashboard_config(
            combined_df,
            filters=req.filters or {},
            quarter=quarter,
            category=category if category != "All" else None,
        )

        # Attach CEO summary (async AI generation)
        try:
            ceo_summary = await generate_ceo_summary(
                top_company=config.get("top_company", ""),
                top_amount=config.get("top_amount", ""),
                total_revenue=config.get("total_revenue", ""),
                invoice_count=config.get("invoice_count", 0),
                quarter=quarter,
                filename=", ".join(filenames),
            )
            config["ceo_summary"] = ceo_summary
        except Exception as ceo_err:
            logger.warning(f"CEO summary failed: {ceo_err}")
            config["ceo_summary"] = ""

        return config
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate auto dashboard")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/generate-all-charts")
async def generate_all_charts(request: AutoDashboardRequest):
    """
    Generate ALL relevant chart types for uploaded CSV using AI logic.
    Returns up to 12 charts with full data ready for ECharts rendering.
    """
    try:
        # Resolve filenames
        filenames = request.filenames
        if not filenames and request.filename:
            filenames = [request.filename]
        if not filenames:
            filenames = list_files()
        if not filenames:
            raise HTTPException(status_code=400, detail="No files uploaded yet.")

        quarter = request.quarter or "All"
        category = request.category or "All"

        # Load DataFrame
        if quarter == "All":
            dfs = []
            for fname in filenames:
                f = get_file(fname)
                if not f:
                    continue
                dfs.append(f.df.copy())
            if not dfs:
                raise HTTPException(status_code=404, detail="No files found.")
            combined_df = pd.concat(dfs, ignore_index=True)
        else:
            quarter_file = next(
                (fn for fn in filenames if detect_quarter_from_filename(fn) == quarter),
                filenames[0] if filenames else None
            )
            if not quarter_file:
                raise HTTPException(status_code=404, detail=f"No file for {quarter}.")
            f = get_file(quarter_file)
            if not f:
                raise HTTPException(status_code=404, detail=f"File '{quarter_file}' not found.")
            combined_df = f.df.copy()

        # Apply category filter
        if category and category != "All":
            party_col = next((c for c in combined_df.columns 
                             if 'party' in c.lower() or 'category' in c.lower()), None)
            if party_col and party_col in combined_df.columns:
                combined_df = combined_df[combined_df[party_col].astype(str) == str(category)]

        # AI auto-select charts
        chart_configs = ai_select_charts(combined_df, filenames[0], quarter, category)
        
        # Add comparison charts if viewing "All" quarters
        if quarter == "All" and len(filenames) > 1:
            dfs_to_compare = []
            for fn in filenames:
                f = get_file(fn)
                if f: dfs_to_compare.append(f.df)
            
            comp_configs = get_comparison_charts(dfs_to_compare, filenames)
            # Insert at beginning for visibility
            chart_configs = comp_configs + chart_configs

        # Prepare data for each chart
        charts_with_data = []
        for config in chart_configs:
            try:
                # For comparison charts, use combined_df but with special handling if needed
                data = prepare_chart_data(combined_df, config)
                charts_with_data.append({
                    **config,
                    'data': data
                })
            except Exception as e:
                logger.warning(f"Chart prep error for {config.get('chartType', 'unknown')}: {e}")
                continue

        return {
            'filename': ",".join(filenames),
            'quarter': quarter,
            'category': category,
            'total_charts': len(charts_with_data),
            'charts': charts_with_data
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("Failed to generate charts")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/quarter-status")
async def quarter_status():
    """
    Returns which label (Q1–Q12, FY25…) maps to which filename.
    Only labels that have a file are included; the frontend receives
    the full set so it can render the correct tabs.
    Example: { "Q1": "q1.csv", "Q3": "q3.csv" }
    """
    status: dict[str, str | None] = {}
    for fname in list_files():
        q = detect_quarter_from_filename(fname)
        if q and q not in status:
            status[q] = fname
    return status

# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health")
async def health():
    ollama_status = await ollama.health_check()
    return {
        "api": "ok",
        "ollama": ollama_status,
        "files_loaded": len(list_files()),
        "files": list_files(),
    }


@app.post("/api/preload")
async def preload_models():
    """
    Preload the fastest models (mistral:7b) to keep them warm.
    Call this on app startup to reduce first-response latency.
    """
    try:
        logger.info("Preloading fastest model (mistral:7b)...")
        # Send a minimal prompt to load the model
        response = await ollama.generate(ModelRole.INTENT, "ok", schema_context="")
        logger.info(f"Model preloaded: {response[:50]}...")
        return {"status": "preloaded", "message": "Models loaded and ready"}
    except Exception as e:
        logger.error(f"Preload failed: {e}")
        return {"status": "error", "message": str(e)}


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
