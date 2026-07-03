from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ExceptionAlert, ProjectDocument

router = APIRouter(prefix="/api/v1/sites", tags=["exceptions"])


def _serialize(alert: ExceptionAlert, document: ProjectDocument | None) -> dict:
    return {
        "id": alert.id,
        "category": alert.category.value,
        "severity": alert.severity.value,
        "message": alert.message,
        "related_table": alert.related_table,
        "related_record_id": alert.related_record_id,
        "is_resolved": alert.is_resolved,
        "created_at": alert.created_at.isoformat() if alert.created_at else None,
        "source_citation": {
            "document_name": document.file_name if document else None,
            "page_number": alert.source_page_number,
            "text_snippet": alert.source_text_snippet,
        },
    }


@router.get("/{site_id}/exceptions")
def list_exceptions(site_id: int, include_resolved: bool = False, db: Session = Depends(get_db)):
    """Critical Exceptions Feed: flagged data anomalies for a site."""
    query = db.query(ExceptionAlert).filter(ExceptionAlert.project_id == site_id)
    if not include_resolved:
        query = query.filter(ExceptionAlert.is_resolved.is_(False))
    alerts = query.order_by(ExceptionAlert.created_at.desc()).all()

    results = []
    for alert in alerts:
        document = db.query(ProjectDocument).filter(ProjectDocument.id == alert.source_document_id).first() if alert.source_document_id else None
        results.append(_serialize(alert, document))
    return results


@router.get("/{site_id}/exceptions/{exception_id}")
def get_exception_detail(site_id: int, exception_id: int, db: Session = Depends(get_db)):
    """Source-citation metadata modal: exact document, page number, and source text snippet."""
    alert = db.query(ExceptionAlert).filter(ExceptionAlert.id == exception_id, ExceptionAlert.project_id == site_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Exception not found")
    document = db.query(ProjectDocument).filter(ProjectDocument.id == alert.source_document_id).first() if alert.source_document_id else None
    return _serialize(alert, document)


@router.post("/{site_id}/exceptions/{exception_id}/resolve")
def resolve_exception(site_id: int, exception_id: int, db: Session = Depends(get_db)):
    alert = db.query(ExceptionAlert).filter(ExceptionAlert.id == exception_id, ExceptionAlert.project_id == site_id).first()
    if not alert:
        raise HTTPException(status_code=404, detail="Exception not found")
    alert.is_resolved = True
    db.commit()
    return {"status": "success", "id": alert.id, "is_resolved": True}
