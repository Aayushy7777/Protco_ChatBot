import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  DocumentPlusIcon,
  TrashIcon,
  PlusIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';

const Sidebar = ({
  datasets,
  activeDataset,
  onDatasetSelect,
  onFileUpload,
  onDeleteDataset,
  conversations = {},
  activeConversation,
  onSelectConversation,
}) => {
  const [expandedSection, setExpandedSection] = useState('datasets');

  const sortedConversations = Object.values(conversations || {})
    .sort((a, b) => b.updatedAt - a.updatedAt);

  return (
    <motion.div
      initial={{ x: -20, opacity: 0 }}
      animate={{ x: 0, opacity: 1 }}
      transition={{ duration: 0.3 }}
      className="w-80 bg-gradient-to-b from-slate-900 to-slate-950 text-slate-300 flex flex-col border-r border-slate-700 overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
        <h1 className="text-2xl font-bold text-white mb-1 flex items-center gap-2">
          📊 <span>Data AI</span>
        </h1>
        <p className="text-xs text-slate-500">Local analytics assistant</p>
      </div>

      {/* Upload Button */}
      <motion.label
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        className="m-4 flex items-center justify-center px-4 py-3 bg-gradient-to-r from-indigo-600 to-indigo-700 text-white rounded-lg cursor-pointer hover:shadow-lg transition-all duration-200"
      >
        <DocumentPlusIcon className="w-5 h-5 mr-2" />
        <span className="font-medium">Upload CSV</span>
        <input
          type="file"
          accept=".csv,text/csv,.xlsx,.xls"
          multiple
          onChange={onFileUpload}
          className="hidden"
        />
      </motion.label>

      {/* Main Content */}
      <div className="flex-1 overflow-y-auto overscroll-none space-y-4 px-4 py-4">
        {/* Datasets Section */}
        <div>
          <motion.button
            whileHover={{ backgroundColor: 'rgba(148, 163, 184, 0.1)' }}
            onClick={() =>
              setExpandedSection(
                expandedSection === 'datasets' ? null : 'datasets'
              )
            }
            className="w-full flex items-center justify-between p-2 rounded-lg transition-colors"
          >
            <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
              📁 Datasets
            </h2>
            <motion.div
              animate={{
                rotate: expandedSection === 'datasets' ? 180 : 0,
              }}
            >
              <ChevronDownIcon className="w-4 h-4" />
            </motion.div>
          </motion.button>

          <AnimatePresence>
            {expandedSection === 'datasets' && (
              <motion.div
                initial={{ opacity: 0, height: 0 }}
                animate={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0 }}
                className="space-y-2 mt-2"
              >
                {datasets.length === 0 ? (
                  <p className="text-sm text-slate-500 text-center py-4">
                    No datasets yet
                  </p>
                ) : (
                  datasets.map((ds) => (
                    <motion.div
                      key={ds.name}
                      whileHover={{ backgroundColor: 'rgba(99, 102, 241, 0.1)' }}
                      onClick={() => onDatasetSelect(ds.name)}
                      className={`flex justify-between items-center p-3 rounded-lg cursor-pointer transition-all duration-200 ${
                        activeDataset === ds.name
                          ? 'bg-indigo-600/30 border border-indigo-500/50'
                          : 'border border-slate-700/50'
                      }`}
                    >
                      <div className="flex-1 min-w-0">
                        <p className="font-medium truncate text-slate-200">
                          {ds.name}
                        </p>
                        <p className="text-xs text-slate-500">
                          {ds.rows} × {ds.columns}
                        </p>
                      </div>
                      <motion.button
                        whileHover={{ scale: 1.1 }}
                        whileTap={{ scale: 0.9 }}
                        onClick={(e) => {
                          e.stopPropagation();
                          onDeleteDataset(ds.name);
                        }}
                        className="p-1 text-slate-500 hover:text-red-500 transition-colors"
                      >
                        <TrashIcon className="w-4 h-4" />
                      </motion.button>
                    </motion.div>
                  ))
                )}
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Conversations Section */}
        {sortedConversations.length > 0 && (
          <div>
            <motion.button
              whileHover={{ backgroundColor: 'rgba(148, 163, 184, 0.1)' }}
              onClick={() =>
                setExpandedSection(
                  expandedSection === 'conversations' ? null : 'conversations'
                )
              }
              className="w-full flex items-center justify-between p-2 rounded-lg transition-colors"
            >
              <h2 className="text-xs font-semibold text-slate-400 uppercase tracking-wider">
                💬 Conversations
              </h2>
              <motion.div
                animate={{
                  rotate: expandedSection === 'conversations' ? 180 : 0,
                }}
              >
                <ChevronDownIcon className="w-4 h-4" />
              </motion.div>
            </motion.button>

            <AnimatePresence>
              {expandedSection === 'conversations' && (
                <motion.div
                  initial={{ opacity: 0, height: 0 }}
                  animate={{ opacity: 1, height: 'auto' }}
                  exit={{ opacity: 0, height: 0 }}
                  className="space-y-2 mt-2"
                >
                  {sortedConversations.map((conv) => (
                    <motion.div
                      key={conv.id}
                      whileHover={{ backgroundColor: 'rgba(99, 102, 241, 0.1)' }}
                      onClick={() => onSelectConversation(conv.id)}
                      className={`p-3 rounded-lg cursor-pointer transition-all duration-200 border ${
                        activeConversation === conv.id
                          ? 'bg-indigo-600/30 border-indigo-500/50'
                          : 'border-slate-700/50 hover:border-slate-600/50'
                      }`}
                    >
                      <p className="font-medium text-slate-200 truncate text-sm">
                        {conv.title || 'Untitled'}
                      </p>
                      <p className="text-xs text-slate-500 mt-1">
                        {conv.messages?.length || 0} messages
                      </p>
                    </motion.div>
                  ))}
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Footer */}
      <div className="p-4 border-t border-slate-700 text-xs text-slate-500 text-center">
        <p>Powered by Ollama</p>
      </div>
    </motion.div>
  );
};

export default Sidebar;

