import { MessageList } from './MessageList';
import { MessageInput } from './MessageInput';
import { HITLApproval } from './HITLApproval';
import type { Message, HITLInterrupt } from '../../types';

interface ChatDrawerProps {
  isOpen: boolean;
  onClose: () => void;
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
}

export function ChatDrawer({
  isOpen,
  onClose,
  messages,
  connected,
  isStreaming,
  pendingHITL,
  onSendMessage,
  onHITLDecision,
  onClear,
}: ChatDrawerProps) {
  return (
    <div
      className={`fixed inset-y-0 right-0 w-[480px] bg-bg-secondary border-l border-border transform transition-transform duration-300 ease-in-out z-50 flex flex-col ${
        isOpen ? 'translate-x-0' : 'translate-x-full'
      }`}
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <div className="flex items-center gap-3">
          <h3 className="text-white font-medium">Chat</h3>
          <div
            className={`w-2 h-2 rounded-full ${
              connected ? 'bg-accent-green' : 'bg-accent-red'
            }`}
            title={connected ? 'Connected' : 'Disconnected'}
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onClear}
            className="text-gray-400 hover:text-white text-sm px-2 py-1"
          >
            Clear
          </button>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-white text-xl leading-none"
          >
            &times;
          </button>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-hidden">
        <MessageList messages={messages} isStreaming={isStreaming} />
      </div>

      {/* HITL Approval */}
      {pendingHITL && (
        <div className="border-t border-border">
          <HITLApproval
            toolCallId={pendingHITL.tool_call_id}
            toolName={pendingHITL.name}
            args={pendingHITL.args}
            onDecision={onHITLDecision}
          />
        </div>
      )}

      {/* Input */}
      <div className="border-t border-border">
        <MessageInput
          onSend={onSendMessage}
          disabled={!connected || isStreaming || !!pendingHITL}
        />
      </div>
    </div>
  );
}
