import React, { useMemo, useRef } from 'react';
import ReactECharts from 'echarts-for-react';
import * as echarts from 'echarts';

const CHART_COLORS = [
  '#00D4FF','#FF6B35','#7B2FBE','#00FF88',
  '#FFD700','#FF3366','#4ECDC4','#45B7D1',
  '#96CEB4','#FFEAA7','#DDA0DD','#98D8C8'
];

// ── Formatters ──────────────────────────────────────────────────────────────

const formatINR = (val) => {
  const n = Number(val);
  if (isNaN(n)) return String(val);
  if (Math.abs(n) >= 10000000) return `₹${(n/10000000).toFixed(2)}Cr`;
  if (Math.abs(n) >= 100000)   return `₹${(n/100000).toFixed(2)}L`;
  if (Math.abs(n) >= 1000)     return `₹${(n/1000).toFixed(1)}K`;
  return `₹${n.toLocaleString('en-IN')}`;
};

const truncate = (str, n = 15) => 
  str && str.length > n ? str.slice(0, n-2) + '..' : str;

// ── Base ECharts Config ──────────────────────────────────────────────────────

const baseConfig = {
  backgroundColor: 'transparent',
  animation: true,
  animationDuration: 800,
  animationEasing: 'cubicOut',
  textStyle: { 
    color: '#CBD5E1', 
    fontFamily: 'Inter, system-ui, sans-serif' 
  },
  tooltip: {
    backgroundColor: '#0D1440',
    borderColor: '#00D4FF',
    borderWidth: 1,
    textStyle: { color: '#E2E8F0', fontSize: 12 },
    confine: true,
  },
  grid: {
    left: '2%', right: '4%', 
    top: '12%', bottom: '8%',
    containLabel: true
  }
};

// ── Main ChartRenderer Component ─────────────────────────────────────────────

export default function ChartRenderer({ chartType = 'BAR_VERTICAL', config = {}, data = {}, height = '360px' }) {
  const chartRef = useRef(null);

  const option = useMemo(() => {
    try {
      const baseOpt = { ...baseConfig };

      switch(chartType) {
        case 'BAR_VERTICAL':
          return barVertical(baseOpt, data);
        case 'BAR_HORIZONTAL':
          return barHorizontal(baseOpt, data);
        case 'BAR_STACKED':
          return barStacked(baseOpt, data);
        case 'BAR_GROUPED':
          return barGrouped(baseOpt, data);
        case 'LINE':
          return lineChart(baseOpt, data, false);
        case 'LINE_SMOOTH':
          return lineChart(baseOpt, data, true);
        case 'LINE_AREA':
          return lineArea(baseOpt, data);
        case 'LINE_AREA_STACKED':
          return lineAreaStacked(baseOpt, data);
        case 'PIE':
          return pieChart(baseOpt, data);
        case 'DONUT':
          return donutChart(baseOpt, data);
        case 'DONUT_NESTED':
          return donutNested(baseOpt, data);
        case 'SCATTER':
          return scatterChart(baseOpt, data);
        case 'BUBBLE':
          return bubbleChart(baseOpt, data);
        case 'HEATMAP':
          return heatmapChart(baseOpt, data);
        case 'TREEMAP':
          return treemapChart(baseOpt, data);
        case 'FUNNEL':
          return funnelChart(baseOpt, data);
        case 'RADAR':
          return radarChart(baseOpt, data);
        case 'WATERFALL':
          return waterfallChart(baseOpt, data);
        case 'GAUGE':
          return gaugeChart(baseOpt, data);
        case 'CALENDAR_HEATMAP':
          return calendarHeatmap(baseOpt, data);
        case 'PARETO':
          return paretoChart(baseOpt, data);
        case 'BOXPLOT':
          return boxplotChart(baseOpt, data);
        case 'HISTOGRAM':
          return histogramChart(baseOpt, data);
        case 'SANKEY':
          return sankeyChart(baseOpt, data);
        default:
          return baseOpt;
      }
    } catch (error) {
      console.error(`ChartRenderer error for ${chartType}:`, error);
      return { ...baseConfig, title: { text: 'Error rendering chart' } };
    }
  }, [chartType, data]);

  return (
    <div style={{ width: '100%', height, backgroundColor: '#0D1440', borderRadius: '8px' }}>
      <ReactECharts
        ref={chartRef}
        option={option}
        style={{ width: '100%', height: '100%' }}
        opts={{ renderer: 'canvas' }}
      />
    </div>
  );
}

// ── Chart implementations ────────────────────────────────────────────────────

function barVertical(base, data) {
  return {
    ...base,
    xAxis: {
      type: 'category',
      data: (data.labels || []).map(l => truncate(String(l), 20)),
      axisLabel: { color: '#94A3B8', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 },
    },
    series: [{
      type: 'bar',
      data: data.values || [],
      barMaxWidth: 60,
      itemStyle: {
        borderRadius: [4, 4, 0, 0],
        color: (params) => CHART_COLORS[params.dataIndex % CHART_COLORS.length]
      },
      label: {
        show: true, position: 'top',
        formatter: (p) => formatINR(p.value),
        color: '#CBD5E1', fontSize: 10
      }
    }]
  };
}

function barHorizontal(base, data) {
  return {
    ...base,
    xAxis: {
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 },
    },
    yAxis: {
      type: 'category',
      data: (data.labels || []).map(l => truncate(String(l), 20)),
      axisLabel: { color: '#94A3B8', fontSize: 10 },
    },
    series: [{
      type: 'bar',
      data: data.values || [],
      barMaxWidth: 40,
      itemStyle: {
        borderRadius: [0, 4, 4, 0],
        color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
          { offset: 0, color: '#0066FF' },
          { offset: 1, color: '#00D4FF' }
        ])
      },
      label: { 
        show: true, position: 'right',
        formatter: (p) => formatINR(p.value),
        color: '#CBD5E1', fontSize: 10
      }
    }]
  };
}

function barStacked(base, data) {
  const series = (data.series || []).map((s, i) => ({
    name: s.name,
    type: 'bar',
    stack: 'total',
    data: s.values,
    itemStyle: { 
      color: CHART_COLORS[i % CHART_COLORS.length],
      borderRadius: i === (data.series || []).length - 1 ? [4,4,0,0] : [0,0,0,0]
    }
  }));

  return {
    ...base,
    xAxis: {
      type: 'category',
      data: (data.labels || []).map(l => truncate(String(l), 20)),
      axisLabel: { color: '#94A3B8', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 },
    },
    legend: { textStyle: { color: '#94A3B8' } },
    series
  };
}

function barGrouped(base, data) {
  const series = (data.series || []).map((s, i) => ({
    name: s.name,
    type: 'bar',
    data: s.values,
    itemStyle: { 
      color: CHART_COLORS[i % CHART_COLORS.length],
      borderRadius: [3,3,0,0]
    }
  }));

  return {
    ...base,
    xAxis: {
      type: 'category',
      data: (data.labels || []).map(l => truncate(String(l), 20)),
      axisLabel: { color: '#94A3B8', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 },
    },
    legend: { textStyle: { color: '#94A3B8' } },
    series
  };
}

function lineChart(base, data, smooth = false) {
  return {
    ...base,
    xAxis: {
      type: 'category',
      data: (data.labels || []).map(l => truncate(String(l), 20)),
      axisLabel: { color: '#94A3B8', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 },
    },
    series: [{
      type: 'line',
      data: data.values || [],
      smooth: smooth,
      symbol: 'circle',
      symbolSize: 6,
      lineStyle: { color: '#00D4FF', width: 2.5 },
      itemStyle: { color: '#00D4FF', borderColor: '#0D1440', borderWidth: 2 },
      emphasis: { scale: true }
    }]
  };
}

function lineArea(base, data) {
  return {
    ...base,
    xAxis: {
      type: 'category',
      data: (data.labels || []).map(l => truncate(String(l), 20)),
      axisLabel: { color: '#94A3B8', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 },
    },
    series: [{
      type: 'line',
      data: data.values || [],
      smooth: true,
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(0,212,255,0.4)' },
          { offset: 1, color: 'rgba(0,212,255,0.02)' }
        ])
      },
      lineStyle: { color: '#00D4FF', width: 2 },
      itemStyle: { color: '#00D4FF' }
    }]
  };
}

function lineAreaStacked(base, data) {
  const series = (data.series || []).map((s, i) => ({
    name: s.name,
    type: 'line',
    stack: 'total',
    smooth: true,
    areaStyle: { color: `${CHART_COLORS[i]}44` },
    lineStyle: { color: CHART_COLORS[i], width: 1.5 },
    data: s.values
  }));

  return {
    ...base,
    xAxis: {
      type: 'category',
      data: (data.labels || []).map(l => truncate(String(l), 20)),
      axisLabel: { color: '#94A3B8', fontSize: 10 },
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 },
    },
    legend: { textStyle: { color: '#94A3B8' } },
    series
  };
}

function pieChart(base, data) {
  return {
    ...base,
    series: [{
      type: 'pie',
      radius: '65%',
      center: ['50%', '55%'],
      data: (data.labels || []).map((label, i) => ({
        name: truncate(String(label), 20),
        value: data.values[i] || 0,
        itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] }
      })),
      label: { 
        formatter: '{b}: {d}%',
        color: '#CBD5E1', fontSize: 11
      },
      emphasis: {
        itemStyle: { shadowBlur: 10, shadowColor: 'rgba(0,212,255,0.5)' }
      }
    }]
  };
}

function donutChart(base, data) {
  const total = (data.values || []).reduce((a, b) => a + (b || 0), 0);
  return {
    ...base,
    series: [{
      type: 'pie',
      radius: ['42%', '68%'],
      center: ['50%', '55%'],
      data: (data.labels || []).map((label, i) => ({
        name: truncate(String(label), 20),
        value: data.values[i] || 0,
        itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] }
      })),
      label: { 
        formatter: '{b}\n{d}%',
        color: '#CBD5E1', fontSize: 10, lineHeight: 16
      },
      labelLine: { length: 12, length2: 8 }
    }],
    graphic: [{
      type: 'text',
      left: 'center', top: 'middle',
      style: { 
        text: formatINR(total),
        fill: '#00D4FF', fontSize: 16, fontWeight: 'bold'
      }
    }]
  };
}

function donutNested(base, data) {
  const outerData = data.outer || [];
  const innerData = data.inner || [];

  return {
    ...base,
    series: [
      {
        name: 'Inner',
        type: 'pie',
        radius: ['25%', '45%'],
        data: innerData.map((d, i) => ({ 
          name: truncate(String(d.name), 12),
          value: d.value,
          itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] }
        })),
        label: { show: false }
      },
      {
        name: 'Outer', 
        type: 'pie',
        radius: ['48%', '68%'],
        data: outerData.map((d, i) => ({
          name: truncate(String(d.name), 12),
          value: d.value,
          itemStyle: { color: `${CHART_COLORS[i % CHART_COLORS.length]}99` }
        })),
        label: { formatter: '{b}: {d}%', fontSize: 10, color: '#CBD5E1' }
      }
    ]
  };
}

function scatterChart(base, data) {
  return {
    ...base,
    xAxis: { 
      type: 'value',
      name: data.x_label || 'X',
      nameLocation: 'middle',
      nameGap: 30,
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      name: data.y_label || 'Y',
      nameLocation: 'middle',
      nameGap: 50,
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 }
    },
    series: [{
      type: 'scatter',
      data: (data.data || []).slice(0, 200),
      symbolSize: 8,
      itemStyle: { 
        color: '#00D4FF', opacity: 0.7,
        borderColor: '#0066FF', borderWidth: 1
      },
      emphasis: { symbolSize: 14 }
    }]
  };
}

function bubbleChart(base, data) {
  const bubbleData = data.data || [];
  const maxZ = Math.max(...bubbleData.map((d, i) => Array.isArray(d) ? d[2] : 0), 1);

  return {
    ...base,
    xAxis: { 
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 }
    },
    series: [{
      type: 'scatter',
      data: bubbleData.slice(0, 100),
      symbolSize: (dataItem) => {
        const sz = Array.isArray(dataItem) ? dataItem[2] : 0;
        return Math.sqrt(sz / maxZ) * 60 + 8;
      },
      itemStyle: {
        color: (params) => CHART_COLORS[params.dataIndex % CHART_COLORS.length],
        opacity: 0.8
      }
    }]
  };
}

function heatmapChart(base, data) {
  const minVal = data.min || 0;
  const maxVal = data.max || 1;

  return {
    ...base,
    visualMap: {
      min: minVal, max: maxVal,
      calculable: true,
      orient: 'horizontal',
      left: 'center', bottom: 0,
      inRange: { 
        color: ['#0A0F2C', '#0066FF', '#00D4FF', '#00FF88']
      },
      textStyle: { color: '#CBD5E1' }
    },
    xAxis: {
      type: 'category',
      data: data.x_labels || [],
      axisLabel: { color: '#94A3B8', fontSize: 9, rotate: 45 }
    },
    yAxis: {
      type: 'category',
      data: data.y_labels || [],
      axisLabel: { color: '#94A3B8', fontSize: 9 }
    },
    series: [{
      type: 'heatmap',
      data: data.data || [],
      label: { show: true, formatter: (p) => formatINR(p.data[2]), fontSize: 9 },
      emphasis: { itemStyle: { shadowBlur: 10 } }
    }]
  };
}

function treemapChart(base, data) {
  return {
    ...base,
    series: [{
      type: 'treemap',
      data: (data.labels || []).map((label, i) => ({
        name: truncate(String(label), 18),
        value: data.values ? data.values[i] : 0,
        itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] }
      })),
      label: {
        show: true,
        formatter: (p) => `${truncate(p.name, 14)}\n${formatINR(p.value)}`,
        color: '#fff', fontSize: 11
      },
      breadcrumb: { show: false },
      roam: false
    }]
  };
}

function funnelChart(base, data) {
  return {
    ...base,
    series: [{
      type: 'funnel',
      left: '10%', width: '80%',
      minSize: '10%', maxSize: '100%',
      sort: 'descending',
      data: (data.labels || []).map((label, i) => ({
        name: truncate(String(label), 18),
        value: data.values ? data.values[i] : 0,
        itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] }
      })),
      label: {
        position: 'inside',
        formatter: (p) => `${truncate(p.name, 14)}\n${formatINR(p.value)}`,
        color: '#fff', fontSize: 11
      }
    }]
  };
}

function radarChart(base, data) {
  const indicators = (data.indicators || []).map(ind => ({
    name: String(ind.name || '').slice(0, 12),
    max: ind.max || 100
  }));

  const series = (data.series || []).map((s, i) => ({
    name: String(s.name || '').slice(0, 20),
    value: s.values || [],
    lineStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] },
    areaStyle: { color: `${CHART_COLORS[i % CHART_COLORS.length]}33` }
  }));

  return {
    ...base,
    radar: {
      indicator: indicators,
      shape: 'polygon',
      splitNumber: 4,
      axisName: { color: '#94A3B8', fontSize: 11 },
      splitLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: 'rgba(255,255,255,0.1)' } }
    },
    legend: { textStyle: { color: '#94A3B8' } },
    series: [{
      type: 'radar',
      data: series
    }]
  };
}

function waterfallChart(base, data) {
  const waterfallData = data.data || [];

  return {
    ...base,
    xAxis: {
      type: 'category',
      data: (data.labels || []).map(l => truncate(String(l), 20)),
      axisLabel: { color: '#94A3B8', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 }
    },
    series: [
      {
        type: 'bar',
        stack: 'total',
        data: waterfallData.map(d => d.base || 0),
        itemStyle: { color: 'transparent', borderColor: 'transparent' }
      },
      {
        type: 'bar',
        stack: 'total',
        data: waterfallData.map(d => ({
          value: d.delta || 0,
          itemStyle: {
            color: (d.delta || 0) >= 0 ? '#00FF88' : '#FF3366',
            borderRadius: (d.delta || 0) >= 0 ? [4,4,0,0] : [0,0,4,4]
          }
        })),
        label: {
          show: true,
          position: (params) => (params.data.value || 0) >= 0 ? 'top' : 'bottom',
          formatter: (p) => formatINR(p.data.value),
          color: '#CBD5E1', fontSize: 10
        }
      }
    ]
  };
}

function gaugeChart(base, data) {
  return {
    ...base,
    series: [{
      type: 'gauge',
      startAngle: 205,
      endAngle: -25,
      min: 0,
      max: 100,
      radius: '85%',
      pointer: {
        length: '65%',
        width: 6,
        itemStyle: { color: '#00D4FF' }
      },
      progress: {
        show: true,
        width: 18,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 1, 0, [
            { offset: 0, color: '#0066FF' },
            { offset: 1, color: '#00FF88' }
          ])
        }
      },
      axisLine: {
        lineStyle: { 
          width: 18,
          color: [[1, 'rgba(255,255,255,0.08)']]
        }
      },
      axisTick: { show: false },
      splitLine: { show: false },
      axisLabel: { show: false },
      detail: {
        formatter: '{value}%',
        color: '#00D4FF',
        fontSize: 28,
        fontWeight: 'bold',
        offsetCenter: [0, '30%']
      },
      data: [{ value: data.value || 0, name: data.label || 'Value' }]
    }]
  };
}

function calendarHeatmap(base, data) {
  const yearStr = data.year || '2024';
  const maxDayValue = data.max || 1;

  return {
    ...base,
    calendar: [{
      range: yearStr,
      cellSize: ['auto', 16],
      itemStyle: { borderColor: '#0A0F2C', borderWidth: 2 },
      dayLabel: { color: '#64748B', fontSize: 10 },
      monthLabel: { color: '#94A3B8', fontSize: 11 },
      yearLabel: { show: false },
      splitLine: { show: false }
    }],
    visualMap: {
      min: 0,
      max: maxDayValue,
      calculable: false,
      orient: 'horizontal',
      left: 'center',
      bottom: 0,
      inRange: { color: ['#0D1440', '#0066FF', '#00D4FF', '#00FF88'] },
      textStyle: { color: '#94A3B8' }
    },
    series: [{
      type: 'heatmap',
      coordinateSystem: 'calendar',
      data: (data.data || []).map(d => [d[0], Number(d[1])])
    }]
  };
}

function paretoChart(base, data) {
  const cumulativePercent = data.cumulative || [];

  return {
    ...base,
    xAxis: {
      type: 'category',
      data: (data.labels || []).map(l => truncate(String(l), 20)),
      axisLabel: { color: '#94A3B8', fontSize: 10 }
    },
    yAxis: [
      {
        type: 'value',
        axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 }
      },
      {
        type: 'value',
        min: 0,
        max: 100,
        axisLabel: { formatter: '{value}%', color: '#FFD700', fontSize: 10 }
      }
    ],
    legend: { textStyle: { color: '#94A3B8' } },
    series: [
      {
        name: 'Amount',
        type: 'bar',
        data: data.values || [],
        yAxisIndex: 0,
        itemStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: '#00D4FF' },
            { offset: 1, color: '#0066FF' }
          ]),
          borderRadius: [4, 4, 0, 0]
        }
      },
      {
        name: 'Cumulative %',
        type: 'line',
        data: cumulativePercent,
        yAxisIndex: 1,
        smooth: false,
        lineStyle: { color: '#FFD700', width: 2 },
        itemStyle: { color: '#FFD700' },
        markLine: {
          silent: true,
          data: [{ yAxis: 80 }],
          lineStyle: { color: '#FF3366', type: 'dashed' },
          label: { formatter: '80%', color: '#FF3366' }
        }
      }
    ]
  };
}

function boxplotChart(base, data) {
  return {
    ...base,
    xAxis: {
      type: 'category',
      data: data.labels || [],
      axisLabel: { color: '#94A3B8', fontSize: 10 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { formatter: formatINR, color: '#94A3B8', fontSize: 10 }
    },
    series: [{
      type: 'boxplot',
      data: data.data || [],
      itemStyle: {
        color: 'rgba(0,212,255,0.2)',
        borderColor: '#00D4FF',
        borderWidth: 1.5
      },
      emphasis: {
        itemStyle: { color: 'rgba(0,212,255,0.4)' }
      }
    }]
  };
}

function histogramChart(base, data) {
  const counts = data.counts || [];
  const bins = data.bins || [];

  return {
    ...base,
    xAxis: {
      type: 'category',
      data: bins.map(b => formatINR(b[0])),
      axisLabel: { color: '#94A3B8', fontSize: 9, rotate: 35 }
    },
    yAxis: {
      type: 'value',
      axisLabel: { color: '#94A3B8', fontSize: 10 }
    },
    series: [{
      type: 'bar',
      data: counts,
      barWidth: '99%',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#7B2FBE' },
          { offset: 1, color: '#4ECDC4' }
        ]),
        borderRadius: [3, 3, 0, 0]
      },
      label: { show: false }
    }]
  };
}

function sankeyChart(base, data) {
  const nodes = (data.nodes || []).map((n, i) => ({
    name: String(n).slice(0, 20),
    itemStyle: { color: CHART_COLORS[i % CHART_COLORS.length] }
  }));

  const links = (data.links || []).map(l => ({
    source: String(l.source).slice(0, 20),
    target: String(l.target).slice(0, 20),
    value: l.value || 0
  }));

  return {
    ...base,
    series: [{
      type: 'sankey',
      layout: 'none',
      emphasis: { focus: 'adjacency' },
      data: nodes,
      links: links,
      lineStyle: {
        color: 'gradient',
        opacity: 0.4,
        curveness: 0.5
      },
      label: { color: '#CBD5E1', fontSize: 11 }
    }]
  };
}
