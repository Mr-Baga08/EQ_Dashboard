// frontend/src/store/index.ts
import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { Client, Token, Trade } from '../types';

interface AppState {
  // Clients
  clients: Client[];
  selectedClient: Client | null;
  
  // Tokens
  tokens: Token[];
  selectedToken: Token | null;
  tokenSearchQuery: string;
  
  // Trades
  trades: Trade[];
  
  // UI State
  isLoading: boolean;
  error: string | null;
  
  // Actions
  setClients: (clients: Client[]) => void;
  setSelectedClient: (client: Client | null) => void;
  setTokens: (tokens: Token[]) => void;
  setSelectedToken: (token: Token | null) => void;
  setTokenSearchQuery: (query: string) => void;
  setTrades: (trades: Trade[]) => void;
  setLoading: (loading: boolean) => void;
  setError: (error: string | null) => void;
  clearError: () => void;
}

export const useAppStore = create<AppState>()(
  devtools(
    (set) => ({
      // Initial state
      clients: [],
      selectedClient: null,
      tokens: [],
      selectedToken: null,
      tokenSearchQuery: '',
      trades: [],
      isLoading: false,
      error: null,
      
      // Actions
      setClients: (clients) => set({ clients }),
      setSelectedClient: (selectedClient) => set({ selectedClient }),
      setTokens: (tokens) => set({ tokens }),
      setSelectedToken: (selectedToken) => set({ selectedToken }),
      setTokenSearchQuery: (tokenSearchQuery) => set({ tokenSearchQuery }),
      setTrades: (trades) => set({ trades }),
      setLoading: (isLoading) => set({ isLoading }),
      setError: (error) => set({ error }),
      clearError: () => set({ error: null }),
    }),
    { name: 'trading-platform-store' }
  )
);