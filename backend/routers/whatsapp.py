"""
WhatsApp text short-circuit: lets a principal/foreman fire off a terse
message like "Silchar labor 42000, misc 8500" and have it upsert directly
into that project's Daily Expense Log, bypassing the LangGraph document
pipeline entirely (there's no document/image here to extract from).

The JSON body below (`from_number` / `message`) is a provider-agnostic
contract. Wiring the exact field names of a specific chosen provider (e.g.
Twilio's form-encoded `From`/`Body`, or the WhatsApp Cloud API's nested
JSON envelope) is a fast-follow once a provider is selected -- the
parsing/routing/upsert core here is reusable either way.
"""
from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.expense_service import upsert_daily_expense
from backend.whatsapp_parser import (
    parse_financial_message,
    resolve_project_from_text,
    resolve_payment_milestone_from_text,
)
from backend.whatsapp_llm import draft_ra_bill_email
from backend.whatsapp_client import send_whatsapp_message

router = APIRouter(prefix="/api/v1/ingest", tags=["whatsapp"])

_DRAFT_INTENT_KEYWORDS = ("draft", "email", "letter")


class WhatsAppInboundMessage(BaseModel):
    from_number: Optional[str] = None
    message: str


def _handle_draft_request(db: Session, payload: WhatsAppInboundMessage) -> dict:
    """
    Second short-circuit intent, checked only after the (cheap, deterministic)
    financial-declaration regex finds nothing: a message like "draft the RA
    Bill 3 email" or "send the letter for RA Bill #2" resolves to a specific
    PaymentMilestone, drafts a formal request-for-joint-measurement email via
    Gemini, and routes the drafted text back to the sender over WhatsApp
    (logged, since no real provider is configured yet).
    """
    project = resolve_project_from_text(db, payload.message)
    if not project:
        return {
            "status": "error",
            "reason": "Could not resolve a project from the message. Mention the site name explicitly.",
        }

    bill = resolve_payment_milestone_from_text(db, project, payload.message)
    if not bill:
        return {
            "status": "error",
            "reason": "Could not resolve which RA Bill / payment milestone this refers to. Mention the bill name explicitly.",
        }

    drafted_email = draft_ra_bill_email(project, bill)
    send_whatsapp_message(db, project.id, payload.from_number, drafted_email)

    return {
        "status": "success",
        "intent": "draft_email",
        "project_id": project.id,
        "project_name": project.name,
        "bill_name": bill.bill_name,
        "drafted_email": drafted_email,
    }


@router.post("/whatsapp")
def receive_whatsapp_message(payload: WhatsAppInboundMessage, db: Session = Depends(get_db)):
    """
    Always returns HTTP 200 (even on "ignored"/"error" outcomes) since
    WhatsApp/webhook providers typically retry non-2xx responses -- the
    `status` field in the body communicates the actual outcome.
    """
    parsed = parse_financial_message(payload.message)
    if parsed["labor_wages_paid"] is None and parsed["misc_expenses_paid"] is None:
        lowered = payload.message.lower()
        if any(keyword in lowered for keyword in _DRAFT_INTENT_KEYWORDS):
            return _handle_draft_request(db, payload)
        return {"status": "ignored", "reason": "No financial declaration pattern recognized."}

    project = resolve_project_from_text(db, payload.message)
    if not project:
        return {
            "status": "error",
            "reason": "Could not resolve a project from the message. Mention the site name explicitly.",
        }

    row = upsert_daily_expense(
        db,
        project.id,
        report_date=None,
        labor_wages_paid=parsed["labor_wages_paid"],
        misc_expenses_paid=parsed["misc_expenses_paid"],
        misc_expenses_notes=parsed.get("misc_expenses_notes"),
        source="WHATSAPP",
    )
    return {
        "status": "success",
        "project_id": project.id,
        "project_name": project.name,
        "report_date": row.report_date,
        "labor_wages_paid": row.labor_wages_paid,
        "misc_expenses_paid": row.misc_expenses_paid,
        "misc_expenses_notes": row.misc_expenses_notes,
        "source": row.source,
    }
