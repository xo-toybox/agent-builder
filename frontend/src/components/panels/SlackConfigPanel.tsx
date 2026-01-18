/**
 * v0.0.3: Slack Configuration Panel
 *
 * Allows users to configure Slack bot token for agent integrations.
 */

import { useState, useEffect, useCallback } from 'react';
import { Panel } from '../layout/Panel';

interface SlackConfigPanelProps {
  onConfigured?: () => void;
}

export function SlackConfigPanel({ onConfigured }: SlackConfigPanelProps) {
  const [isConfigured, setIsConfigured] = useState(false);
  const [loading, setLoading] = useState(true);
  const [showTokenInput, setShowTokenInput] = useState(false);
  const [token, setToken] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const checkStatus = useCallback(async () => {
    try {
      const response = await fetch('/api/v1/credentials/slack/status');
      if (response.ok) {
        const data = await response.json();
        setIsConfigured(data.configured);
      }
    } catch (err) {
      console.error('Failed to check Slack status:', err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkStatus();
  }, [checkStatus]);

  const handleSaveToken = async () => {
    if (!token.trim()) return;

    setError(null);
    setSaving(true);

    try {
      const response = await fetch('/api/v1/credentials/slack', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ token: token.trim() }),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to save Slack token');
      }

      setIsConfigured(true);
      setShowTokenInput(false);
      setToken('');
      onConfigured?.();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save token');
    } finally {
      setSaving(false);
    }
  };

  const handleRemoveToken = async () => {
    if (!confirm('Are you sure you want to remove the Slack configuration?')) return;

    try {
      await fetch('/api/v1/credentials/slack', { method: 'DELETE' });
      setIsConfigured(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to remove token');
    }
  };

  return (
    <Panel
      title="Slack"
      accent="purple"
      action={
        isConfigured ? (
          <button
            onClick={handleRemoveToken}
            className="text-text-muted hover:text-accent-red text-xs"
          >
            Remove
          </button>
        ) : (
          <button
            onClick={() => setShowTokenInput(true)}
            className="text-text-muted hover:text-accent-purple text-xl leading-none"
          >
            +
          </button>
        )
      }
    >
      {loading ? (
        <div className="text-center py-4">
          <p className="text-text-muted text-sm">Checking status...</p>
        </div>
      ) : isConfigured ? (
        <div className="py-2">
          <div className="flex items-center gap-2 text-accent-green">
            <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 24 24">
              <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41L9 16.17z"/>
            </svg>
            <span className="text-sm font-medium">Connected</span>
          </div>
          <p className="text-xs text-text-muted mt-1">
            Slack bot token is configured. Agent can send messages.
          </p>
        </div>
      ) : showTokenInput ? (
        <div className="space-y-3">
          <div>
            <label className="block text-xs text-text-muted mb-1">
              Bot User OAuth Token
            </label>
            <input
              type="password"
              value={token}
              onChange={(e) => setToken(e.target.value)}
              placeholder="xoxb-..."
              className="w-full px-2 py-1.5 bg-bg-secondary border border-border rounded text-sm text-text-primary focus:border-accent-purple focus:outline-none font-mono"
            />
          </div>

          {error && (
            <p className="text-accent-red text-xs">{error}</p>
          )}

          <div className="text-xs text-text-muted">
            <p className="mb-1">To get a Slack bot token:</p>
            <ol className="list-decimal list-inside space-y-0.5 text-text-muted">
              <li>Create a Slack app at api.slack.com</li>
              <li>Add bot scopes: chat:write, channels:read</li>
              <li>Install to your workspace</li>
              <li>Copy the Bot User OAuth Token</li>
            </ol>
          </div>

          <div className="flex gap-2">
            <button
              onClick={handleSaveToken}
              disabled={!token.trim() || saving}
              className="px-3 py-1.5 bg-accent-purple text-white text-xs rounded font-medium hover:bg-purple-600 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {saving ? 'Saving...' : 'Save Token'}
            </button>
            <button
              onClick={() => {
                setShowTokenInput(false);
                setToken('');
                setError(null);
              }}
              className="px-3 py-1.5 bg-bg-secondary text-text-secondary text-xs rounded hover:bg-border"
            >
              Cancel
            </button>
          </div>
        </div>
      ) : (
        <div className="text-center py-4">
          <p className="text-text-muted text-sm">Not configured</p>
          <p className="text-text-muted text-xs mt-1">
            Add a Slack bot token to enable messaging
          </p>
        </div>
      )}
    </Panel>
  );
}
