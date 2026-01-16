import { useBuilderChat } from '../hooks/useBuilderChat';
import { useState, useRef, useEffect } from 'react';

interface AgentBuilderProps {
  onBack: () => void;
  onAgentCreated: (agentId: string) => void;
}

export function AgentBuilder({ onBack, onAgentCreated }: AgentBuilderProps) {
  const { messages, connected, isStreaming, sendMessage, clearMessages } = useBuilderChat();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Check if an agent was created in the last message
  useEffect(() => {
    const lastMessage = messages[messages.length - 1];
    if (lastMessage?.role === 'tool' && lastMessage.content?.includes('Created agent')) {
      // Extract agent ID from message
      const match = lastMessage.content.match(/ID: ([a-f0-9-]+)/);
      if (match) {
        // Wait a moment then redirect
        setTimeout(() => {
          onAgentCreated(match[1]);
        }, 2000);
      }
    }
  }, [messages, onAgentCreated]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isStreaming) return;
    sendMessage(input.trim());
    setInput('');
  };

  return (
    <div className="h-full flex flex-col bg-bg-primary">
      {/* Header */}
      <div className="flex items-center justify-between px-6 py-4 border-b border-border-primary">
        <div className="flex items-center gap-4">
          <button
            onClick={onBack}
            className="p-2 hover:bg-bg-secondary rounded-lg transition-colors"
          >
            <svg className="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
          <div>
            <h1 className="text-lg font-medium text-text-primary">Create New Agent</h1>
            <p className="text-sm text-text-secondary">
              Describe what you want your agent to do
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${connected ? 'bg-green-500' : 'bg-red-500'}`} />
          <span className="text-xs text-text-secondary">
            {connected ? 'Connected' : 'Disconnected'}
          </span>
        </div>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 ? (
          <div className="h-full flex items-center justify-center">
            <div className="text-center max-w-md">
              <h2 className="text-xl font-medium text-text-primary mb-2">
                What kind of agent do you want to build?
              </h2>
              <p className="text-text-secondary mb-6">
                Describe your ideal AI assistant and I'll help you create it.
                For example:
              </p>
              <div className="space-y-2 text-left">
                {[
                  'A newsletter curator that finds and summarizes important emails',
                  'A meeting scheduler that checks calendar conflicts and sends invites',
                  'A daily briefing agent that prepares my schedule and priority emails',
                ].map((example, i) => (
                  <button
                    key={i}
                    onClick={() => sendMessage(example)}
                    className="w-full p-3 text-left bg-bg-secondary rounded-lg border border-border-primary hover:border-accent-primary transition-colors text-sm text-text-secondary"
                  >
                    "{example}"
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div className="space-y-4 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <div
                key={msg.id}
                className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                <div
                  className={`max-w-[80%] rounded-lg p-4 ${
                    msg.role === 'user'
                      ? 'bg-accent-primary text-white'
                      : msg.role === 'tool'
                      ? 'bg-bg-tertiary border border-border-primary text-text-secondary text-sm font-mono'
                      : 'bg-bg-secondary text-text-primary'
                  }`}
                >
                  {msg.role === 'tool' && (
                    <div className="text-xs text-accent-primary mb-1">
                      🔧 {msg.toolName}
                    </div>
                  )}
                  <div className="whitespace-pre-wrap">{msg.content}</div>
                </div>
              </div>
            ))}
            {isStreaming && (
              <div className="flex justify-start">
                <div className="bg-bg-secondary rounded-lg p-4">
                  <span className="inline-block w-2 h-4 bg-text-secondary animate-pulse" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="border-t border-border-primary p-4">
        <form onSubmit={handleSubmit} className="max-w-3xl mx-auto flex gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Describe your agent..."
            disabled={isStreaming}
            className="flex-1 px-4 py-3 bg-bg-secondary border border-border-primary rounded-lg text-text-primary placeholder-text-secondary focus:outline-none focus:ring-2 focus:ring-accent-primary disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isStreaming}
            className="px-6 py-3 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary transition-colors disabled:opacity-50"
          >
            Send
          </button>
        </form>
        {messages.length > 0 && (
          <div className="max-w-3xl mx-auto mt-2">
            <button
              onClick={clearMessages}
              className="text-xs text-text-secondary hover:text-text-primary"
            >
              Clear conversation
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
