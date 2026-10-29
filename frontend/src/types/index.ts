export type AppSection = 'current_money' | 'cbdc';

export interface HealthResponse {
  status: string;
  service: string;
  version: string;
  environment: string;
}

export interface DatabaseHealthResponse {
  status: 'connected' | 'disconnected';
  database: string;
  latency_ms: number | null;
  error: string | null;
}

export interface SystemStatus {
  service: HealthResponse | null;
  database: DatabaseHealthResponse | null;
  loading: boolean;
  lastChecked: Date | null;
  error: string | null;
}

export interface ScenarioTemplate {
  id: string;
  name: string;
  domain: string;
  description: string;
  default_seed: number;
  default_amount: number;
  key_typologies: string[];
}

export interface ScenarioRunResponse {
  id: string;
  domain: string;
  scenario_identifier: string;
  scenario_name?: string;
  scenario_version: string;
  generator_version: string;
  seed: number;
  status: string;
  configuration_json: Record<string, any>;
  started_at?: string;
  completed_at?: string;
  created_at: string;
  transaction_count?: number;
  alert_count?: number;
  case_count?: number;
}

export interface AlertItem {
  id: string;
  domain: string;
  scenario_run_id?: string;
  account_id?: string;
  transaction_id?: string;
  account_ref?: string;
  transaction_ref?: string;
  bank_code?: string;
  risk_score: number;
  risk_band: 'HIGH' | 'MEDIUM' | 'LOW';
  signals: Array<{
    signal: string;
    score: number;
    weight: number;
    description: string;
    evidence: string[];
  }>;
  detector_version: string;
  review_status: string;
  created_at: string;
  updated_at: string;
}

export interface CaseItem {
  id: string;
  case_reference: string;
  domain: string;
  title: string;
  summary?: string;
  status: 'OPEN' | 'UNDER_INVESTIGATION' | 'ESCALATED' | 'CLOSED';
  priority: 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';
  risk_band?: string;
  aggregate_risk_score?: number;
  scenario_run_id?: string;
  is_manual_entry: boolean;
  manual_entry_data?: Record<string, any>;
  created_at: string;
  updated_at: string;
  alert_count: number;
  account_count: number;
  transaction_count: number;
}

export interface CaseDetail extends CaseItem {
  alerts: Array<{
    id: string;
    risk_score: number;
    risk_band: string;
    signals: any[];
    review_status: string;
    created_at: string;
  }>;
  accounts: Array<{
    id: string;
    reference: string;
    alias?: string;
    bank_code: string;
    role?: string;
  }>;
  transactions: Array<{
    id: string;
    reference: string;
    source: string;
    destination: string;
    amount: number;
    currency: string;
    timestamp: string;
    evidence_type: string;
  }>;
  notes: Array<{
    id: string;
    note_type: string;
    content: string;
    previous_status?: string;
    new_status?: string;
    created_at: string;
  }>;
}

export interface CytoscapeNodeData {
  id: string;
  label: string;
  accountRef: string;
  bankCode: string;
  bankName: string;
  riskScore: number;
  riskBand: string;
  totalIn: number;
  totalOut: number;
}

export interface CytoscapeEdgeData {
  id: string;
  source: string;
  target: string;
  amount: number;
  currency: string;
  timestamp: string;
  reference: string;
  evidenceType: 'DIRECT' | 'HISTORICAL' | 'INFERRED';
  normalizedType: string;
  status: string;
}

export interface CytoscapeGraphData {
  nodes: Array<{ data: CytoscapeNodeData }>;
  edges: Array<{ data: CytoscapeEdgeData }>;
}

export interface KingpinRankingItem {
  rank: number;
  accountId: string;
  accountRef: string;
  alias: string;
  riskScore: number;
  kingpinScore: number;
  totalReceived: number;
  totalDisbursed: number;
  inboundTransfers: number;
  outboundTransfers: number;
  betweennessCentrality: number;
  rationale: string;
}

export interface MuleRankingItem {
  rank: number;
  accountId: string;
  accountRef: string;
  alias: string;
  riskScore: number;
  muleScore: number;
  passThroughRatio: number;
  totalReceived: number;
  totalDisbursed: number;
  rationale: string;
}

export interface RankingsData {
  kingpins: KingpinRankingItem[];
  mules: MuleRankingItem[];
}

export interface FIFOAttributionItem {
  transactionId: string;
  transactionRef: string;
  amount: number;
  timestamp: string;
  consumedAllocations: Array<{
    parentTxnId: string;
    parentTxnRef: string;
    attributedAmount: number;
  }>;
  unattributedAmount: number;
  isDirectAttribution: boolean;
}

export interface EvaluationRunData {
  id: string;
  domain: string;
  scenario_run_id: string;
  detector_version: string;
  baseline_version: string;
  seed_type: string;
  metrics: {
    total_evaluated: number;
    true_positives: number;
    false_positives: number;
    true_negatives: number;
    false_negatives: number;
    precision: number;
    recall: number;
    f1_score: number;
  };
  baseline_metrics: {
    total_evaluated: number;
    true_positives: number;
    false_positives: number;
    true_negatives: number;
    false_negatives: number;
    precision: number;
    recall: number;
    f1_score: number;
  };
  confusion_matrix?: {
    TP: number;
    FP: number;
    TN: number;
    FN: number;
  };
  baseline_confusion_matrix?: {
    TP: number;
    FP: number;
    TN: number;
    FN: number;
  };
  created_at: string;
}

export interface CBDCWallet {
  id: string;
  wallet_address: string;
  display_name?: string;
  wallet_type: string;
  balance: number;
  synthetic_classification?: string;
  is_active: boolean;
  created_at: string;
}

export interface CBDCTokenLot {
  id: string;
  lot_reference: string;
  current_holder_wallet_id: string;
  amount: number;
  currency: string;
  status: string;
  created_at: string;
}

export interface CBDCLedgerEvent {
  id: string;
  scenario_run_id?: string;
  event_type: string;
  from_wallet_id?: string;
  to_wallet_id: string;
  from_wallet_address?: string;
  to_wallet_address: string;
  amount: number;
  currency: string;
  event_timestamp: string;
  parent_lot_ids?: string[];
  child_lot_ids?: string[];
}

export interface CBDCProvenanceData {
  targetLot: {
    id: string;
    lotReference: string;
    amount: number;
    status: string;
    currency: string;
    currentHolder: {
      id: string;
      address: string;
      displayName: string;
      type: string;
    };
  };
  parents: Array<{
    id: string;
    lotReference: string;
    amount: number;
    status: string;
    eventType: string;
  }>;
  children: Array<{
    id: string;
    lotReference: string;
    amount: number;
    status: string;
    eventType: string;
  }>;
}

export interface DashboardMetrics {
  domain: string;
  total_cases: number;
  open_cases: number;
  escalated_cases: number;
  high_risk_alerts: number;
  medium_risk_alerts: number;
  low_risk_alerts: number;
  total_transactions: number;
  total_volume: number;
  recent_scenario_runs: Array<{
    id: string;
    scenario: string;
    seed: number;
    status: string;
    createdAt: string;
  }>;
  recent_alerts: Array<{
    id: string;
    riskScore: number;
    riskBand: string;
    signalsCount: number;
    createdAt: string;
  }>;
}

export interface SimulatedBankInfo {
  code: string;
  name: string;
  adapter: string;
  description: string;
  formatType: string;
}
