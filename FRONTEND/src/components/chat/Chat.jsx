import React, { useCallback, useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import MessageList from './MessageList';
import ChatInput from './ChatInput';
import { useChat } from '../../hooks/useChat';
import { useChatStore } from '../../store/chatStore';

const Chat = ({
  activeDataset,
  activeConversation,
  onCreateConversation,
  activeQuarter = 'All',
  activeCategory = 'All',
}) => {
  const storageKey = activeDataset
    ? `chat_history_${activeDataset}_${activeQuarter}`
    : null;

  const {
    messages,
    loading,
    streaming,
    handleSendMessage,
    stopGeneration,
  } = useChat(activeDataset, activeConversation, activeQuarter, activeCategory);

  // ── Persist messages to localStorage ─────────────────────────────────────
  useEffect(() => {
    if (!storageKey || !messages || messages.length === 0) return;
    try {
      // Keep only last 30 messages to avoid bloat
      const toSave = messages.slice(-30);
      localStorage.setItem(storageKey, JSON.stringify(toSave));
    } catch {
      // Ignore localStorage quota errors
    }
  }, [messages, storageKey]);

  // NOTE: Intentionally no auto-trigger message.
  // The app waits for the user's first chat input so it doesn't send any
  // sample-case prompt automatically.

  const clearMemory = useCallback(() => {
    if (storageKey) {
      localStorage.removeItem(storageKey);
    }
    // Reset messages via store if possible
    useChatStore.getState().clearMessages?.(activeConversation);
  }, [storageKey, activeConversation]);

  const handleInitialMessage = useCallback((message) => {
    if (!activeConversation) {
      onCreateConversation?.();
      setTimeout(() => handleSendMessage(message), 100);
    } else {
      handleSendMessage(message);
    }
  }, [activeConversation, onCreateConversation, handleSendMessage]);

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.3 }}
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        background: '#0B0F1A',
      }}
    >
      {/* ── Memory bar ── */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '6px 14px',
        borderBottom: '1px solid rgba(255,255,255,0.06)',
        flexShrink: 0,
      }}>
        <span style={{ fontSize: 10, color: 'rgba(0,212,255,0.5)', letterSpacing: 0.5 }}>
          {messages.length > 0
            ? `Memory: ${Math.min(messages.length, 30)} messages saved`
            : 'No history yet'}
          {activeQuarter !== 'All' && ` · ${activeQuarter}`}
        </span>
        {messages.length > 0 && (
          <button
            onClick={clearMemory}
            style={{
              fontSize: 10,
              color: 'rgba(255,51,102,0.7)',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              padding: 0,
              letterSpacing: 0.3,
            }}
          >
            Clear Memory
          </button>
        )}
      </div>

      <MessageList
        messages={messages}
        isLoading={loading}
        streaming={streaming}
        onRegenerate={() => {
          if (messages.length > 0) {
            const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
            if (lastUserMsg) handleSendMessage(lastUserMsg.content);
          }
        }}
      />
      <ChatInput
        onSendMessage={handleInitialMessage}
        isLoading={loading}
        streaming={streaming}
        onStop={stopGeneration}
      />
    </motion.div>
  );
};

export default Chat;
