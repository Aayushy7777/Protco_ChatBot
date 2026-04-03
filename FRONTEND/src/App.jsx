import { useState, useEffect, useCallback } from "react";
import { motion, AnimatePresence } from "framer-motion";
import Chat from "./components/chat/Chat";
import Dashboard from "./components/dashboard/Dashboard";
import { useChatStore } from "./store/chatStore";
import { useDashboardStore } from "./store/dashboardStore";
import {
  ChatBubbleLeftRightIcon,
  SparklesIcon,
  ArrowUpTrayIcon,
  XMarkIcon,
} from "@heroicons/react/24/outline";

const API = "http://localhost:8888";

// ── File Info Banner Component ──
function FileInfoBanner({ fileMetadata }) {
  const auto = fileMetadata?.auto_detected || {};
  if (!auto.domain) return null;

  const formatCr = (n) => {
    if (n >= 1e7) return (n / 1e7).toFixed(2) + " Cr";
    if (n >= 1e5) return (n / 1e5).toFixed(2) + " L";
    return n.toLocaleString("en-IN");
  };

  return (
    <div style={{
      display: "flex", gap: 16, padding: "8px 14px",
      borderBottom: "1px solid #1e293b",
      background: "#0a0f1a", flexWrap: "wrap",
    }}>
      {auto.domain && (
        <Chip label="Type" value={auto.domain} />
      )}
      {auto.time_period && (
        <Chip label="Period" value={auto.time_period} />
      )}
      {auto.total_revenue && auto.revenue_column && (
        <Chip
          label={auto.revenue_column}
          value={"₹" + formatCr(auto.total_revenue)}
        />
      )}
      {auto.total_clients && auto.client_column && (
        <Chip
          label={auto.client_column}
          value={auto.total_clients + " unique"}
        />
      )}
    </div>
  );
}

function Chip({ label, value }) {
  return (
    <div style={{ fontSize: 11 }}>
      <span style={{ color: "#475569" }}>{label}: </span>
      <span style={{ color: "#a5b4fc", fontWeight: 500 }}>{value}</span>
    </div>
  );
}

// ── Company Filter Sidebar Component ──
function CompanyFilterSidebar({ companies, selected, onSelect }) {
  const [search, setSearch] = useState("");
  
  const filtered = companies.filter(c =>
    c.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div style={{
      width: 220, flexShrink: 0,
      borderRight: "1px solid #1e293b",
      display: "flex", flexDirection: "column",
      height: "100%", background: "#0a0f1a",
    }}>
      {/* Search box */}
      <div style={{ padding: "10px 12px", borderBottom: "1px solid #1e293b" }}>
        <input
          value={search}
          onChange={e => setSearch(e.target.value)}
          placeholder="Search company..."
          style={{
            width: "100%", padding: "6px 10px",
            background: "#0a0f1a", border: "1px solid #1e293b",
            borderRadius: 6, color: "#e2e8f0", fontSize: 12,
          }}
        />
      </div>

      {/* ALL button */}
      <button
        onClick={() => onSelect("ALL")}
        style={{
          margin: "8px 12px 4px",
          padding: "6px 0", borderRadius: 6,
          background: selected === "ALL" ? "#4f46e5" : "transparent",
          border: "1px solid #1e293b",
          color: selected === "ALL" ? "#fff" : "#64748b",
          fontSize: 12, cursor: "pointer", fontWeight: 600,
        }}>
        All companies
      </button>

      {/* Scrollable list */}
      <div style={{ flex: 1, overflowY: "auto", padding: "4px 8px" }}>
        {filtered.map(company => (
          <button key={company}
            onClick={() => onSelect(company)}
            style={{
              width: "100%", textAlign: "left",
              padding: "7px 10px", marginBottom: 2,
              background: selected === company ? "#4f46e51a" : "transparent",
              border: "none",
              borderLeft: selected === company ? "2px solid #4f46e5" : "2px solid transparent",
              color: selected === company ? "#a5b4fc" : "#64748b",
              fontSize: 11.5, cursor: "pointer", borderRadius: "0 4px 4px 0",
            }}>
            {company.replace(/^\d+\-/, "")}
          </button>
        ))}
      </div>

      <div style={{ padding: "8px 12px", borderTop: "1px solid #1e293b",
        fontSize: 10, color: "#334155" }}>
        {filtered.length} companies
      </div>
    </div>
  );
}

export default function App() {
  const [datasets, setDatasets] = useState([]);
  const [activeDataset, setActiveDataset] = useState(null);
  const [fileMetadata, setFileMetadata] = useState(null);
  const [isChatOpen, setIsChatOpen] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [dashboardReadyMsg, setDashboardReadyMsg] = useState(false);
  const [activeQuarter, setActiveQuarter] = useState('All');
  const [activeCategory, setActiveCategory] = useState('All');
  const [detectedQuarter, setDetectedQuarter] = useState(null);

  const {
    conversations,
    activeConversation,
    createConversation,
    setActiveConversation,
  } = useChatStore();

  useEffect(() => {
    fetchDatasets();
  }, []);

  // ── Quarter detector (mirrors backend logic) ─────────────────────────────
  const detectQuarterFromFilename = (filename) => {
    const name = filename.toLowerCase();
    // Q12 → Q1 (longest first to avoid q1 matching q12)
    for (let i = 12; i >= 1; i--) {
      if (name.includes(`q${i}`)) return `Q${i}`;
    }
    // FY99 → FY25 (4-digit form first)
    for (let yr = 99; yr >= 25; yr--) {
      if (name.includes(`fy20${String(yr).padStart(2,'0')}`)) return `FY${yr}`;
      if (name.includes(`fy${yr}`)) return `FY${yr}`;
    }
    return null;
  };

  const autoGenerateDashboard = async (filename) => {
    // Legacy: just trigger a loading toast — Dashboard.jsx handles its own fetch
    setUploading(true);
    setDashboardReadyMsg(true);
    setTimeout(() => {
      setUploading(false);
      setDashboardReadyMsg(false);
    }, 3500);
  };

  const fetchDatasets = async () => {
    try {
      const res = await fetch(`${API}/api/files`);
      const data = await res.json();
      const files = data.files || [];
      setDatasets(files);
      if (files.length > 0 && !activeDataset) {
        const first = files[0].name;
        setActiveDataset(first);
        const convId = createConversation(first);
        setActiveConversation(convId);
        autoGenerateDashboard(first);
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
      const res = await fetch(`${API}/api/upload`, {
        method: "POST",
        body: formData,
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail);

      const firstName = files[0].name;
      setActiveDataset(firstName);
      
      // Capture auto-detected metadata from upload response
      if (data.uploaded && data.uploaded[0]) {
        setFileMetadata(data.uploaded[0]);
      }

      // Auto-detect quarter from filename and jump to that tab
      const q = detectQuarterFromFilename(firstName);
      if (q) {
        setActiveQuarter(q);
        setDetectedQuarter(q);          // tells Dashboard to switch tab
      } else {
        setDetectedQuarter('All');      // no quarter → show All
      }

      const convId = createConversation(firstName);
      setActiveConversation(convId);
      setUploading(false);
      setDashboardReadyMsg(true);
      setTimeout(() => setDashboardReadyMsg(false), 3000);
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

  return (
    <div style={{
      display: "flex",
      height: "100vh",
      background: "#0A0F2C",
      color: "white",
      overflow: "hidden",
      position: "relative",
      flexDirection: "column",
    }}>
      {/* ── Top bar: Upload button + file tabs ── */}
      <div style={{
        position: "relative",
        top: 0,
        left: 0,
        right: 0,
        zIndex: 20,
        display: "flex",
        gap: 12,
        alignItems: "center",
        justifyContent: "space-between",
        padding: "12px 22px",
        borderBottom: "1px solid rgba(255,255,255,0.1)",
        background: "#0A0F2C",
      }}>
        <label className="flex items-center gap-2 px-4 py-2 bg-[#00D4FF] hover:bg-[#00b4db] text-[#0A0F2C] text-sm font-semibold rounded-lg cursor-pointer transition-colors shadow-[0_0_15px_rgba(0,212,255,0.3)]">
          <ArrowUpTrayIcon style={{ width: 17, height: 17, color: "#0A0F2C" }} />
          Upload CSV
          <input
            type="file"
            multiple
            accept=".csv,.xlsx,.xls"
            style={{ display: "none" }}
            onChange={handleFileUpload}
          />
        </label>

        {/* ── File tabs selector ── */}
        {datasets.length > 0 && (
          <div style={{
            display: "flex",
            gap: 8,
            overflowX: "auto",
            paddingBottom: 4,
            flex: 1,
          }}>
            {datasets.map((dataset) => {
              const fileName = typeof dataset === 'string' ? dataset : dataset.name;
              const isActive = fileName === activeDataset;
              return (
                <button
                  key={fileName}
                  onClick={() => {
                    setActiveDataset(fileName);
                    const q = detectQuarterFromFilename(fileName);
                    if (q) {
                      setActiveQuarter(q);
                      setDetectedQuarter(q);
                    }
                    const convId = createConversation(fileName);
                    setActiveConversation(convId);
                  }}
                  style={{
                    padding: "6px 14px",
                    borderRadius: 6,
                    fontSize: 11,
                    fontWeight: 600,
                    whiteSpace: "nowrap",
                    border: isActive ? `2px solid #00D4FF` : `1px solid rgba(255,255,255,0.2)`,
                    background: isActive ? "rgba(0,212,255,0.15)" : "rgba(255,255,255,0.05)",
                    color: isActive ? "#00D4FF" : "rgba(255,255,255,0.65)",
                    cursor: "pointer",
                    transition: "all 0.2s",
                  }}
                  onMouseOver={(e) => {
                    if (!isActive) {
                      e.target.style.background = "rgba(255,255,255,0.08)";
                      e.target.style.borderColor = "rgba(0,212,255,0.4)";
                    }
                  }}
                  onMouseOut={(e) => {
                    if (!isActive) {
                      e.target.style.background = "rgba(255,255,255,0.05)";
                      e.target.style.borderColor = "rgba(255,255,255,0.2)";
                    }
                  }}
                >
                  📄 {fileName}
                </button>
              );
            })}
          </div>
        )}
      </div>

      {/* ── Auto-detected file info banner ── */}
      <FileInfoBanner fileMetadata={fileMetadata} />

      {uploading && (
        <div style={{
          position: "absolute",
          inset: 0,
          zIndex: 40,
          background: "rgba(10,10,10,0.88)",
          backdropFilter: "blur(6px)",
          display: "flex",
          flexDirection: "column",
          alignItems: "center",
          justifyContent: "center",
          gap: 18,
          top: "auto",
        }}>
          <motion.div
            animate={{ rotate: 360 }}
            transition={{ duration: 2, repeat: Infinity, ease: "linear" }}
            className="w-16 h-16 border-4 border-[rgba(0,212,255,0.2)] border-t-[#00D4FF] rounded-full mx-auto mb-4"
          />
          <h2 style={{
            fontSize: 22,
            fontWeight: 700,
            color: "#ffffff",
            margin: 0,
            textShadow: "0 0 12px #00D4FF",
          }}>
            Generating Dashboard…
          </h2>
          <p style={{ color: "rgba(255,255,255,0.45)", margin: 0, fontSize: 13 }}>
            Analysing columns and building charts
          </p>
        </div>
      )}

      <AnimatePresence>
        {dashboardReadyMsg && (
          <motion.div
            initial={{ opacity: 0, y: -50 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: -50 }}
            style={{
              position: "absolute",
              top: 70,
              left: "50%",
              transform: "translateX(-50%)",
              zIndex: 50,
              background: "#00D4FF",
              color: "#0A0F2C",
              padding: "8px 24px",
              borderRadius: 999,
              fontWeight: 800,
              fontSize: 14,
              boxShadow: "0 0 24px rgba(0,212,255,0.6)",
              whiteSpace: "nowrap",
            }}
          >
            ✓ Dashboard Ready!
          </motion.div>
        )}
      </AnimatePresence>

      {/* ── Main body: 3-column layout ── */}
      <div style={{ display: "flex", flex: 1, overflow: "hidden", minHeight: 0 }}>
        
        {/* Left: Company filter sidebar */}
        <CompanyFilterSidebar
          companies={datasets.map(d => typeof d === 'string' ? d : d.name)}
          selected={activeDataset || "ALL"}
          onSelect={(c) => {
            if (c !== "ALL") setActiveDataset(c);
          }}
        />

        {/* Center: Chat pane */}
        <div style={{ width: 380, borderRight: "1px solid #1e293b", display: "flex", flexDirection: "column", background: "#0a0f1a" }}>
          {activeDataset && (
            <Chat 
              dataset={activeDataset} 
              conversationId={activeConversation}
              onCreateConversation={handleCreateConversation}
            />
          )}
        </div>

        {/* Right: Dashboard */}
        <div style={{ flex: 1, overflow: "auto" }}>
          {activeDataset ? (
            <Dashboard
              activeDataset={activeDataset}
              allDatasets={datasets}
              detectedQuarter={detectedQuarter}
              onQuarterChange={(q) => setActiveQuarter(q)}
            />
          ) : (
            <div style={{ 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "center", 
              height: "100%",
              fontSize: 16,
              color: "#64748b",
            }}>
              Upload a CSV or Excel file to get started
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
