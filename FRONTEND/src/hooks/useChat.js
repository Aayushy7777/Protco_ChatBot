import { useState, useRef, useEffect, useCallback } from 'react';
import { useChatStore } from '../store/chatStore';
import { useDashboardStore } from '../store/dashboardStore';

const API = "http://localhost:8000";

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

    addMessage(activeConversation, {
      role: 'user',
      content: message,
    });

    setLoading(true);
    setStreaming(true);
    abortControllerRef.current = new AbortController();

    addMessage(activeConversation, {
      role: 'assistant',
      content: '',
    });

    try {
      // Fetch list of all available files
      const filesRes = await fetch(`${API}/api/files`);
      const filesData = await filesRes.json();
      const allFiles = (filesData.files || []).map(f => f.name);

      const response = await fetch(`${API}/api/chat/stream`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message,
          active_file: activeDataset,
          all_files: allFiles,
          conversation_id: activeConversation,
          session_id: `${activeDataset || 'none'}_${activeQuarter}_${activeCategory}`,
          active_quarter: activeQuarter,
          active_category: activeCategory,
        }),
        signal: abortControllerRef.current.signal,
      });

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      let fullContent = '';
      let pendingCharts = [];

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              
              if (data.status === 'token') {
                fullContent += data.token;
                updateLastMessage(activeConversation, fullContent);
              } else if (data.status === 'chart') {
                pendingCharts.push(data.chart);
              } else if (data.status === 'done') {
                // Process pending charts
                pendingCharts.forEach(chart => {
                  pinChart(chart);
                });
              }
            } catch (e) {
              // Ignore parse errors for empty chunks
            }
          }
        }
      }
    } catch (err) {
      if (err.name !== 'AbortError') {
        updateLastMessage(activeConversation, `❌ Error: ${err.message}`);
      }
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  }, [activeConversation, activeDataset, activeQuarter, activeCategory, loading, addMessage, updateLastMessage, pinChart]);
  
  const stopGeneration = useCallback(() => {
    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
      setLoading(false);
      setStreaming(false);
    }
  }, []);

  return {
    messages,
    loading,
    streaming,
    handleSendMessage,
    stopGeneration,
  };
};

