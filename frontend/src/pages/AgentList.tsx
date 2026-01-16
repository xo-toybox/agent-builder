import { useState } from 'react';
import type { AgentSummary } from '../types';

interface AgentListProps {
  agents: AgentSummary[];
  templates: AgentSummary[];
  onSelectAgent: (agentId: string) => void;
  onCloneTemplate: (templateId: string, newName: string) => Promise<string | null>;
  onDeleteAgent: (agentId: string) => Promise<boolean>;
  onCreateNew: () => void;
}

export function AgentList({
  agents,
  templates,
  onSelectAgent,
  onCloneTemplate,
  onDeleteAgent,
  onCreateNew,
}: AgentListProps) {
  const [cloneDialogOpen, setCloneDialogOpen] = useState(false);
  const [selectedTemplate, setSelectedTemplate] = useState<AgentSummary | null>(null);
  const [newName, setNewName] = useState('');
  const [isCloning, setIsCloning] = useState(false);

  const handleClone = async () => {
    if (!selectedTemplate || !newName.trim()) return;

    setIsCloning(true);
    try {
      const newId = await onCloneTemplate(selectedTemplate.id, newName.trim());
      if (newId) {
        setCloneDialogOpen(false);
        setNewName('');
        setSelectedTemplate(null);
        onSelectAgent(newId);
      }
    } finally {
      setIsCloning(false);
    }
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-8">
        <h1 className="text-2xl font-semibold text-text-primary">Agent Builder</h1>
        <button
          onClick={onCreateNew}
          className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary transition-colors"
        >
          Create New Agent
        </button>
      </div>

      {/* Templates Section */}
      <section className="mb-8">
        <h2 className="text-lg font-medium text-text-primary mb-4">Templates</h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {templates.map((template) => (
            <div
              key={template.id}
              className="p-4 bg-bg-secondary rounded-lg border border-border-primary hover:border-accent-primary transition-colors cursor-pointer"
              onClick={() => {
                setSelectedTemplate(template);
                setNewName(`${template.name} Copy`);
                setCloneDialogOpen(true);
              }}
            >
              <div className="flex items-start justify-between">
                <div>
                  <h3 className="font-medium text-text-primary">{template.name}</h3>
                  <p className="text-sm text-text-secondary mt-1">{template.description}</p>
                </div>
                <span className="text-xs px-2 py-1 bg-accent-primary/20 text-accent-primary rounded">
                  Template
                </span>
              </div>
              <div className="mt-3">
                <span className="text-xs text-text-secondary">Click to clone</span>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* My Agents Section */}
      <section>
        <h2 className="text-lg font-medium text-text-primary mb-4">My Agents</h2>
        {agents.length === 0 ? (
          <div className="p-8 bg-bg-secondary rounded-lg border border-border-primary text-center">
            <p className="text-text-secondary">No agents yet. Create one or clone a template to get started.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {agents.map((agent) => (
              <div
                key={agent.id}
                className="p-4 bg-bg-secondary rounded-lg border border-border-primary hover:border-accent-primary transition-colors cursor-pointer group"
                onClick={() => onSelectAgent(agent.id)}
              >
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <h3 className="font-medium text-text-primary">{agent.name}</h3>
                    <p className="text-sm text-text-secondary mt-1">
                      {agent.description || 'No description'}
                    </p>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (confirm(`Delete "${agent.name}"?`)) {
                        onDeleteAgent(agent.id);
                      }
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-text-secondary hover:text-red-500 transition-opacity"
                  >
                    <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>

      {/* Clone Dialog */}
      {cloneDialogOpen && selectedTemplate && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50">
          <div className="bg-bg-secondary rounded-lg p-6 w-full max-w-md">
            <h2 className="text-lg font-medium text-text-primary mb-4">
              Clone "{selectedTemplate.name}"
            </h2>
            <input
              type="text"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              placeholder="Agent name"
              className="w-full px-3 py-2 bg-bg-primary border border-border-primary rounded-lg text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-primary"
              autoFocus
            />
            <div className="flex justify-end gap-3 mt-4">
              <button
                onClick={() => {
                  setCloneDialogOpen(false);
                  setSelectedTemplate(null);
                  setNewName('');
                }}
                className="px-4 py-2 text-text-secondary hover:text-text-primary transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={handleClone}
                disabled={!newName.trim() || isCloning}
                className="px-4 py-2 bg-accent-primary text-white rounded-lg hover:bg-accent-secondary transition-colors disabled:opacity-50"
              >
                {isCloning ? 'Cloning...' : 'Clone'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
