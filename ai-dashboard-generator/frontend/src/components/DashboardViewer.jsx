import Plot from "react-plotly.js";
import React from "react";

export default function DashboardViewer({ dashboard }) {
  const charts = dashboard?.charts || [];
  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-white">Dashboard</h2>
      {!charts.length && <p className="mt-2 text-sm text-slate-400">No dashboard yet. Ask: "Create dashboard".</p>}
      <div className="mt-3 grid grid-cols-1 gap-4 md:grid-cols-2">
        {charts.map((c) => {
          const fig = JSON.parse(c.plotly_json);
          return (
            <div key={c.id} className="rounded border border-slate-700 bg-slate-950 p-2">
              <p className="mb-1 text-sm text-slate-300">{c.title}</p>
              <Plot data={fig.data} layout={{ ...fig.layout, autosize: true, paper_bgcolor: "#020617", plot_bgcolor: "#020617", font: { color: "#cbd5e1" } }} style={{ width: "100%", height: "300px" }} />
            </div>
          );
        })}
      </div>
      {!!(dashboard?.insights || []).length && (
        <div className="mt-4 rounded border border-indigo-700 bg-indigo-950/30 p-3 text-sm text-indigo-200">
          {(dashboard.insights || []).map((x, i) => (
            <div key={i}>- {x}</div>
          ))}
        </div>
      )}
    </div>
  );
}

