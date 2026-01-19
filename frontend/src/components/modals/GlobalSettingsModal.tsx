import { useState, useEffect, useCallback } from 'react';
import { Modal } from './Modal';
import type { GlobalSettingsResponse, ModelOption } from '../../types';
import toast from 'react-hot-toast';

interface GlobalSettingsModalProps {
  isOpen: boolean;
  onClose: () => void;
}

export function GlobalSettingsModal({ isOpen, onClose }: GlobalSettingsModalProps) {
  const [settings, setSettings] = useState<GlobalSettingsResponse | null>(null);
  const [models, setModels] = useState<ModelOption[]>([]);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // Form state
  const [selectedModel, setSelectedModel] = useState('');
  const [tavilyKey, setTavilyKey] = useState('');
  const [tavilyKeyChanged, setTavilyKeyChanged] = useState(false);

  // Slack status
  const [slackConfigured, setSlackConfigured] = useState(false);

  const fetchSettings = useCallback(async () => {
    try {
      setLoading(true);
      const [settingsRes, modelsRes, slackRes] = await Promise.all([
        fetch('/api/v1/settings'),
        fetch('/api/v1/settings/models'),
        fetch('/api/v1/credentials/slack/status'),
      ]);

      if (settingsRes.ok) {
        const data = await settingsRes.json();
        setSettings(data);
        setSelectedModel(data.default_model);
      }

      if (modelsRes.ok) {
        setModels(await modelsRes.json());
      }

      if (slackRes.ok) {
        const slackData = await slackRes.json();
        setSlackConfigured(slackData.configured);
      }
    } catch (error) {
      console.error('Failed to fetch settings:', error);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (isOpen) {
      fetchSettings();
      // Reset form state
      setTavilyKey('');
      setTavilyKeyChanged(false);
    }
  }, [isOpen, fetchSettings]);

  const handleSave = async () => {
    try {
      setSaving(true);

      const updates: { default_model?: string; tavily_api_key?: string } = {};

      if (selectedModel !== settings?.default_model) {
        updates.default_model = selectedModel;
      }

      if (tavilyKeyChanged) {
        updates.tavily_api_key = tavilyKey;
      }

      if (Object.keys(updates).length === 0) {
        onClose();
        return;
      }

      const response = await fetch('/api/v1/settings', {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });

      if (response.ok) {
        toast.success('Settings saved');
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

  return (
    <Modal isOpen={isOpen} onClose={onClose} title="Workspace Settings" maxWidth="md">
      {loading ? (
        <div className="flex items-center justify-center py-8">
          <div className="animate-spin w-6 h-6 border-2 border-accent-orange border-t-transparent rounded-full" />
        </div>
      ) : (
        <div className="space-y-6">
          {/* Default Model Section */}
          <div className="bg-bg-tertiary rounded-lg border border-border p-4">
            <h3 className="text-sm font-semibold text-accent-purple uppercase tracking-wide mb-3">
              Default Model
            </h3>
            <p className="text-xs text-text-muted mb-3">
              New agents will use this model by default. Individual agents can override this.
            </p>
            <select
              value={selectedModel}
              onChange={(e) => setSelectedModel(e.target.value)}
              className="w-full bg-bg-secondary border border-border rounded-md px-3 py-2 text-sm text-text-primary focus:outline-none focus:ring-2 focus:ring-accent-orange"
            >
              {models.map((model) => (
                <option key={model.id} value={model.id}>
                  {model.name}
                </option>
              ))}
            </select>
          </div>

          {/* API Keys Section */}
          <div className="bg-bg-tertiary rounded-lg border border-border p-4">
            <h3 className="text-sm font-semibold text-accent-teal uppercase tracking-wide mb-3">
              API Keys
            </h3>

            {/* Tavily */}
            <div className="mb-4">
              <label className="block text-sm text-text-secondary mb-1">
                Tavily API Key
                {settings?.tavily_api_key_configured && (
                  <span className="ml-2 text-green-500 text-xs">Configured</span>
                )}
              </label>
              <p className="text-xs text-text-muted mb-2">
                Required for web search. Get a key from{' '}
                <a
                  href="https://tavily.com"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-accent-teal hover:underline"
                >
                  tavily.com
                </a>
              </p>
              <input
                type="password"
                value={tavilyKey}
                onChange={(e) => {
                  setTavilyKey(e.target.value);
                  setTavilyKeyChanged(true);
                }}
                placeholder={settings?.tavily_api_key_preview || 'tvly-...'}
                className="w-full bg-bg-secondary border border-border rounded-md px-3 py-2 text-sm text-text-primary placeholder:text-text-muted focus:outline-none focus:ring-2 focus:ring-accent-orange"
              />
              {settings?.tavily_api_key_configured && !tavilyKeyChanged && (
                <p className="text-xs text-text-muted mt-1">
                  Leave empty to keep current key
                </p>
              )}
            </div>
          </div>

          {/* Connected Integrations Section */}
          <div className="bg-bg-tertiary rounded-lg border border-border p-4">
            <h3 className="text-sm font-semibold text-accent-orange uppercase tracking-wide mb-3">
              Connected Integrations
            </h3>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 bg-[#4A154B] rounded flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52zM6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313zM8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834zM8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312zM18.956 8.834a2.528 2.528 0 0 1 2.522-2.521A2.528 2.528 0 0 1 24 8.834a2.528 2.528 0 0 1-2.522 2.521h-2.522V8.834zM17.688 8.834a2.528 2.528 0 0 1-2.523 2.521 2.527 2.527 0 0 1-2.52-2.521V2.522A2.527 2.527 0 0 1 15.165 0a2.528 2.528 0 0 1 2.523 2.522v6.312zM15.165 18.956a2.528 2.528 0 0 1 2.523 2.522A2.528 2.528 0 0 1 15.165 24a2.527 2.527 0 0 1-2.52-2.522v-2.522h2.52zM15.165 17.688a2.527 2.527 0 0 1-2.52-2.523 2.526 2.526 0 0 1 2.52-2.52h6.313A2.527 2.527 0 0 1 24 15.165a2.528 2.528 0 0 1-2.522 2.523h-6.313z" />
                  </svg>
                </div>
                <div>
                  <p className="text-sm text-text-primary">Slack</p>
                  <p className="text-xs text-text-muted">
                    {slackConfigured ? 'Connected' : 'Not configured'}
                  </p>
                </div>
              </div>
              <div
                className={`w-3 h-3 rounded-full ${
                  slackConfigured ? 'bg-green-500' : 'bg-text-muted'
                }`}
              />
            </div>
            <p className="text-xs text-text-muted mt-3">
              Configure Slack in the agent editor's Slack panel.
            </p>
          </div>

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
