import React, { memo, useCallback, useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDashboardStore } from '../../store/dashboardStore';
import ChartRenderer from './ChartRenderer';
import KPICard from './KPICard';
import { SparklesIcon, XMarkIcon } from '@heroicons/react/24/outline';

const API = 'http://localhost:8000';
const CHART_COLORS = ['#00D4FF','#FF6B35','#7B2FBE','#00FF88','#FFD700','#FF3366','#4ECDC4','#45B7D1','#96CEB4'];

const GM_NAVY    = '#0A0F2C';
const GM_CYAN    = '#00D4FF';
const GM_GOLD    = '#FFD700';
const GM_CARD    = 'rgba(16,22,50,0.7)';

// Chart type cycling
const CHART_TYPE_CYCLE = {
  'BAR_VERTICAL':   'BAR_HORIZONTAL',
  'BAR_HORIZONTAL': 'BAR_STACKED',
  'BAR_STACKED':    'BAR_GROUPED',
  'BAR_GROUPED':    'BAR_VERTICAL',
  'PIE':            'DONUT',
  'DONUT':          'TREEMAP',
  'TREEMAP':        'FUNNEL',
  'FUNNEL':         'PIE',
  'LINE':           'LINE_SMOOTH',
  'LINE_SMOOTH':    'LINE_AREA',
  'LINE_AREA':      'LINE_AREA_STACKED',
  'LINE_AREA_STACKED': 'LINE',
  'SCATTER':        'BUBBLE',
  'BUBBLE':         'SCATTER',
};

const getChartSpan = (chart) => {
  if (['CALENDAR_HEATMAP', 'SANKEY', 'HEATMAP', 'RADAR'].includes(chart.chartType)) return 'col-span-2';
  if ((chart.priority || 999) <= 2) return 'col-span-2';
  if (chart.id?.startsWith('comparison_')) return 'col-span-2';
  return 'col-span-1';
};

const getChartHeight = (chart) => {
  if (chart.chartType === 'CALENDAR_HEATMAP') return '220px';
  if (chart.chartType === 'RADAR') return '380px';
  if (chart.chartType === 'SANKEY') return '400px';
  if (chart.chartType === 'BAR_HORIZONTAL') return `${Math.max(300, (chart.data?.labels?.length || 10) * 36 + 80)}px`;
  return '360px';
};

const Dashboard = memo(({ activeDataset, allDatasets = [], onQuarterChange, detectedQuarter }) => {
  const { pinnedCharts, unpinChart, setAutoDashboard} = useDashboardStore();
  const [chartTypes, setChartTypes] = useState({});
  const [quarterMap, setQuarterMap]       = useState({ Q1: null, Q2: null, Q3: null, Q4: null });
  const [activeQuarter, setActiveQuarter] = useState('All');
  const [activeCategory, setActiveCategory] = useState('All');
  const [categoryValues, setCategoryValues] = useState([]);
  const [kpis, setKpis]                   = useState([]);
  const [ceoSummary, setCeoSummary]       = useState('');
  const [loading, setLoading]             = useState(false);
  const didInit = useRef(false);

  // ── Fetch quarter-status whenever files change ──────────────────────────────
  useEffect(() => {
    fetch(`${API}/api/quarter-status`)
      .then(r => r.json())
      .then(data => setQuarterMap(data))
      .catch(() => {});
  }, [allDatasets, activeDataset]);

  // ── Main fetch ─────────────────────────────────────────────────────────────
  const fetchDashboard = useCallback(async ({ filenames, quarter, category }) => {
    if (!filenames || filenames.length === 0) {
      console.warn('fetchDashboard: no filenames provided');
      return;
    }
    setLoading(true);
    try {
      console.log('Fetching dashboard with:', { filenames, quarter, category });
      
      // Fetch traditional dashboard (KPIs, CEO summary)
      const dashRes = await fetch(`${API}/api/auto-dashboard`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filenames, quarter, category }),
      });
      
      if (!dashRes.ok) {
        console.error(`Dashboard fetch error: ${dashRes.status} ${dashRes.statusText}`);
        const errText = await dashRes.text();
        console.error('Error response:', errText);
        return;
      }
      
      const dashData = await dashRes.json();
      console.log('Dashboard data received:', dashData);
      setKpis(dashData.kpi_cards || []);
      setCategoryValues(dashData.category_values || []);
      setCeoSummary(dashData.ceo_summary || '');

      // Fetch all generated charts with AI selection
      const chartsRes = await fetch(`${API}/api/generate-all-charts`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filenames, quarter, category }),
      });
      
      if (!chartsRes.ok) {
        console.error(`Charts fetch error: ${chartsRes.status} ${chartsRes.statusText}`);
        const errText = await chartsRes.text();
        console.error('Charts error response:', errText);
        return;
      }
      
      const chartsData = await chartsRes.json();
      console.log('Charts data received:', chartsData);

      if (chartsData.charts?.length > 0) {
        setAutoDashboard(chartsData.charts);
      }
    } catch (err) {
      console.error('fetchDashboard error:', err);
    } finally {
      setLoading(false);
    }
  }, [setAutoDashboard]);

  // Auto-fetch when dataset first becomes available or changes
  useEffect(() => {
    if (!activeDataset) return;
    didInit.current = false; // Reset init flag to allow fresh fetch
  }, [activeDataset, allDatasets.length]); // Also trigger on new files uploaded

  useEffect(() => {
    // If we've already initialized for this exact state, skip
    if (!activeDataset || didInit.current) return;
    
    // Validate that we have actual filenames
    let filenames = [];
    if (allDatasets && allDatasets.length > 0) {
      filenames = allDatasets.map(d => {
        if (typeof d === 'string') return d;
        return d.name || d;
      }).filter(Boolean);
    }
    
    if (!filenames.length && activeDataset) {
      filenames = [activeDataset];
    }
    
    if (filenames.length === 0) return;
    
    didInit.current = true;
    fetchDashboard({ filenames, quarter: 'All', category: 'All' });
  }, [activeDataset, allDatasets, fetchDashboard]);

  // ── Auto-switch to detected quarter when a new file is uploaded ─────────
  useEffect(() => {
    if (!detectedQuarter || !activeDataset) return;
    const q = detectedQuarter;
    setActiveQuarter(q);
    setActiveCategory('All');
    // Build filenames: prefer the specific file for this quarter, fallback to all
    const filenames = Object.values(quarterMap).filter(Boolean);
    if (filenames.length === 0) filenames.push(activeDataset);
    // Short delay so quarter-status is refreshed first
    const timer = setTimeout(() => {
      fetchDashboard({ filenames, quarter: q, category: 'All' });
      onQuarterChange?.(q);
    }, 250);
    return () => clearTimeout(timer);
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [detectedQuarter]);

  const handleQuarterChange = useCallback((quarter) => {
    setActiveQuarter(quarter);
    setActiveCategory('All');
    const filenames = Object.values(quarterMap).filter(Boolean);
    if (filenames.length === 0 && activeDataset) filenames.push(activeDataset);
    fetchDashboard({ filenames, quarter, category: 'All' });
    onQuarterChange?.(quarter);
  }, [quarterMap, activeDataset, fetchDashboard, onQuarterChange]);

  const handleCategoryChange = useCallback((category) => {
    setActiveCategory(category);
    const filenames = Object.values(quarterMap).filter(Boolean);
    if (filenames.length === 0 && activeDataset) filenames.push(activeDataset);
    fetchDashboard({ filenames, quarter: activeQuarter, category });
  }, [quarterMap, activeDataset, activeQuarter, fetchDashboard]);

  // ── Empty state ─────────────────────────────────────────────────────────────
  if (!activeDataset) {
    return (
      <div style={{ height: '100%', display: 'flex', flexDirection: 'column',
        alignItems: 'center', justifyContent: 'center', background: GM_NAVY, color: 'white', gap: 18 }}>
        <motion.div animate={{ rotate: 360 }} transition={{ duration: 4, repeat: Infinity, ease: 'linear' }}>
          <SparklesIcon style={{ width: 64, height: 64, color: GM_GOLD }} />
        </motion.div>
        <h2 style={{ fontSize: 28, fontWeight: 700, margin: 0,
          textShadow: `0 0 14px rgba(0,212,255,0.7)`, color: '#fff' }}>
          Gold Medal India — Invoice Dashboard
        </h2>
        <p style={{ color: 'rgba(255,255,255,0.5)', margin: 0 }}>
          Upload a quarterly CSV file to auto-generate your dashboard
        </p>
      </div>
    );
  }

  // ── Main dashboard ─────────────────────────────────────────────────────────
  return (
    <div style={{ height: '100%', display: 'flex', flexDirection: 'column',
      background: GM_NAVY, overflow: 'hidden' }}>

      {/* ── Title Header ── */}
      <div style={{ padding: '16px 24px 10px', borderBottom: `1px solid rgba(212,160,23,0.25)`,
        textAlign: 'center', flexShrink: 0, position: 'relative' }}>
        <h1 style={{ fontSize: 24, fontWeight: 800, color: '#fff', margin: 0,
          display: 'inline-flex', alignItems: 'center', gap: 10,
          textShadow: `0 0 18px rgba(0,212,255,0.6)`, letterSpacing: 0.5 }}>
          {/* Gold Medal logo style */}
          <span style={{ fontSize: 28 }}>🥇</span>
          Gold Medal India · Sales Dashboard
        </h1>

        {/* CEO Summary */}
        {ceoSummary && (
          <div className="flex gap-2">
            <div className="w-1.5 rounded-full bg-[#00D4FF]" />
            <p className="text-[#a3a3a3] text-[15px] leading-relaxed tracking-wide italic font-medium pr-8">
              {ceoSummary}
            </p>
          </div>
        )}

        <p style={{ color: 'rgba(255,255,255,0.35)', fontSize: 11, margin: '2px 0 0' }}>
          Auto-generated insights · {activeDataset}
        </p>
      </div>

      {/* ── Scrollable body ── */}
      <div style={{ flex: 1, overflowY: 'auto', padding: '16px 22px 24px' }}>

        {/* ── Quarter badges strip ── */}
        <div style={{ display: 'flex', gap: 8, marginBottom: 14, alignItems: 'center', flexWrap: 'wrap' }}>
          <span style={{ fontSize: 10, fontWeight: 700, color: 'rgba(255,255,255,0.4)',
            letterSpacing: 1.5, textTransform: 'uppercase' }}>Periods:</span>
          {Object.entries(quarterMap).map(([q, file]) => (
            <span key={q} style={{
              padding: '3px 10px',
              borderRadius: 999,
              fontSize: 11,
              fontWeight: 700,
              background: file ? 'rgba(0,180,80,0.15)' : 'rgba(255,255,255,0.04)',
              color: file ? '#00FF88' : 'rgba(255,255,255,0.25)',
              border: `1px solid ${file ? 'rgba(0,255,136,0.3)' : 'rgba(255,255,255,0.08)'}`,
              title: file || 'Not uploaded',
            }}>
              {q} {file ? '✓' : '✗'}
            </span>
          ))}
        </div>

        {/* ── KPI Row + Filters ── */}
        <motion.div initial={{ opacity: 0, y: -10 }} animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4 }} style={{ marginBottom: 20 }}>

          {/* Filter bar */}
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            marginBottom: 12 }}>
            <h2 style={{ color: 'rgba(255,255,255,0.55)', fontSize: 10, fontWeight: 700,
              letterSpacing: 1.5, margin: 0, textTransform: 'uppercase' }}>Key Metrics</h2>

            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              {/* Quarter selector — dynamic from API */}
              <div style={{ display: 'flex', borderRadius: 8, overflow: 'hidden',
                border: `1px solid rgba(212,160,23,0.3)`, background: GM_CARD, flexWrap: 'wrap' }}>
                {/* "All" tab always shown */}
                {['All', ...Object.keys(quarterMap).sort()].map(q => {
                  const active = activeQuarter === q;
                  const available = q === 'All' || !!quarterMap[q];
                  return (
                    <button key={q}
                      disabled={!available}
                      title={!available ? `Upload a file with ${q} in its name` : ''}
                      onClick={() => handleQuarterChange(q)}
                      style={{
                        padding: '5px 12px', fontSize: 11, fontWeight: 700,
                        border: 'none', cursor: available ? 'pointer' : 'not-allowed',
                        background: active ? `rgba(212,160,23,0.25)` : 'transparent',
                        color: active ? GM_GOLD : available ? 'rgba(255,255,255,0.5)' : 'rgba(255,255,255,0.18)',
                        transition: 'all 0.15s',
                        opacity: available ? 1 : 0.4,
                      }}>
                      {q}
                    </button>
                  );
                })}
              </div>

              {/* ── Tabs (Categories) ── */}
              {categoryValues.length > 0 && (
                <div className="flex flex-wrap gap-3 mt-4 mb-4 pb-2">
                  <button
                    onClick={() => handleCategoryChange('All')}
                    className={`px-5 py-2.5 rounded-full text-sm font-bold tracking-wide transition-all duration-300 shadow-md ${
                      activeCategory === 'All'
                        ? 'bg-[#00D4FF] text-[#0A0F2C] shadow-[0_0_15px_rgba(0,212,255,0.3)]'
                        : 'bg-[rgba(255,255,255,0.04)] text-slate-400 border border-[rgba(0,212,255,0.15)] hover:border-[rgba(0,212,255,0.4)] hover:text-[#00D4FF]'
                    }`}
                  >
                    ALL
                  </button>
                  
                  {categoryValues.map(cat => (
                    <button
                      key={cat}
                      onClick={() => handleCategoryChange(cat)}
                      className={`px-5 py-2.5 rounded-full text-sm font-bold tracking-wide transition-all duration-200 shadow-md ${
                        activeCategory === cat
                          ? 'bg-[#00D4FF] text-[#0A0F2C] shadow-[0_0_15px_rgba(0,212,255,0.3)]'
                          : 'bg-[rgba(255,255,255,0.04)] text-slate-400 border border-[rgba(255,255,255,0.05)] hover:border-[rgba(0,212,255,0.4)] hover:text-[#00D4FF]'
                      }`}
                    >
                      {cat}
                    </button>
                  ))}
                </div>
              )}

              {/* Clear filters */}
              {(activeQuarter !== 'All' || activeCategory !== 'All') && (
                <button onClick={() => { handleQuarterChange('All'); }}
                  style={{ padding: '5px 10px', fontSize: 11, fontWeight: 600,
                    borderRadius: 8, border: `1px solid rgba(255,51,102,0.4)`,
                    background: 'rgba(255,51,102,0.1)', color: '#FF3366', cursor: 'pointer' }}>
                  ✕ Clear Filters
                </button>
              )}
            </div>
          </div>

          {/* 4 KPI Cards */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4,1fr)', gap: 14 }}>
            <AnimatePresence mode="popLayout">
              {kpis
                .filter(k => !/hsn/i.test(k.title))
                .slice(0, 4)
                .map((kpi, idx) => (
                <KPICard
                  key={`${kpi.title}-${idx}`}
                  title={kpi.title}
                  value={kpi.value}
                  unit={kpi.unit || ''}
                  trend={kpi.trend || 0}
                  isCurrency={kpi.is_currency}
                  icon={SparklesIcon}
                  accentColor={CHART_COLORS[idx % CHART_COLORS.length]}
                />
              ))}
            </AnimatePresence>
          </div>
        </motion.div>

        {/* ── Loading spinner ── */}
        {loading && (
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 16,
            color: GM_CYAN, fontSize: 13 }}>
            <motion.div animate={{ rotate: 360 }} transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}>
              <SparklesIcon style={{ width: 18, height: 18 }} />
            </motion.div>
            Refreshing dashboard data…
          </div>
        )}

        {/* ── Auto-generated charts grid ── */}
        {pinnedCharts.length > 0 && (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 16 }}>
            <AnimatePresence mode="popLayout">
              {pinnedCharts.map((chart, idx) => {
                const currentType = chartTypes[chart.id] || chart.chartType;
                const handleCycleChart = () => {
                  const nextType = CHART_TYPE_CYCLE[currentType];
                  if (nextType) {
                    setChartTypes(prev => ({ ...prev, [chart.id]: nextType }));
                  }
                };

                return (
                  <motion.div key={chart.id}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.9 }}
                    transition={{ delay: idx * 0.05, duration: 0.3 }}
                    style={{
                      background: GM_CARD,
                      borderRadius: 12,
                      border: `1px solid rgba(0,212,255,0.1)`,
                      padding: 14,
                      display: 'flex',
                      flexDirection: 'column',
                      gap: 10,
                      gridColumn: getChartSpan(chart) === 'col-span-2' ? 'span 2' : 'auto',
                    }}>
                    {/* Chart header with title and buttons */}
                    <div style={{
                      display: 'flex',
                      justifyContent: 'space-between',
                      alignItems: 'flex-start',
                      gap: 12,
                    }}>
                      <div style={{ flex: 1 }}>
                        <h3 style={{
                          color: GM_CYAN,
                          fontSize: 13,
                          fontWeight: 700,
                          margin: 0,
                          marginBottom: 4,
                          letterSpacing: 0.5,
                        }}>
                          {chart.title}
                        </h3>
                        {chart.business_insight && (
                          <p style={{
                            color: 'rgba(255,255,255,0.45)',
                            fontSize: 11,
                            margin: 0,
                            fontStyle: 'italic',
                            lineHeight: 1.4,
                          }}>
                            {chart.business_insight}
                          </p>
                        )}
                      </div>

                      {/* Cycling & delete buttons */}
                      <div style={{ display: 'flex', gap: 6, flexShrink: 0 }}>
                        {CHART_TYPE_CYCLE[currentType] && (
                          <button
                            onClick={handleCycleChart}
                            title="Cycle chart type"
                            style={{
                              background: 'rgba(0,212,255,0.1)',
                              border: '1px solid rgba(0,212,255,0.3)',
                              color: GM_CYAN,
                              cursor: 'pointer',
                              padding: '4px 8px',
                              borderRadius: 4,
                              fontSize: 10,
                              fontWeight: 600,
                              transition: 'all 0.15s',
                            }}
                            onMouseOver={(e) => {
                              e.target.style.background = 'rgba(0,212,255,0.2)';
                              e.target.style.boxShadow = '0 0 8px rgba(0,212,255,0.3)';
                            }}
                            onMouseOut={(e) => {
                              e.target.style.background = 'rgba(0,212,255,0.1)';
                              e.target.style.boxShadow = 'none';
                            }}
                          >
                            ↻ Cycle
                          </button>
                        )}
                        <button
                          onClick={() => unpinChart(chart.id)}
                          title="Remove chart"
                          style={{
                            background: 'rgba(255,51,102,0.1)',
                            border: '1px solid rgba(255,51,102,0.3)',
                            color: '#FF3366',
                            cursor: 'pointer',
                            padding: '4px 8px',
                            borderRadius: 4,
                            fontSize: 10,
                            fontWeight: 600,
                            transition: 'all 0.15s',
                          }}
                          onMouseOver={(e) => {
                            e.target.style.background = 'rgba(255,51,102,0.2)';
                            e.target.style.boxShadow = '0 0 8px rgba(255,51,102,0.3)';
                          }}
                          onMouseOut={(e) => {
                            e.target.style.background = 'rgba(255,51,102,0.1)';
                            e.target.style.boxShadow = 'none';
                          }}
                        >
                          ✕ Remove
                        </button>
                      </div>
                    </div>

                    {/* Chart renderer */}
                    <div style={{
                      flex: 1,
                      minHeight: idx === 2 ? '500px' : getChartHeight(chart),
                      height: idx === 2 ? '500px' : 'auto',
                      overflowY: idx === 2 ? 'auto' : 'visible',
                      overflowX: 'hidden',
                      marginTop: 4,
                      borderRadius: 8,
                      padding: idx === 2 ? '8px 4px' : '0',
                      backgroundColor: idx === 2 ? 'rgba(0,0,0,0.2)' : 'transparent',
                    }}>
                      <ChartRenderer
                        chartType={currentType}
                        config={chart}
                        data={chart.data}
                        height={idx === 2 ? '100%' : getChartHeight(chart)}
                      />
                    </div>
                  </motion.div>
                );
              })}
            </AnimatePresence>
          </div>
        )}

        {pinnedCharts.length === 0 && !loading && activeDataset && (
          <div style={{ textAlign: 'center', color: 'rgba(255,255,255,0.3)',
            padding: '60px 0', fontSize: 14 }}>
            No charts generated yet. Dashboard will auto-populate after upload.
          </div>
        )}
      </div>
    </div>
  );
});

Dashboard.displayName = 'Dashboard';
export default Dashboard;
