"""
Node 4: Excel Writer.

Persists the validated payload into the relevant SQL ledger tables, then
uses the Excel Service Layer to append the same rows into the styled,
multi-tab local workbook -- embedding formatting flags for any exceptions
"The Judge" raised. Finally persists ExceptionAlert rows (with source
citation metadata) so the frontend's Critical Exceptions Feed can render
them.
"""
from datetime import datetime
from sqlalchemy.orm import Session

from backend.models import (
    IngestionAuditLog,
    IngestionStatus,
    ProjectDocument,
    DailyProgressLog,
    DailyProgressMetric,
    LaborLedger,
    MetricType,
    MaterialLedgerEntry,
    BillingMilestone,
    BillingStatus,
    Drawing,
    SignoffStatus,
    ExceptionAlert,
    ExceptionCategory,
    ExceptionSeverity,
)
from backend.excel_service.writer import ExcelWriterService
from backend.workflow.state import IngestState, ExceptionDraft

NODE_NAME = "excel_writer"

# The field on each category's extracted payload that carries the actual
# operational date written on the physical document (not the upload time).
# Checked in priority order; the first present + parseable value wins.
_REPORT_DATE_FIELDS = {
    "DPR": ("report_date",),
    "MATERIAL": ("report_date",),
    "BILLING": ("invoice_date", "submitted_date"),
    "DRAWING": ("gfc_issue_date", "client_signoff_date"),
}


def _resolve_report_date(category: str, payload: dict):
    for field in _REPORT_DATE_FIELDS.get(category, ()):
        raw = payload.get(field)
        if not raw:
            continue
        try:
            return datetime.strptime(raw, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            continue
    return None


def _write_dpr(db: Session, excel: ExcelWriterService, project_id: int, document_id, payload: dict) -> list:
    log = DailyProgressLog(
        project_id=project_id,
        report_date=payload["report_date"],
        category=payload.get("log_category", "GENERAL_CIVIL_WORKS"),
        labor_headcount=payload["manpower_deployed"]["cumulative_masons"] + payload["manpower_deployed"]["cumulative_helpers"],
        structural_progress_pct=payload.get("structural_progress_pct"),
        source_document_id=document_id,
    )
    db.add(log)
    db.flush()

    db.add(
        LaborLedger(
            log_id=log.id,
            contractor_name="General Structural Subcontractor",
            crew_type="Mixed Allocation Site Crew",
            masons_count=payload["manpower_deployed"]["cumulative_masons"],
            helpers_count=payload["manpower_deployed"]["cumulative_helpers"],
            assigned_activity="General Civil Works Execution",
        )
    )

    excel.write_metadata("DPR", "report_date", payload["report_date"])
    excel.write_metadata("DPR", "log_category", payload.get("log_category", ""))
    excel.write_metadata("DPR", "labor_headcount", log.labor_headcount)
    if payload.get("structural_progress_pct") is not None:
        excel.write_metadata("DPR", "structural_progress_pct", payload["structural_progress_pct"])

    row_refs = []
    for entry in payload.get("quantity_entries", []):
        try:
            metric_type = MetricType(entry.get("metric_type", "OTHER"))
        except ValueError:
            metric_type = MetricType.OTHER

        metric = DailyProgressMetric(
            log_id=log.id,
            metric_type=metric_type,
            category=entry.get("work_category", "General"),
            element_id=entry.get("element_id", "unmapped"),
            sub_component="General",
            formula_notation=" + ".join(entry.get("raw_mathematical_dimensions", [])),
            metric_value=entry.get("resolved_value", 0.0),
            unit=entry.get("unit", "unit"),
        )
        db.add(metric)
        db.flush()

        excel_row = excel.append_row(
            "DPR",
            {
                "element_id": metric.element_id,
                "category": metric.category,
                "metric_type": metric_type.value,
                "formula_notation": metric.formula_notation,
                "metric_value": metric.metric_value,
                "unit": metric.unit,
            },
        )
        row_refs.append({"record_table": "daily_progress_metrics", "record_id": metric.id, "excel_row": excel_row})

    return row_refs


def _write_material(db: Session, excel: ExcelWriterService, project_id: int, document_id, payload: dict) -> list:
    row_refs = []
    for entry in payload.get("entries", []):
        ledger_entry = MaterialLedgerEntry(
            material_id=entry["material_id"],
            project_id=project_id,
            report_date=payload["report_date"],
            received_qty=entry.get("received_qty", 0.0),
            consumed_qty=entry.get("consumed_qty", 0.0),
            stock_balance=entry.get("stock_balance", 0.0),
            wastage_qty=entry.get("wastage_qty", 0.0),
            wastage_pct=entry.get("wastage_pct", 0.0),
            source_document_id=document_id,
        )
        db.add(ledger_entry)
        db.flush()

        excel_row = excel.append_row(
            "MATERIAL",
            {
                "material_name": entry["material_name"],
                "unit": entry.get("unit", "unit"),
                "report_date": payload["report_date"],
                "received_qty": ledger_entry.received_qty,
                "design_specified_qty": entry.get("design_specified_qty"),
                "stock_balance": ledger_entry.stock_balance,
                "wastage_qty": ledger_entry.wastage_qty,
                "wastage_pct": ledger_entry.wastage_pct,
            },
        )
        row_refs.append({"record_table": "material_ledger_entries", "record_id": ledger_entry.id, "excel_row": excel_row})

    return row_refs


def _write_billing(db: Session, excel: ExcelWriterService, project_id: int, document_id, payload: dict) -> list:
    remaining = payload.get("po_remaining_balance")
    status = BillingStatus.OVERDUE if (remaining is not None and remaining < 0) else BillingStatus.PENDING

    milestone = BillingMilestone(
        vendor_id=payload["vendor_id"],
        invoice_number=payload.get("invoice_number"),
        invoice_date=payload.get("invoice_date"),
        certified_work_pct=payload.get("certified_work_pct"),
        invoice_amount=payload.get("invoice_amount", 0.0),
        cumulative_billed=payload.get("cumulative_billed", 0.0),
        po_remaining_balance=remaining,
        submitted_date=payload.get("submitted_date"),
        aging_days=payload.get("aging_days"),
        status=status,
        source_document_id=document_id,
    )
    db.add(milestone)
    db.flush()

    excel_row = excel.append_row(
        "BILLING",
        {
            "vendor_name": payload["vendor_name"],
            "po_number": payload.get("po_number"),
            "po_limit": payload.get("po_limit"),
            "invoice_number": payload.get("invoice_number"),
            "invoice_date": payload.get("invoice_date"),
            "certified_work_pct": payload.get("certified_work_pct"),
            "invoice_amount": milestone.invoice_amount,
            "cumulative_billed": milestone.cumulative_billed,
            "po_remaining_balance": remaining,
            "aging_days": milestone.aging_days,
            "status": status.value,
        },
    )
    return [{"record_table": "billing_milestones", "record_id": milestone.id, "excel_row": excel_row}]


def _write_drawing(db: Session, excel: ExcelWriterService, project_id: int, document_id, payload: dict) -> list:
    try:
        signoff = SignoffStatus(payload.get("client_signoff_status", "PENDING"))
    except ValueError:
        signoff = SignoffStatus.PENDING

    drawing = Drawing(
        project_id=project_id,
        drawing_number=payload["drawing_number"],
        drawing_title=payload.get("drawing_title"),
        discipline=payload.get("discipline"),
        gfc_revision=payload.get("gfc_revision"),
        gfc_issue_date=payload.get("gfc_issue_date"),
        client_signoff_status=signoff,
        client_signoff_date=payload.get("client_signoff_date"),
        source_document_id=document_id,
    )
    db.add(drawing)
    db.flush()

    excel_row = excel.append_row(
        "DRAWING",
        {
            "drawing_number": drawing.drawing_number,
            "drawing_title": drawing.drawing_title,
            "discipline": drawing.discipline,
            "gfc_revision": drawing.gfc_revision,
            "gfc_issue_date": drawing.gfc_issue_date,
            "client_signoff_status": signoff.value,
            "client_signoff_date": drawing.client_signoff_date,
        },
    )
    return [{"record_table": "drawings", "record_id": drawing.id, "excel_row": excel_row}]


_WRITERS = {
    "DPR": _write_dpr,
    "MATERIAL": _write_material,
    "BILLING": _write_billing,
    "DRAWING": _write_drawing,
}


def make_excel_writer_node(db: Session):
    def _node(state: IngestState) -> dict:
        document = db.query(ProjectDocument).filter(ProjectDocument.id == state.document_id).first() if state.document_id else None

        if state.error or not state.extracted_payload:
            if document:
                document.ingestion_status = IngestionStatus.FAILED
                db.add(
                    IngestionAuditLog(
                        project_id=state.project_id,
                        document_id=document.id,
                        node_name=NODE_NAME,
                        status="FAILED",
                        message=state.error or "No payload to write.",
                    )
                )
                db.commit()
            return {"audit_trail": state.audit_trail + [f"{NODE_NAME}: skipped (error/no payload)"]}

        writer_fn = _WRITERS.get(state.category)
        excel = ExcelWriterService()
        row_refs = writer_fn(db, excel, state.project_id, state.document_id, state.extracted_payload)

        persisted_exceptions: list[ExceptionDraft] = []
        for exc in state.exceptions:
            target = row_refs[exc.entry_index] if exc.entry_index is not None and exc.entry_index < len(row_refs) else (row_refs[0] if row_refs else None)

            if target and exc.excel_field:
                excel.flag_cell(state.category, target["excel_row"], exc.excel_field, exc.message, severity=exc.severity)

            alert = ExceptionAlert(
                project_id=state.project_id,
                category=ExceptionCategory(exc.category),
                severity=ExceptionSeverity(exc.severity),
                message=exc.message,
                related_table=target["record_table"] if target else exc.related_table,
                related_record_id=target["record_id"] if target else exc.related_record_id,
                source_document_id=state.document_id,
                source_page_number=exc.source_page_number or 1,
                source_text_snippet=exc.source_text_snippet or exc.message,
            )
            db.add(alert)
            persisted_exceptions.append(exc)

        excel.stamp_last_synced(state.category)
        output_filename = f"{state.category}_{state.project_id}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.xlsx"
        output_path = excel.save(output_filename)

        if document:
            document.ingestion_status = IngestionStatus.COMPLETE
            document.page_count = document.page_count or 1
            document.report_date = _resolve_report_date(state.category, state.extracted_payload)
            document.excel_output_path = output_path

        db.add(
            IngestionAuditLog(
                project_id=state.project_id,
                document_id=state.document_id,
                node_name=NODE_NAME,
                status="SUCCESS",
                message=f"Wrote {len(row_refs)} row(s) and {len(persisted_exceptions)} exception(s) to {output_path}.",
            )
        )
        db.commit()

        return {
            "excel_output_path": output_path,
            "audit_trail": state.audit_trail + [f"{NODE_NAME}: saved {output_path}"],
        }

    return _node
