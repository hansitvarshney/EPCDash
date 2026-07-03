"""
Node 1: Ingestion & Audit Trail.

Records file metadata, persists the raw document to project storage, and
writes the first IngestionAuditLog row so every downstream node has a
document to attach its own audit trail entries to.
"""
import os
import hashlib
from sqlalchemy.orm import Session

from backend.models import ProjectDocument, IngestionAuditLog, IngestionStatus
from backend.workflow.state import IngestState

NODE_NAME = "ingestion_and_audit_trail"


def make_ingestion_node(db: Session):
    def _node(state: IngestState) -> dict:
        storage_dir = f"backend/storage/project_{state.project_id}/documents"
        os.makedirs(storage_dir, exist_ok=True)
        storage_path = os.path.join(storage_dir, state.file_name)
        with open(storage_path, "wb") as f:
            f.write(state.file_bytes)

        file_hash = hashlib.sha256(state.file_bytes).hexdigest()

        doc = ProjectDocument(
            project_id=state.project_id,
            file_name=state.file_name,
            file_category=state.category,
            storage_path=storage_path,
            file_hash=file_hash,
            mime_type=state.mime_type,
            ingestion_status=IngestionStatus.PROCESSING,
        )
        db.add(doc)
        db.flush()

        db.add(
            IngestionAuditLog(
                project_id=state.project_id,
                document_id=doc.id,
                node_name=NODE_NAME,
                status="SUCCESS",
                message=f"Recorded '{state.file_name}' ({len(state.file_bytes)} bytes, category={state.category}).",
            )
        )
        db.flush()

        return {
            "document_id": doc.id,
            "storage_path": storage_path,
            "audit_trail": state.audit_trail + [f"{NODE_NAME}: document #{doc.id} persisted"],
        }

    return _node
