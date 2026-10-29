# Mule Matrix — Module Acceptance Criteria & Verification Matrix

## Module 1: Foundation & Database
- [x] **Criterion 1: Project Foundation & CLAUDE.md**
  - Root `CLAUDE.md` exists with all non-negotiable project rules.
  - Project documentation established in `docs/`.
- [x] **Criterion 2: Backend Architecture & Configuration**
  - FastAPI backend initializes with structured logging, Pydantic settings, and CORS.
  - Health endpoints `GET /api/v1/health` and `GET /api/v1/health/database` respond with verified DB connectivity.
- [x] **Criterion 3: Database & Alembic Migrations**
  - SQLAlchemy models for `banks`, `accounts`, `scenario_runs`, `transactions`, and `ground_truth_labels`.
  - Exact `DECIMAL(18, 4)` and UTC datetimes enforced across all tables.
  - Alembic migrations applied to `head` (`0001_initial_foundation`, `0002_modules_2_through_7`).
- [x] **Criterion 4: Canonical Schema & 4 Bank Adapters**
  - Adapters for Bank A (Apex), Bank B (Beacon), Bank C (Crestline), and Bank D (Delta).
  - Normalization invariants: positive amounts, valid ISO-8601 timestamps, self-transfer rejection.
- [x] **Criterion 5: Ground-Truth Separation**
  - Ground truth model strictly isolated. Surveillance APIs never expose or join ground truth.
- [x] **Criterion 6: Frontend Shell & Visual Identity**
  - React + TypeScript + Vite with Tailwind CSS.
  - Approved design palette: `#090907` background, `#6C5636` earth brown, `#B99D73` burnt amber.

---

## Module 2: Multi-Bank Scenario Engine
- [x] **Criterion 1: Reproducible Scenario Generation**
  - Python Mersenne Twister PRNG seed configuration (`seed=42`).
  - Cap of maximum 10 attack accounts strictly enforced across all scenario variants.
- [x] **Criterion 2: Scenario 1 (Multi-Layer Dispersion)**
  - Single victim -> 2-3 Layer 1 mules -> 4-6 Layer 2 mules -> 1-2 consolidation endpoints.
- [x] **Criterion 3: Scenario 3 (Hidden Kingpin & Smurfing)**
  - Upstream Victim account `V` disburses funds to mules `A`, `B`, `C`.
  - Mules `B` and `C` transfer portions to unflagged Kingpin account `D`.
  - Pre-existing historical non-suspicious transactions between `B->D` and `C->D`.
  - No direct transfer between Victim `V` and Kingpin `D`.
- [x] **Criterion 4: Scenario 4 (Rapid Velocity Structuring)**
  - Just-below-reporting-threshold tranches (e.g. $9,200 - $9,800) within tight time windows.
- [x] **Criterion 5: Background Noise & Decoys**
  - Decoy payroll disbursements and merchant sales injected to prevent 100% synthetic purity.

---

## Module 3: Surveillance, Detection & Risk Scoring
- [x] **Criterion 1: Multi-Signal Scoring Engine**
  - Total signal weight equals 100 points:
    - Pass-through velocity & turnaround ratio (weight: 30)
    - Fan-out / Fan-in dispersion degree (weight: 25)
    - Threshold structuring pattern (weight: 20)
    - Network graph betweenness centrality (weight: 15)
    - Entity age / dormant-account activation (weight: 10)
- [x] **Criterion 2: Risk Categorization & Explainability**
  - High Risk (score >= 70), Medium Risk (score >= 40), Low Risk (score < 40).
  - Explicit rationale breakdown detailing which signals fired for every generated alert.
- [x] **Criterion 3: Guilt-by-Association Protection**
  - Pure originating accounts (such as fraud victims) are protected from receiving high mule scores.
- [x] **Criterion 4: Strict Detector Isolation**
  - Detector algorithms evaluate only transactions and accounts. Zero queries to ground truth tables.

---

## Module 4: Case Management & Audit Trail
- [x] **Criterion 1: Automated Case Aggregation**
  - Alerts on related accounts within a 24-hour event window automatically merge into unified cases.
- [x] **Criterion 2: Manual Lead Entry**
  - Intake interface for investigator-reported leads with automated verification vs database transactions.
  - Generates unverified flagged transactions when reference is not in database.
- [x] **Criterion 3: Immutable Audit History**
  - Case status changes (`OPEN` -> `UNDER_INVESTIGATION` -> `ESCALATED` -> `CLOSED`) record required investigator rationale notes.

---

## Module 5: Graph Investigation & Fund Attribution
- [x] **Criterion 1: Cytoscape.js Investigation Canvas**
  - Dark theme graph canvas with nodes colored by risk band (`HIGH`, `MEDIUM`, `LOW`).
  - Edge differentiation: solid amber arrows for direct transfers vs dashed lines for historical counterparty edges.
  - Interactive click selection displaying account and transaction inspection dossiers.
- [x] **Criterion 2: Network Centrality & Account Rankings**
  - NetworkX betweenness centrality identifies coordinating hub accounts.
  - Scenario 3 Target Verified: Kingpin account `D` ranks #1 coordinating account; Victim is NOT ranked as a mule.
- [x] **Criterion 3: Deterministic FIFO Fund Attribution**
  - Exact First-In, First-Out ledger tracing downstream disbursements back to upstream victim parent tranches.

---

## Module 6: CBDC Token Ledger & Provenance
- [x] **Criterion 1: UTXO-Style Token Lots**
  - Discrete token lot entities with conservation invariant: $\sum \text{Inputs} = \sum \text{Outputs}$.
- [x] **Criterion 2: Scenario 2 (Digital Currency Peeling Chain)**
  - Central bank issuance -> Commercial bank distribution -> Peeling transfers -> Vault consolidation.
- [x] **Criterion 3: Token Lot Provenance Explorer**
  - Visual ancestry tree displaying parent origin lots, target lot, and descendant child lots.

---

## Module 7: Evaluation, Benchmarking & Reporting
- [x] **Criterion 1: Empirical Evaluation Engine**
  - Multi-signal detector benchmarked against naive single-threshold baseline.
  - Real Precision, Recall, F1 scores and 2x2 confusion matrices (TP, FP, TN, FN).
- [x] **Criterion 2: Ground Truth Isolation Verification**
  - Evaluation accesses ground truth strictly post-prediction. Unit tests confirm zero detector leakage.
- [x] **Criterion 3: Investigation Reports & PDF Export**
  - Comprehensive HTML case dossier with Playwright PDF rendering fallback.
