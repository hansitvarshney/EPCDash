"""
FastAPI application entrypoint for the EPC Multi-Agent Platform.

Replaces the old monolithic `parser_agent.py`. All route logic now lives in
`backend/routers/`, all extraction/validation/write logic lives in the
LangGraph pipeline under `backend/workflow/`, and all workbook I/O goes
through `backend/excel_service/`.
"""
import os
import sys

# --- sys.path fallback -----------------------------------------------------
# Some deployment hosts (e.g. Railway/Nixpacks) launch this module with a
# working directory or root that does not put the repository root on
# `sys.path`, which breaks every `from backend.xxx import ...` below with
# `ModuleNotFoundError: No module named 'backend'`. Explicitly prepend the
# repo root (the parent of this `backend/` package) so imports resolve
# correctly no matter how/where the process is started from.
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
# -----------------------------------------------------------------------------

from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent
root_dir = backend_dir.parent
load_dotenv(dotenv_path=root_dir / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db, SessionLocal
from backend.routers import sites, ingest, exceptions, downloads, chat

app = FastAPI(title="EPC Multi-Agent Construction Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _seed_demo_data_if_empty() -> None:
    """
    Fresh deploys (e.g. Railway's ephemeral filesystem, a first-time local
    clone) start with an empty SQLite file. Auto-seed the 3 demo sites the
    very first time there's no project data at all, so the app is never
    left showing a blank portfolio -- this is a no-op (and touches nothing)
    once any project exists.
    """
    from backend.models import Project

    db = SessionLocal()
    try:
        has_data = db.query(Project).first() is not None
    finally:
        db.close()

    if not has_data:
        from backend.seed_projects import seed_active_sites

        print("No existing project data found -- seeding demo sites...")
        seed_active_sites()


@app.on_event("startup")
def on_startup():
    init_db()
    _seed_demo_data_if_empty()


app.include_router(sites.router)
app.include_router(ingest.router)
app.include_router(exceptions.router)
app.include_router(downloads.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "EPC Multi-Agent Construction Platform API"}
