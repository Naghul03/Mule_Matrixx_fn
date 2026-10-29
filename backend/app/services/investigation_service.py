from collections import defaultdict, deque
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional, Set, Tuple
import networkx as nx
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.account import Account
from app.db.models.bank import Bank
from app.db.models.transaction import Transaction
from app.db.models.case import Case, CaseTransaction, CaseAccount
from app.db.models.risk_score import AccountRiskScore


class InvestigationService:
    """Network graph analysis, forward/backward traversal, FIFO attribution, and kingpin ranking."""

    def __init__(self, db: Session):
        self.db = db

    def build_investigation_graph(
        self,
        scenario_run_id: Optional[str] = None,
        case_id: Optional[str] = None,
        account_id: Optional[str] = None,
        max_depth: int = 3,
    ) -> Dict[str, Any]:
        """Constructs an evidence-driven graph representation for Cytoscape.js visualization."""
        txns: List[Transaction] = []

        if case_id:
            # Load transactions linked to case
            case_tx_ids = self.db.execute(
                select(CaseTransaction.transaction_id).where(CaseTransaction.case_id == case_id)
            ).scalars().all()

            if case_tx_ids:
                txns = list(
                    self.db.execute(
                        select(Transaction).where(Transaction.id.in_(case_tx_ids))
                    ).scalars().all()
                )

            # If case has a scenario run, also load the full scenario graph context
            case = self.db.get(Case, case_id)
            if case and case.scenario_run_id:
                scenario_txns = list(
                    self.db.execute(
                        select(Transaction)
                        .where(Transaction.scenario_run_id == case.scenario_run_id)
                        .order_by(Transaction.event_timestamp.asc())
                    ).scalars().all()
                )
                # Combine without duplicates
                seen_ids = {t.id for t in txns}
                for st in scenario_txns:
                    if st.id not in seen_ids:
                        txns.append(st)
        elif scenario_run_id:
            txns = list(
                self.db.execute(
                    select(Transaction)
                    .where(Transaction.scenario_run_id == scenario_run_id)
                    .order_by(Transaction.event_timestamp.asc())
                ).scalars().all()
            )
        elif account_id:
            # Traversal starting from account
            txns = self._traverse_from_account(account_id, max_depth)

        # Assemble graph nodes and edges
        return self._format_cytoscape_elements(txns)

    def _traverse_from_account(self, start_acc_id: str, max_depth: int) -> List[Transaction]:
        """Performs bounded BFS forward and backward from starting account."""
        collected_tx_ids: Set[str] = set()
        visited_nodes: Set[str] = {start_acc_id}
        queue: deque[Tuple[str, int]] = deque([(start_acc_id, 0)])

        while queue:
            curr_acc, depth = queue.popleft()
            if depth >= max_depth:
                continue

            # Forward transfers (outbound)
            out_txns = list(
                self.db.execute(
                    select(Transaction).where(Transaction.source_account_id == curr_acc)
                ).scalars().all()
            )
            for t in out_txns:
                collected_tx_ids.add(t.id)
                if t.destination_account_id not in visited_nodes:
                    visited_nodes.add(t.destination_account_id)
                    queue.append((t.destination_account_id, depth + 1))

            # Backward transfers (inbound)
            in_txns = list(
                self.db.execute(
                    select(Transaction).where(Transaction.destination_account_id == curr_acc)
                ).scalars().all()
            )
            for t in in_txns:
                collected_tx_ids.add(t.id)
                if t.source_account_id not in visited_nodes:
                    visited_nodes.add(t.source_account_id)
                    queue.append((t.source_account_id, depth + 1))

        if not collected_tx_ids:
            return []

        return list(
            self.db.execute(
                select(Transaction).where(Transaction.id.in_(collected_tx_ids))
            ).scalars().all()
        )

    def _format_cytoscape_elements(self, txns: List[Transaction]) -> Dict[str, Any]:
        """Formats transactions into Cytoscape nodes and edges."""
        if not txns:
            return {"nodes": [], "edges": []}

        # Gather accounts
        acc_ids = set()
        for t in txns:
            acc_ids.add(t.source_account_id)
            acc_ids.add(t.destination_account_id)

        accounts = list(
            self.db.execute(select(Account).where(Account.id.in_(acc_ids))).scalars().all()
        )
        acc_map = {a.id: a for a in accounts}

        # Gather banks
        bank_ids = {a.bank_id for a in accounts}
        banks = list(
            self.db.execute(select(Bank).where(Bank.id.in_(bank_ids))).scalars().all()
        )
        bank_map = {b.id: b for b in banks}

        # Fetch risk scores if scenario run id is available
        scenario_run_ids = {t.scenario_run_id for t in txns if t.scenario_run_id}
        risk_map = {}
        if scenario_run_ids:
            scores = list(
                self.db.execute(
                    select(AccountRiskScore).where(
                        AccountRiskScore.account_id.in_(acc_ids),
                        AccountRiskScore.scenario_run_id.in_(scenario_run_ids),
                    )
                ).scalars().all()
            )
            for s in scores:
                risk_map[s.account_id] = {
                    "score": float(s.risk_score),
                    "band": s.risk_band,
                    "signals": s.signals,
                }

        # Classify edges: Direct vs Historical
        # Check if transactions have a significant time gap (Scenario 3 characteristic)
        sorted_txns = sorted(txns, key=lambda x: x.event_timestamp)
        first_time = sorted_txns[0].event_timestamp if sorted_txns else datetime.now(timezone.utc)

        nodes = []
        for acc in accounts:
            bank = bank_map.get(acc.bank_id)
            r_info = risk_map.get(acc.id, {"score": 0.0, "band": "LOW", "signals": []})

            # Calculate total in and out
            in_amt = sum((t.amount for t in txns if t.destination_account_id == acc.id), Decimal("0"))
            out_amt = sum((t.amount for t in txns if t.source_account_id == acc.id), Decimal("0"))

            nodes.append({
                "data": {
                    "id": acc.id,
                    "label": acc.display_alias or acc.bank_account_reference,
                    "accountRef": acc.bank_account_reference,
                    "bankCode": bank.bank_code if bank else "UNKNOWN",
                    "bankName": bank.display_name if bank else "Unknown Bank",
                    "riskScore": r_info["score"],
                    "riskBand": r_info["band"],
                    "totalIn": float(in_amt),
                    "totalOut": float(out_amt),
                }
            })

        edges = []
        for idx, t in enumerate(txns):
            # Evidence classification:
            # In Scenario 3, pre-positioned transfers occurred days before victim transfer
            # If transfer occurred > 24h prior to the main victim flow, classify as HISTORICAL
            time_offset_hours = (t.event_timestamp - first_time).total_seconds() / 3600
            evidence_type = "DIRECT"
            if time_offset_hours < 24 and any(
                (other.event_timestamp - t.event_timestamp).total_seconds() > 86400 for other in txns
            ):
                # Historical relationship transfer
                evidence_type = "HISTORICAL"

            edges.append({
                "data": {
                    "id": t.id,
                    "source": t.source_account_id,
                    "target": t.destination_account_id,
                    "amount": float(t.amount),
                    "currency": t.currency,
                    "timestamp": t.event_timestamp.isoformat(),
                    "reference": t.native_transaction_reference or t.id[:8],
                    "evidenceType": evidence_type,
                    "normalizedType": t.normalized_type,
                    "status": t.status,
                }
            })

        return {"nodes": nodes, "edges": edges}

    def compute_mule_and_kingpin_rankings(
        self, scenario_run_id: str
    ) -> Dict[str, Any]:
        """Calculates algorithmic ranking of potential mules and coordinating kingpins.

        Uses:
        - NetworkX Directed Graph centrality metrics (in-degree, out-degree, betweenness)
        - Net fund retention vs pass-through ratio
        - Temporal positioning
        """
        txns = list(
            self.db.execute(
                select(Transaction)
                .where(Transaction.scenario_run_id == scenario_run_id)
                .order_by(Transaction.event_timestamp.asc())
            ).scalars().all()
        )
        if not txns:
            return {"mules": [], "kingpins": []}

        # Build NetworkX DiGraph
        G = nx.DiGraph()
        acc_ids = set()
        for t in txns:
            acc_ids.add(t.source_account_id)
            acc_ids.add(t.destination_account_id)
            G.add_edge(t.source_account_id, t.destination_account_id, weight=float(t.amount))

        accounts = {
            a.id: a
            for a in self.db.execute(select(Account).where(Account.id.in_(acc_ids))).scalars().all()
        }

        # Fetch risk scores
        risk_entries = {
            r.account_id: r
            for r in self.db.execute(
                select(AccountRiskScore).where(
                    AccountRiskScore.account_id.in_(acc_ids),
                    AccountRiskScore.scenario_run_id == scenario_run_id,
                )
            ).scalars().all()
        }

        # Centrality metrics
        betweenness = nx.betweenness_centrality(G) if len(G) > 2 else {n: 0.0 for n in G}

        mule_candidates = []
        kingpin_candidates = []

        for acc_id in acc_ids:
            acc = accounts.get(acc_id)
            if not acc:
                continue

            in_txns = [t for t in txns if t.destination_account_id == acc_id]
            out_txns = [t for t in txns if t.source_account_id == acc_id]

            total_in = sum((t.amount for t in in_txns), Decimal("0"))
            total_out = sum((t.amount for t in out_txns), Decimal("0"))

            # Exclude pure victims: only out, 0 in
            if len(in_txns) == 0 and len(out_txns) > 0:
                continue

            r_entry = risk_entries.get(acc_id)
            score = float(r_entry.risk_score) if r_entry else 0.0

            # 1. Kingpin Criteria:
            # - High net fund accumulation / terminal recipient (In >> Out)
            # - Multiple inbound connections from intermediaries
            # - Receives from nodes that themselves have outgoing activity
            is_terminal_accumulator = total_in > 0 and (total_out == 0 or total_in >= total_out * Decimal("2.0"))

            if is_terminal_accumulator:
                # Kingpin scoring factor
                kingpin_score = score * 0.5 + float(betweenness.get(acc_id, 0.0)) * 50.0 + min(float(total_in) / 5000.0, 50.0)
                kingpin_candidates.append({
                    "accountId": acc.id,
                    "accountRef": acc.bank_account_reference,
                    "alias": acc.display_alias or acc.bank_account_reference,
                    "riskScore": score,
                    "kingpinScore": round(kingpin_score, 2),
                    "totalReceived": float(total_in),
                    "totalDisbursed": float(total_out),
                    "inboundTransfers": len(in_txns),
                    "outboundTransfers": len(out_txns),
                    "betweennessCentrality": round(betweenness.get(acc_id, 0.0), 4),
                    "rationale": "High net fund retention with convergence of multiple inbound intermediary transfers.",
                })

            # 2. Mule Intermediary Criteria:
            # - High pass-through ratio (In ~ Out)
            # - High betweenness
            if total_in > 0 and total_out > 0:
                pass_through_ratio = min(total_in, total_out) / max(total_in, total_out)
                mule_score = score * 0.6 + float(pass_through_ratio) * 30.0 + float(betweenness.get(acc_id, 0.0)) * 20.0
                mule_candidates.append({
                    "accountId": acc.id,
                    "accountRef": acc.bank_account_reference,
                    "alias": acc.display_alias or acc.bank_account_reference,
                    "riskScore": score,
                    "muleScore": round(mule_score, 2),
                    "passThroughRatio": round(float(pass_through_ratio), 3),
                    "totalReceived": float(total_in),
                    "totalDisbursed": float(total_out),
                    "rationale": f"Rapid transmission node forwarding {round(float(pass_through_ratio)*100, 1)}% of inbound volume.",
                })

        # Sort rankings descending
        kingpin_candidates.sort(key=lambda x: x["kingpinScore"], reverse=True)
        mule_candidates.sort(key=lambda x: x["muleScore"], reverse=True)

        return {
            "kingpins": [
                {**k, "rank": idx + 1} for idx, k in enumerate(kingpin_candidates)
            ],
            "mules": [
                {**m, "rank": idx + 1} for idx, m in enumerate(mule_candidates)
            ],
        }

    def compute_fifo_fund_attribution(
        self, scenario_run_id: str
    ) -> List[Dict[str, Any]]:
        """FIFO Fund Attribution model.

        Incoming funds are treated as discrete allocations.
        Subsequent outgoing transfers consume older available allocations first.
        Handles partial consumption and mixed funds using exact Decimal arithmetic.
        """
        txns = list(
            self.db.execute(
                select(Transaction)
                .where(Transaction.scenario_run_id == scenario_run_id)
                .order_by(Transaction.event_timestamp.asc())
            ).scalars().all()
        )
        if not txns:
            return []

        # Account balance lots: account_id -> deque of {'txn_id', 'amount', 'timestamp'}
        account_lots: Dict[str, deque[Dict[str, Any]]] = defaultdict(deque)
        attributions: List[Dict[str, Any]] = []

        for txn in txns:
            # 1. Check if source account has existing unspent incoming lots to consume
            src_lots = account_lots[txn.source_account_id]
            amount_to_cover = txn.amount
            consumed_sources = []

            while src_lots and amount_to_cover > Decimal("0.0000"):
                oldest_lot = src_lots[0]
                available = oldest_lot["remaining_amount"]

                if available <= amount_to_cover:
                    # Fully consume this lot
                    consumed_sources.append({
                        "parentTxnId": oldest_lot["txn_id"],
                        "parentTxnRef": oldest_lot["txn_ref"],
                        "attributedAmount": float(available),
                    })
                    amount_to_cover -= available
                    src_lots.popleft()
                else:
                    # Partially consume this lot
                    consumed_sources.append({
                        "parentTxnId": oldest_lot["txn_id"],
                        "parentTxnRef": oldest_lot["txn_ref"],
                        "attributedAmount": float(amount_to_cover),
                    })
                    oldest_lot["remaining_amount"] -= amount_to_cover
                    amount_to_cover = Decimal("0.0000")

            # 2. Credit the destination account with a new incoming lot
            account_lots[txn.destination_account_id].append({
                "txn_id": txn.id,
                "txn_ref": txn.native_transaction_reference or txn.id[:8],
                "remaining_amount": txn.amount,
                "timestamp": txn.event_timestamp,
            })

            attributions.append({
                "transactionId": txn.id,
                "transactionRef": txn.native_transaction_reference or txn.id[:8],
                "amount": float(txn.amount),
                "timestamp": txn.event_timestamp.isoformat(),
                "consumedAllocations": consumed_sources,
                "unattributedAmount": float(amount_to_cover),
                "isDirectAttribution": len(consumed_sources) > 0,
            })

        return attributions

