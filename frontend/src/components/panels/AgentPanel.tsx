import { useState, useEffect } from 'react';
import { Panel } from '../layout/Panel';

interface AgentPanelProps {
  name: string;
  instructions: string;
  onUpdate: (updates: { name?: string; instructions?: string }) => void;
}

export function AgentPanel({ name, instructions, onUpdate }: AgentPanelProps) {
  const [localName, setLocalName] = useState(name);
  const [localInstructions, setLocalInstructions] = useState(instructions);

  // Sync with props
  useEffect(() => {
    setLocalName(name);
  }, [name]);

  useEffect(() => {
    setLocalInstructions(instructions);
  }, [instructions]);

  const handleNameBlur = () => {
    if (localName !== name) {
      onUpdate({ name: localName });
    }
  };

  const handleInstructionsBlur = () => {
    if (localInstructions !== instructions) {
      onUpdate({ instructions: localInstructions });
    }
  };

  return (
    <Panel title="Agent" accent="teal" className="h-full flex flex-col">
      <div className="flex flex-col gap-4 flex-1">
        <div>
          <label className="block text-xs text-gray-400 mb-1">Name</label>
          <input
            type="text"
            value={localName}
            onChange={(e) => setLocalName(e.target.value)}
            onBlur={handleNameBlur}
            className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-md text-white text-sm focus:border-accent-teal focus:outline-none"
          />
        </div>

        <div className="flex-1 flex flex-col min-h-0">
          <label className="block text-xs text-gray-400 mb-1">Instructions</label>
          <textarea
            value={localInstructions}
            onChange={(e) => setLocalInstructions(e.target.value)}
            onBlur={handleInstructionsBlur}
            placeholder="Enter agent instructions..."
            className="flex-1 w-full px-3 py-2 bg-bg-tertiary border border-border rounded-md text-white text-sm focus:border-accent-teal focus:outline-none resize-none font-mono"
          />
        </div>
      </div>
    </Panel>
  );
}
