

import React, { useState, memo } from 'react';
import { motion } from 'framer-motion';
import { TrashIcon } from '@heroicons/react/24/outline';
import EChartsWrapper from './EChartsWrapper';

const ChartCard = memo(({
  chart,
  onUnpin,
  onFilterClick,
  isDragging = false,
}) => {
  const [showActions, setShowActions] = useState(false);

  const handleChartClick = (params) => {
    if (params.value && params.name) {
      onFilterClick?.(chart.xKey, params.name);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ type: 'spring', stiffness: 250, damping: 28 }}
      onMouseEnter={() => setShowActions(true)}
      onMouseLeave={() => setShowActions(false)}
      style={{
        position: 'relative',
        minHeight: '320px',
        height: '100%',
        background: 'rgba(15,23,42,0.4)',
        borderRadius: '12px',
        border: '1px solid rgba(0,212,255,0.1)',
      }}
    >
      <EChartsWrapper
        chartConfig={chart}
        title={chart.title}
        height={340}
        onClick={handleChartClick}
        isDragging={isDragging}
      />

      {/* Remove button */}
      <motion.div
        initial={{ opacity: 0 }}
        animate={{ opacity: showActions ? 1 : 0 }}
        transition={{ duration: 0.15 }}
        style={{ position: 'absolute', top: 10, right: 10 }}
      >
        <motion.button
          whileHover={{ scale: 1.1 }}
          whileTap={{ scale: 0.9 }}
          onClick={() => onUnpin(chart.id)}
          title="Remove from dashboard"
          style={{
            padding: '6px',
            borderRadius: '6px',
            background: 'rgba(255,51,102,0.2)',
            border: '1px solid rgba(255,51,102,0.4)',
            cursor: 'pointer',
            display: 'flex',
            alignItems: 'center',
          }}
        >
          <TrashIcon style={{ width: 14, height: 14, color: '#FF3366' }} />
        </motion.button>
      </motion.div>
    </motion.div>
  );
});

ChartCard.displayName = 'ChartCard';

export default ChartCard;
