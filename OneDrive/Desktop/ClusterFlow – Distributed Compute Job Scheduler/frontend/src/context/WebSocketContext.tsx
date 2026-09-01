import React, { createContext, useContext, useEffect, useRef, useState } from 'react';
import { WebSocketMessage } from '../types';

interface WebSocketContextType {
  isConnected: boolean;
  subscribe: (event: string, callback: (payload: any) => void) => () => void;
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined);

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isConnected, setIsConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const listenersRef = useRef<Record<string, Set<(payload: any) => void>>>({});

  useEffect(() => {
    let reconnectTimeout: number;

    const connect = () => {
      const token = localStorage.getItem('cf_token');
      if (!token) {
        setIsConnected(false);
        reconnectTimeout = window.setTimeout(connect, 3000);
        return;
      }

      const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      const host = window.location.host;
      // Connect to path matching the backend WebSocket upgrade handler
      const wsUrl = `${protocol}//${host}/api/v1/ws`;

      const ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        try {
          const message: WebSocketMessage = JSON.parse(event.data);
          const eventListeners = listenersRef.current[message.event];
          if (eventListeners) {
            eventListeners.forEach((callback) => callback(message.payload));
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message', e);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        // Attempt reconnection after a short delay
        reconnectTimeout = window.setTimeout(connect, 3000);
      };

      ws.onerror = (err) => {
        console.error('WebSocket encountered an error:', err);
        ws.close();
      };
    };

    connect();

    // Listen to token changes to reconnect WebSocket if logged in/out
    const handleAuthChange = () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
    window.addEventListener('auth_login', handleAuthChange);
    window.addEventListener('auth_logout', handleAuthChange);

    return () => {
      if (wsRef.current) {
        wsRef.current.close();
      }
      clearTimeout(reconnectTimeout);
      window.removeEventListener('auth_login', handleAuthChange);
      window.removeEventListener('auth_logout', handleAuthChange);
    };
  }, []);

  const subscribe = (event: string, callback: (payload: any) => void) => {
    if (!listenersRef.current[event]) {
      listenersRef.current[event] = new Set();
    }
    listenersRef.current[event].add(callback);

    // Return unsubscription function
    return () => {
      const eventListeners = listenersRef.current[event];
      if (eventListeners) {
        eventListeners.delete(callback);
        if (eventListeners.size === 0) {
          delete listenersRef.current[event];
        }
      }
    };
  };

  return (
    <WebSocketContext.Provider value={{ isConnected, subscribe }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => {
  const context = useContext(WebSocketContext);
  if (context === undefined) {
    throw new Error('useWebSocket must be used within a WebSocketProvider');
  }
  return context;
};
