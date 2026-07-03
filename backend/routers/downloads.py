import os
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.excel_service.registry import TemplateRegistry
from backend.models import (
    ProjectDocument,
    DailyProgressLog,
    MaterialLedgerEntry,
    BillingMilestone,
    Drawing,
    ExceptionAlert,
)

router = APIRouter(prefix="/api/v1/sites", tags=["downloads"])


@router.get("/{site_id}/downloads")
def list_site_downloads(site_id: int, db: Session = Depends(get_db)):
    """
    Download Hub: one card per completed ingestion run that produced a
    tracking workbook, driven by `ProjectDocument` rows rather than a raw
    filesystem glob -- this ties each card to a `document_id` (for deletion)
    and its resolved operational `report_date` (for grouping/sorting).
    """
    docs = (
        db.query(ProjectDocument)
        .filter(
            ProjectDocument.project_id == site_id,
            ProjectDocument.excel_output_path.isnot(None),
        )
        .order_by(ProjectDocument.report_date.desc().nullslast(), ProjectDocument.uploaded_at.desc())
        .all()
    )

    files = []
    for doc in docs:
        path = doc.excel_output_path
        if not path or not os.path.exists(path):
            continue
        filename = os.path.basename(path)
        files.append(
            {
                "document_id": doc.id,
                "file_name": filename,
                "category": doc.file_category,
                "report_date": doc.report_date.isoformat() if doc.report_date else None,
                "last_synced_at": datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M UTC"),
                "size_bytes": os.path.getsize(path),
                "download_url": f"/api/v1/sites/{site_id}/downloads/{filename}",
            }
        )
    return files


@router.get("/{site_id}/downloads/{filename}")
def download_site_file(site_id: int, filename: str):
    config = TemplateRegistry.load()
    file_path = os.path.join(config.output_dir, filename)
    if not os.path.exists(file_path) or f"_{site_id}_" not in filename:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


@router.delete("/{site_id}/documents/{document_id}")
def delete_site_document(site_id: int, document_id: int, db: Session = Depends(get_db)):
    """
    Completely purges one ingestion run: the `ProjectDocument` row, every
    downstream ledger record it produced (DPR/material/billing/drawing +
    any exceptions raised against it), and the physical files on disk --
    the generated workbook always, and the original source upload only if
    no other document row still references the same physical file (which
    can happen when the same file was ingested under multiple categories).
    """
    document = (
        db.query(ProjectDocument)
        .filter(ProjectDocument.id == document_id, ProjectDocument.project_id == site_id)
        .first()
    )
    if not document:
        raise HTTPException(status_code=404, detail="Document not found for this site.")

    # DailyProgressLog cascades to its metrics/labor rows via the ORM
    # relationship's `cascade="all, delete-orphan"`, so load + delete the
    # parent objects rather than issuing a bulk DELETE.
    for log in db.query(DailyProgressLog).filter(DailyProgressLog.source_document_id == document_id).all():
        db.delete(log)

    db.query(MaterialLedgerEntry).filter(MaterialLedgerEntry.source_document_id == document_id).delete(synchronize_session=False)
    db.query(BillingMilestone).filter(BillingMilestone.source_document_id == document_id).delete(synchronize_session=False)
    db.query(Drawing).filter(Drawing.source_document_id == document_id).delete(synchronize_session=False)
    db.query(ExceptionAlert).filter(ExceptionAlert.source_document_id == document_id).delete(synchronize_session=False)

    # Only unlink the original source file if no sibling document (e.g. the
    # same physical upload ingested under a different category) still needs it.
    sibling_exists = (
        db.query(ProjectDocument)
        .filter(ProjectDocument.storage_path == document.storage_path, ProjectDocument.id != document.id)
        .first()
        is not None
    )
    if not sibling_exists and document.storage_path and os.path.exists(document.storage_path):
        try:
            os.remove(document.storage_path)
        except OSError:
            pass

    if document.excel_output_path and os.path.exists(document.excel_output_path):
        try:
            os.remove(document.excel_output_path)
        except OSError:
            pass

    # `IngestionAuditLog` rows cascade automatically via the
    # `ProjectDocument.audit_logs` relationship's delete-orphan cascade.
    db.delete(document)
    db.commit()

    return {"status": "deleted", "document_id": document_id}
