import { useState, useCallback, useEffect } from 'react';
import { useDashboardStore } from '../store/dashboardStore';

const API = 'http://localhost:8888';

/**
 * Hook to fetch KPIs + auto-charts from /api/auto-dashboard.
 * Populates pinnedCharts in dashboardStore as a side effect.
 */
export function useKPIs(filename, filters = null) {
  const [kpis, setKpis] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Only set charts via store setter so we don't cause infinite render
  const { setAutoDashboard } = useDashboardStore();

  const fetchKPIs = useCallback(async () => {
    if (!filename) {
      setKpis([]);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const response = await fetch(`${API}/api/auto-dashboard`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ filename, filters: filters || {} }),
      });

      if (!response.ok) {
        throw new Error(`Failed to fetch dashboard: ${response.status}`);
      }

      const data = await response.json();
      setKpis(data.kpi_cards || []);

      // Push charts into the dashboard store if we have them
      if (data.charts && data.charts.length > 0 && typeof setAutoDashboard === 'function') {
        setAutoDashboard(data.charts);
      }
    } catch (err) {
      console.error('Error fetching KPIs:', err);
      setError(err.message);
      setKpis([]);
    } finally {
      setLoading(false);
    }
  }, [filename, filters, setAutoDashboard]);

  useEffect(() => {
    fetchKPIs();
  }, [fetchKPIs]);

  return {
    kpis,
    loading,
    error,
    refetch: fetchKPIs,
  };
}
