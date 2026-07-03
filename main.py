"""
Root-level deployment entrypoint.

Some hosts (Railway/Nixpacks included) auto-detect and/or default to running
a top-level `main.py` for Python services. The real FastAPI app and all of
its wiring lives in `backend/main.py` -- this file simply re-exports that
`app` object so the process can be started as `python main.py` or
`uvicorn main:app` from the repository root, in addition to the existing
`uvicorn backend.main:app` entrypoint used by local dev (`run_backend.sh`).
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.main import app  # noqa: F401,E402

if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=int(os.environ.get("PORT", 8000)))
