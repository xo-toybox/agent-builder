import { useState, useEffect, useCallback } from 'react';
import { Toaster } from 'react-hot-toast';
import { Sidebar } from './components/layout/Sidebar';
import { Header } from './components/layout/Header';
import { Canvas } from './components/layout/Canvas';
import { ChatPanel } from './components/chat/ChatPanel';
import { AgentList } from './pages/AgentList';
import { AgentBuilder } from './pages/AgentBuilder';
import { GlobalSettingsModal } from './components/modals/GlobalSettingsModal';
import { AgentSettingsModal } from './components/modals/AgentSettingsModal';
import { useAuth } from './hooks/useAuth';
import { useAgents } from './hooks/useAgents';
import { useWebSocket } from './hooks/useWebSocket';

type View = 'list' | 'builder' | 'editor';

function App() {
  const [view, setView] = useState<View>('list');
  const [chatVisible, setChatVisible] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Modal state
  const [globalSettingsOpen, setGlobalSettingsOpen] = useState(false);
  const [agentSettingsOpen, setAgentSettingsOpen] = useState(false);

  // Authentication
  const {
    isAuthenticated,
    userEmail,
    loading: authLoading,
    login,
    logout,
  } = useAuth();

  // Agent management
  const {
    agents,
    templates,
    selectedAgent,
    loading: agentsLoading,
    selectAgent,
    updateAgent,
    cloneTemplate,
    deleteAgent,
    toggleHITL: toggleHITLFn,
    toggleTrigger: toggleTriggerFn,
    refreshAgents,
  } = useAgents();

  // Wrap toggle functions to use current agent ID
  const handleToggleHITL = useCallback((toolName: string, enabled: boolean) => {
    if (selectedAgent) {
      toggleHITLFn(selectedAgent.id, toolName, enabled);
    }
  }, [selectedAgent, toggleHITLFn]);

  const handleToggleTrigger = useCallback((triggerId: string) => {
    if (selectedAgent) {
      toggleTriggerFn(selectedAgent.id, triggerId);
    }
  }, [selectedAgent, toggleTriggerFn]);

  // WebSocket for chat with current agent
  const {
    messages,
    connected,
    pendingHITL,
    pendingMemoryEdit, // v0.0.3
    isStreaming,
    sendMessage,
    sendHITLDecision,
    sendMemoryEditDecision, // v0.0.3
    clearMessages,
  } = useWebSocket(selectedAgent?.id ?? null);

  // Auto-navigate to editor when agent is selected
  useEffect(() => {
    if (selectedAgent) {
      setView('editor');
    }
  }, [selectedAgent]);

  // Handle save changes
  const handleSaveChanges = async () => {
    if (!selectedAgent) return;
    setIsSaving(true);
    try {
      await updateAgent(selectedAgent.id, {
        name: selectedAgent.name,
        description: selectedAgent.description,
        system_prompt: selectedAgent.system_prompt,
        tools: selectedAgent.tools,
        triggers: selectedAgent.triggers,
      });
    } finally {
      setIsSaving(false);
    }
  };

  const loading = agentsLoading || authLoading;

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
        <GlobalSettingsModal
          isOpen={globalSettingsOpen}
          onClose={() => setGlobalSettingsOpen(false)}
        />
        <Sidebar
          isAuthenticated={isAuthenticated}
          userEmail={userEmail}
          onLogin={login}
          onLogout={logout}
          agents={agents}
          selectedAgentId={selectedAgent?.id}
          onSelectAgent={selectAgent}
          onNavigate={setView}
          onOpenSettings={() => setGlobalSettingsOpen(true)}
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
        <GlobalSettingsModal
          isOpen={globalSettingsOpen}
          onClose={() => setGlobalSettingsOpen(false)}
        />
        <Sidebar
          isAuthenticated={isAuthenticated}
          userEmail={userEmail}
          onLogin={login}
          onLogout={logout}
          agents={agents}
          selectedAgentId={selectedAgent?.id}
          onSelectAgent={selectAgent}
          onNavigate={setView}
          onOpenSettings={() => setGlobalSettingsOpen(true)}
        />
        <div className="flex-1">
          <AgentBuilder
            onBack={() => setView('list')}
            onAgentCreated={async (agentId) => {
              await refreshAgents(); // Refresh sidebar list
              selectAgent(agentId);
            }}
          />
        </div>
      </div>
    );
  }

  // Handle agent update from settings modal
  const handleAgentSettingsUpdate = (updatedAgent: typeof selectedAgent) => {
    if (updatedAgent) {
      // Refresh the agent list to get updated data
      selectAgent(updatedAgent.id);
    }
  };

  // Handle agent deletion from settings modal
  const handleAgentSettingsDelete = () => {
    setAgentSettingsOpen(false);
    setView('list');
  };

  // Agent Editor View (existing v0.0.1 UI with enhancements)
  return (
    <div className="h-screen flex bg-bg-primary">
      <Toaster position="top-right" />
      <GlobalSettingsModal
        isOpen={globalSettingsOpen}
        onClose={() => setGlobalSettingsOpen(false)}
      />
      <AgentSettingsModal
        isOpen={agentSettingsOpen}
        onClose={() => setAgentSettingsOpen(false)}
        agent={selectedAgent}
        onAgentUpdate={handleAgentSettingsUpdate}
        onAgentDelete={handleAgentSettingsDelete}
      />
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
        onOpenSettings={() => setGlobalSettingsOpen(true)}
      />

      {/* Main Content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <Header
          agentName={selectedAgent?.name || 'Email Assistant'}
          agentDescription={selectedAgent?.description || 'Organizes and manages your inbox for you'}
          chatVisible={chatVisible}
          onToggleChat={() => setChatVisible(!chatVisible)}
          onBack={() => {
            setView('list');
          }}
          showBackButton={true}
          onSave={handleSaveChanges}
          isSaving={isSaving}
          onOpenAgentSettings={() => setAgentSettingsOpen(true)}
        />

        {/* Content Area */}
        <div className="flex-1 flex min-h-0">
          {/* Chat Panel (Left) */}
          {chatVisible && (
            <ChatPanel
              agentName={selectedAgent?.name || 'Email Assistant'}
              messages={messages}
              connected={connected}
              isStreaming={isStreaming}
              pendingHITL={pendingHITL}
              pendingMemoryEdit={pendingMemoryEdit}
              onSendMessage={sendMessage}
              onHITLDecision={sendHITLDecision}
              onMemoryEditDecision={sendMemoryEditDecision}
              onClear={clearMessages}
              onHide={() => setChatVisible(false)}
            />
          )}

          {/* Canvas (Right) */}
          <Canvas
            agentId={selectedAgent?.id}
            triggers={selectedAgent?.triggers || []}
            tools={selectedAgent?.tools?.map(t => ({
              name: t.name,
              description: t.name,
              enabled: t.enabled,
              hitl: t.hitl_enabled,
            })) || []}
            agentName={selectedAgent?.name || 'Email Assistant'}
            agentDescription={selectedAgent?.description || 'Organizes and manages your inbox for you'}
            agentInstructions={selectedAgent?.system_prompt || ''}
            subagents={selectedAgent?.subagents || []}
            onToggleTrigger={handleToggleTrigger}
            onToggleHITL={handleToggleHITL}
          />
        </div>
      </div>
    </div>
  );
}

export default App;
