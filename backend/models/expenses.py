from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, UniqueConstraint
from sqlalchemy.orm import relationship

from backend.database import Base


class DailyExpenseLog(Base):
    """
    Principal-managed daily cash outflow log. Labor wages and misc site
    overheads are highly variable and controlled entirely by the principal
    (not derivable from vendor POs or ingested DPRs), so this is a thin,
    directly-editable ledger keyed one row per (project, report_date) --
    upserted either via the "Principal Override" widget or a WhatsApp text
    short-circuit (see `backend/expense_service.py`).
    """
    __tablename__ = "daily_expense_logs"
    __table_args__ = (UniqueConstraint("project_id", "report_date", name="uq_daily_expense_project_date"),)

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_date = Column(String, nullable=False)  # "YYYY-MM-DD", same convention as other date-string columns
    labor_wages_paid = Column(Float, nullable=False, default=0.0)
    misc_expenses_paid = Column(Float, nullable=False, default=0.0)
    misc_expenses_notes = Column(String, nullable=True)  # free-text context, e.g. "Diesel, equipment rental"
    source = Column(String, nullable=False, default="MANUAL")  # "MANUAL" | "WHATSAPP"
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    project = relationship("Project", back_populates="daily_expenses")
