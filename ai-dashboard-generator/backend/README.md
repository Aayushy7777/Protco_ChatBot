# 📊 AI Dashboard Generator - Backend Only

**Professional Project Management Dashboard with Local Ollama Integration**

## ✨ Features

- 📤 **File Upload**: Support for CSV, XLSX, XLS files
- 🔍 **Auto-Detection**: Intelligently identifies key columns (Status, Progress, Dates, Categories, Amounts)
- 📊 **Dynamic Charts**: Generates relevant visualizations (horizontal bar, column, line, doughnut)
- 🤖 **AI Chatbot**: Ask natural language questions about your data using local Ollama
- 📈 **KPI Cards**: Professional 5-column KPI strip with percentages and insights
- 📋 **Data Table**: Full interactive data table with status badges and progress bars
- 🎨 **Professional UI**: Dark theme, responsive design, self-contained HTML dashboards

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- Ollama running locally (`ollama serve`)
- Latest llama3.1 model

### Installation

```bash
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1  # Windows
source .venv/bin/activate      # Mac/Linux

pip install -r requirements.txt
```

### Running the Backend

```bash
cd backend
.\.venv\Scripts\Activate.ps1
uvicorn main:app --reload --port 8010
```

**Backend will be available at:** `http://localhost:8010`

## 📝 How to Use

### 1. **Open Upload Page**
Go to `http://localhost:8010`

### 2. **Upload Your File**
Click "Choose File" and select:
- CSV files (.csv)
- Excel files (.xlsx, .xls)

### 3. **Dashboard Auto-Generates**
The dashboard will display:

#### **KPI Strip (5 Cards)**
- **Total Tasks** - Record count + context
- **Completed** - Count + completion %
- **In Progress** - Count + % of tasks
- **Not Started** - Count + % needing attention
- **Total Days/Amount** - With averages

#### **Charts (2-Column Grid)**
- **Horizontal Bar Chart** - Category vs Amount/Days
- **Column Chart** - Status distribution or monthly trends
- **Line Chart** - Trends over time
- **Doughnut Chart** - Status breakdown

#### **Data Table**
- Full dataset with all columns
- Status badges (Completed: green, In Progress: orange, Not Started: purple)
- Progress bars for numeric columns (0-100%)
- Hover effects for better UX

#### **Chatbot Sidebar**
- Ask questions about the data
- Powered by Ollama (local, no API costs)
- 4 quick suggestion chips
- Message history

## 🏗️ Project Structure

```
backend/
├── main.py                 # FastAPI server & endpoints
├── file_processor.py       # Data profiling & analysis
├── html_generator.py       # Dashboard HTML generation
├── ollama_chat.py          # Ollama LLM integration
├── requirements.txt        # Python dependencies
├── .venv/                  # Virtual environment
└── uploads/                # Uploaded files storage
```

## 🔌 API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| `GET` | `/` | Upload page with inline HTML form |
| `POST` | `/upload` | Upload and analyze file |
| `GET` | `/dashboard` | Generate and serve dashboard HTML |
| `POST` | `/api/chat` | Chat with Ollama about loaded data |
| `GET` | `/api/health` | Backend health check |

## 💡 How Data Processing Works

### 1. **Auto-Detection**
The backend automatically detects:
- **Status columns**: Looking for "status", "state", "stage", "phase" keywords
- **Category columns**: "category", "type", "department", "project", "team"
- **Date columns**: "date", "start", "end", "created", "updated"
- **Amount columns**: "amount", "revenue", "total", "value", "price", "days"
- **Progress columns**: Numeric 0-1 or 0-100 ranges

### 2. **Data Profiling**
For each dataset:
- Numeric stats: min, max, mean, sum, std, median
- Categorical analysis: unique values, top 15 categories
- Date ranges and durations
- Sample rows (first 5 records)

### 3. **KPI Generation**
- **Completed Count** + completion percentage
- **In Progress Count** + percentage of all tasks
- **Not Started Count** + percentage needing attention
- **Total Amount/Days** with category averages
- All automatically calculated from the data

### 4. **Chart Generation**
5 different chart configs based on detected columns:
- Category vs Amount (horizontal bar)
- Status distribution (doughnut)
- Category vs Progress (bar)
- Trend over time (line)
- Category record count (bar)

## 🤖 Ollama Integration

### Requirements
1. **Install Ollama**: https://ollama.ai
2. **Download Model**: `ollama pull llama3.1` (or mistral, deepseek-r1)
3. **Run Ollama**: `ollama serve`

### Chat Features
- Context includes full dataset profile
- Maintains message history (last 10 messages)
- Auto-generates 3 business insights on dashboard load
- Fallback responses if Ollama unavailable

## 🎨 Design Specifications

### Color Scheme
- **Background**: `#0f1117` (dark navy)
- **Cards**: `#1a1d2e` (darker blue)
- **Text**: `#e2e8f0` (light gray)
- **Accent**: `#4f46e5` (indigo)
- **Success**: `#10b981` (green)
- **Warning**: `#fb923c` (orange)
- **Danger**: `#f87171` (red)
- **Borders**: `#2d3748` (subtle gray)

### Typography
- **Font**: System UI (Segoe UI, Roboto, -apple-system)
- **KPI Values**: 36px bold
- **KPI Labels**: 13px regular
- **KPI Details**: 12px muted
- **Chart Titles**: 13px bold uppercase

## 📦 Dependencies

```
fastapi              # Web framework
uvicorn              # ASGI server
pandas               # Data analysis
numpy                # Numerical computing
openpyxl             # Excel reading
xlrd                 # Legacy Excel support (.xls)
python-multipart     # File upload handling
python-dotenv        # Environment variables
httpx                # Async HTTP client
pydantic             # Data validation
```

## 🔧 Configuration

### Environment Variables
Create `.env` file in backend folder:

```env
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1
UPLOAD_DIR=./uploads
```

### Ollama Models Tested
- `llama3.1:latest` ✅ Recommended
- `mistral:7b` ✅ Fast & accurate
- `deepseek-r1:8b` ✅ Detailed responses
- `qwen2.5:7b` ✅ Good for project data

## 📊 Example Usage

### Upload a Project Management CSV

```
Project,Task,Status,Progress,Days
Marketing,Research,Completed,100,14
Product,Design,In Progress,65,21
Sales,Outreach,Not Started,0,15
```

**Dashboard will show:**
- ✅ 1 Completed (33% completion)
- 🟡 1 In Progress (33% of tasks)
- ⏳ 1 Not Started (33% need attention)
- 📅 50 Total Days (avg 16.7/task)
- 📊 Charts showing breakdown by category
- 💬 Chat: "Which task is behind schedule?"

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Port 8010 in use** | `netstat -ano \| findstr :8010` → kill process |
| **Ollama not responding** | Run `ollama serve` in another terminal |
| **Excel import fails** | Install: `pip install xlrd openpyxl` |
| **Large file timeout** | Increase timeout in requests (main.py) |
| **Chat not working** | Check Ollama is running & `llama3.1` is downloaded |

## 📈 Performance

- **File Upload**: <1 second for typical CSVs
- **Processing**: ~2-5 seconds for 1000+ rows
- **Dashboard Generation**: ~10 seconds (includes Ollama insights)
- **Chart Rendering**: Instant (Chart.js)
- **Data Table**: Smooth scrolling for 1000+ rows

## 🎯 Next Steps

1. ✅ Upload your CSV/Excel files
2. ✅ Ask the chatbot questions
3. ✅ Export dashboards as HTML (save from browser)
4. ✅ Customize KPI calculations in `file_processor.py`
5. ✅ Add more chart types in `html_generator.py`

## 📄 License

MIT License - Feel free to modify and use!

## 🤝 Support

For issues or improvements, check the backend error logs:
```bash
uvicorn main:app --reload --port 8010 --log-level debug
```

---

**Ready to analyze your data? 🚀 Go to http://localhost:8010**
