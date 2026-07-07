"""
Provider-agnostic parsing helpers for the WhatsApp cost-declaration
short-circuit (see `backend/routers/whatsapp.py`). Deliberately dependency-
free (no NLP/LLM call) since these are terse, highly-patterned field
messages (e.g. "Silchar labor 42000, misc 8500") -- a couple of regexes are
faster, cheaper, and more predictable than an extraction model here.
"""
import re
from typing import Optional

from sqlalchemy.orm import Session

from backend.models import Project, PaymentMilestone

_LABOR_RE = re.compile(r"labou?r\D{0,10}?([\d,]+(?:\.\d+)?)", re.IGNORECASE)
# Optionally captures a trailing free-text clause as the expense's context,
# e.g. "misc 8500 for diesel and equipment rental" -> notes="diesel and
# equipment rental". Kept as a plain regex (no LLM call) since the "for/-/:"
# separator is a deterministic, highly-patterned convention for this field.
_MISC_RE = re.compile(r"misc\w*\D{0,10}?([\d,]+(?:\.\d+)?)(?:\s*(?:for|-|:)\s*(.+))?", re.IGNORECASE)

_TOKEN_RE = re.compile(r"[A-Za-z0-9]+")
_MIN_TOKEN_LEN = 4
# "Bill" alone matches every RA Bill's name, so a numbered reference (e.g.
# "RA Bill 2", "bill #3") needs its own extraction -- the generic >=4-char
# token filter above drops bare digits.
_BILL_NUMBER_RE = re.compile(r"bill\D{0,3}?(\d+)", re.IGNORECASE)


def _to_float(raw: str) -> float:
    return float(raw.replace(",", ""))


def parse_financial_message(text: str) -> dict:
    """
    Extracts a `labor_wages_paid` / `misc_expenses_paid` pair from free-form
    text. Either or both may be `None` if not mentioned -- callers should
    treat "both None" as "not a financial declaration message at all" (the
    short-circuit trigger condition), and otherwise apply patch semantics
    so a message that only mentions one field doesn't blank out the other.
    """
    labor_match = _LABOR_RE.search(text)
    misc_match = _MISC_RE.search(text)
    notes = misc_match.group(2).strip().rstrip(".") if misc_match and misc_match.group(2) else None
    return {
        "labor_wages_paid": _to_float(labor_match.group(1)) if labor_match else None,
        "misc_expenses_paid": _to_float(misc_match.group(1)) if misc_match else None,
        "misc_expenses_notes": notes,
    }


def resolve_project_from_text(db: Session, text: str) -> Optional[Project]:
    """
    Resolves which site a message refers to by checking whether any
    "significant" token (alnum, length >= 4, to avoid false positives on
    short words like "the"/"misc"/"labor") in the message appears as a
    case-insensitive substring of that project's `name` or `location`
    (e.g. the token "Silchar" matches "Integrated Deputy Commissioner
    Office - Silchar"). Falls back to the single active site when there's
    no ambiguity (useful for single-site pilots where the foreman doesn't
    bother naming the project). Returns `None` when unresolved.
    """
    projects = db.query(Project).all()
    if not projects:
        return None

    tokens = [t.lower() for t in _TOKEN_RE.findall(text) if len(t) >= _MIN_TOKEN_LEN]
    for project in projects:
        haystack = f"{project.name or ''} {project.location or ''}".lower()
        if any(token in haystack for token in tokens):
            return project

    if len(projects) == 1:
        return projects[0]

    return None


def resolve_payment_milestone_from_text(db: Session, project: Project, text: str) -> Optional[PaymentMilestone]:
    """
    Resolves which RA Bill a "draft/email/letter" request refers to, using
    the same token-match approach as `resolve_project_from_text`: any
    significant token in the message matching a substring of the bill's
    `bill_name` or its linked physical milestone's name. Falls back to the
    single most-recently-eligible bill for the project when there's no
    ambiguity (e.g. "draft the RA bill email" with no bill number named).
    """
    bills = db.query(PaymentMilestone).filter(PaymentMilestone.project_id == project.id).all()
    if not bills:
        return None

    number_match = _BILL_NUMBER_RE.search(text)
    if number_match:
        wanted = number_match.group(1)
        for bill in bills:
            bill_number = _BILL_NUMBER_RE.search(bill.bill_name or "")
            if bill_number and bill_number.group(1) == wanted:
                return bill

    tokens = [t.lower() for t in _TOKEN_RE.findall(text) if len(t) >= _MIN_TOKEN_LEN and t.lower() != "bill"]
    for bill in bills:
        haystack = f"{bill.bill_name or ''} {bill.linked_physical_milestone_name or ''}".lower()
        if any(token in haystack for token in tokens):
            return bill

    eligible_bills = [b for b in bills if b.status.value == "ELIGIBLE"]
    if len(eligible_bills) == 1:
        return eligible_bills[0]
    if len(bills) == 1:
        return bills[0]

    return None
