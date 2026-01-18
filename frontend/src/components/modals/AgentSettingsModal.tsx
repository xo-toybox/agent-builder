import { useState, useEffect, useCallback } from 'react';
import { Modal } from './Modal';
import type { AgentDetail, ModelOption, GlobalSettingsResponse } from '../../types';
import toast from 'react-hot-toast';

interface AgentSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
  agent: AgentDetail | null;
  onAgentUpdate: (agent: AgentDetail) => void;
  onAgentDelete: () => void;
}

export function AgentSettingsModal({
  isOpen,
  onClose,
  agent,
  onAgentUpdate,
  onAgentDelete,
}: AgentSettingsModalProps) {
  const [models, setModels] = useState<ModelOption[]>([]);
  const [globalSettings, setGlobalSettings] = useState<GlobalSettingsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form state
  const [selectedModel, setSelectedModel] = useState('');
  const [memoryApprovalRequired, setMemoryApprovalRequired] = useState(false);
  const [showDeleteConfirm, setShowDeleteConfirm] = useState(false);

  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      const [modelsRes, settingsRes] = await Promise.all([
        fetch('/api/v1/settings/models'),
        fetch('/api/v1/settings'),
      ]);

      if (modelsRes.ok) {
        setModels(await modelsRes.json());
      }

      if (settingsRes.ok) {
        setGlobalSettings(await settingsRes.json());
      }
    } catch (error) {
      console.error('Failed to fetch data:', error);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchData();
      setShowDeleteConfirm(false);
    }
  }, [isOpen, fetchData]);

  useEffect(() => {
    if (agent) {
      setSelectedModel(agent.model);
      setMemoryApprovalRequired(agent.memory_approval_required);
    }
  }, [agent]);

  const handleSave = async () => {
    if (!agent) return;

    try {
      setSaving(true);

      const updates: { model?: string; memory_approval_required?: boolean } = {};

      if (selectedModel !== agent.model) {
        updates.model = selectedModel;
      }

      if (memoryApprovalRequired !== agent.memory_approval_required) {
        updates.memory_approval_required = memoryApprovalRequired;
      }

      if (Object.keys(updates).length === 0) {
        onClose();
        return;
      }

      const response = await fetch(`/api/v1/agents/${agent.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });

      if (response.ok) {
        toast.success('Agent settings saved');
        onAgentUpdate({
          ...agent,
          ...updates,
        });
        onClose();
      } else {
        try {
          const error = await response.json();
          toast.error(error.detail || 'Failed to save settings');
        } catch {
          toast.error(`Failed to save settings (${response.status})`);
        }
      }
    } catch (error) {
      console.error('Failed to save settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleDelete = async () => {
    if (!agent) return;

    try {
      setSaving(true);

      const response = await fetch(`/api/v1/agents/${agent.id}`, {
        method: 'DELETE',
      });

      if (response.ok) {
        toast.success('Agent deleted');
        onAgentDelete();
        onClose();
      } else {
        try {
          const error = await response.json();
          toast.error(error.detail || 'Failed to delete agent');
        } catch {
          toast.error(`Failed to delete agent (${response.status})`);
        }
      }
    } catch (error) {
      console.error('Failed to delete agent:', error);
      toast.error('Failed to delete agent');
    } finally {
      setSaving(false);
    }
  };

  const getModelName = (modelId: string) => {
    const model = models.find((m) => m.id === modelId);
    return model?.name || modelId;
  };

  if (!agent) return null;

  return (
    <Modal isOpen={isOpen} onClose={onClose} title={`${agent.name} Settings`} maxWidth="md">
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin w-6 h-6 border-2 border-accent-orange border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Model Section */}
          <div className="bg-bg-tertiary rounded-lg border border-border p-4">
            <h3 className="text-sm font-semibold text-accent-teal uppercase tracking-wide mb-3">
              Model
            </h3>
            <p className="text-xs text-text-muted mb-3">
              Choose which model this agent uses.
              {globalSettings && (
                <span className="block mt-1">
                  Workspace default: {getModelName(globalSettings.default_model)}
                </span>
              )}
            </p>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full bg-bg-secondary border border-border rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-orange"
            >
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                  {globalSettings?.default_model === model.id && ' (Default)'}
                </option>
              ))}
            </select>
          </div>

          {/* Memory Section */}
          <div className="bg-bg-tertiary rounded-lg border border-border p-4">
            <h3 className="text-sm font-semibold text-accent-purple uppercase tracking-wide mb-3">
              Memory
            </h3>
            <label className="flex items-start gap-3 cursor-pointer">
              <input
                type="checkbox"
                checked={memoryApprovalRequired}
                onChange={(e) => setMemoryApprovalRequired(e.target.checked)}
                className="mt-1 w-4 h-4 rounded border-border text-accent-orange focus:ring-accent-orange"
              />
              <div>
                <p className="text-sm text-text-primary">Require approval to update memories</p>
                <p className="text-xs text-text-muted mt-1">
                  When enabled, you'll be asked to approve before the agent saves information to its
                  memory.
                </p>
              </div>
            </label>
          </div>

          {/* Danger Zone */}
          {!agent.is_template && (
            <div className="bg-bg-tertiary rounded-lg border border-red-500/30 p-4">
              <h3 className="text-sm font-semibold text-red-500 uppercase tracking-wide mb-3">
                Danger Zone
              </h3>

              {!showDeleteConfirm ? (
                <div>
                  <p className="text-xs text-text-muted mb-3">
                    Permanently delete this agent and all its data.
                  </p>
                  <button
                    onClick={() => setShowDeleteConfirm(true)}
                    className="px-4 py-2 text-sm border border-red-500 text-red-500 rounded-md hover:bg-red-500/10 transition-colors"
                  >
                    Delete Agent
                  </button>
                </div>
              ) : (
                <div className="p-3 bg-red-500/10 rounded-md">
                  <p className="text-sm text-red-400 mb-3">
                    Are you sure? This action cannot be undone.
                  </p>
                  <div className="flex gap-2">
                    <button
                      onClick={() => setShowDeleteConfirm(false)}
                      className="px-3 py-1.5 text-sm text-text-secondary hover:text-text-primary hover:bg-bg-tertiary rounded-md transition-colors"
                    >
                      Cancel
                    </button>
                    <button
                      onClick={handleDelete}
                      disabled={saving}
                      className="px-3 py-1.5 text-sm bg-red-500 text-white rounded-md hover:bg-red-600 transition-colors disabled:opacity-50"
                    >
                      {saving ? 'Deleting...' : 'Yes, Delete'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          )}

          {/* Actions */}
          <div className="flex justify-end gap-3 pt-2">
            <button
              onClick={onClose}
              className="px-4 py-2 text-sm text-text-secondary hover:text-text-primary hover:bg-bg-tertiary rounded-md transition-colors"
            >
              Cancel
            </button>
            <button
              onClick={handleSave}
              disabled={saving}
              className="px-4 py-2 text-sm bg-accent-orange text-white rounded-md hover:bg-orange-600 transition-colors disabled:opacity-50"
            >
              {saving ? 'Saving...' : 'Save Changes'}
            </button>
          </div>
        </div>
      )}
    </Modal>
  );
}
