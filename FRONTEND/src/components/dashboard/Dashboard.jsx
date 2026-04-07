import React, { memo, useCallback, useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useDashboardStore } from '../../store/dashboardStore';
import ChartRenderer from './ChartRenderer';
import KPICard from './KPICard';
import DataTable from './DataTable';
import { SparklesIcon } from '@heroicons/react/24/outline';

const API = 'http://localhost:8000/api';
const CHART_COLORS = ['#00D4FF','#FF6B35','#7B2FBE','#00FF88','#FFD700','#FF3366','#4ECDC4','#45B7D1','#96CEB4'];

const Dashboard = memo(({ activeDataset, allDatasets = [] }) => {
  const { pinnedCharts, setAutoDashboard } = useDashboardStore();
  const [kpis, setKpis] = useState([]);
  const [loading, setLoading] = useState(false);
  const didInit = useRef(false);

  const fetchDashboard = useCallback(async (filename) => {
    if (!filename) return;
    setLoading(true);
    try {
      const res = await fetch(`${API}/auto-dashboard`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename }),
      });
      if (!res.ok) return;
      const data = await res.json();
      setKpis(data.kpi_cards || []);
      if (data.charts?.length > 0) setAutoDashboard(data.charts);
      else setAutoDashboard([]);
    } catch (err) {
      console.error('fetchDashboard error:', err);
    } finally {
      setLoading(false);
    }
  }, [setAutoDashboard]);

  useEffect(() => {
    if (!activeDataset) return;
    didInit.current = false;
  }, [activeDataset, allDatasets.length]);

  useEffect(() => {
    if (!activeDataset || didInit.current) return;
    didInit.current = true;
    fetchDashboard(activeDataset);
  }, [activeDataset, allDatasets, fetchDashboard]);

  // Limit to max 3 charts for clean layout
  const displayCharts = pinnedCharts.slice(0, 3);

  return (
    <div className="h-full flex flex-col bg-[#0B0F1A]">
      {/* Scrollable body */}
      <div className="flex-1 overflow-y-auto px-6 py-5 space-y-6">

        {/* Loading */}
        {loading && (
          <div className="flex items-center gap-2.5 text-white/40 text-sm">
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
              className="w-4 h-4 border-2 border-white/10 border-t-indigo-400 rounded-full"
            />
            Generating insights...
          </div>
        )}

        {/* KPI Row - max 4 cards */}
        {kpis.length > 0 && (
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.3 }}
          >
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-3">
              {kpis.slice(0, 4).map((kpi, idx) => (
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
            </div>
          </motion.div>
        )}

        {/* Charts - max 3 */}
        {displayCharts.length > 0 && (
          <div className="space-y-4">
            <h2 className="text-[11px] font-semibold text-white/30 uppercase tracking-widest">
              Visualizations
            </h2>
            <div className={`grid gap-4 ${
              displayCharts.length === 1 ? 'grid-cols-1' :
              displayCharts.length === 2 ? 'grid-cols-2' :
              'grid-cols-2'
            }`}>
              <AnimatePresence mode="popLayout">
                {displayCharts.map((chart, idx) => (
                  <motion.div
                    key={chart.id}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    exit={{ opacity: 0, scale: 0.95 }}
                    transition={{ delay: idx * 0.05, duration: 0.25 }}
                    className={`bg-white/[0.02] border border-white/[0.06] rounded-xl p-4 flex flex-col gap-2 ${
                      idx === 0 && displayCharts.length === 3 ? 'col-span-2' : ''
                    }`}
                  >
                    <h3 className="text-[12px] font-semibold text-white/60 truncate">
                      {chart.title}
                    </h3>
                    {chart.business_insight && (
                      <p className="text-[11px] text-white/30 leading-relaxed line-clamp-2">
                        {chart.business_insight}
                      </p>
                    )}
                    <div className="flex-1 min-h-[280px]">
                      <ChartRenderer
                        chartType={chart.chartType}
                        config={chart}
                        data={chart.data}
                        height="280px"
                      />
                    </div>
                  </motion.div>
                ))}
              </AnimatePresence>
            </div>
          </div>
        )}

        {/* No charts yet */}
        {displayCharts.length === 0 && !loading && (
          <div className="text-center py-12 text-white/20 text-sm">
            Charts will appear after data is processed.
          </div>
        )}

        {/* Data Table */}
        <DataTable activeDataset={activeDataset} />
      </div>
    </div>
  );
});

Dashboard.displayName = 'Dashboard';
export default Dashboard;
