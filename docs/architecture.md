# Mule Matrix — Full System Architecture Specification

## 1. System Overview
Mule Matrix is a modular monolithic platform designed for simulating, detecting, and investigating money muling and coordinated suspicious financial networks across multiple financial institutions and digital token ledgers.

The platform architecture features two operational sections:
1. **Current Money Transactions:** Conventional multi-bank accounts, wire transfers, ACH, and relational networks.
2. **CBDC Tokens:** Simulated central bank digital currency token ledger with unspent token provenance and UTXO-style peeling chain analysis.

Both sections share the same database engine, UI design system, and financial investigation principles.

```
                          +-------------------------------------------------+
                          |             Mule Matrix React Frontend          |
                          |  - Approved Visual Identity (#090907, Earth/Burnt)
                          |  - Current Money / CBDC Section Switcher        |
                          |  - Cytoscape.js Network Investigation Canvas    |
                          |  - Real-time Alert & Case Surveillance Table    |
                          |  - Empirical Detector Benchmark Dashboard       |
                          |  - CBDC Token Lot Provenance Explorer           |
                          +------------------------+------------------------+
                                                   | HTTP / REST
                                                   v
                          +-------------------------------------------------+
                          |              FastAPI Modular Backend            |
                          |  - Canonical Transaction Normalization Layer    |
                          |  - Bank Adapters (Apex, Beacon, Crestline, Delta)
                          |  - Multi-Bank Scenario Generator (Scenarios 1-4)|
                          |  - Multi-Signal Surveillance Engine (100 pts)   |
                          |  - Case Aggregation & Audit Trail Engine        |
                          |  - NetworkX Graph Centrality & FIFO Attribution |
                          |  - CBDC UTXO Token Ledger Engine                |
                          |  - Isolated Evaluation & Benchmark Suite        |
                          |  - HTML & PDF Case Dossier Reporting Service    |
                          +------------------------+------------------------+
                                                   | SQLAlchemy 2.0 (Alembic)
                                                   v
                          +-------------------------------------------------+
                          |               MySQL 8.0 Database                |
                          |  - banks, accounts, transactions, scenario_runs |
                          |  - alerts, cases, case_notes, risk_scores       |
                          |  - cbdc_wallets, cbdc_token_lots, cbdc_events   |
                          |  - ground_truth_labels, cbdc_ground_truth       |
                          |    (Strictly Isolated Evaluation Stores)        |
                          +-------------------------------------------------+
```

---

## 2. Implemented Subsystems & Modules

### 2.1 Multi-Bank Normalization Pipeline (Module 1)
- Ingests raw native formats from 4 distinct simulated banks:
  - Bank A (Apex Bank): XML/ISO 20022 style payloads.
  - Bank B (Beacon Credit Union): Flat JSON with nested metadata.
  - Bank C (Crestline Commercial): Enterprise wire JSON.
  - Bank D (Delta Cooperative): Delimited key-value formats.
- Normalizes all transactions into `CanonicalTransaction` models with decimal currency precision (`DECIMAL(18, 4)`).

### 2.2 Multi-Bank Scenario Generation (Module 2)
- Mersenne Twister PRNG reproducibility with user-configurable seeds.
- Scenario 1 (Multi-Layer Dispersion): Multi-tiered mule tree consolidating into offshore/vault accounts.
- Scenario 3 (Hidden Kingpin & Smurfing): Upstream victim funds disbursed to mules `A`, `B`, `C`; mules `B` and `C` transfer to unflagged kingpin `D`; historical edges `B->D` and `C->D` preserved without direct victim-to-D transfer.
- Scenario 4 (Rapid Velocity Structuring): Just-below-reporting threshold tranches with high turnaround frequency.
- Decoy generators: Inject realistic payroll and merchant transactions to simulate production false-positive environments.

### 2.3 Surveillance & Risk Scoring Engine (Module 3)
- Multi-signal scoring engine totaling 100 points:
  - Turnaround & pass-through velocity (30 pts)
  - Fan-out / Fan-in dispersion degree (25 pts)
  - Threshold structuring (20 pts)
  - Network graph betweenness centrality (15 pts)
  - Entity age / dormant activation (10 pts)
- Guilt-by-association protection prevents innocent originating victims from being falsely labeled as mules.
- Risk bands: High (>= 70), Medium (40-69), Low (< 40).

### 2.4 Case Management & Audit Trail (Module 4)
- Automated clustering: Alerts occurring on related accounts within a 24-hour event window automatically merge into unified cases.
- Manual lead intake: Supports investigator-reported leads with automated database verification.
- Immutable audit notes: Mandates rationale capture on status transitions (`OPEN`, `UNDER_INVESTIGATION`, `ESCALATED`, `CLOSED`).

### 2.5 Graph Investigation & Fund Attribution (Module 5)
- Cytoscape.js interactive network visualization with custom dark theme styling.
- Visual distinction: solid arrows for direct laundering transfers vs dashed lines for historical edges.
- NetworkX betweenness centrality ranking correctly elevates coordinating kingpin accounts.
- Deterministic FIFO attribution tracks exact fund flows from victim origin to terminal dispersion.

### 2.6 CBDC Token Ledger & Provenance (Module 6)
- Discrete UTXO-style token lot state machine (`ACTIVE`, `SPENT`, `CONSOLIDATED`, `FROZEN`).
- Strict conservation invariant enforced: $\sum \text{Input Lots} = \sum \text{Output Lots}$.
- Scenario 2 generator: Central bank issuance -> Commercial bank distribution -> Intermediary peeling chain -> Vault consolidation.
- Interactive provenance tree explorer tracing upstream parent lots and downstream child lots.

### 2.7 Evaluation & Reporting (Module 7)
- Empirical benchmark comparing the Mule Matrix multi-signal detector against a single-threshold baseline.
- Produces Precision, Recall, F1 scores and 2x2 confusion matrices (TP, FP, TN, FN).
- Strictly isolated ground truth: Detector never queries ground truth tables; evaluation runs post-prediction only.
- Case dossier export: Generates structured HTML reports with Playwright headless PDF generation fallback.
