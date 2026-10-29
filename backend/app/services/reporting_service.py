from datetime import datetime, timezone
import os
from decimal import Decimal
import uuid
from typing import Any, Dict, Optional
from jinja2 import Template
from sqlalchemy.orm import Session
from sqlalchemy import select

from app.db.models.case import Case, CaseAlert, CaseAccount, CaseTransaction, CaseNote
from app.db.models.account import Account
from app.db.models.transaction import Transaction
from app.services.investigation_service import InvestigationService


REPORT_HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Mule Matrix Investigation Report — {{ case.case_reference }}</title>
  <style>
    @page { size: A4; margin: 20mm; }
    body { font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif; color: #222; background: #fff; line-height: 1.5; font-size: 11pt; }
    .header { border-bottom: 3px solid #6C5636; padding-bottom: 12px; margin-bottom: 24px; display: flex; justify-content: space-between; align-items: flex-start; }
    .title { font-size: 20pt; font-weight: bold; color: #090907; margin: 0; text-transform: uppercase; letter-spacing: 1px; }
    .subtitle { font-size: 9pt; color: #6C5636; margin-top: 4px; font-weight: bold; }
    .meta-box { background: #f8f6f2; border: 1px solid #dcd4c6; padding: 12px 16px; border-radius: 4px; margin-bottom: 20px; }
    .meta-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 8px; font-size: 9pt; }
    .badge { display: inline-block; padding: 2px 8px; font-size: 8pt; font-weight: bold; text-transform: uppercase; border-radius: 3px; }
    .badge-high { background: #fee2e2; color: #991b1b; }
    .badge-medium { background: #fef3c7; color: #92400e; }
    .badge-low { background: #dcfce7; color: #166534; }
    h2 { font-size: 13pt; color: #6C5636; border-bottom: 1px solid #e8e2d7; padding-bottom: 4px; margin-top: 24px; text-transform: uppercase; }
    table { width: 100%; border-collapse: collapse; margin-top: 8px; font-size: 9pt; }
    th { background: #f4efe6; text-align: left; padding: 6px 8px; border: 1px solid #dcd4c6; font-weight: bold; color: #4B3A22; }
    td { padding: 6px 8px; border: 1px solid #e8e2d7; }
    .disclaimer { margin-top: 36px; padding: 12px; background: #fef2f2; border-left: 4px solid #ef4444; font-size: 8pt; color: #7f1d1d; }
    .graph-preview { border: 1px solid #dcd4c6; background: #090907; color: #F5F5F0; padding: 16px; border-radius: 4px; text-align: center; margin-top: 12px; }
  </style>
</head>
<body>

  <div class="header">
    <div>
      <h1 class="title">Mule Matrix</h1>
      <div class="subtitle">Financial Crime Intelligence & Suspicious Network Dossier</div>
    </div>
    <div style="text-align: right; font-size: 9pt; color: #666;">
      <div>Ref: <strong>{{ case.case_reference }}</strong></div>
      <div>Date: {{ generated_at }}</div>
    </div>
  </div>

  <div class="meta-box">
    <div class="meta-grid">
      <div><strong>Case Title:</strong> {{ case.title }}</div>
      <div><strong>Domain:</strong> {{ case.domain | upper }}</div>
      <div><strong>Status:</strong> {{ case.status }}</div>
      <div><strong>Priority:</strong> {{ case.priority }}</div>
      <div><strong>Risk Band:</strong> <span class="badge badge-{{ (case.risk_band or 'low') | lower }}">{{ case.risk_band or 'LOW' }}</span></div>
      <div><strong>Aggregate Score:</strong> {{ case.aggregate_risk_score or 'N/A' }} / 100</div>
    </div>
  </div>

  <h2>1. Executive Summary</h2>
  <p>{{ case.summary or 'Automated transaction monitoring alert generated based on multi-leg structuring and rapid pass-through anomaly heuristics.' }}</p>

  <h2>2. Observed Transaction Evidence</h2>
  <table>
    <thead>
      <tr>
        <th>Txn Ref</th>
        <th>Source Account</th>
        <th>Destination Account</th>
        <th>Amount</th>
        <th>Timestamp (UTC)</th>
        <th>Evidence Type</th>
      </tr>
    </thead>
    <tbody>
      {% for t in transactions %}
      <tr>
        <td><strong>{{ t.reference }}</strong></td>
        <td>{{ t.source }}</td>
        <td>{{ t.destination }}</td>
        <td>₹{{ "{:,.2f}".format(t.amount) }}</td>
        <td>{{ t.timestamp }}</td>
        <td>{{ t.evidence_type }}</td>
      </tr>
      {% else %}
      <tr><td colspan="6" style="text-align: center; color: #888;">No transactions linked directly to case dossier.</td></tr>
      {% endfor %}
    </tbody>
  </table>

  <h2>3. Potential Kingpin & Mule Rankings</h2>
  <table>
    <thead>
      <tr>
        <th>Rank</th>
        <th>Role Type</th>
        <th>Account Ref / Alias</th>
        <th>Score</th>
        <th>Rationale</th>
      </tr>
    </thead>
    <tbody>
      {% for k in rankings.kingpins[:3] %}
      <tr>
        <td>#{{ k.rank }}</td>
        <td><strong style="color: #b91c1c;">Potential Kingpin</strong></td>
        <td>{{ k.alias }} ({{ k.accountRef }})</td>
        <td>{{ k.kingpinScore }}</td>
        <td>{{ k.rationale }}</td>
      </tr>
      {% endfor %}
      {% for m in rankings.mules[:3] %}
      <tr>
        <td>#{{ m.rank }}</td>
        <td><strong style="color: #b45309;">Layering Mule</strong></td>
        <td>{{ m.alias }} ({{ m.accountRef }})</td>
        <td>{{ m.muleScore }}</td>
        <td>{{ m.rationale }}</td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <h2>4. FIFO Fund Attribution Trace</h2>
  <table>
    <thead>
      <tr>
        <th>Transaction</th>
        <th>Amount</th>
        <th>Attributed Inbound Parent</th>
        <th>Attributed Share</th>
      </tr>
    </thead>
    <tbody>
      {% for a in attributions[:6] %}
      <tr>
        <td>{{ a.transactionRef }}</td>
        <td>₹{{ "{:,.2f}".format(a.amount) }}</td>
        <td>
          {% for p in a.consumedAllocations %}
            {{ p.parentTxnRef }}<br>
          {% else %}
            <em>Primary Inbound Influx</em>
          {% endfor %}
        </td>
        <td>
          {% for p in a.consumedAllocations %}
            ₹{{ "{:,.2f}".format(p.attributedAmount) }}<br>
          {% else %}
            ₹{{ "{:,.2f}".format(a.amount) }}
          {% endfor %}
        </td>
      </tr>
      {% endfor %}
    </tbody>
  </table>

  <div class="disclaimer">
    <strong>SIMULATION RESEARCH NOTICE:</strong>
    This document was generated by the Mule Matrix academic financial intelligence prototype. All institutions, accounts, token lots, and transaction patterns are synthetic simulations. This report is not associated with live financial institutions, actual bank networks, or real Central Bank Digital Currency infrastructure.
  </div>

</body>
</html>
"""


class ReportingService:
    """Generates case investigation PDF reports with embedded graph and attribution data."""

    def __init__(self, db: Session):
        self.db = db
        self.investigation_service = InvestigationService(db)

    def generate_case_html(self, case_id: str) -> str:
        """Renders the investigation report HTML."""
        case = self.db.get(Case, case_id)
        if not case:
            raise ValueError(f"Case '{case_id}' not found")

        # Load linked transactions
        case_txns = list(
            self.db.execute(
                select(CaseTransaction).where(CaseTransaction.case_id == case_id)
            ).scalars().all()
        )

        formatted_txns = []
        for ct in case_txns:
            t = self.db.get(Transaction, ct.transaction_id)
            if t:
                src = self.db.get(Account, t.source_account_id)
                dst = self.db.get(Account, t.destination_account_id)
                formatted_txns.append({
                    "reference": t.native_transaction_reference or t.id[:8],
                    "source": src.bank_account_reference if src else "UNKNOWN",
                    "destination": dst.bank_account_reference if dst else "UNKNOWN",
                    "amount": float(t.amount),
                    "timestamp": t.event_timestamp.strftime("%Y-%m-%d %H:%M:%S"),
                    "evidence_type": ct.evidence_type,
                })

        # Load rankings and FIFO attribution if scenario run exists
        rankings = {"kingpins": [], "mules": []}
        attributions = []
        if case.scenario_run_id:
            rankings = self.investigation_service.compute_mule_and_kingpin_rankings(case.scenario_run_id)
            attributions = self.investigation_service.compute_fifo_fund_attribution(case.scenario_run_id)

        template = Template(REPORT_HTML_TEMPLATE)
        return template.render(
            case=case,
            transactions=formatted_txns,
            rankings=rankings,
            attributions=attributions,
            generated_at=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        )

    async def generate_case_pdf(self, case_id: str) -> bytes:
        """Prints the rendered HTML report to PDF using Playwright."""
        html_content = self.generate_case_html(case_id)

        try:
            from playwright.async_api import async_playwright
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                await page.set_content(html_content, wait_until="networkidle")
                pdf_bytes = await page.pdf(format="A4", print_background=True)
                await browser.close()
                return pdf_bytes
        except Exception as e:
            # If Playwright browser binary isn't pre-installed, return HTML as bytes
            return html_content.encode("utf-8")

