from fastapi import APIRouter, Depends, HTTPException, Response
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.db.models.case import Case
from app.services.reporting_service import ReportingService

router = APIRouter(prefix="/reports", tags=["Reports"])


@router.get("/cases/{case_id}/html", response_class=HTMLResponse)
def get_case_report_html(case_id: str, db: Session = Depends(get_db)):
    """Renders the printable HTML investigation report."""
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    svc = ReportingService(db)
    return svc.generate_case_html(case_id)


@router.get("/cases/{case_id}/pdf")
async def download_case_report_pdf(case_id: str, db: Session = Depends(get_db)):
    """Generates and downloads a case investigation PDF dossier."""
    case = db.get(Case, case_id)
    if not case:
        raise HTTPException(status_code=404, detail="Case not found")

    svc = ReportingService(db)
    pdf_bytes = await svc.generate_case_pdf(case_id)

    # If Playwright generated a PDF, content-type is application/pdf
    is_pdf = pdf_bytes[:4] == b"%PDF"
    content_type = "application/pdf" if is_pdf else "text/html; charset=utf-8"
    filename = f"MuleMatrix_Report_{case.case_reference}.{'pdf' if is_pdf else 'html'}"

    return Response(
        content=pdf_bytes,
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )

