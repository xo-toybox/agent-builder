import { useEffect, useRef } from 'react';
import type { Message } from '../../types';

interface MessageListProps {
  messages: Message[];
  isStreaming: boolean;
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  const bottomRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  return (
    <div className="h-full overflow-y-auto p-4 space-y-4">
      {messages.length === 0 ? (
        <div className="text-center text-gray-500 py-8">
          <p>No messages yet</p>
          <p className="text-sm mt-1">Start a conversation with your agent</p>
        </div>
      ) : (
        messages.map((message) => (
          <MessageBubble key={message.id} message={message} />
        ))
      )}

      {isStreaming && (
        <div className="flex items-center gap-2 text-gray-400">
          <div className="flex gap-1">
            <span className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" />
            <span
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '0.1s' }}
            />
            <span
              className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"
              style={{ animationDelay: '0.2s' }}
            />
          </div>
        </div>
      )}

      <div ref={bottomRef} />
    </div>
  );
}

function MessageBubble({ message }: { message: Message }) {
  const isUser = message.role === 'user';
  const isTool = message.role === 'tool';
  const isHITL = message.role === 'hitl';

  if (isTool) {
    return (
      <div className="bg-bg-tertiary rounded-lg p-3 text-sm">
        <div className="flex items-center gap-2 text-gray-400 mb-1">
          <span className="text-xs">Tool Call</span>
          <span className="font-mono text-accent-teal">{message.toolName}</span>
        </div>
        <pre className="text-gray-300 text-xs overflow-x-auto whitespace-pre-wrap">
          {message.content}
        </pre>
      </div>
    );
  }

  if (isHITL) {
    return (
      <div className="bg-yellow-900/20 border border-yellow-500/30 rounded-lg p-3">
        <div className="flex items-center gap-2 text-yellow-500 mb-1">
          <svg
            className="w-4 h-4"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <span className="text-sm font-medium">Approval Required</span>
        </div>
        <p className="text-sm text-gray-300">{message.content}</p>
        {message.toolArgs && (
          <pre className="mt-2 text-xs text-gray-400 bg-black/20 p-2 rounded overflow-x-auto">
            {JSON.stringify(message.toolArgs, null, 2)}
          </pre>
        )}
      </div>
    );
  }

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] rounded-lg px-4 py-2 ${
          isUser
            ? 'bg-accent-teal text-white'
            : 'bg-bg-tertiary text-gray-200'
        }`}
      >
        <p className="text-sm whitespace-pre-wrap">{message.content}</p>
      </div>
    </div>
  );
}
