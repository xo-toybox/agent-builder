import { useState } from 'react';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { Canvas } from './components/layout/Canvas';
import { ChatPanel } from './components/chat/ChatPanel';
import { useAgent } from './hooks/useAgent';
import { useWebSocket } from './hooks/useWebSocket';

function App() {
  const [chatVisible, setChatVisible] = useState(true);

  const {
    config,
    tools,
    triggers,
    subagents,
    isAuthenticated,
    userEmail,
    loading,
    toggleHITL,
    toggleTrigger,
    login,
    logout,
  } = useAgent();

  // Use default URL from hook to avoid recreation on every render
  const {
    messages,
    connected,
    pendingHITL,
    isStreaming,
    sendMessage,
    sendHITLDecision,
    clearMessages,
  } = useWebSocket();

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-bg-primary">
        <div className="text-text-secondary">Loading...</div>
      </div>
    );
  }

  return (
    <div className="h-screen flex bg-bg-primary">
      {/* Left Sidebar */}
      <Sidebar
        isAuthenticated={isAuthenticated}
        userEmail={userEmail}
        onLogin={login}
        onLogout={logout}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <Header
          agentName={config?.name || 'Email Assistant'}
          agentDescription="Organizes and manages your inbox for you"
          chatVisible={chatVisible}
          onToggleChat={() => setChatVisible(!chatVisible)}
        />

        {/* Content Area */}
        <div className="flex-1 flex min-h-0">
          {/* Chat Panel (Left) */}
          {chatVisible && (
            <ChatPanel
              agentName={config?.name || 'Email Assistant'}
              messages={messages}
              connected={connected}
              isStreaming={isStreaming}
              pendingHITL={pendingHITL}
              onSendMessage={sendMessage}
              onHITLDecision={sendHITLDecision}
              onClear={clearMessages}
              onHide={() => setChatVisible(false)}
            />
          )}

          {/* Canvas (Right) */}
          <Canvas
            triggers={triggers}
            tools={tools}
            agentName={config?.name || 'Email Assistant'}
            agentDescription="Organizes and manages your inbox for you"
            agentInstructions={config?.instructions || ''}
            subagents={subagents}
            onToggleTrigger={toggleTrigger}
            onToggleHITL={toggleHITL}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
