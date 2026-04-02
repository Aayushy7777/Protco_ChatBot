import React, { useMemo, memo } from 'react';
import ReactECharts from 'echarts-for-react';
import { motion } from 'framer-motion';

const CHART_COLORS = [
  '#00D4FF', '#FFD700', '#00FF88', '#FF6B35',
  '#7B2FBE', '#FF3366', '#4ECDC4', '#45B7D1',
  '#96CEB4',
];

const BG_COLOR = 'transparent';
const CARD_COLOR = 'rgba(15,23,42,0.4)';

const formatINR = (value) => {
  const n = Number(value) || 0;
  if (Math.abs(n) >= 10_000_000) return `₹${(n / 10_000_000).toFixed(2)}Cr`;
  if (Math.abs(n) >= 100_000) return `₹${(n / 100_000).toFixed(2)}L`;
  if (Math.abs(n) >= 1_000) return `₹${(n / 1_000).toFixed(1)}K`;
  return `₹${n.toFixed(0)}`;
};

const isCurrencyCol = (key) =>
  /amount|revenue|sales|cost|price|profit|income|expense|total|inr|₹/i.test(String(key || ''));

const smartFormat = (value, key) => {
  if (isCurrencyCol(key)) return formatINR(value);
  const n = Number(value || 0);
  if (Math.abs(n) >= 1_000_000) return `${(n / 1_000_000).toFixed(1)}M`;
  if (Math.abs(n) >= 1_000) return `${(n / 1_000).toFixed(1)}K`;
  return n.toLocaleString('en-IN');
};

const EChartsWrapper = memo(({
  chartConfig,
  title,
  height = 320,
  onClick,
  isDragging = false,
}) => {
  const option = useMemo(() => buildEChartsOption(chartConfig), [chartConfig]);

  const handleChartClick = (params) => {
    if (onClick && params.componentType === 'series') {
      onClick(params);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.95 }}
      animate={{ opacity: 1, scale: 1 }}
      transition={{ duration: 0.3 }}
      style={{
        background: CARD_COLOR,
        border: '1px solid rgba(0,212,255,0.1)',
        borderRadius: '12px',
        overflow: 'hidden',
        boxShadow: '0 0 18px rgba(0,212,255,0.05)',
        height,
        opacity: isDragging ? 0.75 : 1,
      }}
    >
      <div style={{ width: '100%', height: '100%' }}>
        <ReactECharts
          option={option}
          style={{ height: '100%' }}
          onEvents={{ click: handleChartClick }}
          opts={{ renderer: 'canvas' }}
          notMerge={true}
          lazyUpdate={true}
        />
      </div>
    </motion.div>
  );
});

EChartsWrapper.displayName = 'EChartsWrapper';

export function buildEChartsOption(config) {
  if (!config) return {};

  const {
    type = 'bar',
    title = '',
    xKey = '',
    yKey = '',
    data = [],
  } = config;

  const isHorizontal = type === 'bar_horizontal' || type === 'bar_horizontal_colored';
  const isColored = type === 'bar_colored' || type === 'bar_horizontal_colored';
  const isPie = type === 'pie';
  const isLine = type === 'line' || type === 'area';

  const AXIS_COLOR = 'rgba(255,255,255,0.15)';
  const LABEL_COLOR = '#ffffff';
  const GRID_LINE_COLOR = 'rgba(255,255,255,0.07)';

  const baseTextStyle = { color: LABEL_COLOR, fontSize: 11 };

  const baseOption = {
    backgroundColor: BG_COLOR,
    animation: true,
    animationDuration: 600,
    title: title ? {
      text: title,
      left: 'center',
      top: 8,
      textStyle: {
        color: '#ffffff',
        fontSize: 13,
        fontWeight: 'bold',
      },
    } : undefined,
    tooltip: {
      trigger: isPie ? 'item' : 'axis',
      backgroundColor: 'rgba(10,15,44,0.95)',
      borderColor: 'rgba(0,212,255,0.4)',
      textStyle: { color: '#ffffff', fontSize: 12 },
      axisPointer: { type: 'shadow' },
    },
    grid: {
      left: isHorizontal ? '2%' : '4%',
      right: isHorizontal ? '8%' : '4%',
      top: title ? '18%' : '8%',
      bottom: '6%',
      containLabel: true,
    },
  };

  // ── PIE / DONUT ──────────────────────────────────────────────────────────────
  if (isPie) {
    return {
      ...baseOption,
      tooltip: {
        trigger: 'item',
        backgroundColor: 'rgba(10,15,44,0.95)',
        borderColor: 'rgba(0,212,255,0.4)',
        textStyle: { color: '#ffffff', fontSize: 12 },
        formatter: (params) => {
          const formatted = smartFormat(params.value, yKey);
          return `${params.marker}<b>${params.name}</b><br/>${yKey}: ${formatted} (${params.percent}%)`;
        },
      },
      legend: {
        orient: 'horizontal',
        bottom: 4,
        textStyle: { color: 'rgba(255,255,255,0.7)', fontSize: 10 },
        itemWidth: 10,
        itemHeight: 10,
      },
      series: [{
        type: 'pie',
        radius: ['35%', '70%'],
        center: ['50%', '50%'],
        data: data.map((item, idx) => ({
          value: item[yKey],
          name: item[xKey],
          itemStyle: { color: CHART_COLORS[idx % CHART_COLORS.length] },
        })),
        label: {
          show: true,
          color: '#ffffff',
          fontSize: 10,
          formatter: '{b}\n{d}%',
        },
        emphasis: {
          itemStyle: {
            shadowBlur: 12,
            shadowColor: 'rgba(0,212,255,0.4)',
          },
        },
        itemStyle: {
          borderColor: BG_COLOR,
          borderWidth: 2,
        },
      }],
    };
  }

  // ── LINE / AREA ──────────────────────────────────────────────────────────────
  if (isLine) {
    return {
      ...baseOption,
      xAxis: {
        type: 'category',
        data: data.map(d => String(d[xKey] ?? '').slice(0, 20)),
        axisLabel: { ...baseTextStyle, rotate: 30 },
        axisLine: { lineStyle: { color: AXIS_COLOR } },
        axisTick: { show: false },
      },
      yAxis: {
        type: 'value',
        axisLabel: {
          ...baseTextStyle,
          formatter: (v) => smartFormat(v, yKey),
        },
        axisLine: { lineStyle: { color: AXIS_COLOR } },
        splitLine: { lineStyle: { color: GRID_LINE_COLOR } },
      },
      series: [{
        type: 'line',
        data: data.map(d => d[yKey]),
        smooth: true,
        lineStyle: { color: CHART_COLORS[0], width: 2.5 },
        itemStyle: { color: CHART_COLORS[0] },
        areaStyle: {
          color: {
            type: 'linear', x: 0, y: 0, x2: 0, y2: 1,
            colorStops: [
              { offset: 0, color: 'rgba(0,212,255,0.3)' },
              { offset: 1, color: 'rgba(0,212,255,0.01)' },
            ],
          },
        },
        symbol: 'circle',
        symbolSize: 6,
      }],
    };
  }

  // ── HORIZONTAL BARS ──────────────────────────────────────────────────────────
  if (isHorizontal) {
    return {
      ...baseOption,
      yAxis: {
        type: 'category',
        data: data.map(d => String(d[xKey] ?? '').slice(0, 22)),
        axisLabel: { ...baseTextStyle, fontSize: 11 },
        axisLine: { lineStyle: { color: AXIS_COLOR } },
        axisTick: { show: false },
        inverse: false,
      },
      xAxis: {
        type: 'value',
        axisLabel: {
          ...baseTextStyle,
          formatter: (v) => smartFormat(v, yKey),
        },
        axisLine: { lineStyle: { color: AXIS_COLOR } },
        splitLine: { lineStyle: { color: GRID_LINE_COLOR } },
      },
      series: [{
        type: 'bar',
        data: data.map((d, idx) => ({
          value: d[yKey],
          itemStyle: {
            color: isColored
              ? CHART_COLORS[idx % CHART_COLORS.length]
              : {
                  type: 'linear', x: 0, y: 0, x2: 1, y2: 0,
                  colorStops: [
                    { offset: 0, color: CHART_COLORS[0] },
                    { offset: 1, color: CHART_COLORS[6] },
                  ],
                },
            borderRadius: [0, 4, 4, 0],
          },
        })),
        label: {
          show: true,
          position: 'right',
          color: '#ffffff',
          fontSize: 10,
          formatter: (params) => smartFormat(params.value, yKey),
        },
        barMaxWidth: 28,
        emphasis: { focus: 'self' },
      }],
    };
  }

  // ── DEFAULT: VERTICAL BAR ────────────────────────────────────────────────────
  const isPosneg = config.title?.toLowerCase().includes('pos/neg');

  return {
    ...baseOption,
    xAxis: {
      type: 'category',
      data: data.map(d => String(d[xKey] ?? '').slice(0, 18)),
      axisLabel: { ...baseTextStyle, rotate: 30, fontSize: 10 },
      axisLine: { lineStyle: { color: AXIS_COLOR } },
      axisTick: { show: false },
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        ...baseTextStyle,
        formatter: (v) => smartFormat(v, yKey),
      },
      axisLine: { lineStyle: { color: AXIS_COLOR } },
      splitLine: { lineStyle: { color: GRID_LINE_COLOR } },
    },
    series: [{
      type: 'bar',
      data: data.map((d, idx) => {
        const val = Number(d[yKey]) || 0;
        let color;
        if (isPosneg) {
          color = val >= 0 ? '#00FF88' : '#FF3366';
        } else if (isColored) {
          color = CHART_COLORS[idx % CHART_COLORS.length];
        } else {
          color = CHART_COLORS[0];
        }
        return {
          value: val,
          itemStyle: {
            color,
            borderRadius: val >= 0 ? [4, 4, 0, 0] : [0, 0, 4, 4],
          },
        };
      }),
      label: {
        show: false,
      },
      barMaxWidth: 40,
      emphasis: { focus: 'self' },
    }],
  };
}

export default EChartsWrapper;
