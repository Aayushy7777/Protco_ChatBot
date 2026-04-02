import React, { useState, useMemo } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  FunnelIcon,
  XMarkIcon,
  ChevronDownIcon,
} from '@heroicons/react/24/outline';

const AdvancedFilterPanel = ({ 
  data = [], 
  onFilterChange, 
  categoricalColumns = [],
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedFilters, setSelectedFilters] = useState({});

  // Extract unique values for each categorical column
  const filterOptions = useMemo(() => {
    const options = {};
    categoricalColumns.forEach(col => {
      const unique = [...new Set(data.map(row => row[col]))].filter(Boolean);
      options[col] = unique.slice(0, 20); // Limit to 20 unique values
    });
    return options;
  }, [data, categoricalColumns]);

  const handleFilterSelect = (column, value) => {
    setSelectedFilters(prev => {
      const updated = { ...prev };
      if (updated[column]?.includes(value)) {
        updated[column] = updated[column].filter(v => v !== value);
        if (updated[column].length === 0) delete updated[column];
      } else {
        updated[column] = [...(updated[column] || []), value];
      }
      onFilterChange?.(updated);
      return updated;
    });
  };

  const handleClearAll = () => {
    setSelectedFilters({});
    onFilterChange?.({});
  };

  const activeFilterCount = Object.values(selectedFilters).reduce((sum, arr) => sum + arr.length, 0);

  return (
    <div className="mb-6">
      {/* Filter Button */}
      <motion.button
        whileHover={{ scale: 1.02 }}
        whileTap={{ scale: 0.98 }}
        onClick={() => setIsOpen(!isOpen)}
        className={`flex items-center gap-2 px-4 py-2 rounded-lg transition-all ${
          isOpen
            ? 'bg-indigo-600 text-white border border-indigo-500'
            : 'bg-slate-700/50 text-slate-300 border border-slate-600/30 hover:border-slate-500/50'
        }`}
      >
        <FunnelIcon className="w-4 h-4" />
        <span className="text-sm font-medium">Filters</span>
        {activeFilterCount > 0 && (
          <span className="ml-2 px-2 py-0.5 bg-red-600 text-white text-xs rounded-full">
            {activeFilterCount}
          </span>
        )}
        <ChevronDownIcon className={`w-4 h-4 ml-auto transition-transform ${isOpen ? 'rotate-180' : ''}`} />
      </motion.button>

      {/* Filter Panel */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, height: 0 }}
            animate={{ opacity: 1, height: 'auto' }}
            exit={{ opacity: 0, height: 0 }}
            className="mt-2 bg-slate-800/80 border border-slate-600/30 rounded-lg p-4 backdrop-blur-sm"
          >
            {Object.keys(filterOptions).length === 0 ? (
              <p className="text-sm text-slate-400">No categorical columns available</p>
            ) : (
              <>
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                  {Object.entries(filterOptions).map(([column, values]) => (
                    <div key={column} className="space-y-2">
                      <p className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
                        {column}
                      </p>
                      <div className="space-y-1 max-h-40 overflow-y-auto">
                        {values.map(value => (
                          <label key={value} className="flex items-center gap-2 cursor-pointer hover:bg-slate-700/50 p-2 rounded transition-colors">
                            <input
                              type="checkbox"
                              checked={selectedFilters[column]?.includes(value) || false}
                              onChange={() => handleFilterSelect(column, value)}
                              className="rounded border-slate-500 text-indigo-600 cursor-pointer"
                            />
                            <span className="text-sm text-slate-300 flex-1 truncate">
                              {String(value).slice(0, 30)}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>

                {activeFilterCount > 0 && (
                  <motion.button
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    onClick={handleClearAll}
                    className="mt-4 w-full px-3 py-2 bg-slate-700/50 hover:bg-slate-600 text-slate-300 rounded-lg text-sm transition-colors flex items-center justify-center gap-2"
                  >
                    <XMarkIcon className="w-4 h-4" />
                    Clear all filters
                  </motion.button>
                )}
              </>
            )}
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};

export default AdvancedFilterPanel;
