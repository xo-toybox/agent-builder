import type { Tool, Trigger, Subagent } from '../../types';
import { SkillsPanel } from '../panels/SkillsPanel';
import { SlackConfigPanel } from '../panels/SlackConfigPanel';

interface CanvasProps {
  agentId?: string; // v0.0.3: Required for skills
  triggers: Trigger[];
  tools: Tool[];
  agentName: string;
  agentDescription: string;
  agentInstructions: string;
  subagents: Subagent[];
  onToggleTrigger: (triggerId: string) => void;
  onToggleHITL: (toolName: string, enabled: boolean) => void;
}

export function Canvas({
  agentId,
  triggers,
  tools,
  agentName,
  agentDescription,
  agentInstructions,
  subagents,
  onToggleTrigger,
  onToggleHITL,
}: CanvasProps) {
  return (
    <div className="flex-1 bg-bg-canvas overflow-auto p-6">
      <div className="flex gap-6 min-w-max">
        {/* Left Column - Triggers */}
        <div className="flex flex-col justify-start pt-4">
          <TriggersCard triggers={triggers} onToggle={onToggleTrigger} />
        </div>

        {/* Center Column - Agent */}
        <div className="flex flex-col justify-center">
          <AgentCard
            name={agentName}
            description={agentDescription}
            instructions={agentInstructions}
          />
        </div>

        {/* Right Column - Toolbox, Sub-agents, Skills, Integrations */}
        <div className="flex flex-col gap-4">
          <ToolboxCard tools={tools} onToggleHITL={onToggleHITL} />
          <SubagentsCard subagents={subagents} />
          {/* v0.0.3: Use SkillsPanel with API integration */}
          {agentId ? (
            <div className="w-56">
              <SkillsPanel agentId={agentId} />
            </div>
          ) : (
            <SkillsCard />
          )}
          {/* v0.0.3: Slack Integration */}
          <div className="w-56">
            <SlackConfigPanel />
          </div>
        </div>
      </div>
    </div>
  );
}

// Triggers Card
function TriggersCard({ triggers, onToggle }: { triggers: Trigger[]; onToggle: (id: string) => void }) {
  const gmailTrigger = triggers.find(t => t.type === 'gmail_polling');

  return (
    <div className="w-64 bg-bg-secondary rounded-lg border border-border shadow-sm border-l-4 border-l-accent-orange">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-sm font-semibold text-text-primary">TRIGGERS</span>
        <button className="text-sm text-text-secondary hover:text-text-primary">+ Add</button>
      </div>
      <div className="p-3 space-y-2">
        {/* Schedule */}
        <div className="flex items-center justify-between p-2 hover:bg-bg-tertiary rounded-md">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <span className="text-sm text-text-primary">Schedule</span>
            <svg className="w-4 h-4 text-text-muted" fill="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2"/>
              <text x="12" y="16" textAnchor="middle" fontSize="12" fill="currentColor">?</text>
            </svg>
          </div>
          <span className="text-sm text-text-muted">None</span>
        </div>

        {/* Slack */}
        <div className="flex items-center justify-between p-2 hover:bg-bg-tertiary rounded-md">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#E01E5A" d="M5.042 15.165a2.528 2.528 0 0 1-2.52 2.523A2.528 2.528 0 0 1 0 15.165a2.527 2.527 0 0 1 2.522-2.52h2.52v2.52z"/>
              <path fill="#36C5F0" d="M6.313 15.165a2.527 2.527 0 0 1 2.521-2.52 2.527 2.527 0 0 1 2.521 2.52v6.313A2.528 2.528 0 0 1 8.834 24a2.528 2.528 0 0 1-2.521-2.522v-6.313z"/>
              <path fill="#2EB67D" d="M8.834 5.042a2.528 2.528 0 0 1-2.521-2.52A2.528 2.528 0 0 1 8.834 0a2.528 2.528 0 0 1 2.521 2.522v2.52H8.834z"/>
              <path fill="#ECB22E" d="M8.834 6.313a2.528 2.528 0 0 1 2.521 2.521 2.528 2.528 0 0 1-2.521 2.521H2.522A2.528 2.528 0 0 1 0 8.834a2.528 2.528 0 0 1 2.522-2.521h6.312z"/>
            </svg>
            <span className="text-sm text-text-primary">Slack</span>
            <svg className="w-4 h-4 text-text-muted" fill="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2"/>
              <text x="12" y="16" textAnchor="middle" fontSize="12" fill="currentColor">?</text>
            </svg>
          </div>
          <span className="text-sm text-text-muted">None</span>
        </div>

        {/* Gmail */}
        <div className="flex items-center justify-between p-2 hover:bg-bg-tertiary rounded-md">
          <div className="flex items-center gap-2">
            <svg className="w-5 h-5" viewBox="0 0 24 24">
              <path fill="#EA4335" d="M24 5.457v13.909c0 .904-.732 1.636-1.636 1.636h-3.819V11.73L12 16.64l-6.545-4.91v9.273H1.636A1.636 1.636 0 0 1 0 19.366V5.457c0-2.023 2.309-3.178 3.927-1.964L5.455 4.64 12 9.548l6.545-4.91 1.528-1.145C21.69 2.28 24 3.434 24 5.457z"/>
            </svg>
            <span className="text-sm text-text-primary">Gmail</span>
            <svg className="w-4 h-4 text-text-muted" fill="currentColor" viewBox="0 0 24 24">
              <circle cx="12" cy="12" r="10" fill="none" stroke="currentColor" strokeWidth="2"/>
              <text x="12" y="16" textAnchor="middle" fontSize="12" fill="currentColor">?</text>
            </svg>
          </div>
          <div className="flex items-center gap-1">
            <span className="text-sm text-text-muted">None</span>
            <svg className="w-4 h-4 text-text-muted" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
            </svg>
          </div>
        </div>

        {/* Connect Gmail account */}
        <button className="w-full flex items-center gap-2 p-2 text-sm text-accent-teal hover:bg-bg-tertiary rounded-md">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
          </svg>
          Connect Gmail account
        </button>

        <p className="text-xs text-text-muted px-2">No registrations yet</p>

        {/* Gmail Polling Toggle (if exists) */}
        {gmailTrigger && (
          <div className="flex items-center justify-between p-2 bg-bg-tertiary rounded-md mt-2">
            <span className="text-sm text-text-primary">Polling</span>
            <button
              onClick={() => onToggle(gmailTrigger.id)}
              className={`text-xs px-2 py-0.5 rounded ${
                gmailTrigger.enabled ? 'bg-accent-green/20 text-accent-green' : 'bg-border text-text-muted'
              }`}
            >
              {gmailTrigger.enabled ? 'ON' : 'OFF'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}

// Toolbox Card
function ToolboxCard({ tools, onToggleHITL }: { tools: Tool[]; onToggleHITL: (name: string, enabled: boolean) => void }) {
  const getToolIcon = (name: string) => {
    if (name.includes('email') || name.includes('gmail') || name.startsWith('list_') || name.startsWith('get_') || name.startsWith('search_') || name.startsWith('draft_') || name.startsWith('send_') || name.startsWith('label_')) {
      return (
        <svg className="w-5 h-5 text-red-500" viewBox="0 0 24 24" fill="currentColor">
          <path d="M20 4H4c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/>
        </svg>
      );
    }
    if (name.includes('event') || name.includes('calendar')) {
      return (
        <svg className="w-5 h-5 text-blue-500" viewBox="0 0 24 24" fill="currentColor">
          <path d="M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11z"/>
        </svg>
      );
    }
    return (
      <svg className="w-5 h-5 text-gray-500" viewBox="0 0 24 24" fill="currentColor">
        <path d="M22.7 19l-9.1-9.1c.9-2.3.4-5-1.5-6.9-2-2-5-2.4-7.4-1.3L9 6 6 9 1.6 4.7C.4 7.1.9 10.1 2.9 12.1c1.9 1.9 4.6 2.4 6.9 1.5l9.1 9.1c.4.4 1 .4 1.4 0l2.3-2.3c.5-.4.5-1.1.1-1.4z"/>
      </svg>
    );
  };

  return (
    <div className="w-72 bg-bg-secondary rounded-lg border border-border shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-sm font-semibold text-text-primary">TOOLBOX</span>
        <div className="flex items-center gap-2">
          <button className="text-sm text-text-secondary hover:text-text-primary">+ Add</button>
          <button className="text-sm text-accent-teal flex items-center gap-1">
            <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
              <circle cx="12" cy="12" r="10" />
            </svg>
            MCP
          </button>
        </div>
      </div>
      <div className="p-2 max-h-80 overflow-y-auto">
        {tools.map((tool) => (
          <div key={tool.name} className="flex items-center justify-between px-2 py-2 hover:bg-bg-tertiary rounded-md group">
            <div className="flex items-center gap-3">
              {getToolIcon(tool.name)}
              <div>
                <p className="text-sm text-text-primary">{formatToolName(tool.name)}</p>
                <p className="text-xs text-text-muted">Agent Builder</p>
              </div>
            </div>
            <div className="flex items-center gap-1">
              {tool.hitl && (
                <span className="flex items-center gap-1 px-2 py-0.5 text-xs bg-accent-orange/10 text-accent-orange rounded">
                  <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-2h2v2zm0-4h-2V7h2v6z"/>
                  </svg>
                  Review Required
                  <button
                    onClick={() => onToggleHITL(tool.name, false)}
                    className="ml-1 hover:bg-accent-orange/20 rounded"
                  >
                    <svg className="w-3 h-3" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
                    </svg>
                  </button>
                </span>
              )}
              <button className="p-1 text-text-muted hover:text-text-secondary opacity-0 group-hover:opacity-100">
                <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                </svg>
              </button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

function formatToolName(name: string): string {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ');
}

// Agent Card
function AgentCard({ name, description, instructions }: { name: string; description: string; instructions: string }) {
  const previewText = instructions.slice(0, 150) + (instructions.length > 150 ? '...' : '');

  return (
    <div className="w-80 bg-bg-secondary rounded-lg border border-border shadow-sm">
      <div className="px-4 py-3 border-b border-border">
        <span className="text-xs font-semibold text-text-muted uppercase">AGENT</span>
      </div>
      <div className="p-4">
        <h3 className="text-lg font-semibold text-text-primary">{name}</h3>
        <p className="text-sm text-text-secondary mt-1">{description}</p>

        <div className="mt-4">
          <div className="flex items-center justify-between mb-2">
            <span className="text-xs font-semibold text-text-muted uppercase">INSTRUCTIONS</span>
            <button className="text-sm text-text-secondary hover:text-text-primary flex items-center gap-1">
              <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
              </svg>
              Edit
            </button>
          </div>
          <div className="bg-bg-tertiary rounded-md p-3">
            <p className="text-sm font-medium text-text-primary">{name}</p>
            <p className="text-sm text-text-secondary mt-1">
              {previewText || 'You are an intelligent email assistant that helps process incoming emails, triage them, draft or send appropriate responses, and...'}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

// Subagents Card
function SubagentsCard({ subagents }: { subagents: Subagent[] }) {
  return (
    <div className="w-56 bg-bg-secondary rounded-lg border border-border shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-sm font-semibold text-text-primary">SUB-AGENTS</span>
        <button className="text-sm text-text-secondary hover:text-text-primary">+ Add</button>
      </div>
      <div className="p-3">
        {subagents.length === 0 ? (
          <p className="text-sm text-text-muted">No sub-agents configured</p>
        ) : (
          <div className="space-y-2">
            {subagents.map((subagent) => (
              <div key={subagent.name} className="flex items-center justify-between p-2 bg-bg-tertiary rounded-md">
                <span className="text-sm text-text-primary">{subagent.name}</span>
                <div className="flex items-center gap-1">
                  <button className="p-1 text-text-muted hover:text-text-secondary">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                      <path d="M11 4H4a2 2 0 00-2 2v14a2 2 0 002 2h14a2 2 0 002-2v-7" />
                      <path d="M18.5 2.5a2.121 2.121 0 013 3L12 15l-4 1 1-4 9.5-9.5z" />
                    </svg>
                  </button>
                  <button className="p-1 text-text-muted hover:text-text-secondary">
                    <svg className="w-4 h-4" viewBox="0 0 24 24" fill="currentColor">
                      <path d="M6 19c0 1.1.9 2 2 2h8c1.1 0 2-.9 2-2V7H6v12zM19 4h-3.5l-1-1h-5l-1 1H5v2h14V4z"/>
                    </svg>
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

// Skills Card
function SkillsCard() {
  return (
    <div className="w-56 bg-bg-secondary rounded-lg border border-border shadow-sm">
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <span className="text-sm font-semibold text-text-primary">SKILLS</span>
        <button className="text-sm text-text-secondary hover:text-text-primary">+ Add</button>
      </div>
      <div className="p-4">
        <p className="text-sm text-text-muted">No skills configured</p>
      </div>
    </div>
  );
}
