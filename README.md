# 📊 CSV Chat Agent - AI-Powered Analytics Dashboard

> **🚀 Production-Grade Analytics with Skeleton Loading & Lazy Rendering**

A lightweight CSV analysis platform with auto-generated BI dashboards, AI-powered insights, and local LLM integration — **Zero cloud dependencies, 100% private**.

---

## ⚡ Quick Start (One Click)

```bash
# Windows
START_ALL.bat

# macOS/Linux  
chmod +x start.sh && ./start.sh
```

**Services:**
- 📊 **Analytics Dashboard** → http://localhost:8011 (CSV analysis & charts)
- 🎛️ **Mission Control** → http://localhost:3000 (agent orchestration UI)
- 🤖 **Ollama API** → http://localhost:11434 (local LLM server)

---

## ✨ Key Features

### 📊 Smart Analytics Dashboard
- **4 Intelligent Charts** - Automatically selected from your data:
  - Category vs Amount (Bar Chart)
  - Time Trend Analysis (Line/Bar Chart)
  - Status Distribution (Doughnut Chart)  
  - Average Progress by Category (Bar Chart)
- **5 KPI Cards** - Key metrics above the fold
- **Interactive Data Table** - Full dataset with filtering
- **Skeleton Loading** - Animated placeholders while data loads
- **Lazy Rendering** - Charts render sequentially (no UI blocking)
- **Responsive Design** - 2×2 chart grid on desktop, 1-column on mobile

### 💬 AI Chat Integration
- **Local Ollama LLM** - No API keys, no cloud costs, 100% private
- **Natural Language Q&A** - Ask questions about your data
- **Instant Analysis** - Get AI-powered insights on charts and tables
- **Zero Latency** - Everything runs locally

### 🎛️ Mission Control
- **Agent Orchestration UI** - Deploy and manage AI agents
- **Workflow Dashboard** - Monitor task execution and logs
- **Real-time Status** - Live health indicators for all services

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Analytics UI** | HTML5 + Chart.js 4.4.1 | Interactive dashboard with 4 charts |
| **Dashboard Gen** | Python (FastAPI) | CSV processing & chart generation |
| **Agent Platform** | Next.js 16 + TypeScript | Mission Control UI |
| **Local LLM** | Ollama + llama3.1 | Text generation & embeddings |
| **Data Store** | ChromaDB + SQLite | Vector storage |
| **Language** | Python 3.14 | Backend processing |

---

## 📦 Installation & Setup

### Prerequisites
- **Python 3.10+** (3.14 recommended)
- **Node.js 18+** (for Mission Control)
- **Ollama** → [Download](https://ollama.ai)

### Automated Setup (Recommended)
```bash
# Windows
START_ALL.bat

# Linux/macOS
chmod +x start.sh && ./start.sh
```

### Manual Setup

**Terminal 1: Ollama**
```bash
ollama serve
```

**Terminal 2: Backend (Port 8011)**
```bash
cd ai-dashboard/backend
python -m uvicorn main:app --port 8011 --reload
```

**Terminal 3: Mission Control (Port 3000)**
```bash
cd mission-control
pnpm install
pnpm dev
```

---

## � Usage Guide

### Upload & Analyze CSV
1. Navigate to **http://localhost:8011**
2. Click **"Upload CSV"** button
3. Select a CSV or XLSX file
4. Dashboard auto-generates with:
   - 5 KPI cards (top-right)
   - 4 charts (2×2 grid)
   - Full data table (bottom)
   - Chat sidebar (right)

### Supported File Formats
✅ CSV  
✅ XLSX/XLS  
✅ TSV  

### Analyze with AI Chat
1. Type a question in the chat box (e.g., "What's the trend in sales?")
2. Press Enter or click Send
3. Ollama analyzes the chart data and responds
4. Continue conversation naturally

### Use Mission Control
1. Navigate to **http://localhost:3000**
2. View agent fleet status
3. Deploy new agents
4. Monitor task execution in real-time

---

## 🎨 Dashboard Features

### Skeleton Loading (Production UX)
- Shows animated placeholder rows while data loads
- Shimmer effect (1.5s loop) creates perception of progress
- **No "stuck" spinner** — users see active loading

### Lazy Rendering
- Charts initialize sequentially (50ms stagger)
- Prevents UI blocking even with large datasets
- Smooth fade-in animations as content appears
- **Smooth user experience** on all connection speeds

### Responsive Layout
```
Desktop (>1100px):  2-column chart grid + full table
Tablet (768-1100): Multi-row adapts to width
Mobile (<768px):   Single-column, charts stack vertically
```

---

## � API Endpoints

### Analytics Backend (8011)
```
POST   /upload                  Upload CSV file → Returns dashboard HTML
GET    /docs                    Interactive Swagger API docs
```

### Mission Control (3000)
```
GET    /api/agents              Agent fleet status
POST   /api/chat                Chat query to Ollama
GET    /api/dashboard           Dashboard metrics
```

### Ollama (11434)
```
POST   /api/generate            Generate text from llama3.1
POST   /api/embeddings          Create embeddings
```

---

## 🚀 Production Checklist

✅ **Skeleton Loading** - Animated placeholders prevent "stuck" UI  
✅ **Lazy Rendering** - Sequential chart init with requestAnimationFrame  
✅ **Error Handling** - Graceful fallbacks for missing data  
✅ **No UI Blocking** - setTimeout stagger prevents freezing  
✅ **Responsive Design** - Works on mobile, tablet, desktop  
✅ **Local-First** - Zero cloud dependencies  
✅ **Security** - CSVs never sent to internet

---

## � What Each Chart Shows

| Chart | Data Type | Use Case |
|-------|-----------|----------|
| **Category vs Amount** | Categorical metrics | Top products, sales by region |
| **Time Trend** | Time-series data | Daily/monthly trends, growth patterns |
| **Status Distribution** | Categorical counts | Status breakdowns, proportions |
| **Progress by Category** | Metrics across groups | Performance by team, KPI tracking |

---

## 🔒 Security & Privacy

✅ **Zero Cloud** - Everything on your machine  
✅ **No Telemetry** - No tracking, no analytics collection  
✅ **Private Data** - CSVs only exist locally  
✅ **Open Source** - Inspect all code  
✅ **Ollama Only** - No external LLM usage  

---

## 📋 Project Structure

```
CSV CHAT AGENT/
├── ai-dashboard/           # Main analytics dashboard (port 8011)
│   ├── backend/            # FastAPI + chart generation
│   ├── frontend/           # HTML dashboard + Chart.js
│   └── uploads/            # Uploaded CSV files
├── mission-control/        # Agent orchestration (port 3000)
│   ├── src/                # Next.js + TypeScript
│   └── package.json        # Node dependencies
├── BACKEND/                # Legacy backend
├── FRONTEND/               # Legacy frontend
├── start.bat / start.sh    # Service launcher
└── README.md               # This file
```

---

## 🎯 Current Status

**✅ Production Ready**
- All 3 services running and validated
- 4 charts rendering with smooth animations
- Skeleton loading providing professional UX
- Lazy rendering preventing UI lag
- CSV upload pipeline fully functional

**Last Updated:** 2026  
**Version:** 3.0 (Production-Grade UI)  
**Python:** 3.14 with Pydantic V1 compatibility

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port 8011 in use** | `Get-Process python \| Stop-Process` then restart backend |
| **Dashboard not loading** | Refresh browser (Ctrl+Shift+R for hard reset) |
| **Charts stuck on skeleton** | Check browser console for JavaScript errors, restart backend |
| **Ollama not responding** | Run `ollama pull llama3.1` then restart service |
| **Upload failing** | Verify CSV has headers, try smaller file, check logs |

**Port Reference:**
- **8011** = Analytics Dashboard  
- **3000** = Mission Control  
- **11434** = Ollama API  

---

## 📞 Support

- ❓ Dashboard questions → Check [Usage Guide](#-usage-guide) section
- 🐛 Issues → Review [Troubleshooting](#-troubleshooting) table
- 📄 Architecture → See [Project Structure](#-project-structure)
- 🤖 API Details → Run backend + visit http://localhost:8011/docs

---

## 💡 Tips

- **Reload Dashboard:** Use Ctrl+Shift+R (hard refresh) in browser
- **View Logs:** Check terminal where backend is running
- **Test Upload:** Use sample CSV from `uploads/` folder
- **Debug Charts:** Open browser DevTools (F12) → Console tab
- **Stop All:** Ctrl+C in each terminal or run batch file with kill flag

---

## 🤝 Contributing & License

Open source - use, modify, and distribute freely.
