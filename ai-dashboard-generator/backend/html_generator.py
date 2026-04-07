from __future__ import annotations

import json
from typing import Any, Dict, List


CHART_JS_COLORS = [
    "#4f46e5",
    "#06b6d4",
    "#f59e0b",
    "#10b981",
    "#f43f5e",
    "#8b5cf6",
    "#fb923c",
    "#ec4899",
    "#14b8a6",
    "#a78bfa",
]


def _esc(s: Any) -> str:
    return str(s).replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _status_badge(value: str) -> str:
    v = (value or "").lower()
    cls = "indigo"
    if any(x in v for x in ["completed", "done", "complete"]):
        cls = "green"
    elif any(x in v for x in ["in progress", "active", "running"]):
        cls = "amber"
    elif any(x in v for x in ["failed", "cancelled", "blocked"]):
        cls = "red"
    return f'<span class="badge {cls}">{_esc(value)}</span>'


def _build_table_rows(sample: List[Dict[str, Any]], columns: List[str]) -> str:
    out = []
    for row in sample[:200]:
        tds = []
        for col in columns:
            val = row.get(col, "")
            if "status" in col.lower():
                tds.append(f"<td>{_status_badge(str(val))}</td>")
            elif "progress" in col.lower() and str(val).replace(".", "", 1).isdigit():
                pct = max(0.0, min(100.0, float(val) * (100 if float(val) <= 1 else 1)))
                tds.append(
                    f'<td><div class="prog"><div class="progfill" style="width:{pct:.1f}%"></div></div><span>{pct:.1f}%</span></td>'
                )
            else:
                tds.append(f"<td>{_esc(val)}</td>")
        out.append("<tr>" + "".join(tds) + "</tr>")
    return "".join(out)


def generate_html(profile: Dict[str, Any], charts: List[Dict[str, Any]], kpis: List[Dict[str, Any]], insights: List[str]) -> str:
    columns = profile.get("columns", [])
    sample = profile.get("sample", [])
    table_rows_html = _build_table_rows(sample, columns)
    table_cols_html = "".join([f"<th>{_esc(c)}</th>" for c in columns])
    charts_json = json.dumps(charts, ensure_ascii=False, default=str)
    context_text = json.dumps(profile.get("context_text", ""))
    suggestions = [
        "What is the date range?",
        "Which category contributes the most?",
        "What is the most common status?",
        "Show key trends from this dataset.",
        "Where are the biggest risks?",
    ]
    suggestions_html = "".join([f'<button class="chip" onclick="sendMessage(\'{_esc(s)}\')">{_esc(s)}</button>' for s in suggestions])
    insights_html = "".join([f"<li>{_esc(i)}</li>" for i in insights[:3]])
    kpis_html = "".join(
        [f'<div class="kpi {k.get("color","blue")}"><div class="v">{_esc(k.get("value",""))}</div><div class="l">{_esc(k.get("label",""))}</div></div>' for k in kpis]
    )

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>{_esc(profile.get("filename","Dashboard"))} - Dashboard</title>
  <script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
  <style>
    body {{ margin:0; font-family:'Segoe UI',system-ui,sans-serif; background:#0f1117; color:#e2e8f0; }}
    * {{ box-sizing:border-box; }}
    ::-webkit-scrollbar {{ width:8px; height:8px; }} ::-webkit-scrollbar-thumb {{ background:#334155; border-radius:6px; }}
    .wrap {{ padding:16px; }}
    .header {{ display:flex; justify-content:space-between; align-items:center; margin-bottom:12px; }}
    .sub {{ color:#64748b; font-size:13px; }}
    .kpis {{ display:grid; grid-template-columns:repeat(6,minmax(0,1fr)); gap:10px; margin-bottom:12px; }}
    .kpi {{ background:#1a1d2e; border:1px solid #2d3748; border-radius:10px; padding:12px; border-left:3px solid #4f46e5; }}
    .kpi.green {{ border-left-color:#10b981; }} .kpi.amber {{ border-left-color:#f59e0b; }} .kpi.red {{ border-left-color:#f43f5e; }} .kpi.purple {{ border-left-color:#8b5cf6; }}
    .kpi .v {{ font-size:22px; font-weight:700; }} .kpi .l {{ color:#94a3b8; font-size:12px; margin-top:6px; }}
    .insights {{ background:#121827; border:1px solid #2d3748; border-left:3px solid #4f46e5; border-radius:10px; padding:10px 12px; margin-bottom:12px; }}
    .insights ul {{ margin:6px 0 0 16px; color:#cbd5e1; }}
    .main {{ display:grid; grid-template-columns:1fr 340px; gap:12px; }}
    .charts {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(320px,1fr)); gap:10px; }}
    .card {{ background:#1a1d2e; border:1px solid #2d3748; border-radius:10px; padding:10px; }}
    .card.wide {{ grid-column:1 / -1; }}
    .ctitle {{ font-weight:600; margin-bottom:6px; }} .cinsight {{ font-size:12px; color:#a5b4fc; border-left:3px solid #4f46e5; background:#4f46e51a; padding:6px 8px; margin-bottom:8px; border-radius:6px; }}
    .canvas-wrap {{ height:220px; }} .card.wide .canvas-wrap {{ height:280px; }}
    .table-card {{ grid-column:1 / -1; }}
    table {{ width:100%; border-collapse:collapse; font-size:12px; }} th,td {{ border-bottom:1px solid #2d3748; padding:8px; text-align:left; }} tbody tr:nth-child(even){{ background:#131a2a; }}
    .badge {{ padding:3px 8px; border-radius:999px; font-size:11px; }} .badge.green{{background:#065f4633;color:#6ee7b7;}} .badge.amber{{background:#78350f33;color:#fcd34d;}} .badge.indigo{{background:#312e8133;color:#a5b4fc;}} .badge.red{{background:#7f1d1d33;color:#fca5a5;}}
    .prog {{ width:90px; height:6px; background:#334155; border-radius:999px; display:inline-block; margin-right:8px; }} .progfill {{ height:6px; border-radius:999px; background:#10b981; }}
    .chat {{ background:#1a1d2e; border:1px solid #2d3748; border-radius:10px; display:flex; flex-direction:column; min-height:740px; }}
    .chat-head {{ padding:10px; border-bottom:1px solid #2d3748; }} .dot{{display:inline-block;width:8px;height:8px;border-radius:50%;background:#10b981;margin-right:6px;}}
    #messages {{ flex:1; overflow:auto; padding:10px; }} .msg{{margin-bottom:8px;padding:8px 10px;border-radius:8px;max-width:95%;white-space:pre-wrap;}}
    .msg.user{{background:#4f46e533;margin-left:auto;}} .msg.bot{{background:#0f172a;border:1px solid #2d3748;}}
    .chips{{padding:8px;display:flex;flex-wrap:wrap;gap:6px;border-top:1px solid #2d3748;}} .chip{{background:#0f172a;color:#cbd5e1;border:1px solid #334155;border-radius:999px;padding:5px 10px;font-size:11px;cursor:pointer;}}
    .chat-input {{ padding:8px; border-top:1px solid #2d3748; display:flex; gap:8px; }} textarea {{ flex:1; background:#0f172a; color:#e2e8f0; border:1px solid #334155; border-radius:8px; padding:8px; resize:none; }} button.send{{background:#4f46e5;color:white;border:none;padding:0 14px;border-radius:8px;cursor:pointer;}}
    @media (max-width:1100px) {{ .kpis{{grid-template-columns:repeat(3,minmax(0,1fr));}} .main{{grid-template-columns:1fr;}} .chat{{min-height:520px;}} }}
    @media (max-width:700px) {{ .kpis{{grid-template-columns:repeat(2,minmax(0,1fr));}} }}
  </style>
</head>
<body>
  <div class="wrap">
    <div class="header">
      <div>
        <h2 style="margin:0">{_esc(profile.get("filename","Dashboard"))}</h2>
        <div class="sub">{profile.get("rows",0)} records · {len(columns)} columns</div>
      </div>
      <div class="sub">Powered by Ollama · {_esc(profile.get("model","qwen2.5:7b"))}</div>
    </div>

    <div class="kpis">{kpis_html}</div>
    <div class="insights"><strong>AI insights</strong><ul>{insights_html}</ul></div>

    <div class="main">
      <div class="charts" id="charts"></div>
      <div class="chat">
        <div class="chat-head"><span class="dot"></span><strong>Ask about your data</strong><div class="sub">{_esc(profile.get("filename",""))}</div></div>
        <div id="messages"></div>
        <div class="chips">{suggestions_html}</div>
        <div class="chat-input"><textarea id="chatInput" rows="2" placeholder="Ask a question about this file..."></textarea><button class="send" onclick="sendMessage()">Send</button></div>
      </div>
    </div>
  </div>

  <template id="table-template">
    <div class="card table-card">
      <div class="ctitle">Data table</div>
      <input id="tableSearch" placeholder="Search rows..." style="width:100%;margin-bottom:8px;background:#0f172a;border:1px solid #334155;color:#e2e8f0;border-radius:8px;padding:8px"/>
      <div style="overflow:auto;max-height:360px">
        <table>
          <thead><tr>{table_cols_html}</tr></thead>
          <tbody id="tableBody">{table_rows_html}</tbody>
        </table>
      </div>
    </div>
  </template>

  <script>
    Chart.defaults.color = '#64748b';
    const COLORS = {json.dumps(CHART_JS_COLORS)};
    const CHARTS = {charts_json};
    const FILE_CONTEXT = {context_text};
    const RAW_ROWS = {json.dumps(sample, ensure_ascii=False, default=str)};
    const COLUMNS = {json.dumps(columns, ensure_ascii=False)};

    function colorAlpha(hex, alpha) {{
      const c = hex.replace('#','');
      const r = parseInt(c.substring(0,2), 16), g = parseInt(c.substring(2,4), 16), b = parseInt(c.substring(4,6), 16);
      return `rgba(${{r}},${{g}},${{b}},${{alpha}})`;
    }}

    function renderCharts() {{
      const host = document.getElementById('charts');
      CHARTS.forEach((c, idx) => {{
        const card = document.createElement('div');
        card.className = 'card ' + (c.wide ? 'wide' : '');
        card.innerHTML = `<div class="ctitle">${{c.title}}</div><div class="cinsight">${{c.insight}}</div><div class="canvas-wrap"><canvas id="${{c.id}}"></canvas></div>`;
        host.appendChild(card);

        const bg = c.data.map((_, i) => colorAlpha(COLORS[i % COLORS.length], 0.2));
        const br = c.data.map((_, i) => COLORS[i % COLORS.length]);
        const t = c.type === 'horizontalBar' ? 'bar' : c.type;

        new Chart(document.getElementById(c.id), {{
          type: t,
          data: {{ labels: c.labels, datasets: [{{ data: c.data, backgroundColor: bg, borderColor: br, borderWidth: 1, borderRadius: 4 }}] }},
          options: {{
            indexAxis: c.type === 'horizontalBar' ? 'y' : 'x',
            responsive: true, maintainAspectRatio: false,
            plugins: {{ legend: {{ display: false }}, tooltip: {{ backgroundColor:'#0f172a', borderColor:'#1e293b', borderWidth:1 }} }},
            scales: {{ x: {{ grid: {{ color:'#1e293b' }} }}, y: {{ grid: {{ color:'#1e293b' }} }} }}
          }}
        }});
      }});

      const t = document.getElementById('table-template').content.cloneNode(true);
      host.appendChild(t);
      setupTableFilter();
    }}

    function renderTableRows(rows) {{
      const tb = document.getElementById('tableBody');
      if (!tb) return;
      const render = (rows || []).slice(0, 200).map(r => {{
        const tds = COLUMNS.map(c => `<td>${{String(r[c] ?? '')}}</td>`).join('');
        return `<tr>${{tds}}</tr>`;
      }}).join('');
      tb.innerHTML = render;
    }}

    function setupTableFilter() {{
      const input = document.getElementById('tableSearch');
      if (!input) return;
      input.addEventListener('input', () => {{
        const q = input.value.toLowerCase().trim();
        if (!q) return renderTableRows(RAW_ROWS);
        const filtered = RAW_ROWS.filter(r => Object.values(r || {{}}).some(v => String(v).toLowerCase().includes(q)));
        renderTableRows(filtered);
      }});
    }}

    const msgEl = document.getElementById('messages');
    const inputEl = document.getElementById('chatInput');
    let history = [];

    function addMsg(role, text) {{
      const div = document.createElement('div');
      div.className = 'msg ' + (role === 'user' ? 'user' : 'bot');
      div.innerHTML = text;
      msgEl.appendChild(div);
      msgEl.scrollTop = msgEl.scrollHeight;
      return div;
    }}

    async function sendMessage(text) {{
      const msg = text || (inputEl.value || '').trim();
      if (!msg) return;
      inputEl.value = '';
      addMsg('user', msg);
      const thinking = addMsg('bot', '<em style="color:#64748b">Thinking...</em>');
      history.push({{ role:'user', content: msg }});
      try {{
        const res = await fetch('/api/chat', {{
          method: 'POST',
          headers: {{ 'Content-Type': 'application/json' }},
          body: JSON.stringify({{ message: msg, history: history.slice(-10) }})
        }});
        const data = await res.json();
        const reply = (data.reply || '').replace(/\\n/g, '<br>');
        thinking.innerHTML = reply;
        history.push({{ role:'assistant', content: data.reply || '' }});

        if ((data.intent || '') === 'TABLE' && Array.isArray(data.table_columns) && Array.isArray(data.table_data) && data.table_columns.length) {{
          const cols = data.table_columns;
          const rows = data.table_data.slice(0, 25);
          const header = '<tr>' + cols.map(c => `<th>${{String(c)}}</th>`).join('') + '</tr>';
          const body = rows.map(r => '<tr>' + cols.map(c => `<td>${{String((r||{{}})[c] ?? '')}}</td>`).join('') + '</tr>').join('');
          const tbl = `<div style="overflow:auto;max-height:260px"><table><thead>${{header}}</thead><tbody>${{body}}</tbody></table></div>`;
          addMsg('bot', tbl);
        }}

        if ((data.intent || '') === 'CHART' && data.chart_config && data.chart_config.labels && data.chart_config.data) {{
          appendChatChartCard(data.chart_config);
        }}
      }} catch (e) {{
        thinking.innerHTML = '<span style="color:#f87171">Error: ' + e.message + '</span>';
      }}
    }}

    function appendChatChartCard(cfg) {{
      const host = document.getElementById('charts');
      if (!host || !cfg) return;
      const id = 'chat_chart_' + Math.random().toString(36).slice(2, 9);
      const c = {{
        id,
        type: cfg.type || 'bar',
        title: cfg.title || 'Generated chart',
        insight: cfg.insight || 'From chat response',
        labels: (cfg.data && cfg.data.labels) ? cfg.data.labels : (cfg.labels || []),
        data: (cfg.data && cfg.data.values) ? cfg.data.values : (cfg.data || []),
        wide: String(cfg.chartStyle || '').toLowerCase().includes('horizontal')
      }};
      if (!Array.isArray(c.labels) || !Array.isArray(c.data) || !c.labels.length) return;
      CHARTS.push(c);
      const card = document.createElement('div');
      card.className = 'card ' + (c.wide ? 'wide' : '');
      card.innerHTML = `<div class="ctitle">${{c.title}}</div><div class="cinsight">${{c.insight}}</div><div class="canvas-wrap"><canvas id="${{c.id}}"></canvas></div>`;
      host.prepend(card);
      const bg = c.data.map((_, i) => colorAlpha(COLORS[i % COLORS.length], 0.2));
      const br = c.data.map((_, i) => COLORS[i % COLORS.length]);
      const t = c.type === 'horizontalBar' ? 'bar' : c.type;
      new Chart(document.getElementById(c.id), {{
        type: t,
        data: {{ labels: c.labels, datasets: [{{ data: c.data, backgroundColor: bg, borderColor: br, borderWidth: 1, borderRadius: 4 }}] }},
        options: {{
          indexAxis: c.type === 'horizontalBar' ? 'y' : 'x',
          responsive: true, maintainAspectRatio: false,
          plugins: {{ legend: {{ display: false }}, tooltip: {{ backgroundColor:'#0f172a', borderColor:'#1e293b', borderWidth:1 }} }},
          scales: {{ x: {{ grid: {{ color:'#1e293b' }} }}, y: {{ grid: {{ color:'#1e293b' }} }} }}
        }}
      }});
    }}

    inputEl.addEventListener('keydown', (e) => {{
      if (e.key === 'Enter' && !e.shiftKey) {{
        e.preventDefault();
        sendMessage();
      }}
    }});

    addMsg('bot', `Dataset loaded with ${profile.get("rows",0)} rows. Ask me anything about your data.`);
    renderCharts();
  </script>
</body>
</html>"""
