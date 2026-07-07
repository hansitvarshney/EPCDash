import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum as SAEnum
from sqlalchemy.orm import relationship

from backend.database import Base


class MilestoneStatus(str, enum.Enum):
    PENDING = "PENDING"
    COMPLETED = "COMPLETED"


class ProjectMilestone(Base):
    """
    Micro-Schedule milestone row. Excel is the source of truth: every
    uploaded master-schedule workbook fully replaces the prior set of
    milestones for that project (see excel_writer_node.py's SCHEDULE
    branch), rather than being incrementally appended to like the other
    4 ingestion categories.
    """
    __tablename__ = "project_milestones"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    milestone_name = Column(String, nullable=False)
    target_date = Column(String, nullable=True)  # "YYYY-MM-DD", same convention as Project.start_date
    status = Column(SAEnum(MilestoneStatus), default=MilestoneStatus.PENDING, nullable=False)
    sequence = Column(Integer, default=0, nullable=False)
    source_document_id = Column(Integer, ForeignKey("project_documents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    project = relationship("Project", back_populates="milestones")
