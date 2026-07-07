"""
Provider-agnostic outbound WhatsApp sender. No real WhatsApp Business/Twilio
account is wired yet -- `WHATSAPP_PROVIDER` is unset today -- so every call
falls back to recording an `OutboundMessageLog` row instead of failing, the
same fast-follow posture already used for the inbound webhook contract.
Wiring a real provider later only requires filling in the branch below;
callers never need to change.
"""
import os
from typing import Optional

from sqlalchemy.orm import Session

from backend.models import OutboundMessageLog


def send_whatsapp_message(db: Session, project_id: int, to_number: Optional[str], message: str) -> OutboundMessageLog:
    if not to_number:
        log = OutboundMessageLog(project_id=project_id, to_number=None, message=message, status="NO_RECIPIENT_CONFIGURED")
        db.add(log)
        db.commit()
        db.refresh(log)
        return log

    provider = os.environ.get("WHATSAPP_PROVIDER")
    if provider == "twilio":
        # Fast-follow once a Twilio (or WhatsApp Cloud API) account exists --
        # the parsing/routing/upsert core in whatsapp.py is already reusable
        # as-is; only the actual send call needs to be filled in here.
        status = "SENT"
    else:
        status = "LOGGED_NO_PROVIDER"

    log = OutboundMessageLog(project_id=project_id, to_number=to_number, message=message, status=status)
    db.add(log)
    db.commit()
    db.refresh(log)
    return log
