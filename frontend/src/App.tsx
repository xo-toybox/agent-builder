import { useState, useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { Canvas } from './components/layout/Canvas';
import { ChatPanel } from './components/chat/ChatPanel';
import { AgentList } from './pages/AgentList';
import { AgentBuilder } from './pages/AgentBuilder';
import { useAgent } from './hooks/useAgent';
import { useAgents } from './hooks/useAgents';
import { useWebSocket } from './hooks/useWebSocket';

type View = 'list' | 'builder' | 'editor';

function App() {
  const [view, setView] = useState<View>('list');
  const [chatVisible, setChatVisible] = useState(true);

  // v0.0.2 multi-agent hooks
  const {
    agents,
    templates,
    selectedAgent,
    loading: agentsLoading,
    selectAgent,
    cloneTemplate,
    deleteAgent,
  } = useAgents();

  // Legacy v0.0.1 hooks (for editor view backward compatibility)
  const {
    config,
    tools,
    triggers,
    subagents,
    isAuthenticated,
    userEmail,
    loading: legacyLoading,
    toggleHITL,
    toggleTrigger,
    login,
    logout,
  } = useAgent();

  // WebSocket for chat with current agent
  const {
    messages,
    connected,
    pendingHITL,
    isStreaming,
    sendMessage,
    sendHITLDecision,
    clearMessages,
  } = useWebSocket();

  // Auto-navigate to editor when agent is selected
  useEffect(() => {
    if (selectedAgent) {
      setView('editor');
    }
  }, [selectedAgent]);

  const loading = agentsLoading || legacyLoading;

  if (loading) {
    return (
      <div className="h-screen flex items-center justify-center bg-bg-primary">
        <div className="text-text-secondary">Loading...</div>
      </div>
    );
  }

  // Agent List View (v0.0.2)
  if (view === 'list') {
    return (
      <div className="h-screen flex bg-bg-primary">
        <Toaster position="top-right" />
        <Sidebar
          isAuthenticated={isAuthenticated}
          userEmail={userEmail}
          onLogin={login}
          onLogout={logout}
          agents={agents}
          selectedAgentId={selectedAgent?.id}
          onSelectAgent={selectAgent}
          onNavigate={setView}
        />
        <div className="flex-1 overflow-y-auto">
          <AgentList
            agents={agents}
            templates={templates}
            onSelectAgent={(id) => selectAgent(id)}
            onCloneTemplate={cloneTemplate}
            onDeleteAgent={deleteAgent}
            onCreateNew={() => setView('builder')}
          />
        </div>
      </div>
    );
  }

  // Agent Builder View (v0.0.2)
  if (view === 'builder') {
    return (
      <div className="h-screen flex bg-bg-primary">
        <Toaster position="top-right" />
        <Sidebar
          isAuthenticated={isAuthenticated}
          userEmail={userEmail}
          onLogin={login}
          onLogout={logout}
          agents={agents}
          selectedAgentId={selectedAgent?.id}
          onSelectAgent={selectAgent}
          onNavigate={setView}
        />
        <div className="flex-1">
          <AgentBuilder
            onBack={() => setView('list')}
            onAgentCreated={(agentId) => {
              selectAgent(agentId);
            }}
          />
        </div>
      </div>
    );
  }

  // Agent Editor View (existing v0.0.1 UI with enhancements)
  return (
    <div className="h-screen flex bg-bg-primary">
      <Toaster position="top-right" />
      {/* Left Sidebar */}
      <Sidebar
        isAuthenticated={isAuthenticated}
        userEmail={userEmail}
        onLogin={login}
        onLogout={logout}
        agents={agents}
        selectedAgentId={selectedAgent?.id}
        onSelectAgent={selectAgent}
        onNavigate={setView}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <Header
          agentName={selectedAgent?.name || config?.name || 'Email Assistant'}
          agentDescription={selectedAgent?.description || 'Organizes and manages your inbox for you'}
          chatVisible={chatVisible}
          onToggleChat={() => setChatVisible(!chatVisible)}
          onBack={() => {
            setView('list');
          }}
          showBackButton={true}
        />

        {/* Content Area */}
        <div className="flex-1 flex min-h-0">
          {/* Chat Panel (Left) */}
          {chatVisible && (
            <ChatPanel
              agentName={selectedAgent?.name || config?.name || 'Email Assistant'}
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
            triggers={selectedAgent?.triggers || triggers}
            tools={selectedAgent?.tools?.map(t => ({
              name: t.name,
              description: t.name,
              enabled: t.enabled,
              hitl: t.hitl_enabled,
            })) || tools}
            agentName={selectedAgent?.name || config?.name || 'Email Assistant'}
            agentDescription={selectedAgent?.description || 'Organizes and manages your inbox for you'}
            agentInstructions={selectedAgent?.system_prompt || config?.instructions || ''}
            subagents={selectedAgent?.subagents || subagents}
            onToggleTrigger={toggleTrigger}
            onToggleHITL={toggleHITL}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
