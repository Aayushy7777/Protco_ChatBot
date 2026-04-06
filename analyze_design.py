import httpx

# Analyze the dashboard design using Ollama
prompt = """Analyze this project management dashboard design and extract key UI/UX specifications:

Key Components Visible:
1. KPI Strip (top): 5 cards showing metrics (46 Total Tasks, 9 Completed, 15 In Progress, 22 Not Started, 1,267 Total Days Planned)
2. Main Content Grid (2 columns):
   - Left: Charts section with 2 Chart.js visualizations
     - "Total days planned per project" (horizontal bar chart)
     - "Tasks started by month" (bar/column chart with monthly trends)
   - Right: Chatbot sidebar (360px width)
     - "Ask about your data" heading with green status indicator
     - Chat message history
     - Suggestion chips (4 chips): Questions about projects/tasks/progress
3. Full-width data table: "All tasks — 46 tasks"
   - Columns: Project, Task, Assigned To, Start, End, Days, Progress, Status
   - Status badges: Completed (green), In Progress (orange), Not Started (purple)
   - Progress bars showing completion percentage
   
Color Scheme:
- Background: #0f1117 (dark navy)
- Cards: #1a1d2e (darker blue)
- Text: #e2e8f0 (light gray)
- Accent Blue: #4f46e5 (indigo)
- Status Green: #10b981
- Status Orange: #fb923c
- Status Purple: #a855f7
- Borders: #2d3748

Generate JSON with these specifications for React component implementation."""

response = httpx.post(
    "http://localhost:11434/api/generate",
    json={"model": "llama3.1", "prompt": prompt, "stream": False},
    timeout=60
)

result = response.json()["response"]
print("=" * 70)
print("DASHBOARD UI/UX ANALYSIS FROM LLAMA:")
print("=" * 70)
print(result)
