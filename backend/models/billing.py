import enum
from sqlalchemy import Column, Integer, String, Float, ForeignKey, Enum as SAEnum
from sqlalchemy.orm import relationship

from backend.database import Base


class BillingStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    PAID = "PAID"
    OVERDUE = "OVERDUE"


class Vendor(Base):
    """A sub-contractor / vendor holding a Purchase Order against a project."""
    __tablename__ = "vendors"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    vendor_name = Column(String, nullable=False)
    trade = Column(String, nullable=True)
    po_number = Column(String, nullable=True)
    po_limit = Column(Float, nullable=False, default=0.0)

    project = relationship("Project", back_populates="vendors")
    milestones = relationship("BillingMilestone", back_populates="vendor", cascade="all, delete-orphan")


class BillingMilestone(Base):
    """A single invoice / certified-work milestone submitted against a vendor's PO."""
    __tablename__ = "billing_milestones"

    id = Column(Integer, primary_key=True, index=True)
    vendor_id = Column(Integer, ForeignKey("vendors.id"), nullable=False)
    invoice_number = Column(String, nullable=True)
    invoice_date = Column(String, nullable=True)
    certified_work_pct = Column(Float, nullable=True)
    invoice_amount = Column(Float, nullable=False, default=0.0)
    cumulative_billed = Column(Float, nullable=False, default=0.0)
    po_remaining_balance = Column(Float, nullable=True)
    submitted_date = Column(String, nullable=True)
    aging_days = Column(Integer, nullable=True)
    status = Column(SAEnum(BillingStatus), default=BillingStatus.PENDING, nullable=False)
    source_document_id = Column(Integer, ForeignKey("project_documents.id"), nullable=True)

    vendor = relationship("Vendor", back_populates="milestones")
