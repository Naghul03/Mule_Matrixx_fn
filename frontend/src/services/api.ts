import {
  HealthResponse,
  DatabaseHealthResponse,
  ScenarioTemplate,
  ScenarioRunResponse,
  AlertItem,
  CaseItem,
  CaseDetail,
  CytoscapeGraphData,
  RankingsData,
  FIFOAttributionItem,
  EvaluationRunData,
  CBDCWallet,
  CBDCLedgerEvent,
  CBDCTokenLot,
  CBDCProvenanceData,
  DashboardMetrics,
} from '../types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api/v1';

export class ApiError extends Error {
  constructor(
    public status: number,
    public statusText: string,
    public details?: unknown
  ) {
    super(`API Error ${status}: ${statusText}`);
    this.name = 'ApiError';
  }
}

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const url = `${API_BASE_URL}${path}`;
  try {
    const res = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...(options?.headers || {}),
      },
    });

    if (!res.ok) {
      let errorBody: unknown;
      try {
        errorBody = await res.json();
      } catch {
        errorBody = await res.text();
      }
      throw new ApiError(res.status, res.statusText, errorBody);
    }

    return await res.json();
  } catch (err) {
    if (err instanceof ApiError) {
      throw err;
    }
    throw new Error(
      `Network connection to backend failed (${API_BASE_URL}). Ensure FastAPI is running on ${API_BASE_URL}`
    );
  }
}

export const api = {
  // Health
  async getServiceHealth(): Promise<HealthResponse> {
    return request<HealthResponse>('/health');
  },

  async getDatabaseHealth(): Promise<DatabaseHealthResponse> {
    return request<DatabaseHealthResponse>('/health/database');
  },

  async checkFullSystem(): Promise<{ service: HealthResponse; database: DatabaseHealthResponse }> {
    const [service, database] = await Promise.all([
      this.getServiceHealth(),
      this.getDatabaseHealth(),
    ]);
    return { service, database };
  },

  // Dashboard Metrics
  async getDashboardMetrics(domain: string = 'current_money'): Promise<DashboardMetrics> {
    return request<DashboardMetrics>(`/dashboard/metrics?domain=${domain}`);
  },

  // Scenarios
  async listScenarioTemplates(domain?: string): Promise<ScenarioTemplate[]> {
    const q = domain ? `?domain=${domain}` : '';
    return request<ScenarioTemplate[]>(`/scenarios${q}`);
  },

  async runScenario(params: {
    scenario_id: string;
    seed: number;
    base_amount?: number;
    num_attack_accounts?: number;
    num_decoys?: number;
  }): Promise<ScenarioRunResponse> {
    return request<ScenarioRunResponse>('/scenarios/run', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async listScenarioRuns(domain?: string, limit: number = 20): Promise<ScenarioRunResponse[]> {
    const params = new URLSearchParams();
    if (domain) params.append('domain', domain);
    params.append('limit', limit.toString());
    return request<ScenarioRunResponse[]>(`/scenarios/runs?${params.toString()}`);
  },

  async getScenarioRun(runId: string): Promise<ScenarioRunResponse> {
    return request<ScenarioRunResponse>(`/scenarios/runs/${runId}`);
  },

  // Alerts
  async listAlerts(params?: {
    domain?: string;
    risk_band?: string;
    scenario_run_id?: string;
    review_status?: string;
    limit?: number;
  }): Promise<AlertItem[]> {
    const q = new URLSearchParams();
    if (params?.domain) q.append('domain', params.domain);
    if (params?.risk_band) q.append('risk_band', params.risk_band);
    if (params?.scenario_run_id) q.append('scenario_run_id', params.scenario_run_id);
    if (params?.review_status) q.append('review_status', params.review_status);
    if (params?.limit) q.append('limit', params.limit.toString());
    return request<AlertItem[]>(`/alerts?${q.toString()}`);
  },

  async reviewAlert(alertId: string, reviewStatus: string): Promise<AlertItem> {
    return request<AlertItem>(`/alerts/${alertId}/review`, {
      method: 'POST',
      body: JSON.stringify({ review_status: reviewStatus }),
    });
  },

  // Cases
  async listCases(params?: {
    domain?: string;
    status?: string;
    priority?: string;
    risk_band?: string;
    search?: string;
  }): Promise<CaseItem[]> {
    const q = new URLSearchParams();
    if (params?.domain) q.append('domain', params.domain);
    if (params?.status) q.append('status', params.status);
    if (params?.priority) q.append('priority', params.priority);
    if (params?.risk_band) q.append('risk_band', params.risk_band);
    if (params?.search) q.append('search', params.search);
    return request<CaseItem[]>(`/cases?${q.toString()}`);
  },

  async getCase(caseId: string): Promise<CaseDetail> {
    return request<CaseDetail>(`/cases/${caseId}`);
  },

  async updateCaseStatus(caseId: string, status: string, note: string): Promise<CaseDetail> {
    return request<CaseDetail>(`/cases/${caseId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status, note }),
    });
  },

  async createManualCase(params: {
    bank_code: string;
    transaction_reference?: string;
    account_reference?: string;
    amount?: number;
    suspicion_category: string;
    description: string;
  }): Promise<CaseDetail> {
    return request<CaseDetail>('/cases/manual', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  // Investigation
  async getInvestigationGraph(params: {
    scenario_run_id?: string;
    case_id?: string;
    account_id?: string;
    max_depth?: number;
  }): Promise<CytoscapeGraphData> {
    const q = new URLSearchParams();
    if (params.scenario_run_id) q.append('scenario_run_id', params.scenario_run_id);
    if (params.case_id) q.append('case_id', params.case_id);
    if (params.account_id) q.append('account_id', params.account_id);
    if (params.max_depth) q.append('max_depth', params.max_depth.toString());
    return request<CytoscapeGraphData>(`/investigation/graph?${q.toString()}`);
  },

  async getRankings(scenarioRunId: string): Promise<RankingsData> {
    return request<RankingsData>(`/investigation/rankings?scenario_run_id=${scenarioRunId}`);
  },

  async getFIFOAttribution(scenarioRunId: string): Promise<FIFOAttributionItem[]> {
    return request<FIFOAttributionItem[]>(`/investigation/fifo-attribution?scenario_run_id=${scenarioRunId}`);
  },

  // Evaluation
  async runEvaluation(params: {
    scenario_run_id: string;
    seed_type?: string;
    domain?: string;
  }): Promise<EvaluationRunData> {
    return request<EvaluationRunData>('/evaluation/run', {
      method: 'POST',
      body: JSON.stringify(params),
    });
  },

  async listEvaluationRuns(domain?: string): Promise<EvaluationRunData[]> {
    const q = domain ? `?domain=${domain}` : '';
    return request<EvaluationRunData[]>(`/evaluation/runs${q}`);
  },

  // Reports
  getCaseReportPdfUrl(caseId: string): string {
    return `${API_BASE_URL}/reports/cases/${caseId}/pdf`;
  },

  getCaseReportHtmlUrl(caseId: string): string {
    return `${API_BASE_URL}/reports/cases/${caseId}/html`;
  },

  // CBDC
  async listCBDCWallets(): Promise<CBDCWallet[]> {
    return request<CBDCWallet[]>('/cbdc/wallets');
  },

  async listCBDCEvents(scenarioRunId?: string): Promise<CBDCLedgerEvent[]> {
    const q = scenarioRunId ? `?scenario_run_id=${scenarioRunId}` : '';
    return request<CBDCLedgerEvent[]>(`/cbdc/events${q}`);
  },

  async listCBDCLots(status?: string): Promise<CBDCTokenLot[]> {
    const q = status ? `?status=${status}` : '';
    return request<CBDCTokenLot[]>(`/cbdc/lots${q}`);
  },

  async getCBDCProvenance(lotRef: string): Promise<CBDCProvenanceData> {
    return request<CBDCProvenanceData>(`/cbdc/provenance/${lotRef}`);
  },

  async runCBDCScenario(seed: number = 42, amount?: number): Promise<any> {
    const q = new URLSearchParams({ seed: seed.toString() });
    if (amount) q.append('amount', amount.toString());
    return request<any>(`/cbdc/scenarios/run?${q.toString()}`, { method: 'POST' });
  },
};
