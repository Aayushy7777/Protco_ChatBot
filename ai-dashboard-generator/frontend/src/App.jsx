import React, { useState } from "react";
import ChatPanel from "./components/ChatPanel";
import DashboardViewer from "./components/DashboardViewer";
import UploadPanel from "./components/UploadPanel";

export default function App() {
  const [datasets, setDatasets] = useState([]);
  const [active, setActive] = useState("");
  const [dashboard, setDashboard] = useState(null);

  return (
    <div className="min-h-screen bg-slate-950 p-6 text-slate-100">
      <div className="mx-auto max-w-7xl">
        <h1 className="mb-4 text-2xl font-bold">AI Dashboard Generator with Chatbot</h1>
        <UploadPanel
          onUploaded={(d) => {
            const names = d.uploaded_files || [];
            setDatasets(names);
            setActive(d.active_file || names[0] || "");
          }}
        />

        <div className="mt-4 rounded-xl border border-slate-700 bg-slate-900 p-3">
          <label className="text-sm">Active Dataset</label>
          <select
            className="ml-2 rounded border border-slate-600 bg-slate-800 p-1"
            value={active}
            onChange={(e) => setActive(e.target.value)}
          >
            <option value="">Select</option>
            {datasets.map((d) => (
              <option key={d} value={d}>
                {d}
              </option>
            ))}
          </select>
        </div>

        <div className="mt-4 grid grid-cols-1 gap-4 lg:grid-cols-2">
          <ChatPanel activeDataset={active} onDashboard={setDashboard} />
          <DashboardViewer dashboard={dashboard} />
        </div>
      </div>
    </div>
  );
}

