"""
Node 3: Validation & Cross-Reference ("The Judge").

Evaluates extracted parameters against historical database thresholds --
e.g. flags an invoice that exceeds its remaining PO allocation, a material
ledger entry that drives stock negative, or any resolved value that lands on
0.00 -- and enriches the payload with the computed fields the Excel Writer
node and DB persistence step need (stock balances, wastage, cumulative
billed, aging, etc).
"""
from datetime import datetime, date
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.models import (
    IngestionAuditLog,
    MaterialMaster,
    MaterialLedgerEntry,
    Vendor,
    BillingMilestone,
)
from backend.workflow.state import IngestState, ExceptionDraft

NODE_NAME = "validation_judge"


def _safe_eval_formula(formula: str) -> float:
    safe_formula = formula.replace("×", "*").replace("X", "*").replace("x", "*").replace(" ", "")
    try:
        return eval(safe_formula, {"__builtins__": None}, {})  # noqa: S307 - sandboxed, arithmetic only
    except Exception:
        return None


def _validate_dpr(db: Session, project_id: int, payload: dict) -> list[ExceptionDraft]:
    exceptions: list[ExceptionDraft] = []
    for idx, entry in enumerate(payload.get("quantity_entries", [])):
        raw_dims = entry.get("raw_mathematical_dimensions", [])
        claimed = entry.get("claimed_subtotals_on_paper", [])
        calculated_total = 0.0
        mismatch = False
        for formula, claimed_val in zip(raw_dims, claimed):
            true_val = _safe_eval_formula(formula)
            if true_val is None:
                continue
            calculated_total += true_val
            if abs(true_val - claimed_val) > 0.05:
                mismatch = True

        claimed_sum = sum(claimed) if claimed else 0.0
        final_total = entry.get("element_final_total_weight")
        resolved_value = final_total if final_total else (claimed_sum if claimed_sum else calculated_total)
        entry["resolved_value"] = resolved_value or 0.0

        if mismatch:
            exceptions.append(
                ExceptionDraft(
                    category="DPR",
                    severity="WARNING",
                    message=f"Row {idx + 1} (element {entry.get('element_id')}): formula math does not match the claimed subtotal on paper.",
                    excel_field="metric_value",
                    entry_index=idx,
                )
            )
        if not resolved_value:
            exceptions.append(
                ExceptionDraft(
                    category="DPR",
                    severity="CRITICAL",
                    message=f"Element {entry.get('element_id')} resolved to 0.00 -- verify source document, value may be unreadable.",
                    excel_field="metric_value",
                    entry_index=idx,
                )
            )
    return exceptions


def _validate_material(db: Session, project_id: int, payload: dict) -> list[ExceptionDraft]:
    exceptions: list[ExceptionDraft] = []
    for idx, entry in enumerate(payload.get("entries", [])):
        material_name = entry["material_name"]
        material = (
            db.query(MaterialMaster)
            .filter(MaterialMaster.project_id == project_id, MaterialMaster.material_name == material_name)
            .first()
        )
        if not material:
            material = MaterialMaster(project_id=project_id, material_name=material_name, unit=entry.get("unit", "unit"), design_specified_qty=0.0)
            db.add(material)
            db.flush()
        entry["material_id"] = material.id
        entry["design_specified_qty"] = material.design_specified_qty

        last_entry = (
            db.query(MaterialLedgerEntry)
            .filter(MaterialLedgerEntry.material_id == material.id)
            .order_by(MaterialLedgerEntry.id.desc())
            .first()
        )
        previous_balance = last_entry.stock_balance if last_entry else 0.0
        received = entry.get("received_qty", 0.0)
        consumed = entry.get("consumed_qty", 0.0)
        new_balance = previous_balance + received - consumed

        wastage_qty = abs(new_balance) if new_balance < 0 else 0.0
        wastage_pct = (wastage_qty / received * 100) if received else 0.0

        entry["stock_balance"] = max(new_balance, 0.0)
        entry["wastage_qty"] = wastage_qty
        entry["wastage_pct"] = round(wastage_pct, 2)

        if new_balance < 0:
            exceptions.append(
                ExceptionDraft(
                    category="MATERIAL",
                    severity="CRITICAL",
                    message=f"'{material_name}' consumption exceeds available stock by {wastage_qty:.2f} {entry.get('unit', '')} -- potential wastage/leakage.",
                    related_table="material_ledger_entries",
                    excel_field="stock_balance",
                    entry_index=idx,
                )
            )

        cumulative_received = (
            db.query(func.sum(MaterialLedgerEntry.received_qty)).filter(MaterialLedgerEntry.material_id == material.id).scalar() or 0.0
        ) + received
        if material.design_specified_qty and cumulative_received > material.design_specified_qty:
            exceptions.append(
                ExceptionDraft(
                    category="MATERIAL",
                    severity="WARNING",
                    message=f"Cumulative received quantity for '{material_name}' ({cumulative_received:.2f}) exceeds the design-specified allocation ({material.design_specified_qty:.2f}).",
                    related_table="material_ledger_entries",
                    excel_field="received_qty",
                    entry_index=idx,
                )
            )
        if received == 0 and consumed == 0:
            exceptions.append(
                ExceptionDraft(
                    category="MATERIAL",
                    severity="WARNING",
                    message=f"'{material_name}' resolved to 0.00 received/consumed -- verify source document.",
                    excel_field="received_qty",
                    entry_index=idx,
                )
            )
    return exceptions


def _validate_billing(db: Session, project_id: int, payload: dict) -> list[ExceptionDraft]:
    exceptions: list[ExceptionDraft] = []
    vendor = (
        db.query(Vendor)
        .filter(Vendor.project_id == project_id, Vendor.vendor_name == payload["vendor_name"])
        .first()
    )
    if not vendor:
        vendor = Vendor(
            project_id=project_id,
            vendor_name=payload["vendor_name"],
            trade=payload.get("trade"),
            po_number=payload.get("po_number"),
            po_limit=payload.get("po_limit") or 0.0,
        )
        db.add(vendor)
        db.flush()
    elif payload.get("po_limit") and not vendor.po_limit:
        vendor.po_limit = payload["po_limit"]

    payload["vendor_id"] = vendor.id

    prior_cumulative = (
        db.query(func.sum(BillingMilestone.invoice_amount)).filter(BillingMilestone.vendor_id == vendor.id).scalar() or 0.0
    )
    invoice_amount = payload.get("invoice_amount", 0.0)
    cumulative_billed = prior_cumulative + invoice_amount
    remaining_balance = (vendor.po_limit - cumulative_billed) if vendor.po_limit else None

    payload["cumulative_billed"] = cumulative_billed
    payload["po_remaining_balance"] = remaining_balance

    aging_days = None
    if payload.get("submitted_date"):
        try:
            submitted = datetime.strptime(payload["submitted_date"], "%Y-%m-%d").date()
            aging_days = (date.today() - submitted).days
        except ValueError:
            aging_days = None
    payload["aging_days"] = aging_days

    if vendor.po_limit and invoice_amount > (vendor.po_limit - prior_cumulative):
        exceptions.append(
            ExceptionDraft(
                category="BILLING",
                severity="CRITICAL",
                message=f"Invoice amount {invoice_amount:,.2f} exceeds vendor '{vendor.vendor_name}' remaining PO allocation of {(vendor.po_limit - prior_cumulative):,.2f}.",
                related_table="billing_milestones",
                excel_field="invoice_amount",
            )
        )
    if invoice_amount == 0.0:
        exceptions.append(
            ExceptionDraft(
                category="BILLING",
                severity="WARNING",
                message=f"Invoice amount for vendor '{vendor.vendor_name}' resolved to 0.00 -- verify source document.",
                excel_field="invoice_amount",
            )
        )
    if aging_days is not None and aging_days > 30:
        exceptions.append(
            ExceptionDraft(
                category="BILLING",
                severity="WARNING",
                message=f"Invoice for vendor '{vendor.vendor_name}' has been outstanding for {aging_days} days (>30 day aging threshold).",
                excel_field="aging_days",
            )
        )
    return exceptions


def _validate_drawing(db: Session, project_id: int, payload: dict) -> list[ExceptionDraft]:
    exceptions: list[ExceptionDraft] = []
    if not payload.get("gfc_revision"):
        exceptions.append(
            ExceptionDraft(
                category="DRAWING",
                severity="WARNING",
                message=f"Drawing '{payload.get('drawing_number')}' is missing a GFC revision code.",
                excel_field="gfc_revision",
            )
        )
    if payload.get("client_signoff_status") == "REJECTED":
        exceptions.append(
            ExceptionDraft(
                category="DRAWING",
                severity="CRITICAL",
                message=f"Drawing '{payload.get('drawing_number')}' was REJECTED by the client.",
                excel_field="client_signoff_status",
            )
        )
    return exceptions


_VALIDATORS = {
    "DPR": _validate_dpr,
    "MATERIAL": _validate_material,
    "BILLING": _validate_billing,
    "DRAWING": _validate_drawing,
}


def make_validation_node(db: Session):
    def _node(state: IngestState) -> dict:
        if state.error or not state.extracted_payload:
            return {"audit_trail": state.audit_trail + [f"{NODE_NAME}: skipped (no payload)"]}

        validator = _VALIDATORS.get(state.category)
        payload = dict(state.extracted_payload)
        exceptions = validator(db, state.project_id, payload) if validator else []

        if state.document_id:
            db.add(
                IngestionAuditLog(
                    project_id=state.project_id,
                    document_id=state.document_id,
                    node_name=NODE_NAME,
                    status="SUCCESS",
                    message=f"Raised {len(exceptions)} exception(s) for category {state.category}.",
                )
            )
            db.flush()

        return {
            "extracted_payload": payload,
            "exceptions": exceptions,
            "audit_trail": state.audit_trail + [f"{NODE_NAME}: {len(exceptions)} exception(s)"],
        }

    return _node
