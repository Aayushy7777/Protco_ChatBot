import axios from "axios";
import React, { useState } from "react";

const API = "http://localhost:8010";

export default function ChatPanel({ activeDataset, onDashboard }) {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);

  const send = async () => {
    if (!query.trim()) return;
    const user = { role: "user", text: query };
    const next = [...messages, user];
    setMessages(next);
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/chat`, {
        query,
        active_dataset: activeDataset || null,
        history: next.map((m) => ({ role: m.role, content: m.text })),
      });
      setMessages((m) => [...m, { role: "assistant", text: data.response }]);
      if (data.dashboard) onDashboard(data.dashboard);
    } finally {
      setQuery("");
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-white">Chatbot</h2>
      <div className="mt-3 h-72 overflow-auto rounded border border-slate-700 bg-slate-950 p-2">
        {messages.map((m, i) => (
          <div key={i} className={`mb-2 text-sm ${m.role === "user" ? "text-cyan-300" : "text-slate-200"}`}>
            <b>{m.role === "user" ? "You" : "Bot"}:</b> {m.text}
          </div>
        ))}
      </div>
      <div className="mt-3 flex gap-2">
        <input
          className="flex-1 rounded border border-slate-600 bg-slate-800 p-2 text-slate-200"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Ask about total revenue, top products, monthly trend..."
        />
        <button className="rounded bg-indigo-600 px-3 py-2 text-white" onClick={send} disabled={loading}>
          {loading ? "..." : "Send"}
        </button>
      </div>
    </div>
  );
}

