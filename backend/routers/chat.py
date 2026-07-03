import os
import shutil

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import ProjectDocument
from backend.graph_query_engine import answer_project_query

router = APIRouter(prefix="/api/v1/sites", tags=["chat"])


class ChatQueryRequest(BaseModel):
    question: str


@router.post("/{site_id}/chat")
def chat_with_site_documents(site_id: int, payload: ChatQueryRequest):
    if not payload.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")
    return {"status": "success", "site_id": site_id, "response": answer_project_query(site_id, payload.question)}


@router.get("/{site_id}/documents")
def list_site_documents(site_id: int, db: Session = Depends(get_db)):
    docs = db.query(ProjectDocument).filter(ProjectDocument.project_id == site_id).all()
    return [
        {
            "id": d.id,
            "file_name": d.file_name,
            "file_category": d.file_category,
            "ingestion_status": d.ingestion_status.value if d.ingestion_status else None,
            "uploaded_at": d.uploaded_at.isoformat() if d.uploaded_at else None,
        }
        for d in docs
    ]


@router.delete("/{site_id}/documents/{document_id}")
def delete_site_document(site_id: int, document_id: int, db: Session = Depends(get_db)):
    doc = db.query(ProjectDocument).filter(ProjectDocument.project_id == site_id, ProjectDocument.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    if os.path.exists(doc.storage_path):
        os.remove(doc.storage_path)
    index_path = f"backend/storage/project_{site_id}/doc_{document_id}"
    if os.path.exists(index_path):
        shutil.rmtree(index_path)
    db.delete(doc)
    db.commit()
    return {"status": "success", "message": f"Document {doc.file_name} removed successfully."}
