# CSV Chat Agent - Project Status

**Last Updated**: April 2, 2026  
**Current Phase**: Dashboard KPI Integration Complete

---

## 📊 Quick Summary

A full-stack AI data analysis tool that lets users upload CSV/XLSX files and ask questions in natural language, with AI-powered responses, automatic chart generation, and a professional dashboard with KPI metrics.

**Status**: ✅ Fully Functional - Both backends running, KPI integration complete

---

## 🏗️ Architecture Overview

```
CSV Chat Agent
├── BACKEND (FastAPI + Python)
│   ├── main.py (API server, routes)
│   ├── agent.py (Intent classification, LLM orchestration)
│   ├── csv_processor.py (Data parsing, aggregation, KPI formatting)
│   └── ollama_manager.py (Local LLM integration)
│
├── FRONTEND (React + Vite)
│   ├── src/
│   │   ├── App.jsx (Main app, file management)
│   │   ├── components/
│   │   │   ├── chat/ (Chat interface, messages, input)
│   │   │   ├── dashboard/ (KPI cards, charts, filters)
│   │   │   └── layout/ (Sidebar, header)
│   │   ├── hooks/ (useChat, useKPIs, custom state logic)
│   │   ├── store/ (Zustand stores: chat, dashboard, filters)
│   │   └── utils/ (Helpers, formatters)
│   └── vite.config.js (Dev server, API proxy)
│
└── Data Files & Tests
```

---

## ✅ Features Implemented

### Chat Interface
- **Multi-file upload**: CSV, XLSX, XLS support
- **Chat streaming**: Token-by-token responses with SSE
- **Intent classification**: Auto-detects CHAT, CHART, TABLE, STATS
- **Multi-file context**: Maintains all loaded files, active file selection
- **Conversation history**: Persistent chat threads per file

### Data Processing
- **Automatic column detection**: Numeric, categorical, datetime types
- **INR formatting**: Currency auto-detected, formatted as ₹Cr/₹L/₹XX,XXX
- **Aggregation**: Sum, avg, min, max with proper formatting
- **Time-series resampling**: Monthly/quarterly/yearly aggregation
- **Safe JSON parsing**: LLM-assisted retry on parse errors

### Dashboard & Visualization
- **Interactive charts**: Bar, Line, Pie with ECharts
- **Color palette**: 9-color CHART_COLORS scheme applied to all charts
- **KPI metrics**: Auto-calculated for numeric columns (sum, avg, count, min, max, median)
- **KPI cards**: Display with trend indicators, currency detection
- **Filter support**: Category-based multi-select filters
- **Responsive grid**: 1→2→4 columns (mobile→tablet→desktop)
- **Drill-down**: Click charts to filter by category
- **Pin/unpin**: Save favorite charts to dashboard

### LLM Models (Ollama)
1. **mistral:7b** (Fast, default)
2. **qwen2.5:7b** (SQL-optimized)
3. **llama3.1:8b** (Chat)
4. **deepseek-r1:8b** (Advanced reasoning)
5. **qwen3-coder** (Code generation)
6. **gpt-oss** (GPT-style)
7. **deepseek-v3.1** (Latest)

---

## 🚀 How to Run

### Backend
```bash
cd BACKEND
.\.venv\Scripts\activate
uvicorn main:app --reload --port 8000
```
**Runs on**: http://localhost:8000

### Frontend
```bash
cd FRONTEND
npm run dev
```
**Runs on**: http://localhost:5173

### Prerequisites
- Python 3.10+ (with venv activated)
- Node.js 18+
- Ollama running on localhost:11434
- Backend running on port 8000
- Frontend accessible at 5173 (with API proxy to 8000)

---

## 📁 Key Files & Their Purpose

### Backend

| File | Purpose | Key Functions |
|------|---------|---------------|
| `main.py` | FastAPI app, all API routes | `/api/upload`, `/api/chat/stream`, `/api/kpi-metrics`, `/api/files`, `/api/health` |
| `agent.py` | Intent classification, LLM calls | `_classify()`, `_handle_chart()`, `_handle_stats()`, `parse_llm_json()` |
| `csv_processor.py` | CSV parsing, aggregation, formatting | `parse_csv()`, `aggregate()`, `format_inr()`, `format_kpi_metrics()` |
| `ollama_manager.py` | Ollama API wrapper | `OllamaManager` class, model selection |

### Frontend

| File | Purpose |
|------|---------|
| `App.jsx` | Main app, file management, tab routing (Chat/Dashboard) |
| `src/hooks/useChat.js` | Chat streaming, message handling |
| `src/hooks/useKPIs.js` | KPI fetching, auto-refresh on file change |
| `src/store/chatStore.js` | Zustand: conversations, messages |
| `src/store/dashboardStore.js` | Zustand: pinned charts, filters, drill-down |
| `src/components/dashboard/Dashboard.jsx` | Dashboard layout, KPI section, chart grid |
| `src/components/dashboard/KPICard.jsx` | KPI card display with trends |
| `src/components/dashboard/ChartRenderer.jsx` | ECharts wrapper with color palette |
| `src/components/dashboard/AdvancedFilterPanel.jsx` | Multi-select filter UI |

---

## 🔧 API Endpoints

### File Management
- `POST /api/upload` - Upload CSV/XLSX/XLS files
- `GET /api/files` - List all uploaded files with metadata
- `GET /api/files/{name}/schema` - Get column metadata
- `DELETE /api/files/{name}` - Remove a file

### Chat & Analysis
- `POST /api/chat/stream` - Send message, get SSE streaming response
  - Request: `{message, active_file, all_files, conversation_id}`
  - Response: SSE stream with status updates (classifying, loading, generating, token, chart, done)
- `POST /api/kpi-metrics` - Get KPI metrics for a file
  - Query: `?filename=...&filters=...`
  - Response: `{filename, row_count, kpi_cards: [...], filters_applied}`

### System
- `GET /api/health` - Ollama status, loaded files

---

## 📊 Request/Response Flows

### Chat Flow
1. User types message in Chat tab
2. Frontend fetches all file list from `/api/files`
3. Sends POST to `/api/chat/stream` with message + file context
4. Backend:
   - Classifies intent (CHART/TABLE/STATS/CHAT)
   - Selects appropriate LLM model
   - Processes data (aggregation, filtering)
   - Generates response
5. Backend streams response as SSE
6. Frontend appends tokens to message
7. If CHART intent, frontend receives chart config and pins to dashboard

### KPI Flow
1. Dashboard mounted with active file
2. Calls `useKPIs(activeDataset)` hook
3. Hook fetches POST `/api/kpi-metrics?filename=...`
4. Backend:
   - Loads CSV data
   - Calculates metrics for each numeric column
   - Formats to dashboard card structure
5. Returns KPI cards array
6. Dashboard renders KPICard components

---

## 💾 Data Structures

### KPI Card Object
```javascript
{
  title: "Total Revenue",           // Formatted column name
  value: "₹25.50Cr",                // Formatted value
  metric: "sum",                    // Primary metric used
  unit: "",                         // Unit suffix
  trend: 12.5,                      // % trend (avg vs median)
  raw_value: 255000000,             // Numeric value
  count: 1000,                      // Row count
  is_currency: true                 // Currency detected
}
```

### Chart Config Object
```javascript
{
  chartType: "bar",                 // bar|line|pie|scatter
  x_col: "Category",                // X-axis column
  y_col: "Revenue",                 // Y-axis column
  aggregation: "sum",               // sum|avg|count|min|max
  data_source: "aggregated",        // Source type
  title: "Revenue by Category"      // Display title
}
```

---

## 🎨 Styling & UI

- **Theme**: Dark (slate-900 base)
- **Colors**: 
  - Primary: Indigo-600
  - Chart palette: 9-color palette (185FA5, 0F6E56, 993556, ...)
  - Neutral: Slate shades
- **Framework**: Tailwind CSS + Framer Motion
- **Icons**: Heroicons
- **Animations**: Smooth transitions, motion enter/exit

---

## 🔄 State Management

### Zustand Stores

**chatStore.js**
- `conversations`: Map of chat threads
- `activeConversation`: Current chat ID
- `addMessage()`, `updateLastMessage()`, `createConversation()`

**dashboardStore.js**
- `pinnedCharts`: Array of chart objects
- `filters`, `activeFilters`: Column filters
- `drillDownPath`: Navigation breadcrumb
- `setFilter()`, `removeFilter()`, `clearFilters()`
- `pinChart()`, `unpinChart()`, `drillDown()`, `drillUp()`

**useChatStore Hook** (custom)
- Wraps chatStore with additional helpers

---

## 🧪 Testing Files

Test scripts for debugging:
- `test_streaming.py` - Stream chat responses
- `test_intent_classification.py` - Intent detection
- `test_excel_upload.py` - XLSX parsing
- `test_classification_debug.py` - Intent classification edge cases
- `test_user_scenarios.py` - End-to-end flows
- `test_data_with_dates.csv` - Sample data with timestamps

---

## 🐛 Common Issues & Fixes

| Issue | Cause | Solution |
|-------|-------|----------|
| Port 5173/8000 in use | Previous process still running | Kill process: `Get-Process node/python \| Stop-Process -Force` |
| File not found in API | File may not be loaded | Check `/api/files` endpoint first |
| Charts not rendering | JSON parse error from LLM | Check LLM output in console logs |
| INR format missing | Currency column not detected | Add 'revenue', 'sales', 'amount' to column name |
| KPI cards blank | No numeric columns in file | Upload file with numeric data |

---

## 📋 Completed Milestones

✅ Backend API with FastAPI  
✅ CSV/XLSX/XLS parsing  
✅ Intent classification (CHAT/CHART/TABLE/STATS)  
✅ Chat streaming with SSE  
✅ Multi-file support with context  
✅ ECharts integration with color palette  
✅ INR formatting for currency  
✅ Safe JSON parsing with LLM retry  
✅ Dashboard with responsive grid  
✅ KPI metrics calculation and display  
✅ Filter panel implementation  
✅ Zustand state management  
✅ Both servers running simultaneously  

---

## 🔮 Possible Enhancements

- [ ] Tab-based dashboard views (Sales, Marketing, Operations)
- [ ] Advanced filter panel wire-up to real-time updates
- [ ] KPI card custom coloring by metric type
- [ ] Drill-down support for KPIs
- [ ] CSV export from filtered data
- [ ] Chart customization UI (colors, titles, axes)
- [ ] Saved chart templates
- [ ] Sharing/embedding charts
- [ ] Real-time data refresh
- [ ] Multi-language support

---

## 📞 Quick Reference

| Command | Purpose |
|---------|---------|
| `npm run dev` | Start frontend (port 5173) |
| `uvicorn main:app --reload` | Start backend (port 8000) |
| `python test_streaming.py` | Test chat streaming |
| `python -m py_compile main.py` | Check Python syntax |
| `Get-Process node` | Find Node processes |

---

## 🎯 Current Status

**Backend**: ✅ Running on port 8000  
**Frontend**: ✅ Running on port 5173  
**Ollama**: ✅ Available at localhost:11434  
**Dashboard**: ✅ KPI cards integrated and functional  
**Chat**: ✅ Streaming responses with chart generation  
**Overall**: 🟢 Production Ready
