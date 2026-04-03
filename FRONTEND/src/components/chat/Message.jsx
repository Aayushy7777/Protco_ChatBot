import React, { useState } from 'react';
import { motion } from 'framer-motion';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import {
  DocumentDuplicateIcon,
  ArrowPathIcon,
  UserIcon,
  SparklesIcon
} from '@heroicons/react/24/outline';

const Message = ({ message, onRegenerate, isLast }) => {
  const { role, content } = message;
  const isUser = role === 'user';
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-4 w-full group mb-6 px-2 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {/* ── AI Avatar (Left) ── */}
      {!isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-md bg-[rgba(255,255,255,0.04)] border border-[rgba(0,212,255,0.3)] flex items-center justify-center mt-1">
          <SparklesIcon className="w-5 h-5 text-[#00D4FF]" />
        </div>
      )}

      {/* ── Message Bubble/Container ── */}
      <div
        className={`relative max-w-[85%] sm:max-w-[75%] px-5 py-3.5 text-[15px] leading-relaxed transition-all duration-200 ${
          isUser
            ? 'bg-[#1E293B] text-slate-100 rounded-2xl rounded-tr-sm shadow-md border border-[rgba(255,255,255,0.05)]'
            : 'bg-transparent text-slate-200'
        }`}
      >
        {isUser ? (
          <div className="whitespace-pre-wrap">{content}</div>
        ) : (
          <ReactMarkdown
            remarkPlugins={[remarkGfm]}
            className="prose prose-invert max-w-none prose-p:mb-4"
            components={{
              code({ node, inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline && match ? (
                  <div className="bg-[#050505] border border-[#1E293B] rounded-lg my-3 overflow-hidden">
                    <div className="bg-[#111111] px-4 py-1.5 text-xs text-slate-400 border-b border-[#1E293B]">
                      {match[1]}
                    </div>
                    <pre className="p-4 overflow-x-auto text-sm text-slate-200">
                      <code className={className} {...props}>
                        {children}
                      </code>
                    </pre>
                  </div>
                ) : (
                  <code className="bg-[rgba(0,212,255,0.1)] text-[#00D4FF] px-1.5 py-0.5 rounded text-[13px] font-mono break-words" {...props}>
                    {children}
                  </code>
                );
              },
              h1({ children }) { return <h1 className="text-xl font-bold text-white mb-3 mt-4">{children}</h1>; },
              h2({ children }) { return <h2 className="text-lg font-bold text-[#00D4FF] mb-3 mt-4">{children}</h2>; },
              h3({ children }) { return <h3 className="text-base font-bold text-slate-200 mb-2 mt-3">{children}</h3>; },
              ul({ children }) { return <ul className="list-disc pl-5 space-y-1.5 mb-4 text-slate-300">{children}</ul>; },
              ol({ children }) { return <ol className="list-decimal pl-5 space-y-1.5 mb-4 text-slate-300">{children}</ol>; },
              li({ children }) { return <li className="pl-1">{children}</li>; },
              strong({ children }) { return <strong className="font-semibold text-white">{children}</strong>; },
              table({ children }) {
                return (
                  <div className="overflow-x-auto my-4 rounded-lg border border-[rgba(255,255,255,0.1)]">
                    <table className="w-full text-sm text-left border-collapse">
                      {children}
                    </table>
                  </div>
                );
              },
              thead({ children }) { return <thead className="bg-[#111111] text-slate-300">{children}</thead>; },
              th({ children }) { return <th className="px-4 py-2 border-b border-[rgba(255,255,255,0.1)] font-semibold">{children}</th>; },
              td({ children }) { return <td className="px-4 py-2 border-b border-[rgba(255,255,255,0.05)] text-slate-300">{children}</td>; },
            }}
          >
            {content}
          </ReactMarkdown>
        )}

        {/* ── Actions (Copy / Regenerate) ── */}
        {!isUser && isLast && (
          <div className="flex items-center gap-3 mt-2 pt-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200">
            <button
              onClick={handleCopy}
              className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-[#00D4FF] transition-colors bg-transparent border-none cursor-pointer"
              title="Copy message"
            >
              <DocumentDuplicateIcon className="w-4 h-4" />
              {copied ? 'Copied!' : 'Copy'}
            </button>
            {onRegenerate && (
              <button
                onClick={onRegenerate}
                className="flex items-center gap-1.5 text-xs text-slate-400 hover:text-[#00D4FF] transition-colors bg-transparent border-none cursor-pointer"
                title="Regenerate response"
              >
                <ArrowPathIcon className="w-4 h-4" />
                Retry
              </button>
            )}
          </div>
        )}
      </div>

      {/* ── User Avatar (Right) ── */}
      {isUser && (
        <div className="flex-shrink-0 w-8 h-8 rounded-full bg-slate-700 flex items-center justify-center mt-1 border border-slate-600">
          <UserIcon className="w-5 h-5 text-slate-300" />
        </div>
      )}
    </motion.div>
  );
};

export default Message;

