from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class ExceptionDraft(BaseModel):
    """In-flight exception raised by the Validation node, persisted by the Excel Writer node."""

    category: str
    severity: str = "WARNING"  # INFO | WARNING | CRITICAL
    message: str
    related_table: Optional[str] = None
    related_record_id: Optional[int] = None
    source_page_number: Optional[int] = None
    source_text_snippet: Optional[str] = None
    excel_row: Optional[int] = None
    excel_field: Optional[str] = None
    entry_index: Optional[int] = None  # index into payload's list of records this exception targets, if any


class IngestFile(BaseModel):
    """One physical page/photo within a (possibly multi-image) upload batch."""

    file_name: str
    mime_type: str = "application/pdf"
    file_bytes: bytes = b""


class IngestState(BaseModel):
    """
    Shared state threaded through the 4-node LangGraph ingestion workflow.

    `files` holds an ordered batch of one-or-more physical images/pages that
    together represent a single logical report (e.g. 2-3 sequential WhatsApp
    photos of the same day's DPR sheet). The pipeline persists the whole
    batch under one `ProjectDocument` row and asks Gemini to read all pages
    together, producing a single cohesive extracted record.
    """

    project_id: int
    category: str  # DPR | MATERIAL | BILLING | DRAWING
    files: List[IngestFile] = Field(default_factory=list)

    document_id: Optional[int] = None
    storage_path: Optional[str] = None

    extracted_payload: Optional[Dict[str, Any]] = None
    exceptions: List[ExceptionDraft] = Field(default_factory=list)

    excel_output_path: Optional[str] = None
    audit_trail: List[str] = Field(default_factory=list)
    error: Optional[str] = None
