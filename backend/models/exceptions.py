import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Boolean, Float, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship

from backend.database import Base


class ExceptionCategory(str, enum.Enum):
    DPR = "DPR"
    MATERIAL = "MATERIAL"
    BILLING = "BILLING"
    DRAWING = "DRAWING"
    SCHEDULE = "SCHEDULE"


class ExceptionSeverity(str, enum.Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"


class ExceptionAlert(Base):
    """
    Output of the Validation ("The Judge") node. Powers the frontend's
    Critical Exceptions Feed, including the source-citation modal
    (document name + page number + source text snippet).
    """
    __tablename__ = "exception_alerts"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    category = Column(SAEnum(ExceptionCategory), nullable=False)
    severity = Column(SAEnum(ExceptionSeverity), nullable=False, default=ExceptionSeverity.WARNING)
    message = Column(String, nullable=False)
    related_table = Column(String, nullable=True)
    related_record_id = Column(Integer, nullable=True)

    source_document_id = Column(Integer, ForeignKey("project_documents.id"), nullable=True)
    source_page_number = Column(Integer, nullable=True)
    source_text_snippet = Column(String, nullable=True)

    is_resolved = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Monetary impact of this exception, when known (e.g. a contractual
    # penalty/liquidated-damages amount). Nullable/defaulted to 0.0 since
    # today's validators don't populate it yet -- it's wired into
    # `AnalyticsEngine.get_financial_ledger()`'s "Active Penalties" term now
    # so a future Compliance & EHS Penalty Log (see SILCHAR_AUDIT.md) can
    # start writing real amounts without any further formula changes.
    penalty_amount = Column(Float, nullable=True, default=0.0)

    project = relationship("Project", back_populates="exceptions")
    source_document = relationship("ProjectDocument", back_populates="exceptions")
