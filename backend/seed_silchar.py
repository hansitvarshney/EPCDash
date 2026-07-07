import os
import json
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta

from sqlalchemy.orm import Session
from backend.database import SessionLocal, engine, Base
from backend.models import (
    Project,
    MaterialMaster,
    Vendor,
    ProjectMilestone,
    MilestoneStatus,
    Drawing,
    SignoffStatus,
    PaymentMilestone,
)
from backend.milestone_service import sync_payment_milestone_eligibility

def seed_silchar_project():
    db: Session = SessionLocal()
    try:
        # Create Project
        project_name = "Integrated Deputy Commissioner Office - Silchar"
        project = db.query(Project).filter(Project.name == project_name).first()
        
        if not project:
            start_date = datetime(2024, 1, 1)
            target_end_date = start_date + relativedelta(months=30)
            
            project = Project(
                name=project_name,
                location="Silchar, Cachar, Assam",
                client_name="Government of Assam, Public Works Department (Building)",
                contract_value=414406450.00,
                start_date=start_date.strftime("%Y-%m-%d"),
                target_end_date=target_end_date.strftime("%Y-%m-%d"),
            )
            db.add(project)
            db.commit()
            db.refresh(project)
            print(f"Created project: {project.name} (ID: {project.id})")
        else:
            print(f"Project already exists: {project.name} (ID: {project.id})")
            # We can optionally clear existing data to re-seed, but let's just proceed or skip.
            # For this script, we'll just add the data if it doesn't exist.

        # No real WhatsApp Business account is wired yet (see whatsapp_client.py)
        # and there's no UI for this field -- set directly here for the demo.
        if not project.principal_whatsapp_number:
            project.principal_whatsapp_number = "+919876543210"

        # Seed MaterialMaster
        materials_data = [
            {"name": "TMT Rebar Fe500", "unit": "MT", "qty": 1500.0},
            {"name": "OPC 53 Grade Cement", "unit": "Bags", "qty": 50000.0},
            {"name": "Ready Mix Concrete M30", "unit": "m³", "qty": 10000.0},
            {"name": "Structural Steel", "unit": "MT", "qty": 500.0},
        ]
        
        for mat in materials_data:
            existing = db.query(MaterialMaster).filter(
                MaterialMaster.project_id == project.id,
                MaterialMaster.material_name == mat["name"]
            ).first()
            if not existing:
                db.add(MaterialMaster(
                    project_id=project.id,
                    material_name=mat["name"],
                    unit=mat["unit"],
                    design_specified_qty=mat["qty"]
                ))
        
        # Seed Vendors (Site Financial Ledger)
        vendors_data = [
            {"name": "Structural & Civil Vendor", "trade": "Structural & Civil", "limit": 185000000.0},
            {"name": "MEP & HVAC Vendor", "trade": "MEP & HVAC", "limit": 125000000.0},
            {"name": "Finishing & Façade Vendor", "trade": "Finishing & Façade", "limit": 80000000.0},
        ]
        
        for ven in vendors_data:
            existing = db.query(Vendor).filter(
                Vendor.project_id == project.id,
                Vendor.vendor_name == ven["name"]
            ).first()
            if not existing:
                db.add(Vendor(
                    project_id=project.id,
                    vendor_name=ven["name"],
                    trade=ven["trade"],
                    po_number=f"PO-{ven['trade'][:3].upper()}-001",
                    po_limit=ven["limit"]
                ))

        # Seed Micro-Schedule Milestones -- split into pure PHYSICAL progress
        # stages (Layer A) and their linked contractual RA Bill tranches
        # (Layer B, PaymentMilestone), per the tender's cumulative 25/50/75/
        # 90/100% financial-completion clauses. Each RA Bill's contract_pct
        # is the *incremental* share since the previous stage (25+25+25+15+10
        # = 100%), reactively unlocked when its linked physical stage is
        # marked COMPLETED -- never derived from a raw progress % anymore.
        start_date = datetime.strptime(project.start_date, "%Y-%m-%d")
        milestones_data = [
            {"name": "Planning, Design & Engineering Works", "months": 3},
            {"name": "25% Physical Work Completion", "months": 10},
            {"name": "50% Physical Work Completion", "months": 17},
            {"name": "75% Physical Work Completion", "months": 24},
            {"name": "90% Physical Work Completion", "months": 27},
            {"name": "All civil, electrical & mechanical and horticulture work completed", "months": 30},
        ]

        # One-time rename for sites seeded before this split: the original
        # names doubled as both the physical stage AND the (now-separate)
        # financial-completion clause. Renaming in place preserves each
        # row's id/status (esp. COMPLETED) instead of leaving orphaned
        # duplicates under the old names.
        _LEGACY_NAME_MAP = {
            "25% of Total work in Financial Terms": "25% Physical Work Completion",
            "50% of Total work in Financial Terms": "50% Physical Work Completion",
            "75% of Total work in Financial Terms": "75% Physical Work Completion",
            "90% of Total work in Financial Terms": "90% Physical Work Completion",
        }
        for legacy_name, new_name in _LEGACY_NAME_MAP.items():
            legacy_row = db.query(ProjectMilestone).filter(
                ProjectMilestone.project_id == project.id,
                ProjectMilestone.milestone_name == legacy_name,
            ).first()
            if legacy_row:
                legacy_row.milestone_name = new_name
        db.flush()  # autoflush=False on this session -- make renames visible to the existence checks below

        for idx, ms in enumerate(milestones_data, start=1):
            existing = db.query(ProjectMilestone).filter(
                ProjectMilestone.project_id == project.id,
                ProjectMilestone.milestone_name == ms["name"]
            ).first()
            if not existing:
                target_date = start_date + relativedelta(months=ms["months"])
                # Determine status based on target date vs today
                status = MilestoneStatus.COMPLETED if target_date < datetime.utcnow() else MilestoneStatus.PENDING
                db.add(ProjectMilestone(
                    project_id=project.id,
                    milestone_name=ms["name"],
                    target_date=target_date.strftime("%Y-%m-%d"),
                    status=status,
                    sequence=idx
                ))

        db.commit()

        payment_milestones_data = [
            {"bill_name": "RA Bill #1", "contract_pct": 25.0, "linked": "25% Physical Work Completion", "sequence": 1},
            {"bill_name": "RA Bill #2", "contract_pct": 25.0, "linked": "50% Physical Work Completion", "sequence": 2},
            {"bill_name": "RA Bill #3", "contract_pct": 25.0, "linked": "75% Physical Work Completion", "sequence": 3},
            {"bill_name": "RA Bill #4", "contract_pct": 15.0, "linked": "90% Physical Work Completion", "sequence": 4},
            {
                "bill_name": "Final RA Bill",
                "contract_pct": 10.0,
                "linked": "All civil, electrical & mechanical and horticulture work completed",
                "sequence": 5,
            },
        ]

        for pm in payment_milestones_data:
            existing = db.query(PaymentMilestone).filter(
                PaymentMilestone.project_id == project.id,
                PaymentMilestone.bill_name == pm["bill_name"]
            ).first()
            if not existing:
                db.add(PaymentMilestone(
                    project_id=project.id,
                    bill_name=pm["bill_name"],
                    contract_pct=pm["contract_pct"],
                    linked_physical_milestone_name=pm["linked"],
                    sequence=pm["sequence"],
                ))

        # Seed GFC Drawing Status
        drawings_data = [
            {"number": "STR-FND-001", "title": "Foundation Layout", "discipline": "Structural"},
            {"number": "STR-COL-001", "title": "Column Details", "discipline": "Structural"},
            {"number": "ARC-FLR-001", "title": "Ground Floor Plan", "discipline": "Architectural"},
            {"number": "MEP-HVAC-001", "title": "HVAC Layout", "discipline": "MEP"},
        ]
        
        for drw in drawings_data:
            existing = db.query(Drawing).filter(
                Drawing.project_id == project.id,
                Drawing.drawing_number == drw["number"]
            ).first()
            if not existing:
                db.add(Drawing(
                    project_id=project.id,
                    drawing_number=drw["number"],
                    drawing_title=drw["title"],
                    discipline=drw["discipline"],
                    gfc_revision="R0",
                    gfc_issue_date=project.start_date,
                    client_signoff_status=SignoffStatus.APPROVED,
                    client_signoff_date=project.start_date
                ))

        db.commit()

        sync_payment_milestone_eligibility(db, project.id)
        print("Silchar project successfully seeded.")

    finally:
        db.close()

if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    seed_silchar_project()
