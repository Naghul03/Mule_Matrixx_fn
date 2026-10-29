import React, { useEffect, useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Play,
  RotateCcw,
  CheckCircle2,
  GitGraph,
  BellRing,
  Layers,
  HelpCircle,
} from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';
import { Button } from '../components/common/Button';
import { EmptyState } from '../components/common/EmptyState';
import { ScenarioTemplate, ScenarioRunResponse } from '../types';
import { api } from '../services/api';

export const ScenariosPage: React.FC = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const isCBDC = location.pathname.startsWith('/cbdc');
  const domain = isCBDC ? 'cbdc' : 'current_money';

  const [templates, setTemplates] = useState<ScenarioTemplate[]>([]);
  const [selectedScenario, setSelectedScenario] = useState<string>(isCBDC ? 'scenario_2' : 'scenario_3');
  const [seed, setSeed] = useState<number>(1337);
  const [baseAmount, setBaseAmount] = useState<number>(400000);
  const [attackAccounts, setAttackAccounts] = useState<number>(5);
  const [decoys, setDecoys] = useState<number>(4);

  const [runs, setRuns] = useState<ScenarioRunResponse[]>([]);
  const [loading, setLoading] = useState(false);
  const [running, setRunning] = useState(false);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const [tList, rList] = await Promise.all([
        api.listScenarioTemplates(domain),
        api.listScenarioRuns(domain, 15),
      ]);
      setTemplates(tList);
      setRuns(rList);
      if (tList.length > 0 && !tList.some((t) => t.id === selectedScenario)) {
        setSelectedScenario(tList[0].id);
        setSeed(tList[0].default_seed);
        setBaseAmount(tList[0].default_amount);
      }
    } catch {
      // Handled
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, [domain]);

  const handleScenarioSelect = (id: string) => {
    setSelectedScenario(id);
    const tmpl = templates.find((t) => t.id === id);
    if (tmpl) {
      setSeed(tmpl.default_seed);
      setBaseAmount(tmpl.default_amount);
    }
  };

  const handleRun = async (e: React.FormEvent) => {
    e.preventDefault();
    setRunning(true);
    setSuccessMessage(null);
    try {
      const res = await api.runScenario({
        scenario_id: selectedScenario,
        seed: Number(seed),
        base_amount: Number(baseAmount),
        num_attack_accounts: Number(attackAccounts),
        num_decoys: Number(decoys),
      });
      setSuccessMessage(
        `Scenario executed successfully! Generated ${res.transaction_count} transactions, ${res.alert_count} alerts, and ${res.case_count} cases.`
      );
      await loadData();
    } catch (err: any) {
      alert(`Scenario execution error: ${err.message}`);
    } finally {
      setRunning(false);
    }
  };

  return (
    <div className="max-w-7xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex flex-col md:flex-row md:items-center justify-between pb-4 border-b border-muted-border gap-4">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-amber tracking-wider font-semibold">
              Scenario Execution Engine
            </span>
            <Badge variant="amber" size="sm">Seeded PRNG</Badge>
          </div>
          <h2 className="text-xl font-bold font-mono tracking-tight text-warm-white">
            {isCBDC ? 'CBDC Token Simulation Generator' : 'Synthetic Multi-Bank Scenarios'}
          </h2>
          <p className="text-xs text-muted-gray mt-1">
            Reproducible money-laundering topologies, pre-positioned replenishment, and structuring flows.
          </p>
        </div>
        <Button variant="outline" size="sm" onClick={loadData} isLoading={loading}>
          <RotateCcw size={13} className="mr-1.5" />
          <span>Refresh Runs</span>
        </Button>
      </div>

      {successMessage && (
        <div className="p-4 bg-status-success/15 border border-status-success/30 rounded-lg text-xs font-mono text-status-success flex items-center gap-2">
          <CheckCircle2 size={16} />
          <span>{successMessage}</span>
        </div>
      )}

      {/* Main Grid: Config Panel on Left, Historical Runs on Right */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left: Configuration Form */}
        <div className="lg:col-span-1 space-y-4">
          <Card
            title="Scenario Parameters"
            subtitle="Configure topology seed and scale"
            action={<Layers size={16} className="text-amber" />}
          >
            <form onSubmit={handleRun} className="space-y-4">
              <div>
                <label className="block text-xs font-mono uppercase text-muted-gray mb-1.5 font-semibold">
                  Select Scenario
                </label>
                <div className="space-y-2">
                  {templates.map((t) => (
                    <div
                      key={t.id}
                      onClick={() => handleScenarioSelect(t.id)}
                      className={`p-3 rounded border text-xs cursor-pointer transition-all ${
                        selectedScenario === t.id
                          ? 'bg-earth/25 border-amber text-warm-white font-medium shadow-sm'
                          : 'bg-background-secondary border-muted-border text-muted-gray hover:border-muted-borderLight'
                      }`}
                    >
                      <div className="flex items-center justify-between mb-1">
                        <span className="font-mono font-bold text-warm-white">{t.name}</span>
                        {selectedScenario === t.id && (
                          <Badge variant="amber" size="sm">Active</Badge>
                        )}
                      </div>
                      <p className="text-[11px] text-muted-gray leading-relaxed mb-2">
                        {t.description}
                      </p>
                      <div className="flex flex-wrap gap-1">
                        {t.key_typologies.map((k) => (
                          <span
                            key={k}
                            className="text-[10px] bg-background px-1.5 py-0.5 rounded border border-muted-border font-mono text-muted-gray"
                          >
                            {k}
                          </span>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* Seed Control */}
              <div>
                <div className="flex justify-between items-center mb-1">
                  <label className="text-xs font-mono uppercase text-muted-gray font-semibold">
                    Reproducibility Seed
                  </label>
                  <span className="text-[10px] text-muted-dark font-mono">Isolated PRNG</span>
                </div>
                <input
                  type="number"
                  value={seed}
                  onChange={(e) => setSeed(Number(e.target.value))}
                  required
                  className="w-full bg-background border border-muted-border rounded px-3 py-2 text-xs font-mono text-warm-white focus:outline-none focus:border-amber"
                />
              </div>

              {/* Amount Control */}
              <div>
                <label className="block text-xs font-mono uppercase text-muted-gray mb-1 font-semibold">
                  Base Transfer Amount (₹)
                </label>
                <input
                  type="number"
                  value={baseAmount}
                  onChange={(e) => setBaseAmount(Number(e.target.value))}
                  required
                  min={1000}
                  step={1000}
                  className="w-full bg-background border border-muted-border rounded px-3 py-2 text-xs font-mono text-warm-white focus:outline-none focus:border-amber"
                />
              </div>

              {/* Attack Accounts (Max 10) */}
              {!isCBDC && (
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <label className="text-xs font-mono uppercase text-muted-gray font-semibold">
                      Attack Pattern Accounts
                    </label>
                    <span className="text-[10px] text-amber font-mono font-semibold">Max 10</span>
                  </div>
                  <input
                    type="number"
                    value={attackAccounts}
                    onChange={(e) => setAttackAccounts(Math.min(10, Math.max(3, Number(e.target.value))))}
                    min={3}
                    max={10}
                    className="w-full bg-background border border-muted-border rounded px-3 py-2 text-xs font-mono text-warm-white focus:outline-none focus:border-amber"
                  />
                </div>
              )}

              {/* Decoys */}
              {!isCBDC && (
                <div>
                  <label className="block text-xs font-mono uppercase text-muted-gray mb-1 font-semibold">
                    Decoy Accounts (Merchant/Payroll)
                  </label>
                  <input
                    type="number"
                    value={decoys}
                    onChange={(e) => setDecoys(Number(e.target.value))}
                    min={0}
                    max={15}
                    className="w-full bg-background border border-muted-border rounded px-3 py-2 text-xs font-mono text-warm-white focus:outline-none focus:border-amber"
                  />
                </div>
              )}

              <Button
                type="submit"
                variant="primary"
                size="md"
                isLoading={running}
                className="w-full text-xs font-mono uppercase font-bold tracking-wider"
              >
                <Play size={14} className="mr-1.5" />
                <span>Generate & Execute Scenario</span>
              </Button>
            </form>
          </Card>
        </div>

        {/* Right: Historical Scenario Runs */}
        <div className="lg:col-span-2 space-y-4">
          <Card
            title="Generated Scenario Runs"
            subtitle="Persisted datasets with exact seed provenance"
            action={<Badge variant="neutral" size="sm">{runs.length} Runs</Badge>}
          >
            {runs.length === 0 ? (
              <EmptyState
                title="No Scenarios Run Yet"
                description="Configure parameters on the left and click 'Generate & Execute Scenario' to produce a reproducible dataset."
                icon={HelpCircle}
              />
            ) : (
              <div className="space-y-3">
                {runs.map((r) => (
                  <div
                    key={r.id}
                    className="p-4 bg-background-secondary rounded-lg border border-muted-border space-y-3 hover:border-muted-borderLight transition-all"
                  >
                    <div className="flex flex-col md:flex-row md:items-center justify-between gap-2 border-b border-muted-border pb-2.5">
                      <div>
                        <div className="flex items-center gap-2">
                          <span className="font-mono font-bold text-xs text-warm-white uppercase">
                            {r.scenario_identifier}
                          </span>
                          <Badge variant="amber" size="sm">Seed {r.seed}</Badge>
                          <Badge variant={r.status === 'COMPLETED' ? 'success' : 'danger'} size="sm">
                            {r.status}
                          </Badge>
                        </div>
                        <span className="text-[10px] text-muted-gray font-mono">
                          Run ID: {r.id} • {new Date(r.created_at).toLocaleString()}
                        </span>
                      </div>

                      <div className="flex items-center gap-2">
                        <Button
                          variant="secondary"
                          size="sm"
                          onClick={() => navigate(isCBDC ? `/cbdc/investigation?scenario_run_id=${r.id}` : `/current-money/investigation?scenario_run_id=${r.id}`)}
                          className="text-xs font-mono"
                        >
                          <GitGraph size={13} className="mr-1" />
                          <span>Inspect Graph</span>
                        </Button>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => navigate(isCBDC ? `/cbdc/alerts?scenario_run_id=${r.id}` : `/current-money/alerts?scenario_run_id=${r.id}`)}
                          className="text-xs font-mono"
                        >
                          <BellRing size={13} className="mr-1" />
                          <span>View Alerts ({r.alert_count || 0})</span>
                        </Button>
                      </div>
                    </div>

                    <div className="grid grid-cols-3 gap-2 text-xs font-mono">
                      <div className="p-2 bg-background rounded border border-muted-border">
                        <div className="text-[10px] text-muted-dark uppercase">Transactions</div>
                        <div className="text-sm font-bold text-warm-white">{r.transaction_count || 0}</div>
                      </div>
                      <div className="p-2 bg-background rounded border border-muted-border">
                        <div className="text-[10px] text-muted-dark uppercase">Alerts Generated</div>
                        <div className="text-sm font-bold text-status-warning">{r.alert_count || 0}</div>
                      </div>
                      <div className="p-2 bg-background rounded border border-muted-border">
                        <div className="text-[10px] text-muted-dark uppercase">Cases Created</div>
                        <div className="text-sm font-bold text-amber">{r.case_count || 0}</div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </Card>
        </div>
      </div>
    </div>
  );
};

