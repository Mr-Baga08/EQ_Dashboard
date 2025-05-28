// frontend/src/services/websocket.ts
import { useEffect, useRef, useCallback, useState } from 'react';

const WEBSOCKET_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

interface PortfolioUpdate {
  type: 'portfolio_update';
  client_id: string;
  data: {
    available_funds: number;
    margin_used: number;
    margin_available: number;
    total_pnl: number;
    positions: any[];
  };
  timestamp: string;
}

interface PriceUpdate {
  type: 'price_update';
  token_id: number;
  symbol: string;
  ltp: number;
  change: number;
  change_percent: number;
  timestamp: string;
}

interface TradeUpdate {
  type: 'trade_update';
  trade_id: string;
  client_id: number;
  status: string;
  data: any;
  timestamp: string;
}

type WebSocketMessage = PortfolioUpdate | PriceUpdate | TradeUpdate;

export const useWebSocket = (
  clientId: string, 
  onMessage?: (data: WebSocketMessage) => void,
  onConnect?: () => void,
  onDisconnect?: () => void,
  onError?: (error: Event) => void
) => {
  const socketRef = useRef<WebSocket | null>(null);
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null);
  const reconnectAttempts = useRef(0);
  const maxReconnectAttempts = 5;
  const reconnectDelay = 3000; // 3 seconds

  const connect = useCallback(() => {
    try {
      const wsUrl = `${WEBSOCKET_URL}/ws/${clientId}`;
      socketRef.current = new WebSocket(wsUrl);

      socketRef.current.onopen = () => {
        console.log('WebSocket connected');
        reconnectAttempts.current = 0;
        onConnect?.();
      };

      socketRef.current.onclose = (event) => {
        console.log('WebSocket disconnected:', event.code, event.reason);
        onDisconnect?.();
        
        // Attempt to reconnect if not a normal closure
        if (event.code !== 1000 && reconnectAttempts.current < maxReconnectAttempts) {
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            console.log(`Reconnecting... Attempt ${reconnectAttempts.current}/${maxReconnectAttempts}`);
            connect();
          }, reconnectDelay * Math.pow(2, reconnectAttempts.current)); // Exponential backoff
        }
      };

      socketRef.current.onerror = (error) => {
        console.error('WebSocket error:', error);
        onError?.(error);
      };

      socketRef.current.onmessage = (event) => {
        try {
          const data: WebSocketMessage = JSON.parse(event.data);
          onMessage?.(data);
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };
    } catch (error) {
      console.error('Error connecting to WebSocket:', error);
      onError?.(error as Event);
    }
  }, [clientId, onMessage, onConnect, onDisconnect, onError]);

  useEffect(() => {
    connect();

    return () => {
      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current);
      }
      if (socketRef.current) {
        socketRef.current.close(1000, 'Component unmounting');
      }
    };
  }, [connect]);

  const sendMessage = useCallback((message: any) => {
    if (socketRef.current?.readyState === WebSocket.OPEN) {
      socketRef.current.send(JSON.stringify(message));
    } else {
      console.warn('WebSocket is not connected. Message not sent:', message);
    }
  }, []);

  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (socketRef.current) {
      socketRef.current.close(1000, 'Manual disconnect');
    }
  }, []);

  const getConnectionState = useCallback(() => {
    return socketRef.current?.readyState;
  }, []);

  return { 
    sendMessage, 
    disconnect, 
    getConnectionState,
    isConnected: socketRef.current?.readyState === WebSocket.OPEN
  };
};

// Custom hook for portfolio updates specifically
export const usePortfolioUpdates = (
  onPortfolioUpdate?: (update: PortfolioUpdate) => void,
  onPriceUpdate?: (update: PriceUpdate) => void,
  onTradeUpdate?: (update: TradeUpdate) => void
) => {
  const handleMessage = useCallback((data: WebSocketMessage) => {
    switch (data.type) {
      case 'portfolio_update':
        onPortfolioUpdate?.(data);
        break;
      case 'price_update':
        onPriceUpdate?.(data);
        break;
      case 'trade_update':
        onTradeUpdate?.(data);
        break;
      default:
        console.log('Unknown message type:', data);
    }
  }, [onPortfolioUpdate, onPriceUpdate, onTradeUpdate]);

  return useWebSocket('dashboard', handleMessage);
};

// WebSocket connection status hook
export const useWebSocketStatus = (clientId: string) => {
  const [status, setStatus] = useState<'connecting' | 'connected' | 'disconnected'>('disconnected');
  const [lastConnected, setLastConnected] = useState<Date | null>(null);

  const handleConnect = useCallback(() => {
    setStatus('connected');
    setLastConnected(new Date());
  }, []);

  const handleDisconnect = useCallback(() => {
    setStatus('disconnected');
  }, []);

  const { sendMessage, disconnect, getConnectionState } = useWebSocket(
    clientId,
    undefined,
    handleConnect,
    handleDisconnect
  );

  useEffect(() => {
    setStatus('connecting');
  }, []);

  return {
    status,
    lastConnected,
    sendMessage,
    disconnect,
    getConnectionState
  };
};