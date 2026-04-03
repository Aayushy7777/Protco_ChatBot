import { useCallback, useRef } from 'react';
import { useDashboardStore } from '../store/dashboardStore';

const API = "http://localhost:8000/api";

export const useDashboardPersistence = () => {
  const {
    pinnedCharts,
    filters,
    saveDashboard,
    loadDashboard,
    deleteDashboard,
    dashboards,
  } = useDashboardStore();

  const saveToDashboard = useCallback(async (name) => {
    try {
      const layoutData = pinnedCharts.map((chart, index) => ({
        i: String(chart.id),
        x: (index % 2) * 6,
        y: Math.floor(index / 2) * 4,
        w: 6,
        h: 4,
        static: false,
      }));

      saveDashboard(name, layoutData);
      return { success: true, id: Object.keys(dashboards)[0] };
    } catch (err) {
      console.error('Failed to save dashboard:', err);
      return { success: false, error: err.message };
    }
  }, [pinnedCharts, saveDashboard, dashboards]);

  const exportDashboard = useCallback(async (dashboardId) => {
    const dashboard = dashboards[dashboardId];
    if (!dashboard) return null;

    const json = JSON.stringify(dashboard, null, 2);
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `dashboard-${dashboard.name}-${Date.now()}.json`;
    a.click();
    URL.revokeObjectURL(url);
  }, [dashboards]);

  const importDashboard = useCallback(async (file) => {
    try {
      const text = await file.text();
      const dashboard = JSON.parse(text);
      saveDashboard(dashboard.name, dashboard.layout);
      return { success: true };
    } catch (err) {
      console.error('Failed to import dashboard:', err);
      return { success: false, error: err.message };
    }
  }, [saveDashboard]);

  return {
    dashboards,
    saveToDashboard,
    loadDashboard,
    deleteDashboard,
    exportDashboard,
    importDashboard,
  };
};
