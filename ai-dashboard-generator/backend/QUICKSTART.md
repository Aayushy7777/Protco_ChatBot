# 🚀 AI Dashboard Backend - Quick Start Guide

## ⚡ Fastest Way to Get Running (2 minutes)

### Step 1: Start Ollama (First Time Only)

**If you haven't installed Ollama yet:**
1. Download: https://ollama.ai
2. Install and run

**In a terminal, start Ollama:**
```bash
ollama serve
```

**In another terminal, download the model (first time only):**
```bash
ollama pull llama3.1
```

### Step 2: Start Backend

**Desktop Windows Users:**
- Double-click: `start-backend.bat`

**Terminal Users:**
```bash
cd backend
.\.venv\Scripts\activate.ps1
uvicorn main:app --reload --port 8010
```

### Step 3: Use Dashboard

Open browser: **http://localhost:8010**

---

## 📋 What Gets Auto-Generated

When you upload a CSV or Excel file, you get:

### 1️⃣ KPI Strip (5 Cards)
```
[Total Tasks: 46]  [Completed: 9]  [In Progress: 15]  [Not Started: 22]  [Total Days: 1267]
  across projects     19.6% rate      32.6% of tasks      47.8% attention    27.5 avg days
```

### 2️⃣ Charts (Automatically Generated)
- Horizontal bar chart (by category)
- Column chart (by status)
- Line chart (trends)
- Doughnut chart (distribution)

### 3️⃣ Data Table
- Full dataset with all columns
- Status badges (✅ Completed, 🟡 In Progress, ⏳ Not Started)
- Progress bars for numeric values
- Sortable columns

### 4️⃣ AI Chatbot
- Ask questions about your data
- Powered by local Ollama (no API costs!)
- Example questions:
  - "What's the status of the marketing project?"
  - "Which tasks are behind schedule?"
  - "Show me the completion rate by category"

---

## 📁 What You Need in Your CSV/Excel

The backend automatically detects these columns:

| Type | Looks For | Examples |
|------|-----------|----------|
| **Status** | status, state, stage, phase | "Completed", "In Progress", "Not Started" |
| **Progress** | progress, completion, completion_percentage | 0.0-1.0 or 0-100 |
| **Category** | category, type, project, department, team | "Marketing", "Product", "Sales" |
| **Date** | date, start_date, due_date, created | 2024-01-15 |
| **Amount** | amount, total, days, revenue, hours | 100, 50.5 |

**Minimal Example:**
```csv
Project,Task,Status,Days
Marketing,Research,Completed,14
Product,Design,In Progress,21
Sales,Outreach,Not Started,15
```

---

## 🔧 Customization

### Add Your Own Models
Edit `file_processor.py` (`build_kpis()` function):

```python
def build_kpis(df):
    # Customize KPI generation here
    # Add your own metrics or calculations
```

### Add Chart Types
Edit `html_generator.py` (`build_charts()` function):

```python
# Add new Chart.js config types
# (line, scatter, radar, etc.)
```

### Change Colors
Edit `html_generator.py` (search for color definitions):

```python
kpi_colors = {
    'blue': '#4f46e5',
    'green': '#10b981',
    # Add your colors
}
```

---

## 🐛 Troubleshooting

### Backend Won't Start
```bash
# Check if port 8010 is in use
netstat -ano | findstr :8010
# Kill the process if needed
taskkill /PID <PID> /F
```

### Ollama Not Responding
```bash
# In a new terminal, start Ollama
ollama serve
```

### Missing Model
```bash
# Download the model
ollama pull llama3.1
```

### Excel/CSV Won't Upload
```bash
# Make sure dependencies are installed
pip install -r requirements.txt
```

---

## 📊 Example Projects to Try

### 1. Project Management
```csv
project_name,task_name,status,progress,start_date,due_date,assigned_to,days_spent
Website,Design,Completed,100,2024-01-01,2024-01-14,John,14
Website,Development,In Progress,65,2024-01-15,2024-02-04,Jane,21
Website,Testing,Not Started,0,2024-02-05,2024-02-15,Bob,15
```

### 2. Sales Pipeline
```csv
company,contact,stage,value,probability,owner,days_in_stage
TechCorp,John Doe,Proposal,50000,80,Alice,30
StartupX,Jane Smith,Demo,75000,40,Bob,15
MegaCo,Mike Johnson,Qualified,100000,20,Charlie,60
```

### 3. Product Roadmap
```csv
feature,status,priority,effort_days,dependencies,category
Auth,Completed,High,21,None,Backend
API,In Progress,High,35,Auth,Backend
Dashboard,Not Started,Medium,14,API,Frontend
Reports,Planned,Low,28,API Dashboard,Frontend
```

---

## 💡 Pro Tips

1. **Column Headers Don't Matter** - The backend detects content, not headers
   ```csv
   Proj | Assignment | State | % Done | Days
   # Auto-detected as: project | task | status | progress | amount
   ```

2. **Status Values Are Auto-Detected**
   - Completed: ✅, done, finished, closed, resolved
   - In Progress: 🟡, pending, active, wip, ongoing
   - Not Started: ⏳, todo, backlog, planned, new

3. **Large Files Work Fine**
   - Tested up to 10,000+ rows
   - Processing takes 2-5 seconds

4. **Export Dashboards**
   - Right-click → Save As HTML
   - Share with non-technical users
   - Works offline

5. **Custom Questions**
   - Chatbot learns from your data context
   - Ask in natural language
   - Works in any language Ollama supports

---

## 🎯 Common Questions

**Q: Does it send my data to the cloud?**  
A: No! Everything runs locally. Ollama is local, no external APIs.

**Q: Can I use different Ollama models?**  
A: Yes! Try `mistral:7b`, `deepseek-r1:8b`, `qwen2.5:7b`

**Q: How do I share the dashboard?**  
A: Export as HTML file → share with anyone (no backend needed)

**Q: Can I customize the KPIs?**  
A: Yes! Edit `build_kpis()` in `file_processor.py`

---

## 🚀 Next Steps

1. ✅ Start Ollama: `ollama serve`
2. ✅ Start Backend: `start-backend.bat`
3. ✅ Open: http://localhost:8010
4. ✅ Upload your CSV/Excel
5. ✅ Explore the dashboard & chat!

**Enjoy your AI-powered dashboard! 🎉**

---

For detailed docs, see **README.md**
