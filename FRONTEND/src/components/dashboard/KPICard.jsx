import React from 'react';
import { motion } from 'framer-motion';
import { ArrowUpIcon, ArrowDownIcon, SparklesIcon } from '@heroicons/react/24/outline';

const KPICard = ({
  title,
  value,
  trend = 0,
  unit = '',
  icon: Icon = SparklesIcon,
  accentColor = '#00D4FF',
}) => {
  const isPositive = trend >= 0;
  const absTrend = Math.abs(trend).toFixed(1);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      style={{
        background: 'rgba(30,41,59,0.5)',
        border: '1px solid rgba(0,212,255,0.2)',
        borderRadius: 14,
        padding: '20px 20px 18px',
        boxShadow: '0 0 20px rgba(0,212,255,0.05)',
        display: 'flex',
        flexDirection: 'column',
        gap: 6,
        minWidth: 0,
        overflow: 'hidden',
        position: 'relative',
      }}
    >
      {/* Glow accent border-top */}
      <div style={{
        position: 'absolute',
        top: 0, left: 0, right: 0,
        height: 3,
        background: `linear-gradient(90deg, transparent, ${accentColor}, transparent)`,
        borderRadius: '14px 14px 0 0',
        opacity: 0.7,
      }} />

      {/* Icon + trend row */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <div style={{
          padding: 8,
          borderRadius: 10,
          background: 'rgba(0,212,255,0.08)',
          border: '1px solid rgba(0,212,255,0.18)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}>
          <Icon style={{ width: 18, height: 18, color: accentColor }} />
        </div>

        {trend !== 0 && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 3,
            fontSize: 12,
            fontWeight: 700,
            color: isPositive ? '#00FF88' : '#FF3366',
          }}>
            {isPositive
              ? <ArrowUpIcon style={{ width: 13, height: 13 }} />
              : <ArrowDownIcon style={{ width: 13, height: 13 }} />
            }
            {absTrend}%
          </div>
        )}
      </div>

      {/* Big value */}
      <div style={{
        fontSize: 36,
        fontWeight: 800,
        color: '#ffffff',
        lineHeight: 1.1,
        letterSpacing: -0.5,
        marginTop: 10,
        whiteSpace: 'nowrap',
        overflow: 'hidden',
        textOverflow: 'ellipsis',
      }}>
        {typeof value === 'number' ? value.toLocaleString('en-IN') : value}
        {unit && (
          <span style={{ fontSize: 16, fontWeight: 500, color: 'rgba(255,255,255,0.5)', marginLeft: 4 }}>
            {unit}
          </span>
        )}
      </div>

      {/* Label */}
      <div style={{
        fontSize: 11,
        fontWeight: 600,
        color: 'rgba(255,255,255,0.45)',
        letterSpacing: 1.2,
        textTransform: 'uppercase',
        marginTop: 2,
      }}>
        {title}
      </div>
    </motion.div>
  );
};

export default KPICard;
