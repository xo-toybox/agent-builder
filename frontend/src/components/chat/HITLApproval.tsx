import { useState } from 'react';

interface HITLApprovalProps {
  toolCallId: string;
  toolName: string;
  args: Record<string, unknown>;
  onDecision: (
    decision: 'approve' | 'edit' | 'reject',
    toolCallId: string,
    newArgs?: Record<string, unknown>
  ) => void;
}

export function HITLApproval({
  toolCallId,
  toolName,
  args,
  onDecision,
}: HITLApprovalProps) {
  const [editing, setEditing] = useState(false);
  const [editedArgs, setEditedArgs] = useState(JSON.stringify(args, null, 2));
  const [error, setError] = useState<string | null>(null);

  const handleApprove = () => {
    onDecision('approve', toolCallId);
  };

  const handleReject = () => {
    onDecision('reject', toolCallId);
  };

  const handleConfirmEdit = () => {
    try {
      const parsed = JSON.parse(editedArgs);
      setError(null);
      onDecision('edit', toolCallId, parsed);
    } catch {
      setError('Invalid JSON');
    }
  };

  return (
    <div className="p-4 bg-yellow-900/10">
      <div className="flex items-center gap-2 text-yellow-500 mb-3">
        <svg
          className="w-5 h-5"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            strokeWidth={2}
            d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
          />
        </svg>
        <span className="font-medium">Approval Required: {toolName}</span>
      </div>

      {editing ? (
        <div className="mb-3">
          <textarea
            value={editedArgs}
            onChange={(e) => {
              setEditedArgs(e.target.value);
              setError(null);
            }}
            rows={8}
            className="w-full px-3 py-2 bg-bg-tertiary border border-border rounded-md text-white text-sm font-mono focus:border-accent-teal focus:outline-none"
          />
          {error && <p className="text-accent-red text-xs mt-1">{error}</p>}
        </div>
      ) : (
        <pre className="mb-3 p-3 bg-black/30 rounded-md text-sm text-gray-300 overflow-x-auto">
          {JSON.stringify(args, null, 2)}
        </pre>
      )}

      <div className="flex gap-2">
        <button
          onClick={handleApprove}
          className="px-4 py-2 bg-accent-green text-white rounded-md text-sm font-medium hover:bg-green-600 transition-colors"
        >
          Approve
        </button>

        {editing ? (
          <button
            onClick={handleConfirmEdit}
            className="px-4 py-2 bg-accent-blue text-white rounded-md text-sm font-medium hover:bg-blue-600 transition-colors"
          >
            Confirm Edit
          </button>
        ) : (
          <button
            onClick={() => setEditing(true)}
            className="px-4 py-2 bg-bg-tertiary text-gray-300 rounded-md text-sm font-medium hover:bg-gray-700 transition-colors"
          >
            Edit
          </button>
        )}

        <button
          onClick={handleReject}
          className="px-4 py-2 bg-accent-red text-white rounded-md text-sm font-medium hover:bg-red-600 transition-colors"
        >
          Reject
        </button>
      </div>
    </div>
  );
}
