import { Panel } from '../layout/Panel';
import type { Subagent } from '../../types';

interface SubagentsPanelProps {
  subagents: Subagent[];
}

export function SubagentsPanel({ subagents }: SubagentsPanelProps) {
  return (
    <Panel
      title="Sub-agents"
      accent="purple"
      action={
        <button className="text-gray-400 hover:text-white text-xl leading-none">
          +
        </button>
      }
      className="h-full"
    >
      {subagents.length === 0 ? (
        <p className="text-gray-500 text-sm">No sub-agents configured</p>
      ) : (
        <div className="space-y-3">
          {subagents.map((subagent) => (
            <div
              key={subagent.name}
              className="p-3 bg-bg-tertiary rounded-md border-l-2 border-accent-purple"
            >
              <p className="text-sm text-white font-medium">{subagent.name}</p>
              <p className="text-xs text-gray-400 mt-1">{subagent.description}</p>
              <div className="flex flex-wrap gap-1 mt-2">
                {subagent.tools.map((tool) => (
                  <span
                    key={tool}
                    className="px-2 py-0.5 text-xs bg-bg-secondary rounded text-gray-400 font-mono"
                  >
                    {tool}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}
