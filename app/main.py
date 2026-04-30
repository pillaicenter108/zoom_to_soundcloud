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

# ── In-memory job store ───────────────────────────────────────────────────────
# logs is a SHARED LIST — sync_service appends to it live, status endpoint
# reads it live. No copy is made until the job finishes.
jobs: dict[str, dict] = {}


class SyncRequest(BaseModel):
    zoom_account: str
    from_date: str
    to_date: str


def _run_job(job_id: str, zoom_account: str, from_date: str, to_date: str):
    """Runs in a background thread. Passes the live logs list into run_sync
    so every append is immediately visible via /status."""
    job = jobs[job_id]
    job["status"] = "running"
    live_logs = job["logs"]          # same list object — mutations are instant

    try:
        result = run_sync(zoom_account, from_date, to_date, live_logs)
        job["status"]           = result.get("status", "success")
        job["meetings_fetched"] = result.get("meetings_fetched")
        job["new_uploads"]      = result.get("new_uploads")
        # live_logs is already up to date — no need to overwrite
    except Exception as exc:
        job["status"] = "error"
        job["error"]  = str(exc)
        live_logs.append(f"❌ Unexpected error: {exc}")


@app.post("/sync")
def sync(req: SyncRequest):
    """Kicks off a background sync and returns a job_id immediately."""
    job_id = str(uuid.uuid4())
    jobs[job_id] = {
        "status": "pending",
        "meetings_fetched": None,
        "new_uploads": None,
        "logs": [],          # live list — shared with the worker thread
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
    """Returns current job state including all logs appended so far."""
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return {"job_id": job_id, **job}