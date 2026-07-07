from datetime import datetime
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime

from backend.database import Base


class OutboundMessageLog(Base):
    """
    Audit record of every outbound WhatsApp message the backend attempted
    to send (milestone-eligibility alerts, drafted RA Bill emails). No real
    WhatsApp Business/Twilio account is wired yet, so `status` is almost
    always "LOGGED_NO_PROVIDER"/"NO_RECIPIENT_CONFIGURED" today -- this
    table is what lets the dashboard show "what would have gone out"
    without a live provider, and becomes a real send-audit log once one is
    configured (see `backend/whatsapp_client.py`).
    """
    __tablename__ = "outbound_message_logs"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    to_number = Column(String, nullable=True)
    message = Column(String, nullable=False)
    status = Column(String, nullable=False)  # "SENT" | "LOGGED_NO_PROVIDER" | "NO_RECIPIENT_CONFIGURED"
    created_at = Column(DateTime, default=datetime.utcnow)
