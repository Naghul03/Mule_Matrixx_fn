import React from 'react';
import { RefreshCw, Server, Database } from 'lucide-react';
import { AppSection, SystemStatus } from '../../types';
import { ConnectionStatusBadge } from '../common/ConnectionStatusBadge';
import { Button } from '../common/Button';

interface HeaderProps {
  currentSection: AppSection;
  systemStatus: SystemStatus;
  onRefreshHealth: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  currentSection,
  systemStatus,
  onRefreshHealth,
}) => {
  const sectionTitle =
    currentSection === 'current_money'
      ? 'Current Money — Conventional Multi-Bank Simulation'
      : 'CBDC Tokens — Digital Currency Ledger (Module 6)';

  return (
    <header className="h-16 border-b border-muted-border bg-background-secondary/80 backdrop-blur px-6 flex items-center justify-between flex-shrink-0 z-10">
      <div className="flex items-center gap-3">
        <div className="text-xs font-mono uppercase text-muted-gray tracking-wider">
          Environment:
        </div>
        <div className="text-xs font-semibold text-warm-white tracking-wide">
          {sectionTitle}
        </div>
      </div>

      <div className="flex items-center gap-3">
        {/* API Health Status */}
        <div className="flex items-center gap-1.5">
          <Server size={14} className="text-muted-gray" />
          <ConnectionStatusBadge
            status={
              systemStatus.loading
                ? 'loading'
                : systemStatus.service?.status === 'ok'
                ? 'connected'
                : 'disconnected'
            }
            label="API"
          />
        </div>

        {/* Database Health Status */}
        <div className="flex items-center gap-1.5">
          <Database size={14} className="text-muted-gray" />
          <ConnectionStatusBadge
            status={
              systemStatus.loading
                ? 'loading'
                : systemStatus.database?.status === 'connected'
                ? 'connected'
                : 'disconnected'
            }
            label="MySQL"
            latency={systemStatus.database?.latency_ms}
          />
        </div>

        {/* Refresh Connectivity Button */}
        <Button
          variant="outline"
          size="sm"
          onClick={onRefreshHealth}
          disabled={systemStatus.loading}
          className="text-xs font-mono ml-2"
          title="Refresh connection status"
        >
          <RefreshCw
            size={12}
            className={systemStatus.loading ? 'animate-spin' : ''}
          />
          <span>Check</span>
        </Button>
      </div>
    </header>
  );
};

