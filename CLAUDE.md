# Mule Matrix — Developer & Architecture Rules

## Product Identity
- **Product Name:** Mule Matrix
- **Tagline:** Follow the Money. Uncover the Network.
- **Purpose:** Simulate financial transactions across multiple banks, identify suspicious money movement, investigate potential mule accounts, trace transaction relationships, and identify possible coordinating accounts or kingpins.
- **Sections:**
  1. **Current Money Transactions:** Simulated conventional bank-transfer investigation environment.
  2. **CBDC Tokens:** Simulated digital-currency token ledger and provenance explorer (implemented in Module 6).

---

## Non-Negotiable Project Rules

1. **Module-by-Module Progression:**
   - Implement one module at a time.
   - Do not implement future modules early.
   - Do not proceed past a module's acceptance gate until its tests pass or any remaining limitations are explicitly documented.
   - Read this `CLAUDE.md` before making any project changes.

2. **Preserve Approved Architecture:**
   - Maintain naming conventions, database contracts, visual design, and business rules across modules.
   - Do not silently rewrite previously approved modules.
   - Modular monolith structure: one React frontend and one FastAPI backend.
   - No unnecessary infrastructure (no Redis, Celery, Kafka, microservices, or separate auth service unless an approved requirement demands them).

3. **No Fabricated / Hardcoded Operational Data:**
   - Never hardcode fake investigation results, transaction graphs, account rankings, risk scores, alerts, or evaluation metrics in the UI.
   - Future screens must consume persisted data through typed API contracts.
   - No decorative static dashboards presented as functional tools.
   - Any development fixtures must be explicitly identified as test or demonstration data.

4. **Reproducibility:**
   - Generated transaction data must be reproducible from a recorded seed and configuration.
   - Preserve transaction provenance, bank origin, normalization details, scenario version, seed, and generation configuration.

5. **Strict Ground-Truth Isolation:**
   - Keep hidden ground-truth evaluation labels strictly separate from detector inputs.
   - The detector must never use scenario labels, attack-account IDs, or hidden ground truth to predict suspicious activity.
   - Ground truth may be accessed only by the evaluation layer after predictions have been generated.
   - Do not create detector APIs or queries that expose or consume ground-truth labels.

6. **Financial Precision:**
   - Use exact decimal arithmetic (`Decimal` in Python, exact `DECIMAL(18, 4)` in MySQL).
   - Never use floating-point arithmetic for monetary calculations.

7. **Graph & Investigation Integrity:**
   - Distinguish observed transactions, historical relationships, and inferred relationships.
   - Do not automatically label every account connected to a suspicious account as malicious.
   - Do not fabricate transactions or graph edges when evidence is unavailable.

8. **Database & Migration Integrity:**
   - Use Alembic migrations exclusively for schema evolution. Do not use `Base.metadata.create_all()` in application code.
   - Use timezone-aware UTC timestamps for all persisted date-time values.

9. **Visual Identity:**
   - Strictly adhere to the approved Mule Matrix visual identity:
     - Primary background: `#090907`
     - Earth brown: `#6C5636`
     - Burnt amber: `#B99D73`
     - Primary text: warm white (`#F5F5F0`)
     - Secondary text: muted gray (`#9E9E96`)
   - Dark, restrained, precise, data-dense, professional financial intelligence aesthetic.

10. **Security & Prototype Scope:**
    - Local development simulation prototype. Bind backend to localhost (`127.0.0.1`).
    - Never commit real credentials. Use parameterized queries.
    - Explicitly document that this platform is a research and simulation prototype, not connected to live banks.

