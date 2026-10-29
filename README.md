# Mule Matrix

> **Follow the Money. Uncover the Network.**

Mule Matrix is a multi-bank financial transaction investigation and suspicious money-flow detection platform. It simulates multilateral financial activity across distinct banking institutions to identify money mule accounts, layering chains, cash-out funnels, and coordinating kingpins.

The platform encompasses two core sections:
1. **Current Money Transactions:** Simulated conventional multi-bank transfer and wire environment.
2. **CBDC Tokens:** Simulated digital-currency token ledger with UTXO-like unspent token provenance (implemented in Module 6).

---

## Module 1: Foundation & Database

This release implements **Module 1 (Foundation & Database)**:
- Core modular monolith architecture (FastAPI backend + React/Vite/Tailwind frontend).
- MySQL database schema managed exclusively via **Alembic migrations**.
- Exact decimal monetary arithmetic (`DECIMAL(18, 4)` / Python `Decimal`).
- Four independent simulated bank adapters (Bank A, B, C, D) normalizing diverse native schemas into a canonical transaction contract.
- Separation of operational transaction streams from synthetic ground-truth evaluation labels.
- Dual-section UI shell adhering to the Mule Matrix design identity (`#090907` background, Earth Brown `#6C5636`, Burnt Amber `#B99D73`).
- Health and database connectivity verification endpoints.

---

## Tech Stack

- **Backend:** Python 3.10+, FastAPI, Pydantic v2, SQLAlchemy 2.0, Alembic, PyMySQL, Pytest
- **Database:** MySQL 8.0 (strict InnoDB, `utf8mb4`)
- **Frontend:** React 18, TypeScript 5, Vite, Tailwind CSS, React Router v6, Lucide Icons

---

## Project Structure

```text
mule-matrix/
├── CLAUDE.md                   # Persistent non-negotiable project rules
├── README.md                   # Project setup and documentation
├── .gitignore                  # Git ignore rules
├── .env.example                # Environment template
├── docker-compose.yml          # Optional local MySQL container
├── docs/
│   ├── architecture.md         # System architecture & modular monolith design
│   ├── database-schema.md      # Detailed table specifications & constraints
│   ├── transaction-contract.md # Canonical transaction & 4 bank adapter schemas
│   ├── security-and-limitations.md # Security boundaries & prototype limitations
│   └── module-acceptance-criteria.md # Verification checklist
├── backend/
│   ├── pyproject.toml          # Python project & dependencies
│   ├── alembic.ini             # Alembic migration configuration
│   ├── alembic/                # Migration scripts (0001_initial_foundation.py)
│   ├── app/
│   │   ├── main.py             # FastAPI entrypoint & CORS setup
│   │   ├── core/               # Settings & structured logging
│   │   ├── api/                # Health & connectivity endpoints
│   │   ├── db/                 # Base, session, and SQLAlchemy models
│   │   ├── schemas/            # Canonical transaction & Pydantic contracts
│   │   ├── adapters/           # Bank A, B, C, D normalization adapters
│   │   └── services/           # Ingestion & idempotency service
│   └── tests/
│       ├── conftest.py         # Test fixtures & database isolation
│       ├── unit/               # Adapter, canonical schema, and isolation tests
│       └── integration/        # MySQL model, constraint, and API tests
└── frontend/
    ├── package.json            # Node dependencies
    ├── vite.config.ts          # Vite configuration
    ├── tsconfig.json           # TypeScript configuration
    ├── tailwind.config.js      # Approved Mule Matrix design tokens
    └── src/
        ├── app/                # React App entrypoint
        ├── components/         # Reusable design token components
        ├── layouts/            # Shared RootLayout with sidebar & header
        ├── pages/              # Overview, Placeholders, NotFound
        ├── routes/             # Client-side router
        ├── services/           # Typed backend API client
        └── types/              # TypeScript data contracts
```

---

## Setup & Local Development Instructions

### 1. Prerequisites
- **Python:** 3.10 or higher
- **Node.js:** 18 or higher (with npm)
- **MySQL:** 8.0 (local installation or via Docker Compose)

### 2. Environment Configuration
Copy `.env.example` to `.env` in the project root:
```bash
cp .env.example .env
```
Ensure database credentials match your local MySQL server:
```ini
DB_HOST=127.0.0.1
DB_PORT=3306
DB_NAME=mule_matrix
DB_USER=root
DB_PASSWORD=your_password_here

BACKEND_HOST=127.0.0.1
BACKEND_PORT=8000
ENVIRONMENT=development
CORS_ORIGINS=http://localhost:5173,http://127.0.0.1:5173
VITE_API_BASE_URL=http://127.0.0.1:8000/api/v1
```

*(Optional: If using Docker for MySQL)*:
```bash
docker compose up -d
```

### 3. Database Migration with Alembic
Ensure the target database exists in MySQL:
```sql
CREATE DATABASE IF NOT EXISTS mule_matrix CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

Run migrations from the `backend/` directory:
```bash
cd backend
python -m alembic upgrade head
```

To test migration downgrade and re-upgrade:
```bash
python -m alembic downgrade base
python -m alembic upgrade head
```

### 4. Running the Backend
From `backend/`:
```bash
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```
Interactive API documentation will be available at:
- **Swagger UI:** [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
- **ReDoc:** [http://127.0.0.1:8000/redoc](http://127.0.0.1:8000/redoc)
- **Health check:** [http://127.0.0.1:8000/api/v1/health](http://127.0.0.1:8000/api/v1/health)
- **Database health:** [http://127.0.0.1:8000/api/v1/health/database](http://127.0.0.1:8000/api/v1/health/database)

### 5. Running the Frontend
From `frontend/`:
```bash
cd frontend
npm install
npm run dev
```
Open [http://localhost:5173](http://localhost:5173) in your browser.

To verify production build compilation:
```bash
npm run build
```

---

## Automated Test Suite

Run unit and integration tests from `backend/`:
```bash
cd backend
python -m pytest -v
```

The test suite covers:
- **Bank Adapters (Unit):** Valid normalization, negative amounts, missing fields, identical self-transfers, invalid timestamps, and registry lookups across Bank A, Bank B, Bank C, and Bank D.
- **Canonical Schema (Unit):** Exact decimal enforcement, positive amounts, timezone-awareness validation, currency format, and self-transfer rejection.
- **Ground-Truth Isolation (Unit):** Strict verification that transaction, account, and bank contracts contain zero ground-truth leakage.
- **Database Integrity (Integration):** Foreign keys, bank account reference uniqueness, decimal precision retention (`DECIMAL(18, 4)`), check constraint enforcement (`ck_transactions_no_self_transfer`), and multi-transfer coexistence.
- **Health APIs (Integration):** Service health check and database connectivity verification with latency measurement and error handling.

---

## Simulated Bank Adapters Reference

| Bank | Institution Name | Adapter ID | Native Schema Format | Key Features |
| :--- | :--- | :--- | :--- | :--- |
| **BNK_A** | Apex National Bank | `bank_a_adapter_v1` | Modern REST JSON | ISO-8601 UTC string, decimal string amounts, wire kinds |
| **BNK_B** | Beacon Commercial Bank | `bank_b_adapter_v1` | Mainframe Flat | Integer cents (`TX_AMT_CENTS`), split `YYYYMMDD` date & `HHMMSS` time |
| **BNK_C** | Crestline Trust | `bank_c_adapter_v1` | ISO 20022 SEPA | Nested debtor/creditor with IBAN, instructed amount with currency, `ACCP`/`PDNG` codes |
| **BNK_D** | Delta Direct | `bank_d_adapter_v1` | Modern Fintech JSON | Unix epoch ms timestamp, nested `sender`/`recipient`, lowercase states |

---

## Troubleshooting Common Database Connection Errors

1. **Access Denied / Password Error (`1045`):**
   - Verify `DB_USER` and `DB_PASSWORD` in `.env`.
   - Test directly: `python -c "import pymysql; pymysql.connect(host='127.0.0.1', user='root', password='YOUR_PASSWORD')"`

2. **Database Does Not Exist (`1049`):**
   - Create the database: `CREATE DATABASE mule_matrix;`

3. **Connection Refused / Port Blocked (`2003`):**
   - Verify MySQL service is running on `127.0.0.1:3306`.
   - On Windows, ensure local socket access is allowed.

#   M u l e _ M a t r i x x _ f n  
 