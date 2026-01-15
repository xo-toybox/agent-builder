import { useState } from 'react';
import type { Message, HITLInterrupt } from '../../types';

interface ChatPanelProps {
  agentName: string;
  messages: Message[];
  connected: boolean;
  isStreaming: boolean;
  pendingHITL: HITLInterrupt | null;
  onSendMessage: (content: string) => void;
  onHITLDecision: (
    decision: 'approve' | 'edit' | 'reject',
    toolCallId: string,
    newArgs?: Record<string, unknown>
  ) => void;
  onClear: () => void;
  onHide: () => void;
}

export function ChatPanel({
  agentName,
  messages,
  connected,
  isStreaming,
  pendingHITL,
  onSendMessage,
  onHITLDecision,
  onClear,
  onHide,
}: ChatPanelProps) {
  const [input, setInput] = useState('');

  const handleSubmit = () => {
    if (!input.trim() || isStreaming || pendingHITL) return;
    onSendMessage(input.trim());
    setInput('');
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div className="w-[420px] border-r border-border bg-bg-secondary flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <button onClick={onHide} className="flex items-center gap-2 hover:bg-bg-tertiary rounded-md px-2 py-1 -ml-2">
          <svg className="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
          <span className="text-sm text-text-secondary">Hide Chat</span>
        </button>
        <div className="flex items-center gap-2">
          <div className={`w-2 h-2 rounded-full ${connected ? 'bg-accent-green' : 'bg-accent-red'}`} />
          <button onClick={onClear} className="text-xs text-text-muted hover:text-text-secondary">
            Clear
          </button>
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col items-center justify-center text-center px-8">
            <div className="w-12 h-12 bg-accent-orange rounded-lg flex items-center justify-center mb-4">
              <span className="text-white font-bold">EA</span>
            </div>
            <h3 className="text-lg font-semibold text-text-primary">Chat with {agentName}</h3>
            <p className="text-sm text-text-secondary mt-2">
              Test your agent or ask it to make changes
            </p>
          </div>
        ) : (
          <div className="p-4 space-y-4">
            {messages.map((message) => (
              <MessageBubble key={message.id} message={message} />
            ))}
            {isStreaming && (
              <div className="flex items-center gap-2 text-text-muted">
                <div className="flex gap-1">
                  <span className="w-2 h-2 bg-text-muted rounded-full animate-bounce" />
                  <span className="w-2 h-2 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: '0.1s' }} />
                  <span className="w-2 h-2 bg-text-muted rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                </div>
              </div>
            )}
          </div>
        )}
      </div>

      {/* HITL Approval */}
      {pendingHITL && (
        <HITLApprovalInline
          interrupt={pendingHITL}
          onDecision={onHITLDecision}
        />
      )}

      {/* Input Area */}
      <div className="p-4 border-t border-border">
        <div className="relative">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask your agent to update itself..."
            disabled={!connected || isStreaming || !!pendingHITL}
            rows={2}
            className="w-full px-4 py-3 pr-12 bg-bg-tertiary border border-border rounded-lg text-text-primary text-sm resize-none focus:border-accent-teal focus:outline-none disabled:opacity-50"
          />
          <button
            onClick={handleSubmit}
            disabled={!connected || isStreaming || !!pendingHITL || !input.trim()}
            className="absolute right-3 bottom-3 p-1.5 text-accent-orange disabled:text-text-muted"
          >
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
              <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z"/>
            </svg>
          </button>
        </div>

        {/* Quick Actions */}
        <div className="flex gap-2 mt-3">
          <button className="px-3 py-1.5 text-xs border border-border rounded-md text-text-secondary hover:bg-bg-tertiary">
            Change instructions
          </button>
          <button className="px-3 py-1.5 text-xs border border-border rounded-md text-text-secondary hover:bg-bg-tertiary">
            Add subagent
          </button>
          <button className="px-3 py-1.5 text-xs border border-border rounded-md text-text-secondary hover:bg-bg-tertiary">
            Add tools
          </button>
        </div>
      </div>
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const isTool = message.role === 'tool';
  const isHITL = message.role === 'hitl';

  if (isTool) {
    return (
      <div className="bg-bg-tertiary rounded-lg p-3">
        <div className="flex items-center gap-2 text-text-muted mb-1">
          <span className="text-xs">Tool</span>
          <span className="font-mono text-accent-teal text-xs">{message.toolName}</span>
        </div>
        <pre className="text-text-secondary text-xs overflow-x-auto whitespace-pre-wrap">
          {message.content}
        </pre>
      </div>
    );
  }

  if (isHITL) {
    return (
      <div className="bg-accent-orange/10 border border-accent-orange/30 rounded-lg p-3">
        <div className="flex items-center gap-2 text-accent-orange mb-1">
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
          </svg>
          <span className="text-sm font-medium">Approval Required</span>
        </div>
        <p className="text-sm text-text-secondary">{message.content}</p>
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-accent-teal text-white'
            : 'bg-bg-tertiary text-text-primary'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}

function HITLApprovalInline({
  interrupt,
  onDecision,
}: {
  interrupt: HITLInterrupt;
  onDecision: (decision: 'approve' | 'edit' | 'reject', toolCallId: string, newArgs?: Record<string, unknown>) => void;
}) {
  const [editing, setEditing] = useState(false);
  const [editedArgs, setEditedArgs] = useState(JSON.stringify(interrupt.args, null, 2));

  const handleApprove = () => onDecision('approve', interrupt.tool_call_id);
  const handleReject = () => onDecision('reject', interrupt.tool_call_id);
  const handleConfirmEdit = () => {
    try {
      const parsed = JSON.parse(editedArgs);
      onDecision('edit', interrupt.tool_call_id, parsed);
    } catch {
      // Invalid JSON
    }
  };

  return (
    <div className="p-4 bg-accent-orange/5 border-t border-accent-orange/30">
      <div className="flex items-center gap-2 text-accent-orange mb-3">
        <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 24 24">
          <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
        </svg>
        <span className="font-medium">Approve {interrupt.name}?</span>
      </div>

      {editing ? (
        <textarea
          value={editedArgs}
          onChange={(e) => setEditedArgs(e.target.value)}
          rows={6}
          className="w-full px-3 py-2 bg-bg-secondary border border-border rounded-md text-text-primary text-sm font-mono mb-3"
        />
      ) : (
        <pre className="bg-bg-secondary border border-border rounded-md p-3 text-sm text-text-secondary overflow-x-auto mb-3">
          {JSON.stringify(interrupt.args, null, 2)}
        </pre>
      )}

      <div className="flex gap-2">
        <button
          onClick={handleApprove}
          className="px-4 py-2 bg-accent-green text-white rounded-md text-sm font-medium hover:bg-green-600"
        >
          Approve
        </button>
        {editing ? (
          <button
            onClick={handleConfirmEdit}
            className="px-4 py-2 bg-accent-blue text-white rounded-md text-sm font-medium hover:bg-blue-600"
          >
            Confirm
          </button>
        ) : (
          <button
            onClick={() => setEditing(true)}
            className="px-4 py-2 bg-bg-tertiary text-text-primary rounded-md text-sm font-medium hover:bg-border"
          >
            Edit
          </button>
        )}
        <button
          onClick={handleReject}
          className="px-4 py-2 bg-accent-red text-white rounded-md text-sm font-medium hover:bg-red-600"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
