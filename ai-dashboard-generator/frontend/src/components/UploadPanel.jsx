import axios from "axios";
import React, { useState } from "react";

const API = "http://localhost:8010";

export default function UploadPanel({ onUploaded }) {
  const [loading, setLoading] = useState(false);

  const handleUpload = async (files) => {
    if (!files?.length) return;
    const fd = new FormData();
    [...files].forEach((f) => fd.append("files", f));
    setLoading(true);
    try {
      const { data } = await axios.post(`${API}/upload`, fd);
      onUploaded(data);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="rounded-xl border border-slate-700 bg-slate-900 p-4">
      <h2 className="text-lg font-semibold text-white">Upload CSV Files</h2>
      <input
        className="mt-3 block w-full rounded border border-slate-600 bg-slate-800 p-2 text-slate-200"
        type="file"
        multiple
        accept=".csv"
        onChange={(e) => handleUpload(e.target.files)}
      />
      {loading && <p className="mt-2 text-sm text-cyan-300">Uploading and indexing...</p>}
    </div>
  );
}

