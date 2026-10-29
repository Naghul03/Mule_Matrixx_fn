import React from 'react';
import { LucideIcon, Info } from 'lucide-react';

export interface EmptyStateProps {
  title: string;
  description: string;
  icon?: LucideIcon;
  action?: React.ReactNode;
}

export const EmptyState: React.FC<EmptyStateProps> = ({
  title,
  description,
  icon: Icon = Info,
  action,
}) => {
  return (
    <div className="flex flex-col items-center justify-center p-8 text-center border border-dashed border-muted-borderLight rounded-lg bg-background-secondary/50">
      <div className="w-12 h-12 rounded-full bg-background-hover flex items-center justify-center mb-3 text-amber">
        <Icon size={22} />
      </div>
      <h3 className="text-sm font-semibold text-warm-white font-mono uppercase tracking-wide">
        {title}
      </h3>
      <p className="text-xs text-muted-gray mt-1 max-w-sm mb-4">
        {description}
      </p>
      {action && <div>{action}</div>}
    </div>
  );
};

