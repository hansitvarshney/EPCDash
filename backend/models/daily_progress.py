import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship

from backend.database import Base


class MetricType(str, enum.Enum):
    CONCRETE_VOLUME_M3 = "CONCRETE_VOLUME_M3"
    REINFORCEMENT_MT = "REINFORCEMENT_MT"
    SHUTTERING_SQM = "SHUTTERING_SQM"
    OTHER = "OTHER"


class DailyProgressLog(Base):
    """
    Header row for a single project/date Daily Progress Report (DPR).
    Granular quantities live in DailyProgressMetric; per-contractor labor
    breakdowns live in LaborLedger.
    """
    __tablename__ = "daily_progress_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_date = Column(String, nullable=False)
    category = Column(String, nullable=False, default="GENERAL_CIVIL_WORKS")
    labor_headcount = Column(Integer, default=0)
    structural_progress_pct = Column(Float, nullable=True)
    notes = Column(String, nullable=True)
    source_document_id = Column(Integer, ForeignKey("project_documents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="daily_logs")
    metrics = relationship("DailyProgressMetric", back_populates="log", cascade="all, delete-orphan")
    labor_entries = relationship("LaborLedger", back_populates="log", cascade="all, delete-orphan")


class DailyProgressMetric(Base):
    """
    Element-level granular quantity row (replaces the old DailyWorkMetrics).
    `metric_type` classifies the row into one of the DPR's headline KPIs
    (concrete / reinforcement / shuttering) or OTHER for anything else.
    """
    __tablename__ = "daily_progress_metrics"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("daily_progress_logs.id"), nullable=False)
    metric_type = Column(SAEnum(MetricType), default=MetricType.OTHER, nullable=False)
    category = Column(String, nullable=False)
    element_id = Column(String, nullable=False)
    sub_component = Column(String, nullable=True)
    formula_notation = Column(String, nullable=True)
    metric_value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)

    log = relationship("DailyProgressLog", back_populates="metrics")


class LaborLedger(Base):
    __tablename__ = "ledger_labor"

    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("daily_progress_logs.id"), nullable=False)
    contractor_name = Column(String, nullable=False)
    crew_type = Column(String, nullable=False)
    masons_count = Column(Integer, default=0)
    helpers_count = Column(Integer, default=0)
    assigned_activity = Column(String, nullable=True)

    log = relationship("DailyProgressLog", back_populates="labor_entries")
