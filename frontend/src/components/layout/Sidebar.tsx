import type { AgentSummary } from '../../types';

interface SidebarProps {
  isAuthenticated: boolean;
  userEmail: string | null;
  onLogin: () => void;
  onLogout: () => void;
  agents?: AgentSummary[];
  selectedAgentId?: string | null;
  onSelectAgent?: (id: string) => void;
  onNavigate?: (view: 'list' | 'builder') => void;
}

export function Sidebar({
  isAuthenticated,
  userEmail,
  onLogin,
  onLogout,
  agents = [],
  selectedAgentId,
  onSelectAgent,
  onNavigate,
}: SidebarProps) {
  // Filter out templates from agents list
  const myAgents = agents.filter(a => !a.is_template);

  return (
    <div className="w-52 bg-bg-secondary border-r border-border flex flex-col">
      {/* Logo */}
      <div
        className="p-4 border-b border-border flex items-center gap-2 cursor-pointer hover:bg-bg-tertiary"
        onClick={() => onNavigate?.('list')}
      >
        <div className="w-6 h-6 bg-text-primary rounded flex items-center justify-center">
          <span className="text-white text-xs font-bold">A</span>
        </div>
        <span className="font-semibold text-text-primary">Agent Builder</span>
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 overflow-y-auto">
        <div className="mb-4">
          <button
            onClick={() => onNavigate?.('list')}
            className="w-full flex items-center gap-2 px-3 py-2 text-text-secondary hover:bg-bg-tertiary rounded-md text-left"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Feed
          </button>
        </div>

        <div className="mb-2">
          <div className="flex items-center justify-between px-3 py-1">
            <span className="text-xs font-medium text-text-secondary uppercase">My Agents</span>
            <button
              onClick={() => onNavigate?.('builder')}
              className="text-text-muted hover:text-text-primary text-lg"
              title="Create new agent"
            >
              +
            </button>
          </div>

          {myAgents.length === 0 ? (
            <div className="px-3 py-2 text-xs text-text-muted">
              No agents yet
            </div>
          ) : (
            myAgents.map(agent => {
              const initials = agent.name.split(' ').map(w => w[0]).join('').slice(0, 2).toUpperCase();
              const isSelected = selectedAgentId === agent.id;

              return (
                <button
                  key={agent.id}
                  onClick={() => onSelectAgent?.(agent.id)}
                  className={`w-full flex items-center gap-2 px-3 py-2 rounded-md text-left ${
                    isSelected
                      ? 'text-text-primary bg-accent-orange/10'
                      : 'text-text-secondary hover:bg-bg-tertiary'
                  }`}
                >
                  <div className={`w-5 h-5 rounded flex items-center justify-center flex-shrink-0 ${
                    isSelected ? 'bg-accent-orange' : 'bg-text-muted'
                  }`}>
                    <span className="text-white text-xs font-bold">{initials}</span>
                  </div>
                  <span className="truncate text-sm">{agent.name}</span>
                </button>
              );
            })
          )}
        </div>

        <div className="mb-4">
          <div className="px-3 py-1">
            <span className="text-xs font-medium text-text-secondary uppercase">Explore</span>
          </div>
          <button
            onClick={() => onNavigate?.('list')}
            className="w-full flex items-center gap-2 px-3 py-2 text-text-secondary hover:bg-bg-tertiary rounded-md text-left"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 5a1 1 0 011-1h14a1 1 0 011 1v2a1 1 0 01-1 1H5a1 1 0 01-1-1V5zM4 13a1 1 0 011-1h6a1 1 0 011 1v6a1 1 0 01-1 1H5a1 1 0 01-1-1v-6zM16 13a1 1 0 011-1h2a1 1 0 011 1v6a1 1 0 01-1 1h-2a1 1 0 01-1-1v-6z" />
            </svg>
            Templates
          </button>
          <button
            onClick={() => onNavigate?.('list')}
            className="w-full flex items-center gap-2 px-3 py-2 text-text-secondary hover:bg-bg-tertiary rounded-md text-left"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
            Workspace Agents
          </button>
        </div>
      </nav>

      {/* Bottom Links */}
      <div className="p-2 border-t border-border">
        <a href="https://github.com" target="_blank" rel="noopener noreferrer" className="flex items-center gap-2 px-3 py-2 text-text-secondary hover:bg-bg-tertiary rounded-md text-sm">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Documentation
        </a>
        <button className="w-full flex items-center gap-2 px-3 py-2 text-text-secondary hover:bg-bg-tertiary rounded-md text-sm text-left">
          <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
          </svg>
          Settings
        </button>
      </div>

      {/* User */}
      <div className="p-3 border-t border-border">
        {isAuthenticated ? (
          <button
            onClick={onLogout}
            className="w-full flex items-center gap-2 px-2 py-1.5 text-sm text-text-secondary hover:bg-bg-tertiary rounded-md"
            title="Click to logout"
          >
            <div className="w-6 h-6 bg-accent-teal rounded-full flex items-center justify-center flex-shrink-0">
              <span className="text-white text-xs font-medium">
                {userEmail ? userEmail[0].toUpperCase() : 'U'}
              </span>
            </div>
            <span className="flex-1 text-left truncate text-xs">
              {userEmail || 'Logged in'}
            </span>
          </button>
        ) : (
          <button
            onClick={onLogin}
            className="w-full px-3 py-2 bg-accent-teal text-white rounded-md text-sm font-medium hover:bg-teal-700"
          >
            Login with Google
          </button>
        )}
      </div>
    </div>
  );
}
