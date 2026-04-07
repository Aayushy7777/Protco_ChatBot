import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Chat from "./components/chat/Chat";
import Dashboard from "./components/dashboard/Dashboard";
import { useChatStore } from "./store/chatStore";
import { ArrowUpTrayIcon } from "@heroicons/react/24/outline";

const API = "http://localhost:8000/api";

export default function App() {
  const [datasets, setDatasets] = useState([]);
  const [activeDataset, setActiveDataset] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [backendStatus, setBackendStatus] = useState("checking");

  const {
    activeConversation,
    createConversation,
    setActiveConversation,
  } = useChatStore();

  // Health check
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch(`${API}/health`);
        if (res.ok) setBackendStatus("connected");
        else setBackendStatus("error");
      } catch {
        setBackendStatus("error");
      }
    };
    check();
    const interval = setInterval(check, 15000);
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    fetchDatasets();
  }, []);

  const fetchDatasets = async () => {
    try {
      const res = await fetch(`${API}/files`);
      const data = await res.json();
      const files = data.files || [];
      setDatasets(files);
      if (files.length > 0 && !activeDataset) {
        const first = files[0].name;
        setActiveDataset(first);
        const convId = createConversation(first);
        setActiveConversation(convId);
      }
    } catch (err) {
      console.error("Failed to fetch datasets:", err);
    }
  };

  const handleFileUpload = async (event) => {
    const files = event.target.files;
    if (!files || files.length === 0) return;

    const formData = new FormData();
    for (const file of files) {
      formData.append("files", file);
    }

    try {
      setUploading(true);
      const res = await fetch(`${API}/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      const firstName = files[0].name;
      setActiveDataset(firstName);
      const convId = createConversation(firstName);
      setActiveConversation(convId);
      setUploading(false);
      fetchDatasets();
    } catch (err) {
      console.error("Upload error:", err);
      setUploading(false);
    }
    event.target.value = "";
  };

  const handleCreateConversation = useCallback(() => {
    if (activeDataset) {
      const convId = createConversation(activeDataset);
      setActiveConversation(convId);
      return convId;
    }
    return null;
  }, [activeDataset, createConversation, setActiveConversation]);

  const handleSelectDataset = (fileName) => {
    setActiveDataset(fileName);
    const convId = createConversation(fileName);
    setActiveConversation(convId);
  };

  return (
    <div className="flex flex-col h-screen bg-[#0B0F1A] text-white overflow-hidden">
      {/* ── Header ── */}
      <header className="flex items-center justify-between px-5 py-3 border-b border-white/[0.06] bg-[#0B0F1A] flex-shrink-0">
        <div className="flex items-center gap-3">
          <h1 className="text-[15px] font-semibold tracking-tight text-white/90">
            CSV Chat Agent
          </h1>
          <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-white/[0.04] border border-white/[0.06]">
            <div className={`w-1.5 h-1.5 rounded-full ${
              backendStatus === "connected" ? "bg-emerald-400" :
              backendStatus === "error" ? "bg-red-400" : "bg-yellow-400 animate-pulse"
            }`} />
            <span className="text-[10px] text-white/40 font-medium">
              {backendStatus === "connected" ? "Connected" :
               backendStatus === "error" ? "Disconnected" : "Checking..."}
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          {/* File selector chips */}
          {datasets.length > 0 && (
            <div className="flex gap-1.5 overflow-x-auto max-w-md">
              {datasets.map((dataset) => {
                const fileName = typeof dataset === "string" ? dataset : dataset.name;
                const isActive = fileName === activeDataset;
                return (
                  <button
                    key={fileName}
                    onClick={() => handleSelectDataset(fileName)}
                    className={`px-2.5 py-1 rounded-md text-[11px] font-medium whitespace-nowrap transition-all ${
                      isActive
                        ? "bg-indigo-500/15 text-indigo-400 border border-indigo-500/30"
                        : "bg-white/[0.03] text-white/40 border border-white/[0.06] hover:text-white/60 hover:border-white/10"
                    }`}
                  >
                    {fileName}
                  </button>
                );
              })}
            </div>
          )}

          <label className="flex items-center gap-1.5 px-3 py-1.5 bg-indigo-500 hover:bg-indigo-600 text-white text-[12px] font-medium rounded-lg cursor-pointer transition-colors">
            <ArrowUpTrayIcon className="w-3.5 h-3.5" />
            Upload
            <input
              type="file"
              multiple
              accept=".csv,.xlsx,.xls"
              className="hidden"
              onChange={handleFileUpload}
            />
          </label>
        </div>
      </header>

      {/* ── Upload overlay ── */}
      <AnimatePresence>
        {uploading && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="absolute inset-0 z-50 bg-black/80 backdrop-blur-sm flex flex-col items-center justify-center gap-4"
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1.5, repeat: Infinity, ease: "linear" }}
              className="w-10 h-10 border-2 border-white/10 border-t-indigo-400 rounded-full"
            />
            <p className="text-sm text-white/70 font-medium">Processing file...</p>
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Main: Left 70% Data | Right 30% Chat ── */}
      <div className="flex flex-1 min-h-0">
        {/* Left: Data + Visualization */}
        <div className="w-[70%] overflow-y-auto border-r border-white/[0.06]">
          {activeDataset ? (
            <Dashboard
              activeDataset={activeDataset}
              allDatasets={datasets}
            />
          ) : (
            <EmptyState onUpload={() => document.querySelector('input[type="file"]')?.click()} />
          )}
        </div>

        {/* Right: AI Chat */}
        <div className="w-[30%] flex flex-col min-w-[320px] bg-[#0B0F1A]">
          {activeDataset ? (
            <Chat
              activeDataset={activeDataset}
              activeConversation={activeConversation}
              onCreateConversation={handleCreateConversation}
            />
          ) : (
            <div className="flex-1 flex items-center justify-center px-6">
              <p className="text-sm text-white/25 text-center leading-relaxed">
                Ask something about your data...
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function EmptyState({ onUpload }) {
  return (
    <div className="h-full flex flex-col items-center justify-center gap-5">
      <div className="w-16 h-16 rounded-2xl bg-white/[0.03] border border-white/[0.06] flex items-center justify-center">
        <ArrowUpTrayIcon className="w-7 h-7 text-white/20" />
      </div>
      <div className="text-center">
        <h2 className="text-lg font-semibold text-white/70 mb-1">No data uploaded</h2>
        <p className="text-sm text-white/30 max-w-xs">
          Upload a CSV or Excel file to generate insights and start chatting with your data.
        </p>
      </div>
      <button
        onClick={onUpload}
        className="px-4 py-2 bg-indigo-500 hover:bg-indigo-600 text-white text-sm font-medium rounded-lg transition-colors"
      >
        Upload File
      </button>
    </div>
  );
}
