// API endpoints
export const API_BASE = "http://localhost:8888";

export const ENDPOINTS = {
  UPLOAD: `${API_BASE}/api/upload`,
  CHAT: `${API_BASE}/api/chat`,
  CHAT_STREAM: `${API_BASE}/api/chat/stream`,
  FILES: `${API_BASE}/api/files`,
  FILE_SCHEMA: (name) => `${API_BASE}/api/files/${encodeURIComponent(name)}/schema`,
  FILE_FILTER: (name) => `${API_BASE}/api/files/${encodeURIComponent(name)}/filter`,
  FILE_AGGREGATE: (name) => `${API_BASE}/api/files/${encodeURIComponent(name)}/aggregate`,
  FILE_TIMESERIES: (name) => `${API_BASE}/api/files/${encodeURIComponent(name)}/timeseries`,
  FILE_DELETE: (name) => `${API_BASE}/api/files/${encodeURIComponent(name)}`,
  HEALTH: `${API_BASE}/api/health`,
  DASHBOARD_PRESETS: `${API_BASE}/api/dashboard/presets`,
};

// Chart types
export const CHART_TYPES = {
  BAR: 'bar',
  LINE: 'line',
  PIE: 'pie',
  SCATTER: 'scatter',
  AREA: 'area',
  HISTOGRAM: 'histogram',
};

// Intent types
export const INTENTS = {
  CHAT: 'CHAT',
  CHART: 'CHART',
  TABLE: 'TABLE',
  STATS: 'STATS',
};

// Message roles
export const MESSAGE_ROLES = {
  USER: 'user',
  ASSISTANT: 'assistant',
  SYSTEM: 'system',
};

// Stream statuses
export const STREAM_STATUS = {
  CLASSIFYING: 'classifying',
  LOADING: 'loading',
  GENERATING: 'generating',
  TOKEN: 'token',
  CHART: 'chart',
  TABLE: 'table',
  DONE: 'done',
  ERROR: 'error',
};

// Local storage keys
export const STORAGE_KEYS = {
  CHAT_STORE: 'chat-store',
  DASHBOARD_STORE: 'dashboard-store',
  USER_PREFERENCES: 'user-preferences',
};

// Animation durations (ms)
export const ANIMATIONS = {
  FADE: 300,
  SLIDE: 300,
  BOUNCE: 200,
  SLOW: 500,
};

// Error messages
export const ERROR_MESSAGES = {
  NO_DATASET: 'Please upload a CSV file first',
  NO_CONVERSATION: 'No active conversation',
  NETWORK_ERROR: 'Network error. Please check your connection',
  INVALID_FILE: 'Invalid file format. Please upload CSV, XLSX, or XLS',
  FILE_TOO_LARGE: 'File is too large (max 50MB)',
};

// Success messages
export const SUCCESS_MESSAGES = {
  FILE_UPLOADED: 'File uploaded successfully',
  DASHBOARD_SAVED: 'Dashboard saved successfully',
  DASHBOARD_DELETED: 'Dashboard deleted successfully',
  MESSAGE_COPIED: 'Message copied to clipboard',
};

// Request timeouts (ms)
export const TIMEOUTS = {
  DEFAULT: 30000,
  UPLOAD: 60000,
  STREAM: 120000,
};

// Breakpoints
export const BREAKPOINTS = {
  SM: 640,
  MD: 768,
  LG: 1024,
  XL: 1280,
  '2XL': 1536,
};

// Default chart dimensions
export const CHART_DEFAULTS = {
  HEIGHT: 400,
  MIN_HEIGHT: 300,
  MAX_HEIGHT: 600,
  WIDTH: '100%',
};

// Suggested prompts
export const SUGGESTED_PROMPTS = [
  {
    icon: '📊',
    text: 'Show data distribution',
    description: 'Visualize how data is distributed across categories',
  },
  {
    icon: '📈',
    text: 'Top categories by count',
    description: 'Find the most common or significant categories',
  },
  {
    icon: '🔍',
    text: 'Find trends over time',
    description: 'Analyze how values change over time',
  },
  {
    icon: '💡',
    text: 'Generate insights',
    description: 'Get AI-powered insights from your data',
  },
];
