import React, { memo } from 'react';
import { motion } from 'framer-motion';
import { ChevronRightIcon, HomeIcon } from '@heroicons/react/24/solid';

const Breadcrumb = memo(({ path = [], onNavigate, onReset }) => {
  if (!path || path.length === 0) {
    return null;
  }

  return (
    <motion.div
      initial={{ opacity: 0, y: -10 }}
      animate={{ opacity: 1, y: 0 }}
      className="flex items-center gap-2 bg-slate-800/50 border border-slate-700 rounded-lg p-3 mb-4 overflow-x-auto"
    >
      <button
        onClick={onReset}
        className="flex items-center gap-1 text-sm text-slate-400 hover:text-slate-200 transition-colors whitespace-nowrap"
      >
        <HomeIcon className="w-4 h-4" />
        All Data
      </button>

      {path.map((level, idx) => (
        <div key={idx} className="flex items-center gap-2">
          <ChevronRightIcon className="w-4 h-4 text-slate-600" />
          <button
            onClick={() => onNavigate(idx)}
            className="text-sm text-slate-300 hover:text-slate-100 transition-colors whitespace-nowrap"
          >
            {level}
          </button>
        </div>
      ))}
    </motion.div>
  );
});

Breadcrumb.displayName = 'Breadcrumb';

export default Breadcrumb;
