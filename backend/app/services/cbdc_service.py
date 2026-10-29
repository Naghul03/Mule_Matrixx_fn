from datetime import datetime, timedelta, timezone
from decimal import Decimal
import random
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.scenario_run import ScenarioRun
from app.db.models.cbdc import CBDCWallet, CBDCTokenLot, CBDCLedgerEvent, CBDCGroundTruth
from app.db.models.alert import Alert
from app.db.models.case import Case, CaseAlert


class CBDCService:
    """Simulated Central Bank Digital Currency (CBDC) token ledger and provenance engine."""

    def __init__(self, db: Session):
        self.db = db

    def _get_or_create_wallet(
        self,
        address: str,
        display_name: str,
        wallet_type: str,
        initial_balance: Decimal = Decimal("0.0000"),
        classification: Optional[str] = None,
    ) -> CBDCWallet:
        wallet = self.db.execute(
            select(CBDCWallet).where(CBDCWallet.wallet_address == address)
        ).scalar_one_or_none()

        if not wallet:
            wallet = CBDCWallet(
                id=str(uuid.uuid4()),
                wallet_address=address,
                display_name=display_name,
                wallet_type=wallet_type,
                balance=initial_balance,
                synthetic_classification=classification,
                is_active=True,
            )
            self.db.add(wallet)
            self.db.flush()
        return wallet

    def issue_tokens(
        self,
        issuer_wallet: CBDCWallet,
        target_wallet: CBDCWallet,
        amount: Decimal,
        scenario_run_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[CBDCTokenLot, CBDCLedgerEvent]:
        """Mints a new token lot from the Central Bank Issuer into a target wallet."""
        event_time = timestamp or datetime.now(timezone.utc)
        event_id = str(uuid.uuid4())

        # Create new Token Lot
        lot_ref = f"LOT-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:8].upper()}"
        lot = CBDCTokenLot(
            id=str(uuid.uuid4()),
            lot_reference=lot_ref,
            current_holder_wallet_id=target_wallet.id,
            amount=amount,
            currency="INR",
            status="ACTIVE",
            origin_event_id=event_id,
        )
        self.db.add(lot)
        self.db.flush()

        # Create Ledger Event
        event = CBDCLedgerEvent(
            id=event_id,
            scenario_run_id=scenario_run_id,
            event_type="ISSUANCE",
            from_wallet_id=issuer_wallet.id,
            to_wallet_id=target_wallet.id,
            amount=amount,
            currency="INR",
            event_timestamp=event_time,
            parent_lot_ids=None,
            child_lot_ids=[lot.id],
            metadata_json={"minting_authority": issuer_wallet.wallet_address},
        )
        self.db.add(event)

        # Update balance
        target_wallet.balance += amount
        self.db.flush()
        return lot, event

    def split_token_lot(
        self,
        parent_lot: CBDCTokenLot,
        split_amounts: List[Decimal],
        scenario_run_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[List[CBDCTokenLot], CBDCLedgerEvent]:
        """Conservation rule: sum(split_amounts) must strictly equal parent_lot.amount."""
        total_split = sum(split_amounts, Decimal("0.0000"))
        if total_split != parent_lot.amount:
            raise ValueError(
                f"CBDC Conservation Violation: Split sum {total_split} does not equal parent lot amount {parent_lot.amount}"
            )

        event_time = timestamp or datetime.now(timezone.utc)
        event_id = str(uuid.uuid4())

        # Mark parent lot as SPENT
        parent_lot.status = "SPENT"

        child_lots = []
        child_lot_ids = []
        for idx, amt in enumerate(split_amounts):
            lot_ref = f"LOT-SPLIT-{uuid.uuid4().hex[:8].upper()}"
            child_lot = CBDCTokenLot(
                id=str(uuid.uuid4()),
                lot_reference=lot_ref,
                current_holder_wallet_id=parent_lot.current_holder_wallet_id,
                amount=amt,
                currency="INR",
                status="ACTIVE",
                origin_event_id=event_id,
            )
            self.db.add(child_lot)
            child_lots.append(child_lot)
            child_lot_ids.append(child_lot.id)

        self.db.flush()

        event = CBDCLedgerEvent(
            id=event_id,
            scenario_run_id=scenario_run_id,
            event_type="SPLIT",
            from_wallet_id=parent_lot.current_holder_wallet_id,
            to_wallet_id=parent_lot.current_holder_wallet_id,
            amount=parent_lot.amount,
            currency="INR",
            event_timestamp=event_time,
            parent_lot_ids=[parent_lot.id],
            child_lot_ids=child_lot_ids,
            metadata_json={"num_children": len(child_lots)},
        )
        self.db.add(event)
        self.db.flush()
        return child_lots, event

    def transfer_token_lot(
        self,
        lot: CBDCTokenLot,
        to_wallet: CBDCWallet,
        scenario_run_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> CBDCLedgerEvent:
        """Transfers an active token lot to another wallet."""
        if lot.status != "ACTIVE":
            raise ValueError(f"Cannot transfer token lot with status {lot.status}")

        from_wallet = self.db.get(CBDCWallet, lot.current_holder_wallet_id)
        if not from_wallet:
            raise ValueError("Sender wallet not found")

        if from_wallet.balance < lot.amount:
            raise ValueError("Insufficient wallet balance for token transfer")

        event_time = timestamp or datetime.now(timezone.utc)
        event_id = str(uuid.uuid4())

        # Update balances
        from_wallet.balance -= lot.amount
        to_wallet.balance += lot.amount

        # Update holder
        lot.current_holder_wallet_id = to_wallet.id

        event = CBDCLedgerEvent(
            id=event_id,
            scenario_run_id=scenario_run_id,
            event_type="TRANSFER",
            from_wallet_id=from_wallet.id,
            to_wallet_id=to_wallet.id,
            amount=lot.amount,
            currency="INR",
            event_timestamp=event_time,
            parent_lot_ids=[lot.id],
            child_lot_ids=[lot.id],
            metadata_json={"lot_reference": lot.lot_reference},
        )
        self.db.add(event)
        self.db.flush()
        return event

    def merge_token_lots(
        self,
        parent_lots: List[CBDCTokenLot],
        scenario_run_id: Optional[str] = None,
        timestamp: Optional[datetime] = None,
    ) -> Tuple[CBDCTokenLot, CBDCLedgerEvent]:
        """Merges multiple active token lots held by the same wallet into one consolidated lot."""
        if not parent_lots:
            raise ValueError("Cannot merge empty lot list")

        wallet_id = parent_lots[0].current_holder_wallet_id
        if any(l.current_holder_wallet_id != wallet_id for l in parent_lots):
            raise ValueError("All lots to merge must be held by the same wallet")

        total_amount = sum((l.amount for l in parent_lots), Decimal("0.0000"))
        event_time = timestamp or datetime.now(timezone.utc)
        event_id = str(uuid.uuid4())

        parent_lot_ids = []
        for l in parent_lots:
            l.status = "MERGED"
            parent_lot_ids.append(l.id)

        merged_lot_ref = f"LOT-MERGE-{uuid.uuid4().hex[:8].upper()}"
        merged_lot = CBDCTokenLot(
            id=str(uuid.uuid4()),
            lot_reference=merged_lot_ref,
            current_holder_wallet_id=wallet_id,
            amount=total_amount,
            currency="INR",
            status="ACTIVE",
            origin_event_id=event_id,
        )
        self.db.add(merged_lot)
        self.db.flush()

        event = CBDCLedgerEvent(
            id=event_id,
            scenario_run_id=scenario_run_id,
            event_type="MERGE",
            from_wallet_id=wallet_id,
            to_wallet_id=wallet_id,
            amount=total_amount,
            currency="INR",
            event_timestamp=event_time,
            parent_lot_ids=parent_lot_ids,
            child_lot_ids=[merged_lot.id],
            metadata_json={"num_merged_parents": len(parent_lots)},
        )
        self.db.add(event)
        self.db.flush()
        return merged_lot, event

    def generate_scenario_2(
        self,
        seed: int = 42,
        base_amount: Optional[Decimal] = None,
        num_intermediaries: int = 3,
    ) -> ScenarioRun:
        """Scenario 2 (CBDC Tokens Only):
        1. Token Issuance from Central Bank Issuer
        2. Transfer to Initial Source Wallet
        3. Lot Splitting into structured fragments
        4. Multi-hop transmission through intermediary wallets
        5. Lot Merging into terminal coordinating wallet
        6. Independent Decoy wallets and token activity
        """
        rng = random.Random(seed)
        amount = base_amount or Decimal("1000000.0000")  # ₹10,00,000

        run = ScenarioRun(
            id=str(uuid.uuid4()),
            domain="cbdc",
            scenario_identifier="scenario_2",
            scenario_version="1.0.0",
            generator_version="1.0.0",
            seed=seed,
            configuration_json={
                "scenario_id": "scenario_2",
                "seed": seed,
                "amount": str(amount),
                "num_intermediaries": num_intermediaries,
            },
            status="RUNNING",
            started_at=datetime.now(timezone.utc),
        )
        self.db.add(run)
        self.db.flush()

        base_dt = datetime(2026, 10, 25, 9, 0, 0, tzinfo=timezone.utc)

        try:
            # 1. Issuer Wallet
            issuer = self._get_or_create_wallet("WAL-CBDC-CENTRAL-BANK", "Reserve Issuer", "ISSUER")

            # 2. Originating Source Wallet
            funder_addr = f"WAL-CBDC-FUNDER-{rng.randint(1000, 9999)}"
            funder = self._get_or_create_wallet(funder_addr, "Primary Source Wallet", "INDIVIDUAL", classification="cbdc_funder")
            self.db.add(
                CBDCGroundTruth(
                    id=str(uuid.uuid4()),
                    scenario_run_id=run.id,
                    wallet_id=funder.id,
                    role_label="cbdc_funder",
                    expected_relationship="source_originator",
                    rationale="Initial wallet funding the digital currency distribution chain",
                )
            )

            # Issue initial lot
            parent_lot, _ = self.issue_tokens(issuer, funder, amount, run.id, base_dt)

            # 3. Split parent lot into 3 structured child lots (e.g., 4L, 3L, 3L)
            dt_step1 = base_dt + timedelta(hours=1)
            split_amts = [
                Decimal("400000.0000"),
                Decimal("300000.0000"),
                Decimal("300000.0000"),
            ]
            child_lots, _ = self.split_token_lot(parent_lot, split_amts, run.id, dt_step1)

            # 4. Create Intermediary Wallets
            intermediary_wallets = []
            for i in range(len(child_lots)):
                w_addr = f"WAL-CBDC-INT{i+1}-{rng.randint(1000, 9999)}"
                w = self._get_or_create_wallet(w_addr, f"Intermediary Wallet {i+1}", "INTERMEDIARY", classification="cbdc_mixer_intermediary")
                intermediary_wallets.append(w)
                self.db.add(
                    CBDCGroundTruth(
                        id=str(uuid.uuid4()),
                        scenario_run_id=run.id,
                        wallet_id=w.id,
                        role_label="cbdc_mixer_intermediary",
                        expected_relationship="layering_hop",
                        rationale=f"Intermediary token lot holder {i+1}",
                    )
                )

            # 5. Transfer each child lot to an intermediary
            dt_step2 = base_dt + timedelta(hours=3)
            for idx, lot in enumerate(child_lots):
                target_w = intermediary_wallets[idx]
                tx_time = dt_step2 + timedelta(minutes=idx * 15)
                self.transfer_token_lot(lot, target_w, run.id, tx_time)

            # 6. Terminal Coordinating Wallet
            kingpin_addr = f"WAL-CBDC-COORDINATOR-{rng.randint(1000, 9999)}"
            coordinator = self._get_or_create_wallet(kingpin_addr, "Terminal Coordinating Wallet", "INDIVIDUAL", classification="cbdc_coordinating_wallet")
            self.db.add(
                CBDCGroundTruth(
                    id=str(uuid.uuid4()),
                    scenario_run_id=run.id,
                    wallet_id=coordinator.id,
                    role_label="cbdc_coordinating_wallet",
                    expected_relationship="destination_aggregator",
                    rationale="Terminal wallet re-aggregating and merging split token lots",
                )
            )

            # 7. Intermediaries transfer lots to Coordinator
            dt_step3 = base_dt + timedelta(hours=6)
            for idx, lot in enumerate(child_lots):
                tx_time = dt_step3 + timedelta(minutes=idx * 20)
                self.transfer_token_lot(lot, coordinator, run.id, tx_time)

            # 8. Coordinator merges the child lots back into one consolidated lot
            dt_step4 = base_dt + timedelta(hours=8)
            merged_lot, _ = self.merge_token_lots(child_lots, run.id, dt_step4)

            # 9. Decoy Wallets & Retail Activity
            decoy_merchant = self._get_or_create_wallet(
                f"WAL-DEC-STORE-{rng.randint(1000, 9999)}", "CBDC Grocery Decoy", "MERCHANT", classification="decoy_merchant"
            )
            # Fund a shopper
            decoy_shopper = self._get_or_create_wallet(
                f"WAL-DEC-SHOPPER-{rng.randint(1000, 9999)}", "CBDC Shopper Decoy", "INDIVIDUAL", classification="decoy_consumer"
            )
            shopper_lot, _ = self.issue_tokens(issuer, decoy_shopper, Decimal("50000.0000"), run.id, base_dt + timedelta(hours=2))
            # Shopper pays merchant
            self.transfer_token_lot(shopper_lot, decoy_merchant, run.id, base_dt + timedelta(hours=5))

            run.status = "COMPLETED"
            run.completed_at = datetime.now(timezone.utc)
            self.db.commit()

            # Run CBDC Detection
            self._run_cbdc_detection(run.id)
            return run
        except Exception as e:
            self.db.rollback()
            run.status = "FAILED"
            run.completed_at = datetime.now(timezone.utc)
            self.db.commit()
            raise e

    def _run_cbdc_detection(self, scenario_run_id: str) -> None:
        """Evaluates CBDC ledger events for rapid split, multi-hop, and merge anomalies."""
        events = list(
            self.db.execute(
                select(CBDCLedgerEvent)
                .where(CBDCLedgerEvent.scenario_run_id == scenario_run_id)
                .order_by(CBDCLedgerEvent.event_timestamp.asc())
            ).scalars().all()
        )

        # Detect wallets involved in SPLIT or MERGE operations
        split_events = [e for e in events if e.event_type == "SPLIT"]
        merge_events = [e for e in events if e.event_type == "MERGE"]

        if split_events and merge_events:
            # High risk detection for token obfuscation / mixing pattern
            merge_evt = merge_events[0]
            alert = Alert(
                id=str(uuid.uuid4()),
                domain="cbdc",
                scenario_run_id=scenario_run_id,
                account_id=None,
                transaction_id=None,
                risk_score=Decimal("88.00"),
                risk_band="HIGH",
                signals=[
                    {
                        "signal": "token_lot_split_merge_cycle",
                        "score": 45.0,
                        "description": "Structured token lot split followed by rapid multi-wallet re-aggregation and merge.",
                        "evidence": [f"Parent lot split into {len(split_events[0].child_lot_ids or [])} children then merged."],
                    },
                    {
                        "signal": "rapid_peeling_hop",
                        "score": 43.0,
                        "description": "Multi-hop token lineage traversal with high velocity.",
                        "evidence": [f"Total transferred amount ₹{merge_evt.amount:,.2f}"],
                    },
                ],
                detector_version="cbdc_provenance_v1.0.0",
                review_status="PENDING",
            )
            self.db.add(alert)
            self.db.flush()

            # Create CBDC Case
            case_ref = f"CBDC-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
            case = Case(
                id=str(uuid.uuid4()),
                case_reference=case_ref,
                domain="cbdc",
                title=f"CBDC Token Mixing & Obfuscation Chain ({alert.risk_band} Risk)",
                summary="Digital token ledger detected coordinated split-transfer-merge cycle across synthetic wallets.",
                status="OPEN",
                priority="HIGH",
                risk_band="HIGH",
                aggregate_risk_score=Decimal("88.00"),
                scenario_run_id=scenario_run_id,
                is_manual_entry=False,
            )
            self.db.add(case)
            self.db.flush()

            self.db.add(CaseAlert(id=str(uuid.uuid4()), case_id=case.id, alert_id=alert.id))
            self.db.commit()

    def get_token_provenance(self, lot_id_or_ref: str) -> Dict[str, Any]:
        """Traces the complete parent-child lineage of a token lot."""
        lot = self.db.execute(
            select(CBDCTokenLot).where(
                (CBDCTokenLot.id == lot_id_or_ref) | (CBDCTokenLot.lot_reference == lot_id_or_ref)
            )
        ).scalar_one_or_none()

        if not lot:
            raise ValueError(f"Token lot '{lot_id_or_ref}' not found")

        holder = self.db.get(CBDCWallet, lot.current_holder_wallet_id)

        # Find events where this lot was produced (origin) or consumed
        all_events = list(
            self.db.execute(
                select(CBDCLedgerEvent).order_by(CBDCLedgerEvent.event_timestamp.asc())
            ).scalars().all()
        )

        parent_lots = []
        child_lots = []

        for e in all_events:
            p_ids = e.parent_lot_ids or []
            c_ids = e.child_lot_ids or []

            # If this lot is a child, parents are e.parent_lot_ids
            if lot.id in c_ids and e.event_type in ("SPLIT", "MERGE"):
                for pid in p_ids:
                    p = self.db.get(CBDCTokenLot, pid)
                    if p:
                        parent_lots.append({
                            "id": p.id,
                            "lotReference": p.lot_reference,
                            "amount": float(p.amount),
                            "status": p.status,
                            "eventType": e.event_type,
                        })

            # If this lot is a parent, children are e.child_lot_ids
            if lot.id in p_ids and e.event_type in ("SPLIT", "MERGE"):
                for cid in c_ids:
                    c = self.db.get(CBDCTokenLot, cid)
                    if c:
                        child_lots.append({
                            "id": c.id,
                            "lotReference": c.lot_reference,
                            "amount": float(c.amount),
                            "status": c.status,
                            "eventType": e.event_type,
                        })

        return {
            "targetLot": {
                "id": lot.id,
                "lotReference": lot.lot_reference,
                "amount": float(lot.amount),
                "status": lot.status,
                "currency": lot.currency,
                "currentHolder": {
                    "id": holder.id if holder else None,
                    "address": holder.wallet_address if holder else "UNKNOWN",
                    "displayName": holder.display_name if holder else "Unknown",
                    "type": holder.wallet_type if holder else "INDIVIDUAL",
                },
            },
            "parents": parent_lots,
            "children": child_lots,
        }

