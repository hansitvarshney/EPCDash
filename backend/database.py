"""
Core database bootstrap: engine, session factory, declarative Base, and
schema initialization. All ORM models live under `backend/models/` and are
imported here (indirectly, via `backend.models`) so that `Base.metadata`
is aware of every table before `create_all()` runs.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

DB_PATH = "epc_contractor.db"
engine = create_engine(f"sqlite:///{DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    """FastAPI dependency: yields a scoped session and guarantees closure."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    # Import side-effect: registers every model class on Base.metadata.
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)


if __name__ == "__main__":
    print("Initializing local SQLite schema...")
    init_db()
    print("Database ready.")
