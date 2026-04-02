import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export const useDashboardStore = create(
  persist(
    (set, get) => ({
      // Global filters
      filters: {},
      activeFilters: [],
      
      // Dashboard layouts & widgets
      dashboards: {},
      activeDashboard: null,
      
      // Charts
      pinnedCharts: [],
      
      // Drill-down
      drillDownPath: [],
      drillDownLevels: {},
      
      // Layout
      layout: [],
      
      // Filter operations
      setFilter: (column, value) =>
        set((state) => ({
          filters: {
            ...state.filters,
            [column]: value,
          },
          activeFilters: [
            ...state.activeFilters.filter(f => f.column !== column),
            { column, value, id: `${column}_${Date.now()}` }
          ],
        })),
      
      removeFilter: (column) =>
        set((state) => ({
          filters: Object.fromEntries(
            Object.entries(state.filters).filter(([k]) => k !== column)
          ),
          activeFilters: state.activeFilters.filter(f => f.column !== column),
        })),
      
      clearFilters: () =>
        set({
          filters: {},
          activeFilters: [],
        }),
      
      // Chart operations
      pinChart: (chart) =>
        set((state) => ({
          pinnedCharts: [...state.pinnedCharts, {
            ...chart,
            id: chart.id || `chart_${Date.now()}`,
            createdAt: Date.now(),
          }],
        })),
      
      // Replace all pinned charts from auto-dashboard (does not duplicate)
      setAutoDashboard: (charts) =>
        set({
          pinnedCharts: charts.map((c, i) => ({
            ...c,
            id: c.id || `auto_${i}_${Date.now()}`,
            createdAt: Date.now(),
          })),
        }),

      unpinChart: (chartId) =>
        set((state) => ({
          pinnedCharts: state.pinnedCharts.filter((c) => c.id !== chartId),
        })),
      
      updateChart: (chartId, updates) =>
        set((state) => ({
          pinnedCharts: state.pinnedCharts.map(c =>
            c.id === chartId ? { ...c, ...updates } : c
          ),
        })),
      
      clearDashboard: () =>
        set({ pinnedCharts: [] }),
      
      // Drill-down operations
      drillDown: (level) =>
        set((state) => ({
          drillDownPath: [...state.drillDownPath, level],
        })),
      
      drillUp: () =>
        set((state) => ({
          drillDownPath: state.drillDownPath.slice(0, -1),
        })),
      
      resetDrillDown: () =>
        set({ drillDownPath: [] }),
      
      setDrillDownLevel: (chartId, level) =>
        set((state) => ({
          drillDownLevels: {
            ...state.drillDownLevels,
            [chartId]: level,
          },
        })),
      
      // Dashboard management
      saveDashboard: (name, layout) =>
        set((state) => {
          const id = `dash_${Date.now()}`;
          return {
            dashboards: {
              ...state.dashboards,
              [id]: {
                id,
                name,
                layout,
                charts: [...state.pinnedCharts],
                filters: { ...state.filters },
                createdAt: Date.now(),
                updatedAt: Date.now(),
              }
            }
          };
        }),
      
      loadDashboard: (dashboardId) =>
        set((state) => {
          const dashboard = state.dashboards[dashboardId];
          if (!dashboard) return state;
          return {
            activeDashboard: dashboardId,
            pinnedCharts: [...dashboard.charts],
            filters: { ...dashboard.filters },
            layout: [...dashboard.layout],
          };
        }),
      
      deleteDashboard: (dashboardId) =>
        set((state) => {
          const { [dashboardId]: removed, ...rest } = state.dashboards;
          return {
            dashboards: rest,
            activeDashboard: state.activeDashboard === dashboardId ? null : state.activeDashboard,
          };
        }),
      
      // Layout
      setLayout: (layout) =>
        set({ layout }),
    }),
    {
      name: 'dashboard-store',
      version: 1,
    }
  )
);

