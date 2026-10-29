import React from 'react';

export interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  action?: React.ReactNode;
}

export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  title,
  subtitle,
  action,
}) => {
  return (
    <div
      className={`bg-background-card border border-muted-border rounded-lg shadow-sm overflow-hidden ${className}`}
    >
      {(title || action) && (
        <div className="px-5 py-4 border-b border-muted-border flex items-center justify-between">
          <div>
            {title && (
              <h3 className="text-sm font-semibold text-warm-white tracking-wide uppercase font-mono">
                {title}
              </h3>
            )}
            {subtitle && (
              <p className="text-xs text-muted-gray mt-0.5">{subtitle}</p>
            )}
          </div>
          {action && <div>{action}</div>}
        </div>
      )}
      <div className="p-5">{children}</div>
    </div>
  );
};

