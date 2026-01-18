import { useState, useEffect, useRef, useCallback } from 'react';
import type { Message, HITLInterrupt, MemoryEditRequest, WSMessageType } from '../types';

function buildWsUrl(agentId: string): string {
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return `${protocol}//${host}/api/v1/chat/${agentId}`;
}

export function useWebSocket(agentId: string | null) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [connected, setConnected] = useState(false);
  const [pendingHITL, setPendingHITL] = useState<HITLInterrupt | null>(null);
  const [pendingMemoryEdit, setPendingMemoryEdit] = useState<MemoryEditRequest | null>(null); // v0.0.3
  const [isStreaming, setIsStreaming] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);
  const messageIdRef = useRef(0);
  const isStreamingRef = useRef(false);
  const shouldReconnectRef = useRef(true);

  const connect = useCallback(() => {
    if (!agentId) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;

    const url = buildWsUrl(agentId);
    console.log('WebSocket connecting to:', url);
    const ws = new WebSocket(url);
    wsRef.current = ws;

    ws.onopen = () => {
      setConnected(true);
      console.log('WebSocket connected');
    };

    ws.onclose = (event) => {
      setConnected(false);
      console.log('WebSocket disconnected:', event.code, event.reason);

      // Auto-reconnect if we should and weren't intentionally closed
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
      console.error('WebSocket error:', error);
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
          // Append to last assistant message or create new one
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
              toolArgs: data.args,
            },
          ]);
          break;

        case 'tool_result':
          setMessages((prev) => {
            // Find and update the last tool message with this name
            const idx = [...prev].reverse().findIndex(
              (m) => m.role === 'tool' && m.toolName === data.name
            );
            if (idx === -1) return prev;
            const actualIdx = prev.length - 1 - idx;
            const updated = [...prev];
            updated[actualIdx] = {
              ...updated[actualIdx],
              content: `${data.name}: ${typeof data.result === 'string' ? data.result : JSON.stringify(data.result, null, 2)}`,
            };
            return updated;
          });
          break;

        case 'hitl_interrupt':
          setPendingHITL({
            tool_call_id: data.tool_call_id,
            name: data.name,
            args: data.args,
          });
          setMessages((prev) => [
            ...prev,
            {
              id: `msg-${++messageIdRef.current}`,
              role: 'hitl',
              content: `Approval required for ${data.name}`,
              toolName: data.name,
              toolArgs: data.args,
              toolCallId: data.tool_call_id,
            },
          ]);
          isStreamingRef.current = false;
          setIsStreaming(false);
          break;

        // v0.0.3: Memory edit request handling
        case 'memory_edit_request':
          setPendingMemoryEdit({
            request_id: data.request_id,
            tool_call_id: data.tool_call_id,
            path: data.path,
            operation: data.operation as 'write' | 'append' | 'delete',
            current_content: data.current_content,
            proposed_content: data.proposed_content,
            reason: data.reason,
            suspicious_flags: data.suspicious_flags,
          });
          setMessages((prev) => [
            ...prev,
            {
              id: `msg-${++messageIdRef.current}`,
              role: 'hitl',
              content: `Memory update requested: ${data.path}`,
              toolName: 'write_memory',
              toolArgs: { path: data.path, reason: data.reason },
              toolCallId: data.tool_call_id,
            },
          ]);
          isStreamingRef.current = false;
          setIsStreaming(false);
          break;

        case 'memory_edit_complete':
          setMessages((prev) => [
            ...prev,
            {
              id: `msg-${++messageIdRef.current}`,
              role: 'tool',
              content: data.success
                ? `Memory updated: ${data.path}`
                : `Memory update rejected: ${data.path}`,
              toolName: 'write_memory',
            },
          ]);
          break;

        case 'complete':
          isStreamingRef.current = false;
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
          isStreamingRef.current = false;
          setIsStreaming(false);
          break;

        case 'new_email':
          // Could add notification here
          console.log('New email:', data.email);
          break;
      }
    };
  }, [agentId]);

  // Connect/reconnect when agentId changes
  useEffect(() => {
    // Close existing connection when agent changes
    if (wsRef.current) {
      shouldReconnectRef.current = false;
      wsRef.current.close(1000, 'Agent changed');
      wsRef.current = null;
    }

    // Clear state for new agent
    setMessages([]);
    setPendingHITL(null);
    setPendingMemoryEdit(null);
    setIsStreaming(false);
    isStreamingRef.current = false;
    messageIdRef.current = 0;

    // Don't connect if no agent selected
    if (!agentId) {
      setConnected(false);
      return;
    }

    // Connect to new agent
    shouldReconnectRef.current = true;
    connect();

    return () => {
      shouldReconnectRef.current = false;
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmount');
      }
    };
  }, [agentId, connect]);

  const sendMessage = useCallback((content: string) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      console.error('WebSocket not connected, state:', wsRef.current?.readyState);
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

    isStreamingRef.current = true;
    setIsStreaming(true);
    wsRef.current.send(JSON.stringify({ type: 'message', content }));
  }, []);

  const sendHITLDecision = useCallback(
    (
      decision: 'approve' | 'edit' | 'reject',
      toolCallId: string,
      newArgs?: Record<string, unknown>
    ) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.error('WebSocket not connected');
        return;
      }

      isStreamingRef.current = true;
      setIsStreaming(true);
      setPendingHITL(null);

      wsRef.current.send(
        JSON.stringify({
          type: 'hitl_decision',
          tool_call_id: toolCallId,
          decision,
          new_args: newArgs,
        })
      );

      // Add decision message
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-${++messageIdRef.current}`,
          role: 'user',
          content: `Decision: ${decision}${newArgs ? ` with edited args` : ''}`,
        },
      ]);
    },
    []
  );

  // v0.0.3: Send memory edit decision
  const sendMemoryEditDecision = useCallback(
    (
      decision: 'approve' | 'edit' | 'reject',
      requestId: string,
      toolCallId: string,
      editedContent?: string
    ) => {
      if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
        console.error('WebSocket not connected');
        return;
      }

      isStreamingRef.current = true;
      setIsStreaming(true);
      setPendingMemoryEdit(null);

      wsRef.current.send(
        JSON.stringify({
          type: 'memory_edit_decision',
          request_id: requestId,
          tool_call_id: toolCallId,
          decision,
          edited_content: editedContent,
        })
      );

      // Add decision message
      setMessages((prev) => [
        ...prev,
        {
          id: `msg-${++messageIdRef.current}`,
          role: 'user',
          content: `Memory ${decision === 'approve' ? 'approved' : decision === 'edit' ? 'approved with edits' : 'rejected'}`,
        },
      ]);
    },
    []
  );

  const clearMessages = useCallback(() => {
    setMessages([]);
    setPendingHITL(null);
    setPendingMemoryEdit(null);
  }, []);

  return {
    messages,
    connected,
    pendingHITL,
    pendingMemoryEdit, // v0.0.3
    isStreaming,
    sendMessage,
    sendHITLDecision,
    sendMemoryEditDecision, // v0.0.3
    clearMessages,
    reconnect: connect,
  };
}
