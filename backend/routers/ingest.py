import os
import traceback
from pathlib import Path
from typing import List

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Project, ProjectDocument
from backend.workflow.graph import run_ingest_workflow
from backend.graph_rag import build_project_knowledge_graph

router = APIRouter(prefix="/api/v1/sites", tags=["ingest"])

VALID_CATEGORIES = {"DPR", "MATERIAL", "BILLING", "DRAWING"}


def _get_or_create_site(db: Session, site_id: int) -> Project:
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        site = Project(id=site_id, name=f"Site Workspace {site_id}")
        db.add(site)
        db.commit()
        db.refresh(site)
    return site


@router.post("/{site_id}/ingest")
async def ingest_site_document(
    site_id: int,
    categories: List[str] = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Runs the full 4-node LangGraph pipeline (Ingestion & Audit Trail ->
    Extraction -> Validation/Judge -> Excel Writer) against one uploaded
    document, once per selected operational category. This supports
    multi-sheet documents that pack more than one ledger's worth of data
    (e.g. a combined DPR + Material sheet) into a single upload -- the same
    file bytes are re-run through the category-specific extraction schema
    for each selection, and results are aggregated into one response.
    """
    normalized_categories = [c.strip().upper() for c in categories if c.strip()]
    if not normalized_categories:
        raise HTTPException(status_code=400, detail="At least one category must be selected.")
    invalid = sorted(set(normalized_categories) - VALID_CATEGORIES)
    if invalid:
        raise HTTPException(status_code=400, detail=f"Invalid categories {invalid}. Must be one of {sorted(VALID_CATEGORIES)}.")

    _get_or_create_site(db, site_id)

    file_bytes = await file.read()
    suffix = Path(file.filename).suffix.lower()
    mime_type = "application/pdf" if suffix == ".pdf" else ("image/png" if suffix == ".png" else "image/jpeg")

    results = []
    for category in normalized_categories:
        try:
            result_state = run_ingest_workflow(
                db=db,
                project_id=site_id,
                category=category,
                file_name=file.filename,
                file_bytes=file_bytes,
                mime_type=mime_type,
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

    return {"status": overall_status, "file_name": file.filename, "results": results}


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

    try:
        build_project_knowledge_graph(site_id, db)
    except Exception as exc:
        print(f"Graph compilation deferred: {exc}")

    return {"status": "success", "file_name": file.filename, "message": "File indexed successfully."}
