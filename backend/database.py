import os
from datetime import datetime
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
    documents = relationship("ProjectDocument", back_populates="project") # 🔗 Link docs to projects

# 📄 ADD THIS NEW CLASS TO FIX THE IMPORT ERROR
class ProjectDocument(Base):
    """Tracks document processing metadata for GraphRAG document uploads."""
    __tablename__ = "project_documents"
    
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    file_name = Column(String, nullable=False)
    file_category = Column(String, nullable=False)  # e.g., 'CONTRACT', 'TENDER'
    storage_path = Column(String, nullable=False)   # Path on disk
    
    project = relationship("Project", back_populates="documents")

class DailySiteLog(Base):
    __tablename__ = "daily_site_logs"
    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    report_date = Column(String, nullable=False)  
    category = Column(String, nullable=False)     
    
    project = relationship("Project", back_populates="logs")
    labor_entries = relationship("LaborLedger", back_populates="site_log")
    work_metrics = relationship("DailyWorkMetrics", back_populates="site_log")

class LaborLedger(Base):
    __tablename__ = "ledger_labor"
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("daily_site_logs.id"), nullable=False)
    contractor_name = Column(String, nullable=False)
    crew_type = Column(String, nullable=False)      
    masons_count = Column(Integer, default=0)       
    helpers_count = Column(Integer, default=0)      
    assigned_activity = Column(String, nullable=True) 
    
    site_log = relationship("DailySiteLog", back_populates="labor_entries")

class DailyWorkMetrics(Base):
    __tablename__ = "ledger_daily_work_metrics"
    id = Column(Integer, primary_key=True, index=True)
    log_id = Column(Integer, ForeignKey("daily_site_logs.id"), nullable=False)
    category = Column(String, nullable=False)         
    element_id = Column(String, nullable=False)       
    sub_component = Column(String, nullable=True)     
    formula_notation = Column(String, nullable=True)  
    metric_value = Column(Float, nullable=False)      
    unit = Column(String, nullable=False)             
    
    site_log = relationship("DailySiteLog", back_populates="work_metrics")

def run_legacy_date_migration():
    """
    Scans existing DB rows to enforce strict standardization down to YYYY-MM-DD tokens.
    Prevents deletion route drops caused by variable formatting extractions.
    """
    db = SessionLocal()
    try:
        logs = db.query(DailySiteLog).all()
        modified = False
        for log in logs:
            clean = log.report_date.strip().replace("/", "-").replace(".", "-")
            for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%y-%m-%d", "%d-%m-%y"):
                try:
                    standardized = datetime.strptime(clean, fmt).strftime("%Y-%m-%d")
                    if log.report_date != standardized:
                        print(f"🔧 Retrofitting legacy database entry format: {log.report_date} -> {standardized}")
                        log.report_date = standardized
                        modified = True
                    break
                except ValueError:
                    continue
        if modified:
            db.commit()
            print("✅ Database structural date records successfully aligned.")
    except Exception as e:
        print(f"⚠️ Routine migration check deferred: {e}")
    finally:
        db.close()

def init_db():
    Base.metadata.create_all(bind=engine)
    # Automatically ensure historical rows match format layouts smoothly
    run_legacy_date_migration()

if __name__ == "__main__":
    print("Initializing local SQLite schemas...")
    # NOTE: Commented out schema removal to preserve your active database progress rows during manual test script execution runs
    # if os.path.exists(DB_PATH):
    #     os.remove(DB_PATH)
    init_db()
    print("Database ready.")