/**
 * v0.0.3: Skills Panel Component
 *
 * Displays and manages agent skills with create/delete functionality.
 */

import { useState, useEffect, useCallback } from 'react';
import { Panel } from '../layout/Panel';
import type { Skill, SkillCreate } from '../../types';

interface SkillsPanelProps {
  agentId: string;
}

export function SkillsPanel({ agentId }: SkillsPanelProps) {
  const [skills, setSkills] = useState<Skill[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [expandedSkillId, setExpandedSkillId] = useState<string | null>(null);

  const fetchSkills = useCallback(async () => {
    try {
      setError(null);
      const response = await fetch(`/api/v1/agents/${agentId}/skills`);
      if (!response.ok) {
        throw new Error('Failed to fetch skills');
      }
      const data = await response.json();
      setSkills(data.skills || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load skills');
    } finally {
      setLoading(false);
    }
  }, [agentId]);

  useEffect(() => {
    fetchSkills();
  }, [fetchSkills]);

  const handleCreateSkill = async (skill: SkillCreate) => {
    try {
      const response = await fetch(`/api/v1/agents/${agentId}/skills`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(skill),
      });

      if (!response.ok) {
        const data = await response.json();
        throw new Error(data.detail || 'Failed to create skill');
      }

      setShowCreateForm(false);
      await fetchSkills();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to create skill');
    }
  };

  const handleDeleteSkill = async (skillId: string) => {
    if (!confirm('Are you sure you want to delete this skill?')) return;

    try {
      const response = await fetch(`/api/v1/agents/${agentId}/skills/${skillId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete skill');
      }

      await fetchSkills();
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to delete skill');
    }
  };

  return (
    <Panel
      title="Skills"
      accent="blue"
      action={
        <button
          onClick={() => setShowCreateForm(true)}
          className="text-text-muted hover:text-accent-blue text-xl leading-none"
        >
          +
        </button>
      }
    >
      {error && (
        <div className="bg-accent-red/10 border border-accent-red/30 rounded-md p-2 mb-3">
          <p className="text-accent-red text-xs">{error}</p>
        </div>
      )}

      {showCreateForm && (
        <CreateSkillForm
          onSubmit={handleCreateSkill}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {loading ? (
        <div className="text-center py-4">
          <p className="text-text-muted text-sm">Loading skills...</p>
        </div>
      ) : skills.length === 0 ? (
        <div className="text-center py-4">
          <p className="text-text-muted text-sm">No skills configured</p>
          <p className="text-text-muted text-xs mt-1">Click + to add a skill</p>
        </div>
      ) : (
        <div className="space-y-2">
          {skills.map((skill) => (
            <SkillItem
              key={skill.id}
              skill={skill}
              expanded={expandedSkillId === skill.id}
              onToggle={() => setExpandedSkillId(
                expandedSkillId === skill.id ? null : skill.id
              )}
              onDelete={() => handleDeleteSkill(skill.id)}
            />
          ))}
        </div>
      )}
    </Panel>
  );
}

interface SkillItemProps {
  skill: Skill;
  expanded: boolean;
  onToggle: () => void;
  onDelete: () => void;
}

function SkillItem({ skill, expanded, onToggle, onDelete }: SkillItemProps) {
  return (
    <div className="bg-bg-tertiary rounded-md overflow-hidden">
      <div
        className="flex items-center justify-between p-2 cursor-pointer hover:bg-bg-secondary"
        onClick={onToggle}
      >
        <div className="flex items-center gap-2">
          <svg
            className={`w-4 h-4 text-text-muted transition-transform ${expanded ? 'rotate-90' : ''}`}
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
          </svg>
          <span className="text-sm text-text-primary font-medium">{skill.name}</span>
        </div>
        <button
          onClick={(e) => {
            e.stopPropagation();
            onDelete();
          }}
          className="p-1 text-text-muted hover:text-accent-red rounded"
        >
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
          </svg>
        </button>
      </div>

      {expanded && (
        <div className="p-3 border-t border-border">
          <p className="text-xs text-text-muted mb-2">{skill.description}</p>
          <div className="bg-bg-secondary rounded p-2">
            <p className="text-xs text-text-muted mb-1">Instructions:</p>
            <pre className="text-xs text-text-secondary whitespace-pre-wrap">{skill.instructions}</pre>
          </div>
        </div>
      )}
    </div>
  );
}

interface CreateSkillFormProps {
  onSubmit: (skill: SkillCreate) => void;
  onCancel: () => void;
}

function CreateSkillForm({ onSubmit, onCancel }: CreateSkillFormProps) {
  const [name, setName] = useState('');
  const [description, setDescription] = useState('');
  const [instructions, setInstructions] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!name.trim() || !instructions.trim()) return;
    onSubmit({
      name: name.trim(),
      description: description.trim(),
      instructions: instructions.trim(),
    });
  };

  return (
    <form onSubmit={handleSubmit} className="mb-3 bg-bg-tertiary rounded-md p-3">
      <div className="space-y-2">
        <div>
          <label className="block text-xs text-text-muted mb-1">Name</label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            placeholder="e.g., Email Triage"
            className="w-full px-2 py-1.5 bg-bg-secondary border border-border rounded text-sm text-text-primary focus:border-accent-blue focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-text-muted mb-1">Description</label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            placeholder="Brief description of the skill"
            className="w-full px-2 py-1.5 bg-bg-secondary border border-border rounded text-sm text-text-primary focus:border-accent-blue focus:outline-none"
          />
        </div>
        <div>
          <label className="block text-xs text-text-muted mb-1">Instructions</label>
          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder="Detailed instructions for when to apply this skill..."
            rows={4}
            className="w-full px-2 py-1.5 bg-bg-secondary border border-border rounded text-sm text-text-primary focus:border-accent-blue focus:outline-none resize-y"
          />
        </div>
      </div>
      <div className="flex gap-2 mt-3">
        <button
          type="submit"
          disabled={!name.trim() || !instructions.trim()}
          className="px-3 py-1.5 bg-accent-blue text-white text-xs rounded font-medium hover:bg-blue-600 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          Create
        </button>
        <button
          type="button"
          onClick={onCancel}
          className="px-3 py-1.5 bg-bg-secondary text-text-secondary text-xs rounded hover:bg-border"
        >
          Cancel
        </button>
      </div>
    </form>
  );
}
