import { ReactNode } from 'react';

interface EditorLayoutProps {
  triggersPanel: ReactNode;
  toolboxPanel: ReactNode;
  agentPanel: ReactNode;
  subagentsPanel: ReactNode;
  skillsPanel: ReactNode;
}

export function EditorLayout({
  triggersPanel,
  toolboxPanel,
  agentPanel,
  subagentsPanel,
  skillsPanel,
}: EditorLayoutProps) {
  return (
    <div className="flex-1 p-4 overflow-auto">
      <div className="grid grid-cols-2 gap-4 h-full">
        {/* Left Column */}
        <div className="flex flex-col gap-4">
          {/* Triggers - smaller */}
          <div className="flex-shrink-0">{triggersPanel}</div>
          {/* Agent - takes remaining space */}
          <div className="flex-1 min-h-0">{agentPanel}</div>
        </div>

        {/* Right Column */}
        <div className="flex flex-col gap-4">
          {/* Toolbox */}
          <div className="flex-shrink-0">{toolboxPanel}</div>
          {/* Subagents */}
          <div className="flex-1 min-h-0">{subagentsPanel}</div>
          {/* Skills */}
          <div className="flex-shrink-0">{skillsPanel}</div>
        </div>
      </div>
    </div>
  );
}
