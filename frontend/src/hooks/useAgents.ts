import { useState, useEffect, useCallback } from 'react';
import toast from 'react-hot-toast';
import type { AgentSummary, AgentDetail } from '../types';

const API_BASE = '/api/v1';

export function useAgents() {
  const [agents, setAgents] = useState<AgentSummary[]>([]);
  const [templates, setTemplates] = useState<AgentSummary[]>([]);
  const [selectedAgent, setSelectedAgent] = useState<AgentDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Fetch all agents
  const fetchAgents = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/agents`);
      if (!response.ok) throw new Error('Failed to fetch agents');
      const data = await response.json();
      setAgents(data.filter((a: AgentSummary) => !a.is_template));
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error(message);
    }
  }, []);

  // Fetch templates
  const fetchTemplates = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE}/agents/templates`);
      if (!response.ok) throw new Error('Failed to fetch templates');
      const data = await response.json();
      setTemplates(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    }
  }, []);

  // Get agent details
  const getAgent = useCallback(async (agentId: string): Promise<AgentDetail | null> => {
    try {
      const response = await fetch(`${API_BASE}/agents/${agentId}`);
      if (!response.ok) {
        if (response.status === 404) return null;
        throw new Error('Failed to fetch agent');
      }
      return await response.json();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      return null;
    }
  }, []);

  // Select an agent
  const selectAgent = useCallback(async (agentId: string) => {
    setLoading(true);
    const agent = await getAgent(agentId);
    setSelectedAgent(agent);
    setLoading(false);
  }, [getAgent]);

  // Clone a template
  const cloneTemplate = useCallback(async (templateId: string, newName: string): Promise<string | null> => {
    try {
      const response = await fetch(`${API_BASE}/agents/${templateId}/clone`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ new_name: newName }),
      });
      if (!response.ok) throw new Error('Failed to clone template');
      const data = await response.json();
      await fetchAgents(); // Refresh list
      toast.success(`Created "${newName}" successfully`);
      return data.agent_id;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error(message);
      return null;
    }
  }, [fetchAgents]);

  // Update an agent
  const updateAgent = useCallback(async (agentId: string, updates: Partial<AgentDetail>): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/agents/${agentId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(updates),
      });
      if (!response.ok) throw new Error('Failed to save changes');

      // Refresh the selected agent
      if (selectedAgent?.id === agentId) {
        const updated = await getAgent(agentId);
        setSelectedAgent(updated);
      }
      await fetchAgents();
      toast.success('Changes saved');
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error(message);
      return false;
    }
  }, [fetchAgents, selectedAgent, getAgent]);

  // Delete an agent
  const deleteAgent = useCallback(async (agentId: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/agents/${agentId}`, {
        method: 'DELETE',
      });
      if (!response.ok) throw new Error('Failed to delete agent');
      await fetchAgents();
      if (selectedAgent?.id === agentId) {
        setSelectedAgent(null);
      }
      toast.success('Agent deleted');
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      setError(message);
      toast.error(message);
      return false;
    }
  }, [fetchAgents, selectedAgent]);

  // Toggle HITL for a tool
  const toggleHITL = useCallback(async (agentId: string, toolName: string, enabled: boolean): Promise<boolean> => {
    try {
      // Get current agent to modify tools
      const agent = selectedAgent?.id === agentId ? selectedAgent : await getAgent(agentId);
      if (!agent) throw new Error('Agent not found');

      // Update the tool's hitl_enabled status
      const updatedTools = agent.tools.map(tool =>
        tool.name === toolName ? { ...tool, hitl_enabled: enabled } : tool
      );

      return await updateAgent(agentId, { tools: updatedTools });
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error(message);
      return false;
    }
  }, [selectedAgent, getAgent, updateAgent]);

  // Toggle trigger on/off
  const toggleTrigger = useCallback(async (agentId: string, triggerId: string): Promise<boolean> => {
    try {
      const response = await fetch(`${API_BASE}/triggers/${agentId}/${triggerId}/toggle`, {
        method: 'POST',
      });
      if (!response.ok) throw new Error('Failed to toggle trigger');

      // Refresh agent to get updated trigger state
      if (selectedAgent?.id === agentId) {
        const updated = await getAgent(agentId);
        setSelectedAgent(updated);
      }
      return true;
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error';
      toast.error(message);
      return false;
    }
  }, [selectedAgent, getAgent]);

  // Initial load
  useEffect(() => {
    const load = async () => {
      setLoading(true);
      await Promise.all([fetchAgents(), fetchTemplates()]);
      setLoading(false);
    };
    load();
  }, [fetchAgents, fetchTemplates]);

  return {
    agents,
    templates,
    selectedAgent,
    loading,
    error,
    selectAgent,
    updateAgent,
    cloneTemplate,
    deleteAgent,
    toggleHITL,
    toggleTrigger,
    refreshAgents: fetchAgents,
    refreshTemplates: fetchTemplates,
    clearError: () => setError(null),
  };
}
