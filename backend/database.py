"""
Core database bootstrap: engine, session factory, declarative Base, and
schema initialization. All ORM models live under `backend/models/` and are
imported here (indirectly, via `backend.models`) so that `Base.metadata`
is aware of every table before `create_all()` runs.
"""
from sqlalchemy import create_engine, inspect, text
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


def _add_missing_columns() -> None:
    """
    Lightweight stand-in for a real migration tool (no Alembic in this
    project). `create_all()` only creates whole tables that don't exist yet
    -- it silently skips new columns added to a model whose table is
    already present (e.g. adding `ExceptionAlert.penalty_amount` to the
    live `exception_alerts` table). This walks every mapped table/column
    and issues a plain `ALTER TABLE ... ADD COLUMN` for anything missing,
    which SQLite supports directly. Safe to run on every startup: it's a
    no-op once columns exist.
    """
    inspector = inspect(engine)
    existing_tables = set(inspector.get_table_names())
    with engine.connect() as conn:
        for table in Base.metadata.tables.values():
            if table.name not in existing_tables:
                continue  # brand-new table -- create_all() already handled it
            existing_columns = {col["name"] for col in inspector.get_columns(table.name)}
            for column in table.columns:
                if column.name in existing_columns:
                    continue
                conn.execute(text(f'ALTER TABLE "{table.name}" ADD COLUMN "{column.name}" {column.type}'))
        conn.commit()


def init_db():
    # Import side-effect: registers every model class on Base.metadata.
    from backend import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
    _add_missing_columns()


if __name__ == "__main__":
    print("Initializing local SQLite schema...")
    init_db()
    print("Database ready.")
