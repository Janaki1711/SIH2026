import { useState, useEffect, useRef, useCallback } from 'react';

export type WebSocketState = 'CONNECTING' | 'OPEN' | 'CLOSED';

export function useWebSocket(url: string) {
  const [state, setState] = useState<WebSocketState>('CLOSED');
  const [lastMessage, setLastMessage] = useState<any>(null);
  const ws = useRef<WebSocket | null>(null);
  const reconnectTimeout = useRef<number | null>(null);

  const connect = useCallback(() => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    
    setState('CONNECTING');
    const socket = new WebSocket(url);
    
    socket.onopen = () => {
      setState('OPEN');
      console.log(`[WS] Connected to ${url}`);
      if (reconnectTimeout.current) {
        clearTimeout(reconnectTimeout.current);
        reconnectTimeout.current = null;
      }
    };
    
    socket.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        setLastMessage(data);
      } catch (e) {
        console.error('[WS] Failed to parse message', event.data);
      }
    };
    
    socket.onclose = () => {
      setState('CLOSED');
      ws.current = null;
      // Auto reconnect
      reconnectTimeout.current = window.setTimeout(connect, 2000);
    };
    
    socket.onerror = (err) => {
      console.error('[WS] Error', err);
    };
    
    ws.current = socket;
  }, [url]);

  useEffect(() => {
    connect();
    return () => {
      if (reconnectTimeout.current) clearTimeout(reconnectTimeout.current);
      if (ws.current) {
        ws.current.onclose = null; // Prevent reconnect on unmount
        ws.current.close();
      }
    };
  }, [connect]);

  const sendMessage = useCallback((msg: any) => {
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify(msg));
    } else {
      console.warn('[WS] Cannot send, socket not open', msg);
    }
  }, []);

  return { state, lastMessage, sendMessage };
}
