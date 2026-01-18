/**
 * v0.0.3: Memory Edit Approval Component
 *
 * Displays a diff view of memory changes with suspicious pattern highlighting.
 * Allows user to approve, edit, or reject memory updates.
 */

import { useState, useEffect } from 'react';
import type { MemoryEditRequest, SuspiciousFlag } from '../../types';

interface MemoryEditApprovalProps {
  request: MemoryEditRequest;
  onDecision: (
    decision: 'approve' | 'edit' | 'reject',
    requestId: string,
    toolCallId: string,
    editedContent?: string
  ) => void;
}

export function MemoryEditApproval({ request, onDecision }: MemoryEditApprovalProps) {
  const [editing, setEditing] = useState(false);
  const [editedContent, setEditedContent] = useState(request.proposed_content);
  const [viewMode, setViewMode] = useState<'diff' | 'proposed'>('diff');

  // Reset state when request changes
  useEffect(() => {
    setEditedContent(request.proposed_content);
    setEditing(false);
    setViewMode('diff');
  }, [request.request_id, request.proposed_content]);

  const handleApprove = () => {
    onDecision('approve', request.request_id, request.tool_call_id);
  };

  const handleReject = () => {
    onDecision('reject', request.request_id, request.tool_call_id);
  };

  const handleConfirmEdit = () => {
    onDecision('edit', request.request_id, request.tool_call_id, editedContent);
  };

  const hasSuspiciousPatterns = request.suspicious_flags.length > 0;
  const hasDangerPatterns = request.suspicious_flags.some(f => f.severity === 'danger');

  return (
    <div className={`p-4 border-t ${hasDangerPatterns ? 'bg-accent-red/5 border-accent-red/30' : hasSuspiciousPatterns ? 'bg-accent-orange/5 border-accent-orange/30' : 'bg-accent-blue/5 border-accent-blue/30'}`}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <svg className={`w-5 h-5 ${hasDangerPatterns ? 'text-accent-red' : hasSuspiciousPatterns ? 'text-accent-orange' : 'text-accent-blue'}`} fill="currentColor" viewBox="0 0 24 24">
            <path d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/>
          </svg>
          <span className={`font-medium ${hasDangerPatterns ? 'text-accent-red' : hasSuspiciousPatterns ? 'text-accent-orange' : 'text-accent-blue'}`}>
            Memory Update: {request.path}
          </span>
        </div>
        <div className="flex gap-1">
          <button
            onClick={() => setViewMode('diff')}
            className={`px-2 py-1 text-xs rounded ${viewMode === 'diff' ? 'bg-bg-tertiary text-text-primary' : 'text-text-muted hover:text-text-secondary'}`}
          >
            Diff
          </button>
          <button
            onClick={() => setViewMode('proposed')}
            className={`px-2 py-1 text-xs rounded ${viewMode === 'proposed' ? 'bg-bg-tertiary text-text-primary' : 'text-text-muted hover:text-text-secondary'}`}
          >
            Proposed
          </button>
        </div>
      </div>

      {/* Reason */}
      <p className="text-sm text-text-secondary mb-3">
        <span className="text-text-muted">Reason:</span> {request.reason}
      </p>

      {/* Suspicious Patterns Warning */}
      {hasSuspiciousPatterns && (
        <div className={`mb-3 p-3 rounded-md ${hasDangerPatterns ? 'bg-accent-red/10 border border-accent-red/30' : 'bg-accent-orange/10 border border-accent-orange/30'}`}>
          <div className="flex items-center gap-2 mb-2">
            <svg className={`w-4 h-4 ${hasDangerPatterns ? 'text-accent-red' : 'text-accent-orange'}`} fill="currentColor" viewBox="0 0 24 24">
              <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
            </svg>
            <span className={`text-sm font-medium ${hasDangerPatterns ? 'text-accent-red' : 'text-accent-orange'}`}>
              Suspicious patterns detected
            </span>
          </div>
          <ul className="text-xs space-y-1">
            {request.suspicious_flags.map((flag, idx) => (
              <li key={idx} className={`flex items-start gap-2 ${flag.severity === 'danger' ? 'text-accent-red' : 'text-accent-orange'}`}>
                <span className="mt-0.5">•</span>
                <span>{flag.description}: <code className="bg-bg-tertiary px-1 rounded">{flag.pattern}</code></span>
              </li>
            ))}
          </ul>
        </div>
      )}

      {/* Content View */}
      {editing ? (
        <div className="mb-3">
          <textarea
            value={editedContent}
            onChange={(e) => setEditedContent(e.target.value)}
            rows={10}
            className="w-full px-3 py-2 bg-bg-secondary border border-border rounded-md text-text-primary text-sm font-mono resize-y"
          />
        </div>
      ) : viewMode === 'diff' ? (
        <DiffView
          current={request.current_content}
          proposed={request.proposed_content}
          suspiciousFlags={request.suspicious_flags}
        />
      ) : (
        <pre className="bg-bg-secondary border border-border rounded-md p-3 text-sm text-text-secondary overflow-x-auto mb-3 max-h-64 overflow-y-auto">
          <HighlightedContent content={request.proposed_content} suspiciousFlags={request.suspicious_flags} />
        </pre>
      )}

      {/* Actions */}
      <div className="flex gap-2">
        <button
          onClick={handleApprove}
          className="px-4 py-2 bg-accent-green text-white rounded-md text-sm font-medium hover:bg-green-600"
        >
          Approve
        </button>
        {editing ? (
          <button
            onClick={handleConfirmEdit}
            className="px-4 py-2 bg-accent-blue text-white rounded-md text-sm font-medium hover:bg-blue-600"
          >
            Confirm Edit
          </button>
        ) : (
          <button
            onClick={() => setEditing(true)}
            className="px-4 py-2 bg-bg-tertiary text-text-primary rounded-md text-sm font-medium hover:bg-border"
          >
            Edit
          </button>
        )}
        <button
          onClick={handleReject}
          className="px-4 py-2 bg-accent-red text-white rounded-md text-sm font-medium hover:bg-red-600"
        >
          Reject
        </button>
      </div>
    </div>
  );
}

/**
 * Simple diff view showing current vs proposed content
 */
function DiffView({
  current,
  proposed,
  suspiciousFlags,
}: {
  current: string | null;
  proposed: string;
  suspiciousFlags: SuspiciousFlag[];
}) {
  if (!current) {
    return (
      <div className="mb-3">
        <div className="text-xs text-text-muted mb-1">New file</div>
        <pre className="bg-accent-green/10 border border-accent-green/30 rounded-md p-3 text-sm text-text-secondary overflow-x-auto max-h-64 overflow-y-auto">
          <HighlightedContent content={proposed} suspiciousFlags={suspiciousFlags} />
        </pre>
      </div>
    );
  }

  const currentLines = current.split('\n');
  const proposedLines = proposed.split('\n');

  return (
    <div className="mb-3 grid grid-cols-2 gap-2">
      <div>
        <div className="text-xs text-text-muted mb-1">Current</div>
        <pre className="bg-accent-red/5 border border-accent-red/20 rounded-md p-3 text-sm text-text-secondary overflow-x-auto max-h-64 overflow-y-auto">
          {currentLines.map((line, idx) => (
            <div key={idx} className="whitespace-pre-wrap">
              <span className="text-accent-red/50 mr-2 select-none">-</span>
              {line}
            </div>
          ))}
        </pre>
      </div>
      <div>
        <div className="text-xs text-text-muted mb-1">Proposed</div>
        <pre className="bg-accent-green/5 border border-accent-green/20 rounded-md p-3 text-sm text-text-secondary overflow-x-auto max-h-64 overflow-y-auto">
          {proposedLines.map((line, idx) => (
            <div key={idx} className="whitespace-pre-wrap">
              <span className="text-accent-green/50 mr-2 select-none">+</span>
              <HighlightedLine line={line} suspiciousFlags={suspiciousFlags} />
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}

/**
 * Highlight suspicious patterns in content
 */
function HighlightedContent({
  content,
  suspiciousFlags,
}: {
  content: string;
  suspiciousFlags: SuspiciousFlag[];
}) {
  return (
    <>
      {content.split('\n').map((line, idx) => (
        <div key={idx} className="whitespace-pre-wrap">
          <HighlightedLine line={line} suspiciousFlags={suspiciousFlags} />
        </div>
      ))}
    </>
  );
}

/**
 * Highlight a single line with suspicious patterns
 */
function HighlightedLine({
  line,
  suspiciousFlags,
}: {
  line: string;
  suspiciousFlags: SuspiciousFlag[];
}) {
  // Find matches for all suspicious patterns using the actual matched text
  const lineLower = line.toLowerCase();

  // Check if any matched text appears in this line
  const matchingFlag = suspiciousFlags.find(f =>
    f.match && lineLower.includes(f.match.toLowerCase())
  );

  if (!matchingFlag) {
    return <>{line}</>;
  }

  // Highlight the entire line if it contains suspicious patterns
  return (
    <span className={`${matchingFlag.severity === 'danger' ? 'bg-accent-red/20 text-accent-red' : 'bg-accent-orange/20 text-accent-orange'}`}>
      {line}
    </span>
  );
}
