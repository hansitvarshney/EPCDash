from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.database import DailySiteLog, LaborLedger, DailyWorkMetrics
from datetime import datetime, timedelta

class AnalyticsEngine:
    @staticmethod
    def get_project_summary(db: Session, project_id: int):
        """
        Aggregates total quantities executed and total labor force deployed 
        across the entire lifecycle of a specific project.
        """
        # 1. Aggregate Cumulative Work Volumes by Category/Element
        work_totals = (
            db.query(
                DailyWorkMetrics.category,
                DailyWorkMetrics.element_id,
                DailyWorkMetrics.unit,
                func.sum(DailyWorkMetrics.metric_value).label("total_executed")
            )
            .join(DailySiteLog)
            .filter(DailySiteLog.project_id == project_id)
            .group_by(DailyWorkMetrics.category, DailyWorkMetrics.element_id, DailyWorkMetrics.unit)
            .all()
        )

        # 2. Raw query aggregation to make sure variables reader numbers
        total_m = db.query(func.sum(LaborLedger.masons_count)).join(DailySiteLog).filter(DailySiteLog.project_id == project_id).scalar() or 0
        total_h = db.query(func.sum(LaborLedger.helpers_count)).join(DailySiteLog).filter(DailySiteLog.project_id == project_id).scalar() or 0

        # 3. Extract distinct log dates, converting date objects safely to strings
        raw_dates = db.query(DailySiteLog.report_date).filter(DailySiteLog.project_id == project_id).distinct().all()
        active_dates = []
        for d in raw_dates:
            if d[0]:
                date_str = d[0] if isinstance(d[0], str) else d[0].strftime("%Y-%m-%d")
                active_dates.append(date_str)

        return {
            "project_id": project_id,
            "active_log_dates": active_dates,
            "manpower_deployed": {
                "cumulative_masons": int(total_m),
                "cumulative_helpers": int(total_h),
                "total_man_days": int(total_m) + int(total_h)
            },
            "quantities_executed": [
                {
                    "category": w.category,
                    "element_id": w.element_id,
                    "total_output": float(w.total_executed),
                    "unit": w.unit
                }
                for w in work_totals
            ]
        }

    @staticmethod
    def get_velocity_trend(db: Session, project_id: int, days: int = 7):
        """
        Calculates daily progress velocity to build historical trend lines.
        """
        cutoff_date = (datetime.utcnow() - timedelta(days=days)).date()
        
        daily_progress = (
            db.query(
                DailySiteLog.report_date,
                DailyWorkMetrics.category,
                func.sum(DailyWorkMetrics.metric_value).label("daily_volume")
            )
            .join(DailyWorkMetrics, DailySiteLog.id == DailyWorkMetrics.log_id)
            .filter(DailySiteLog.project_id == project_id, DailySiteLog.report_date >= cutoff_date)
            .group_by(DailySiteLog.report_date, DailyWorkMetrics.category)
            .order_by(DailySiteLog.report_date.asc())
            .all()
        )

               # Structure data gracefully for time-series charts
        trend_data = {}
        for row in daily_progress:
            # FIX: Check if it's already a string; if not, format it safely
            date_str = row.report_date if isinstance(row.report_date, str) else row.report_date.strftime("%Y-%m-%d")
            
            if date_str not in trend_data:
                trend_data[date_str] = {}
            trend_data[date_str][row.category] = float(row.daily_volume)

        return trend_data