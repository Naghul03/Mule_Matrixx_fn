import React, { useState, useEffect, useCallback } from 'react';
import {
  BarChart3,
  Play,
  ShieldCheck,
  RefreshCw,
  Award,
} from 'lucide-react';
import { api } from '../services/api';
import { EvaluationRunData, ScenarioRunResponse } from '../types';

export const EvaluationPage: React.FC = () => {
  const [runs, setRuns] = useState<EvaluationRunData[]>([]);
  const [scenarioRuns, setScenarioRuns] = useState<ScenarioRunResponse[]>([]);
  const [selectedScenarioRunId, setSelectedScenarioRunId] = useState<string>('');
  const [selectedEvalRun, setSelectedEvalRun] = useState<EvaluationRunData | null>(null);
  const [loading, setLoading] = useState<boolean>(true);
  const [evaluating, setEvaluating] = useState<boolean>(false);
  const [error, setError] = useState<string | null>(null);
  const [successMsg, setSuccessMsg] = useState<string | null>(null);

  const loadData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const [evalHistory, scenarios] = await Promise.all([
        api.listEvaluationRuns(),
        api.listScenarioRuns(undefined, 20),
      ]);
      setRuns(evalHistory);
      setScenarioRuns(scenarios);

      if (evalHistory.length > 0) {
        setSelectedEvalRun(evalHistory[0]);
      }
      if (scenarios.length > 0 && !selectedScenarioRunId) {
        setSelectedScenarioRunId(scenarios[0].id);
      }
    } catch (err) {
      console.error('Failed to load evaluation data:', err);
      setError((err as Error).message);
    } finally {
      setLoading(false);
    }
  }, [selectedScenarioRunId]);

  useEffect(() => {
    loadData();
  }, [loadData]);

  const handleRunEvaluation = async () => {
    if (!selectedScenarioRunId) return;
    setEvaluating(true);
    setError(null);
    setSuccessMsg(null);
    try {
      const result = await api.runEvaluation({
        scenario_run_id: selectedScenarioRunId,
        seed_type: 'FIXED_REPRODUCIBLE',
      });
      setSuccessMsg('Evaluation run completed against isolated ground-truth labels.');
      await loadData();
      setSelectedEvalRun(result);
    } catch (err) {
      console.error('Failed to run evaluation:', err);
      setError((err as Error).message || 'Evaluation failed.');
    } finally {
      setEvaluating(false);
    }
  };

  return (
    <div className="space-y-6">
      {/* Page Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-muted-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono tracking-wide text-warm-white">
              Evaluation & Benchmark Suite
            </h1>
            <span className="text-[10px] font-mono uppercase bg-amber/15 text-amber px-2 py-0.5 rounded border border-amber/30">
              Module 7
            </span>
          </div>
          <p className="text-xs text-muted-gray mt-1">
            Empirical benchmarking of the multi-signal detector against a single-threshold baseline using isolated ground truth.
          </p>
        </div>

        {/* Action Button */}
        <div className="flex items-center gap-3">
          <select
            value={selectedScenarioRunId}
            onChange={(e) => setSelectedScenarioRunId(e.target.value)}
            className="bg-background-secondary border border-muted-border rounded px-3 py-1.5 text-xs font-mono text-warm-white focus:outline-none focus:border-amber"
          >
            {scenarioRuns.map((r) => (
              <option key={r.id} value={r.id}>
                {r.scenario_name || r.scenario_identifier} (Seed: {r.seed})
              </option>
            ))}
          </select>
          <button
            onClick={handleRunEvaluation}
            disabled={evaluating || !selectedScenarioRunId}
            className="flex items-center gap-2 px-3 py-1.5 bg-earth hover:bg-earth/80 text-warm-white text-xs font-mono font-medium rounded border border-amber/40 transition-colors disabled:opacity-50"
          >
            {evaluating ? (
              <RefreshCw size={13} className="animate-spin text-amber" />
            ) : (
              <Play size={13} className="text-amber" />
            )}
            <span>Execute Benchmark</span>
          </button>
        </div>
      </div>

      {/* Ground Truth Isolation Banner */}
      <div className="p-4 bg-background-secondary border border-muted-border rounded-lg flex items-start gap-3">
        <ShieldCheck size={20} className="text-emerald-400 mt-0.5 flex-shrink-0" />
        <div className="text-xs font-mono">
          <span className="font-bold text-warm-white">Strict Ground-Truth Isolation Architecture</span>
          <p className="text-muted-gray mt-0.5">
            Mule Matrix strictly decouples synthetic scenario generation from detection inference. Ground truth labels are stored in an isolated table and never joined or queried by the detection engine. Only this evaluation module queries ground truth post-prediction to compute genuine precision, recall, and F1 benchmarks.
          </p>
        </div>
      </div>

      {/* Messages */}
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-500/40 rounded text-xs text-red-200 font-mono">
          {error}
        </div>
      )}
      {successMsg && (
        <div className="p-3 bg-emerald-950/40 border border-emerald-500/40 rounded text-xs text-emerald-200 font-mono">
          {successMsg}
        </div>
      )}

      {/* Detailed View */}
      {loading ? (
        <div className="p-12 bg-background-secondary border border-muted-border rounded-lg text-center text-amber font-mono text-xs animate-pulse">
          Loading benchmark runs and evaluation metrics...
        </div>
      ) : selectedEvalRun ? (
        <div className="space-y-6">
          {/* Metadata bar */}
          <div className="flex flex-wrap items-center justify-between p-3.5 bg-background-secondary border border-muted-border rounded text-xs font-mono">
            <div className="flex items-center gap-4">
              <div>
                <span className="text-muted-dark uppercase text-[10px] block">Evaluation Run ID</span>
                <span className="text-warm-white font-bold">{selectedEvalRun.id}</span>
              </div>
              <div>
                <span className="text-muted-dark uppercase text-[10px] block">Detector Engine</span>
                <span className="text-amber">{selectedEvalRun.detector_version}</span>
              </div>
              <div>
                <span className="text-muted-dark uppercase text-[10px] block">Baseline Benchmark</span>
                <span className="text-muted-gray">{selectedEvalRun.baseline_version}</span>
              </div>
            </div>
            <div>
              <span className="text-muted-dark uppercase text-[10px] block">Evaluated At</span>
              <span className="text-warm-white">{new Date(selectedEvalRun.created_at).toUTCString()}</span>
            </div>
          </div>

          {/* Side by side comparison cards */}
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {/* Mule Matrix Multi-Signal Detector */}
            <div className="bg-background-secondary border-2 border-amber/40 rounded-lg p-5">
              <div className="flex items-center justify-between pb-3 border-b border-muted-border mb-4">
                <div className="flex items-center gap-2">
                  <Award size={18} className="text-amber" />
                  <h3 className="font-mono font-bold text-warm-white text-sm">
                    Mule Matrix Multi-Signal Engine
                  </h3>
                </div>
                <span className="text-[10px] font-mono uppercase bg-amber/15 text-amber px-2 py-0.5 rounded border border-amber/30">
                  Target Model
                </span>
              </div>

              {/* Metrics Grid */}
              <div className="grid grid-cols-3 gap-3 mb-6">
                <div className="p-3 bg-background rounded border border-muted-border text-center">
                  <div className="text-[10px] uppercase font-mono text-muted-dark">Precision</div>
                  <div className="text-xl font-mono font-bold text-warm-white mt-1">
                    {(selectedEvalRun.metrics.precision * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-muted-gray mt-0.5">TP / (TP + FP)</div>
                </div>
                <div className="p-3 bg-background rounded border border-muted-border text-center">
                  <div className="text-[10px] uppercase font-mono text-muted-dark">Recall</div>
                  <div className="text-xl font-mono font-bold text-warm-white mt-1">
                    {(selectedEvalRun.metrics.recall * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-muted-gray mt-0.5">TP / (TP + FN)</div>
                </div>
                <div className="p-3 bg-background rounded border border-muted-border text-center">
                  <div className="text-[10px] uppercase font-mono text-muted-dark">F1-Score</div>
                  <div className="text-xl font-mono font-bold text-amber mt-1">
                    {selectedEvalRun.metrics.f1_score.toFixed(3)}
                  </div>
                  <div className="text-[10px] text-muted-gray mt-0.5">Harmonic Mean</div>
                </div>
              </div>

              {/* 2x2 Confusion Matrix */}
              <div>
                <h4 className="text-xs font-mono font-semibold text-muted-gray uppercase mb-2">
                  Empirical Confusion Matrix
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-3 bg-emerald-950/20 border border-emerald-500/30 rounded flex justify-between items-center">
                    <div>
                      <div className="text-[10px] text-emerald-400 font-semibold uppercase">True Positives (TP)</div>
                      <div className="text-[10px] text-muted-gray">Correctly flagged mules</div>
                    </div>
                    <span className="text-lg font-bold text-emerald-300">
                      {selectedEvalRun.metrics.true_positives}
                    </span>
                  </div>

                  <div className="p-3 bg-red-950/20 border border-red-500/30 rounded flex justify-between items-center">
                    <div>
                      <div className="text-[10px] text-red-400 font-semibold uppercase">False Positives (FP)</div>
                      <div className="text-[10px] text-muted-gray">Legit accounts flagged</div>
                    </div>
                    <span className="text-lg font-bold text-red-300">
                      {selectedEvalRun.metrics.false_positives}
                    </span>
                  </div>

                  <div className="p-3 bg-amber/10 border border-amber/30 rounded flex justify-between items-center">
                    <div>
                      <div className="text-[10px] text-amber font-semibold uppercase">False Negatives (FN)</div>
                      <div className="text-[10px] text-muted-gray">Mules overlooked</div>
                    </div>
                    <span className="text-lg font-bold text-amber">
                      {selectedEvalRun.metrics.false_negatives}
                    </span>
                  </div>

                  <div className="p-3 bg-background rounded border border-muted-border flex justify-between items-center">
                    <div>
                      <div className="text-[10px] text-muted-gray font-semibold uppercase">True Negatives (TN)</div>
                      <div className="text-[10px] text-muted-gray">Legit accounts cleared</div>
                    </div>
                    <span className="text-lg font-bold text-warm-white">
                      {selectedEvalRun.metrics.true_negatives}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            {/* Baseline Detector */}
            <div className="bg-background-secondary border border-muted-border rounded-lg p-5">
              <div className="flex items-center justify-between pb-3 border-b border-muted-border mb-4">
                <div className="flex items-center gap-2">
                  <BarChart3 size={18} className="text-muted-gray" />
                  <h3 className="font-mono font-bold text-warm-white text-sm">
                    Single-Transaction Baseline
                  </h3>
                </div>
                <span className="text-[10px] font-mono uppercase bg-muted-border/40 text-muted-gray px-2 py-0.5 rounded border border-muted-border">
                  Naive Benchmark
                </span>
              </div>

              {/* Baseline Metrics Grid */}
              <div className="grid grid-cols-3 gap-3 mb-6">
                <div className="p-3 bg-background rounded border border-muted-border text-center">
                  <div className="text-[10px] uppercase font-mono text-muted-dark">Precision</div>
                  <div className="text-xl font-mono font-bold text-warm-white mt-1">
                    {(selectedEvalRun.baseline_metrics.precision * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-muted-gray mt-0.5">TP / (TP + FP)</div>
                </div>
                <div className="p-3 bg-background rounded border border-muted-border text-center">
                  <div className="text-[10px] uppercase font-mono text-muted-dark">Recall</div>
                  <div className="text-xl font-mono font-bold text-warm-white mt-1">
                    {(selectedEvalRun.baseline_metrics.recall * 100).toFixed(1)}%
                  </div>
                  <div className="text-[10px] text-muted-gray mt-0.5">TP / (TP + FN)</div>
                </div>
                <div className="p-3 bg-background rounded border border-muted-border text-center">
                  <div className="text-[10px] uppercase font-mono text-muted-dark">F1-Score</div>
                  <div className="text-xl font-mono font-bold text-muted-gray mt-1">
                    {selectedEvalRun.baseline_metrics.f1_score.toFixed(3)}
                  </div>
                  <div className="text-[10px] text-muted-gray mt-0.5">Harmonic Mean</div>
                </div>
              </div>

              {/* Baseline Confusion Matrix */}
              <div>
                <h4 className="text-xs font-mono font-semibold text-muted-gray uppercase mb-2">
                  Baseline Confusion Matrix
                </h4>
                <div className="grid grid-cols-2 gap-2 text-xs font-mono">
                  <div className="p-3 bg-background rounded border border-muted-border flex justify-between items-center">
                    <div>
                      <div className="text-[10px] text-emerald-400 font-semibold uppercase">True Positives</div>
                      <div className="text-[10px] text-muted-gray">Correctly flagged</div>
                    </div>
                    <span className="text-lg font-bold text-warm-white">
                      {selectedEvalRun.baseline_metrics.true_positives}
                    </span>
                  </div>

                  <div className="p-3 bg-background rounded border border-muted-border flex justify-between items-center">
                    <div>
                      <div className="text-[10px] text-red-400 font-semibold uppercase">False Positives</div>
                      <div className="text-[10px] text-muted-gray">Legit flagged</div>
                    </div>
                    <span className="text-lg font-bold text-warm-white">
                      {selectedEvalRun.baseline_metrics.false_positives}
                    </span>
                  </div>

                  <div className="p-3 bg-background rounded border border-muted-border flex justify-between items-center">
                    <div>
                      <div className="text-[10px] text-amber font-semibold uppercase">False Negatives</div>
                      <div className="text-[10px] text-muted-gray">Missed</div>
                    </div>
                    <span className="text-lg font-bold text-warm-white">
                      {selectedEvalRun.baseline_metrics.false_negatives}
                    </span>
                  </div>

                  <div className="p-3 bg-background rounded border border-muted-border flex justify-between items-center">
                    <div>
                      <div className="text-[10px] text-muted-gray font-semibold uppercase">True Negatives</div>
                      <div className="text-[10px] text-muted-gray">Cleared</div>
                    </div>
                    <span className="text-lg font-bold text-warm-white">
                      {selectedEvalRun.baseline_metrics.true_negatives}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      ) : (
        <div className="p-12 bg-background-secondary border border-muted-border rounded-lg text-center text-muted-gray font-mono">
          <BarChart3 size={36} className="mx-auto text-muted-dark mb-3" />
          <p className="text-warm-white font-medium">No Evaluation Benchmark Runs Yet</p>
          <p className="text-xs text-muted-gray mt-1 max-w-md mx-auto">
            Select a generated scenario run above and click &quot;Execute Benchmark&quot; to test detector accuracy against isolated ground truth.
          </p>
        </div>
      )}

      {/* Historical Evaluation Runs Table */}
      {runs.length > 0 && (
        <div className="bg-background-secondary border border-muted-border rounded-lg p-5">
          <h3 className="text-xs font-mono uppercase tracking-wider text-muted-gray font-semibold mb-3">
            Benchmark Run Registry ({runs.length} Runs)
          </h3>
          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-muted-border text-muted-dark uppercase text-[10px]">
                  <th className="pb-2">Run ID</th>
                  <th className="pb-2">Detector F1</th>
                  <th className="pb-2">Detector Precision</th>
                  <th className="pb-2">Detector Recall</th>
                  <th className="pb-2">Baseline F1</th>
                  <th className="pb-2">Evaluated Accounts</th>
                  <th className="pb-2">Timestamp</th>
                  <th className="pb-2 text-right">Action</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-muted-border/50">
                {runs.map((r) => (
                  <tr
                    key={r.id}
                    className={`hover:bg-background transition-colors ${
                      selectedEvalRun?.id === r.id ? 'bg-amber/10' : ''
                    }`}
                  >
                    <td className="py-2.5 font-bold text-warm-white">{r.id.slice(0, 8)}...</td>
                    <td className="py-2.5 text-amber font-bold">{r.metrics.f1_score.toFixed(3)}</td>
                    <td className="py-2.5">{(r.metrics.precision * 100).toFixed(1)}%</td>
                    <td className="py-2.5">{(r.metrics.recall * 100).toFixed(1)}%</td>
                    <td className="py-2.5 text-muted-gray">{r.baseline_metrics.f1_score.toFixed(3)}</td>
                    <td className="py-2.5 text-warm-white">{r.metrics.total_evaluated}</td>
                    <td className="py-2.5 text-muted-gray">{new Date(r.created_at).toLocaleTimeString()}</td>
                    <td className="py-2.5 text-right">
                      <button
                        onClick={() => setSelectedEvalRun(r)}
                        className="px-2 py-1 bg-background hover:bg-earth/40 text-warm-white text-[10px] rounded border border-muted-border"
                      >
                        Inspect
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
