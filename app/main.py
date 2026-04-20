from fastapi import FastAPI
from pydantic import BaseModel
from app.services.sync_service import run_sync
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    # allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class SyncRequest(BaseModel):
    zoom_account: str
    from_date: str
    to_date: str


@app.post("/sync")
def sync(req: SyncRequest):
    result = run_sync(
        req.zoom_account,
        req.from_date,
        req.to_date
    )
    return result