import React, { useState, useEffect, useRef, useCallback } from 'react';
import cytoscape, { Core, EventObject } from 'cytoscape';
import {
  GitGraph,
  ZoomIn,
  ZoomOut,
  Maximize2,
  RotateCcw,
  ShieldAlert,
  Layers,
  ArrowRight,
  Info,
  CheckCircle,
  Filter,
} from 'lucide-react';
import { api } from '../services/api';
import {
  CytoscapeGraphData,
  CytoscapeNodeData,
  CytoscapeEdgeData,
  KingpinRankingItem,
  MuleRankingItem,
  FIFOAttributionItem,
  ScenarioRunResponse,
} from '../types';

export const InvestigationPage: React.FC = () => {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<Core | null>(null);

  const [scenarioRuns, setScenarioRuns] = useState<ScenarioRunResponse[]>([]);
  const [selectedRunId, setSelectedRunId] = useState<string>('');
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // Graph data & inspection state
  const [graphData, setGraphData] = useState<CytoscapeGraphData | null>(null);
  const [selectedNode, setSelectedNode] = useState<CytoscapeNodeData | null>(null);
  const [selectedEdge, setSelectedEdge] = useState<CytoscapeEdgeData | null>(null);

  // Analytics data
  const [kingpins, setKingpins] = useState<KingpinRankingItem[]>([]);
  const [mules, setMules] = useState<MuleRankingItem[]>([]);
  const [fifoAttributions, setFifoAttributions] = useState<FIFOAttributionItem[]>([]);
  const [activeTab, setActiveTab] = useState<'graph' | 'rankings' | 'fifo'>('graph');

  // Load available scenario runs
  const loadScenarioRuns = useCallback(async () => {
    try {
      const runs = await api.listScenarioRuns('current_money', 20);
      setScenarioRuns(runs);
      if (runs.length > 0 && !selectedRunId) {
        setSelectedRunId(runs[0].id);
      }
    } catch (err) {
      console.error('Failed to load runs:', err);
    }
  }, [selectedRunId]);

  useEffect(() => {
    loadScenarioRuns();
  }, [loadScenarioRuns]);

  // Load graph, rankings, and FIFO attribution when selectedRunId changes
  const loadInvestigationData = useCallback(async (runId: string) => {
    if (!runId) return;
    setLoading(true);
    setError(null);
    setSelectedNode(null);
    setSelectedEdge(null);

    try {
      const [gData, rData, fData] = await Promise.all([
        api.getInvestigationGraph({ scenario_run_id: runId }),
        api.getRankings(runId),
        api.getFIFOAttribution(runId),
      ]);

      setGraphData(gData);
      setKingpins(rData.kingpins || []);
      setMules(rData.mules || []);
      setFifoAttributions(fData || []);
    } catch (err) {
      console.error('Failed to load investigation data:', err);
      setError((err as Error).message || 'Failed to load investigation graph data.');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (selectedRunId) {
      loadInvestigationData(selectedRunId);
    }
  }, [selectedRunId, loadInvestigationData]);

  // Initialize and update Cytoscape canvas
  useEffect(() => {
    if (!containerRef.current || !graphData) return;

    // Destroy existing instance if any
    if (cyRef.current) {
      cyRef.current.destroy();
    }

    const elements = [
      ...graphData.nodes.map((n) => ({
        group: 'nodes' as const,
        data: {
          id: n.data.id,
          label: n.data.label || n.data.accountRef,
          accountRef: n.data.accountRef,
          bankCode: n.data.bankCode,
          bankName: n.data.bankName,
          riskScore: n.data.riskScore,
          riskBand: n.data.riskBand,
          totalIn: n.data.totalIn,
          totalOut: n.data.totalOut,
        },
      })),
      ...graphData.edges.map((e) => ({
        group: 'edges' as const,
        data: {
          id: e.data.id,
          source: e.data.source,
          target: e.data.target,
          amount: e.data.amount,
          currency: e.data.currency,
          timestamp: e.data.timestamp,
          reference: e.data.reference,
          evidenceType: e.data.evidenceType,
          normalizedType: e.data.normalizedType,
          status: e.data.status,
          label: `$${Number(e.data.amount).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`,
        },
      })),
    ];

    const cy = cytoscape({
      container: containerRef.current,
      elements,
      style: [
        {
          selector: 'node',
          style: {
            label: 'data(label)',
            color: '#F5F5F0',
            'font-family': 'monospace',
            'font-size': '11px',
            'text-valign': 'bottom',
            'text-margin-y': 6,
            'background-color': '#6C5636',
            width: 36,
            height: 36,
            'border-width': 2,
            'border-color': '#B99D73',
          },
        },
        {
          selector: 'node[riskBand = "HIGH"]',
          style: {
            'background-color': '#DC2626',
            'border-color': '#EF4444',
            'border-width': 3,
            width: 44,
            height: 44,
          },
        },
        {
          selector: 'node[riskBand = "MEDIUM"]',
          style: {
            'background-color': '#D97706',
            'border-color': '#F59E0B',
            'border-width': 2,
            width: 38,
            height: 38,
          },
        },
        {
          selector: 'node[riskBand = "LOW"]',
          style: {
            'background-color': '#059669',
            'border-color': '#10B981',
            'border-width': 1.5,
          },
        },
        {
          selector: 'node:selected',
          style: {
            'border-color': '#FFFFFF',
            'border-width': 4,
          },
        },
        {
          selector: 'edge',
          style: {
            width: 2.5,
            'line-color': '#B99D73',
            'target-arrow-color': '#B99D73',
            'target-arrow-shape': 'triangle',
            'curve-style': 'bezier',
            label: 'data(label)',
            color: '#B99D73',
            'font-family': 'monospace',
            'font-size': '9px',
            'text-rotation': 'autorotate',
            'text-background-opacity': 0.8,
            'text-background-color': '#090907',
            'text-background-padding': '2px',
          },
        },
        {
          selector: 'edge[evidenceType = "HISTORICAL"]',
          style: {
            'line-style': 'dashed',
            'line-dash-pattern': [6, 4],
            'line-color': '#8B7355',
            'target-arrow-color': '#8B7355',
            opacity: 0.85,
          },
        },
        {
          selector: 'edge:selected',
          style: {
            width: 4,
            'line-color': '#F5F5F0',
            'target-arrow-color': '#F5F5F0',
          },
        },
      ],
      layout: {
        name: 'cose',
        animate: false,
        padding: 50,
        nodeRepulsion: () => 450000,
        idealEdgeLength: () => 120,
      },
    });

    cy.on('tap', 'node', (evt: EventObject) => {
      const node = evt.target;
      setSelectedNode(node.data());
      setSelectedEdge(null);
    });

    cy.on('tap', 'edge', (evt: EventObject) => {
      const edge = evt.target;
      setSelectedEdge(edge.data());
      setSelectedNode(null);
    });

    cy.on('tap', (evt: EventObject) => {
      if (evt.target === cy) {
        setSelectedNode(null);
        setSelectedEdge(null);
      }
    });

    cyRef.current = cy;

    return () => {
      cy.destroy();
    };
  }, [graphData]);

  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.25);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit(undefined, 40);
  const handleResetLayout = () => {
    cyRef.current?.layout({ name: 'cose', animate: true, padding: 50 }).run();
  };

  return (
    <div className="space-y-6">
      {/* Top Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 border-b border-muted-border pb-5">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="text-xl font-bold font-mono tracking-wide text-warm-white">
              Transaction Investigation Canvas
            </h1>
            <span className="text-[10px] font-mono uppercase bg-amber/15 text-amber px-2 py-0.5 rounded border border-amber/30">
              Module 5
            </span>
          </div>
          <p className="text-xs text-muted-gray mt-1">
            Multi-hop graph visualization distinguishing direct from historical relationships, identifying kingpins, and tracking FIFO attribution.
          </p>
        </div>

        {/* Run Selector */}
        <div className="flex items-center gap-3">
          <label className="text-xs font-mono text-muted-gray flex items-center gap-1.5">
            <Filter size={13} className="text-amber" />
            <span>Scenario Run:</span>
          </label>
          <select
            value={selectedRunId}
            onChange={(e) => setSelectedRunId(e.target.value)}
            className="bg-background-secondary border border-muted-border rounded px-3 py-1.5 text-xs font-mono text-warm-white focus:outline-none focus:border-amber"
          >
            {scenarioRuns.map((r) => (
              <option key={r.id} value={r.id}>
                {r.scenario_name || r.scenario_identifier} (Seed: {r.seed}) — {new Date(r.created_at).toLocaleTimeString()}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* Navigation Tabs */}
      <div className="flex border-b border-muted-border gap-2">
        <button
          onClick={() => setActiveTab('graph')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-mono border-b-2 transition-all ${
            activeTab === 'graph'
              ? 'border-amber text-amber font-semibold bg-amber/5'
              : 'border-transparent text-muted-gray hover:text-warm-white'
          }`}
        >
          <GitGraph size={14} />
          <span>Interactive Canvas ({graphData?.nodes.length || 0} Nodes)</span>
        </button>
        <button
          onClick={() => setActiveTab('rankings')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-mono border-b-2 transition-all ${
            activeTab === 'rankings'
              ? 'border-amber text-amber font-semibold bg-amber/5'
              : 'border-transparent text-muted-gray hover:text-warm-white'
          }`}
        >
          <ShieldAlert size={14} />
          <span>Network Rankings (Kingpins & Mules)</span>
        </button>
        <button
          onClick={() => setActiveTab('fifo')}
          className={`flex items-center gap-2 px-4 py-2 text-xs font-mono border-b-2 transition-all ${
            activeTab === 'fifo'
              ? 'border-amber text-amber font-semibold bg-amber/5'
              : 'border-transparent text-muted-gray hover:text-warm-white'
          }`}
        >
          <Layers size={14} />
          <span>FIFO Fund Attribution ({fifoAttributions.length} Traces)</span>
        </button>
      </div>

      {/* Error / Loading */}
      {error && (
        <div className="p-3 bg-red-950/40 border border-red-500/40 rounded text-xs text-red-200 font-mono">
          {error}
        </div>
      )}

      {/* Tab 1: Graph Canvas */}
      {activeTab === 'graph' && (
        <div className="grid grid-cols-1 lg:grid-cols-4 gap-4">
          <div className="lg:col-span-3 bg-background-secondary border border-muted-border rounded-lg relative overflow-hidden flex flex-col h-[620px]">
            {/* Toolbar */}
            <div className="p-3 border-b border-muted-border bg-background/60 flex items-center justify-between z-10">
              <div className="flex items-center gap-2">
                <button
                  onClick={handleZoomIn}
                  className="p-1.5 bg-background-secondary hover:bg-background-hover border border-muted-border rounded text-muted-gray hover:text-warm-white transition-colors"
                  title="Zoom In"
                >
                  <ZoomIn size={14} />
                </button>
                <button
                  onClick={handleZoomOut}
                  className="p-1.5 bg-background-secondary hover:bg-background-hover border border-muted-border rounded text-muted-gray hover:text-warm-white transition-colors"
                  title="Zoom Out"
                >
                  <ZoomOut size={14} />
                </button>
                <button
                  onClick={handleFit}
                  className="p-1.5 bg-background-secondary hover:bg-background-hover border border-muted-border rounded text-muted-gray hover:text-warm-white transition-colors"
                  title="Fit to Canvas"
                >
                  <Maximize2 size={14} />
                </button>
                <button
                  onClick={handleResetLayout}
                  className="p-1.5 bg-background-secondary hover:bg-background-hover border border-muted-border rounded text-muted-gray hover:text-warm-white transition-colors"
                  title="Recalculate Layout"
                >
                  <RotateCcw size={14} />
                </button>
              </div>

              {/* Legend */}
              <div className="flex items-center gap-4 text-[10px] font-mono text-muted-gray">
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-red-500 inline-block"></span>
                  <span>High Risk</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-amber-500 inline-block"></span>
                  <span>Medium Risk</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block"></span>
                  <span>Decoy / Legitimate</span>
                </div>
                <div className="flex items-center gap-1.5 border-l border-muted-border pl-3">
                  <span className="w-4 h-0.5 bg-amber inline-block"></span>
                  <span>Direct Transfer</span>
                </div>
                <div className="flex items-center gap-1.5">
                  <span className="w-4 h-0.5 border-b border-dashed border-muted-gray inline-block"></span>
                  <span>Historical</span>
                </div>
              </div>
            </div>

            {/* Canvas Container */}
            <div ref={containerRef} className="flex-1 w-full h-full bg-[#090907]" />

            {loading && (
              <div className="absolute inset-0 bg-background/70 backdrop-blur-sm flex items-center justify-center">
                <span className="text-xs font-mono text-amber animate-pulse">Rendering investigation graph...</span>
              </div>
            )}
          </div>

          {/* Inspection Drawer */}
          <div className="bg-background-secondary border border-muted-border rounded-lg p-4 flex flex-col h-[620px] overflow-y-auto">
            <h3 className="text-xs font-mono uppercase tracking-wider text-muted-gray font-semibold mb-3 pb-2 border-b border-muted-border">
              Inspection Dossier
            </h3>

            {selectedNode && (
              <div className="space-y-4">
                <div className="p-3 bg-background rounded border border-muted-border">
                  <div className="text-[10px] uppercase font-mono text-muted-dark font-semibold">Account Label</div>
                  <div className="text-sm font-mono font-bold text-warm-white mt-0.5">
                    {selectedNode.label}
                  </div>
                  <div className="text-xs font-mono text-amber mt-1">{selectedNode.accountRef}</div>
                </div>

                <div className="grid grid-cols-2 gap-2">
                  <div className="p-2.5 bg-background rounded border border-muted-border">
                    <div className="text-[10px] font-mono text-muted-dark uppercase">Bank</div>
                    <div className="text-xs font-mono font-semibold text-warm-white mt-0.5">{selectedNode.bankCode}</div>
                    <div className="text-[10px] text-muted-gray">{selectedNode.bankName}</div>
                  </div>
                  <div className="p-2.5 bg-background rounded border border-muted-border">
                    <div className="text-[10px] font-mono text-muted-dark uppercase">Risk Profile</div>
                    <div className={`text-xs font-mono font-bold mt-0.5 ${
                      selectedNode.riskBand === 'HIGH' ? 'text-red-400' :
                      selectedNode.riskBand === 'MEDIUM' ? 'text-amber' : 'text-emerald-400'
                    }`}>
                      {selectedNode.riskScore.toFixed(1)} / 100
                    </div>
                    <div className="text-[10px] font-mono text-muted-gray">Band: {selectedNode.riskBand}</div>
                  </div>
                </div>

                <div className="p-3 bg-background rounded border border-muted-border space-y-2">
                  <div className="text-[10px] uppercase font-mono text-muted-dark font-semibold">Observed Fund Flows</div>
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-muted-gray">Total Inflow:</span>
                    <span className="text-emerald-400 font-semibold">
                      ${Number(selectedNode.totalIn).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs font-mono">
                    <span className="text-muted-gray">Total Outflow:</span>
                    <span className="text-red-400 font-semibold">
                      ${Number(selectedNode.totalOut).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                  <div className="flex justify-between text-xs font-mono border-t border-muted-border/60 pt-1.5">
                    <span className="text-muted-gray">Net Retained:</span>
                    <span className="text-warm-white font-semibold">
                      ${(Number(selectedNode.totalIn) - Number(selectedNode.totalOut)).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                    </span>
                  </div>
                </div>

                {selectedNode.riskBand === 'HIGH' && (
                  <div className="p-3 bg-red-950/30 border border-red-500/30 rounded text-[11px] font-mono text-red-300">
                    <div className="flex items-center gap-1.5 font-bold mb-1">
                      <ShieldAlert size={13} className="text-red-400" />
                      <span>Elevated Money Mule Indicator</span>
                    </div>
                    Account exhibits rapid multi-hop dispersion, high pass-through ratio, or central betweenness in this run.
                  </div>
                )}
              </div>
            )}

            {selectedEdge && (
              <div className="space-y-4">
                <div className="p-3 bg-background rounded border border-muted-border">
                  <div className="text-[10px] uppercase font-mono text-muted-dark font-semibold">Transaction Reference</div>
                  <div className="text-xs font-mono font-bold text-amber mt-0.5 break-all">
                    {selectedEdge.reference}
                  </div>
                  <div className="flex items-center gap-1.5 mt-2">
                    <span className={`text-[10px] font-mono px-2 py-0.5 rounded border uppercase ${
                      selectedEdge.evidenceType === 'HISTORICAL'
                        ? 'bg-amber/15 text-amber border-amber/30'
                        : 'bg-blue-500/15 text-blue-400 border-blue-500/30'
                    }`}>
                      {selectedEdge.evidenceType} EDGE
                    </span>
                    <span className="text-[10px] font-mono text-muted-gray">{selectedEdge.normalizedType}</span>
                  </div>
                </div>

                <div className="p-3 bg-background rounded border border-muted-border">
                  <div className="text-[10px] uppercase font-mono text-muted-dark font-semibold">Transferred Sum</div>
                  <div className="text-lg font-mono font-bold text-warm-white mt-1">
                    ${Number(selectedEdge.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })} {selectedEdge.currency}
                  </div>
                  <div className="text-[10px] font-mono text-muted-gray mt-1">
                    Timestamp: {new Date(selectedEdge.timestamp).toUTCString()}
                  </div>
                </div>

                <div className="p-3 bg-background rounded border border-muted-border">
                  <div className="text-[10px] uppercase font-mono text-muted-dark font-semibold mb-2">Transfer Direction</div>
                  <div className="text-xs font-mono space-y-1.5">
                    <div className="text-muted-gray">Source Node: <span className="text-warm-white">{selectedEdge.source}</span></div>
                    <div className="flex items-center justify-center text-amber py-1">
                      <ArrowRight size={14} />
                    </div>
                    <div className="text-muted-gray">Destination Node: <span className="text-warm-white">{selectedEdge.target}</span></div>
                  </div>
                </div>

                {selectedEdge.evidenceType === 'HISTORICAL' && (
                  <div className="p-3 bg-amber/10 border border-amber/30 rounded text-[11px] font-mono text-amber">
                    <div className="flex items-center gap-1.5 font-bold mb-1">
                      <Info size={13} />
                      <span>Historical Relationship</span>
                    </div>
                    This edge represents an established counterparty relationship prior to the immediate laundering incident.
                  </div>
                )}
              </div>
            )}

            {!selectedNode && !selectedEdge && (
              <div className="flex-1 flex flex-col items-center justify-center text-center p-6 text-muted-gray">
                <GitGraph size={32} className="text-muted-dark mb-3 stroke-[1.5]" />
                <p className="text-xs font-mono text-warm-white font-medium">No Element Selected</p>
                <p className="text-[11px] text-muted-dark mt-1 font-mono">
                  Click on any account node or transaction edge on the canvas to inspect its parameters, flow attribution, and bank metadata.
                </p>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Tab 2: Network Rankings */}
      {activeTab === 'rankings' && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Kingpins */}
          <div className="bg-background-secondary border border-muted-border rounded-lg p-5">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-muted-border">
              <div>
                <h3 className="text-sm font-mono font-bold text-warm-white flex items-center gap-2">
                  <ShieldAlert size={16} className="text-amber" />
                  <span>Potential Kingpin / Coordinating Accounts</span>
                </h3>
                <p className="text-[11px] text-muted-gray mt-0.5">
                  Ranked by NetworkX betweenness centrality, degree concentration, and fund accumulation.
                </p>
              </div>
              <span className="text-xs font-mono text-amber bg-amber/10 px-2 py-0.5 rounded border border-amber/20">
                {kingpins.length} Ranked
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-muted-border text-muted-dark uppercase text-[10px]">
                    <th className="pb-2">Rank</th>
                    <th className="pb-2">Account / Alias</th>
                    <th className="pb-2">Score</th>
                    <th className="pb-2">Centrality</th>
                    <th className="pb-2">Received</th>
                    <th className="pb-2">Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-muted-border/50">
                  {kingpins.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-muted-gray">
                        No coordinating accounts identified for this scenario run.
                      </td>
                    </tr>
                  ) : (
                    kingpins.map((k) => (
                      <tr
                        key={k.accountId}
                        className={`hover:bg-background transition-colors ${
                          k.rank === 1 ? 'bg-amber/10 border-l-2 border-amber' : ''
                        }`}
                      >
                        <td className="py-2.5 font-bold text-warm-white">
                          {k.rank === 1 ? '🥇 #1' : `#${k.rank}`}
                        </td>
                        <td className="py-2.5">
                          <div className="font-semibold text-warm-white">{k.alias || k.accountRef}</div>
                          <div className="text-[10px] text-muted-gray">{k.accountRef}</div>
                        </td>
                        <td className="py-2.5 text-amber font-semibold">{k.kingpinScore.toFixed(1)}</td>
                        <td className="py-2.5 text-muted-gray">{k.betweennessCentrality.toFixed(4)}</td>
                        <td className="py-2.5 text-emerald-400">
                          ${Number(k.totalReceived).toLocaleString('en-US', { minimumFractionDigits: 0 })}
                        </td>
                        <td className="py-2.5 text-[10px] text-muted-gray max-w-[180px] truncate" title={k.rationale}>
                          {k.rationale}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>

          {/* Mules */}
          <div className="bg-background-secondary border border-muted-border rounded-lg p-5">
            <div className="flex items-center justify-between mb-4 pb-3 border-b border-muted-border">
              <div>
                <h3 className="text-sm font-mono font-bold text-warm-white flex items-center gap-2">
                  <Layers size={16} className="text-red-400" />
                  <span>Identified Money Mules</span>
                </h3>
                <p className="text-[11px] text-muted-gray mt-0.5">
                  Ranked by pass-through velocity, dispersion ratios, and rapid inbound/outbound cycling.
                </p>
              </div>
              <span className="text-xs font-mono text-red-400 bg-red-500/10 px-2 py-0.5 rounded border border-red-500/20">
                {mules.length} Identified
              </span>
            </div>

            <div className="overflow-x-auto">
              <table className="w-full text-left text-xs font-mono">
                <thead>
                  <tr className="border-b border-muted-border text-muted-dark uppercase text-[10px]">
                    <th className="pb-2">Rank</th>
                    <th className="pb-2">Account / Alias</th>
                    <th className="pb-2">Mule Score</th>
                    <th className="pb-2">Pass-through</th>
                    <th className="pb-2">Flow (In / Out)</th>
                    <th className="pb-2">Rationale</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-muted-border/50">
                  {mules.length === 0 ? (
                    <tr>
                      <td colSpan={6} className="py-6 text-center text-muted-gray">
                        No money mules identified for this scenario run.
                      </td>
                    </tr>
                  ) : (
                    mules.map((m) => (
                      <tr key={m.accountId} className="hover:bg-background transition-colors">
                        <td className="py-2.5 font-bold text-warm-white">#{m.rank}</td>
                        <td className="py-2.5">
                          <div className="font-semibold text-warm-white">{m.alias || m.accountRef}</div>
                          <div className="text-[10px] text-muted-gray">{m.accountRef}</div>
                        </td>
                        <td className="py-2.5 text-red-400 font-semibold">{m.muleScore.toFixed(1)}</td>
                        <td className="py-2.5 text-muted-gray">{(m.passThroughRatio * 100).toFixed(0)}%</td>
                        <td className="py-2.5 text-[11px]">
                          <span className="text-emerald-400">${Number(m.totalReceived).toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
                          <span className="text-muted-gray"> / </span>
                          <span className="text-red-400">${Number(m.totalDisbursed).toLocaleString('en-US', { maximumFractionDigits: 0 })}</span>
                        </td>
                        <td className="py-2.5 text-[10px] text-muted-gray max-w-[180px] truncate" title={m.rationale}>
                          {m.rationale}
                        </td>
                      </tr>
                    ))
                  )}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Tab 3: FIFO Attribution */}
      {activeTab === 'fifo' && (
        <div className="bg-background-secondary border border-muted-border rounded-lg p-5">
          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-2 mb-4 pb-3 border-b border-muted-border">
            <div>
              <h3 className="text-sm font-mono font-bold text-warm-white flex items-center gap-2">
                <Layers size={16} className="text-amber" />
                <span>Deterministic FIFO Fund Attribution Ledger</span>
              </h3>
              <p className="text-[11px] text-muted-gray mt-0.5">
                First-In, First-Out ledger matching downstream outgoing disbursements to upstream incoming parent tranches.
              </p>
            </div>
          </div>

          <div className="overflow-x-auto">
            <table className="w-full text-left text-xs font-mono">
              <thead>
                <tr className="border-b border-muted-border text-muted-dark uppercase text-[10px]">
                  <th className="pb-2.5">Tx Reference</th>
                  <th className="pb-2.5">Timestamp</th>
                  <th className="pb-2.5">Total Amount</th>
                  <th className="pb-2.5">Consumed Inflows (Parent Tranches)</th>
                  <th className="pb-2.5">Unattributed Amount</th>
                  <th className="pb-2.5">Attribution Class</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-muted-border/50">
                {fifoAttributions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="py-8 text-center text-muted-gray">
                      No outgoing transfers requiring FIFO attribution in this run.
                    </td>
                  </tr>
                ) : (
                  fifoAttributions.map((item) => (
                    <tr key={item.transactionId} className="hover:bg-background transition-colors">
                      <td className="py-3 font-semibold text-warm-white">{item.transactionRef}</td>
                      <td className="py-3 text-[11px] text-muted-gray">
                        {new Date(item.timestamp).toLocaleTimeString()}
                      </td>
                      <td className="py-3 font-bold text-warm-white">
                        ${Number(item.amount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                      </td>
                      <td className="py-3">
                        {item.consumedAllocations.length === 0 ? (
                          <span className="text-[10px] text-muted-dark italic">Pure Initial Outflow (No parent)</span>
                        ) : (
                          <div className="space-y-1">
                            {item.consumedAllocations.map((a, idx) => (
                              <div key={idx} className="flex items-center gap-1.5 text-[11px]">
                                <span className="text-amber">{a.parentTxnRef}</span>
                                <span className="text-muted-gray">:</span>
                                <span className="text-emerald-400 font-semibold">
                                  ${Number(a.attributedAmount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                                </span>
                              </div>
                            ))}
                          </div>
                        )}
                      </td>
                      <td className="py-3">
                        {Number(item.unattributedAmount) > 0 ? (
                          <span className="text-amber font-mono font-medium">
                            ${Number(item.unattributedAmount).toLocaleString('en-US', { minimumFractionDigits: 2 })}
                          </span>
                        ) : (
                          <span className="text-emerald-400 font-mono text-[11px] flex items-center gap-1">
                            <CheckCircle size={12} />
                            <span>100% Attributed</span>
                          </span>
                        )}
                      </td>
                      <td className="py-3">
                        <span className={`text-[10px] uppercase px-2 py-0.5 rounded border ${
                          item.isDirectAttribution
                            ? 'bg-blue-500/15 text-blue-400 border-blue-500/30'
                            : 'bg-muted-border/30 text-muted-gray border-muted-border'
                        }`}>
                          {item.isDirectAttribution ? 'Direct Lineage' : 'Residual Flow'}
                        </span>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
