import React, { useRef, useEffect, memo } from 'react';
import { motion } from 'framer-motion';
import Message from './Message';
import { SparklesIcon } from '@heroicons/react/24/outline';

const TypingIndicator = () => (
  <motion.div
    initial={{ opacity: 0 }}
    animate={{ opacity: 1 }}
    className="flex items-center gap-4 p-2 w-fit mb-4"
  >
    <div className="flex-shrink-0 w-8 h-8 rounded-md bg-[rgba(255,255,255,0.04)] border border-[rgba(0,212,255,0.3)] flex items-center justify-center">
      <motion.div
        animate={{ opacity: [0.4, 1, 0.4], scale: [0.95, 1.05, 0.95] }}
        transition={{ duration: 1.5, repeat: Infinity, ease: 'easeInOut' }}
      >
        <SparklesIcon className="w-5 h-5 text-[#00D4FF]" />
      </motion.div>
    </div>
    <span className="text-[13px] text-slate-400 font-medium">Generating response...</span>
  </motion.div>
);

const MessageList = memo(({ messages, isLoading, streaming, onRegenerate }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading, streaming]);

  return (
    <div className="flex-1 overflow-y-auto overscroll-none px-4 py-6 bg-[#0A0F2C]">
      {messages.length === 0 ? (
        <motion.div
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          className="h-full flex flex-col items-center justify-center text-center px-4"
        >
          <div className="w-16 h-16 rounded-2xl bg-[rgba(255,255,255,0.04)] border border-[rgba(0,212,255,0.3)] flex items-center justify-center mb-6 shadow-[0_0_20px_rgba(0,212,255,0.15)]">
            <SparklesIcon className="w-8 h-8 text-[#00D4FF]" />
          </div>
          <h2 className="text-xl font-bold text-white mb-2 tracking-wide">
            How can I help you today?
          </h2>
          <p className="text-[15px] text-slate-400 max-w-md leading-relaxed">
            I can analyze your uploaded sales data, identify trends, summarize performance, or answer specific business questions.
          </p>
        </motion.div>
      ) : (
        <div className="max-w-4xl mx-auto w-full flex flex-col gap-2">
          {messages.map((msg, index) => (
            <Message
              key={index}
              message={msg}
              onRegenerate={
                msg.role === 'assistant' && index === messages.length - 1
                  ? onRegenerate
                  : null
              }
              isLast={index === messages.length - 1}
            />
          ))}
          {(isLoading || streaming) && <TypingIndicator />}
          <div ref={messagesEndRef} className="h-4" />
        </div>
      )}
    </div>
  );
});

MessageList.displayName = 'MessageList';

export default MessageList;

