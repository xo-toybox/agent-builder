interface HeaderProps {
  agentName: string;
  agentDescription: string;
  chatVisible: boolean;
  onToggleChat: () => void;
  onBack?: () => void;
  showBackButton?: boolean;
}

export function Header({
  agentName,
  agentDescription,
  chatVisible,
  onToggleChat,
  onBack,
  showBackButton = false,
}: HeaderProps) {
  return (
    <header className="h-14 border-b border-border bg-bg-secondary flex items-center justify-between px-4">
      <div className="flex items-center gap-3">
        {/* Back button */}
        {showBackButton && onBack && (
          <button
            onClick={onBack}
            className="p-1.5 hover:bg-bg-tertiary rounded-md text-text-secondary"
            title="Back to agent list"
          >
            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
            </svg>
          </button>
        )}

        {/* Agent name and status */}
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-semibold text-text-primary">{agentName}</h1>
            <span className="px-2 py-0.5 text-xs bg-bg-tertiary text-text-secondary rounded">Editing</span>
            <span className="px-2 py-0.5 text-xs bg-bg-tertiary text-text-secondary rounded">Private</span>
          </div>
          <p className="text-sm text-text-secondary">{agentDescription}</p>
        </div>
      </div>

      <div className="flex items-center gap-2">
        {/* Toggle chat */}
        <button
          onClick={onToggleChat}
          className={`p-2 rounded-md ${chatVisible ? 'bg-bg-tertiary' : 'hover:bg-bg-tertiary'}`}
          title={chatVisible ? 'Hide Chat' : 'Show Chat'}
        >
          <svg className="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </button>

        {/* Save Changes - TODO: wire up to save config */}
        <button className="px-4 py-1.5 text-sm font-medium text-accent-orange hover:bg-accent-orange/10 rounded-md">
          Save Changes
        </button>
      </div>
    </header>
  );
}
