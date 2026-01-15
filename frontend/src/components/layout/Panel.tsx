import { ReactNode } from 'react';

type AccentColor = 'orange' | 'teal' | 'purple' | 'blue';

const accentColors: Record<AccentColor, string> = {
  orange: 'border-l-accent-orange',
  teal: 'border-l-accent-teal',
  purple: 'border-l-accent-purple',
  blue: 'border-l-accent-blue',
};

const accentTextColors: Record<AccentColor, string> = {
  orange: 'text-accent-orange',
  teal: 'text-accent-teal',
  purple: 'text-accent-purple',
  blue: 'text-accent-blue',
};

interface PanelProps {
  title: string;
  accent: AccentColor;
  action?: ReactNode;
  children: ReactNode;
  className?: string;
}

export function Panel({ title, accent, action, children, className = '' }: PanelProps) {
  return (
    <div
      className={`bg-bg-secondary rounded-lg border border-border border-l-4 ${accentColors[accent]} ${className}`}
    >
      <div className="flex items-center justify-between px-4 py-3 border-b border-border">
        <h2 className={`text-sm font-semibold uppercase tracking-wide ${accentTextColors[accent]}`}>
          {title}
        </h2>
        {action}
      </div>
      <div className="p-4">{children}</div>
    </div>
  );
}
