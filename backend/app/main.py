# Backend/app/main.py
import uuid

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from spotify_integration.csv_reader import read_history
from pydantic import BaseModel

# import existing automation functions
from backend.full_pipeline import run_full_pipeline

# In memory store of run parameters (lives until restart uvicorn)
run_metadata: dict[str, dict] = {}

# For type-safety in request bodies
class RunRequest(BaseModel):
    instagram_username: str
    playlist_name: str | None = None
    limit : int = 10 # Optional limit for reels to process, default is 10

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://127.0.1:3000",
                   ],  # Adjust this to your frontend URL in production
    allow_methods=["*"],
    allow_headers=["*"],
    allow_credentials=True,
)

@app.post("/api/run")
async def start_run(req: RunRequest, bg: BackgroundTasks):
    """
    Kick off the full automation pipeline in the background.
    Returns an immediate response to the client to state the task has begun.
    """
    # Generate a unique run ID
    run_id = uuid.uuid4().hex

    # 2 store the run parameters in memory
    run_metadata[run_id] = {
        "instagram_username": req.instagram_username,
        "playlist_name": req.playlist_name or "ig2spotify",
        "limit": req.limit,
    }

    # RUn full_pipeline, returns nothing
    bg.add_task(run_full_pipeline, 
                req.instagram_username, 
                req.playlist_name, 
                req.limit,
                run_id=run_id)
    return {"message": "Pipeline started", "run_id": run_id}

@app.get("/api/runs/{run_id}/status")
async def get_run_status(run_id: str, req: RunRequest):
    """
    Return progress for a given run ID.
    """
    # Look up the stored run parameters
    if run_metadata:
        # If run_metadata is empty, we can skip this check
        meta = run_metadata.get(run_id)
        if not meta:
            raise HTTPException(status_code=404, detail="Run ID not found")

    total_expected = meta["limit"]

    # Load all history for this run

    df = read_history("recognition_history.csv") # read the master history log
    df_run = df[df['run_id'] == run_id] # Filter down to just this run
    processed = len(df_run)

    # Return JSON with everything the front end needs
    return {
        "run_id": run_id,
        "processed": processed,
        "total": total_expected, 
        "records": df_run.to_dict(orient='records'),
    }