"""
Central re-export surface for every ORM model, so callers can simply do:

    from backend.models import Project, DailyProgressLog, ExceptionAlert, ...

Importing this package is also what registers every table on `Base.metadata`
before `database.init_db()` calls `create_all()`.
"""
from backend.models.project import Project
from backend.models.documents import ProjectDocument, IngestionAuditLog, IngestionStatus
from backend.models.daily_progress import (
    DailyProgressLog,
    DailyProgressMetric,
    LaborLedger,
    MetricType,
)
from backend.models.material_ledger import MaterialMaster, MaterialLedgerEntry
from backend.models.billing import Vendor, BillingMilestone, BillingStatus
from backend.models.drawings import Drawing, SignoffStatus
from backend.models.exceptions import ExceptionAlert, ExceptionCategory, ExceptionSeverity
from backend.models.schedule import ProjectMilestone, MilestoneStatus
from backend.models.expenses import DailyExpenseLog
from backend.models.payment_milestones import PaymentMilestone, PaymentMilestoneStatus
from backend.models.outbound_log import OutboundMessageLog

__all__ = [
    "Project",
    "ProjectDocument",
    "IngestionAuditLog",
    "IngestionStatus",
    "DailyProgressLog",
    "DailyProgressMetric",
    "LaborLedger",
    "MetricType",
    "MaterialMaster",
    "MaterialLedgerEntry",
    "Vendor",
    "BillingMilestone",
    "BillingStatus",
    "Drawing",
    "SignoffStatus",
    "ExceptionAlert",
    "ExceptionCategory",
    "ExceptionSeverity",
    "ProjectMilestone",
    "MilestoneStatus",
    "DailyExpenseLog",
    "PaymentMilestone",
    "PaymentMilestoneStatus",
    "OutboundMessageLog",
]
