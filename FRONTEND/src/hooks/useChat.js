import { useState, useRef, useEffect, useCallback } from 'react';
import { useChatStore } from '../store/chatStore';
import { useDashboardStore } from '../store/dashboardStore';

const API = "http://localhost:8000/api";

export const useChat = (activeDataset, activeConversation, activeQuarter = 'All', activeCategory = 'All') => {
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const abortControllerRef = useRef(null);
  
  const {
    conversations,
    addMessage,
    updateLastMessage,
  } = useChatStore();
  
  const { pinChart } = useDashboardStore();
  
  const messages = activeConversation ? conversations[activeConversation]?.messages || [] : [];
  
  const handleSendMessage = useCallback(async (message) => {
    if (!message.trim() || loading || !activeConversation) return;

    try {
      // Update UI immediately for better perceived latency.
      addMessage(activeConversation, { role: 'user', content: message });
      addMessage(activeConversation, { role: 'assistant', content: '' });

      setLoading(true);
      setStreaming(false);

      // Fetch list of all available files (for agent context selection).
      const filesRes = await fetch(`${API}/files`);
      const filesData = await filesRes.json().catch(() => ({}));
      const allFiles = (filesData.files || []).map((f) => f.name);

      const conversation_history = [
        ...(messages || []),
        { role: 'user', content: message },
      ].slice(-30);

      const response = await fetch(`${API}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          active_file: activeDataset,
          conversation_history,
          all_files: allFiles,
        }),
      });

      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        throw new Error(data?.detail || response.statusText || 'Chat request failed');
      }

      const answer = data?.answer || '';
      let finalAnswer = answer;
      if (!finalAnswer.trim()) {
        if (data?.intent === 'CHART' && data?.chart_config) {
          finalAnswer = 'Chart generated and added to the dashboard.';
        } else if (data?.intent === 'TABLE' && data?.table_columns?.length) {
          finalAnswer = 'Table generated from your request.';
        }
      }
      updateLastMessage(activeConversation, finalAnswer);

      if (data?.intent === 'CHART' && data?.chart_config) {
        pinChart(data.chart_config);
      }

      if (data?.intent === 'TABLE' && data?.table_columns?.length) {
        const cols = data.table_columns || [];
        const rows = data.table_data || [];

        // Render a simple markdown table into the assistant bubble.
        if (cols.length > 0 && Array.isArray(rows) && rows.length > 0) {
          const header = `| ${cols.join(' | ')} |`;
          const sep = `| ${cols.map(() => '---').join(' | ')} |`;
          const rowLines = rows
            .slice(0, 50)
            .map((r) => `| ${cols.map((c) => String(r?.[c] ?? '')).join(' | ')} |`)
            .join('\\n');

          updateLastMessage(activeConversation, `${answer}\\n\\n${header}\\n${sep}\\n${rowLines}`);
        }
      }
    } catch (err) {
      updateLastMessage(
        activeConversation,
        `❌ Error: ${err?.message || String(err)}`
      );
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  }, [activeConversation, activeDataset, loading, messages, addMessage, updateLastMessage, pinChart]);
  
  const stopGeneration = useCallback(() => {
    // Backend chat is non-streaming currently, so stop is best-effort.
    abortControllerRef.current?.abort?.();
    setLoading(false);
    setStreaming(false);
  }, []);

  return {
    messages,
    loading,
    streaming,
    handleSendMessage,
    stopGeneration,
  };
};

