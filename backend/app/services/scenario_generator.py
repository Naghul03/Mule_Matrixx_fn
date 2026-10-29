import random
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.bank import Bank
from app.db.models.account import Account
from app.db.models.scenario_run import ScenarioRun
from app.db.models.transaction import Transaction
from app.db.models.ground_truth import GroundTruthLabel
from app.services.transaction_service import TransactionIngestionService


class ScenarioGeneratorService:
    """Configurable, reproducible scenario generation engine for simulated multi-bank transfers."""

    def __init__(self, db: Session):
        self.db = db
        self.ingestion_service = TransactionIngestionService(db)

    def _get_or_create_account(
        self, bank: Bank, account_ref: str, display_alias: str, classification: Optional[str] = None
    ) -> Account:
        acc = self.db.execute(
            select(Account).where(
                Account.bank_id == bank.id,
                Account.bank_account_reference == account_ref,
            )
        ).scalar_one_or_none()

        if not acc:
            acc = Account(
                id=str(uuid.uuid4()),
                bank_id=bank.id,
                bank_account_reference=account_ref,
                display_alias=display_alias,
                synthetic_classification=classification,
            )
            self.db.add(acc)
            self.db.flush()
        return acc

    def _create_native_payload_and_ingest(
        self,
        bank: Bank,
        native_ref: str,
        src_ref: str,
        dst_ref: str,
        amount: Decimal,
        currency: str,
        timestamp: datetime,
        scenario_run_id: str,
    ) -> Transaction:
        """Constructs bank-native payload conforming to the specific bank's adapter and ingests it."""
        code = bank.bank_code
        dt_utc = timestamp if timestamp.tzinfo else timestamp.replace(tzinfo=timezone.utc)

        if code == "BNK_A":
            # Modern REST JSON (Apex)
            raw = {
                "txn_id": native_ref,
                "src_account": src_ref,
                "dst_account": dst_ref,
                "txn_amount": str(amount.quantize(Decimal("0.0001"))),
                "currency_code": currency,
                "timestamp_iso": dt_utc.isoformat(),
                "status": "COMPLETED",
                "transfer_kind": "WIRE",
            }
        elif code == "BNK_B":
            # Mainframe Flat (Beacon)
            cents = int(amount * 100)
            raw = {
                "TRANSACTION_REF": native_ref,
                "SND_ACCT_NO": src_ref,
                "RCV_ACCT_NO": dst_ref,
                "TX_AMT_CENTS": cents,
                "CCY": currency,
                "TX_DATE": dt_utc.strftime("%Y%m%d"),
                "TX_TIME": dt_utc.strftime("%H%M%S"),
                "POST_STATUS": "SETTLED",
                "TX_CODE": "TRF",
            }
        elif code == "BNK_C":
            # ISO 20022 SEPA (Crestline)
            raw = {
                "endToEndId": native_ref,
                "debtorAccount": {"iban": src_ref},
                "creditorAccount": {"iban": dst_ref},
                "instructedAmount": {
                    "value": str(amount.quantize(Decimal("0.0001"))),
                    "currency": currency,
                },
                "bookingDateTime": dt_utc.isoformat(),
                "paymentStatus": "ACCP",
            }
        else:
            # Modern Fintech JSON (Delta Direct)
            epoch_ms = int(dt_utc.timestamp() * 1000)
            raw = {
                "payment_id": native_ref,
                "sender": {"account_id": src_ref},
                "recipient": {"account_id": dst_ref},
                "amount": str(amount.quantize(Decimal("0.0001"))),
                "currency": currency,
                "unix_epoch_ms": epoch_ms,
                "state": "succeeded",
                "type": "direct_transfer",
            }

        return self.ingestion_service.ingest_transaction(
            bank_code=code, raw_payload=raw, scenario_run_id=scenario_run_id
        )

    def generate_scenario(
        self,
        scenario_id: str,
        seed: int = 42,
        base_amount: Optional[Decimal] = None,
        num_attack_accounts: int = 5,
        num_decoys: int = 4,
        start_time: Optional[datetime] = None,
        custom_config: Optional[Dict[str, Any]] = None,
    ) -> ScenarioRun:
        """Master scenario generation entrypoint.

        Enforces:
        - attack accounts capped at 10
        - separate decoy population
        - isolated local PRNG
        - distinct native schemas normalized through adapters
        - ground truth stored strictly in ground_truth_labels
        """
        capped_attack_accounts = min(max(3, num_attack_accounts), 10)
        rng = random.Random(seed)

        effective_config = {
            "scenario_id": scenario_id,
            "seed": seed,
            "base_amount": str(base_amount) if base_amount else "default",
            "num_attack_accounts": capped_attack_accounts,
            "num_decoys": num_decoys,
            "custom_config": custom_config or {},
        }

        # Create ScenarioRun record
        run = ScenarioRun(
            id=str(uuid.uuid4()),
            domain="current_money",
            scenario_identifier=scenario_id,
            scenario_version="1.0.0",
            generator_version="1.0.0",
            seed=seed,
            configuration_json=effective_config,
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        self.db.flush()

        # Load banks
        banks = self.db.execute(select(Bank).order_by(Bank.bank_code)).scalars().all()
        if len(banks) < 4:
            raise ValueError("All 4 simulated banks must be seeded in database.")
        bank_map = {b.bank_code: b for b in banks}

        base_dt = start_time or (datetime(2026, 10, 20, 10, 0, 0, tzinfo=timezone.utc))

        try:
            if scenario_id == "scenario_1":
                self._generate_scenario_1(run.id, bank_map, rng, base_dt, base_amount, capped_attack_accounts)
            elif scenario_id == "scenario_3":
                self._generate_scenario_3(run.id, bank_map, rng, base_dt, base_amount)
            elif scenario_id == "scenario_4":
                self._generate_scenario_4(run.id, bank_map, rng, base_dt, base_amount, capped_attack_accounts)
            else:
                raise ValueError(f"Unknown scenario ID: {scenario_id}")

            # Generate realistic Decoy background population
            self._generate_decoys(run.id, bank_map, rng, base_dt, num_decoys)

            run.status = "COMPLETED"
            run.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            return run
        except Exception as e:
            self.db.rollback()
            run.status = "FAILED"
            run.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise e

    def _generate_scenario_1(
        self,
        run_id: str,
        banks: Dict[str, Bank],
        rng: random.Random,
        base_dt: datetime,
        base_amount: Optional[Decimal],
        num_accounts: int,
    ) -> None:
        """Scenario 1: Conventional money tracing chain.
        Victim -> Intermediary 1 -> Intermediary 2 -> ... -> Kingpin
        """
        amount = base_amount or Decimal("500000.0000")
        bank_codes = ["BNK_A", "BNK_B", "BNK_C", "BNK_D"]

        # 1. Victim Account
        victim_bank = banks[bank_codes[0]]
        victim_ref = f"ACC-VIC-{rng.randint(1000, 9999)}"
        victim_acc = self._get_or_create_account(victim_bank, victim_ref, "Victim Account", "victim")

        self.db.add(
            GroundTruthLabel(
                id=str(uuid.uuid4()),
                scenario_run_id=run_id,
                account_id=victim_acc.id,
                role_label="victim",
                expected_relationship="source",
                rationale="Victim account initiating unauthorized or defrauded transfer",
            )
        )

        # 2. Intermediary accounts + Kingpin
        intermediaries = []
        num_intermediaries = num_accounts - 2  # victim + intermediaries + kingpin = num_accounts
        for i in range(num_intermediaries):
            b_code = bank_codes[(i + 1) % len(bank_codes)]
            acc_ref = f"ACC-MULE{i+1}-{rng.randint(1000, 9999)}"
            acc = self._get_or_create_account(banks[b_code], acc_ref, f"Intermediary Mule {i+1}", "mule_layering")
            intermediaries.append(acc)
            self.db.add(
                GroundTruthLabel(
                    id=str(uuid.uuid4()),
                    scenario_run_id=run_id,
                    account_id=acc.id,
                    role_label="mule_layering",
                    expected_relationship="intermediary",
                    rationale=f"Layering mule node {i+1} in sequential pass-through chain",
                )
            )

        # Kingpin Account
        kingpin_bank = banks[bank_codes[-1]]
        kingpin_ref = f"ACC-KINGPIN-{rng.randint(1000, 9999)}"
        kingpin_acc = self._get_or_create_account(kingpin_bank, kingpin_ref, "Suspected Kingpin Account", "kingpin_coordinator")
        self.db.add(
            GroundTruthLabel(
                id=str(uuid.uuid4()),
                scenario_run_id=run_id,
                account_id=kingpin_acc.id,
                role_label="kingpin_coordinator",
                expected_relationship="destination_coordinator",
                rationale="Terminal aggregating account receiving laundered funds",
            )
        )

        # Sequence of transactions
        chain = [victim_acc] + intermediaries + [kingpin_acc]
        curr_dt = base_dt
        curr_amount = amount

        for idx in range(len(chain) - 1):
            src = chain[idx]
            dst = chain[idx + 1]
            src_bank = self.db.get(Bank, src.bank_id)

            # Fast pass-through: 15 to 45 mins between hops
            gap_minutes = rng.randint(15, 45)
            curr_dt += timedelta(minutes=gap_minutes)

            # Small fee deduction to simulate real-world cut
            if idx > 0:
                fee = Decimal(rng.randint(1000, 3000))
                curr_amount = max(Decimal("1000.0000"), curr_amount - fee)

            tx_ref = f"TX-S1-{idx+1}-{rng.randint(100000, 999999)}"
            txn = self._create_native_payload_and_ingest(
                bank=src_bank,
                native_ref=tx_ref,
                src_ref=src.bank_account_reference,
                dst_ref=dst.bank_account_reference,
                amount=curr_amount,
                currency="INR",
                timestamp=curr_dt,
                scenario_run_id=run_id,
            )

            self.db.add(
                GroundTruthLabel(
                    id=str(uuid.uuid4()),
                    scenario_run_id=run_id,
                    transaction_id=txn.id,
                    role_label="layering_transfer",
                    expected_relationship="chain_hop",
                    rationale=f"Hop {idx+1} in direct money trace",
                )
            )

    def _generate_scenario_3(
        self,
        run_id: str,
        banks: Dict[str, Bank],
        rng: random.Random,
        base_dt: datetime,
        base_amount: Optional[Decimal],
    ) -> None:
        """Scenario 3: Pre-positioned transfers and delayed replenishment.

        DAY 0:
        B -> D : ₹2,00,000 (Historical relationship)
        C -> D : ₹2,00,000 (Historical relationship)

        DAY 2:
        Victim -> A : ₹4,00,000 (Victim transfer)

        DAY 3:
        A -> B : ₹2,00,000 (Delayed replenishment)
        A -> C : ₹2,00,000 (Delayed replenishment)

        Ground truth:
        - Victim: victim (NOT mule)
        - A: primary layering mule
        - B, C: pre-positioned mules / layering intermediaries
        - D: coordinating kingpin (ranks #1)
        """
        amt_each = (base_amount / Decimal(2)) if base_amount else Decimal("200000.0000")
        amt_total = amt_each * Decimal(2)

        bank_a = banks["BNK_A"]
        bank_b = banks["BNK_B"]
        bank_c = banks["BNK_C"]
        bank_d = banks["BNK_D"]

        # Accounts
        vic_ref = f"ACC-S3-VIC-{rng.randint(1000, 9999)}"
        acc_a_ref = f"ACC-S3-A-{rng.randint(1000, 9999)}"
        acc_b_ref = f"ACC-S3-B-{rng.randint(1000, 9999)}"
        acc_c_ref = f"ACC-S3-C-{rng.randint(1000, 9999)}"
        acc_d_ref = f"ACC-S3-D-{rng.randint(1000, 9999)}"

        vic = self._get_or_create_account(bank_a, vic_ref, "Victim (S3)", "victim")
        acc_a = self._get_or_create_account(bank_a, acc_a_ref, "Mule Node A", "mule_layering")
        acc_b = self._get_or_create_account(bank_b, acc_b_ref, "Mule Node B", "mule_layering")
        acc_c = self._get_or_create_account(bank_c, acc_c_ref, "Mule Node C", "mule_layering")
        acc_d = self._get_or_create_account(bank_d, acc_d_ref, "Kingpin D", "kingpin_coordinator")

        # Ground truth labels
        labels = [
            (vic.id, None, "victim", "originator", "Victim entity who initiated the primary defrauded transfer"),
            (acc_a.id, None, "mule_layering", "funnel_distributor", "Account A receiving victim funds and replenishing B and C"),
            (acc_b.id, None, "mule_layering", "pre_positioned_intermediary", "Account B pre-funding D and receiving delayed replenishment from A"),
            (acc_c.id, None, "mule_layering", "pre_positioned_intermediary", "Account C pre-funding D and receiving delayed replenishment from A"),
            (acc_d.id, None, "kingpin_coordinator", "beneficiary_kingpin", "Kingpin D coordinating the pre-positioned network"),
        ]
        for acc_id, txn_id, role, rel, rat in labels:
            self.db.add(
                GroundTruthLabel(
                    id=str(uuid.uuid4()),
                    scenario_run_id=run_id,
                    account_id=acc_id,
                    transaction_id=txn_id,
                    role_label=role,
                    expected_relationship=rel,
                    rationale=rat,
                )
            )

        # Timestamps
        day_0 = base_dt
        day_2 = base_dt + timedelta(days=2)
        day_3 = base_dt + timedelta(days=3)

        # 1. DAY 0: Pre-positioned transfers B -> D and C -> D (HISTORICAL)
        t_b_d = self._create_native_payload_and_ingest(
            bank=bank_b,
            native_ref=f"TX-S3-BD-{rng.randint(100000, 999999)}",
            src_ref=acc_b.bank_account_reference,
            dst_ref=acc_d.bank_account_reference,
            amount=amt_each,
            currency="INR",
            timestamp=day_0 + timedelta(hours=10),
            scenario_run_id=run_id,
        )
        t_c_d = self._create_native_payload_and_ingest(
            bank=bank_c,
            native_ref=f"TX-S3-CD-{rng.randint(100000, 999999)}",
            src_ref=acc_c.bank_account_reference,
            dst_ref=acc_d.bank_account_reference,
            amount=amt_each,
            currency="INR",
            timestamp=day_0 + timedelta(hours=11, minutes=30),
            scenario_run_id=run_id,
        )

        # 2. DAY 2: Victim -> A ₹4,00,000 (DIRECT VICTIM INCOMING)
        t_vic_a = self._create_native_payload_and_ingest(
            bank=bank_a,
            native_ref=f"TX-S3-VICA-{rng.randint(100000, 999999)}",
            src_ref=vic.bank_account_reference,
            dst_ref=acc_a.bank_account_reference,
            amount=amt_total,
            currency="INR",
            timestamp=day_2 + timedelta(hours=14),
            scenario_run_id=run_id,
        )

        # 3. DAY 3: A -> B ₹2,00,000 and A -> C ₹2,00,000 (DELAYED REPLENISHMENT)
        t_a_b = self._create_native_payload_and_ingest(
            bank=bank_a,
            native_ref=f"TX-S3-AB-{rng.randint(100000, 999999)}",
            src_ref=acc_a.bank_account_reference,
            dst_ref=acc_b.bank_account_reference,
            amount=amt_each,
            currency="INR",
            timestamp=day_3 + timedelta(hours=9, minutes=15),
            scenario_run_id=run_id,
        )
        t_a_c = self._create_native_payload_and_ingest(
            bank=bank_a,
            native_ref=f"TX-S3-AC-{rng.randint(100000, 999999)}",
            src_ref=acc_a.bank_account_reference,
            dst_ref=acc_c.bank_account_reference,
            amount=amt_each,
            currency="INR",
            timestamp=day_3 + timedelta(hours=10, minutes=45),
            scenario_run_id=run_id,
        )

        # Transaction ground truth labels
        txn_labels = [
            (t_b_d.id, "historical_preposition", "B to D pre-position transfer prior to victim event"),
            (t_c_d.id, "historical_preposition", "C to D pre-position transfer prior to victim event"),
            (t_vic_a.id, "victim_fraud_event", "Direct victim transfer to node A"),
            (t_a_b.id, "delayed_replenishment", "Replenishment from A to B following victim funds"),
            (t_a_c.id, "delayed_replenishment", "Replenishment from A to C following victim funds"),
        ]
        for tid, r_label, rat in txn_labels:
            self.db.add(
                GroundTruthLabel(
                    id=str(uuid.uuid4()),
                    scenario_run_id=run_id,
                    transaction_id=tid,
                    role_label=r_label,
                    rationale=rat,
                )
            )

    def _generate_scenario_4(
        self,
        run_id: str,
        banks: Dict[str, Bank],
        rng: random.Random,
        base_dt: datetime,
        base_amount: Optional[Decimal],
        num_accounts: int,
    ) -> None:
        """Scenario 4: Fragmented transfers (Structuring).
        Total amount: ₹9,60,000 in 8 structured transfers of ₹1,20,000 each.
        Smurfs / Sub-accounts -> Collector / Aggregator
        """
        each_amount = base_amount or Decimal("120000.0000")
        num_transfers = 8
        total_amount = each_amount * Decimal(num_transfers)

        bank_a = banks["BNK_A"]
        bank_b = banks["BNK_B"]
        bank_c = banks["BNK_C"]
        bank_d = banks["BNK_D"]
        bank_list = [bank_a, bank_b, bank_c, bank_d]

        # Target collector
        collector_ref = f"ACC-S4-COLL-{rng.randint(1000, 9999)}"
        collector_acc = self._get_or_create_account(bank_d, collector_ref, "Structuring Collector", "mule_collector")

        self.db.add(
            GroundTruthLabel(
                id=str(uuid.uuid4()),
                scenario_run_id=run_id,
                account_id=collector_acc.id,
                role_label="kingpin_coordinator",
                expected_relationship="structuring_collector",
                rationale="Collector node aggregating structured smurfing deposits",
            )
        )

        # Smurf source accounts
        smurf_accounts = []
        num_smurfs = min(num_accounts - 1, 6)
        for i in range(num_smurfs):
            b = bank_list[i % len(bank_list)]
            s_ref = f"ACC-S4-SMURF{i+1}-{rng.randint(1000, 9999)}"
            s_acc = self._get_or_create_account(b, s_ref, f"Smurf Account {i+1}", "smurf")
            smurf_accounts.append(s_acc)

            self.db.add(
                GroundTruthLabel(
                    id=str(uuid.uuid4()),
                    scenario_run_id=run_id,
                    account_id=s_acc.id,
                    role_label="smurf",
                    expected_relationship="structuring_smurf",
                    rationale=f"Smurfing account {i+1} executing repetitive sub-threshold transfers",
                )
            )

        # 8 transfers distributed across smurfs within a compact time window
        curr_dt = base_dt
        for t_idx in range(num_transfers):
            smurf = smurf_accounts[t_idx % len(smurf_accounts)]
            smurf_bank = self.db.get(Bank, smurf.bank_id)

            curr_dt += timedelta(minutes=rng.randint(20, 60))
            tx_ref = f"TX-S4-STR-{t_idx+1}-{rng.randint(100000, 999999)}"

            txn = self._create_native_payload_and_ingest(
                bank=smurf_bank,
                native_ref=tx_ref,
                src_ref=smurf.bank_account_reference,
                dst_ref=collector_acc.bank_account_reference,
                amount=each_amount,
                currency="INR",
                timestamp=curr_dt,
                scenario_run_id=run_id,
            )

            self.db.add(
                GroundTruthLabel(
                    id=str(uuid.uuid4()),
                    scenario_run_id=run_id,
                    transaction_id=txn.id,
                    role_label="structuring_fragment",
                    expected_relationship="smurfing_flow",
                    rationale=f"Structured transfer {t_idx+1} of {each_amount} under reporting threshold",
                )
            )

    def _generate_decoys(
        self,
        run_id: str,
        banks: Dict[str, Bank],
        rng: random.Random,
        base_dt: datetime,
        num_decoys: int,
    ) -> None:
        """Generates legitimate synthetic background population:
        1. High-fan-in merchant account with regular consumer payments.
        2. Salary payroll account with recurring disbursements.
        3. Normal commercial business account with routine supplier payments.
        """
        bank_list = list(banks.values())

        # 1. Merchant Account
        merchant_bank = bank_list[0]
        merchant_ref = f"ACC-DEC-MERCH-{rng.randint(1000, 9999)}"
        merchant_acc = self._get_or_create_account(
            merchant_bank, merchant_ref, "Metro Supermarket Decoy", "decoy_merchant"
        )
        self.db.add(
            GroundTruthLabel(
                id=str(uuid.uuid4()),
                scenario_run_id=run_id,
                account_id=merchant_acc.id,
                role_label="decoy_merchant",
                expected_relationship="legitimate_commercial",
                rationale="Legitimate retail merchant with high fan-in consumer purchases",
            )
        )

        # 3-5 retail shopper deposits to merchant
        for c in range(3):
            cust_bank = bank_list[(c + 1) % len(bank_list)]
            cust_ref = f"ACC-DEC-CUST{c+1}-{rng.randint(1000, 9999)}"
            cust_acc = self._get_or_create_account(cust_bank, cust_ref, f"Shopper {c+1}", "decoy_consumer")

            tx_time = base_dt + timedelta(hours=rng.randint(2, 48), minutes=rng.randint(5, 50))
            amt = Decimal(rng.randint(500, 4500))

            self._create_native_payload_and_ingest(
                bank=cust_bank,
                native_ref=f"TX-DEC-RTL-{c+1}-{rng.randint(100000, 999999)}",
                src_ref=cust_acc.bank_account_reference,
                dst_ref=merchant_acc.bank_account_reference,
                amount=amt,
                currency="INR",
                timestamp=tx_time,
                scenario_run_id=run_id,
            )

        # 2. Corporate Payroll Account
        payroll_bank = bank_list[1 % len(bank_list)]
        payroll_ref = f"ACC-DEC-CORP-{rng.randint(1000, 9999)}"
        payroll_acc = self._get_or_create_account(
            payroll_bank, payroll_ref, "Apex Corp Payroll", "decoy_payroll"
        )
        self.db.add(
            GroundTruthLabel(
                id=str(uuid.uuid4()),
                scenario_run_id=run_id,
                account_id=payroll_acc.id,
                role_label="decoy_payroll",
                expected_relationship="legitimate_salary",
                rationale="Legitimate corporate account disbursing monthly payroll",
            )
        )

        # 2 employee salary transfers
        for e in range(2):
            emp_bank = bank_list[(e + 2) % len(bank_list)]
            emp_ref = f"ACC-DEC-EMP{e+1}-{rng.randint(1000, 9999)}"
            emp_acc = self._get_or_create_account(emp_bank, emp_ref, f"Employee {e+1}", "decoy_employee")

            tx_time = base_dt + timedelta(hours=rng.randint(6, 24))
            sal_amt = Decimal(rng.randint(45000, 95000))

            self._create_native_payload_and_ingest(
                bank=payroll_bank,
                native_ref=f"TX-DEC-SAL-{e+1}-{rng.randint(100000, 999999)}",
                src_ref=payroll_acc.bank_account_reference,
                dst_ref=emp_acc.bank_account_reference,
                amount=sal_amt,
                currency="INR",
                timestamp=tx_time,
                scenario_run_id=run_id,
            )

