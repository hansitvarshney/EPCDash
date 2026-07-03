"""
Structured-output Pydantic schemas for the Extraction Node — one per
ingestion category (DPR / MATERIAL / BILLING / DRAWING). These are passed
directly to Gemini's `response_schema` for guaranteed-shape JSON output,
following the same pattern already proven in `backend/parser_agent.py`.
"""
from typing import List, Optional
from pydantic import BaseModel, Field, field_validator

from backend.workflow.coercion import coerce_numeric_string

# ─────────────────────────────────────────────────────────────
# DPR — Daily Progress Log
# ─────────────────────────────────────────────────────────────


class DPRQuantityEntry(BaseModel):
    work_category: str = Field(description="Executive title for the work, e.g. 'Shear Wall Shuttering'.")
    element_id: str = Field(description="The structural tracking node code (e.g. 'SW-4', 'C-12').")
    metric_type: str = Field(
        default="OTHER",
        description="One of CONCRETE_VOLUME_M3, REINFORCEMENT_MT, SHUTTERING_SQM, OTHER — classify the quantity type.",
    )
    raw_mathematical_dimensions: List[str] = Field(default_factory=list, description="Raw multi-line calculation text as written.")
    claimed_subtotals_on_paper: List[float] = Field(default_factory=list, description="Per-row written subtotal values, if present.")
    element_final_total_weight: Optional[float] = Field(default=None, description="Single closing total figure, if the sheet shows one consolidated total instead of per-row subtotals.")
    unit: str = Field(default="unit")

    @field_validator("claimed_subtotals_on_paper", mode="before")
    @classmethod
    def _sanitize_subtotals(cls, values):
        if not isinstance(values, list):
            return values
        cleaned = []
        for v in values:
            coerced = coerce_numeric_string(v)
            if coerced is not None:
                cleaned.append(coerced)
        return cleaned

    @field_validator("element_final_total_weight", mode="before")
    @classmethod
    def _sanitize_total(cls, value):
        if value in (None, ""):
            return None
        return coerce_numeric_string(value)


class DPRManpower(BaseModel):
    cumulative_masons: int = Field(default=0)
    cumulative_helpers: int = Field(default=0)


class DPRExtraction(BaseModel):
    report_date: str = Field(description="Report date, strictly formatted 'YYYY-MM-DD'.")
    log_category: str = Field(default="GENERAL_CIVIL_WORKS")
    manpower_deployed: DPRManpower = Field(default_factory=DPRManpower)
    structural_progress_pct: Optional[float] = Field(default=None, description="Overall structural completion % noted on the sheet, if present.")
    quantity_entries: List[DPRQuantityEntry] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# MATERIAL — Master Material & Inventory Ledger
# ─────────────────────────────────────────────────────────────


class MaterialEntry(BaseModel):
    material_name: str = Field(description="Material name exactly as written, e.g. 'TMT Rebar Fe500', 'OPC 53 Cement'.")
    unit: str = Field(default="unit")
    received_qty: float = Field(default=0.0)
    consumed_qty: float = Field(default=0.0)

    @field_validator("received_qty", "consumed_qty", mode="before")
    @classmethod
    def _sanitize(cls, value):
        coerced = coerce_numeric_string(value)
        return coerced if coerced is not None else 0.0


class MaterialExtraction(BaseModel):
    report_date: str = Field(description="Report date, strictly formatted 'YYYY-MM-DD'.")
    entries: List[MaterialEntry] = Field(default_factory=list)


# ─────────────────────────────────────────────────────────────
# BILLING — Vendor Billing & Milestone Tracker
# ─────────────────────────────────────────────────────────────


class BillingExtraction(BaseModel):
    vendor_name: str
    trade: Optional[str] = Field(default=None)
    po_number: Optional[str] = Field(default=None)
    po_limit: Optional[float] = Field(default=None, description="Total sanctioned PO value for this vendor, if stated on the document.")
    invoice_number: Optional[str] = Field(default=None)
    invoice_date: Optional[str] = Field(default=None, description="'YYYY-MM-DD' if determinable.")
    certified_work_pct: Optional[float] = Field(default=None)
    invoice_amount: float = Field(default=0.0)
    submitted_date: Optional[str] = Field(default=None)

    @field_validator("po_limit", "certified_work_pct", mode="before")
    @classmethod
    def _sanitize_optional(cls, value):
        if value in (None, ""):
            return None
        return coerce_numeric_string(value)

    @field_validator("invoice_amount", mode="before")
    @classmethod
    def _sanitize_amount(cls, value):
        coerced = coerce_numeric_string(value)
        return coerced if coerced is not None else 0.0


# ─────────────────────────────────────────────────────────────
# DRAWING — EPC Regulatory & Drawing Log
# ─────────────────────────────────────────────────────────────


class DrawingExtraction(BaseModel):
    drawing_number: str
    drawing_title: Optional[str] = Field(default=None)
    discipline: Optional[str] = Field(default=None, description="e.g. Structural, Architectural, MEP.")
    gfc_revision: Optional[str] = Field(default=None, description="Good-for-Construction revision code, e.g. 'Rev C'.")
    gfc_issue_date: Optional[str] = Field(default=None)
    client_signoff_status: str = Field(default="PENDING", description="One of PENDING, APPROVED, REJECTED.")
    client_signoff_date: Optional[str] = Field(default=None)


CATEGORY_SCHEMAS = {
    "DPR": DPRExtraction,
    "MATERIAL": MaterialExtraction,
    "BILLING": BillingExtraction,
    "DRAWING": DrawingExtraction,
}

CATEGORY_PROMPTS = {
    "DPR": (
        "You are an expert construction data-compiler agent. Extract this Daily Progress Report (DPR) sheet. "
        "Locate the master report date, cumulative manpower (masons/helpers), overall structural progress % if "
        "stated, and every quantity line item with its element ID, work category, metric_type classification "
        "(CONCRETE_VOLUME_M3 / REINFORCEMENT_MT / SHUTTERING_SQM / OTHER), raw formula text, and either per-row "
        "subtotals or one consolidated closing total. Never guess a value you cannot read -- omit it instead."
    ),
    "MATERIAL": (
        "You are an expert construction inventory auditor. Extract this material receipt/consumption sheet: the "
        "report date, and for every material line its name, unit, received quantity, and consumed quantity. "
        "Never guess a value of 0 for a quantity you cannot actually read -- omit that entry field instead."
    ),
    "BILLING": (
        "You are an expert EPC billing auditor. Extract this vendor invoice / milestone certificate: vendor name, "
        "trade, PO number, PO limit if stated, invoice number, invoice date, certified work percentage, invoice "
        "amount, and submission date."
    ),
    "DRAWING": (
        "You are an expert EPC document controller. Extract this drawing register / transmittal entry: drawing "
        "number, title, discipline, GFC (Good-for-Construction) revision code, GFC issue date, client sign-off "
        "status (PENDING/APPROVED/REJECTED), and sign-off date if present."
    ),
}
