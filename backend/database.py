import os
from sqlalchemy import create_engine, Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker, relationship

DB_PATH = "epc_contractor.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class Project(Base):
    __tablename__ = "projects"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    logs = relationship("DailySiteLog", back_populates="project")

class DailySiteLog(Base):
    __tablename__ = "daily_site_logs"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_date = Column(String, nullable=False)  # YYYY-MM-DD
    category = Column(String, nullable=False)     # SHUTTERING, REINFORCEMENT_BBS, CONCRETE_POUR
    
    project = relationship("Project", back_populates="logs")
    labor_entries = relationship("LaborLedger", back_populates="site_log")
    work_metrics = relationship("DailyWorkMetrics", back_populates="site_log")

class LaborLedger(Base):
    """Tracks crew strengths across all phases (Civil, MEP, Finishes, Landscaping)."""
    __tablename__ = "ledger_labor"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("daily_site_logs.id"), nullable=False)
    contractor_name = Column(String, nullable=False)
    crew_type = Column(String, nullable=False)      # e.g., 'On Contract Basis', 'PRW'
    masons_count = Column(Integer, default=0)       # 'M' count
    helpers_count = Column(Integer, default=0)      # 'H' count
    assigned_activity = Column(String, nullable=True) # e.g., 'Excavation', 'Shear Wall Shuttering'
    
    site_log = relationship("DailySiteLog", back_populates="labor_entries")

class DailyWorkMetrics(Base):
    """
    AN INFINITELY ADAPTIVE LEDGER.
    Maps whatever work quantity is captured on the sheet based on the active construction timeline.
    """
    __tablename__ = "ledger_daily_work_metrics"
    
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("daily_site_logs.id"), nullable=False)
    
    category = Column(String, nullable=False)         # e.g., 'Shuttering Area', 'Concrete Pour', 'Steel BBS'
    element_id = Column(String, nullable=False)       # e.g., 'S/W-15', 'Stair Landing'
    sub_component = Column(String, nullable=True)     # e.g., 'Lapping', 'Hook', 'Ring'
    
    formula_notation = Column(String, nullable=True)  # Logs breakdown: '(1.35 x 3) x 2'
    metric_value = Column(Float, nullable=False)      # Quantitative output: 8.10, 4202.55
    unit = Column(String, nullable=False)             # Dynamic unit string: 'm2', 'm3', 'kg'
    
    site_log = relationship("DailySiteLog", back_populates="work_metrics")

def init_db():
    Base.metadata.create_all(bind=engine)

if __name__ == "__main__":
    print("Initializing local SQLite schemas...")
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    init_db()
    print("Database ready.")