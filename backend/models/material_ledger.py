from datetime import datetime
from sqlalchemy import Column, Integer, String, Float, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from backend.database import Base


class MaterialMaster(Base):
    """One row per tracked material per project — holds the BOQ/design allocation."""
    __tablename__ = "material_master"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    material_name = Column(String, nullable=False)
    unit = Column(String, nullable=False)
    design_specified_qty = Column(Float, nullable=False, default=0.0)

    project = relationship("Project", back_populates="materials")
    entries = relationship("MaterialLedgerEntry", back_populates="material", cascade="all, delete-orphan")


class MaterialLedgerEntry(Base):
    """
    A single received/consumed transaction against a MaterialMaster row.
    `stock_balance` / `wastage_*` are computed at write time (by the
    Validation node) and persisted as a snapshot so historical rows don't
    silently shift if a later entry is corrected.
    """
    __tablename__ = "material_ledger_entries"

    id = Column(Integer, primary_key=True, index=True)
    material_id = Column(Integer, ForeignKey("material_master.id"), nullable=False)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_date = Column(String, nullable=False)
    received_qty = Column(Float, default=0.0)
    consumed_qty = Column(Float, default=0.0)
    stock_balance = Column(Float, default=0.0)
    wastage_qty = Column(Float, default=0.0)
    wastage_pct = Column(Float, default=0.0)
    source_document_id = Column(Integer, ForeignKey("project_documents.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    material = relationship("MaterialMaster", back_populates="entries")
