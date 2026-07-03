from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.database import get_db
from backend.models import Project
from backend.analytics import AnalyticsEngine

router = APIRouter(prefix="/api/v1/sites", tags=["sites"])


@router.get("")
def list_active_sites(db: Session = Depends(get_db)):
    """Landing page gallery: Active Site cards with health indicators."""
    sites = db.query(Project).order_by(Project.id.asc()).all()
    return [AnalyticsEngine.get_site_card_summary(db, site) for site in sites]


@router.get("/{site_id}")
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")
    return {
        "id": site.id,
        "name": site.name,
        "location": site.location,
        "client_name": site.client_name,
        "contract_value": site.contract_value,
        "start_date": site.start_date,
        "target_end_date": site.target_end_date,
        "health_status": AnalyticsEngine.get_site_health(db, site.id),
    }


@router.get("/{site_id}/overview")
def get_site_overview(site_id: int, db: Session = Depends(get_db)):
    """Powers the Site Detail page: KPI summary + Timeline & Velocity tracker data."""
    site = db.query(Project).filter(Project.id == site_id).first()
    if not site:
        raise HTTPException(status_code=404, detail="Site not found")

    return {
        "site": {
            "id": site.id,
            "name": site.name,
            "location": site.location,
            "client_name": site.client_name,
            "health_status": AnalyticsEngine.get_site_health(db, site.id),
        },
        "summary": AnalyticsEngine.get_project_summary(db, site_id),
        "velocity": AnalyticsEngine.get_progress_velocity(db, site_id),
        "open_exceptions": AnalyticsEngine.get_open_exception_counts(db, site_id),
    }
