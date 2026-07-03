import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship

from backend.database import Base


class SignoffStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class Drawing(Base):
    """EPC Regulatory & Drawing Log entry: GFC revision + client sign-off tracking."""
    __tablename__ = "drawings"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    drawing_number = Column(String, nullable=False)
    drawing_title = Column(String, nullable=True)
    discipline = Column(String, nullable=True)  # e.g. Structural / Architectural / MEP
    gfc_revision = Column(String, nullable=True)
    gfc_issue_date = Column(String, nullable=True)
    client_signoff_status = Column(SAEnum(SignoffStatus), default=SignoffStatus.PENDING, nullable=False)
    client_signoff_date = Column(String, nullable=True)
    source_document_id = Column(Integer, ForeignKey("project_documents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="drawings")
