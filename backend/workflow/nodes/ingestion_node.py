"""
Node 1: Ingestion & Audit Trail.

Records file metadata, persists the raw document batch to project storage,
and writes the first IngestionAuditLog row so every downstream node has a
document to attach its own audit trail entries to.

A single logical report can span multiple physical images (e.g. 2-3
sequential WhatsApp photos of the same day's log). All pages in the batch
are persisted under one `ProjectDocument` row so downstream nodes still
deal with a single `document_id`, while the physical bytes live in an
ordered, page-numbered batch directory on disk.
"""
import os
import hashlib
from sqlalchemy.orm import Session

from backend.models import ProjectDocument, IngestionAuditLog, IngestionStatus
from backend.workflow.state import IngestState

NODE_NAME = "ingestion_and_audit_trail"


def _batch_signature(state: IngestState) -> str:
    """Deterministic key derived from the ordered set of filenames in this
    batch, so re-ingesting the exact same batch (e.g. under a different
    category) maps to the same storage directory -- mirroring the existing
    single-file dedup-safety behavior relied on by the delete endpoint."""
    joined = "|".join(f.file_name for f in state.files)
    return hashlib.sha1(joined.encode("utf-8")).hexdigest()[:12]


def _display_name(state: IngestState) -> str:
    names = [f.file_name for f in state.files]
    if len(names) <= 2:
        return ", ".join(names)
    return f"{names[0]} +{len(names) - 1} more page(s)"


def make_ingestion_node(db: Session):
    def _node(state: IngestState) -> dict:
        batch_dir = os.path.join(
            f"backend/storage/project_{state.project_id}/documents",
            f"batch_{_batch_signature(state)}",
        )
        os.makedirs(batch_dir, exist_ok=True)

        combined_hasher = hashlib.sha256()
        total_bytes = 0
        for idx, page in enumerate(state.files, start=1):
            page_path = os.path.join(batch_dir, f"page_{idx:02d}_{page.file_name}")
            with open(page_path, "wb") as f:
                f.write(page.file_bytes)
            combined_hasher.update(page.file_bytes)
            total_bytes += len(page.file_bytes)

        doc = ProjectDocument(
            project_id=state.project_id,
            file_name=_display_name(state),
            file_category=state.category,
            storage_path=batch_dir,
            file_hash=combined_hasher.hexdigest(),
            mime_type=state.files[0].mime_type if state.files else None,
            page_count=len(state.files),
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
                message=f"Recorded batch '{_display_name(state)}' ({len(state.files)} page(s), {total_bytes} bytes, category={state.category}).",
            )
        )
        db.flush()

        return {
            "document_id": doc.id,
            "storage_path": batch_dir,
            "audit_trail": state.audit_trail + [f"{NODE_NAME}: document #{doc.id} persisted ({len(state.files)} page(s))"],
        }

    return _node
