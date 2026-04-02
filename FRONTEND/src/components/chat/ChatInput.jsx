import React, { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { PaperAirplaneIcon, StopIcon } from '@heroicons/react/24/solid';
import { SUGGESTED_PROMPTS } from '../../constants';

const ChatInput = ({ onSendMessage, isLoading, onStop, streaming }) => {
  const [input, setInput] = useState('');
  const [showSuggestions, setShowSuggestions] = useState(true);
  const inputRef = useRef(null);

  useEffect(() => {
    if (inputRef.current && !isLoading) {
      inputRef.current.focus();
    }
  }, [isLoading]);

  const handleSendMessage = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input);
      setInput('');
      setShowSuggestions(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(e);
    }
  };

  const handleSuggestedPrompt = (prompt) => {
    onSendMessage(prompt);
    setInput('');
    setShowSuggestions(false);
  };

  return (
    <div className="bg-[#0A0F2C] px-4 py-4 w-full max-w-4xl mx-auto">
      <AnimatePresence>
        {showSuggestions && !isLoading && (
          <motion.div
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.95, transition: { duration: 0.15 } }}
            className="mb-4 grid grid-cols-2 gap-2"
          >
            {SUGGESTED_PROMPTS.map((prompt, idx) => (
              <motion.button
                key={idx}
                whileHover={{ scale: 1.01 }}
                whileTap={{ scale: 0.99 }}
                onClick={() => handleSuggestedPrompt(prompt.text)}
                className="p-3 rounded-xl bg-[#111111] border border-[rgba(255,255,255,0.05)] hover:border-[rgba(237,28,36,0.3)] text-left group transition-all duration-200"
              >
                <div className="flex items-center gap-3">
                  <span className="text-xl group-hover:scale-110 transition-transform text-[#00D4FF]">
                    {prompt.icon}
                  </span>
                  <div className="text-[13px] text-slate-300 font-medium group-hover:text-white transition-colors line-clamp-2 leading-tight">
                    {prompt.text}
                  </div>
                </div>
              </motion.button>
            ))}
          </motion.div>
        )}
      </AnimatePresence>

      <form onSubmit={handleSendMessage} className="relative group">
        <div className="relative flex items-end w-full rounded-2xl bg-[rgba(255,255,255,0.04)] border border-[rgba(255,255,255,0.1)] focus-within:border-[rgba(0,212,255,0.4)] focus-within:shadow-[0_0_15px_rgba(0,212,255,0.1)] transition-all duration-300">
          <textarea
            ref={inputRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask anything about your data..."
            disabled={isLoading}
            className="flex-1 max-h-48 min-h-[56px] w-full resize-none bg-transparent py-4 pl-5 pr-14 text-[15px] font-medium text-white placeholder-slate-400 focus:outline-none disabled:opacity-50 break-words"
            rows={1}
            style={{ overflowY: input.length > 50 ? 'auto' : 'hidden' }}
          />

          <div className="absolute right-2 bottom-2">
            {isLoading || streaming ? (
              <motion.button
                type="button"
                onClick={onStop}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="p-2 rounded-xl bg-transparent hover:bg-slate-800 text-slate-400 hover:text-red-400 transition-colors duration-200"
                title="Stop generation (Escape)"
              >
                <StopIcon className="w-6 h-6" />
              </motion.button>
            ) : (
              <motion.button
                type="submit"
                disabled={isLoading || !input.trim()}
                whileHover={{ scale: isLoading || !input.trim() ? 1 : 1.05 }}
                whileTap={{ scale: isLoading || !input.trim() ? 1 : 0.95 }}
                className={`p-2 rounded-xl flex items-center justify-center transition-all duration-300 shadow-md ${
                  input.trim() && !isLoading
                    ? 'bg-[#00D4FF] text-[#0A0F2C] hover:bg-[#00b4db] hover:shadow-[0_0_15px_rgba(0,212,255,0.4)]'
                    : 'bg-slate-800 text-slate-500 cursor-not-allowed shadow-none'
                }`}
                title="Send message (Enter)"
              >
                <PaperAirplaneIcon className="w-5 h-5 -mt-0.5 ml-0.5" />
              </motion.button>
            )}
          </div>
        </div>
        
        <div className="mt-2 text-center text-[11px] text-slate-500">
          AI generated content may be inaccurate.
        </div>
      </form>
    </div>
  );
};

export default ChatInput;


