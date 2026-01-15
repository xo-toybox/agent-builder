import { Panel } from '../layout/Panel';
import type { Trigger } from '../../types';

interface TriggersPanelProps {
  triggers: Trigger[];
  onToggle: (triggerId: string) => void;
}

export function TriggersPanel({ triggers, onToggle }: TriggersPanelProps) {
  return (
    <Panel
      title="Triggers"
      accent="orange"
      action={
        <button className="text-gray-400 hover:text-white text-xl leading-none">
          +
        </button>
      }
    >
      {triggers.length === 0 ? (
        <p className="text-gray-500 text-sm">No triggers configured</p>
      ) : (
        <div className="space-y-2">
          {triggers.map((trigger) => (
            <div
              key={trigger.id}
              className="flex items-center justify-between p-3 bg-bg-tertiary rounded-md"
            >
              <div className="flex items-center gap-3">
                <div
                  className={`w-2 h-2 rounded-full ${
                    trigger.enabled ? 'bg-accent-green' : 'bg-gray-500'
                  }`}
                />
                <div>
                  <p className="text-sm text-white">
                    {trigger.type === 'gmail_polling' ? 'Gmail Polling' : trigger.type}
                  </p>
                  <p className="text-xs text-gray-400">
                    {trigger.type === 'gmail_polling' &&
                      `every ${trigger.config.interval_seconds || 30}s`}
                  </p>
                </div>
              </div>
              <button
                onClick={() => onToggle(trigger.id)}
                className={`px-3 py-1 text-xs rounded-md transition-colors ${
                  trigger.enabled
                    ? 'bg-accent-green/20 text-accent-green'
                    : 'bg-gray-700 text-gray-400 hover:bg-gray-600'
                }`}
              >
                {trigger.enabled ? 'ON' : 'OFF'}
              </button>
            </div>
          ))}
        </div>
      )}
    </Panel>
  );
}
