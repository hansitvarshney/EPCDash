"""
Node 2: Extraction.

Leverages Gemini structured outputs to safely populate the target schema for
the document's category (DPR / MATERIAL / BILLING / DRAWING).
"""
import time
import json
from sqlalchemy.orm import Session
from google import genai
from google.genai import types
from google.genai.errors import ServerError

from backend.models import IngestionAuditLog
from backend.workflow.state import IngestState
from backend.workflow.schemas import CATEGORY_SCHEMAS, CATEGORY_PROMPTS

NODE_NAME = "extraction"
_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client()
    return _client


def _execute_with_retry(client, contents, config_obj, max_retries: int = 4, backoff_delay: int = 5):
    for attempt in range(max_retries):
        try:
            return client.models.generate_content(model="gemini-2.5-flash", contents=contents, config=config_obj)
        except ServerError as se:
            error_msg = str(se)
            transient = "503" in error_msg or "429" in error_msg or "Resource exhausted" in error_msg
            if transient and attempt < max_retries - 1:
                time.sleep(backoff_delay)
                backoff_delay *= 2
                continue
            raise


def make_extraction_node(db: Session):
    def _node(state: IngestState) -> dict:
        schema_cls = CATEGORY_SCHEMAS.get(state.category)
        if not schema_cls:
            return {
                "error": f"Unsupported ingestion category '{state.category}'.",
                "audit_trail": state.audit_trail + [f"{NODE_NAME}: unsupported category"],
            }

        client = _get_client()
        part = types.Part.from_bytes(data=state.file_bytes, mime_type=state.mime_type)
        prompt = CATEGORY_PROMPTS[state.category]

        config_obj = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=schema_cls,
            temperature=0.0,
        )

        try:
            response = _execute_with_retry(client, [part, prompt], config_obj)
            parsed = schema_cls.model_validate_json(response.text)
            payload = parsed.model_dump()
            status, message = "SUCCESS", f"Extracted {state.category} payload."
        except Exception as exc:  # noqa: BLE001 - surfaced to caller via state.error
            payload = None
            status, message = "FAILED", f"Extraction failed: {exc}"

        if state.document_id:
            db.add(
                IngestionAuditLog(
                    project_id=state.project_id,
                    document_id=state.document_id,
                    node_name=NODE_NAME,
                    status=status,
                    message=message,
                )
            )
            db.flush()

        return {
            "extracted_payload": payload,
            "error": None if payload is not None else message,
            "audit_trail": state.audit_trail + [f"{NODE_NAME}: {status}"],
        }

    return _node
