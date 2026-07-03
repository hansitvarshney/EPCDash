from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timedelta

from backend.models import (
    Project,
    DailyProgressLog,
    DailyProgressMetric,
    LaborLedger,
    ExceptionAlert,
    ExceptionSeverity,
    MaterialLedgerEntry,
    BillingMilestone,
    Vendor,
)

ON_TRACK = "ON_TRACK"
AT_RISK = "AT_RISK"
ACTION_REQUIRED = "ACTION_REQUIRED"


class AnalyticsEngine:
    @staticmethod
    def get_project_summary(db: Session, project_id: int):
        """
        Aggregates total quantities executed and total labor force deployed
        across the entire lifecycle of a specific site.
        """
        work_totals = (
            db.query(
                DailyProgressMetric.category,
                DailyProgressMetric.element_id,
                DailyProgressMetric.unit,
                func.sum(DailyProgressMetric.metric_value).label("total_executed"),
            )
            .join(DailyProgressLog)
            .filter(DailyProgressLog.project_id == project_id)
            .group_by(DailyProgressMetric.category, DailyProgressMetric.element_id, DailyProgressMetric.unit)
            .all()
        )

        total_m = db.query(func.sum(LaborLedger.masons_count)).join(DailyProgressLog).filter(DailyProgressLog.project_id == project_id).scalar() or 0
        total_h = db.query(func.sum(LaborLedger.helpers_count)).join(DailyProgressLog).filter(DailyProgressLog.project_id == project_id).scalar() or 0

        raw_dates = db.query(DailyProgressLog.report_date).filter(DailyProgressLog.project_id == project_id).distinct().all()
        active_dates = []
        for d in raw_dates:
            if d[0]:
                date_str = d[0] if isinstance(d[0], str) else d[0].strftime("%Y-%m-%d")
                active_dates.append(date_str)

        return {
            "project_id": project_id,
            "active_log_dates": sorted(active_dates),
            "manpower_deployed": {
                "cumulative_masons": int(total_m),
                "cumulative_helpers": int(total_h),
                "total_man_days": int(total_m) + int(total_h),
            },
            "quantities_executed": [
                {
                    "category": w.category,
                    "element_id": w.element_id,
                    "total_output": float(w.total_executed),
                    "unit": w.unit,
                }
                for w in work_totals
            ],
        }

    @staticmethod
    def get_velocity_trend(db: Session, project_id: int, days: int = 14):
        """Calculates daily progress velocity to build historical trend lines."""
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")

        daily_progress = (
            db.query(
                DailyProgressLog.report_date,
                DailyProgressMetric.category,
                func.sum(DailyProgressMetric.metric_value).label("daily_volume"),
            )
            .join(DailyProgressMetric, DailyProgressLog.id == DailyProgressMetric.log_id)
            .filter(DailyProgressLog.project_id == project_id, DailyProgressLog.report_date >= cutoff_date)
            .group_by(DailyProgressLog.report_date, DailyProgressMetric.category)
            .order_by(DailyProgressLog.report_date.asc())
            .all()
        )

        trend_data = {}
        for row in daily_progress:
            date_str = row.report_date if isinstance(row.report_date, str) else row.report_date.strftime("%Y-%m-%d")
            trend_data.setdefault(date_str, {})[row.category] = float(row.daily_volume)

        return trend_data

    @staticmethod
    def get_progress_velocity(db: Session, project_id: int, days: int = 30):
        """
        Builds the Timeline & Progress Velocity Tracker series: schedule
        baseline completion % vs. actual field-reported structural
        progress %, for the last `days` days of DPR entries.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        baseline_pct = None
        if project and project.start_date and project.target_end_date:
            try:
                start = datetime.strptime(project.start_date, "%Y-%m-%d")
                end = datetime.strptime(project.target_end_date, "%Y-%m-%d")
                today = datetime.utcnow()
                total_days = max((end - start).days, 1)
                elapsed_days = min(max((today - start).days, 0), total_days)
                baseline_pct = round((elapsed_days / total_days) * 100, 1)
            except ValueError:
                baseline_pct = None

        cutoff_date = (datetime.utcnow() - timedelta(days=days)).strftime("%Y-%m-%d")
        logs = (
            db.query(DailyProgressLog.report_date, DailyProgressLog.structural_progress_pct)
            .filter(
                DailyProgressLog.project_id == project_id,
                DailyProgressLog.report_date >= cutoff_date,
                DailyProgressLog.structural_progress_pct.isnot(None),
            )
            .order_by(DailyProgressLog.report_date.asc())
            .all()
        )

        series = [
            {"report_date": row.report_date, "actual_progress_pct": row.structural_progress_pct}
            for row in logs
        ]
        latest_actual_pct = series[-1]["actual_progress_pct"] if series else None

        return {
            "project_id": project_id,
            "schedule_baseline_pct": baseline_pct,
            "latest_actual_progress_pct": latest_actual_pct,
            "series": series,
        }

    @staticmethod
    def get_site_health(db: Session, project_id: int) -> str:
        """
        Computes On Track / At Risk / Action Required live from open
        ExceptionAlert severities, so the health badge can never drift
        out of sync with the underlying ledgers.
        """
        open_alerts = (
            db.query(ExceptionAlert.severity, func.count(ExceptionAlert.id))
            .filter(ExceptionAlert.project_id == project_id, ExceptionAlert.is_resolved.is_(False))
            .group_by(ExceptionAlert.severity)
            .all()
        )
        counts = {severity: count for severity, count in open_alerts}

        critical_count = counts.get(ExceptionSeverity.CRITICAL, 0)
        warning_count = counts.get(ExceptionSeverity.WARNING, 0)

        if critical_count > 0:
            return ACTION_REQUIRED
        if warning_count > 0:
            return AT_RISK
        return ON_TRACK

    @staticmethod
    def get_open_exception_counts(db: Session, project_id: int) -> dict:
        open_alerts = (
            db.query(ExceptionAlert.severity, func.count(ExceptionAlert.id))
            .filter(ExceptionAlert.project_id == project_id, ExceptionAlert.is_resolved.is_(False))
            .group_by(ExceptionAlert.severity)
            .all()
        )
        counts = {severity.value: count for severity, count in open_alerts}
        return {
            "critical": counts.get("CRITICAL", 0),
            "warning": counts.get("WARNING", 0),
            "info": counts.get("INFO", 0),
        }

    @staticmethod
    def get_site_card_summary(db: Session, project: Project) -> dict:
        """Compact summary used by the landing page's Active Site gallery cards."""
        last_log = (
            db.query(DailyProgressLog.report_date)
            .filter(DailyProgressLog.project_id == project.id)
            .order_by(DailyProgressLog.report_date.desc())
            .first()
        )
        open_po_value = db.query(func.sum(Vendor.po_limit)).filter(Vendor.project_id == project.id).scalar() or 0

        return {
            "id": project.id,
            "name": project.name,
            "location": project.location,
            "client_name": project.client_name,
            "health_status": AnalyticsEngine.get_site_health(db, project.id),
            "open_exceptions": AnalyticsEngine.get_open_exception_counts(db, project.id),
            "last_synced_date": last_log[0] if last_log else None,
            "total_po_value": float(open_po_value),
        }
