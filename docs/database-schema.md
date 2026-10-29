# Mule Matrix — Database Schema Specification

## Overview
The Mule Matrix database stores simulated financial institutions, accounts, conventional transactions, scenario-run reproducibility metadata, and isolated ground-truth evaluation labels.

The storage engine is MySQL (InnoDB) with strict character set `utf8mb4` and collation `utf8mb4_unicode_ci`.

---

## 1. Tables and Entities

### 1.1 `banks`
Stores simulated banking institutions.
- **Purpose:** Represents the distinct participating institutions in the financial network simulation.
- **Columns:**
  - `id` (VARCHAR(36), PK): Stable UUID/string identifier for the bank.
  - `bank_code` (VARCHAR(16), UNIQUE, NOT NULL): Standardized routing code (e.g., `BNK_A`, `BNK_B`).
  - `display_name` (VARCHAR(128), NOT NULL): Human-readable institution name (e.g., `Apex National Bank`).
  - `adapter_identifier` (VARCHAR(64), NOT NULL): The identifier of the native bank adapter (e.g., `bank_a_adapter_v1`).
  - `is_enabled` (BOOLEAN, NOT NULL, DEFAULT TRUE): Whether the bank is active in simulations.
  - `created_at` (DATETIME(6), NOT NULL): UTC creation timestamp.
  - `updated_at` (DATETIME(6), NOT NULL): UTC last modification timestamp.
- **Indexes & Constraints:**
  - `uq_banks_bank_code`: UNIQUE (`bank_code`)

### 1.2 `accounts`
Stores canonical account identities for simulated bank transfers.
- **Purpose:** Represents accounts held at simulated banks.
- **Columns:**
  - `id` (VARCHAR(36), PK): Canonical account UUID.
  - `bank_id` (VARCHAR(36), FK -> `banks.id`, NOT NULL): Owning simulated bank.
  - `bank_account_reference` (VARCHAR(64), NOT NULL): Account number or reference native to the bank (e.g., `ACC-A-100234`).
  - `display_alias` (VARCHAR(128), NULL): Optional descriptive alias (e.g., `Metro Logistics LLC`).
  - `synthetic_classification` (VARCHAR(64), NULL): Optional non-detector simulation classification (e.g., `retail`, `commercial`, `merchant`). Kept isolated from detector queries.
  - `created_at` (DATETIME(6), NOT NULL): UTC creation timestamp.
  - `updated_at` (DATETIME(6), NOT NULL): UTC last modification timestamp.
- **Indexes & Constraints:**
  - `uq_accounts_bank_ref`: UNIQUE (`bank_id`, `bank_account_reference`)
  - `ix_accounts_bank_id`: INDEX (`bank_id`)

### 1.3 `scenario_runs`
Stores metadata and generation configurations for reproducible scenario runs.
- **Purpose:** Enables strict reproducibility of simulated financial activity and provides run scoping.
- **Columns:**
  - `id` (VARCHAR(36), PK): Unique scenario run UUID.
  - `domain` (VARCHAR(32), NOT NULL): Section domain, e.g., `current_money` (conventional) or `cbdc` (future token ledger).
  - `scenario_identifier` (VARCHAR(64), NOT NULL): Scenario design key (e.g., `structuring_fan_out`, `circular_layering`).
  - `scenario_version` (VARCHAR(16), NOT NULL): Version of the scenario generator template (e.g., `1.0.0`).
  - `generator_version` (VARCHAR(16), NOT NULL): Version of the generator engine (e.g., `1.0.0`).
  - `seed` (BIGINT, NOT NULL): Random generator seed used for reproducibility.
  - `configuration_json` (JSON, NOT NULL): Exact parameters and topology settings passed to the generator.
  - `status` (VARCHAR(24), NOT NULL): Lifecycle state (`PENDING`, `RUNNING`, `COMPLETED`, `FAILED`).
  - `started_at` (DATETIME(6), NULL): UTC execution start timestamp.
  - `completed_at` (DATETIME(6), NULL): UTC completion timestamp.
  - `created_at` (DATETIME(6), NOT NULL): UTC record creation timestamp.
- **Indexes & Constraints:**
  - `ix_scenario_runs_domain`: INDEX (`domain`)
  - `ix_scenario_runs_created_at`: INDEX (`created_at`)

### 1.4 `transactions`
Canonical normalized transaction events.
- **Purpose:** Stores individual financial transfer events across simulated banks in canonical format.
- **Columns:**
  - `id` (VARCHAR(36), PK): Unique transaction UUID.
  - `scenario_run_id` (VARCHAR(36), FK -> `scenario_runs.id`, NULL): Optional scenario run link for synthetic generation.
  - `originating_bank_id` (VARCHAR(36), FK -> `banks.id`, NOT NULL): Bank where the transaction originated.
  - `source_account_id` (VARCHAR(36), FK -> `accounts.id`, NOT NULL): Source debtor account.
  - `destination_account_id` (VARCHAR(36), FK -> `accounts.id`, NOT NULL): Destination creditor account.
  - `amount` (DECIMAL(18, 4), NOT NULL): Exact monetary value (never float).
  - `currency` (VARCHAR(3), NOT NULL): Standard 3-character currency code (e.g., `USD`).
  - `event_timestamp` (DATETIME(6), NOT NULL): UTC timestamp of the financial event.
  - `native_transaction_reference` (VARCHAR(128), NULL): Original transaction reference from the source bank.
  - `normalized_type` (VARCHAR(32), NOT NULL): Standard transaction type (`TRANSFER`, `PAYMENT`, `SETTLEMENT`).
  - `status` (VARCHAR(24), NOT NULL): Execution status (`COMPLETED`, `PENDING`, `REJECTED`, `FAILED`).
  - `source_adapter_version` (VARCHAR(64), NOT NULL): Identifier and version of the adapter that normalized the payload.
  - `raw_payload` (JSON, NOT NULL): Faithful copy of the native input payload before normalization.
  - `normalization_metadata` (JSON, NOT NULL): Normalization timestamp, original schema fields, adapter diagnostics.
  - `created_at` (DATETIME(6), NOT NULL): UTC record creation timestamp.
- **Indexes & Constraints:**
  - `ck_transactions_no_self_transfer`: CHECK (`source_account_id` <> `destination_account_id`)
  - `uq_transactions_bank_native_ref`: UNIQUE (`originating_bank_id`, `native_transaction_reference`) — enforces idempotency when native reference is present.
  - `ix_transactions_scenario_run`: INDEX (`scenario_run_id`)
  - `ix_transactions_origin_bank`: INDEX (`originating_bank_id`)
  - `ix_transactions_source_acc`: INDEX (`source_account_id`)
  - `ix_transactions_dest_acc`: INDEX (`destination_account_id`)
  - `ix_transactions_event_time`: INDEX (`event_timestamp`)
  - `ix_transactions_created_at`: INDEX (`created_at`)

### 1.5 `ground_truth_labels` (Evaluation Separation)
Isolated synthetic labels used strictly for evaluation, NOT detector input.
- **Purpose:** Stores synthetic ground-truth roles for accounts and transactions generated during scenario runs.
- **Isolation Policy:** Detector queries must NEVER join or read from this table. Only post-detection evaluation pipelines (Module 5/7) may query this table.
- **Columns:**
  - `id` (VARCHAR(36), PK): Label UUID.
  - `scenario_run_id` (VARCHAR(36), FK -> `scenario_runs.id`, NOT NULL): Run reference.
  - `account_id` (VARCHAR(36), FK -> `accounts.id`, NULL): Optional labeled account.
  - `transaction_id` (VARCHAR(36), FK -> `transactions.id`, NULL): Optional labeled transaction.
  - `role_label` (VARCHAR(64), NOT NULL): Synthetic ground-truth role (e.g., `mule_layering`, `mule_cashout`, `kingpin_coordination`, `legitimate_activity`).
  - `expected_relationship` (VARCHAR(64), NULL): Relationship classification (e.g., `fan_out_member`, `funnel_receiver`).
  - `rationale` (TEXT, NULL): Ground truth explanation and generator rationale.
  - `created_at` (DATETIME(6), NOT NULL): UTC record creation timestamp.
- **Indexes & Constraints:**
  - `ix_gt_scenario_run`: INDEX (`scenario_run_id`)
  - `ix_gt_account_id`: INDEX (`account_id`)
  - `ix_gt_transaction_id`: INDEX (`transaction_id`)

---

## 2. Integrity and Storage Rules

1. **Monetary Precision:** Decimal arithmetic uses `DECIMAL(18, 4)`. No floating-point data types (`FLOAT`, `DOUBLE`) are permitted for currency values.
2. **Timezone Policy:** All timestamps are strictly UTC. Stored using `DATETIME(6)` (microsecond precision).
3. **No Fabricated Data:** Database migrations must not seed fake investigation reports, alerts, or risk scores.
4. **Idempotency:** Re-ingesting a transaction from the same bank with the same native reference will violate `uq_transactions_bank_native_ref`, preventing duplicate recording.

