"""
LLM-drafted correspondence for the WhatsApp reply loop, layered on top of
the milestone unlock event. Uses the same `genai.Client()` /
`gemini-2.5-flash` pattern already established in `graph_query_engine.py`.
"""
from google import genai
from google.genai import types

from backend.models import Project, PaymentMilestone

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = genai.Client()
    return _client


def draft_ra_bill_email(project: Project, bill: PaymentMilestone) -> str:
    """
    Drafts a formal Subject + Body addressed to the client's Executive
    Engineer, citing the completed physical milestone as justification and
    requesting a joint site measurement to certify and clear the named RA
    Bill -- the standard EPC-contracting convention for moving a bill from
    ELIGIBLE to actually INVOICED.
    """
    bill_amount = (project.contract_value or 0.0) * (bill.contract_pct / 100)
    prompt = f"""You are drafting a formal, professional email on behalf of an EPC contractor's project manager to the client's
Executive Engineer, requesting a joint site measurement to certify and clear a contract stage-payment (RA Bill).

Project: {project.name}
Location: {project.location or 'N/A'}
Client: {project.client_name or 'N/A'}
Completed physical milestone justifying this bill: {bill.linked_physical_milestone_name or 'the relevant work stage'}
Bill being requested: {bill.bill_name} ({bill.contract_pct:g}% of the tender value, approx. Rs. {bill_amount:,.0f})

Write a concise, formal email with:
- A clear "Subject:" line on the first line.
- A body that: (1) states the physical milestone above is now 100% complete, (2) requests a joint site measurement
  at the earliest mutual convenience to certify the completed work, and (3) requests certification/clearance of
  {bill.bill_name} following the measurement.
- A professional closing (no need to fill in a specific sender name -- sign off as "Project Manager").

Return ONLY the email text (Subject line + body), no extra commentary."""

    try:
        client = _get_client()
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
            config=types.GenerateContentConfig(temperature=0.3),
        )
        return response.text.strip()
    except Exception as exc:  # noqa: BLE001 - surfaced to the WhatsApp reply
        return (
            f"Subject: Request for Joint Measurement -- {bill.bill_name}\n\n"
            f"(Automatic draft generation failed: {exc}. Please draft manually citing completion of "
            f"'{bill.linked_physical_milestone_name}' and requesting a joint site measurement to clear "
            f"{bill.bill_name}.)"
        )
