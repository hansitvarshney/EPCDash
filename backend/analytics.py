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
    MaterialMaster,
    MaterialLedgerEntry,
    BillingMilestone,
    Vendor,
    Drawing,
    ProjectMilestone,
    MilestoneStatus,
    DailyExpenseLog,
    PaymentMilestone,
    PaymentMilestoneStatus,
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
    def get_contract_timeline(db: Session, project: Project) -> dict:
        """
        Contract Timeline Status: replaces the raw labor-count header stats
        with schedule-anchored facts (start/end dates + elapsed/remaining
        days), reusing the same date-math already proven in
        `get_progress_velocity`'s baseline calculation.
        """
        start_date = project.start_date
        target_end_date = project.target_end_date
        days_elapsed = None
        days_remaining = None
        total_days = None
        pct_elapsed = None
        is_overdue = False

        if start_date and target_end_date:
            try:
                start = datetime.strptime(start_date, "%Y-%m-%d")
                end = datetime.strptime(target_end_date, "%Y-%m-%d")
                today = datetime.utcnow()
                total_days = max((end - start).days, 1)
                days_elapsed = (today - start).days
                days_remaining = (end - today).days
                pct_elapsed = round((min(max(days_elapsed, 0), total_days) / total_days) * 100, 1)
                is_overdue = days_remaining < 0
            except ValueError:
                pass

        return {
            "start_date": start_date,
            "target_end_date": target_end_date,
            "contract_value": project.contract_value,
            "total_days": total_days,
            "days_elapsed": days_elapsed,
            "days_remaining": days_remaining,
            "pct_elapsed": pct_elapsed,
            "is_overdue": is_overdue,
        }

    @staticmethod
    def get_operational_metrics(db: Session, project_id: int) -> dict:
        """
        Two high-value business metrics surfaced alongside the contract
        timeline, computed from data the pipeline already extracts and
        validates -- no new ingestion fields required.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        contract_value = project.contract_value if project else None

        # Tender Invoiced Rate: the principal-facing counterpart to the old
        # subcontracted PO burn rate -- what share of the TOP-LINE tender
        # value has actually crossed into a billable event (INVOICED/PAID)
        # via the PaymentMilestone state machine, not how much has been
        # committed to vendors.
        payment_milestones = db.query(PaymentMilestone).filter(PaymentMilestone.project_id == project_id).all()
        invoiced_pct = sum(
            bill.contract_pct
            for bill in payment_milestones
            if bill.status in (PaymentMilestoneStatus.INVOICED, PaymentMilestoneStatus.PAID)
        )
        invoiced_amount = (contract_value or 0.0) * (invoiced_pct / 100)

        # Uninvoiced Work Value: bills whose linked physical milestone is
        # already COMPLETED (so the PaymentMilestone state machine has
        # unlocked them into ELIGIBLE) but which haven't been invoiced yet
        # -- i.e. work the site has actually earned but not yet formally
        # billed to the client. Direct principal-facing cash-flow signal,
        # more actionable day-to-day than a materials variance count.
        uninvoiced_pct = sum(
            bill.contract_pct for bill in payment_milestones if bill.status == PaymentMilestoneStatus.ELIGIBLE
        )
        uninvoiced_amount = (contract_value or 0.0) * (uninvoiced_pct / 100)

        materials = (
            db.query(MaterialMaster)
            .filter(MaterialMaster.project_id == project_id, MaterialMaster.design_specified_qty > 0)
            .all()
        )
        over_allocated_count = 0
        worst_material_name = None
        worst_variance_pct = None
        for material in materials:
            cumulative_received = (
                db.query(func.sum(MaterialLedgerEntry.received_qty))
                .filter(MaterialLedgerEntry.material_id == material.id)
                .scalar()
                or 0.0
            )
            variance_pct = ((cumulative_received - material.design_specified_qty) / material.design_specified_qty) * 100
            if variance_pct > 0:
                over_allocated_count += 1
                if worst_variance_pct is None or variance_pct > worst_variance_pct:
                    worst_variance_pct = round(variance_pct, 1)
                    worst_material_name = material.material_name

        return {
            "tender_invoiced_rate": {
                "contract_value": contract_value,
                "invoiced_amount": invoiced_amount,
                "invoiced_pct": round(invoiced_pct, 1) if payment_milestones else None,
            },
            "uninvoiced_work_value": {
                "contract_value": contract_value,
                "uninvoiced_amount": uninvoiced_amount,
                "uninvoiced_pct": round(uninvoiced_pct, 1) if payment_milestones else None,
            },
            "material_variance": {
                "materials_over_allocated": over_allocated_count,
                "worst_material_name": worst_material_name,
                "worst_variance_pct": worst_variance_pct,
            },
        }

    @staticmethod
    def get_attendance_sheet(db: Session, project_id: int) -> dict:
        """
        Powers the Site Attendance Sheet: today's structured labor
        breakdown (Tab 1) plus the all-time daily man-day log (Tab 2).
        """
        latest_log_date = (
            db.query(DailyProgressLog.report_date)
            .filter(DailyProgressLog.project_id == project_id)
            .order_by(DailyProgressLog.report_date.desc())
            .first()
        )
        current_date = latest_log_date[0] if latest_log_date else None

        current_day_entries = []
        if current_date:
            rows = (
                db.query(LaborLedger)
                .join(DailyProgressLog)
                .filter(DailyProgressLog.project_id == project_id, DailyProgressLog.report_date == current_date)
                .all()
            )
            current_day_entries = [
                {
                    "contractor_name": row.contractor_name,
                    "crew_type": row.crew_type,
                    "masons_count": row.masons_count,
                    "helpers_count": row.helpers_count,
                    "assigned_activity": row.assigned_activity,
                }
                for row in rows
            ]

        current_day_totals = {
            "masons": sum(e["masons_count"] for e in current_day_entries),
            "helpers": sum(e["helpers_count"] for e in current_day_entries),
        }
        current_day_totals["total"] = current_day_totals["masons"] + current_day_totals["helpers"]

        daily_totals = (
            db.query(
                DailyProgressLog.report_date,
                func.sum(LaborLedger.masons_count).label("masons"),
                func.sum(LaborLedger.helpers_count).label("helpers"),
            )
            .join(LaborLedger, LaborLedger.log_id == DailyProgressLog.id)
            .filter(DailyProgressLog.project_id == project_id)
            .group_by(DailyProgressLog.report_date)
            .order_by(DailyProgressLog.report_date.desc())
            .all()
        )
        historical_daily_totals = [
            {
                "report_date": row.report_date,
                "masons_count": int(row.masons or 0),
                "helpers_count": int(row.helpers or 0),
                "total_man_days": int(row.masons or 0) + int(row.helpers or 0),
            }
            for row in daily_totals
        ]

        return {
            "current_date": current_date,
            "current_day_entries": current_day_entries,
            "current_day_totals": current_day_totals,
            "historical_daily_totals": historical_daily_totals,
        }

    @staticmethod
    def get_attendance_ledger_rows(db: Session, project_id: int) -> list:
        """
        Every historical LaborLedger row joined to its report_date, chronological
        ascending -- used only by the on-demand Excel export so the lighter-weight
        `/attendance` JSON payload (Today tab + chart) doesn't need to carry the
        full lifetime ledger on every poll.
        """
        rows = (
            db.query(
                DailyProgressLog.report_date,
                LaborLedger.contractor_name,
                LaborLedger.crew_type,
                LaborLedger.masons_count,
                LaborLedger.helpers_count,
                LaborLedger.assigned_activity,
            )
            .join(LaborLedger, LaborLedger.log_id == DailyProgressLog.id)
            .filter(DailyProgressLog.project_id == project_id)
            .order_by(DailyProgressLog.report_date.asc())
            .all()
        )
        return [
            {
                "report_date": row.report_date,
                "contractor_name": row.contractor_name,
                "crew_type": row.crew_type,
                "masons_count": row.masons_count,
                "helpers_count": row.helpers_count,
                "assigned_activity": row.assigned_activity,
            }
            for row in rows
        ]

    @staticmethod
    def get_milestone_tracker(db: Session, project_id: int) -> dict:
        """
        Micro-Schedule Milestone Tracker: completed phases + a "Days Left"
        countdown to the next chronological incomplete milestone, flagged
        against the same schedule-baseline-vs-actual comparison already
        computed in `get_progress_velocity()`.
        """
        completed = (
            db.query(ProjectMilestone)
            .filter(ProjectMilestone.project_id == project_id, ProjectMilestone.status == MilestoneStatus.COMPLETED)
            .order_by(ProjectMilestone.sequence.asc())
            .all()
        )
        upcoming = (
            db.query(ProjectMilestone)
            .filter(
                ProjectMilestone.project_id == project_id,
                ProjectMilestone.status == MilestoneStatus.PENDING,
                ProjectMilestone.target_date.isnot(None),
            )
            .order_by(ProjectMilestone.target_date.asc())
            .first()
        )

        next_milestone = None
        if upcoming:
            days_left = None
            try:
                target = datetime.strptime(upcoming.target_date, "%Y-%m-%d")
                days_left = (target - datetime.utcnow()).days
            except (ValueError, TypeError):
                days_left = None
            next_milestone = {
                "milestone_name": upcoming.milestone_name,
                "target_date": upcoming.target_date,
                "days_left": days_left,
            }

        velocity = AnalyticsEngine.get_progress_velocity(db, project_id)
        baseline_pct = velocity["schedule_baseline_pct"]
        actual_pct = velocity["latest_actual_progress_pct"]
        is_lagging_schedule = (
            baseline_pct is not None and actual_pct is not None and actual_pct < baseline_pct
        )

        total_milestones = db.query(func.count(ProjectMilestone.id)).filter(ProjectMilestone.project_id == project_id).scalar() or 0

        all_milestones = (
            db.query(ProjectMilestone)
            .filter(ProjectMilestone.project_id == project_id)
            .order_by(ProjectMilestone.sequence.asc())
            .all()
        )

        project = db.query(Project).filter(Project.id == project_id).first()
        contract_value = project.contract_value if project else None
        payment_milestones = (
            db.query(PaymentMilestone)
            .filter(PaymentMilestone.project_id == project_id)
            .order_by(PaymentMilestone.sequence.asc())
            .all()
        )

        return {
            "completed_milestones": [
                {"milestone_name": m.milestone_name, "target_date": m.target_date, "sequence": m.sequence}
                for m in completed
            ],
            "completed_count": len(completed),
            "total_count": total_milestones,
            "next_milestone": next_milestone,
            "all_milestones": [
                {"id": m.id, "milestone_name": m.milestone_name, "target_date": m.target_date, "status": m.status.value}
                for m in all_milestones
            ],
            "is_lagging_schedule": is_lagging_schedule,
            "schedule_baseline_pct": baseline_pct,
            "latest_actual_progress_pct": actual_pct,
            "payment_milestones": [
                {
                    "id": bill.id,
                    "bill_name": bill.bill_name,
                    "contract_pct": bill.contract_pct,
                    "bill_amount": (contract_value or 0.0) * (bill.contract_pct / 100),
                    "status": bill.status.value,
                    "linked_physical_milestone_name": bill.linked_physical_milestone_name,
                    "eligible_at": bill.eligible_at.isoformat() if bill.eligible_at else None,
                    "invoiced_at": bill.invoiced_at.isoformat() if bill.invoiced_at else None,
                    "paid_at": bill.paid_at.isoformat() if bill.paid_at else None,
                }
                for bill in payment_milestones
            ],
        }

    @staticmethod
    def get_material_velocity(db: Session, project_id: int) -> list:
        """
        Supply-chain health module: for every tracked material, contrasts
        what was consumed yesterday against lifetime consumption, and
        flags over-allocation against the BOQ design-specified quantity.
        Sorted highest-risk (closest to / over 100% of BOQ) first.
        """
        yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y-%m-%d")
        materials = db.query(MaterialMaster).filter(MaterialMaster.project_id == project_id).all()

        rows = []
        for material in materials:
            consumed_yesterday = (
                db.query(func.sum(MaterialLedgerEntry.consumed_qty))
                .filter(MaterialLedgerEntry.material_id == material.id, MaterialLedgerEntry.report_date == yesterday)
                .scalar()
                or 0.0
            )
            consumed_till_now = (
                db.query(func.sum(MaterialLedgerEntry.consumed_qty))
                .filter(MaterialLedgerEntry.material_id == material.id)
                .scalar()
                or 0.0
            )
            pct_of_boq = (
                round((consumed_till_now / material.design_specified_qty) * 100, 1)
                if material.design_specified_qty
                else None
            )
            rows.append(
                {
                    "material_name": material.material_name,
                    "unit": material.unit,
                    "consumed_yesterday": consumed_yesterday,
                    "consumed_till_now": consumed_till_now,
                    "design_specified_qty": material.design_specified_qty,
                    "pct_of_boq": pct_of_boq,
                }
            )

        rows.sort(key=lambda r: (r["pct_of_boq"] is None, -(r["pct_of_boq"] or 0)))
        return rows

    @staticmethod
    def get_latest_billing_activity(db: Session, project_id: int, limit: int = 3) -> list:
        """Live feed of the most recent vendor invoices, with exception-aware status."""
        rows = (
            db.query(BillingMilestone, Vendor)
            .join(Vendor, BillingMilestone.vendor_id == Vendor.id)
            .filter(Vendor.project_id == project_id)
            .order_by(BillingMilestone.id.desc())
            .limit(limit)
            .all()
        )

        results = []
        for milestone, vendor in rows:
            has_open_exception = (
                db.query(ExceptionAlert)
                .filter(
                    ExceptionAlert.project_id == project_id,
                    ExceptionAlert.related_table == "billing_milestones",
                    ExceptionAlert.related_record_id == milestone.id,
                    ExceptionAlert.is_resolved.is_(False),
                )
                .first()
                is not None
            )
            results.append(
                {
                    "vendor_name": vendor.vendor_name,
                    "invoice_number": milestone.invoice_number,
                    "invoice_date": milestone.invoice_date,
                    "invoice_amount": milestone.invoice_amount,
                    "status": "EXCEPTION_FLAGGED" if has_open_exception else milestone.status.value,
                }
            )
        return results

    @staticmethod
    def get_financial_ledger(db: Session, project_id: int) -> dict:
        """
        Capital health block: money invested to date (latest certified
        cumulative billing per vendor) vs. the total committed PO ceiling
        across all vendors -- the most defensible "projected total" figure
        the data actually supports, since `contract_value` doesn't
        decompose into what's been PO'd out yet.

        Also computes a principal-facing Estimated Profit:
            Estimated Profit = Contract Value - (Total Vendor PO Limits
                + Sum of Manually Logged Labor/Misc Day-Expenses
                + Sum of Active (unresolved) Penalties)
        Labor wages and daily site overheads are managed entirely by the
        principal and are NOT derivable from vendor POs or ingested DPRs,
        so they're read from the separately-maintained `DailyExpenseLog`
        table (see `backend/expense_service.py`) rather than computed here.
        """
        project = db.query(Project).filter(Project.id == project_id).first()
        vendors = db.query(Vendor).filter(Vendor.project_id == project_id).all()

        total_invested = 0.0
        total_po_limit = 0.0
        for vendor in vendors:
            total_po_limit += vendor.po_limit or 0.0
            latest_milestone = (
                db.query(BillingMilestone)
                .filter(BillingMilestone.vendor_id == vendor.id)
                .order_by(BillingMilestone.id.desc())
                .first()
            )
            if latest_milestone:
                total_invested += latest_milestone.cumulative_billed or 0.0

        contract_value = project.contract_value if project else None
        pct_of_contract_invested = (
            round((total_invested / contract_value) * 100, 1) if contract_value else None
        )

        total_manual_daily_expenses = (
            db.query(
                func.sum(DailyExpenseLog.labor_wages_paid + DailyExpenseLog.misc_expenses_paid)
            )
            .filter(DailyExpenseLog.project_id == project_id)
            .scalar()
            or 0.0
        )

        total_active_penalties = (
            db.query(func.sum(ExceptionAlert.penalty_amount))
            .filter(
                ExceptionAlert.project_id == project_id,
                ExceptionAlert.is_resolved.is_(False),
                ExceptionAlert.penalty_amount.isnot(None),
            )
            .scalar()
            or 0.0
        )

        estimated_profit = (
            contract_value - (total_po_limit + total_manual_daily_expenses + total_active_penalties)
            if contract_value is not None
            else None
        )

        today_str = datetime.utcnow().strftime("%Y-%m-%d")
        todays_row = (
            db.query(DailyExpenseLog)
            .filter(DailyExpenseLog.project_id == project_id, DailyExpenseLog.report_date == today_str)
            .first()
        )
        todays_expense_log = (
            {
                "report_date": todays_row.report_date,
                "labor_wages_paid": todays_row.labor_wages_paid,
                "misc_expenses_paid": todays_row.misc_expenses_paid,
                "misc_expenses_notes": todays_row.misc_expenses_notes,
                "source": todays_row.source,
            }
            if todays_row
            else None
        )

        return {
            "total_invested_till_now": total_invested,
            "projected_total_to_completion": total_po_limit,
            "contract_value": contract_value,
            "pct_of_contract_invested": pct_of_contract_invested,
            "total_manual_daily_expenses": total_manual_daily_expenses,
            "total_active_penalties": total_active_penalties,
            "estimated_profit": estimated_profit,
            "todays_expense_log": todays_expense_log,
        }

    @staticmethod
    def get_drawing_status_ledger(db: Session, project_id: int, limit: int = 5) -> list:
        """Recent structural layout entries + client sign-off compliance gate."""
        rows = (
            db.query(Drawing)
            .filter(Drawing.project_id == project_id)
            .order_by(Drawing.created_at.desc())
            .limit(limit)
            .all()
        )
        return [
            {
                "drawing_number": d.drawing_number,
                "drawing_title": d.drawing_title,
                "discipline": d.discipline,
                "gfc_revision": d.gfc_revision,
                "gfc_issue_date": d.gfc_issue_date,
                "client_signoff_status": d.client_signoff_status.value,
                "client_signoff_date": d.client_signoff_date,
            }
            for d in rows
        ]

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

        return {
            "id": project.id,
            "name": project.name,
            "location": project.location,
            "client_name": project.client_name,
            "health_status": AnalyticsEngine.get_site_health(db, project.id),
            "open_exceptions": AnalyticsEngine.get_open_exception_counts(db, project.id),
            "last_synced_date": last_log[0] if last_log else None,
            # Portfolio-level headline figure is the true contract/tender
            # top-line value, not the subcontracted PO sum -- consistent
            # with the principal-focused Site Financial Ledger (see
            # FinancialLedger.tsx's "Total Tender Value" stat).
            "total_tender_value": float(project.contract_value) if project.contract_value is not None else 0.0,
        }
