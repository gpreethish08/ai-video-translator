"""
FastAPI Server for AI Video Translator
Provides REST API endpoints for video upload, URL processing, translation progress polling,
preview streaming, and output video download.
"""

import os
import sys
import uuid
import shutil
import logging
from pathlib import Path
from typing import Optional
from pydantic import BaseModel

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from fastapi import FastAPI, UploadFile, File, Form, BackgroundTasks, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from backend.config import UPLOAD_DIR, OUTPUT_DIR, SUPPORTED_LANGUAGES
from database.db_manager import db
from backend.pipeline.orchestrator import TranslationOrchestrator

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("ai_video_translator.api")

app = FastAPI(
    title="AI Video Translator API",
    description="Translates videos up to 40 minutes into all global languages with speaker gender detection and lip-sync synchronization.",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

orchestrator = TranslationOrchestrator()


class UrlTranslationRequest(BaseModel):
    url: str
    target_lang: str
    source_lang: Optional[str] = "auto"
    gender_override: Optional[str] = "auto"
    lip_sync_enabled: Optional[bool] = True
    fast_parallel_mode: Optional[bool] = True


def run_translation_background(job_id: str):
    """Background task worker to run orchestrator pipeline."""
    try:
        logger.info("Starting background translation worker for job: %s", job_id)
        orchestrator.process_job(job_id)
        logger.info("Successfully finished translation job: %s", job_id)
    except Exception as e:
        logger.error("Job %s execution failed: %s", job_id, e)


@app.get("/api/languages")
def get_languages():
    """Returns catalog of supported languages and their details."""
    languages = []
    for code, info in SUPPORTED_LANGUAGES.items():
        languages.append({
            "code": code,
            "name": info["name"],
            "male_voice": info["male_voice"],
            "female_voice": info["female_voice"]
        })
    return {"status": "success", "languages": languages}


@app.post("/api/translate/file")
async def translate_video_file(
    background_tasks: BackgroundTasks,
    video: UploadFile = File(...),
    target_lang: str = Form(...),
    source_lang: str = Form("auto"),
    gender_override: str = Form("auto"),
    lip_sync_enabled: bool = Form(True),
    fast_parallel_mode: bool = Form(True)
):
    """Handles direct video file upload (.mp4, .mkv, .mov, .webm) and initiates translation."""
    job_id = str(uuid.uuid4())
    safe_filename = f"{job_id}_{video.filename}"
    saved_path = UPLOAD_DIR / safe_filename

    # Save uploaded file to disk
    with open(saved_path, "wb") as buffer:
        shutil.copyfileobj(video.file, buffer)

    # Register in database
    db.create_job({
        "id": job_id,
        "title": video.filename or "Uploaded Video",
        "input_source_type": "FILE",
        "original_filename": video.filename,
        "original_video_path": str(saved_path),
        "source_language": source_lang,
        "target_language": target_lang,
        "speaker_gender_override": gender_override,
        "lip_sync_enabled": lip_sync_enabled,
        "fast_parallel_mode": fast_parallel_mode
    })

    # Trigger background worker
    background_tasks.add_task(run_translation_background, job_id)

    return {
        "status": "success",
        "job_id": job_id,
        "message": "Video uploaded successfully. Translation started."
    }


@app.post("/api/translate/url")
def translate_video_url(
    payload: UrlTranslationRequest,
    background_tasks: BackgroundTasks
):
    """Handles video translation from web URL (YouTube, Vimeo, direct MP4 link)."""
    if not payload.url or not payload.url.strip():
        raise HTTPException(status_code=400, detail="Invalid video URL provided.")

    job_id = str(uuid.uuid4())
    dummy_input_path = str(UPLOAD_DIR / f"{job_id}_raw.mp4")

    # Register in database
    db.create_job({
        "id": job_id,
        "title": f"Web Video: {payload.url[:40]}...",
        "input_source_type": "URL",
        "input_url": payload.url.strip(),
        "original_video_path": dummy_input_path,
        "source_language": payload.source_lang or "auto",
        "target_language": payload.target_lang,
        "speaker_gender_override": payload.gender_override or "auto",
        "lip_sync_enabled": payload.lip_sync_enabled,
        "fast_parallel_mode": payload.fast_parallel_mode
    })

    # Trigger background worker
    background_tasks.add_task(run_translation_background, job_id)

    return {
        "status": "success",
        "job_id": job_id,
        "message": "URL received. Video downloading and translation started."
    }


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    """Poll job progress, status, and speaker segments."""
    job = db.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")

    segments = db.get_speaker_segments(job_id)
    return {
        "job_id": job["id"],
        "status": job["status"],
        "progress": job["progress_percentage"],
        "current_step": job["current_step"],
        "error_message": job["error_message"],
        "target_language": job["target_language"],
        "completed_at": job["completed_at"],
        "output_available": bool(job["output_video_path"] and os.path.exists(job["output_video_path"])),
        "segments": segments
    }


@app.get("/api/download/{job_id}")
def download_translated_video(job_id: str):
    """Download the completed translated MP4 video."""
    job = db.get_job(job_id)
    if not job or not job.get("output_video_path"):
        raise HTTPException(status_code=404, detail="Translated video not ready or job not found")

    output_path = job["output_video_path"]
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Output video file does not exist on server")

    # Record download in database
    db.record_download(str(uuid.uuid4()), job_id)

    filename = f"translated_{job.get('target_language', 'video')}_{job_id[:8]}.mp4"
    return FileResponse(
        path=output_path,
        media_type="video/mp4",
        filename=filename,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


@app.get("/api/stream/{job_id}")
def stream_translated_video(job_id: str):
    """Stream video for in-browser video player preview."""
    job = db.get_job(job_id)
    if not job or not job.get("output_video_path"):
        raise HTTPException(status_code=404, detail="Translated video not found")

    output_path = job["output_video_path"]
    if not os.path.exists(output_path):
        raise HTTPException(status_code=404, detail="Video file does not exist")

    return FileResponse(path=output_path, media_type="video/mp4")


# Mount Frontend Static Directory
frontend_dir = PROJECT_ROOT / "frontend"
if frontend_dir.exists():
    app.mount("/", StaticFiles(directory=str(frontend_dir), html=True), name="frontend")


if __name__ == "__main__":
    import uvicorn
    print("Starting AI Video Translator Server at http://127.0.0.1:8000")
    uvicorn.run("backend.app:app", host="0.0.0.0", port=8000, reload=True)
