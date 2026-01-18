interface HeaderProps {
  agentName: string;
  agentDescription: string;
  chatVisible: boolean;
  onToggleChat: () => void;
  onBack?: () => void;
  showBackButton?: boolean;
  onSave?: () => void;
  isSaving?: boolean;
  onOpenAgentSettings?: () => void;
}

export function Header({
  agentName,
  agentDescription,
  chatVisible,
  onToggleChat,
  onBack,
  showBackButton = false,
  onSave,
  isSaving = false,
  onOpenAgentSettings,
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

        {/* Agent Settings */}
        {onOpenAgentSettings && (
          <button
            onClick={onOpenAgentSettings}
            className="p-2 rounded-md hover:bg-bg-tertiary"
            title="Agent Settings"
          >
            <svg className="w-5 h-5 text-text-secondary" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
            </svg>
          </button>
        )}

        {/* Save Changes */}
        {onSave && (
          <button
            onClick={onSave}
            disabled={isSaving}
            className="px-4 py-1.5 text-sm font-medium text-accent-orange hover:bg-accent-orange/10 rounded-md disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSaving ? 'Saving...' : 'Save Changes'}
          </button>
        )}
      </div>
    </header>
  );
}
