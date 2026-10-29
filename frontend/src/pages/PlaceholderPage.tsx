import React from 'react';
import { useLocation } from 'react-router-dom';
import { Lock, Construction, CheckCircle2 } from 'lucide-react';
import { Card } from '../components/common/Card';
import { Badge } from '../components/common/Badge';

interface ModuleMapItem {
  title: string;
  module: number;
  moduleName: string;
  description: string;
  plannedFeatures: string[];
}

const MODULE_MAP: Record<string, ModuleMapItem> = {
  '/current-money/scenarios': {
    title: 'Current Money — Synthetic Scenarios',
    module: 2,
    moduleName: 'Scenario Generator & Normal Traffic Engine',
    description: 'Generates reproducible multi-bank transaction networks, background normal transactions, and money muling attack chains from explicit seeds.',
    plannedFeatures: [
      'Isolated seeded PRNG transaction generation',
      'Structuring & fan-out topology generation',
      'Circular layering and funnel cash-out chains',
      'Normal commercial & payroll background noise',
      'Strict separation of hidden ground-truth attack roles',
    ],
  },
  '/current-money/alerts': {
    title: 'Current Money — Monitoring & Alerts',
    module: 3,
    moduleName: 'Detection Engine & Typology Rules',
    description: 'Streaming and batch rule-based anomaly detection engines running without access to hidden ground truth.',
    plannedFeatures: [
      'Rapid velocity & structuring detectors',
      'Fan-out smurfing pattern matchers',
      'Aggregated risk scoring pipelines',
      'Rule triage and priority queues',
    ],
  },
  '/current-money/cases': {
    title: 'Current Money — Case Management',
    module: 4,
    moduleName: 'Case Management & Workflow',
    description: 'Investigator case dossiers, evidence attachment, escalation workflows, and SAR draft preparation.',
    plannedFeatures: [
      'Case lifecycle states and investigator assignment',
      'Transaction and account bookmarking',
      'Audit log and evidence chain of custody',
    ],
  },
  '/current-money/investigation': {
    title: 'Current Money — Investigation Graph',
    module: 5,
    moduleName: 'Network Analysis & Cytoscape Graph',
    description: 'Interactive multi-bank relational graph visualization powered by Cytoscape.js and NetworkX centrality metrics.',
    plannedFeatures: [
      'Interactive Cytoscape.js directed transaction graph',
      'Mule account path traversal and cycle detection',
      'Kingpin coordinator & aggregation node identification',
      'Temporal playback of money flows',
    ],
  },
  '/current-money/evaluation': {
    title: 'Current Money — Detection Evaluation',
    module: 7,
    moduleName: 'Evaluation, Benchmarking & Reporting',
    description: 'Post-detection benchmark evaluation comparing detector alerts against hidden ground-truth labels.',
    plannedFeatures: [
      'Precision, recall, and F1 calculation against ground truth',
      'Mule network identification accuracy',
      'HTML and Playwright automated PDF reports',
    ],
  },
  '/cbdc/overview': {
    title: 'CBDC Tokens — Ledger Overview',
    module: 6,
    moduleName: 'CBDC Token Ledger & Provenance Engine',
    description: 'Simulated Central Bank Digital Currency (CBDC) token ledger tracking discrete token lots and unspent token provenance.',
    plannedFeatures: [
      'Digital token minting and distribution ledger',
      'Unspent token lineage and wallet states',
      'Dark wallet and token mixing typology tracking',
    ],
  },
  '/cbdc/scenarios': {
    title: 'CBDC Tokens — Scenarios',
    module: 6,
    moduleName: 'CBDC Token Ledger & Provenance Engine',
    description: 'Synthetic token laundering scenarios and mixer patterns.',
    plannedFeatures: ['Simulated token peeling chains', 'Mixer and obfuscation cycles'],
  },
  '/cbdc/alerts': {
    title: 'CBDC Tokens — Alerts',
    module: 6,
    moduleName: 'CBDC Token Ledger & Provenance Engine',
    description: 'Token velocity and wallet hopping detection signals.',
    plannedFeatures: ['Token split and merge alerts', 'Sanctioned wallet proximity'],
  },
  '/cbdc/cases': {
    title: 'CBDC Tokens — Cases',
    module: 6,
    moduleName: 'CBDC Token Ledger & Provenance Engine',
    description: 'Digital asset investigation dossiers.',
    plannedFeatures: ['Token seizure and freeze tracking', 'Cross-wallet flow correlation'],
  },
  '/cbdc/investigation': {
    title: 'CBDC Tokens — Investigation Graph',
    module: 6,
    moduleName: 'CBDC Token Ledger & Provenance Engine',
    description: 'Directed acyclic token provenance graph exploration.',
    plannedFeatures: ['Token tree lineage traversal', 'UTXO-like token split visualization'],
  },
  '/cbdc/provenance': {
    title: 'CBDC Tokens — Token Provenance Explorer',
    module: 6,
    moduleName: 'CBDC Token Ledger & Provenance Engine',
    description: 'Detailed inspection of specific token lot parentage and custody history.',
    plannedFeatures: ['Complete mint-to-burn custody tracking', 'Token taint analysis'],
  },
  '/cbdc/evaluation': {
    title: 'CBDC Tokens — Token Evaluation',
    module: 7,
    moduleName: 'Evaluation, Benchmarking & Reporting',
    description: 'Evaluation of token flow anomaly models against synthetic ground truth.',
    plannedFeatures: ['Token recovery rate metrics', 'Mixer de-anonymization benchmarks'],
  },
};

export const PlaceholderPage: React.FC = () => {
  const location = useLocation();
  const info = MODULE_MAP[location.pathname] || {
    title: 'Planned Destination',
    module: 2,
    moduleName: 'Future Module',
    description: 'This area is reserved for future implementation in accordance with the Mule Matrix modular roadmap.',
    plannedFeatures: [],
  };

  return (
    <div className="max-w-4xl mx-auto space-y-6">
      <div className="flex items-center justify-between pb-4 border-b border-muted-border">
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span className="text-xs font-mono uppercase text-muted-gray tracking-wider font-semibold">
              Planned Destination
            </span>
            <Badge variant="neutral" size="sm">
              Module {info.module} Scope
            </Badge>
          </div>
          <h2 className="text-xl font-bold font-mono tracking-tight text-warm-white">
            {info.title}
          </h2>
          <p className="text-xs text-muted-gray mt-1">
            {info.description}
          </p>
        </div>
      </div>

      <Card
        title={`Module ${info.module} Specification Gate`}
        subtitle={info.moduleName}
        action={<Lock size={16} className="text-muted-gray" />}
      >
        <div className="space-y-4">
          <div className="p-4 bg-background-secondary rounded border border-muted-border flex items-start gap-3">
            <Construction size={20} className="text-amber flex-shrink-0 mt-0.5" />
            <div className="text-xs text-muted-gray leading-relaxed">
              <strong className="text-warm-white font-mono">Module Boundary Rule:</strong> In strict compliance with the project architecture specifications, future modules are not implemented prematurely or populated with fabricated statistics. This screen will consume persisted contracts when Module {info.module} is approved and implemented.
            </div>
          </div>

          {info.plannedFeatures.length > 0 && (
            <div>
              <h4 className="text-xs font-mono font-semibold uppercase text-warm-white mb-2 tracking-wider">
                Planned Architectural Deliverables
              </h4>
              <ul className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                {info.plannedFeatures.map((feat, idx) => (
                  <li
                    key={idx}
                    className="flex items-center gap-2 p-2 bg-background rounded border border-muted-border text-muted-gray font-mono text-[11px]"
                  >
                    <CheckCircle2 size={13} className="text-amber flex-shrink-0" />
                    <span>{feat}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}

          <div className="pt-2 flex items-center justify-between text-xs text-muted-dark font-mono border-t border-muted-border">
            <span>Status: Awaiting Prior Module Acceptance</span>
            <span>Module 1: Foundation Active</span>
          </div>
        </div>
      </Card>
    </div>
  );
};
