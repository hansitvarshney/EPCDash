import io
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Project, ProjectMilestone, MilestoneStatus, PaymentMilestone, PaymentMilestoneStatus
from backend.analytics import AnalyticsEngine
from backend.excel_service.attendance_export import build_attendance_workbook
from backend.expense_service import upsert_daily_expense
from backend.milestone_service import sync_payment_milestone_eligibility, notify_payment_milestone_eligible

router = APIRouter(prefix="/api/v1/sites", tags=["sites"])


class DailyExpenseInput(BaseModel):
    report_date: Optional[str] = None
    labor_wages_paid: Optional[float] = None
    misc_expenses_paid: Optional[float] = None
    misc_expenses_notes: Optional[str] = None


class MilestoneStatusInput(BaseModel):
    status: str  # "PENDING" | "COMPLETED"


class PaymentMilestoneStatusInput(BaseModel):
    status: str  # "INVOICED" | "PAID"


_PAYMENT_STATUS_FORWARD_ORDER = [
    PaymentMilestoneStatus.LOCKED,
    PaymentMilestoneStatus.ELIGIBLE,
    PaymentMilestoneStatus.INVOICED,
    PaymentMilestoneStatus.PAID,
]


@router.get("")
def list_active_sites(db: Session = Depends(get_db)):
    """Landing page gallery: Active Site cards with health indicators."""
    sites = db.query(Project).order_by(Project.id.asc()).all()
    return [AnalyticsEngine.get_site_card_summary(db, site) for site in sites]


@router.get("/{site_id}")
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return {
        "id": site.id,
        "name": site.name,
        "location": site.location,
        "client_name": site.client_name,
        "contract_value": site.contract_value,
        "start_date": site.start_date,
        "target_end_date": site.target_end_date,
        "health_status": AnalyticsEngine.get_site_health(db, site.id),
    }


@router.get("/{site_id}/overview")
def get_site_overview(site_id: int, db: Session = Depends(get_db)):
    """Powers the Site Detail page: KPI summary + Timeline & Velocity tracker data."""
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    return {
        "site": {
            "id": site.id,
            "name": site.name,
            "location": site.location,
            "client_name": site.client_name,
            "health_status": AnalyticsEngine.get_site_health(db, site.id),
            "start_date": site.start_date,
            "target_end_date": site.target_end_date,
            "contract_value": site.contract_value,
        },
        "summary": AnalyticsEngine.get_project_summary(db, site_id),
        "velocity": AnalyticsEngine.get_progress_velocity(db, site_id),
        "open_exceptions": AnalyticsEngine.get_open_exception_counts(db, site_id),
        "contract_timeline": AnalyticsEngine.get_contract_timeline(db, site),
        "operational_metrics": AnalyticsEngine.get_operational_metrics(db, site_id),
    }


@router.get("/{site_id}/attendance")
def get_site_attendance(site_id: int, db: Session = Depends(get_db)):
    """Powers the Site Attendance Sheet: today's labor breakdown + all-time daily log."""
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return AnalyticsEngine.get_attendance_sheet(db, site_id)


@router.get("/{site_id}/insights")
def get_site_insights(site_id: int, db: Session = Depends(get_db)):
    """
    Bundles the 5 Operational Cockpit micro-insight modules in one call
    (kept separate from `/overview`, mirroring the `/attendance` precedent,
    so each concern stays independently cacheable/fetchable).
    """
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    return {
        "milestone_tracker": AnalyticsEngine.get_milestone_tracker(db, site_id),
        "material_velocity": AnalyticsEngine.get_material_velocity(db, site_id),
        "latest_billing_activity": AnalyticsEngine.get_latest_billing_activity(db, site_id),
        "financial_ledger": AnalyticsEngine.get_financial_ledger(db, site_id),
        "drawing_status_ledger": AnalyticsEngine.get_drawing_status_ledger(db, site_id),
    }


@router.post("/{site_id}/expenses")
def log_daily_expense(site_id: int, payload: DailyExpenseInput, db: Session = Depends(get_db)):
    """
    "Principal Override" endpoint: locks in the true daily labor wages /
    misc site overheads for a given date (defaults to today), since these
    figures are managed entirely by the principal and can't be derived
    from vendor POs or ingested DPRs. Upserts via `expense_service` so
    this shares identical patch semantics with the WhatsApp short-circuit.
    """
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    row = upsert_daily_expense(
        db,
        site_id,
        report_date=payload.report_date,
        labor_wages_paid=payload.labor_wages_paid,
        misc_expenses_paid=payload.misc_expenses_paid,
        misc_expenses_notes=payload.misc_expenses_notes,
        source="MANUAL",
    )
    return {
        "report_date": row.report_date,
        "labor_wages_paid": row.labor_wages_paid,
        "misc_expenses_paid": row.misc_expenses_paid,
        "misc_expenses_notes": row.misc_expenses_notes,
        "source": row.source,
    }


@router.patch("/{site_id}/milestones/{milestone_id}")
def set_milestone_status(site_id: int, milestone_id: int, payload: MilestoneStatusInput, db: Session = Depends(get_db)):
    """
    Toggles a physical schedule milestone's status. This is both the
    day-to-day "mark complete" path (so the principal isn't forced to
    re-upload the whole schedule workbook for every stage) and the
    deliberate-reversal path for undoing a mistake. Reactively re-syncs
    any linked PaymentMilestone eligibility and fires a WhatsApp alert for
    anything that just became ELIGIBLE.
    """
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    milestone = (
        db.query(ProjectMilestone)
        .filter(ProjectMilestone.id == milestone_id, ProjectMilestone.project_id == site_id)
        .first()
    )
    if not milestone:
        raise HTTPException(status_code=404, detail="Milestone not found")

    try:
        new_status = MilestoneStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="status must be 'PENDING' or 'COMPLETED'")

    milestone.status = new_status
    db.commit()

    newly_eligible = sync_payment_milestone_eligibility(db, site_id)
    for bill in newly_eligible:
        notify_payment_milestone_eligible(db, site_id, bill)

    return {"id": milestone.id, "milestone_name": milestone.milestone_name, "status": milestone.status.value}


@router.patch("/{site_id}/payment-milestones/{payment_milestone_id}")
def set_payment_milestone_status(
    site_id: int, payment_milestone_id: int, payload: PaymentMilestoneStatusInput, db: Session = Depends(get_db)
):
    """
    Principal's manual "Mark Invoiced" / "Mark Paid" action -- the real-world
    financial event happens outside this app (the bill is physically issued
    to / paid by the client); this just records it. Forward-only: a bill
    can't be invoiced before it's ELIGIBLE, and statuses can't be skipped
    or moved backward through this endpoint.
    """
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    bill = (
        db.query(PaymentMilestone)
        .filter(PaymentMilestone.id == payment_milestone_id, PaymentMilestone.project_id == site_id)
        .first()
    )
    if not bill:
        raise HTTPException(status_code=404, detail="Payment milestone not found")

    try:
        new_status = PaymentMilestoneStatus(payload.status)
    except ValueError:
        raise HTTPException(status_code=400, detail="status must be 'INVOICED' or 'PAID'")

    if new_status not in (PaymentMilestoneStatus.INVOICED, PaymentMilestoneStatus.PAID):
        raise HTTPException(status_code=400, detail="Only 'INVOICED' or 'PAID' may be set manually.")

    current_idx = _PAYMENT_STATUS_FORWARD_ORDER.index(bill.status)
    target_idx = _PAYMENT_STATUS_FORWARD_ORDER.index(new_status)
    if target_idx != current_idx + 1:
        raise HTTPException(
            status_code=409,
            detail=f"Cannot move '{bill.bill_name}' from {bill.status.value} to {new_status.value} -- transitions must be sequential.",
        )

    bill.status = new_status
    if new_status == PaymentMilestoneStatus.INVOICED:
        bill.invoiced_at = datetime.utcnow()
    elif new_status == PaymentMilestoneStatus.PAID:
        bill.paid_at = datetime.utcnow()
    db.commit()

    return {"id": bill.id, "bill_name": bill.bill_name, "status": bill.status.value}


@router.get("/{site_id}/attendance/export")
def export_site_attendance(site_id: int, db: Session = Depends(get_db)):
    """
    On-demand .xlsx export of the complete historical labor ledger --
    generated fresh in-memory on every request (not persisted to `outputs/`
    or tracked as a `ProjectDocument`), keeping the web UI's Historical tab
    fast while leaving deep-history logging to spreadsheet software.
    """
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    attendance = AnalyticsEngine.get_attendance_sheet(db, site_id)
    daily_totals_asc = list(reversed(attendance["historical_daily_totals"]))
    ledger_rows = AnalyticsEngine.get_attendance_ledger_rows(db, site_id)

    workbook = build_attendance_workbook(site.name, daily_totals_asc, ledger_rows)
    buffer = io.BytesIO()
    workbook.save(buffer)
    buffer.seek(0)

    safe_name = "".join(c if c.isalnum() else "_" for c in site.name)[:60]
    filename = f"{safe_name}_Attendance_Log.xlsx"
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
