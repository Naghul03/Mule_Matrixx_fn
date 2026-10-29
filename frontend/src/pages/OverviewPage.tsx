import React, { useEffect, useState } from 'react';
import { useOutletContext, useLocation, useNavigate } from 'react-router-dom';
import {
  ShieldCheck,
  Building2,
  Database,
  Cpu,
  AlertTriangle,
  Briefcase,
  TrendingUp,
  Coins,
  ArrowRight,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { SystemStatus, DashboardMetrics, SimulatedBankInfo } from '../types';
import { api } from '../services/api';

interface ContextType {
  systemStatus: SystemStatus;
  refreshConnectivity: () => void;
}

const SIMULATED_BANKS: SimulatedBankInfo[] = [
  {
    code: 'BNK_A',
    name: 'Apex National Bank',
    adapter: 'bank_a_adapter_v1',
    formatType: 'REST JSON (ISO-8601, Decimal strings)',
    description: 'Corporate and retail banking interface with wire transfer payloads.',
  },
  {
    code: 'BNK_B',
    name: 'Beacon Commercial Bank',
    adapter: 'bank_b_adapter_v1',
    formatType: 'Mainframe Flat (Integer Cents, YYYYMMDD/HHMMSS)',
    description: 'Core-banking mainframe batch feeds with integer cents.',
  },
  {
    code: 'BNK_C',
    name: 'Crestline Trust',
    adapter: 'bank_c_adapter_v1',
    formatType: 'ISO 20022 SEPA (IBAN, Structured Amount)',
    description: 'European/SEPA standardized messaging protocol.',
  },
  {
    code: 'BNK_D',
    name: 'Delta Direct',
    adapter: 'bank_d_adapter_v1',
    formatType: 'Fintech JSON (Unix Epoch ms, Nested Parties)',
    description: 'High-velocity consumer peer-to-peer digital payments platform.',
  },
];

export const OverviewPage: React.FC = () => {
  const { systemStatus, refreshConnectivity } = useOutletContext<ContextType>();
  const location = useLocation();
  const navigate = useNavigate();
  const isCBDC = location.pathname.startsWith('/cbdc');
  const domain = isCBDC ? 'cbdc' : 'current_money';

  const [metrics, setMetrics] = useState<DashboardMetrics | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchMetrics = async () => {
    setLoading(true);
    try {
      const data = await api.getDashboardMetrics(domain);
      setMetrics(data);
    } catch {
      // Keep null if error
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMetrics();
  }, [domain]);

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Title & Platform Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-muted-border gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-amber tracking-wider font-semibold">
              {isCBDC ? 'Digital Currency Token Ledger' : 'Conventional Bank Simulation'}
            </span>
            <Badge variant="amber" size="sm">Active Platform</Badge>
          </div>
          <h2 className="text-xl font-bold font-mono tracking-tight text-warm-white">
            {isCBDC ? 'CBDC Tokens — Operational Command' : 'Current Money — Investigation Command'}
          </h2>
          <p className="text-xs text-muted-gray mt-1">
            {isCBDC
              ? 'Simulated Central Bank Digital Currency token issuance, splitting, peeling, and provenance tracing.'
              : 'Multi-bank transaction simulation, money mule detection, and coordinating kingpin ranking.'}
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => { refreshConnectivity(); fetchMetrics(); }}
            isLoading={systemStatus.loading || loading}
            className="text-xs font-mono"
          >
            Refresh Dashboard
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => navigate(isCBDC ? '/cbdc/scenarios' : '/current-money/scenarios')}
            className="text-xs font-mono"
          >
            <span>Run New Scenario</span>
            <ArrowRight size={13} className="ml-1" />
          </Button>
        </div>
      </div>

      {/* Live Operational Metrics from Persisted Database */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
        <div className="bg-background-card p-4 rounded-lg border border-muted-border">
          <div className="flex items-center justify-between text-muted-gray mb-1">
            <span className="text-xs font-mono uppercase">Open Cases</span>
            <Briefcase size={15} className="text-amber" />
          </div>
          <div className="text-2xl font-bold font-mono text-warm-white">
            {metrics ? metrics.open_cases : 0}
          </div>
          <div className="text-[11px] text-muted-gray mt-1 font-mono">
            {metrics ? metrics.total_cases : 0} total cases recorded
          </div>
        </div>

        <div className="bg-background-card p-4 rounded-lg border border-muted-border">
          <div className="flex items-center justify-between text-muted-gray mb-1">
            <span className="text-xs font-mono uppercase">High Risk Alerts</span>
            <AlertTriangle size={15} className="text-status-danger" />
          </div>
          <div className="text-2xl font-bold font-mono text-status-danger">
            {metrics ? metrics.high_risk_alerts : 0}
          </div>
          <div className="text-[11px] text-muted-gray mt-1 font-mono">
            {metrics ? metrics.medium_risk_alerts : 0} medium risk
          </div>
        </div>

        <div className="bg-background-card p-4 rounded-lg border border-muted-border">
          <div className="flex items-center justify-between text-muted-gray mb-1">
            <span className="text-xs font-mono uppercase">{isCBDC ? 'Ledger Events' : 'Transactions'}</span>
            {isCBDC ? <Coins size={15} className="text-amber" /> : <TrendingUp size={15} className="text-amber" />}
          </div>
          <div className="text-2xl font-bold font-mono text-warm-white">
            {metrics ? metrics.total_transactions : 0}
          </div>
          <div className="text-[11px] text-muted-gray mt-1 font-mono">
            Normalized across adapters
          </div>
        </div>

        <div className="bg-background-card p-4 rounded-lg border border-muted-border">
          <div className="flex items-center justify-between text-muted-gray mb-1">
            <span className="text-xs font-mono uppercase">Total Volume</span>
            <TrendingUp size={15} className="text-amber" />
          </div>
          <div className="text-xl font-bold font-mono text-warm-white truncate" title={`₹${metrics?.total_volume.toLocaleString() || '0'}`}>
            ₹{metrics ? (metrics.total_volume >= 100000 ? `${(metrics.total_volume / 100000).toFixed(1)}L` : metrics.total_volume.toLocaleString()) : '0'}
          </div>
          <div className="text-[11px] text-status-success mt-1 font-mono">
            Exact Decimal precision
          </div>
        </div>
      </div>

      {/* Connectivity & Operational State Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <Card
          title="FastAPI Service"
          subtitle="Modular REST Monolith"
          action={<Cpu size={16} className="text-amber" />}
        >
          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-muted-gray">Service:</span>
              <span className="font-mono text-warm-white">mule-matrix-backend</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-muted-gray">Environment:</span>
              <Badge variant="neutral" size="sm">{systemStatus.service?.environment || 'development'}</Badge>
            </div>
            <div className="flex justify-between items-center text-xs pt-1 border-t border-muted-border">
              <span className="text-muted-gray">Status:</span>
              <Badge variant={systemStatus.service?.status === 'ok' ? 'success' : 'danger'} size="sm">
                {systemStatus.service?.status === 'ok' ? 'Operational' : 'Offline'}
              </Badge>
            </div>
          </div>
        </Card>

        <Card
          title="MySQL Engine"
          subtitle="Alembic Managed Schema"
          action={<Database size={16} className="text-amber" />}
        >
          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-muted-gray">Database:</span>
              <span className="font-mono text-warm-white">{systemStatus.database?.database || 'mule_matrix'}</span>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-muted-gray">Latency:</span>
              <span className="font-mono text-warm-white">
                {systemStatus.database?.latency_ms !== null && systemStatus.database?.latency_ms !== undefined
                  ? `${systemStatus.database.latency_ms} ms`
                  : '—'}
              </span>
            </div>
            <div className="flex justify-between items-center text-xs pt-1 border-t border-muted-border">
              <span className="text-muted-gray">Connection:</span>
              <Badge variant={systemStatus.database?.status === 'connected' ? 'success' : 'danger'} size="sm">
                {systemStatus.database?.status === 'connected' ? 'Connected' : 'Disconnected'}
              </Badge>
            </div>
          </div>
        </Card>

        <Card
          title="Security & Isolation"
          subtitle="Evaluation Boundary"
          action={<ShieldCheck size={16} className="text-amber" />}
        >
          <div className="space-y-3">
            <div className="flex justify-between items-center text-xs">
              <span className="text-muted-gray">Ground Truth:</span>
              <Badge variant="amber" size="sm">Strictly Segregated</Badge>
            </div>
            <div className="flex justify-between items-center text-xs">
              <span className="text-muted-gray">Detector Leakage:</span>
              <span className="font-mono text-status-success">Zero Tolerated</span>
            </div>
            <div className="flex justify-between items-center text-xs pt-1 border-t border-muted-border">
              <span className="text-muted-gray">Evaluation Access:</span>
              <span className="font-mono text-xs text-muted-gray">Post-Detection Only</span>
            </div>
          </div>
        </Card>
      </div>

      {/* Simulated Institutions & Adapters (for Current Money) */}
      {!isCBDC && (
        <Card
          title="Simulated Bank Institutions & Normalized Adapters"
          subtitle="Four distinct native schemas validated and normalized into one canonical contract."
          action={<Badge variant="neutral" size="sm">4 Registered Adapters</Badge>}
        >
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {SIMULATED_BANKS.map((bank) => (
              <div
                key={bank.code}
                className="p-4 bg-background-secondary rounded border border-muted-border flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Building2 size={16} className="text-amber" />
                      <span className="font-mono font-semibold text-xs text-warm-white">
                        {bank.name}
                      </span>
                    </div>
                    <Badge variant="earth" size="sm">{bank.code}</Badge>
                  </div>
                  <p className="text-xs text-muted-gray mb-3">{bank.description}</p>
                </div>
                <div className="pt-3 border-t border-muted-border space-y-1.5 font-mono text-[11px]">
                  <div className="flex justify-between">
                    <span className="text-muted-dark">Adapter ID:</span>
                    <span className="text-amber">{bank.adapter}</span>
                  </div>
                  <div className="flex justify-between">
                    <span className="text-muted-dark">Native Schema:</span>
                    <span className="text-warm-white text-right truncate max-w-[200px]" title={bank.formatType}>
                      {bank.formatType}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </Card>
      )}

      {/* Recent Alerts Feed */}
      {metrics && metrics.recent_alerts.length > 0 && (
        <Card
          title="Recent High Priority Signals"
          subtitle="Latest suspicious transaction alerts generated by detection engine."
          action={<Button variant="ghost" size="sm" onClick={() => navigate(isCBDC ? '/cbdc/alerts' : '/current-money/alerts')}>View All</Button>}
        >
          <div className="space-y-2">
            {metrics.recent_alerts.map((al) => (
              <div
                key={al.id}
                className="p-3 bg-background-secondary rounded border border-muted-border flex items-center justify-between text-xs"
              >
                <div className="flex items-center gap-3">
                  <Badge variant={al.riskBand === 'HIGH' ? 'danger' : 'warning'} size="sm">
                    {al.riskBand} ({al.riskScore})
                  </Badge>
                  <span className="text-muted-gray font-mono">{al.id.slice(0, 8)}...</span>
                  <span className="text-warm-white font-medium">{al.signalsCount} anomaly signals detected</span>
                </div>
                <span className="text-muted-dark font-mono">{new Date(al.createdAt).toLocaleTimeString()}</span>
              </div>
            ))}
          </div>
        </Card>
      )}
    </div>
  );
};
