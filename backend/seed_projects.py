"""
Seeds three demo Active Sites with representative rows across all four
operational ledgers (DPR, Material, Billing, Drawings) plus a handful of
sample exceptions, so the Executive Reaction Center has something
meaningful to render immediately after a clean-slate rebuild.
"""
from datetime import datetime, timedelta

from backend.database import SessionLocal, init_db
from backend.models import (
    Project,
    DailyProgressLog,
    DailyProgressMetric,
    LaborLedger,
    MetricType,
    MaterialMaster,
    MaterialLedgerEntry,
    Vendor,
    BillingMilestone,
    BillingStatus,
    Drawing,
    SignoffStatus,
    ExceptionAlert,
    ExceptionCategory,
    ExceptionSeverity,
)


def _d(days_ago: int) -> str:
    return (datetime.utcnow() - timedelta(days=days_ago)).strftime("%Y-%m-%d")


def seed_active_sites():
    db = SessionLocal()
    try:
        print("Clearing existing demo data...")
        for model in (
            ExceptionAlert,
            BillingMilestone,
            Vendor,
            MaterialLedgerEntry,
            MaterialMaster,
            Drawing,
            DailyProgressMetric,
            LaborLedger,
            DailyProgressLog,
            Project,
        ):
            db.query(model).delete()
        db.commit()

        sites = [
            Project(
                id=1,
                name="Sector 65 Commercial High-Rise Complex",
                location="Sector 65, Gurgaon, Haryana",
                client_name="Sector65 Realty Pvt Ltd",
                contract_value=450_000_000,
                start_date=_d(180),
                target_end_date=(datetime.utcnow() + timedelta(days=350)).strftime("%Y-%m-%d"),
            ),
            Project(
                id=2,
                name="DLF Phase 5 Infrastructure Development",
                location="DLF Phase 5, Gurgaon, Haryana",
                client_name="DLF Limited",
                contract_value=280_000_000,
                start_date=_d(120),
                target_end_date=(datetime.utcnow() + timedelta(days=270)).strftime("%Y-%m-%d"),
            ),
            Project(
                id=3,
                name="Sohna Road Turnkey Industrial Warehouse",
                location="Sohna Road, Gurgaon, Haryana",
                client_name="LogiPark Industries",
                contract_value=150_000_000,
                start_date=_d(60),
                target_end_date=(datetime.utcnow() + timedelta(days=180)).strftime("%Y-%m-%d"),
            ),
        ]
        db.add_all(sites)
        db.commit()

        # ── Site 1: Action Required (has a CRITICAL open exception) ──
        _seed_dpr(db, 1, progress_pct=42.0)
        _seed_material(db, 1, overshoot=True)
        _seed_billing(db, 1, over_po=True)
        _seed_drawings(db, 1, rejected=True)

        # ── Site 2: At Risk (has WARNING-level open exceptions) ──
        _seed_dpr(db, 2, progress_pct=61.0)
        _seed_material(db, 2, overshoot=False)
        _seed_billing(db, 2, over_po=False)
        _seed_drawings(db, 2, rejected=False)
        db.add(
            ExceptionAlert(
                project_id=2,
                category=ExceptionCategory.MATERIAL,
                severity=ExceptionSeverity.WARNING,
                message="Cumulative received quantity for 'TMT Rebar Fe500' exceeds the design-specified allocation.",
                related_table="material_ledger_entries",
                source_page_number=1,
                source_text_snippet="Received: 42,500 kg against design allocation of 40,000 kg.",
            )
        )

        # ── Site 3: On Track (no open exceptions) ──
        _seed_dpr(db, 3, progress_pct=28.0)
        _seed_material(db, 3, overshoot=False)
        _seed_billing(db, 3, over_po=False)
        _seed_drawings(db, 3, rejected=False)

        db.commit()
        print("Successfully seeded 3 demo sites with DPR, Material, Billing, and Drawing ledger data.")

    except Exception as e:
        db.rollback()
        print(f"Error seeding sites: {e}")
        raise
    finally:
        db.close()


def _seed_dpr(db, project_id: int, progress_pct: float):
    for offset, elements in [
        (2, [("SW-4", 9.99, MetricType.SHUTTERING_SQM), ("SW-6", 12.4, MetricType.SHUTTERING_SQM)]),
        (1, [("C-12", 4.2, MetricType.CONCRETE_VOLUME_M3), ("RF-9", 1.8, MetricType.REINFORCEMENT_MT)]),
    ]:
        log = DailyProgressLog(
            project_id=project_id,
            report_date=_d(offset),
            category="GENERAL_CIVIL_WORKS",
            labor_headcount=38,
            structural_progress_pct=progress_pct - offset,
        )
        db.add(log)
        db.flush()
        db.add(
            LaborLedger(
                log_id=log.id,
                contractor_name="General Structural Subcontractor",
                crew_type="Mixed Allocation Site Crew",
                masons_count=15,
                helpers_count=23,
                assigned_activity="General Civil Works Execution",
            )
        )
        for element_id, value, metric_type in elements:
            db.add(
                DailyProgressMetric(
                    log_id=log.id,
                    metric_type=metric_type,
                    category="Shear Wall Shuttering" if metric_type == MetricType.SHUTTERING_SQM else "Structural Concrete",
                    element_id=element_id,
                    metric_value=value,
                    unit="m2" if metric_type == MetricType.SHUTTERING_SQM else ("m3" if metric_type == MetricType.CONCRETE_VOLUME_M3 else "MT"),
                )
            )


def _seed_material(db, project_id: int, overshoot: bool):
    cement = MaterialMaster(project_id=project_id, material_name="OPC 53 Grade Cement", unit="bags", design_specified_qty=5000)
    rebar = MaterialMaster(project_id=project_id, material_name="TMT Rebar Fe500", unit="kg", design_specified_qty=40000)
    db.add_all([cement, rebar])
    db.flush()

    db.add(
        MaterialLedgerEntry(
            material_id=cement.id,
            project_id=project_id,
            report_date=_d(2),
            received_qty=1200,
            consumed_qty=1050,
            stock_balance=150,
            wastage_qty=0,
            wastage_pct=0,
        )
    )
    rebar_received = 42500 if overshoot else 18000
    db.add(
        MaterialLedgerEntry(
            material_id=rebar.id,
            project_id=project_id,
            report_date=_d(1),
            received_qty=rebar_received,
            consumed_qty=17200,
            stock_balance=rebar_received - 17200,
            wastage_qty=0,
            wastage_pct=0,
        )
    )

    if overshoot:
        db.add(
            ExceptionAlert(
                project_id=project_id,
                category=ExceptionCategory.MATERIAL,
                severity=ExceptionSeverity.CRITICAL,
                message="Cumulative received quantity for 'TMT Rebar Fe500' (42,500 kg) exceeds the design-specified allocation (40,000 kg).",
                related_table="material_ledger_entries",
                source_page_number=1,
                source_text_snippet="Received: 42,500 kg against design allocation of 40,000 kg.",
            )
        )


def _seed_billing(db, project_id: int, over_po: bool):
    vendor = Vendor(
        project_id=project_id,
        vendor_name="Shree Balaji Structural Contractors",
        trade="Civil & Structural",
        po_number=f"PO-{2000 + project_id}",
        po_limit=12_000_000,
    )
    db.add(vendor)
    db.flush()

    invoice_amount = 13_500_000 if over_po else 3_200_000
    cumulative_billed = invoice_amount
    milestone = BillingMilestone(
        vendor_id=vendor.id,
        invoice_number=f"INV-{3000 + project_id}",
        invoice_date=_d(5),
        certified_work_pct=32.0,
        invoice_amount=invoice_amount,
        cumulative_billed=cumulative_billed,
        po_remaining_balance=vendor.po_limit - cumulative_billed,
        submitted_date=_d(5),
        aging_days=5,
        status=BillingStatus.OVERDUE if over_po else BillingStatus.PENDING,
    )
    db.add(milestone)

    if over_po:
        db.add(
            ExceptionAlert(
                project_id=project_id,
                category=ExceptionCategory.BILLING,
                severity=ExceptionSeverity.CRITICAL,
                message=f"Invoice amount 13,500,000.00 exceeds vendor '{vendor.vendor_name}' remaining PO allocation of 12,000,000.00.",
                related_table="billing_milestones",
                source_page_number=2,
                source_text_snippet="Total Invoice Amount Due: Rs. 1,35,00,000.00",
            )
        )


def _seed_drawings(db, project_id: int, rejected: bool):
    db.add(
        Drawing(
            project_id=project_id,
            drawing_number=f"STR-{100 + project_id}",
            drawing_title="Shear Wall Reinforcement Detail - Tower A",
            discipline="Structural",
            gfc_revision="Rev C",
            gfc_issue_date=_d(30),
            client_signoff_status=SignoffStatus.REJECTED if rejected else SignoffStatus.APPROVED,
            client_signoff_date=_d(10) if not rejected else None,
        )
    )
    if rejected:
        db.add(
            ExceptionAlert(
                project_id=project_id,
                category=ExceptionCategory.DRAWING,
                severity=ExceptionSeverity.CRITICAL,
                message=f"Drawing 'STR-{100 + project_id}' was REJECTED by the client.",
                related_table="drawings",
                source_page_number=1,
                source_text_snippet="Client Review Comments: Reinforcement congestion at wall junction not addressed. Resubmit.",
            )
        )


if __name__ == "__main__":
    init_db()
    seed_active_sites()
