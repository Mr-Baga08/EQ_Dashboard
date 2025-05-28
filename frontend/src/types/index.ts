// frontend/src/types/index.ts
export interface Client {
  id: number;
  name: string;
  motilal_client_id: string;
  available_funds: number;
  total_pnl: number;
  margin_used: number;
  margin_available: number;
  is_active: boolean;
  created_at: string;
  updated_at?: string;
}

export interface Token {
  id: number;
  symbol: string;
  token_id: number;
  exchange: string;
  instrument_type?: string;
  ltp: number;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  lot_size: number;
  tick_size: number;
  is_active: boolean;
  is_tradeable: boolean;
}

export interface Trade {
  id: number;
  trade_id: string;
  client_id: number;
  token_id: number;
  trade_type: 'MTF' | 'INTRADAY' | 'DELIVERY';
  execution_type: 'BUY' | 'SELL';
  status: 'ACTIVE' | 'CLOSED' | 'PENDING';
  quantity: number;
  avg_price: number;
  current_price: number;
  realized_pnl: number;
  unrealized_pnl: number;
  total_pnl: number;
  margin_required: number;
  margin_blocked: number;
  entry_time: string;
  exit_time?: string;
  client?: Client;
  token?: Token;
}

export interface OrderCreate {
  client_id: number;
  token_id: number;
  execution_type: 'BUY' | 'SELL' | 'EXIT';
  order_type: 'MARKET' | 'LIMIT';
  trade_type: 'MTF' | 'INTRADAY' | 'DELIVERY';
  quantity: number;
  price?: number;
  tag?: string;
}

export interface BatchOrder {
  token_id: number;
  execution_type: 'BUY' | 'SELL' | 'EXIT';
  order_type: 'MARKET' | 'LIMIT';
  trade_type: 'MTF' | 'INTRADAY' | 'DELIVERY';
  price?: number;
  client_orders: Array<{
    client_id: number;
    quantity: number;
  }>;
}
