// frontend/src/services/websocket.ts
import { useEffect, useRef } from 'react';
import io, { Socket } from 'socket.io-client';

const WEBSOCKET_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000';

export const useWebSocket = (clientId: string, onMessage?: (data: any) => void) => {
  const socketRef = useRef<Socket | null>(null);

  useEffect(() => {
    // Initialize WebSocket connection
    socketRef.current = io(WEBSOCKET_URL, {
      transports: ['websocket'],
      query: { client_id: clientId }
    });

    const socket = socketRef.current;

    socket.on('connect', () => {
      console.log('WebSocket connected');
    });

    socket.on('disconnect', () => {
      console.log('WebSocket disconnected');
    });

    socket.on('portfolio_update', (data) => {
      if (onMessage) {
        onMessage(data);
      }
    });

    socket.on('trade_update', (data) => {
      if (onMessage) {
        onMessage(data);
      }
    });

    socket.on('price_update', (data) => {
      if (onMessage) {
        onMessage(data);
      }
    });

    return () => {
      socket.disconnect();
    };
  }, [clientId, onMessage]);

  const sendMessage = (event: string, data: any) => {
    if (socketRef.current?.connected) {
      socketRef.current.emit(event, data);
    }
  };

  return { sendMessage };
};
