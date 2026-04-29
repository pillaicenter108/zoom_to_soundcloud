import uuid
import threading
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from app.services.sync_service import run_sync
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── In-memory job store ──────────────────────────────────────────────────────
# Structure per job_id:
#   { status: "pending"|"running"|"success"|"error",
#     meetings_fetched: int|None,
#     new_uploads: int|None,
#     logs: list[str],
#     error: str|None }
jobs: dict[str, dict] = {}


class SyncRequest(BaseModel):
    zoom_account: str
    from_date: str
    to_date: str


def _run_job(job_id: str, zoom_account: str, from_date: str, to_date: str):
    """Executed in a background thread. Calls run_sync and stores results."""
    jobs[job_id]["status"] = "running"
    try:
        result = run_sync(zoom_account, from_date, to_date)
        jobs[job_id].update({
            "status": result.get("status", "success"),
            "meetings_fetched": result.get("meetings_fetched"),
            "new_uploads": result.get("new_uploads"),
            "logs": result.get("logs", []),
        })
    except Exception as exc:
        jobs[job_id].update({
            "status": "error",
            "error": str(exc),
        })


@app.post("/sync")
def sync(req: SyncRequest):
    """Start a background sync job and return a job_id immediately."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "meetings_fetched": None,
        "new_uploads": None,
        "logs": [],
        "error": None,
    }
    thread = threading.Thread(
        target=_run_job,
        args=(job_id, req.zoom_account, req.from_date, req.to_date),
        daemon=True,
    )
    thread.start()
    return {"job_id": job_id, "status": "pending"}


@app.get("/status/{job_id}")
def status(job_id: str):
    """Poll this endpoint to get the current state of a sync job."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}