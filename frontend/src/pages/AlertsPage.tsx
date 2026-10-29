import React, { useEffect, useState } from 'react';
import { useLocation, useSearchParams, useNavigate } from 'react-router-dom';
import {
  AlertTriangle,
  RotateCcw,
  CheckCircle,
  XCircle,
  Eye,
  GitGraph,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { AlertItem } from '../types';
import { api } from '../services/api';

export const AlertsPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const isCBDC = location.pathname.startsWith('/cbdc');
  const domain = isCBDC ? 'cbdc' : 'current_money';

  const runIdFilter = searchParams.get('scenario_run_id');

  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [riskFilter, setRiskFilter] = useState<string>('ALL');
  const [statusFilter, setStatusFilter] = useState<string>('ALL');
  const [selectedAlert, setSelectedAlert] = useState<AlertItem | null>(null);

  const fetchAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.listAlerts({
        domain,
        risk_band: riskFilter !== 'ALL' ? riskFilter : undefined,
        review_status: statusFilter !== 'ALL' ? statusFilter : undefined,
        scenario_run_id: runIdFilter || undefined,
        limit: 100,
      });
      setAlerts(data);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAlerts();
  }, [domain, riskFilter, statusFilter, runIdFilter]);

  const handleReview = async (alertId: string, status: string) => {
    try {
      await api.reviewAlert(alertId, status);
      await fetchAlerts();
      if (selectedAlert && selectedAlert.id === alertId) {
        setSelectedAlert((prev) => prev ? { ...prev, review_status: status } : null);
      }
    } catch (err: any) {
      alert(`Error updating review status: ${err.message}`);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-muted-border gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-amber tracking-wider font-semibold">
              Anomaly Surveillance Feed
            </span>
            <Badge variant="amber" size="sm">Multi-Signal Scoring</Badge>
          </div>
          <h2 className="text-xl font-bold font-mono tracking-tight text-warm-white">
            {isCBDC ? 'CBDC Token Anomaly Alerts' : 'Conventional Transaction Alerts'}
          </h2>
          <p className="text-xs text-muted-gray mt-1">
            Explainable suspicion signals detected across pass-through velocity, fan-in/fan-out, and temporal coordination.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {runIdFilter && (
            <Badge variant="neutral" size="sm" className="font-mono">
              Filtered: Run {runIdFilter.slice(0, 8)}...
            </Badge>
          )}
          <Button variant="outline" size="sm" onClick={fetchAlerts} isLoading={loading}>
            <RotateCcw size={13} className="mr-1.5" />
            <span>Refresh Alerts</span>
          </Button>
        </div>
      </div>

      {/* Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-background-secondary rounded-lg border border-muted-border text-xs font-mono">
        <div className="flex items-center gap-2">
          <span className="text-muted-gray uppercase font-semibold">Risk Band:</span>
          {['ALL', 'HIGH', 'MEDIUM', 'LOW'].map((b) => (
            <button
              key={b}
              onClick={() => setRiskFilter(b)}
              className={`px-2.5 py-1 rounded transition-colors ${
                riskFilter === b
                  ? 'bg-earth text-warm-white font-bold'
                  : 'bg-background text-muted-gray hover:text-warm-white border border-muted-border'
              }`}
            >
              {b}
            </button>
          ))}
        </div>

        <div className="flex items-center gap-2">
          <span className="text-muted-gray uppercase font-semibold">Review:</span>
          {['ALL', 'PENDING', 'REVIEWED', 'DISMISSED'].map((s) => (
            <button
              key={s}
              onClick={() => setStatusFilter(s)}
              className={`px-2.5 py-1 rounded transition-colors ${
                statusFilter === s
                  ? 'bg-earth text-warm-white font-bold'
                  : 'bg-background text-muted-gray hover:text-warm-white border border-muted-border'
              }`}
            >
              {s}
            </button>
          ))}
        </div>
      </div>

      {/* Alerts Table / List */}
      <Card
        title="Detected Risk Alerts"
        subtitle="Ranked by total explainable anomaly score"
        action={<Badge variant="neutral" size="sm">{alerts.length} Total Alerts</Badge>}
      >
        {alerts.length === 0 ? (
          <EmptyState
            title="No Alerts Found"
            description="No suspicious activity detected for the active filters. Run a scenario to generate transactions."
            icon={AlertTriangle}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-muted-border text-muted-gray text-[11px] uppercase">
                  <th className="pb-3 font-semibold">Risk Level</th>
                  <th className="pb-3 font-semibold">Subject Account / Wallet</th>
                  <th className="pb-3 font-semibold">Triggered Signals</th>
                  <th className="pb-3 font-semibold">Review Status</th>
                  <th className="pb-3 font-semibold">Timestamp</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-muted-border/50">
                {alerts.map((a) => (
                  <tr key={a.id} className="hover:bg-background-hover/50 transition-colors">
                    <td className="py-3">
                      <div className="flex items-center gap-2">
                        <Badge
                          variant={
                            a.risk_band === 'HIGH'
                              ? 'danger'
                              : a.risk_band === 'MEDIUM'
                              ? 'warning'
                              : 'neutral'
                          }
                          size="sm"
                        >
                          {a.risk_band} ({a.risk_score})
                        </Badge>
                      </div>
                    </td>
                    <td className="py-3">
                      <div className="font-semibold text-warm-white">
                        {a.account_ref || a.account_id?.slice(0, 12) || 'Simulated Entity'}
                      </div>
                      {a.bank_code && (
                        <span className="text-[10px] text-amber font-mono">{a.bank_code}</span>
                      )}
                    </td>
                    <td className="py-3">
                      <div className="flex flex-wrap gap-1 max-w-md">
                        {a.signals.map((s, idx) => (
                          <span
                            key={idx}
                            className="bg-background px-1.5 py-0.5 rounded border border-muted-border text-[10px] text-muted-gray"
                            title={s.description}
                          >
                            {s.signal} (+{s.score})
                          </span>
                        ))}
                      </div>
                    </td>
                    <td className="py-3">
                      <Badge
                        variant={
                          a.review_status === 'REVIEWED'
                            ? 'success'
                            : a.review_status === 'DISMISSED'
                            ? 'neutral'
                            : 'warning'
                        }
                        size="sm"
                      >
                        {a.review_status}
                      </Badge>
                    </td>
                    <td className="py-3 text-muted-gray text-[11px]">
                      {new Date(a.created_at).toLocaleTimeString()}
                    </td>
                    <td className="py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => setSelectedAlert(a)}
                          title="Inspect Evidence Details"
                        >
                          <Eye size={13} />
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            navigate(
                              isCBDC
                                ? `/cbdc/investigation?account_id=${a.account_id || ''}`
                                : `/current-money/investigation?account_id=${a.account_id || ''}&scenario_run_id=${a.scenario_run_id || ''}`
                            )
                          }
                          title="Open in Graph"
                        >
                          <GitGraph size={13} />
                        </Button>
                        {a.review_status === 'PENDING' && (
                          <Button
                            variant="secondary"
                            size="sm"
                            onClick={() => handleReview(a.id, 'REVIEWED')}
                            title="Mark as Reviewed"
                          >
                            <CheckCircle size={13} />
                          </Button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Alert Detail Modal */}
      {selectedAlert && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-background-card border border-muted-border rounded-lg max-w-2xl w-full p-6 space-y-4 shadow-xl">
            <div className="flex items-center justify-between border-b border-muted-border pb-3">
              <div>
                <span className="text-xs font-mono uppercase text-amber font-semibold">
                  Signal Evidence Dossier
                </span>
                <h3 className="text-base font-bold font-mono text-warm-white">
                  Alert ID: {selectedAlert.id}
                </h3>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedAlert(null)}>
                <XCircle size={18} />
              </Button>
            </div>

            <div className="grid grid-cols-2 gap-3 text-xs font-mono">
              <div className="p-3 bg-background-secondary rounded border border-muted-border">
                <span className="text-muted-gray">Risk Score:</span>
                <div className="text-base font-bold text-warm-white mt-0.5">
                  {selectedAlert.risk_score} / 100 ({selectedAlert.risk_band})
                </div>
              </div>
              <div className="p-3 bg-background-secondary rounded border border-muted-border">
                <span className="text-muted-gray">Subject:</span>
                <div className="text-sm font-bold text-warm-white mt-0.5">
                  {selectedAlert.account_ref || selectedAlert.account_id}
                </div>
              </div>
            </div>

            <div>
              <h4 className="text-xs font-mono font-semibold uppercase text-warm-white mb-2">
                Triggered Anomaly Signals ({selectedAlert.signals.length})
              </h4>
              <div className="space-y-2">
                {selectedAlert.signals.map((s, idx) => (
                  <div
                    key={idx}
                    className="p-3 bg-background-secondary rounded border border-muted-border text-xs font-mono space-y-1"
                  >
                    <div className="flex justify-between items-center">
                      <span className="font-bold text-amber uppercase">{s.signal}</span>
                      <span className="text-status-warning font-semibold">Score: +{s.score} / {s.weight}</span>
                    </div>
                    <p className="text-muted-gray text-[11px]">{s.description}</p>
                    {s.evidence && s.evidence.length > 0 && (
                      <div className="mt-2 pt-2 border-t border-muted-border/50 text-[11px] text-warm-white/80">
                        <span className="text-muted-dark">Evidence: </span>
                        {s.evidence.join('; ')}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-between items-center pt-3 border-t border-muted-border text-xs font-mono">
              <div className="flex items-center gap-2">
                <Button
                  variant="secondary"
                  size="sm"
                  onClick={() => handleReview(selectedAlert.id, 'REVIEWED')}
                >
                  Mark as Reviewed
                </Button>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => handleReview(selectedAlert.id, 'DISMISSED')}
                >
                  Dismiss Alert
                </Button>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedAlert(null)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
