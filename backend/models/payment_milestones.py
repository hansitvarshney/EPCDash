import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship

from backend.database import Base


class PaymentMilestoneStatus(str, enum.Enum):
    LOCKED = "LOCKED"      # linked physical stage not yet complete
    ELIGIBLE = "ELIGIBLE"  # physical stage complete -> principal may invoice
    INVOICED = "INVOICED"  # principal has issued the RA Bill (manual action)
    PAID = "PAID"          # client has paid (manual action)


class PaymentMilestone(Base):
    """
    A contract stage-payment (RA Bill) tranche, decoupled from pure physical
    schedule tracking (see `ProjectMilestone`). Unlocked reactively by
    `backend/milestone_service.py` when its linked physical milestone is
    marked COMPLETED -- never derived from raw progress %, since billing
    eligibility is a discrete contractual event, not a continuous metric.

    Linked to its physical counterpart by NAME STRING, not a foreign key:
    Schedule Excel re-uploads fully replace `ProjectMilestone` rows (ids
    churn every time), so a hard FK would orphan on the very next upload.
    Resolving the link by name at sync time keeps this row's own lifecycle
    (LOCKED/ELIGIBLE/INVOICED/PAID) durable across those re-uploads.
    """
    __tablename__ = "payment_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    bill_name = Column(String, nullable=False)  # "RA Bill #3"
    contract_pct = Column(Float, nullable=False)  # 15.0 -- % of Project.contract_value
    linked_physical_milestone_name = Column(String, nullable=True)
    status = Column(SAEnum(PaymentMilestoneStatus), default=PaymentMilestoneStatus.LOCKED, nullable=False)

    eligible_at = Column(DateTime, nullable=True)
    invoiced_at = Column(DateTime, nullable=True)
    paid_at = Column(DateTime, nullable=True)
    whatsapp_alert_sent_at = Column(DateTime, nullable=True)  # idempotency guard for the eligibility alert

    sequence = Column(Integer, default=0, nullable=False)
    # Audit trail back to the actual signed tender/contract PDF this bill's
    # contract_pct terms were derived from (see ingest.py's TENDER_AGREEMENT
    # category).
    source_document_id = Column(Integer, ForeignKey("project_documents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="payment_milestones")
