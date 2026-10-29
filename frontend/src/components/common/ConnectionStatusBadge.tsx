import React from 'react';
import { Badge } from './Badge';

interface ConnectionStatusBadgeProps {
  status: 'connected' | 'disconnected' | 'loading';
  label: string;
  latency?: number | null;
}

export const ConnectionStatusBadge: React.FC<ConnectionStatusBadgeProps> = ({
  status,
  label,
  latency,
}) => {
  if (status === 'loading') {
    return (
      <Badge variant="neutral" size="sm">
        <span className="w-1.5 h-1.5 rounded-full bg-muted-gray animate-pulse" />
        {label}: Checking...
      </Badge>
    );
  }

  if (status === 'connected') {
    return (
      <Badge variant="success" size="sm">
        <span className="w-1.5 h-1.5 rounded-full bg-status-success animate-pulse" />
        {label}: Online {latency !== undefined && latency !== null ? `(${latency}ms)` : ''}
      </Badge>
    );
  }

  return (
    <Badge variant="danger" size="sm">
      <span className="w-1.5 h-1.5 rounded-full bg-status-danger" />
      {label}: Offline
    </Badge>
  );
};

