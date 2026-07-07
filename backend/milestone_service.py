"""
Reactive unlock engine bridging Layer A (physical `ProjectMilestone` rows)
and Layer B (contractual `PaymentMilestone` / RA Bill rows). There is no
cron/poll -- this is invoked synchronously right after anything that could
change a physical milestone's status: a Schedule Excel re-upload
(`_write_schedule`) or a manual toggle (`PATCH /sites/{id}/milestones/{id}`).
"""
from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from backend.models import (
    Project,
    ProjectMilestone,
    MilestoneStatus,
    PaymentMilestone,
    PaymentMilestoneStatus,
    ExceptionAlert,
    ExceptionCategory,
    ExceptionSeverity,
)
from backend.whatsapp_client import send_whatsapp_message


def sync_payment_milestone_eligibility(db: Session, project_id: int) -> List[PaymentMilestone]:
    """
    Resolves each PaymentMilestone's linked physical milestone by NAME
    (never by id -- physical rows are fully replaced on every Schedule
    Excel re-upload, so ids churn) and applies exactly one of three
    transitions:

      LOCKED   -> ELIGIBLE  when the linked physical milestone is COMPLETED.
      ELIGIBLE -> LOCKED    when the linked physical milestone reverts to
                            PENDING (safe -- no financial action taken yet).
      INVOICED/PAID + linked physical milestone reverted to PENDING ->
                            refused; raises a CRITICAL ExceptionAlert for
                            manual reconciliation instead of silently
                            undoing a real-world billing action.

    Returns the list of bills that just transitioned to ELIGIBLE in this
    call, so the caller can fire a WhatsApp alert for each exactly once.
    """
    physical_status = {
        m.milestone_name: m.status
        for m in db.query(ProjectMilestone).filter(ProjectMilestone.project_id == project_id)
    }

    newly_eligible: List[PaymentMilestone] = []
    bills = db.query(PaymentMilestone).filter(PaymentMilestone.project_id == project_id).all()

    for bill in bills:
        linked_status = physical_status.get(bill.linked_physical_milestone_name)
        is_complete = linked_status == MilestoneStatus.COMPLETED

        if bill.status == PaymentMilestoneStatus.LOCKED and is_complete:
            bill.status = PaymentMilestoneStatus.ELIGIBLE
            bill.eligible_at = datetime.utcnow()
            newly_eligible.append(bill)

        elif bill.status == PaymentMilestoneStatus.ELIGIBLE and not is_complete:
            bill.status = PaymentMilestoneStatus.LOCKED
            bill.eligible_at = None

        elif bill.status in (PaymentMilestoneStatus.INVOICED, PaymentMilestoneStatus.PAID) and not is_complete:
            already_flagged = (
                db.query(ExceptionAlert)
                .filter(
                    ExceptionAlert.project_id == project_id,
                    ExceptionAlert.related_table == "payment_milestones",
                    ExceptionAlert.related_record_id == bill.id,
                    ExceptionAlert.is_resolved.is_(False),
                )
                .first()
            )
            if not already_flagged:
                db.add(
                    ExceptionAlert(
                        project_id=project_id,
                        category=ExceptionCategory.SCHEDULE,
                        severity=ExceptionSeverity.CRITICAL,
                        message=(
                            f"'{bill.bill_name}' is already {bill.status.value} but its linked physical "
                            f"milestone '{bill.linked_physical_milestone_name}' was reverted to PENDING -- "
                            f"reconcile manually."
                        ),
                        related_table="payment_milestones",
                        related_record_id=bill.id,
                    )
                )

    db.commit()
    for bill in newly_eligible:
        db.refresh(bill)
    return newly_eligible


def notify_payment_milestone_eligible(db: Session, project_id: int, bill: PaymentMilestone) -> None:
    """
    Fires the outbound WhatsApp alert for a bill that just became ELIGIBLE.
    Guarded by `whatsapp_alert_sent_at` so it only ever fires once per
    transition, no matter how many times `sync_payment_milestone_eligibility`
    is re-run (e.g. a Schedule re-upload followed by a manual toggle on the
    same day).
    """
    if bill.whatsapp_alert_sent_at:
        return
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        return
    bill_amount = (project.contract_value or 0.0) * (bill.contract_pct / 100)
    message = (
        f"{project.name} {bill.linked_physical_milestone_name} is 100% complete. You are now eligible to "
        f"issue {bill.bill_name} for {bill.contract_pct:g}% of the tender value (Rs. {bill_amount:,.0f})."
    )
    send_whatsapp_message(db, project_id, project.principal_whatsapp_number, message)
    bill.whatsapp_alert_sent_at = datetime.utcnow()
    db.commit()
