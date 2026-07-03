import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Date, Enum as SAEnum
from sqlalchemy.orm import relationship

from backend.database import Base


class IngestionStatus(str, enum.Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    COMPLETE = "COMPLETE"
    FAILED = "FAILED"


class ProjectDocument(Base):
    """Tracks every document uploaded for a project/site, plus ingest metadata."""
    __tablename__ = "project_documents"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_category = Column(String, nullable=False)  # e.g. 'CONTRACT', 'TENDER', 'DPR', 'MATERIAL', 'BILLING', 'DRAWING'
    storage_path = Column(String, nullable=False)

    uploaded_at = Column(DateTime, default=datetime.utcnow)
    file_hash = Column(String, nullable=True)
    page_count = Column(Integer, nullable=True)
    mime_type = Column(String, nullable=True)
    ingestion_status = Column(SAEnum(IngestionStatus), default=IngestionStatus.PENDING, nullable=False)

    # Operational date written on the physical log/document itself (not the
    # upload timestamp) -- resolved per-category by the Excel Writer node.
    report_date = Column(Date, nullable=True)
    # Path to the generated tracking workbook produced by this specific
    # ingestion run, if the pipeline completed successfully.
    excel_output_path = Column(String, nullable=True)

    project = relationship("Project", back_populates="documents")
    audit_logs = relationship("IngestionAuditLog", back_populates="document", cascade="all, delete-orphan")
    exceptions = relationship("ExceptionAlert", back_populates="source_document")


class IngestionAuditLog(Base):
    """
    One row per LangGraph node execution against a given document — the
    "Ingestion & Audit Trail Node" writes the first of these, and every
    downstream node (extraction / validation / excel writer) appends its own.
    """
    __tablename__ = "ingestion_audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    document_id = Column(Integer, ForeignKey("project_documents.id"), nullable=True)
    node_name = Column(String, nullable=False)
    status = Column(String, nullable=False)  # e.g. STARTED / SUCCESS / FAILED
    message = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="audit_logs")
    document = relationship("ProjectDocument", back_populates="audit_logs")
