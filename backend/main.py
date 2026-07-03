"""
FastAPI application entrypoint for the EPC Multi-Agent Platform.

Replaces the old monolithic `parser_agent.py`. All route logic now lives in
`backend/routers/`, all extraction/validation/write logic lives in the
LangGraph pipeline under `backend/workflow/`, and all workbook I/O goes
through `backend/excel_service/`.
"""
from pathlib import Path
from dotenv import load_dotenv

backend_dir = Path(__file__).resolve().parent
root_dir = backend_dir.parent
load_dotenv(dotenv_path=root_dir / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.database import init_db
from backend.routers import sites, ingest, exceptions, downloads, chat

app = FastAPI(title="EPC Multi-Agent Construction Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(sites.router)
app.include_router(ingest.router)
app.include_router(exceptions.router)
app.include_router(downloads.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"status": "ok", "service": "EPC Multi-Agent Construction Platform API"}
