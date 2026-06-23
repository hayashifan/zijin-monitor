import axios from 'axios';

// 使用Vite代理，不需要配置baseURL
const api = axios.create({
  timeout: 10000,
});

// Stock API
export const stockAPI = {
  getRealtime: (code: string = '601899', market: string = 'A') =>
    api.get('/api/stock/realtime', { params: { code, market } }),
  
  getHistory: (code: string = '601899', market: string = 'A', days: number = 30) =>
    api.get('/api/stock/history', { params: { code, market, days } }),
  
  getOverview: () =>
    api.get('/api/stock/overview'),
};

// Commodity API
export const commodityAPI = {
  getGold: () => api.get('/api/commodity/gold'),
  getCopperLME: () => api.get('/api/commodity/copper/lme'),
  getCopperSHFE: () => api.get('/api/commodity/copper/shfe'),
  getOverview: () => api.get('/api/commodity/overview'),
};

// Announcement API
export const announcementAPI = {
  getList: (code: string = '601899', source: string = 'cninfo', page: number = 1, size: number = 20) =>
    api.get('/api/announcement/list', { params: { code, source, page, size } }),
};

// Fundamental API
export const fundamentalAPI = {
  getSummary: (code: string = '601899') =>
    api.get('/api/fundamental/summary', { params: { code } }),
  
  getMetrics: (code: string = '601899') =>
    api.get('/api/fundamental/metrics', { params: { code } }),
  
  getProfitTrend: (code: string = '601899', periods: number = 8) =>
    api.get('/api/fundamental/profit-trend', { params: { code, periods } }),
};

// Quant Analysis API
export const quantAPI = {
  getLatest: () => api.get('/api/quant/latest'),
  getList: (limit: number = 10) => api.get('/api/quant/list', { params: { limit } }),
};

export default api;
