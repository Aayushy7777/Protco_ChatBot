# CSV Chat Agent - AI-Powered Data Analysis Platform

An intelligent chatbot application that analyzes CSV/Excel data using natural language queries, powered by Ollama AI models. Upload your data and ask questions in plain English to get instant insights, reports, and visualizations.

## 🌟 Features

- **Natural Language Queries**: Ask questions about your data in plain English
- **Smart Query Engine**: Automatic detection of data columns and aggregations
- **Real-time Analytics**: Instant Top-N analysis, customer reports, and data summaries
- **Dashboard Visualization**: Beautiful HTML dashboards with charts and insights
- **Multi-file Support**: Upload and analyze multiple CSV/Excel files
- **AI-Powered Responses**: Context-aware answers using Ollama (phi3 model)
- **Fallback Intelligence**: Graceful degradation when AI model is unavailable
- **Error Handling**: Robust error recovery with detailed logging

## 🏆 Key Capabilities

### Smart Queries
- **Top-N Analysis**: "Top 5 Customers by Amount", "Top 10 Categories by Sales"
- **Customer Reports**: "Give me a customer report of [Customer Name]"
- **Data Summaries**: Column statistics, counts, aggregations
- **Custom Filters**: Natural language-based data filtering

### Dashboard Features
- Interactive HTML dashboards
- Real-time data visualization
- KPI monitoring
- Performance metrics
- Export capabilities

## 📋 Prerequisites

### Required
- **Python 3.8+**: Core runtime
- **Ollama**: Local LLM server (Download: https://ollama.ai)
- **phi3 Model**: Run `ollama pull phi3` before starting

### Optional
- **Node.js 18+**: For frontend (Mission Control dashboard)
- **Git**: For version control

## ⚙️ Installation

### 1. Clone the Repository
```bash
git clone https://github.com/Aayushy7777/Protco_ChatBot.git
cd Protco_ChatBot
```

### 2. Set Up Python Environment

#### Windows (PowerShell)
```powershell
# Create virtual environment
python -m venv ai_env

# Activate virtual environment
.\ai_env\Scripts\Activate.ps1

# Install dependencies
pip install -r ai-dashboard/backend/requirements.txt
```

#### macOS/Linux
```bash
# Create virtual environment
python3 -m venv ai_env

# Activate virtual environment
source ai_env/bin/activate

# Install dependencies
pip install -r ai-dashboard/backend/requirements.txt
```

### 3. Configure Environment

Copy `.env.example` to `.env` in the backend directory:
```bash
cd ai-dashboard/backend
cp .env.example .env
```

Edit `.env` with your configuration:
```env
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=phi3
CHAT_MODEL=phi3
PORT=8011
HOST=127.0.0.1
UPLOAD_DIR=../uploads
```

### 4. Start Ollama
In a separate terminal/Command Prompt, ensure Ollama is running:
```bash
# Ollama server runs on http://localhost:11434
ollama serve

# In another terminal, pull the phi3 model if not already done
ollama pull phi3
```

### 5. Set Up Frontend (Optional)

If you want to use the Mission Control dashboard:
```bash
cd mission-control
npm install
# or
pnpm install
```

## 🚀 Running the Project

### Option 1: Backend Only (API Mode)

```bash
# Navigate to backend directory
cd ai-dashboard/backend

# Activate virtual environment
# Windows: .\..\..\ai_env\Scripts\Activate.ps1
# macOS/Linux: source ../../../ai_env/bin/activate

# Start the API server
python -m uvicorn main:app --port 8011 --host 127.0.0.1

# Server will be available at http://127.0.0.1:8011
# Health check: http://127.0.0.1:8011/api/health
```

### Option 2: Full Stack (API + Dashboard)

**Terminal 1 - Start Backend:**
```bash
cd ai-dashboard/backend
# Activate venv and run:
python -m uvicorn main:app --port 8011 --host 127.0.0.1
```

**Terminal 2 - Start Frontend:**
```bash
cd mission-control
pnpm dev
# Dashboard available at http://localhost:3000
```

### Option 3: Using Docker (if available)
```bash
# Build and run with docker-compose
docker-compose up -d
```

## 📡 API Endpoints

### Health Check
```
GET /api/health
Response: 200 OK
```

### Upload CSV/Excel File
```
POST /upload
Content-Type: multipart/form-data
Body: file (CSV or Excel file)
Response: { "message": "File uploaded", "filename": "..." }
```

### Chat with Data
```
POST /api/chat
Content-Type: application/json
Body: {
    "question": "What are the top 5 customers by amount?",
    "history": []  // Optional conversation history
}
Response: {
    "answer": "...",
    "type": "smart_query|custom|error",
    "data": {...}  // Optional data for visualizations
}
```

Example using curl:
```bash
curl -X POST http://127.0.0.1:8011/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Top 5 customers by amount", "history": []}'
```

## 📂 Project Structure

```
Protco_ChatBot/
├── ai-dashboard/
│   ├── backend/
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── local_csv_chat.py       # Smart query engine
│   │   ├── requirements.txt        # Python dependencies
│   │   ├── .env.example            # Environment template
│   │   ├── .env                    # Environment config (git-ignored)
│   │   └── uploads/                # Uploaded CSV/Excel files
│   └── frontend/
│       ├── src/                    # React components
│       └── public/                 # Static assets
├── mission-control/                # Dashboard application
│   ├── src/
│   ├── package.json
│   └── pnpm-lock.yaml
├── BACKEND/                        # Legacy backend
├── .env                            # Root environment (git-ignored)
├── .env.example                    # Root environment template
├── .gitignore                      # Git ignore rules
├── README.md                       # This file
└── requirements.txt                # Root dependencies

```

## 🔧 Configuration

### Ollama Model Options
The system is configured for **phi3** model, but you can use other models:
```bash
# Pull alternative models
ollama pull llama2          # ~4GB
ollama pull neural-chat     # ~3GB
ollama pull mistral         # ~5GB

# Update .env with the new model name
OLLAMA_MODEL=llama2
```

### Server Port
To change the API port from 8011:
```bash
python -m uvicorn main:app --port 8012 --host 127.0.0.1
```

### Upload Directory
Change where files are stored:
```env
UPLOAD_DIR=../../data/uploads
```

## 🧪 Testing

### Test Smart Queries
```bash
cd ai-dashboard/backend
python test_topN.py          # Test Top-N queries
python test_customer_report.py  # Test customer reports
python test_all_features.py   # Run all feature tests
```

### Manual API Testing
```bash
# 1. Upload a CSV file
curl -F "file=@sample.csv" http://127.0.0.1:8011/upload

# 2. Ask a question
curl -X POST http://127.0.0.1:8011/api/chat \
  -H "Content-Type: application/json" \
  -d '{"question": "Give me a customer report of [customer name]"}'
```

## 🔒 Security

### Important Security Notes
- **Never commit `.env` files** - Environment variables are git-ignored
- **API Keys**: Keep MC_API_KEY and other sensitive data in `.env` only
- **CORS**: Configure properly for production use
- **Uploads**: Validate and sanitize file inputs
- **Ollama**: Run on localhost only or use authentication

### Pre-Push Security Checklist
- ✅ `.env` files are in `.gitignore`
- ✅ No hardcoded credentials in source code
- ✅ `.env.example` has placeholder values only
- ✅ Sensitive files (uploads, cache) are ignored
- ✅ Database files are git-ignored

## 🐛 Troubleshooting

### Port Already in Use
```
OSError: [Errno 48] Address already in use
```
**Solution:**
```bash
# Windows
netstat -ano | findstr :8011
taskkill /PID <PID> /F

# macOS/Linux
lsof -i :8011
kill -9 <PID>
```

### Ollama Not Running
```
Error: Connection refused - http://localhost:11434
```
**Solution:** Ensure Ollama is running:
```bash
ollama serve
```

### Module Not Found Error
```
ModuleNotFoundError: No module named 'tabulate'
```
**Solution:** Install dependencies in virtual environment:
```bash
pip install -r ai-dashboard/backend/requirements.txt
```

### CSV File Not Processing
```
ParserError: Error tokenizing data
```
**Solution:**
- Verify CSV is properly formatted
- Check encoding (use UTF-8)
- Ensure file isn't corrupted
- Check file size limits

## 📊 Query Examples

### Instant Analytics
```
"What are the top 5 customers by amount?"
"Show me the top 10 product categories"
"Give me a report of customer 2140056-Siliguri Agencies"
"How many transactions are in the dataset?"
"What's the total revenue by category?"
```

### Natural Language
```
"Which customer spent the most?"
"Break down sales by region"
"Show transactions for [customer name] from highest to lowest"
"How many unique customers are there?"
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes
4. Run tests: `python test_all_features.py`
5. Commit: `git commit -m 'Add amazing feature'`
6. Push: `git push origin feature/amazing-feature`
7. Open a Pull Request

## 📝 Changelog

### v1.0.0 (Current)
- ✅ Smart query engine for Top-N analysis
- ✅ Customer detail reports
- ✅ Real-time data processing
- ✅ Error handling with graceful fallbacks
- ✅ Ollama AI integration (phi3 model)
- ✅ FastAPI backend
- ✅ Frontend dashboard integration

### Planned Features
- [ ] Multi-language support
- [ ] Advanced data visualization
- [ ] Scheduled reports via email
- [ ] User authentication & authorization
- [ ] Data export (CSV, PDF)
- [ ] Custom model fine-tuning
- [ ] API rate limiting
- [ ] Batch processing

## 📄 License

This project is provided as-is for educational and commercial use.

## 👨‍💻 Author

**Aayush Yadav**
- GitHub: [@Aayushy7777](https://github.com/Aayushy7777)
- Repository: [Protco_ChatBot](https://github.com/Aayushy7777/Protco_ChatBot)

## 🙏 Acknowledgments

- **Ollama**: For providing excellent local LLM infrastructure
- **FastAPI**: For the amazing Python web framework
- **Pandas**: For data manipulation and analysis
- **Community**: For feedback and contributions

## ❓ FAQ

### Q: Do I need internet connection?
**A:** No, everything runs locally. Ollama runs on localhost:11434.

### Q: Can I use GPU acceleration?
**A:** Yes, Ollama supports GPU. Install NVIDIA CUDA drivers and enable GPU in Ollama settings.

### Q: What's the data size limit?
**A:** Currently tested up to 10,000+ rows. Performance depends on available RAM.

### Q: Can I use different AI models?
**A:** Yes! Pull any Ollama-compatible model and update `.env` with the model name.

### Q: How do I export results?
**A:** API returns JSON data. Frontend dashboard includes export options.

### Q: Is this production-ready?
**A:** Current version is suitable for development and small deployments. For production, add authentication, rate limiting, and use a production WSGI server.

## 📞 Support

For issues, questions, or suggestions:
1. Check the [Troubleshooting](#troubleshooting) section
2. Review existing GitHub Issues
3. Create a new GitHub Issue with details
4. Contact via GitHub discussions

---

**Last Updated:** April 2026  
**Status:** Active Development
