"""
agent.py
--------
The CSV Chat Agent. Orchestrates:
  1. Intent classification  (mistral:7b — fast, one-word reply)
  2. Context injection      (schema + stats + sample rows from csv_processor)
  3. LLM routing            (llama3.1:8b for chat, qwen2.5:7b for data)
  4. Chart config parsing   (extracts JSON from qwen response)
  5. Response assembly      (AgentResponse dataclass → FastAPI → React)
"""

import re
import json
import logging
from dataclasses import dataclass, field
import collections

from ollama_manager import OllamaManager, ModelRole, ollama
from csv_processor import (
    build_context, build_multi_context, build_multi_file_context, list_files, get_file,
    aggregate, time_series, apply_filters, ColumnMeta, auto_dashboard_config,
    format_inr, detect_quarter_from_filename, get_category_values
)
from profiler import profile_dataframe, profile_to_prompt_context

logger = logging.getLogger(__name__)

# ── Conversation memory (keyed by session_id) ────────────────────────────────
# Stores last 20 turns per session so chat has context across messages.
conversation_memory: dict[str, list[dict]] = collections.defaultdict(list)

MAX_MEMORY_TURNS = 20


# ── Response model ────────────────────────────────────────────────────────────

@dataclass
class AgentResponse:
    intent: str                               # CHAT | CHART | TABLE | STATS
    answer: str                               # Natural language reply
    chart_config: dict | None = None          # Recharts-compatible config
    dashboard_config: dict | None = None      # Auto dashboard config
    table_data: list[dict] = field(default_factory=list)
    table_columns: list[str] = field(default_factory=list)
    active_file: str = ""
    error: str | None = None


# ── CEO Summary Generator ─────────────────────────────────────────────────────

async def generate_ceo_summary(
    top_company: str,
    top_amount: str,
    total_revenue: str,
    invoice_count: int,
    quarter: str,
    filename: str,
) -> str:
    """
    Use llama3.1:8b to generate a 2-sentence CEO-level business insight.
    Returns empty string on failure so it never blocks the dashboard.
    """
    if not top_company:
        return ""
    prompt = (
        f"You are a business analyst presenting to a CEO.\n"
        f"Data file: {filename}\n"
        f"Period: {quarter or 'Full Year'}\n"
        f"Top company by revenue: {top_company} with {top_amount}\n"
        f"Total revenue across all companies: {total_revenue}\n"
        f"Total invoices processed: {invoice_count}\n\n"
        f"Write exactly 2 sentences of KEY BUSINESS INSIGHT the CEO must know. "
        f"Be specific with numbers. Use ₹ and Cr/L formatting. No bullet points."
    )
    try:
        response = await ollama.generate(ModelRole.SUMMARY, prompt, schema_context="")
        return response.strip()
    except Exception as e:
        logger.warning(f"CEO summary generation failed: {e}")
        return ""


# ── Chart config helpers ──────────────────────────────────────────────────────

CHART_KEYWORDS = {
    "line":      ["trend", "over time", "monthly", "yearly", "quarterly", "time series"],
    "pie":       ["share", "percent", "proportion", "breakdown", "distribution"],
    "scatter":   ["correlation", "vs", "versus", "scatter", "relationship"],
    "histogram": ["histogram", "frequency", "distribution of"],
    "bar":       [],   # default
}

COLORS = ["#4f46e5","#06b6d4","#f59e0b","#10b981","#f43f5e","#8b5cf6","#fb923c"]

def _infer_chart_type(question: str) -> str:
    q = question.lower()
    for ctype, keywords in CHART_KEYWORDS.items():
        if any(kw in q for kw in keywords):
            return ctype
    return "bar"

def _extract_json_from_text(text: str) -> dict | None:
    """Pull first JSON object out of a model response."""
    match = re.search(r"\{[^{}]+\}", text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None

def _build_chart_config(
    data: list[dict],
    x_key: str,
    y_key: str,
    chart_type: str,
    title: str,
) -> dict:
    series = [{"dataKey": y_key, "name": y_key.replace("_", " ").title(), "color": COLORS[0]}]
    return {
        "type": chart_type,
        "data": data,
        "xKey": x_key,
        "yKey": y_key,
        "series": series,
        "title": title[:80],
    }


# ── Main Agent ────────────────────────────────────────────────────────────────

class CSVChatAgent:
    def __init__(self, llm: OllamaManager):
        self.llm = llm

    async def parse_llm_json(self, raw: str, retries: int = 2) -> dict:
        """Parse JSON from LLM response with retry logic."""
        for attempt in range(retries + 1):
            try:
                # Strip markdown fences if present
                clean = re.sub(r"```(?:json)?|```", "", raw).strip()
                return json.loads(clean)
            except json.JSONDecodeError:
                if attempt < retries:
                    # Ask the model to fix its own output
                    fix_prompt = f"This is not valid JSON: {raw}\nReturn ONLY the corrected JSON object, no explanation."
                    raw = await self.llm.generate(ModelRole.CHART, fix_prompt, temp=0.1)
                else:
                    raise ValueError(f"Could not parse LLM JSON after {retries} retries: {raw}")

    async def run(
        self,
        message: str,
        active_file: str,
        all_files: list[str],
        conversation_history: list[dict],
        session_id: str = "",
        active_quarter: str = "All",
        active_category: str = "All",
    ) -> AgentResponse:

        files = all_files or list_files()
        if not files:
            return AgentResponse(
                intent="CHAT",
                answer="Please upload a CSV file first so I can analyse your data.",
            )

        # Use active file, fallback to first
        filename = active_file if active_file in files else files[0]
        
        # ── Step 0: Detect relevant file if multiple files exist ──
        if len(files) > 1:
            filename = await self._detect_relevant_file(message, files)
            logger.info(f"Detected relevant file: {filename}")

        # ── Step 1: Intent classification (fast, mistral:7b) ──
        intent = await self._classify(message)
        logger.info(f"Intent: {intent} | File: {filename}")

        # ── Step 2: Route ──
        if intent == "CHART":
            return await self._handle_chart(message, filename, files, conversation_history)
        elif intent == "TABLE":
            return await self._handle_table(message, filename, files, conversation_history)
        elif intent == "STATS":
            return await self._handle_stats(message, filename, files, conversation_history)
        elif intent == "DASHBOARD":
            return await self._handle_dashboard(message, filename, files, conversation_history)
        else:
            return await self._handle_chat(
                message, filename, files, conversation_history,
                session_id=session_id,
                active_quarter=active_quarter,
                active_category=active_category,
            )

    # ── File detection ────────────────────────────────────────────────────────

    async def _detect_relevant_file(self, message: str, files: list[str]) -> str:
        """
        Detect which file is most relevant to the user's question.
        Uses mistral:7b with temp=0 for deterministic results.
        """
        if len(files) <= 1:
            return files[0] if files else ""
        
        file_list = ", ".join(files)
        detection_prompt = (
            f"Given these uploaded files:\n{file_list}\n"
            f"User asked: '{message}'\n"
            f"Which filename is most relevant? Reply with ONLY the filename or ALL."
        )
        
        raw = await self.llm.generate(ModelRole.INTENT, detection_prompt)
        answer = raw.strip()
        
        # Check if refers to a specific file
        for fname in files:
            if fname.lower() in answer.lower():
                return fname
        
        # If "ALL" or multiple files mentioned, return the active/first one
        return files[0]

    # ── Intent ────────────────────────────────────────────────────────────────

    async def _classify(self, message: str) -> str:
        """
        Classify user intent into one of four categories:
        - CHAT: List, summary, and descriptive queries (who, what filters apply)
        - CHART: Analysis, trends, patterns, distributions, comparisons
        - TABLE: Raw data viewing (show me data, display records)
        - STATS: Statistics, aggregations, metrics, summaries
        """
        m = message.lower()
        
        # ── Fast keyword-based rules (high confidence) ──
        # Check STATS first (most specific)
        stats_keywords = ["total ", "average ", "statistics", "how much", "how many", " sum ", 
                         " count ", "aggregate", "metrics", "median ", "maximum ", "minimum ",
                         "standard deviation", "variance"]
        
        chart_keywords = ["trend", "pattern", "distribution", "compare", "correlation", 
                         "dashboard", "analysis", "visualize", "graph", "chart", "plot"]
        
        table_keywords = ["show data", "display records", "show table", "raw data", "view records",
                         "show me the data", "display all"]
                         
        dashboard_keywords = ["generate dashboard", "show dashboard", "create dashboard", "analyze this file", "full dashboard"]
        
        # Priority order: DASHBOARD > STATS > CHART > TABLE > CHAT (fallback)
        if any(kw in m for kw in dashboard_keywords):
            return "DASHBOARD"
        if any(kw in m for kw in stats_keywords):
            return "STATS"
        if any(kw in m for kw in chart_keywords):
            return "CHART"
        if any(kw in m for kw in table_keywords):
            return "TABLE"
        
        # ── Fallback: Ask LLM for classification ──
        classification_prompt = f"""Classify this request into ONE word ONLY:
        
Request: {message}

Classification rules:
- CHAT: "list of", "which", "who", "filter by", "explain", "describe", "tell me about" (text explanation)
- CHART: "trend", "analyze", "distribution", "compare", "visualization", "graph", "plot" (needs chart)
- TABLE: "show me data", "display records", "raw data", "view table" (tabular format)
- STATS: "total", "average", "sum", "count", "statistics", "how much", "how many" (numerical metrics)
- DASHBOARD: "generate dashboard", "show dashboard", "create dashboard", "analyze this file" (full dashboard)

Respond ONLY with: CHAT or CHART or TABLE or STATS or DASHBOARD"""
        
        raw = await self.llm.generate(ModelRole.INTENT, classification_prompt)
        word = raw.strip().upper().split()[0] if raw.strip() else "CHAT"
        return word if word in ("CHAT", "CHART", "TABLE", "STATS", "DASHBOARD") else "CHAT"

    # ── Chat handler ──────────────────────────────────────────────────────────

    async def _handle_chat(
        self,
        message: str,
        filename: str,
        all_files: list[str],
        history: list[dict],
        session_id: str = "",
        active_quarter: str = "All",
        active_category: str = "All",
    ) -> AgentResponse:
        ctx = build_multi_file_context(all_files, active_file=filename)

        # ── Build data-context summary using profiler ──
        f_obj = get_file(filename)
        if f_obj and hasattr(f_obj, 'df'):
            try:
                # Profile the DataFrame to auto-detect everything
                profile = profile_dataframe(f_obj.df, filename=filename)
                profile_context = profile_to_prompt_context(profile)
                
                system_ctx = (
                    f"You are an expert data analyst assistant.\n\n"
                    f"A file has been uploaded. Here is everything automatically detected about it:\n\n"
                    f"{profile_context}\n\n"
                    f"Your rules:\n"
                    f"1. NEVER mention Q1, Q2, Q3, Q4 unless those exact words appear as column values in the data itself.\n"
                    f"2. NEVER assume time periods — read them from the date column ranges above.\n"
                    f"3. NEVER assume column names — use only the exact column names listed above.\n"
                    f"4. When you see a date column, group by whatever granularity makes sense:\n"
                    f"   - Data spanning < 3 months → group by week or day\n"
                    f"   - Data spanning 3–12 months → group by month\n"
                    f"   - Data spanning > 12 months → group by quarter or year\n"
                    f"5. For revenue/amount questions, always state the total and top contributors.\n"
                    f"6. For client questions, always rank by the detected revenue column.\n"
                    f"7. If asked to generate a chart, pick axes from the actual column names above.\n"
                    f"8. Respond in plain business language. Use ₹ and Cr/Lakh for Indian amounts.\n"
                    f"9. If a question cannot be answered from this data, say exactly why (which column is missing).\n"
                )
            except Exception as e:
                logger.warning(f"Profile generation failed: {e}, using fallback context")
                system_ctx = "You are a concise, highly capable business data analyst AI."
        else:
            system_ctx = "You are a concise, highly capable business data analyst AI."

        # ── Pull conversation memory ──
        mem_turns = ""
        if session_id and conversation_memory[session_id]:
            last_n = conversation_memory[session_id][-10:]
            mem_turns = "\n".join(
                f"{m['role'].upper()}: {m['content']}"
                for m in last_n
            )

        # ── Build prompt ──
        history_turns = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history[-6:]
        )
        if mem_turns and not history_turns:
            history_turns = mem_turns

        wants_systematic = any(
            kw in message.lower()
            for kw in ["systematic", "format", "structure", "organized", "proper", "neat"]
        )

        if any(kw in message.lower() for kw in ["list", "which", "who", "show", "get", "find", "filter", "where"]):
            prompt = (
                f"{history_turns}\nUSER: {message}" if history_turns else message
            ) + (
                "\n\nDO NOT include any SQL, code, or technical queries."
            )
        else:
            prompt = f"{history_turns}\nUSER: {message}" if history_turns else message

        if wants_systematic:
            prompt += (
                "\n\nIMPORTANT: Format your response SYSTEMATICALLY with:\n"
                "- Clear numbered sections\n- **Bold headers**\n"
                "- Bullet points for lists\n- Markdown formatting\n- NO SQL or code"
            )
        elif "sql" not in prompt.lower():
            prompt += "\n\nNOTE: Only provide natural language descriptions, no SQL or code."

        full_prompt = f"{system_ctx}\n\n{prompt}" if system_ctx else prompt
        answer = await self.llm.generate(ModelRole.CHAT, full_prompt, schema_context=ctx)

        # ── Store to memory ──
        if session_id:
            conversation_memory[session_id].append({
                'role': 'user', 'content': message,
                'data_context': {'file': filename, 'quarter': active_quarter, 'category': active_category},
            })
            conversation_memory[session_id].append({'role': 'assistant', 'content': answer})
            # Trim to MAX_MEMORY_TURNS
            if len(conversation_memory[session_id]) > MAX_MEMORY_TURNS:
                conversation_memory[session_id] = conversation_memory[session_id][-MAX_MEMORY_TURNS:]

        return AgentResponse(intent="CHAT", answer=answer, active_file=filename)

    # ── Chart handler ─────────────────────────────────────────────────────────

    async def _handle_chart(
        self, message: str, filename: str, all_files: list[str], history: list[dict]
    ) -> AgentResponse:
        ctx = build_multi_file_context(all_files, active_file=filename)
        f = get_file(filename)
        
        if not f:
            return AgentResponse(
                intent="CHART",
                answer=f"Dataset '{filename}' not found. Please upload it first.",
                active_file="",
            )

        # Check for systematic/structured formatting request
        wants_systematic = any(kw in message.lower() for kw in ["systematic", "format", "structure", "organized", "proper"])

        # Ask SQL role (qwen-like) to decide the best chart config
        chart_prompt = (
            f"The user asked: {message}\n\n"
            "Use data from the ACTIVE file unless the user explicitly names another file.\n"
            "Based on the data context, choose the best columns and chart type. "
            "Respond ONLY with a JSON object: "
            "{\"type\":\"bar\",\"xKey\":\"col\",\"yKey\":\"col\",\"title\":\"...\",\"aggregation\":\"sum\"}"
        )
        raw = await self.llm.generate(ModelRole.CHART, chart_prompt, schema_context=ctx)
        try:
            config = await self.parse_llm_json(raw)
        except ValueError:
            config = None

        chart_type = _infer_chart_type(message)
        title = message[:60]

        if config:
            x_key = config.get("xKey", "")
            y_key = config.get("yKey", "")
            chart_type = config.get("type", chart_type)
            agg_func = config.get("aggregation", "sum")
            title = config.get("title", title)
        else:
            # fallback: first cat col × first numeric col
            x_key = f.categorical_cols[0] if f.categorical_cols else (f.columns[0].name if f.columns else "")
            y_key = f.numeric_cols[0] if f.numeric_cols else ""
            agg_func = "sum"

        # Compute the actual data using pandas (reliable aggregation)
        if not x_key or not y_key:
            return AgentResponse(
                intent="CHART",
                answer="I couldn't determine the right columns for a chart. Try asking with specific column names.",
                active_file=filename,
            )

        # Check if it's a time-series scenario
        date_cols = [c.name for c in f.columns if c.dtype == "datetime"]
        if x_key in date_cols or "time" in message.lower() or "trend" in message.lower():
            data = time_series(filename, x_key, y_key, freq="M", agg_func=agg_func)
        else:
            data = aggregate(filename, x_key, y_key, agg_func=agg_func)

        if not data:
            return AgentResponse(
                intent="CHART",
                answer="I generated a chart configuration but the aggregation returned no data. Please check column names.",
                active_file=filename,
            )

        chart_config = _build_chart_config(data, x_key, y_key, chart_type, title)
        # Add aggregation function to response
        chart_config['aggregation'] = agg_func
        chart_config['chartType'] = chart_type  # Alias for 'type' field for compatibility

        # Generate detailed natural language description of what the chart shows
        summary_prompt = (
            f"User asked: {message}\n"
            f"Chart Type: {chart_type}\n"
            f"X-Axis: {x_key} | Y-Axis: {y_key} ({agg_func})\n"
            f"Data Sample:\n{json.dumps(data[:5], default=str, indent=2)}\n\n"
            f"Write a detailed 2-3 sentence explanation of:\n"
            f"1. What this chart shows (what's on X and Y axes)\n"
            f"2. Key values and patterns visible in the data\n"
            f"3. What insight this provides to the user\n"
            f"\nDO NOT include any SQL, code, or technical queries. Only natural language description."
        )
        
        # Add formatting instructions if systematic format requested
        if wants_systematic:
            summary_prompt += (
                "\n\nIMPORTANT: Format your response SYSTEMATICALLY with:\n"
                "- Clear numbered sections (1. 2. 3. etc.)\n"
                "- **Bold headers** for sections\n"
                "- Bullet points for key insights\n"
                "- Use markdown formatting for readability\n"
                "- NO SQL or code"
            )
        
        answer = await self.llm.generate(ModelRole.CHAT, summary_prompt)

        return AgentResponse(
            intent="CHART",
            answer=answer,
            chart_config=chart_config,
            active_file=filename,
        )

    # ── Table handler ─────────────────────────────────────────────────────────

    async def _handle_table(
        self, message: str, filename: str, all_files: list[str], history: list[dict]
    ) -> AgentResponse:
        ctx = build_multi_file_context(all_files, active_file=filename)
        f = get_file(filename)
        
        if not f:
            return AgentResponse(
                intent="TABLE",
                answer=f"Dataset '{filename}' not found. Please upload it first.",
                active_file="",
            )

        # Check for systematic/structured formatting request
        wants_systematic = any(kw in message.lower() for kw in ["systematic", "format", "structure", "organized", "proper", "neat", "structured"])

        # Ask SQL role to decide what filter/sort to apply
        table_prompt = (
            f"User asked: {message}\n"
            "Use data from the ACTIVE file unless the user explicitly names another file.\n"
            "Respond ONLY with JSON: "
            "{\"sort_col\":\"col_or_null\",\"sort_asc\":true,\"limit\":20,"
            "\"filters\":{\"col\":{\"op\":\"gt\",\"value\":0}}}"
            " Use null for no sort/filters."
        )
        raw = await self.llm.generate(ModelRole.CHART, table_prompt, schema_context=ctx)
        try:
            config = await self.parse_llm_json(raw)
        except ValueError:
            config = {}

        rows, total = apply_filters(
            filename,
            filters=config.get("filters", {}),
            sort_col=config.get("sort_col"),
            sort_asc=config.get("sort_asc", True),
            limit=config.get("limit", 50),
        )

        cols = list(rows[0].keys()) if rows else [c.name for c in f.columns]

        # Generate detailed description of table
        if rows:
            description_prompt = (
                f"User asked: {message}\n"
                f"Returned {len(rows)} rows out of {total} matching records\n"
                f"Sample data:\n{json.dumps(rows[:3], default=str, indent=2)}\n"
                f"Columns: {', '.join(cols)}\n\n"
                "Write a detailed 2-3 sentence description of what these results show.\n"
                "DO NOT include any SQL, code, or technical queries. Only natural language description."
            )
            
            # Add formatting instructions if systematic format requested
            if wants_systematic:
                description_prompt += (
                    "\n\nIMPORTANT: Format your response SYSTEMATICALLY with:\n"
                    "- Clear numbered sections (1. 2. 3. etc.)\n"
                    "- **Bold headers** for categories\n"
                    "- Bullet points for key details\n"
                    "- Clean, organized structure\n"
                    "- Use markdown formatting for readability\n"
                    "- NO SQL or code"
                )
            
            answer = await self.llm.generate(ModelRole.CHAT, description_prompt)
        else:
            answer = f"No records match your query. Total records in dataset: {total:,}"

        return AgentResponse(
            intent="TABLE",
            answer=answer,
            table_data=rows,
            table_columns=cols,
            active_file=filename,
        )

    # ── Stats handler ─────────────────────────────────────────────────────────

    async def _handle_stats(
        self, message: str, filename: str, all_files: list[str], history: list[dict]
    ) -> AgentResponse:
        # Instead of asking the SQL model to "guess" stats from a 3-row sample,
        # we pipeline stats questions directly to the robust Chat handler which
        # precisely calculates Total Revenue, Top Company, etc.
        return await self._handle_chat(message, filename, all_files, history)

    # ── Dashboard handler ─────────────────────────────────────────────────────

    async def _handle_dashboard(
        self, message: str, filename: str, all_files: list[str], history: list[dict]
    ) -> AgentResponse:
        f = get_file(filename)
        if not f:
            return AgentResponse(
                intent="DASHBOARD",
                answer=f"Dataset '{filename}' not found. Please upload it first.",
                active_file="",
            )

        # Generate config synchronously
        config = auto_dashboard_config(filename, filters={})

        answer = "I have generated a complete dashboard based on the data in your file. It includes key performance indicators and relevant charts."

        return AgentResponse(
            intent="DASHBOARD",
            answer=answer,
            dashboard_config=config,
            active_file=filename,
        )


# ── Singleton ─────────────────────────────────────────────────────────────────
agent = CSVChatAgent(llm=ollama)
