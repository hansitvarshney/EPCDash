import os
import traceback
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Project, ProjectDocument
from backend.workflow.graph import run_ingest_workflow
from backend.workflow.state import IngestFile
from backend.graph_rag import build_project_knowledge_graph
from backend.graph_query_engine import invalidate_document_cache

router = APIRouter(prefix="/api/v1/sites", tags=["ingest"])

# Categories that flow through the 4-node LangGraph ledger pipeline
# (Ingestion -> Extraction -> Validation -> Excel Writer), producing rows in
# a specific SQL table + a generated tracking workbook.
LEDGER_CATEGORIES = {"DPR", "MATERIAL", "BILLING", "DRAWING", "SCHEDULE"}
# Raw reference documents -- no extraction schema produces ledger rows from
# these; they're stored + indexed into the GraphRAG knowledge graph for the
# chat assistant instead, identical to the "Attach" flow in DocumentChat.
REFERENCE_CATEGORIES = {"TENDER_AGREEMENT"}
VALID_CATEGORIES = LEDGER_CATEGORIES | REFERENCE_CATEGORIES


def _get_or_create_site(db: Session, site_id: int) -> Project:
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        site = Project(id=site_id, name=f"Site Workspace {site_id}")
        db.add(site)
        db.commit()
        db.refresh(site)
    return site


def _infer_mime_type(filename: str) -> str:
    suffix = Path(filename).suffix.lower()
    if suffix == ".pdf":
        return "application/pdf"
    if suffix == ".png":
        return "image/png"
    if suffix in (".xlsx", ".xlsm"):
        return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    return "image/jpeg"


def _ingest_reference_documents(db: Session, site_id: int, category: str, files: List[UploadFile], file_bytes: List[bytes]) -> dict:
    """
    Persists each uploaded file as a `ProjectDocument` tagged with the given
    reference category (e.g. TENDER_AGREEMENT) and rebuilds the project's
    GraphRAG knowledge graph -- mirroring `upload_reference_document()`
    below, just reachable from the same "Ingest New Document" panel used
    for the 4 ledger categories instead of the separate DocumentChat
    "Attach" button. Bypasses the LangGraph pipeline entirely: a tender
    contract PDF has no extraction schema that produces ledger rows.
    """
    storage_dir = f"backend/storage/project_{site_id}/documents"
    os.makedirs(storage_dir, exist_ok=True)

    document_ids = []
    for upload, content in zip(files, file_bytes):
        local_path = os.path.join(storage_dir, upload.filename)
        with open(local_path, "wb") as f:
            f.write(content)

        existing = (
            db.query(ProjectDocument)
            .filter(ProjectDocument.project_id == site_id, ProjectDocument.file_name == upload.filename)
            .first()
        )
        if existing:
            existing.file_category = category
            existing.storage_path = local_path
            document = existing
        else:
            document = ProjectDocument(
                project_id=site_id,
                file_name=upload.filename,
                file_category=category,
                storage_path=local_path,
                mime_type=_infer_mime_type(upload.filename),
            )
            db.add(document)
        db.commit()
        db.refresh(document)
        document_ids.append(document.id)

    # Invalidate before rebuilding the graph so a chat query racing this
    # upload can't repopulate the cache with stale (pre-upload) text.
    invalidate_document_cache(site_id)
    try:
        build_project_knowledge_graph(site_id, db)
    except Exception as exc:
        print(f"Graph compilation deferred: {exc}")

    return {
        "category": category,
        "status": "success",
        "document_id": document_ids[-1] if document_ids else None,
        "excel_output_path": None,
        "exceptions_raised": 0,
        "audit_trail": [f"reference_ingestion: stored {len(document_ids)} {category} document(s)"],
    }


@router.post("/{site_id}/ingest")
async def ingest_site_document(
    site_id: int,
    categories: List[str] = Form(...),
    files: List[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    """
    Runs the full 4-node LangGraph pipeline (Ingestion & Audit Trail ->
    Extraction -> Validation/Judge -> Excel Writer) against a batch of one
    or more uploaded pages/photos, once per selected operational category.

    The batch supports two independent axes of "multiple":
    - Multiple physical images that together form ONE logical report (e.g.
      2-3 sequential WhatsApp photos of the same day's log) -- these are
      read together by Gemini as continuous context and resolve to a single
      cohesive record.
    - Multiple selected categories for that same batch (e.g. a combined
      DPR + Material sheet) -- the same batch is re-run through each
      category-specific extraction schema, and results are aggregated into
      one response.
    """
    normalized_categories = [c.strip().upper() for c in categories if c.strip()]
    if not normalized_categories:
        raise HTTPException(status_code=400, detail="At least one category must be selected.")
    invalid = sorted(set(normalized_categories) - VALID_CATEGORIES)
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid categories {invalid}. Must be one of {sorted(VALID_CATEGORIES)}.")
    if not files:
        raise HTTPException(status_code=400, detail="At least one file must be uploaded.")

    _get_or_create_site(db, site_id)

    ingest_files: List[IngestFile] = []
    for upload in files:
        content = await upload.read()
        ingest_files.append(IngestFile(file_name=upload.filename, mime_type=_infer_mime_type(upload.filename), file_bytes=content))

    results = []
    for category in normalized_categories:
        if category in REFERENCE_CATEGORIES:
            try:
                results.append(
                    _ingest_reference_documents(
                        db, site_id, category, files, [f.file_bytes for f in ingest_files]
                    )
                )
            except Exception as exc:
                db.rollback()
                traceback.print_exc()
                results.append({"category": category, "status": "error", "error": f"Reference document ingestion fault: {exc}"})
            continue

        try:
            result_state = run_ingest_workflow(
                db=db,
                project_id=site_id,
                category=category,
                files=ingest_files,
            )
        except Exception as exc:
            db.rollback()
            traceback.print_exc()
            results.append({"category": category, "status": "error", "error": f"Ingestion pipeline fault: {exc}"})
            continue

        if result_state.error:
            results.append({"category": category, "status": "error", "error": result_state.error})
            continue

        results.append(
            {
                "category": category,
                "status": "success",
                "document_id": result_state.document_id,
                "excel_output_path": result_state.excel_output_path,
                "exceptions_raised": len(result_state.exceptions),
                "audit_trail": result_state.audit_trail,
            }
        )

    success_count = sum(1 for r in results if r["status"] == "success")
    if success_count == len(results):
        overall_status = "success"
    elif success_count == 0:
        overall_status = "error"
    else:
        overall_status = "partial_success"

    return {
        "status": overall_status,
        "file_names": [f.filename for f in files],
        "page_count": len(files),
        "results": results,
    }


@router.post("/{site_id}/documents")
async def upload_reference_document(site_id: int, file: UploadFile = File(...), db: Session = Depends(get_db)):
    """
    Uploads a contract/tender/spec reference document (not a ledger sheet)
    for the GraphRAG document assistant, and refreshes the site's knowledge graph.
    """
    _get_or_create_site(db, site_id)

    storage_dir = f"backend/storage/project_{site_id}/documents"
    os.makedirs(storage_dir, exist_ok=True)
    local_path = os.path.join(storage_dir, file.filename)

    try:
        contents = await file.read()
        with open(local_path, "wb") as f:
            f.write(contents)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to write file: {exc}")

    exists = db.query(ProjectDocument).filter(ProjectDocument.project_id == site_id, ProjectDocument.file_name == file.filename).first()
    if not exists:
        file_category = "SPEC"
        lowered = file.filename.lower()
        if "contract" in lowered:
            file_category = "CONTRACT"
        elif "tender" in lowered:
            file_category = "TENDER"

        db.add(ProjectDocument(project_id=site_id, file_name=file.filename, file_category=file_category, storage_path=local_path))
        db.commit()

    invalidate_document_cache(site_id)
    try:
        build_project_knowledge_graph(site_id, db)
    except Exception as exc:
        print(f"Graph compilation deferred: {exc}")

    return {"status": "success", "file_name": file.filename, "message": "File indexed successfully."}
