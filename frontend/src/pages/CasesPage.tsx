import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Briefcase,
  PlusCircle,
  RotateCcw,
  GitGraph,
  FileText,
  Search,
  XCircle,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { CaseItem, CaseDetail } from '../types';
import { api } from '../services/api';

export const CasesPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const isCBDC = location.pathname.startsWith('/cbdc');
  const domain = isCBDC ? 'cbdc' : 'current_money';

  const [cases, setCases] = useState<CaseItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');

  const [selectedCase, setSelectedCase] = useState<CaseDetail | null>(null);
  const [statusModalOpen, setStatusModalOpen] = useState(false);
  const [newStatus, setNewStatus] = useState('UNDER_INVESTIGATION');
  const [statusNote, setStatusNote] = useState('');

  // Manual Case Entry Modal state
  const [manualModalOpen, setManualModalOpen] = useState(false);
  const [manualBank, setManualBank] = useState('BNK_A');
  const [manualTxRef, setManualTxRef] = useState('');
  const [manualAccRef, setManualAccRef] = useState('');
  const [manualCategory, setManualCategory] = useState('SUSPICIOUS_PASS_THROUGH');
  const [manualDesc, setManualDesc] = useState('');
  const [manualSubmitting, setManualSubmitting] = useState(false);

  const fetchCases = async () => {
    setLoading(true);
    try {
      const data = await api.listCases({
        domain,
        status: statusFilter !== 'ALL' ? statusFilter : undefined,
        priority: priorityFilter !== 'ALL' ? priorityFilter : undefined,
        search: search.trim() || undefined,
      });
      setCases(data);
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchCases();
  }, [domain, statusFilter, priorityFilter]);

  const openCaseDetail = async (caseId: string) => {
    try {
      const detail = await api.getCase(caseId);
      setSelectedCase(detail);
    } catch (err: any) {
      alert(`Error loading case: ${err.message}`);
    }
  };

  const handleUpdateStatus = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedCase) return;
    try {
      const updated = await api.updateCaseStatus(selectedCase.id, newStatus, statusNote);
      setSelectedCase(updated);
      setStatusModalOpen(false);
      setStatusNote('');
      await fetchCases();
    } catch (err: any) {
      alert(`Failed to update status: ${err.message}`);
    }
  };

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setManualSubmitting(true);
    try {
      const newCase = await api.createManualCase({
        bank_code: manualBank,
        transaction_reference: manualTxRef || undefined,
        account_reference: manualAccRef || undefined,
        suspicion_category: manualCategory,
        description: manualDesc,
      });
      setManualModalOpen(false);
      setManualTxRef('');
      setManualAccRef('');
      setManualDesc('');
      await fetchCases();
      setSelectedCase(newCase);
    } catch (err: any) {
      alert(`Manual entry error: ${err.message}`);
    } finally {
      setManualSubmitting(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-muted-border gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-amber tracking-wider font-semibold">
              Case Investigation Registry
            </span>
            <Badge variant="amber" size="sm">Evidence Dossiers</Badge>
          </div>
          <h2 className="text-xl font-bold font-mono tracking-tight text-warm-white">
            {isCBDC ? 'CBDC Investigation Cases' : 'Conventional Financial Crime Cases'}
          </h2>
          <p className="text-xs text-muted-gray mt-1">
            Automated cluster aggregation, manual lead intake, evidence tracking, and formal escalation.
          </p>
        </div>

        <div className="flex items-center gap-2">
          {!isCBDC && (
            <Button
              variant="primary"
              size="sm"
              onClick={() => setManualModalOpen(true)}
              className="text-xs font-mono"
            >
              <PlusCircle size={13} className="mr-1.5" />
              <span>Manual Lead Entry</span>
            </Button>
          )}
          <Button variant="outline" size="sm" onClick={fetchCases} isLoading={loading}>
            <RotateCcw size={13} className="mr-1.5" />
            <span>Refresh Cases</span>
          </Button>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-background-secondary rounded-lg border border-muted-border text-xs font-mono">
        <div className="flex items-center gap-2 flex-1 max-w-sm">
          <Search size={14} className="text-muted-gray" />
          <input
            type="text"
            placeholder="Search reference, title..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && fetchCases()}
            className="w-full bg-background border border-muted-border rounded px-2.5 py-1 text-xs text-warm-white focus:outline-none focus:border-amber"
          />
        </div>

        <div className="flex items-center gap-2">
          <span className="text-muted-gray uppercase font-semibold">Priority:</span>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="bg-background border border-muted-border rounded px-2 py-1 text-xs text-warm-white focus:outline-none focus:border-amber"
          >
            <option value="ALL">ALL</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
        <div className="flex items-center gap-2">
          <span className="text-muted-gray uppercase font-semibold">Status:</span>
          {['ALL', 'OPEN', 'UNDER_INVESTIGATION', 'ESCALATED', 'CLOSED'].map((st) => (
            <button
              key={st}
              onClick={() => setStatusFilter(st)}
              className={`px-2 py-1 rounded transition-colors text-[11px] ${
                statusFilter === st
                  ? 'bg-earth text-warm-white font-bold'
                  : 'bg-background text-muted-gray hover:text-warm-white border border-muted-border'
              }`}
            >
              {st}
            </button>
          ))}
        </div>
      </div>

      {/* Cases Table */}
      <Card
        title="Active Investigation Dossiers"
        subtitle="Cases aggregated by shared account and 24h event temporal clustering"
        action={<Badge variant="neutral" size="sm">{cases.length} Cases</Badge>}
      >
        {cases.length === 0 ? (
          <EmptyState
            title="No Cases Recorded"
            description="Run a scenario to trigger automated high-risk case creation, or use 'Manual Lead Entry'."
            icon={Briefcase}
          />
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-muted-border text-muted-gray text-[11px] uppercase">
                  <th className="pb-3 font-semibold">Case Reference</th>
                  <th className="pb-3 font-semibold">Title & Context</th>
                  <th className="pb-3 font-semibold">Priority</th>
                  <th className="pb-3 font-semibold">Risk Band</th>
                  <th className="pb-3 font-semibold">Status</th>
                  <th className="pb-3 font-semibold">Evidence Entities</th>
                  <th className="pb-3 font-semibold text-right">Actions</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-muted-border/50">
                {cases.map((c) => (
                  <tr key={c.id} className="hover:bg-background-hover/50 transition-colors">
                    <td className="py-3">
                      <div className="font-bold text-amber">{c.case_reference}</div>
                      {c.is_manual_entry && (
                        <span className="text-[10px] bg-earth/30 text-warm-white px-1 py-0.5 rounded border border-earth/50">
                          Manual Lead
                        </span>
                      )}
                    </td>
                    <td className="py-3 max-w-sm">
                      <div className="font-semibold text-warm-white truncate" title={c.title}>{c.title}</div>
                      <div className="text-[11px] text-muted-gray truncate">{c.summary}</div>
                    </td>
                    <td className="py-3">
                      <Badge
                        variant={c.priority === 'CRITICAL' ? 'danger' : c.priority === 'HIGH' ? 'warning' : 'neutral'}
                        size="sm"
                      >
                        {c.priority}
                      </Badge>
                    </td>
                    <td className="py-3">
                      <Badge variant={c.risk_band === 'HIGH' ? 'danger' : 'warning'} size="sm">
                        {c.risk_band || 'MEDIUM'} ({c.aggregate_risk_score || 0})
                      </Badge>
                    </td>
                    <td className="py-3">
                      <Badge
                        variant={
                          c.status === 'OPEN'
                            ? 'amber'
                            : c.status === 'UNDER_INVESTIGATION'
                            ? 'warning'
                            : c.status === 'ESCALATED'
                            ? 'danger'
                            : 'neutral'
                        }
                        size="sm"
                      >
                        {c.status}
                      </Badge>
                    </td>
                    <td className="py-3 text-muted-gray text-[11px]">
                      {c.alert_count} alerts • {c.account_count} accounts • {c.transaction_count} txns
                    </td>
                    <td className="py-3 text-right">
                      <div className="flex items-center justify-end gap-1.5">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => openCaseDetail(c.id)}
                          className="text-xs font-mono"
                        >
                          Dossier
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() =>
                            navigate(
                              isCBDC
                                ? `/cbdc/investigation?case_id=${c.id}`
                                : `/current-money/investigation?case_id=${c.id}`
                            )
                          }
                          title="Open Graph"
                        >
                          <GitGraph size={13} />
                        </Button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>

      {/* Case Detail Modal / Drawer */}
      {selectedCase && (
        <div className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-4">
          <div className="bg-background-card border border-muted-border rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto p-6 space-y-6 shadow-2xl">
            <div className="flex items-center justify-between border-b border-muted-border pb-3">
              <div>
                <span className="text-xs font-mono uppercase text-amber font-semibold">
                  Investigation Dossier
                </span>
                <h3 className="text-lg font-bold font-mono text-warm-white">
                  {selectedCase.case_reference} — {selectedCase.title}
                </h3>
              </div>
              <Button variant="ghost" size="sm" onClick={() => setSelectedCase(null)}>
                <XCircle size={18} />
              </Button>
            </div>

            {/* Quick Status Bar */}
            <div className="flex flex-wrap items-center justify-between gap-3 p-3 bg-background-secondary rounded border border-muted-border text-xs font-mono">
              <div className="flex items-center gap-3">
                <span>Status: <Badge variant="amber" size="sm">{selectedCase.status}</Badge></span>
                <span>Priority: <Badge variant="warning" size="sm">{selectedCase.priority}</Badge></span>
                <span>Score: <strong className="text-status-danger">{selectedCase.aggregate_risk_score || 0}/100</strong></span>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="secondary" size="sm" onClick={() => setStatusModalOpen(true)}>
                  Change Status
                </Button>
                <a
                  href={api.getCaseReportPdfUrl(selectedCase.id)}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-earth hover:bg-earth-light rounded text-warm-white text-xs font-mono font-medium"
                >
                  <FileText size={13} />
                  <span>Download PDF Dossier</span>
                </a>
                <Button
                  variant="primary"
                  size="sm"
                  onClick={() =>
                    navigate(
                      isCBDC
                        ? `/cbdc/investigation?case_id=${selectedCase.id}`
                        : `/current-money/investigation?case_id=${selectedCase.id}`
                    )
                  }
                >
                  <GitGraph size={13} className="mr-1" />
                  <span>Launch Graph</span>
                </Button>
              </div>
            </div>

            {/* Summary */}
            <div>
              <h4 className="text-xs font-mono font-semibold uppercase text-warm-white mb-1">
                Executive Overview
              </h4>
              <p className="text-xs text-muted-gray leading-relaxed bg-background p-3 rounded border border-muted-border font-mono">
                {selectedCase.summary}
              </p>
            </div>

            {/* Linked Transactions */}
            <div>
              <h4 className="text-xs font-mono font-semibold uppercase text-warm-white mb-2">
                Linked Evidence Transactions ({selectedCase.transactions.length})
              </h4>
              <div className="max-h-48 overflow-y-auto border border-muted-border rounded">
                <table className="w-full text-left text-xs font-mono">
                  <thead className="bg-background-secondary text-muted-gray text-[11px]">
                    <tr>
                      <th className="p-2">Tx Ref</th>
                      <th className="p-2">Source</th>
                      <th className="p-2">Destination</th>
                      <th className="p-2">Amount</th>
                      <th className="p-2">Timestamp</th>
                      <th className="p-2">Type</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-muted-border/50">
                    {selectedCase.transactions.map((t) => (
                      <tr key={t.id} className="hover:bg-background-hover">
                        <td className="p-2 font-bold text-amber">{t.reference}</td>
                        <td className="p-2">{t.source}</td>
                        <td className="p-2">{t.destination}</td>
                        <td className="p-2 font-bold text-warm-white">₹{t.amount.toLocaleString()}</td>
                        <td className="p-2 text-muted-gray">{new Date(t.timestamp).toLocaleTimeString()}</td>
                        <td className="p-2"><Badge variant="neutral" size="sm">{t.evidence_type}</Badge></td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            {/* Audit Notes */}
            <div>
              <h4 className="text-xs font-mono font-semibold uppercase text-warm-white mb-2">
                Investigator Notes & Chain of Custody ({selectedCase.notes.length})
              </h4>
              <div className="space-y-2 max-h-40 overflow-y-auto">
                {selectedCase.notes.map((n) => (
                  <div key={n.id} className="p-2.5 bg-background rounded border border-muted-border text-xs font-mono space-y-1">
                    <div className="flex justify-between items-center text-[10px] text-muted-dark">
                      <span className="font-bold text-amber">{n.note_type}</span>
                      <span>{new Date(n.created_at).toLocaleString()}</span>
                    </div>
                    <p className="text-muted-gray">{n.content}</p>
                    {n.previous_status && (
                      <div className="text-[10px] text-muted-dark">
                        Status transition: {n.previous_status} &rarr; {n.new_status}
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>

            <div className="flex justify-end pt-3 border-t border-muted-border">
              <Button variant="ghost" size="sm" onClick={() => setSelectedCase(null)}>
                Close Dossier
              </Button>
            </div>
          </div>
        </div>
      )}

      {/* Change Status Modal */}
      {statusModalOpen && selectedCase && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <form
            onSubmit={handleUpdateStatus}
            className="bg-background-card border border-muted-border rounded-lg max-w-md w-full p-6 space-y-4 shadow-xl text-xs font-mono"
          >
            <h3 className="text-sm font-bold text-warm-white uppercase">Update Case Status</h3>
            <div>
              <label className="block text-muted-gray mb-1">New Status</label>
              <select
                value={newStatus}
                onChange={(e) => setNewStatus(e.target.value)}
                className="w-full bg-background border border-muted-border rounded p-2 text-warm-white focus:outline-none focus:border-amber"
              >
                <option value="OPEN">OPEN</option>
                <option value="UNDER_INVESTIGATION">UNDER_INVESTIGATION</option>
                <option value="ESCALATED">ESCALATED</option>
                <option value="CLOSED">CLOSED</option>
              </select>
            </div>
            <div>
              <label className="block text-muted-gray mb-1">Investigator Rationale (Audit Record)</label>
              <textarea
                value={statusNote}
                onChange={(e) => setStatusNote(e.target.value)}
                required
                rows={3}
                placeholder="Document justification for status change..."
                className="w-full bg-background border border-muted-border rounded p-2 text-warm-white focus:outline-none focus:border-amber"
              />
            </div>
            <div className="flex justify-end gap-2 pt-2">
              <Button variant="ghost" size="sm" type="button" onClick={() => setStatusModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" type="submit">
                Confirm Update
              </Button>
            </div>
          </form>
        </div>
      )}

      {/* Manual Lead Entry Modal (Current Money only) */}
      {manualModalOpen && (
        <div className="fixed inset-0 z-50 bg-black/80 flex items-center justify-center p-4">
          <form
            onSubmit={handleManualSubmit}
            className="bg-background-card border border-muted-border rounded-lg max-w-lg w-full p-6 space-y-4 shadow-2xl text-xs font-mono"
          >
            <div className="flex justify-between items-center border-b border-muted-border pb-2">
              <h3 className="text-sm font-bold text-warm-white uppercase">Manual Investigation Lead Entry</h3>
              <Button variant="ghost" size="sm" onClick={() => setManualModalOpen(false)}>
                <XCircle size={16} />
              </Button>
            </div>

            <div className="p-3 bg-earth/15 border border-earth/30 rounded text-[11px] text-muted-gray">
              If the submitted transaction or account reference matches real synthetic records in the database, the case will link to observed evidence. If not, an <strong>Unverified Lead</strong> will be created without fabricating fake graphs.
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-muted-gray mb-1">Originating Bank</label>
                <select
                  value={manualBank}
                  onChange={(e) => setManualBank(e.target.value)}
                  className="w-full bg-background border border-muted-border rounded p-2 text-warm-white focus:outline-none focus:border-amber"
                >
                  <option value="BNK_A">Apex National (BNK_A)</option>
                  <option value="BNK_B">Beacon Commercial (BNK_B)</option>
                  <option value="BNK_C">Crestline Trust (BNK_C)</option>
                  <option value="BNK_D">Delta Direct (BNK_D)</option>
                </select>
              </div>

              <div>
                <label className="block text-muted-gray mb-1">Suspicion Category</label>
                <select
                  value={manualCategory}
                  onChange={(e) => setManualCategory(e.target.value)}
                  className="w-full bg-background border border-muted-border rounded p-2 text-warm-white focus:outline-none focus:border-amber"
                >
                  <option value="SUSPICIOUS_PASS_THROUGH">Suspicious Pass-Through</option>
                  <option value="STRUCTURING_SMURFING">Structuring / Smurfing</option>
                  <option value="VICTIM_DEFRAUDED">Victim Defrauded Funds</option>
                  <option value="PRE_POSITIONED_TRANSFER">Pre-Positioned Liquidity</option>
                </select>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-3">
              <div>
                <label className="block text-muted-gray mb-1">Transaction Ref (If Known)</label>
                <input
                  type="text"
                  placeholder="e.g. TX-S1-1-..."
                  value={manualTxRef}
                  onChange={(e) => setManualTxRef(e.target.value)}
                  className="w-full bg-background border border-muted-border rounded p-2 text-warm-white focus:outline-none focus:border-amber"
                />
              </div>

              <div>
                <label className="block text-muted-gray mb-1">Account Ref (If Known)</label>
                <input
                  type="text"
                  placeholder="e.g. ACC-..."
                  value={manualAccRef}
                  onChange={(e) => setManualAccRef(e.target.value)}
                  className="w-full bg-background border border-muted-border rounded p-2 text-warm-white focus:outline-none focus:border-amber"
                />
              </div>
            </div>

            <div>
              <label className="block text-muted-gray mb-1">Investigator Concern / Lead Description</label>
              <textarea
                value={manualDesc}
                onChange={(e) => setManualDesc(e.target.value)}
                required
                rows={3}
                placeholder="Enter field notes describing the reported suspicion..."
                className="w-full bg-background border border-muted-border rounded p-2 text-warm-white focus:outline-none focus:border-amber"
              />
            </div>

            <div className="flex justify-end gap-2 pt-2 border-t border-muted-border">
              <Button variant="ghost" size="sm" type="button" onClick={() => setManualModalOpen(false)}>
                Cancel
              </Button>
              <Button variant="primary" size="sm" type="submit" isLoading={manualSubmitting}>
                Submit Lead
              </Button>
            </div>
          </form>
        </div>
      )}
    </div>
  );
};
