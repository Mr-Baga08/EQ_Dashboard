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
