# Mule Matrix — Canonical Transaction Contract & Bank Adapters

## 1. Canonical Transaction Schema

The Canonical Transaction contract defines the standardized format to which all incoming simulated bank transactions must conform. Regardless of the native system format, every transaction ingested into Mule Matrix is validated and converted into this canonical structure.

### 1.1 Canonical Fields

| Field Name | Type | Description | Required | Validation Constraints |
| :--- | :--- | :--- | :--- | :--- |
| `native_bank_code` | `str` | Standardized bank code (e.g. `BNK_A`) | Yes | Non-empty string, matches registered bank |
| `native_transaction_reference` | `str` | Source transaction identifier | Yes | Non-empty string, max 128 characters |
| `source_account_reference` | `str` | Debtor / sender account reference | Yes | Non-empty string, max 64 characters |
| `destination_account_reference` | `str` | Creditor / recipient account reference | Yes | Non-empty string, max 64 characters |
| `amount` | `Decimal` | Exact monetary value | Yes | Strictly positive (`amount > 0`), max 4 decimal places |
| `currency` | `str` | ISO 4217 currency code | Yes | Exact 3 uppercase ASCII letters (e.g., `USD`, `EUR`, `GBP`) |
| `event_timestamp` | `datetime` | Exact time the transaction occurred | Yes | UTC timezone-aware datetime |
| `normalized_type` | `TransactionType` | Normalized type of transfer | Yes | Enum: `TRANSFER`, `PAYMENT`, `SETTLEMENT` |
| `status` | `TransactionStatus` | Normalized execution status | Yes | Enum: `COMPLETED`, `PENDING`, `REJECTED`, `FAILED` |
| `source_adapter_version` | `str` | Adapter identifier and version | Yes | Non-empty string (e.g., `bank_a_adapter_v1`) |
| `raw_payload` | `Dict[str, Any]` | Pristine original payload | Yes | Faithful JSON-serializable dictionary |
| `normalization_metadata` | `Dict[str, Any]` | Transformation metadata & diagnostics | Yes | Contains `normalized_at` (UTC ISO string), adapter id |

### 1.2 Invariant Validation Rules

1. **Strict Positive Amounts:** `amount` must be greater than zero. Non-positive numbers, zero amounts, and non-numeric representations are strictly rejected with validation errors.
2. **No Self-Transfers:** `source_account_reference != destination_account_reference` within the same bank transfer context.
3. **No Silent Coercions:**
   - Floats are forbidden in input schemas where precision can be lost. Strings or integer cents are parsed directly into `Decimal`.
   - Incomplete or ambiguous dates (e.g. missing timezone) are not silently assumed if format specification dictates explicit offsets.
   - Missing fields are not filled with invented defaults.
4. **Idempotency & Provenance:** The original native payload is preserved untouched in `raw_payload`.

---

## 2. Simulated Bank Native Schemas and Adapters

To reflect real-world financial heterogeneity across institutions, Mule Matrix implements four distinct simulated bank adapters.

### 2.1 Bank A Adapter (`bank_a_adapter_v1`) — Apex National Bank
- **Design:** Modern REST JSON API with nested payload conventions.
- **Native Schema Fields:**
  - `txn_id` (string): Native identifier (e.g. `TXA-849201948`)
  - `src_account` (string): Source account number (e.g. `ACC-A-10293`)
  - `dst_account` (string): Target account number (e.g. `ACC-A-84920`)
  - `txn_amount` (string or number): Exact decimal string (e.g. `"1450.50"`)
  - `currency_code` (string): 3-letter currency code (e.g. `"USD"`)
  - `timestamp_iso` (string): ISO 8601 formatted timestamp with UTC indicator (e.g. `"2026-10-28T14:30:00Z"`)
  - `status` (string): Native status (`COMPLETED`, `PENDING`, `FAILED`)
  - `transfer_kind` (string, optional): E.g. `"WIRE"`, `"ACH"` -> maps to `TRANSFER` or `PAYMENT`

### 2.2 Bank B Adapter (`bank_b_adapter_v1`) — Beacon Commercial Bank
- **Design:** Core-banking mainframe uppercase flat schema with split date and time.
- **Native Schema Fields:**
  - `TRANSACTION_REF` (string): E.g. `"BNKB-9948210"`
  - `SND_ACCT_NO` (string): E.g. `"BKN-002934"`
  - `RCV_ACCT_NO` (string): E.g. `"BKN-883921"`
  - `TX_AMT_CENTS` (integer): Amount in integer cents (e.g. `145050` = `1450.50`)
  - `CCY` (string): E.g. `"USD"`
  - `TX_DATE` (string): Format `"YYYYMMDD"` (e.g. `"20261028"`)
  - `TX_TIME` (string): Format `"HHMMSS"` (e.g. `"143000"`)
  - `POST_STATUS` (string): Native status (`SETTLED` -> `COMPLETED`, `QUEUED` -> `PENDING`, `DECLINED` -> `REJECTED`)
  - `TX_CODE` (string): Code e.g. `"TRF"` -> `TRANSFER`

### 2.3 Bank C Adapter (`bank_c_adapter_v1`) — Crestline Trust
- **Design:** ISO 20022 / SEPA camt/pain payment messaging model.
- **Native Schema Fields:**
  - `endToEndId` (string): Unique end-to-end message identifier (e.g. `"E2E-C-77401928"`)
  - `debtorAccount` (dict): `{"iban": "CRST-DEBT-9012"}`
  - `creditorAccount` (dict): `{"iban": "CRST-CRED-4491"}`
  - `instructedAmount` (dict): `{"value": "1250.75", "currency": "USD"}`
  - `bookingDateTime` (string): Standard ISO-8601 with timezone offset (e.g. `"2026-10-28T14:30:00+00:00"`)
  - `paymentStatus` (string): ISO 20022 codes (`ACCP` -> `COMPLETED`, `PDNG` -> `PENDING`, `RJCT` -> `REJECTED`)

### 2.4 Bank D Adapter (`bank_d_adapter_v1`) — Delta Direct (Fintech)
- **Design:** Modern developer-first fintech payload with Unix millisecond epoch timestamp and nested party objects.
- **Native Schema Fields:**
  - `payment_id` (string): Unique string ID (e.g. `"pay_d_93401824"`)
  - `sender` (dict): `{"account_id": "DD-SND-1928"}`
  - `recipient` (dict): `{"account_id": "DD-REC-9912"}`
  - `amount` (string or number): Exact decimal string or positive number (e.g. `"500.00"`)
  - `currency` (string): `"USD"`
  - `unix_epoch_ms` (integer): Milliseconds since Unix epoch (e.g. `1793197800000`)
  - `state` (string): Native state (`succeeded` -> `COMPLETED`, `processing` -> `PENDING`, `canceled` -> `FAILED`)
  - `type` (string): `"direct_transfer"` -> `TRANSFER`

---

## 3. Normalization Interface

Every adapter implements the `BaseBankAdapter` contract:
```python
class BaseBankAdapter(ABC):
    @property
    @abstractmethod
    def bank_code(self) -> str:
        ...

    @property
    @abstractmethod
    def adapter_version(self) -> str:
        ...

    @abstractmethod
    def normalize(self, raw_record: Dict[str, Any]) -> CanonicalTransaction:
        """Validates native input and transforms into CanonicalTransaction.
        Raises BankAdapterValidationError on invalid or malformed data.
        """
        ...
```

---

## 4. Error Handling and Diagnostics

Validation errors raise `BankAdapterValidationError` with:
- `adapter`: Adapter identifier
- `field`: Specific field causing failure
- `reason`: Actionable, plain-language explanation of why validation failed
- `raw_value`: The faulty value received
No silent conversions (such as dropping precision or substituting fake timestamps) are permitted.

