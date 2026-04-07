from __future__ import annotations

import json
from typing import Any, Dict, List


def generate_html(profile: dict, charts: list, df, insights: list, suggestions: list) -> str:
    # Embed full records for table + filtering
    df_records = df.fillna("").to_dict(orient="records")

    # Profile summary safe for JSON
    auto = profile.get("auto", {}) or {}
    profile_summary = {
        "filename": profile.get("filename"),
        "rows": profile.get("rows"),
        "columns": profile.get("columns", []),
        "kpis": profile.get("kpis", []),
        "category_col": auto.get("category_col"),
        "status_col": auto.get("status_col"),
        "progress_col": auto.get("progress_col"),
        "pct_col": auto.get("pct_col"),
        "amount_col": auto.get("amount_col"),
        "date_col": auto.get("date_col"),
    }

    kpis = (profile.get("kpis") or [])[:5]
    # Pad to exactly 5 cards for layout consistency
    while len(kpis) < 5:
        kpis.append({"label": "", "value": "", "detail": "", "color": "blue"})

    kpi_html = "\n".join(
        [
            f"""
<div class="kpi-card kpi-{k.get('color','blue')}">
  <div class="kpi-val">{_esc(k.get('value',''))}</div>
  <div class="kpi-label">{_esc(k.get('label',''))}</div>
  <div class="kpi-detail">{_esc(k.get('detail',''))}</div>
</div>""".strip()
            for k in kpis
        ]
    )

    # Render all charts in a responsive grid layout with lazy loading support
    charts_for_row = (charts or [])
    chart_cards = []
    for i, c in enumerate(charts_for_row):
        chart_cards.append(
            f"""
<div class="chart-card" data-chart-index="{i}" data-chart-id="{_esc(c.get('id','chart'))}" data-lazy="true">
  <div class="chart-title">{_esc(c.get('title','Chart'))}</div>
  <div class="chart-insight">{_esc(c.get('insight',''))}</div>
  <div class="chart-wrap">
    <div class="skeleton-chart" id="skeleton-{_esc(c.get('id','chart'))}"></div>
    <canvas id="{_esc(c.get('id','chart'))}" style="display:none"></canvas>
  </div>
</div>""".strip()
        )
    charts_html = "\n".join(chart_cards)

    category_col = auto.get("category_col")
    filter_buttons = ""
    if category_col and category_col in (profile.get("filter_values") or {}):
        vals = (profile.get("filter_values") or {}).get(category_col, []) or []
        btns = [
            '<button class="filter-btn active" onclick="filterTable(\'ALL\',this)">ALL</button>'
        ]
        for v in vals:
            safe = _esc(str(v))
            btns.append(
                f'<button class="filter-btn" onclick="filterTable({json.dumps(str(v))},this)">{safe}</button>'
            )
        filter_buttons = "\n".join(btns)

    suggestions_html = "\n".join(
        [f'<span class="chip" onclick="askChip(this)">{_esc(s)}</span>' for s in (suggestions or [])[:6]]
    )

    insights_for_table = ""
    if insights:
        # Put first insight into the table insight line (like screenshot style)
        insights_for_table = str(insights[0])

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{_esc(profile.get("filename","Dashboard"))} — Dashboard</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    :root {{
      --bg: #0f1117;
      --card: #1a1d2e;
      --border: #2d3748;
      --accent: #4f46e5;
      --text: #e2e8f0;
      --muted: #64748b;
      --blue: #60a5fa;
      --green: #34d399;
      --amber: #fbbf24;
      --red: #f87171;
      --purple: #a78bfa;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      background: var(--bg);
      color: var(--text);
      font-family: 'Segoe UI', system-ui, sans-serif;
      height: 100vh;
      display: flex;
      flex-direction: column;
      overflow: hidden;
    }}

    .kpi-strip {{
      display: grid;
      grid-template-columns: repeat(5, 1fr);
      gap: 12px;
      padding: 12px 16px;
      flex-shrink: 0;
    }}
    .kpi-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px 16px;
      min-height: 74px;
      animation: fadeIn 0.4s ease-in-out;
    }}
    @keyframes fadeIn {{
      from {{ opacity: 0; transform: translateY(4px); }}
      to {{ opacity: 1; transform: translateY(0); }}
    }}
    
    /* Skeleton Loaders */
    .skeleton {{
      background: linear-gradient(90deg, #1a1d2e 25%, #2d3748 50%, #1a1d2e 75%);
      background-size: 200% 100%;
      animation: skeleton-loading 1.5s infinite;
    }}
    @keyframes skeleton-loading {{
      0% {{ background-position: 200% 0; }}
      100% {{ background-position: -200% 0; }}
    }}
    .skeleton-kpi {{
      background: linear-gradient(90deg, #1a1d2e 25%, #2d3748 50%, #1a1d2e 75%);
      background-size: 200% 100%;
      animation: skeleton-loading 1.5s infinite;
      min-height: 74px;
      border-radius: 10px;
    }}
    .skeleton-chart {{
      background: linear-gradient(90deg, #1a1d2e 25%, #2d3748 50%, #1a1d2e 75%);
      background-size: 200% 100%;
      animation: skeleton-loading 1.5s infinite;
      height: 220px;
      border-radius: 10px;
      margin-bottom: 4px;
      position: relative;
      overflow: hidden;
    }}
    .skeleton-chart::after {{
      content: '';
      position: absolute;
      top: 50%;
      left: 50%;
      transform: translate(-50%, -50%);
      font-size: 11px;
      color: #64748b;
      opacity: 0.5;
    }}
    .skeleton-row {{
      display: flex;
      gap: 10px;
      padding: 8px 10px;
      border-bottom: 1px solid #1e293b20;
    }}
    .skeleton-cell {{
      background: linear-gradient(90deg, #1a1d2e 25%, #2d3748 50%, #1a1d2e 75%);
      background-size: 200% 100%;
      animation: skeleton-loading 1.5s infinite;
      height: 12px;
      border-radius: 4px;
      flex: 1;
    }}
    .kpi-val {{ font-size: 28px; font-weight: 700; line-height: 1; }}
    .kpi-label {{ font-size: 12px; color: var(--muted); margin-top: 3px; }}
    .kpi-detail {{ font-size: 11px; margin-top: 5px; }}
    .kpi-blue .kpi-val {{ color: var(--blue); }}
    .kpi-blue .kpi-detail {{ color: var(--muted); }}
    .kpi-green .kpi-val {{ color: var(--green); }}
    .kpi-green .kpi-detail {{ color: var(--green); }}
    .kpi-amber .kpi-val {{ color: var(--amber); }}
    .kpi-amber .kpi-detail {{ color: var(--amber); }}
    .kpi-red .kpi-val {{ color: var(--red); }}
    .kpi-red .kpi-detail {{ color: var(--red); }}
    .kpi-purple .kpi-val {{ color: var(--purple); }}
    .kpi-purple .kpi-detail {{ color: var(--muted); }}

    .main {{
      display: flex;
      flex: 1;
      overflow: hidden;
      min-height: 0;
    }}
    .left-panel {{
      flex: 1;
      overflow-y: auto;
      padding: 0 12px 16px;
    }}
    .right-panel {{
      width: 340px;
      flex-shrink: 0;
      background: var(--card);
      border-left: 1px solid var(--border);
      display: flex;
      flex-direction: column;
    }}

    .charts-row {{
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 12px;
      margin-bottom: 12px;
    }}
    .chart-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px;
      animation: fadeIn 0.4s ease-in-out;
    }}
    .chart-title {{
      font-size: 12px;
      font-weight: 600;
      color: var(--text);
      margin-bottom: 4px;
    }}
    .chart-insight {{
      font-size: 11px;
      color: #60a5fa;
      border-left: 2px solid var(--accent);
      padding-left: 8px;
      margin-bottom: 10px;
      line-height: 1.4;
    }}
    .chart-wrap {{ position: relative; height: 220px; }}

    .filter-row {{
      display: flex;
      gap: 6px;
      flex-wrap: wrap;
      margin-bottom: 10px;
      padding-top: 4px;
    }}
    .filter-btn {{
      font-size: 11px;
      padding: 4px 12px;
      border-radius: 20px;
      cursor: pointer;
      border: 1px solid var(--border);
      background: transparent;
      color: var(--muted);
      transition: all 0.15s;
    }}
    .filter-btn:hover {{ border-color: var(--accent); color: #a5b4fc; }}
    .filter-btn.active {{ background: var(--accent); color: white; border-color: var(--accent); }}

    .table-card {{
      background: var(--card);
      border: 1px solid var(--border);
      border-radius: 10px;
      padding: 14px;
      animation: fadeIn 0.4s ease-in-out;
    }}
    .table-header {{ margin-bottom: 6px; }}
    .table-title {{ font-size: 13px; font-weight: 600; }}
    .table-insight {{
      font-size: 11px;
      color: #60a5fa;
      border-left: 2px solid var(--accent);
      padding-left: 8px;
      margin: 4px 0 10px;
      line-height: 1.4;
    }}
    .table-scroll {{
      overflow-x: auto;
      max-height: 300px;
      overflow-y: auto;
    }}
    table {{ width: 100%; border-collapse: collapse; font-size: 11.5px; }}
    th {{
      padding: 7px 10px;
      text-align: left;
      border-bottom: 1px solid var(--border);
      color: var(--muted);
      font-weight: 500;
      white-space: nowrap;
      position: sticky;
      top: 0;
      background: var(--card);
      z-index: 1;
    }}
    td {{
      padding: 6px 10px;
      color: #cbd5e1;
      border-bottom: 1px solid #1e293b20;
      white-space: nowrap;
    }}
    tr:hover td {{ background: #1e293b40; }}
    tr:nth-child(even) td {{ background: #0f172a30; }}

    .badge {{
      padding: 2px 8px;
      border-radius: 20px;
      font-size: 10px;
      font-weight: 600;
      white-space: nowrap;
      display: inline-block;
    }}
    .badge-green {{ background: #064e3b; color: #34d399; }}
    .badge-amber {{ background: #451a03; color: #fbbf24; }}
    .badge-indigo {{ background: #1e1b4b; color: #818cf8; }}
    .badge-red {{ background: #450a0a; color: #f87171; }}
    .badge-gray {{ background: #1e293b; color: #94a3b8; }}

    .prog-wrap {{
      background: #1e293b;
      border-radius: 4px;
      height: 6px;
      width: 80px;
      display: inline-block;
      vertical-align: middle;
      overflow: hidden;
    }}
    .prog-fill {{ height: 6px; border-radius: 4px; }}
    .prog-green {{ background: #34d399; }}
    .prog-amber {{ background: #fbbf24; }}
    .prog-gray {{ background: #475569; }}

    .chat-header {{
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
      flex-shrink: 0;
    }}
    .chat-header-top {{ display: flex; align-items: center; gap: 7px; }}
    .chat-dot {{ width: 8px; height: 8px; border-radius: 50%; background: #34d399; flex-shrink: 0; }}
    .chat-title {{ font-size: 13px; font-weight: 600; }}
    .chat-sub {{ font-size: 10px; color: var(--muted); margin-top: 2px; padding-left: 15px; }}
    .messages {{
      flex: 1;
      overflow-y: auto;
      padding: 12px;
      display: flex;
      flex-direction: column;
      gap: 8px;
    }}
    .msg {{
      padding: 9px 12px;
      border-radius: 10px;
      font-size: 12.5px;
      line-height: 1.55;
      max-width: 92%;
    }}
    .msg-bot {{
      background: #0f172a;
      border: 1px solid var(--border);
      color: #cbd5e1;
      align-self: flex-start;
      border-radius: 4px 10px 10px 10px;
    }}
    .msg-user {{
      background: var(--accent);
      color: white;
      align-self: flex-end;
      border-radius: 10px 4px 10px 10px;
    }}
    .msg-thinking {{ color: var(--muted); font-style: italic; }}
    .chips {{
      display: flex;
      flex-wrap: wrap;
      gap: 5px;
      padding: 6px 12px;
      border-top: 1px solid #1e293b;
    }}
    .chip {{
      font-size: 10.5px;
      padding: 4px 9px;
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 20px;
      cursor: pointer;
      color: #94a3b8;
      transition: all 0.15s;
      user-select: none;
    }}
    .chip:hover {{ border-color: var(--accent); color: #a5b4fc; }}
    .input-row {{
      display: flex;
      gap: 7px;
      padding: 9px 12px;
      border-top: 1px solid var(--border);
      flex-shrink: 0;
    }}
    .chat-input {{
      flex: 1;
      background: #0f172a;
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 7px 11px;
      font-size: 12.5px;
      color: var(--text);
      outline: none;
      resize: none;
      font-family: inherit;
    }}
    .chat-input:focus {{ border-color: var(--accent); }}
    .send-btn {{
      padding: 7px 16px;
      background: var(--accent);
      color: white;
      border: none;
      border-radius: 8px;
      font-size: 13px;
      cursor: pointer;
      font-weight: 500;
    }}
    .send-btn:disabled {{ opacity: 0.4; cursor: default; }}

    ::-webkit-scrollbar {{ width: 4px; height: 4px; }}
    ::-webkit-scrollbar-thumb {{ background: #2d3748; border-radius: 4px; }}

    @media (max-width: 1100px) {{
      .right-panel {{ display: none; }}
      .charts-row {{ grid-template-columns: 1fr; }}
      .kpi-strip {{ grid-template-columns: repeat(2, 1fr); }}
    }}
  </style>
</head>
<body>
<div class="kpi-strip" id="kpi-strip">
    {kpi_html}
    </div>
    
    <!-- KPI Skeleton Loaders (shown during initial load) -->
    <div class="kpi-strip skeleton-kpi-strip" id="skeleton-kpi-strip" style="display:none">
      <div class="skeleton-kpi"></div>
      <div class="skeleton-kpi"></div>
      <div class="skeleton-kpi"></div>
      <div class="skeleton-kpi"></div>
      <div class="skeleton-kpi"></div>
  </div>

  <div class="main">
    <div class="left-panel">
      <div class="charts-row" id="charts-row">
        {charts_html}
      </div>

      <div class="filter-row" id="filter-row">
        {filter_buttons}
      </div>

      <div class="table-card">
        <div class="table-header">
          <div class="table-title" id="table-title">All records — {_esc(str(profile.get("rows",0)))} rows</div>
          <div class="table-insight" id="table-insight">{_esc(insights_for_table or "Showing all · click a filter above to drill down")}</div>
        </div>
        <div class="table-scroll">
          <!-- Table Skeleton Loader -->
          <div id="skeleton-table">
            <div class="skeleton-row">
              <div class="skeleton-cell" style="width: 15%"></div>
              <div class="skeleton-cell" style="width: 20%"></div>
              <div class="skeleton-cell" style="width: 25%"></div>
              <div class="skeleton-cell" style="width: 20%"></div>
            </div>
            <div class="skeleton-row">
              <div class="skeleton-cell" style="width: 15%"></div>
              <div class="skeleton-cell" style="width: 20%"></div>
              <div class="skeleton-cell" style="width: 25%"></div>
              <div class="skeleton-cell" style="width: 20%"></div>
            </div>
            <div class="skeleton-row">
              <div class="skeleton-cell" style="width: 15%"></div>
              <div class="skeleton-cell" style="width: 20%"></div>
              <div class="skeleton-cell" style="width: 25%"></div>
              <div class="skeleton-cell" style="width: 20%"></div>
            </div>
          </div>
          <!-- Actual Table (shown after load) -->
          <table id="data-table" style="display:none">
            <thead>
              <tr>
                {''.join([f"<th>{_esc(str(c).replace('_',' ').title())}</th>" for c in (profile.get('columns') or [])])}
              </tr>
            </thead>
            <tbody id="table-body"></tbody>
          </table>
        </div>
      </div>
    </div>

    <div class="right-panel">
      <div class="chat-header">
        <div class="chat-header-top">
          <div class="chat-dot"></div>
          <div class="chat-title">Ask about your data</div>
        </div>
        <div class="chat-sub">Powered by Ollama · {_esc(profile.get("filename",""))}</div>
      </div>
      <div class="messages" id="messages"></div>
      <div class="chips" id="chips">
        {suggestions_html}
      </div>
      <div class="input-row">
        <textarea class="chat-input" id="chatInput" rows="2" placeholder="Ask about tasks, projects, progress..."></textarea>
        <button class="send-btn" id="sendBtn">Send</button>
      </div>
    </div>
  </div>

  <script>
    const ALL_DATA = {json.dumps(df_records, ensure_ascii=False, default=str)};
    const PROFILE = {json.dumps(profile_summary, ensure_ascii=False, default=str)};
    const CHARTS_DATA = {json.dumps(charts or [], ensure_ascii=False, default=str)};
    const CONTEXT = {json.dumps(str(profile.get("context_text","")), ensure_ascii=False)};
    const FILENAME = {json.dumps(str(profile.get("filename","")), ensure_ascii=False)};

    Chart.defaults.color = '#64748b';
    Chart.defaults.font.family = "'Segoe UI', system-ui";
    Chart.defaults.font.size = 11;

    const COLORS = [
      '#4f46e5','#06b6d4','#f59e0b','#10b981',
      '#f43f5e','#8b5cf6','#fb923c','#ec4899',
      '#14b8a6','#a78bfa','#34d399','#60a5fa',
      '#fbbf24','#f87171','#818cf8'
    ];

    function initChart(c) {{
      const canvas = document.getElementById(c.id);
      if (!canvas || !c.data || c.data.length === 0) return;

      const labels = c.data.map(r => String(r[c.x_key] || ''));
      const values = c.data.map(r => Number(r[c.y_key]) || 0);

      const bgColors = values.map((_,i) => COLORS[i % COLORS.length] + '33');
      const borderColors = values.map((_,i) => COLORS[i % COLORS.length]);

      if (c.type === 'doughnut') {{
        new Chart(canvas, {{
          type: 'doughnut',
          data: {{
            labels: labels,
            datasets: [{{
              data: values,
              backgroundColor: COLORS.slice(0, values.length).map(c => c + '99'),
              borderColor: COLORS.slice(0, values.length),
              borderWidth: 1,
              hoverOffset: 4
            }}]
          }},
          options: {{
            responsive: true, maintainAspectRatio: false,
            cutout: '65%',
            plugins: {{
              legend: {{ position:'bottom', labels:{{padding:10, boxWidth:10, font:{{size:10}}}} }},
              tooltip: {{ callbacks: {{ label: ctx => ` ${{ctx.label}}: ${{ctx.raw}}` }} }}
            }}
          }}
        }});
        return;
      }}

      const isLine = c.type === 'line' || c.type === 'area';
      const isHorizontal = c.type === 'horizontalBar';
      const chartType = isLine ? 'line' : 'bar';

      const dataset = {{
        data: values,
        backgroundColor: isLine ? '#4f46e520' : bgColors,
        borderColor: isLine ? '#4f46e5' : borderColors,
        borderWidth: 1,
        borderRadius: isLine ? 0 : 4,
        fill: c.type === 'area',
        tension: 0.3,
        pointRadius: isLine ? 3 : 0,
      }};

      const chartConfig = {{
        type: chartType,
        data: {{ labels: labels, datasets: [dataset] }},
        options: {{
          indexAxis: isHorizontal ? 'y' : 'x',
          responsive: true, maintainAspectRatio: false,
          plugins: {{
            legend: {{ display: false }},
            tooltip: {{
              backgroundColor: '#0f172a',
              borderColor: '#1e293b',
              borderWidth: 1,
              callbacks: {{ label: ctx => ` ${{ctx.raw}}` }}
            }}
          }},
          scales: {{
            x: {{
              grid: {{ display: false }},
              ticks: {{
                maxRotation: 45,
                font: {{ size: 10 }},
                callback: (val, idx) => {{
                  const label = (isHorizontal ? labels[idx] : labels[idx]) || '';
                  return label.length > 12 ? label.slice(0,12)+'...' : label;
                }}
              }}
            }},
            y: {{
              grid: {{ color: '#1e293b' }},
              ticks: {{
                font: {{ size: 10 }},
                callback: v => {{
                  if (v >= 1000000) return (v/1000000).toFixed(1)+'M';
                  if (v >= 1000) return (v/1000).toFixed(1)+'K';
                  return v;
                }}
              }}
            }}
          }}
        }}
      }};

      new Chart(canvas, chartConfig);

    const STATUS_COL = PROFILE.status_col;
    const CATEGORY_COL = PROFILE.category_col;
    const PROGRESS_COLS = [PROFILE.progress_col, PROFILE.pct_col].filter(Boolean);

    function getStatusBadgeClass(val) {{
      const v = String(val).toLowerCase();
      if (/complet|done|finish|success/.test(v)) return 'badge-green';
      if (/progress|active|running|ongoing|work/.test(v)) return 'badge-amber';
      if (/start|pending|todo|new|wait|not/.test(v)) return 'badge-indigo';
      if (/fail|cancel|block|error/.test(v)) return 'badge-red';
      return 'badge-gray';
    }}

    function getProgressBarHTML(val) {{
      const n = Number(val);
      const pct = n <= 1 ? n * 100 : n;
      const cls = pct >= 100 ? 'prog-green' : pct > 0 ? 'prog-amber' : 'prog-gray';
      return `<div style="display:flex;align-items:center;gap:6px">
        <div class="prog-wrap">
          <div class="prog-fill ${{cls}}" style="width:${{Math.min(pct,100)}}%"></div>
        </div>
        <span style="font-size:10px;color:#64748b">${{Math.round(pct)}}%</span>
      </div>`;
    }}

    function escHtml(s) {{
      return String(s ?? '')
        .replaceAll('&', '&amp;')
        .replaceAll('<', '&lt;')
        .replaceAll('>', '&gt;')
        .replaceAll('"', '&quot;')
        .replaceAll("'", '&#39;');
    }}

    function renderTable(rows) {{
      const tbody = document.getElementById('table-body');
      const cols = PROFILE.columns || [];
      tbody.innerHTML = (rows || []).map((row) => {{
        const cells = cols.map(col => {{
          const val = (row && (row[col] ?? '')) ?? '';
          if (STATUS_COL && col === STATUS_COL) {{
            const cls = getStatusBadgeClass(val);
            return `<td><span class="badge ${{cls}}">${{escHtml(val)}}</span></td>`;
          }}
          if (PROGRESS_COLS.includes(col) && val !== '') {{
            const n = parseFloat(val);
            if (!isNaN(n)) return `<td>${{getProgressBarHTML(n)}}</td>`;
          }}
          if (CATEGORY_COL && col === CATEGORY_COL) {{
            return `<td style="color:#a5b4fc;font-size:11px">${{escHtml(val)}}</td>`;
          }}
          return `<td>${{escHtml(val)}}</td>`;
        }}).join('');
        return `<tr>${{cells}}</tr>`;
      }}).join('');

      document.getElementById('table-title').textContent = `All records — ${{(rows||[]).length}} rows`;
    }}

    let currentFilter = 'ALL';
    function filterTable(value, btn) {{
      currentFilter = value;
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      if (btn) btn.classList.add('active');
      const rows = (value === 'ALL' || !CATEGORY_COL) ? ALL_DATA : ALL_DATA.filter(r => String(r[CATEGORY_COL] || '') === String(value));
      renderTable(rows);
      const insight = (value === 'ALL' || !CATEGORY_COL) ? 'Showing all · click a filter above to drill down' : `${{value}}: ${{rows.length}} records`;
      document.getElementById('table-insight').textContent = insight;
    }}

    let chatHistory = [];
    function addMsg(role, html) {{
      const msgs = document.getElementById('messages');
      const div = document.createElement('div');
      div.className = `msg msg-${{role === 'user' ? 'user':'bot'}}`;
      div.innerHTML = html;
      msgs.appendChild(div);
      msgs.scrollTop = msgs.scrollHeight;
      return div;
    }}

    window.addEventListener('DOMContentLoaded', () => {{
      // Show all data immediately - no waiting
      const tableSkeleton = document.getElementById('skeleton-table');
      const dataTable = document.getElementById('data-table');
      if (tableSkeleton) tableSkeleton.remove();
      if (dataTable) dataTable.style.display = '';
      
      renderTable(ALL_DATA);

      // Render all charts immediately (no recursive delays)
      setTimeout(() => {{
        const charts = CHARTS_DATA || [];
        charts.forEach((chart, index) => {{
          try {{
            const skeleton = document.getElementById(`skeleton-${{chart.id}}`);
            const canvas = document.getElementById(chart.id);
            
            if (skeleton) skeleton.style.display = 'none';
            if (canvas) canvas.style.display = '';
            
            setTimeout(() => {{
              initChart(chart);
            }}, index * 50); // Stagger by 50ms per chart
          }} catch (e) {{
            console.error(`Chart ${{chart.id}} error:`, e);
          }}
        }});
      }}, 150);

      // Show welcome message with initial insights
      const kpis = PROFILE.kpis || [];
      const k1 = kpis[0] || {{}};
      const k2 = kpis[1] || {{}};
      const k3 = kpis[3] || {{}};
      addMsg('bot', `Hi! I've analysed your <strong>${{escHtml(FILENAME)}}</strong>.<br><br>
        <strong style="color:#60a5fa">${{escHtml(k1.value || '')}} ${{escHtml(k1.label || '')}}</strong> — ${{escHtml(k1.detail || '')}}.<br>
        <strong style="color:#34d399">${{escHtml(k2.value || '')}} ${{escHtml(k2.label || '')}}</strong> ·
        <strong style="color:#f87171">${{escHtml(k3.value || '')}} ${{escHtml(k3.label || '')}}</strong>.<br><br>
        Ask me anything about the data!`);
    }});

    async function sendMessage(text) {{
      const input = document.getElementById('chatInput');
      const msg = text || (input.value || '').trim();
      if (!msg) return;
      input.value = '';

      const sendBtn = document.getElementById('sendBtn');
      sendBtn.disabled = true;
      const chips = document.getElementById('chips');
      if (chips) chips.style.display = 'none';

      addMsg('user', escHtml(msg));
      const thinking = addMsg('bot', '<span class="msg-thinking">Thinking...</span>');
      chatHistory.push({{role:'user', content: msg}});

      try {{
        const r = await fetch('/api/chat', {{
          method: 'POST',
          headers: {{'Content-Type':'application/json'}},
          body: JSON.stringify({{ message: msg, history: chatHistory.slice(-8) }})
        }});
        const d = await r.json();
        const reply = d.reply || d.answer || 'No response';
        thinking.innerHTML = String(reply)
          .replace(/\\*\\*(.*?)\\*\\*/g,'<strong>$1</strong>')
          .replace(/\\n/g,'<br>');
        chatHistory.push({{role:'assistant', content: String(reply)}});
      }} catch(e) {{
        thinking.innerHTML = `<span style="color:#f87171">Error connecting to backend: ${{escHtml(e.message)}}</span>`;
      }} finally {{
        sendBtn.disabled = false;
      }}
    }}

    function askChip(el) {{
      sendMessage((el.textContent || '').trim());
    }}

    document.getElementById('sendBtn').addEventListener('click', () => {{ sendMessage(); }});
    document.getElementById('chatInput').addEventListener('keydown', e => {{
      if (e.key === 'Enter' && !e.shiftKey) {{
        e.preventDefault();
        sendMessage();
      }}
    }});
  </script>
</body>
</html>"""


def _esc(v: Any) -> str:
    s = "" if v is None else str(v)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&#39;")
    )

