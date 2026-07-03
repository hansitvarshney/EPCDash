"""
Wires the 4-node ingestion pipeline into a LangGraph StateGraph:

    Ingestion & Audit Trail -> Extraction -> Validation (The Judge) -> Excel Writer

Each node is built as a closure bound to the current request's SQLAlchemy
session via `make_*_node(db)`, mirroring the pattern already established in
the (now retired) `backend/graph_agent.py` prototype.
"""
from sqlalchemy.orm import Session
from langgraph.graph import StateGraph, END

from backend.workflow.state import IngestState
from backend.workflow.nodes.ingestion_node import make_ingestion_node
from backend.workflow.nodes.extraction_node import make_extraction_node
from backend.workflow.nodes.validation_node import make_validation_node
from backend.workflow.nodes.excel_writer_node import make_excel_writer_node


def build_ingest_graph(db: Session):
    workflow = StateGraph(IngestState)

    workflow.add_node("ingestion_and_audit_trail", make_ingestion_node(db))
    workflow.add_node("extraction", make_extraction_node(db))
    workflow.add_node("validation_judge", make_validation_node(db))
    workflow.add_node("excel_writer", make_excel_writer_node(db))

    workflow.set_entry_point("ingestion_and_audit_trail")
    workflow.add_edge("ingestion_and_audit_trail", "extraction")
    workflow.add_edge("extraction", "validation_judge")
    workflow.add_edge("validation_judge", "excel_writer")
    workflow.add_edge("excel_writer", END)

    return workflow.compile()


def run_ingest_workflow(
    db: Session,
    project_id: int,
    category: str,
    file_name: str,
    file_bytes: bytes,
    mime_type: str = "application/pdf",
) -> IngestState:
    """Convenience entrypoint used by the FastAPI ingest router."""
    graph = build_ingest_graph(db)
    initial_state = IngestState(
        project_id=project_id,
        category=category,
        file_name=file_name,
        mime_type=mime_type,
        file_bytes=file_bytes,
    )
    result = graph.invoke(initial_state)
    return IngestState(**result) if isinstance(result, dict) else result
