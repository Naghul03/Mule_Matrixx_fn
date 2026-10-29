# Mule Matrix — Security and Limitations

## 1. Scope & Research Nature
Mule Matrix is an academic, research, and simulation prototype. It does NOT:
- Connect to live banking networks (SWIFT, Fedwire, ACH, Target2).
- Access real customer banking data or Personally Identifiable Information (PII).
- Interface with real blockchain or live Central Bank Digital Currency (CBDC) infrastructure.
- Provide cryptographic privacy guarantees (e.g., zero-knowledge proofs) or production-grade federated learning in this initial phase.

---

## 2. Security Boundaries & Development Hardening

1. **Localhost Binding:**
   The backend binds strictly to `127.0.0.1` (localhost) during local development to avoid unauthenticated external exposure.
2. **CORS Restrictions:**
   Cross-Origin Resource Sharing (CORS) is configured strictly for explicitly allowed frontend development origins (e.g., `http://localhost:5173`). Unrestricted wildcards (`*`) are disallowed.
3. **No Hardcoded Secrets:**
   All configuration is loaded via environment variables (`.env`). Default credentials are provided solely for local development and clearly labeled.
4. **SQL Injection Defense:**
   All persistence operations use SQLAlchemy 2.0 parameterized queries and ORM constructs. Raw string SQL concatenation is forbidden.
5. **No Production Exposure:**
   This local simulation prototype lacks authentication and role-based access control (RBAC). It must NOT be exposed to the public Internet or deployed into untrusted production environments without an enterprise authentication layer.

---

## 3. Data Integrity & Idempotency

- Ingestion uses bank code + native transaction reference composite keys to prevent duplicate transactions.
- Zero silent conversions: corrupted or unparseable bank messages raise explicit validation failures rather than coercing values.

