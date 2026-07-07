"""
Shared write-path for the principal-managed Daily Expense Log. Used by both
the manual "Principal Override" endpoint (`POST /sites/{id}/expenses`) and
the WhatsApp text short-circuit (`POST /ingest/whatsapp`), so both entry
points converge on identical upsert/patch semantics.
"""
from datetime import date, datetime
from typing import Optional

from sqlalchemy.orm import Session

from backend.models import DailyExpenseLog


def upsert_daily_expense(
    db: Session,
    project_id: int,
    report_date: Optional[str] = None,
    labor_wages_paid: Optional[float] = None,
    misc_expenses_paid: Optional[float] = None,
    misc_expenses_notes: Optional[str] = None,
    source: str = "MANUAL",
) -> DailyExpenseLog:
    """
    Creates or updates the one `DailyExpenseLog` row for (project_id,
    report_date). Only overwrites fields that are actually provided (patch
    semantics) -- e.g. a WhatsApp message that only mentions "labor 50000"
    must not blank out a misc-expense figure already logged for that day.
    """
    report_date = report_date or date.today().isoformat()

    row = (
        db.query(DailyExpenseLog)
        .filter(DailyExpenseLog.project_id == project_id, DailyExpenseLog.report_date == report_date)
        .first()
    )
    if not row:
        row = DailyExpenseLog(
            project_id=project_id,
            report_date=report_date,
            labor_wages_paid=0.0,
            misc_expenses_paid=0.0,
        )
        db.add(row)

    if labor_wages_paid is not None:
        row.labor_wages_paid = labor_wages_paid
    if misc_expenses_paid is not None:
        row.misc_expenses_paid = misc_expenses_paid
    if misc_expenses_notes is not None:
        row.misc_expenses_notes = misc_expenses_notes
    row.source = source
    row.updated_at = datetime.utcnow()

    db.commit()
    db.refresh(row)
    return row
