import React, { memo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { XMarkIcon } from '@heroicons/react/24/solid';

const FilterBar = memo(({ filters = [], onRemoveFilter, onClearAll }) => {
  if (!filters || filters.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="bg-gradient-to-r from-slate-800 to-slate-900 border border-slate-700 rounded-lg p-4 mb-4"
    >
      <div className="flex items-center justify-between">
        <div className="flex flex-wrap gap-2 flex-1">
          <span className="text-xs font-semibold text-slate-400 uppercase tracking-wide">
            🔍 Active Filters:
          </span>
          <AnimatePresence mode="popLayout">
            {filters.map((filter) => (
              <motion.div
                key={filter.id}
                initial={{ opacity: 0, scale: 0.8 }}
                animate={{ opacity: 1, scale: 1 }}
                exit={{ opacity: 0, scale: 0.8 }}
                className="flex items-center gap-2 px-3 py-1 bg-indigo-600/20 border border-indigo-500/40 rounded-full"
              >
                <span className="text-xs text-indigo-100">
                  {filter.column}: <strong>{filter.value}</strong>
                </span>
                <button
                  onClick={() => onRemoveFilter(filter.column)}
                  className="hover:text-indigo-300 transition-colors"
                >
                  <XMarkIcon className="w-3 h-3" />
                </button>
              </motion.div>
            ))}
          </AnimatePresence>
        </div>
        <button
          onClick={onClearAll}
          className="text-xs px-3 py-1 bg-red-500/20 border border-red-500/40 text-red-300 rounded-lg hover:bg-red-500/30 transition-colors"
        >
          Clear All
        </button>
      </div>
    </motion.div>
  );
});

FilterBar.displayName = 'FilterBar';

export default FilterBar;
