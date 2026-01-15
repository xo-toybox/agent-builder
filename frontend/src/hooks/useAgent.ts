import { useState, useEffect, useCallback } from 'react';
import type { AgentConfig, Tool, Trigger, Subagent } from '../types';

const API_BASE = '';

// Mock data for demo when backend is not running
const MOCK_TOOLS: Tool[] = [
  { name: 'list_emails', description: 'List recent emails from inbox', enabled: true, hitl: false },
  { name: 'get_email', description: 'Get email details by ID', enabled: true, hitl: false },
  { name: 'search_emails', description: 'Search emails by query', enabled: true, hitl: false },
  { name: 'draft_reply', description: 'Draft a reply to an email', enabled: true, hitl: true },
  { name: 'send_email', description: 'Send an email', enabled: true, hitl: true },
  { name: 'label_email', description: 'Apply label to an email', enabled: true, hitl: false },
  { name: 'list_events', description: 'List calendar events', enabled: true, hitl: false },
  { name: 'get_event', description: 'Get event details', enabled: true, hitl: false },
];

const MOCK_TRIGGERS: Trigger[] = [
  { id: 'gmail_polling', type: 'gmail_polling', enabled: false, config: { interval_seconds: 60 } },
];

const MOCK_CONFIG: AgentConfig = {
  name: 'Email Assistant',
  instructions: 'You are an intelligent email assistant that helps process incoming emails, triage them, draft or send appropriate responses, and manage calendar events.',
  tools: MOCK_TOOLS.map(t => t.name),
  hitl_tools: ['draft_reply', 'send_email'],
  subagents: [],
  triggers: MOCK_TRIGGERS,
};

export function useAgent() {
  const [config, setConfig] = useState<AgentConfig | null>(null);
  const [tools, setTools] = useState<Tool[]>([]);
  const [triggers, setTriggers] = useState<Trigger[]>([]);
  const [subagents, setSubagents] = useState<Subagent[]>([]);
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [userEmail, setUserEmail] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  // Check auth status
  const checkAuth = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/auth/status`);
      const data = await res.json();
      setIsAuthenticated(data.authenticated);
      setUserEmail(data.email || null);
    } catch (error) {
      console.error('Auth check failed:', error);
      setIsAuthenticated(false);
      setUserEmail(null);
    }
  }, []);

  // Load agent config
  const loadConfig = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/agent`);
      if (!res.ok) throw new Error('API not available');
      const data = await res.json();
      setConfig(data);
    } catch (error) {
      console.log('Using mock config (backend not running)');
      setConfig(MOCK_CONFIG);
    }
  }, []);

  // Load tools
  const loadTools = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/tools`);
      if (!res.ok) throw new Error('API not available');
      const data = await res.json();
      setTools(data);
    } catch (error) {
      console.log('Using mock tools (backend not running)');
      setTools(MOCK_TOOLS);
    }
  }, []);

  // Load triggers
  const loadTriggers = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/triggers`);
      if (!res.ok) throw new Error('API not available');
      const data = await res.json();
      setTriggers(data);
    } catch (error) {
      console.log('Using mock triggers (backend not running)');
      setTriggers(MOCK_TRIGGERS);
    }
  }, []);

  // Load subagents
  const loadSubagents = useCallback(async () => {
    try {
      const res = await fetch(`${API_BASE}/api/subagents`);
      const data = await res.json();
      setSubagents(data);
    } catch (error) {
      console.error('Failed to load subagents:', error);
    }
  }, []);

  // Initial load
  useEffect(() => {
    const init = async () => {
      setLoading(true);
      await checkAuth();
      await Promise.all([loadConfig(), loadTools(), loadTriggers(), loadSubagents()]);
      setLoading(false);
    };
    init();
  }, [checkAuth, loadConfig, loadTools, loadTriggers, loadSubagents]);

  // Update agent name/instructions
  const updateAgent = useCallback(
    async (updates: { name?: string; instructions?: string }) => {
      try {
        const res = await fetch(`${API_BASE}/api/agent`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates),
        });
        const data = await res.json();
        setConfig(data);
      } catch (error) {
        console.error('Failed to update agent:', error);
      }
    },
    []
  );

  // Toggle HITL for a tool
  const toggleHITL = useCallback(
    async (toolName: string, enabled: boolean) => {
      try {
        await fetch(`${API_BASE}/api/tools/${toolName}/hitl`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ enabled }),
        });
        await loadTools();
      } catch (error) {
        console.error('Failed to toggle HITL:', error);
      }
    },
    [loadTools]
  );

  // Toggle trigger
  const toggleTrigger = useCallback(
    async (triggerId: string) => {
      try {
        await fetch(`${API_BASE}/api/triggers/${triggerId}/toggle`, {
          method: 'POST',
        });
        await loadTriggers();
      } catch (error) {
        console.error('Failed to toggle trigger:', error);
      }
    },
    [loadTriggers]
  );

  // Login
  const login = useCallback(() => {
    window.location.href = `${API_BASE}/auth/login`;
  }, []);

  // Logout
  const logout = useCallback(async () => {
    try {
      await fetch(`${API_BASE}/auth/logout`, { method: 'POST' });
      setIsAuthenticated(false);
      setUserEmail(null);
    } catch (error) {
      console.error('Logout failed:', error);
    }
  }, []);

  return {
    config,
    tools,
    triggers,
    subagents,
    isAuthenticated,
    userEmail,
    loading,
    updateAgent,
    toggleHITL,
    toggleTrigger,
    login,
    logout,
    refresh: () => {
      loadConfig();
      loadTools();
      loadTriggers();
      loadSubagents();
    },
  };
}
