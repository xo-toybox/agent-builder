import { useState, useEffect, useRef, useCallback } from 'react';
import type { BuilderMessage, WSMessageType } from '../types';

const WS_URL = `${window.location.protocol === 'https:' ? 'wss:' : 'ws:'}//${window.location.host}/api/v1/wizard/chat`;

export function useBuilderChat() {
  const [messages, setMessages] = useState<BuilderMessage[]>([]);
  const [connected, setConnected] = useState(false);
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messageIdRef = useRef(0);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;

    console.log('Builder WebSocket connecting to:', WS_URL);
    const ws = new WebSocket(WS_URL);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log('Builder WebSocket connected');
    };

    ws.onclose = (event) => {
      setConnected(false);
      console.log('Builder WebSocket disconnected:', event.code, event.reason);

      if (shouldReconnectRef.current && event.code !== 1000) {
        console.log('Attempting to reconnect in 1s...');
        setTimeout(() => {
          if (shouldReconnectRef.current) {
            connect();
          }
        }, 1000);
      }
    };

    ws.onerror = (error) => {
      console.error('Builder WebSocket error:', error);
    };

    ws.onmessage = (event) => {
      let data: WSMessageType;
      try {
        data = JSON.parse(event.data);
      } catch (e) {
        console.error('Failed to parse WebSocket message:', e);
        return;
      }

      switch (data.type) {
        case 'token':
          setMessages((prev) => {
            const lastMsg = prev[prev.length - 1];
            if (lastMsg?.role === 'assistant') {
              return [
                ...prev.slice(0, -1),
                { ...lastMsg, content: lastMsg.content + data.content },
              ];
            }
            return [
              ...prev,
              {
                id: `msg-${++messageIdRef.current}`,
                role: 'assistant',
                content: data.content,
              },
            ];
          });
          break;

        case 'tool_call':
          setMessages((prev) => [
            ...prev,
            {
              id: `msg-${++messageIdRef.current}`,
              role: 'tool',
              content: `Calling ${data.name}...`,
              toolName: data.name,
            },
          ]);
          break;

        case 'tool_result':
          setMessages((prev) => {
            const idx = [...prev].reverse().findIndex(
              (m) => m.role === 'tool' && m.toolName === data.name
            );
            if (idx === -1) return prev;
            const actualIdx = prev.length - 1 - idx;
            const updated = [...prev];
            updated[actualIdx] = {
              ...updated[actualIdx],
              content: `${data.name}: ${typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2)}`,
              toolResult: data.result,
            };
            return updated;
          });
          break;

        case 'complete':
          setIsStreaming(false);
          break;

        case 'error':
          setMessages((prev) => [
            ...prev,
            {
              id: `msg-${++messageIdRef.current}`,
              role: 'assistant',
              content: `Error: ${data.message}`,
            },
          ]);
          setIsStreaming(false);
          break;

        case 'cleared':
          setMessages([]);
          break;
      }
    };
  }, []);

  useEffect(() => {
    shouldReconnectRef.current = true;
    connect();
    return () => {
      shouldReconnectRef.current = false;
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
      }
    };
  }, [connect]);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected');
      return;
    }

    setMessages((prev) => [
      ...prev,
      {
        id: `msg-${++messageIdRef.current}`,
        role: 'user',
        content,
      },
    ]);

    setIsStreaming(true);
    wsRef.current.send(JSON.stringify({ type: 'message', content }));
  }, []);

  const clearMessages = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'clear' }));
    }
    setMessages([]);
  }, []);

  return {
    messages,
    connected,
    isStreaming,
    sendMessage,
    clearMessages,
    reconnect: connect,
  };
}
