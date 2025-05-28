// frontend/src/services/api.ts
import axios from 'axios';
import { Client, Token, Trade, OrderCreate, BatchOrder } from '../types';

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000/api/v1';

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor for error handling
api.interceptors.request.use(
  (config) => {
    // Add any auth tokens here if needed
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for error handling
api.interceptors.response.use(
  (response) => response,
  (error) => {
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Clients API
export const clientsApi = {
  getAll: () => api.get<Client[]>('/clients'),
  getById: (id: number) => api.get<Client>(`/clients/${id}`),
  getPortfolio: (id: number) => api.get(`/clients/${id}/portfolio`),
  create: (data: Partial<Client>) => api.post<Client>('/clients', data),
};

// Tokens API
export const tokensApi = {
  search: (query: string, limit = 10) => 
    api.get<Token[]>(`/tokens/search?q=${query}&limit=${limit}`),
  getById: (id: number) => api.get<Token>(`/tokens/${id}`),
  getHolders: (id: number) => api.get(`/tokens/${id}/holders`),
};

// Trades API
export const tradesApi = {
  getAll: (params?: {
    client_id?: number;
    token_id?: number;
    status?: string;
    skip?: number;
    limit?: number;
  }) => api.get<Trade[]>('/trades', { params }),
  getById: (id: string) => api.get<Trade>(`/trades/${id}`),
  exit: (id: string) => api.post(`/trades/${id}/exit`),
  exitByToken: (tokenId: number, clientIds?: number[]) =>
    api.post(`/trades/exit-by-token/${tokenId}`, { client_ids: clientIds }),
};

// Orders API
export const ordersApi = {
  place: (data: OrderCreate) => api.post('/orders/place', data),
  executeAll: (data: BatchOrder) => api.post('/orders/execute-all', data),
};

// Admin API - New section for admin functions
export const adminApi = {
  // Refresh all clients' portfolio data from Motilal
  refreshPortfolio: () => api.post('/admin/refresh-portfolio'),
  
  // Refresh specific client's portfolio data
  refreshClientPortfolio: (clientId: number) => 
    api.post(`/admin/refresh-client/${clientId}`),
  
  // Get aggregated portfolio statistics
  getPortfolioStats: () => api.get('/admin/portfolio-stats'),
  
  // Force sync all client data
  syncAllClients: () => api.post('/admin/sync-all-clients'),
  
  // Test Motilal API connectivity for a client
  testClientConnection: (clientId: number) => 
    api.post(`/admin/test-connection/${clientId}`),
  
  // Get system health status
  getSystemHealth: () => api.get('/admin/health'),
  
  // Get real-time connection status for all clients
  getConnectionStatus: () => api.get('/admin/connection-status'),
};

// Utility functions for API calls
export const apiUtils = {
  // Retry failed requests
  retryRequest: async <T>(
    requestFn: () => Promise<T>, 
    maxRetries = 3, 
    delay = 1000
  ): Promise<T> => {
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await requestFn();
      } catch (error) {
        if (i === maxRetries - 1) throw error;
        await new Promise(resolve => setTimeout(resolve, delay * Math.pow(2, i)));
      }
    }
    throw new Error('Max retries exceeded');
  },

  // Batch API calls with concurrency control
  batchRequests: async <T>(
    requests: (() => Promise<T>)[], 
    concurrency = 5
  ): Promise<T[]> => {
    const results: T[] = [];
    
    for (let i = 0; i < requests.length; i += concurrency) {
      const batch = requests.slice(i, i + concurrency);
      const batchResults = await Promise.allSettled(batch.map(req => req()));
      
      batchResults.forEach((result, index) => {
        if (result.status === 'fulfilled') {
          results[i + index] = result.value;
        } else {
          console.error(`Request ${i + index} failed:`, result.reason);
          // You might want to handle failures differently
        }
      });
    }
    
    return results;
  },

  // Handle API errors consistently
  handleApiError: (error: any) => {
    if (error.response) {
      // Server responded with error status
      const message = error.response.data?.detail || 
                     error.response.data?.message || 
                     `HTTP ${error.response.status}`;
      return {
        type: 'api_error',
        message,
        status: error.response.status,
        data: error.response.data
      };
    } else if (error.request) {
      // Network error
      return {
        type: 'network_error',
        message: 'Network connection failed',
        data: null
      };
    } else {
      // Other error
      return {
        type: 'unknown_error',
        message: error.message || 'An unknown error occurred',
        data: null
      };
    }
  }
};

// Real-time data API
export const realtimeApi = {
  // Get current market status
  getMarketStatus: () => api.get('/realtime/market-status'),
  
  // Get live prices for tokens
  getLivePrices: (tokenIds: number[]) => 
    api.post('/realtime/live-prices', { token_ids: tokenIds }),
  
  // Subscribe to price updates for specific tokens
  subscribeToPrices: (tokenIds: number[]) => 
    api.post('/realtime/subscribe-prices', { token_ids: tokenIds }),
  
  // Unsubscribe from price updates
  unsubscribeFromPrices: (tokenIds: number[]) => 
    api.post('/realtime/unsubscribe-prices', { token_ids: tokenIds }),
  
  // Get real-time portfolio summary
  getPortfolioSummary: () => api.get('/realtime/portfolio-summary'),
};

// Export all APIs
export {
  api as default,
  API_BASE_URL
};