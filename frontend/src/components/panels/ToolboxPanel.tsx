import { Panel } from '../layout/Panel';
import type { Tool } from '../../types';

interface ToolboxPanelProps {
  tools: Tool[];
  onToggleHITL: (toolName: string, enabled: boolean) => void;
}

export function ToolboxPanel({ tools, onToggleHITL }: ToolboxPanelProps) {
  return (
    <Panel
      title="Toolbox"
      accent="teal"
      action={
        <button className="text-xs text-gray-400 hover:text-white px-2 py-1 bg-bg-tertiary rounded">
          + MCP
        </button>
      }
    >
      <div className="space-y-1">
        {tools.map((tool) => (
          <div
            key={tool.name}
            className="flex items-center justify-between py-2 px-3 rounded-md hover:bg-bg-tertiary transition-colors"
          >
            <div className="flex items-center gap-3">
              <input
                type="checkbox"
                checked={tool.enabled}
                readOnly
                className="w-4 h-4 rounded border-gray-600 bg-bg-tertiary text-accent-teal focus:ring-accent-teal"
              />
              <div>
                <p className="text-sm text-white font-mono">{tool.name}</p>
                <p className="text-xs text-gray-500">{tool.description}</p>
              </div>
            </div>
            {tool.hitl ? (
              <button
                onClick={() => onToggleHITL(tool.name, false)}
                className="px-2 py-0.5 text-xs rounded bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500/30 transition-colors"
              >
                HITL
              </button>
            ) : (
              <button
                onClick={() => onToggleHITL(tool.name, true)}
                className="px-2 py-0.5 text-xs rounded bg-gray-700 text-gray-400 hover:bg-gray-600 transition-colors opacity-0 group-hover:opacity-100"
              >
                + HITL
              </button>
            )}
          </div>
        ))}
      </div>
    </Panel>
  );
}
