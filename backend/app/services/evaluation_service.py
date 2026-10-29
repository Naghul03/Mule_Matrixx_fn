from collections import defaultdict
from decimal import Decimal
import uuid
from typing import Any, Dict, List, Optional, Set, Tuple
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.db.models.ground_truth import GroundTruthLabel
from app.db.models.evaluation import EvaluationRun
from app.db.models.risk_score import AccountRiskScore
from app.services.detection_service import DetectionService


class EvaluationService:
    """Benchmark evaluation comparing Mule Matrix detection against a simple single-transaction baseline.

    Strict ground truth isolation: Ground truth is ONLY accessed after both detectors have predicted.
    """

    BASELINE_VERSION = "single_txn_threshold_v1"

    # Default baseline threshold: Flags account if it has any single transfer >= 1,50,000 INR
    BASELINE_AMOUNT_THRESHOLD = Decimal("150000.0000")

    def __init__(self, db: Session):
        self.db = db

    def evaluate_scenario_run(
        self,
        scenario_run_id: str,
        seed_type: str = "HOLDOUT",
        domain: str = "current_money",
    ) -> EvaluationRun:
        """Executes full evaluation sequence:

        1. Run Baseline predictions
        2. Read Mule Matrix predictions (from DetectionService)
        3. Load isolated Ground Truth labels
        4. Calculate Precision, Recall, F1, and Confusion Matrices
        5. Persist and return EvaluationRun
        """
        # Step 1: Run Baseline Detector
        baseline_preds = self._run_baseline_detector(scenario_run_id)

        # Step 2: Run / Fetch Mule Matrix Detector predictions
        mule_matrix_preds = self._fetch_or_compute_mule_matrix_preds(scenario_run_id, domain)

        # Step 3: Access Hidden Ground Truth (ONLY at evaluation stage!)
        ground_truth_positives = self._fetch_ground_truth_positives(scenario_run_id)

        # Universe of all evaluated accounts in this scenario run
        all_accounts = set(baseline_preds.keys()).union(set(mule_matrix_preds.keys())).union(ground_truth_positives)

        # Step 4: Calculate Metrics
        mm_metrics, mm_cm = self._calculate_metrics(all_accounts, mule_matrix_preds, ground_truth_positives)
        base_metrics, base_cm = self._calculate_metrics(all_accounts, baseline_preds, ground_truth_positives)

        # Step 5: Persist Evaluation Run
        eval_run = EvaluationRun(
            id=str(uuid.uuid4()),
            domain=domain,
            scenario_run_id=scenario_run_id,
            detector_version=DetectionService.DETECTOR_VERSION,
            baseline_version=self.BASELINE_VERSION,
            seed_type=seed_type,
            metrics=mm_metrics,
            baseline_metrics=base_metrics,
            confusion_matrix=mm_cm,
            baseline_confusion_matrix=base_cm,
        )
        self.db.add(eval_run)
        self.db.commit()
        self.db.refresh(eval_run)
        return eval_run

    def _run_baseline_detector(self, scenario_run_id: str) -> Dict[str, bool]:
        """Simple baseline: Flags accounts that participated in any single transfer >= threshold."""
        txns = list(
            self.db.execute(
                select(Transaction).where(Transaction.scenario_run_id == scenario_run_id)
            ).scalars().all()
        )

        preds: Dict[str, bool] = {}
        for t in txns:
            # Initialize accounts as False if not seen
            if t.source_account_id not in preds:
                preds[t.source_account_id] = False
            if t.destination_account_id not in preds:
                preds[t.destination_account_id] = False

            if t.amount >= self.BASELINE_AMOUNT_THRESHOLD:
                # Exclude obvious originators if threshold only flags receivers,
                # but standard naive threshold flags both parties
                preds[t.source_account_id] = True
                preds[t.destination_account_id] = True

        return preds

    def _fetch_or_compute_mule_matrix_preds(
        self, scenario_run_id: str, domain: str
    ) -> Dict[str, bool]:
        """Retrieves Mule Matrix risk classifications. High and Medium risk accounts flagged as True."""
        scores = list(
            self.db.execute(
                select(AccountRiskScore).where(AccountRiskScore.scenario_run_id == scenario_run_id)
            ).scalars().all()
        )

        if not scores:
            # Run detection if not yet scored
            detector = DetectionService(self.db)
            detector.analyze_scenario_run(scenario_run_id, domain)
            scores = list(
                self.db.execute(
                    select(AccountRiskScore).where(AccountRiskScore.scenario_run_id == scenario_run_id)
                ).scalars().all()
            )

        # High (>= 70) or Medium (>= 40) is predicted positive
        preds: Dict[str, bool] = {}
        for s in scores:
            preds[s.account_id] = s.risk_band in ("HIGH", "MEDIUM")

        return preds

    def _fetch_ground_truth_positives(self, scenario_run_id: str) -> Set[str]:
        """Queries the isolated ground_truth_labels table.

        Positive ground truth roles: mule_layering, kingpin_coordinator, smurf, mule_collector.
        Negative roles: victim, decoy_merchant, decoy_payroll, decoy_consumer, decoy_employee.
        """
        gt_labels = list(
            self.db.execute(
                select(GroundTruthLabel).where(
                    GroundTruthLabel.scenario_run_id == scenario_run_id,
                    GroundTruthLabel.account_id.isnot(None),
                )
            ).scalars().all()
        )

        # Legitimate or non-malicious roles
        benign_roles = {"victim", "decoy_merchant", "decoy_payroll", "decoy_consumer", "decoy_employee", "witness"}

        positives = set()
        for label in gt_labels:
            if label.role_label not in benign_roles:
                positives.add(label.account_id)

        return positives

    def _calculate_metrics(
        self,
        all_accounts: Set[str],
        predictions: Dict[str, bool],
        ground_truth_positives: Set[str],
    ) -> Tuple[Dict[str, Any], Dict[str, int]]:
        """Calculates TP, FP, TN, FN, Precision, Recall, and F1."""
        tp = 0
        fp = 0
        tn = 0
        fn = 0

        for acc in all_accounts:
            pred = predictions.get(acc, False)
            actual = acc in ground_truth_positives

            if pred and actual:
                tp += 1
            elif pred and not actual:
                fp += 1
            elif not pred and not actual:
                tn += 1
            else:
                fn += 1

        precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        metrics = {
            "total_evaluated": len(all_accounts),
            "true_positives": tp,
            "false_positives": fp,
            "true_negatives": tn,
            "false_negatives": fn,
            "precision": round(precision, 4),
            "recall": round(recall, 4),
            "f1_score": round(f1, 4),
        }

        confusion_matrix = {
            "TP": tp,
            "FP": fp,
            "TN": tn,
            "FN": fn,
        }

        return metrics, confusion_matrix

