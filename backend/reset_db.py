"""Drops and recreates every table against the current model set, then reseeds demo data."""
from backend.database import Base, engine, init_db
from backend import models  # noqa: F401 - registers all tables on Base.metadata
from backend.seed_projects import seed_active_sites


def force_reset_database():
    print("Dropping all tables...")
    Base.metadata.drop_all(bind=engine)
    print("Recreating schema...")
    init_db()
    seed_active_sites()


if __name__ == "__main__":
    force_reset_database()
