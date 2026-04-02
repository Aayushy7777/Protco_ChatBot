# CSV Chat Agent - AI-Powered Business Intelligence Dashboard

🚀 **Professional BI Dashboard with Auto-Generated Charts & AI Chat Analysis**

An intelligent CSV analysis platform that automatically generates meaningful business intelligence charts and provides AI-powered insights through natural language processing.

---

## 🎯 Features

### 📊 Auto-Generated Dashboards
- **5-6 Essential Charts per Dataset** - Automatically selected based on data analysis
- **24 Chart Types Supported** - Bar, Line, Pie, Donut, Scatter, Pareto, Treemap, and more
- **AI-Driven Intelligence** - Intelligent chart selection using 7 business rules
- **Multi-file Support** - Upload multiple CSVs (Q1-Q4, quarterly data, etc.)
- **Business Insights** - Every chart includes contextual AI-generated explanations

### 💬 AI Chat Analysis
- **Ollama Integration** - Local LLM-powered conversation (no API keys needed)
- **Real-time Analysis** - Ask questions about your data in natural language
- **Context-Aware** - Chat remembers your active datasets and filters

### 🎨 Professional Dashboard UI
- **Dark-Themed Design** - Navy (#0A0F2C) + Cyan (#00D4FF) color scheme
- **Responsive Layout** - Works on desktop, tablet, mobile
- **Smooth Animations** - Framer Motion transitions
- **File Tabs** - Quick switching between uploaded datasets
- **Filter Support** - Filter by quarter and category dynamically

### 🧠 Intelligent Processing
- **Column Auto-Detection** - Identifies numeric, date, categorical, and currency columns
- **Data Exclusion** - Automatically excludes non-analysis columns (HSN, ZIP, PIN, GSTIN, etc.)
- **Quarter Detection** - Auto-detects Q1-Q4 or FY25+ from filenames
- **INR Currency Formatting** - Proper Indian Rupee formatting (₹Cr, ₹L, ₹K)

---

## 🛠 Tech Stack

### Backend
- **FastAPI** - REST API framework
- **Pandas** - Data processing
- **Ollama** - Local LLM integration
- **Python 3.10+** - Core language

### Frontend
- **React 18+** - UI framework
- **ECharts v5** - 24 chart implementations
- **Vite** - Build tool
- **Tailwind CSS** - Styling
- **Zustand** - State management
- **Framer Motion** - Animations

---

## 📦 Installation

### Prerequisites
- Python 3.10+
- Node.js 16+
- Ollama (for AI features)

### Backend Setup
```bash
cd "CSV CHAT AGENT"
python -m venv .venv
.venv\Scripts\activate  # Windows
source .venv/bin/activate  # Linux/Mac
pip install -r BACKEND/requirements.txt
```

### Frontend Setup
```bash
cd FRONTEND
npm install
```

---

## 🚀 Quick Start

### Terminal 1 - Start Backend
```bash
cd "CSV CHAT AGENT"
.venv\Scripts\activate
python BACKEND/main.py
```
Backend will run on `http://localhost:8000`

### Terminal 2 - Start Frontend
```bash
cd "CSV CHAT AGENT\FRONTEND"
npm run dev
```
Frontend will run on `http://localhost:5173`

### Terminal 3 - Run Tests (Optional)
```bash
cd "CSV CHAT AGENT"
.venv\Scripts\activate
python test_charts_e2e.py
```

---

## 📊 Usage

1. **Open Dashboard** → http://localhost:5173
2. **Upload CSV File** → Click "Upload CSV" button
3. **View Auto-Generated Charts** → 5-6 focused analysis charts appear automatically
4. **Switch Between Files** → Use file tabs at the top
5. **Chat with AI** → Click chat bubble to ask questions about your data
6. **Cycle Chart Types** → Click "↻ Cycle" to switch visualization types
7. **Remove Charts** → Click "✕ Remove" to delete charts from dashboard

### Supported File Types
- CSV (.csv)
- Excel (.xlsx, .xls)
- Multiple files at once

### File Naming Convention
- Include quarter in filename: `InvoiceDetails_Q1.csv`, `Sales_Q2.xlsx`
- System auto-detects: Q1-Q4, FY25-FY99
- Use clear column names for best analysis

---

## 📈 Chart Types

### Currently Implemented (5-6 per dataset)
1. **Bar Horizontal** - Top performers ranking
2. **Donut** - Revenue distribution
3. **Pareto** - 80/20 analysis
4. **Line Area** - Trends over time
5. **Scatter** - Correlation analysis
6. *(Optional 6th based on data)*

### Full Library Available (24 total)
Line, Bar (4 types), Pie, Donut, Scatter, Bubble, Radar, Gauge, Waterfall, Pareto, TreeMap, Funnel, Sankey, Calendar Heatmap, Histogram, BoxPlot, and more.

---

## 🧪 Testing

Run end-to-end tests:
```bash
python test_charts_e2e.py
```

Expected output:
- ✅ CSV loading
- ✅ AI chart selection
- ✅ Data preparation
- ✅ Chart type diversity
- ✅ Business insights

---

## 📁 Project Structure

```
CSV CHAT AGENT/
├── BACKEND/
│   ├── main.py                 # FastAPI app & routes
│   ├── csv_processor.py        # AI selection & data prep
│   ├── agent.py                # Ollama AI chat
│   ├── ollama_manager.py       # Ollama connection
│   └── requirements.txt        # Python dependencies
├── FRONTEND/
│   ├── src/
│   │   ├── components/
│   │   │   ├── chat/           # Chat UI
│   │   │   ├── dashboard/      # Dashboard & charts
│   │   │   └── layout/         # Layout components
│   │   ├── store/              # State management
│   │   ├── hooks/              # Custom React hooks
│   │   ├── utils/              # Utilities
│   │   └── App.jsx             # Main app
│   ├── package.json
│   ├── vite.config.js
│   └── tailwind.config.js
├── test_charts_e2e.py          # End-to-end tests
├── test_*.py                   # Additional tests
├── README_CHARTS.md            # Detailed chart docs
└── IMPLEMENTATION_SUMMARY.md   # Technical reference
```

---

## 🔧 Configuration

### Backend Environment
Edit `BACKEND/main.py`:
- Change `DEFAULT_MODEL` for different Ollama models
- Adjust `UPLOAD_DIR` for file storage location
- Modify `API_HOST` and `API_PORT` as needed

### Frontend Environment
Edit `FRONTEND/src/App.jsx`:
- Change `API` URL if backend is on different server
- Adjust colors in Dashboard and ChartRenderer

### CORS Settings
Currently allows:
- http://localhost:5173
- http://localhost:5174
- http://localhost:3000
- http://127.0.0.1:5173

Modify in `BACKEND/main.py` to add more origins.

---

## 📊 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| POST | `/api/upload` | Upload CSV files |
| GET | `/api/files` | List uploaded files |
| POST | `/api/auto-dashboard` | Generate KPIs & summary |
| POST | `/api/generate-all-charts` | Generate all charts with AI selection |
| POST | `/api/chat` | Send message to AI agent |
| POST | `/api/chat/stream` | Stream AI responses |
| GET | `/api/quarter-status` | Get uploaded quarters |
| GET | `/api/health` | Health check |

---

## 🎓 Learning Resources

- [ECharts Documentation](https://echarts.apache.org/)
- [FastAPI Docs](https://fastapi.tiangolo.com/)
- [React Hooks](https://react.dev/reference/react/hooks)
- [Pandas API](https://pandas.pydata.org/docs/)
- [Ollama Models](https://ollama.ai/library)

---

## 🐛 Troubleshooting

### CORS Errors
- Ensure backend is running on http://localhost:8000
- Check `allow_origins` in `main.py`
- Browser console shows exact origin issue

### Charts Not Appearing
- Check browser console for errors
- Verify data has numeric/categorical columns
- Run `test_charts_e2e.py` to validate backend

### Ollama Not Connecting
- Ensure Ollama service is running
- Check Ollama is on http://localhost:11434
- Run `ollama pull qwen2.5:7b` to download model

### Port Already in Use
- Backend: `lsof -i :8000` (Linux/Mac) or find process on Windows
- Frontend: Try `npm run dev -- --port 5174`

---

## 📝 License

This project is open source. Use and modify for your needs.

---

## 👨‍💻 Author

Created with ❤️ for business intelligence analysis.

---

## 🤝 Contributing

Contributions welcome! Please:
1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📞 Support

For issues or questions:
1. Check README_CHARTS.md for detailed documentation
2. Run test_charts_e2e.py to verify setup
3. Check browser DevTools console for errors
4. Review backend logs for API issues

---

**Status**: ✅ Production Ready  
**Version**: 1.0.0  
**Last Updated**: April 2, 2026

Built with FastAPI, React, ECharts, and Ollama. 🚀
