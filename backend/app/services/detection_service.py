from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.alert import Alert
from app.db.models.case import Case, CaseAlert, CaseAccount, CaseTransaction, CaseNote
from app.db.models.risk_score import AccountRiskScore


class DetectionService:
    """Explainable risk-scoring and anomaly detection engine.

    Evaluates observable transaction topology and temporal patterns.
    STRICT PRIVACY: NEVER inspects or joins with ground_truth_labels.
    """

    DETECTOR_VERSION = "mule_matrix_v1.0.0"

    # Configurable prototype signal weights (Total = 100)
    DEFAULT_WEIGHTS = {
        "rapid_pass_through": Decimal("25.00"),
        "network_intermediary": Decimal("20.00"),
        "temporal_coordination": Decimal("20.00"),
        "repeated_counterparties": Decimal("15.00"),
        "behavioral_deviation": Decimal("10.00"),
        "fan_in_out": Decimal("10.00"),
    }

    def __init__(self, db: Session, weights: Optional[Dict[str, Decimal]] = None):
        self.db = db
        self.weights = weights or self.DEFAULT_WEIGHTS

    def analyze_scenario_run(
        self, scenario_run_id: str, domain: str = "current_money"
    ) -> List[Alert]:
        """Runs the detection engine over observable transactions of a scenario run."""
        # 1. Fetch all observable transactions for this run (Strictly NO ground truth)
        stmt = (
            select(Transaction)
            .where(Transaction.scenario_run_id == scenario_run_id)
            .order_by(Transaction.event_timestamp.asc())
        )
        transactions = list(self.db.execute(stmt).scalars().all())
        if not transactions:
            return []

        # 2. Build in-memory graph representation of observable transfers
        incoming_by_acc: Dict[str, List[Transaction]] = defaultdict(list)
        outgoing_by_acc: Dict[str, List[Transaction]] = defaultdict(list)
        all_account_ids: Set[str] = set()

        for t in transactions:
            incoming_by_acc[t.destination_account_id].append(t)
            outgoing_by_acc[t.source_account_id].append(t)
            all_account_ids.add(t.source_account_id)
            all_account_ids.add(t.destination_account_id)

        alerts_created: List[Alert] = []

        # 3. Score every observable account
        for acc_id in all_account_ids:
            score_data = self._calculate_account_risk(
                acc_id=acc_id,
                incoming=incoming_by_acc.get(acc_id, []),
                outgoing=outgoing_by_acc.get(acc_id, []),
                all_txns=transactions,
                incoming_by_acc=incoming_by_acc,
                outgoing_by_acc=outgoing_by_acc,
            )

            # Persist AccountRiskScore
            risk_entry = AccountRiskScore(
                id=str(uuid.uuid4()),
                domain=domain,
                scenario_run_id=scenario_run_id,
                account_id=acc_id,
                risk_score=score_data["total_score"],
                risk_band=score_data["risk_band"],
                signals=score_data["signals"],
                detector_version=self.DETECTOR_VERSION,
            )
            self.db.add(risk_entry)

            # 4. Generate Alert if High or Medium risk
            if score_data["risk_band"] in ("HIGH", "MEDIUM"):
                # Associated transaction is the most suspicious or primary transaction
                primary_txn = (
                    outgoing_by_acc.get(acc_id, [None])[0]
                    or incoming_by_acc.get(acc_id, [None])[0]
                )

                alert = Alert(
                    id=str(uuid.uuid4()),
                    domain=domain,
                    scenario_run_id=scenario_run_id,
                    account_id=acc_id,
                    transaction_id=primary_txn.id if primary_txn else None,
                    risk_score=score_data["total_score"],
                    risk_band=score_data["risk_band"],
                    signals=score_data["signals"],
                    detector_version=self.DETECTOR_VERSION,
                    review_status="PENDING",
                )
                self.db.add(alert)
                alerts_created.append(alert)

        self.db.flush()

        # 5. Apply Case Creation and Merging Policy
        self._apply_case_policy(alerts_created, scenario_run_id, domain)

        self.db.commit()
        return alerts_created

    def _calculate_account_risk(
        self,
        acc_id: str,
        incoming: List[Transaction],
        outgoing: List[Transaction],
        all_txns: List[Transaction],
        incoming_by_acc: Dict[str, List[Transaction]],
        outgoing_by_acc: Dict[str, List[Transaction]],
    ) -> Dict[str, Any]:
        """Calculates multi-signal explainable risk score for an account."""
        signals = []
        total_score = Decimal("0.00")

        total_in = sum((t.amount for t in incoming), Decimal("0"))
        total_out = sum((t.amount for t in outgoing), Decimal("0"))

        # Guilt-by-Association Check: Is this a pure originator/victim?
        # If account has ONLY outgoing transfers and zero incoming transfers,
        # it is an originator. Originators sending funds must not be falsely scored as mules!
        is_pure_originator = len(incoming) == 0 and len(outgoing) > 0

        # SIGNAL 1: Rapid Pass-Through (Max: 25)
        # Condition: Receives funds and subsequently transfers them out in narrow window (< 24 hrs)
        pass_through_score = Decimal("0.00")
        pass_through_evidence = []
        if not is_pure_originator and incoming and outgoing:
            for t_in in incoming:
                for t_out in outgoing:
                    if t_out.event_timestamp >= t_in.event_timestamp:
                        time_diff = (t_out.event_timestamp - t_in.event_timestamp).total_seconds()
                        if time_diff <= 86400:  # Within 24 hours
                            # Ratio of amounts
                            ratio = min(t_out.amount / t_in.amount, t_in.amount / t_out.amount)
                            if ratio >= Decimal("0.50"):
                                pass_through_score = self.weights["rapid_pass_through"]
                                pass_through_evidence.append(
                                    f"In {t_in.native_transaction_reference} ({t_in.amount}) -> Out {t_out.native_transaction_reference} ({t_out.amount}) in {round(time_diff / 3600, 1)}h"
                                )
                                break
                if pass_through_score > 0:
                    break

        if pass_through_score > 0:
            total_score += pass_through_score
            signals.append({
                "signal": "rapid_pass_through",
                "score": float(pass_through_score),
                "weight": float(self.weights["rapid_pass_through"]),
                "description": "Rapid outgoing dissipation of newly received incoming funds.",
                "evidence": pass_through_evidence,
            })

        # SIGNAL 2: Network Intermediary Role (Max: 20)
        # Condition: Has both upstream payers and downstream beneficiaries (bridges two network components)
        intermediary_score = Decimal("0.00")
        if not is_pure_originator and len(incoming) >= 1 and len(outgoing) >= 1:
            intermediary_score = self.weights["network_intermediary"]
            total_score += intermediary_score
            signals.append({
                "signal": "network_intermediary",
                "score": float(intermediary_score),
                "weight": float(self.weights["network_intermediary"]),
                "description": "Account acts as a transmission intermediary between upstream and downstream entities.",
                "evidence": [f"{len(incoming)} incoming counterparties, {len(outgoing)} outgoing counterparties"],
            })

        # SIGNAL 3: Temporal Coordination (Max: 20)
        # Condition: Multi-leg transfers synchronized within 1-3 days or pre-positioning / delayed replenishment
        coordination_score = Decimal("0.00")
        coord_evidence = []

        # Check for pre-positioned / delayed replenishment pattern (Scenario 3 characteristic)
        # Case A: Outgoing historical transfers followed by incoming replenishment
        for t_out in outgoing:
            for t_in in incoming:
                if t_in.event_timestamp > t_out.event_timestamp:
                    days_gap = (t_in.event_timestamp - t_out.event_timestamp).total_seconds() / 86400
                    if 1 <= days_gap <= 4:
                        coordination_score = self.weights["temporal_coordination"]
                        coord_evidence.append(
                            f"Pre-positioned transfer {t_out.native_transaction_reference} replenished by {t_in.native_transaction_reference} after {round(days_gap, 1)} days"
                        )
                        break
            if coordination_score > 0:
                break

        # Case B: Terminal aggregator receiving multiple large pre-positioned inputs or structured bursts
        if coordination_score == 0 and len(incoming) >= 2 and not is_pure_originator:
            sorted_in = sorted(incoming, key=lambda x: x.event_timestamp)
            gap = (sorted_in[-1].event_timestamp - sorted_in[0].event_timestamp).total_seconds()
            if gap <= 172800:  # within 48h
                coordination_score = self.weights["temporal_coordination"]
                coord_evidence.append(f"Multiple incoming transfers clustered within {round(gap / 3600, 1)}h")

        if coordination_score > 0:
            total_score += coordination_score
            signals.append({
                "signal": "temporal_coordination",
                "score": float(coordination_score),
                "weight": float(self.weights["temporal_coordination"]),
                "description": "Coordinated temporal spacing characteristic of pre-positioning or delayed replenishment.",
                "evidence": coord_evidence,
            })

        # SIGNAL 4: Repeated Counterparties / Circular Links (Max: 15)
        repeated_score = Decimal("0.00")
        in_sources = {t.source_account_id for t in incoming}
        out_dests = {t.destination_account_id for t in outgoing}
        common = in_sources.intersection(out_dests)

        if common:
            repeated_score = self.weights["repeated_counterparties"]
            total_score += repeated_score
            signals.append({
                "signal": "repeated_counterparties",
                "score": float(repeated_score),
                "weight": float(self.weights["repeated_counterparties"]),
                "description": "Bidirectional or reciprocal transaction activity with identical counterparties.",
                "evidence": [f"Common reciprocal counterparties: {len(common)}"],
            })
        elif len(incoming) >= 3 or len(outgoing) >= 3:
            # High frequency repeating activity
            repeated_score = self.weights["repeated_counterparties"] * Decimal("0.70")
            total_score += repeated_score
            signals.append({
                "signal": "repeated_counterparties",
                "score": float(repeated_score),
                "weight": float(self.weights["repeated_counterparties"]),
                "description": "High-frequency repeated transactions within observation window.",
                "evidence": [f"{len(incoming)} in / {len(outgoing)} out transaction volume"],
            })

        # SIGNAL 5: Behavioral Deviation / High Velocity Spurt (Max: 10)
        # Large total throughput > 1,50,000 INR
        behavioral_score = Decimal("0.00")
        if (total_in + total_out) >= Decimal("150000.0000") and not is_pure_originator:
            behavioral_score = self.weights["behavioral_deviation"]
            total_score += behavioral_score
            signals.append({
                "signal": "behavioral_deviation",
                "score": float(behavioral_score),
                "weight": float(self.weights["behavioral_deviation"]),
                "description": "Substantial monetary volume executed through account in brief monitoring timeframe.",
                "evidence": [f"Total throughput ₹{(total_in + total_out):,.2f}"],
            })

        # SIGNAL 6: Fan-In / Fan-Out Structuring Behavior (Max: 10)
        fan_score = Decimal("0.00")
        if len(incoming) >= 3 and len(outgoing) <= 1:
            # Fan-in (Collector)
            fan_score = self.weights["fan_in_out"]
            total_score += fan_score
            signals.append({
                "signal": "fan_in_out",
                "score": float(fan_score),
                "weight": float(self.weights["fan_in_out"]),
                "description": "Funnel/Fan-in pattern: Multiple depositors converging on a single recipient account.",
                "evidence": [f"{len(incoming)} inbound source accounts converging"],
            })
        elif len(outgoing) >= 2 and len(incoming) >= 1 and not is_pure_originator:
            # Fan-out (Layerer/Distributor)
            fan_score = self.weights["fan_in_out"]
            total_score += fan_score
            signals.append({
                "signal": "fan_in_out",
                "score": float(fan_score),
                "weight": float(self.weights["fan_in_out"]),
                "description": "Fan-out structuring: Funds dispersed rapidly to multiple downstream nodes.",
                "evidence": [f"Dispersal to {len(outgoing)} recipient nodes"],
            })

        # Guilt-by-association protection rule:
        # If pure originator/victim, cap score to prevent false classification
        if is_pure_originator:
            total_score = min(total_score, Decimal("25.00"))

        # Bound score between 0.00 and 100.00
        total_score = min(max(total_score, Decimal("0.00")), Decimal("100.00"))

        # Determine risk band
        if total_score >= Decimal("70.00"):
            risk_band = "HIGH"
        elif total_score >= Decimal("40.00"):
            risk_band = "MEDIUM"
        else:
            risk_band = "LOW"

        return {
            "total_score": total_score.quantize(Decimal("0.01")),
            "risk_band": risk_band,
            "signals": signals,
        }

    def _apply_case_policy(
        self, alerts: List[Alert], scenario_run_id: str, domain: str
    ) -> None:
        """Applies case creation and 24h event-window merging policy."""
        # Policy:
        # - High-risk alert (>= 70): Qualifies for case
        # - Medium-risk alert (40-69): Qualifies if len(signals) >= 2
        # - Low-risk: Observation only
        qualifying_alerts = [
            a for a in alerts
            if a.risk_band == "HIGH" or (a.risk_band == "MEDIUM" and len(a.signals) >= 2)
        ]

        if not qualifying_alerts:
            return

        # Find existing OPEN cases for this scenario run
        existing_cases = list(
            self.db.execute(
                select(Case).where(
                    Case.scenario_run_id == scenario_run_id,
                    Case.domain == domain,
                    Case.status.in_(["OPEN", "UNDER_INVESTIGATION"]),
                )
            ).scalars().all()
        )

        for alert in qualifying_alerts:
            # Check if this alert can merge into an existing case
            # Merge condition:
            # 1. Same scenario run and domain
            # 2. Shared account OR event time within 24h merge window of case's alerts
            merged_case = None

            for c in existing_cases:
                # Check shared accounts
                linked_acc_ids = {ca.account_id for ca in c.accounts}
                if alert.account_id in linked_acc_ids:
                    merged_case = c
                    break

                # Check 24-hour window with case creation / event time
                time_diff = abs((alert.created_at - c.created_at).total_seconds())
                if time_diff <= 86400:  # 24 hours
                    merged_case = c
                    break

            if merged_case:
                # Associate alert with existing case
                self._attach_alert_to_case(merged_case, alert)
            else:
                # Create a new Case
                new_case = self._create_case_from_alert(alert, scenario_run_id, domain)
                existing_cases.append(new_case)

    def _create_case_from_alert(self, alert: Alert, run_id: str, domain: str) -> Case:
        """Instantiates a new investigation case from a qualifying alert."""
        ref_prefix = "CM" if domain == "current_money" else "CBDC"
        case_ref = f"{ref_prefix}-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

        priority = "CRITICAL" if alert.risk_score >= Decimal("85.00") else ("HIGH" if alert.risk_band == "HIGH" else "MEDIUM")

        case = Case(
            id=str(uuid.uuid4()),
            case_reference=case_ref,
            domain=domain,
            title=f"Suspicious Money Movement Pattern: {alert.risk_band} Risk ({alert.risk_score} Score)",
            summary=f"Automated risk detection identified {len(alert.signals)} anomaly signals matching money mule or layering typologies.",
            status="OPEN",
            priority=priority,
            risk_band=alert.risk_band,
            aggregate_risk_score=alert.risk_score,
            scenario_run_id=run_id,
            is_manual_entry=False,
        )
        self.db.add(case)
        self.db.flush()

        # Add initial audit note
        self.db.add(
            CaseNote(
                id=str(uuid.uuid4()),
                case_id=case.id,
                note_type="SYSTEM",
                content=f"Case automatically initialized by Detection Engine ({self.DETECTOR_VERSION}) from Alert {alert.id[:8]}.",
                new_status="OPEN",
            )
        )

        self._attach_alert_to_case(case, alert)
        return case

    def _attach_alert_to_case(self, case: Case, alert: Alert) -> None:
        """Links an alert, its account, and transactions to a case with audit logging."""
        # 1. Link Alert
        existing_ca = self.db.execute(
            select(CaseAlert).where(CaseAlert.case_id == case.id, CaseAlert.alert_id == alert.id)
        ).scalar_one_or_none()

        if not existing_ca:
            self.db.add(CaseAlert(id=str(uuid.uuid4()), case_id=case.id, alert_id=alert.id))

        # 2. Link Account
        if alert.account_id:
            existing_acc = self.db.execute(
                select(CaseAccount).where(CaseAccount.case_id == case.id, CaseAccount.account_id == alert.account_id)
            ).scalar_one_or_none()

            if not existing_acc:
                role = "kingpin_candidate" if alert.risk_score >= Decimal("80.00") else "suspect"
                self.db.add(CaseAccount(id=str(uuid.uuid4()), case_id=case.id, account_id=alert.account_id, role=role))

        # 3. Link Transaction
        if alert.transaction_id:
            existing_tx = self.db.execute(
                select(CaseTransaction).where(CaseTransaction.case_id == case.id, CaseTransaction.transaction_id == alert.transaction_id)
            ).scalar_one_or_none()

            if not existing_tx:
                self.db.add(CaseTransaction(id=str(uuid.uuid4()), case_id=case.id, transaction_id=alert.transaction_id, evidence_type="DIRECT"))

        # Update case aggregate score (maximum alert score)
        if case.aggregate_risk_score is None or alert.risk_score > case.aggregate_risk_score:
            case.aggregate_risk_score = alert.risk_score
            case.risk_band = alert.risk_band

