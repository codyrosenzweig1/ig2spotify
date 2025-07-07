# Backend/app/main.py
import uuid

from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from spotify_integration.csv_reader import read_history
from pydantic import BaseModel
from backend.progress import PROGRESS_DATA

# import existing automation functions
from backend.full_pipeline import run_full_pipeline

# In memory store of run parameters (lives until restart uvicorn)
run_metadata: dict[str, dict] = {}

# For type-safety in request bodies
class RunRequest(BaseModel):
    instagram_username: str
    playlist_name: str 
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
    runId = uuid.uuid4().hex

    # 2 store the run parameters in memory
    PROGRESS_DATA[runId] = {
        "reels_downloaded": 0,
        "audio_converted": 0,
        "track_recognition_processed": 0,
        "tracks_matched": 0,
        "playlist_done": False,
        "instagram_username": req.instagram_username,
        "playlist_name": req.playlist_name or "ig2spotify",
        "limit": req.limit,
        'runId': runId,
    }

    # RUn full_pipeline, returns nothing
    bg.add_task(run_full_pipeline, 
                req.instagram_username, 
                req.playlist_name, 
                req.limit,
                runId=runId)
    return {"message": "Pipeline started", "runId": runId}

@app.get("/api/runs/{runId}/status")
async def get_run_status(runId: str):
    """
    Return progress for a given run ID.
    """
    # Look up the stored run parameters
    if PROGRESS_DATA:
        # If run_metadata is empty, we can skip this check
        meta = PROGRESS_DATA.get(runId)
        if not meta:
            raise HTTPException(status_code=404, detail="Run ID not found")

    total_expected = meta["limit"]

    # Load all history for this run

    df = read_history("recognition_history.csv") # read the master history log
    df_run = df[df['run_id'] == runId] # Filter down to just this run
    processed = len(df_run)


    # Return JSON with everything the front end needs
    return PROGRESS_DATA[runId] | {}