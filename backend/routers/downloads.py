import os
import glob
from datetime import datetime

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse

from backend.excel_service.registry import TemplateRegistry

router = APIRouter(prefix="/api/v1/sites", tags=["downloads"])


@router.get("/{site_id}/downloads")
def list_site_downloads(site_id: int):
    """Download Hub: generated tracking sheets for a site with live sync timestamps."""
    config = TemplateRegistry.load()
    output_dir = config.output_dir
    pattern = os.path.join(output_dir, f"*_{site_id}_*.xlsx")

    files = []
    for path in sorted(glob.glob(pattern), key=os.path.getmtime, reverse=True):
        filename = os.path.basename(path)
        category = filename.split("_")[0]
        files.append(
            {
                "file_name": filename,
                "category": category,
                "last_synced_at": datetime.fromtimestamp(os.path.getmtime(path)).strftime("%Y-%m-%d %H:%M UTC"),
                "size_bytes": os.path.getsize(path),
                "download_url": f"/api/v1/sites/{site_id}/downloads/{filename}",
            }
        )
    return files


@router.get("/{site_id}/downloads/{filename}")
def download_site_file(site_id: int, filename: str):
    config = TemplateRegistry.load()
    file_path = os.path.join(config.output_dir, filename)
    if not os.path.exists(file_path) or f"_{site_id}_" not in filename:
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        path=file_path,
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
