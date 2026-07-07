from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.orm import relationship

from backend.database import Base


class Project(Base):
    """
    A single active construction Site. Kept as a flat entity (no separate
    Site sub-table) per the architectural decision: Project == Site.
    """
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    location = Column(String, nullable=True)
    client_name = Column(String, nullable=True)
    contract_value = Column(Float, nullable=True)
    start_date = Column(String, nullable=True)
    target_end_date = Column(String, nullable=True)
    # Recipient for outbound WhatsApp alerts (milestone-eligibility pings,
    # drafted RA Bill emails). Nullable -- see whatsapp_client.py, which
    # logs to OutboundMessageLog instead of failing when unset.
    principal_whatsapp_number = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Note: health_status (On Track / At Risk / Action Required) is NOT a
    # stored column. It is computed live by AnalyticsEngine.get_site_health()
    # from open ExceptionAlert severities + schedule variance, so it can
    # never drift out of sync with the underlying ledgers.

    documents = relationship("ProjectDocument", back_populates="project", cascade="all, delete-orphan")
    daily_logs = relationship("DailyProgressLog", back_populates="project", cascade="all, delete-orphan")
    materials = relationship("MaterialMaster", back_populates="project", cascade="all, delete-orphan")
    vendors = relationship("Vendor", back_populates="project", cascade="all, delete-orphan")
    drawings = relationship("Drawing", back_populates="project", cascade="all, delete-orphan")
    exceptions = relationship("ExceptionAlert", back_populates="project", cascade="all, delete-orphan")
    audit_logs = relationship("IngestionAuditLog", back_populates="project", cascade="all, delete-orphan")
    milestones = relationship("ProjectMilestone", back_populates="project", cascade="all, delete-orphan")
    daily_expenses = relationship("DailyExpenseLog", back_populates="project", cascade="all, delete-orphan")
    payment_milestones = relationship("PaymentMilestone", back_populates="project", cascade="all, delete-orphan")
