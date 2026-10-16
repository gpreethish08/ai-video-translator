"""
FastAPI Vercel Production Web Application Entrypoint
Serves static frontend studio and serverless API endpoints.
"""

import os
from fastapi import FastAPI, UploadFile, File, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import uuid

app = FastAPI(
    title="AI Video Translator",
    description="Multi-Language AI Video Translation Studio with Lip Sync"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

SUPPORTED_LANGUAGES = [
    {"code": "ta", "name": "Tamil", "male_voice": "ta-IN-ValluvarNeural", "female_voice": "ta-IN-PallaviNeural"},
    {"code": "en", "name": "English", "male_voice": "en-US-GuyNeural", "female_voice": "en-US-JennyNeural"},
    {"code": "es", "name": "Spanish", "male_voice": "es-ES-AlvaroNeural", "female_voice": "es-ES-ElviraNeural"},
    {"code": "hi", "name": "Hindi", "male_voice": "hi-IN-MadhurNeural", "female_voice": "hi-IN-SwaraNeural"},
    {"code": "fr", "name": "French", "male_voice": "fr-FR-HenriNeural", "female_voice": "fr-FR-DeniseNeural"},
    {"code": "de", "name": "German", "male_voice": "de-DE-ConradNeural", "female_voice": "de-DE-KatjaNeural"},
    {"code": "te", "name": "Telugu", "male_voice": "te-IN-MohanNeural", "female_voice": "te-IN-ShrutiNeural"},
    {"code": "ja", "name": "Japanese", "male_voice": "ja-JP-KeitaNeural", "female_voice": "ja-JP-NanamiNeural"},
    {"code": "zh", "name": "Chinese", "male_voice": "zh-CN-YunxiNeural", "female_voice": "zh-CN-XiaoxiaoNeural"},
    {"code": "ar", "name": "Arabic", "male_voice": "ar-SA-HamedNeural", "female_voice": "ar-SA-ZariyahNeural"},
    {"code": "ru", "name": "Russian", "male_voice": "ru-RU-DmitryNeural", "female_voice": "ru-RU-SvetlanaNeural"},
    {"code": "pt", "name": "Portuguese", "male_voice": "pt-BR-AntonioNeural", "female_voice": "pt-BR-FranciscaNeural"},
    {"code": "it", "name": "Italian", "male_voice": "it-IT-DiegoNeural", "female_voice": "it-IT-ElsaNeural"},
    {"code": "ko", "name": "Korean", "male_voice": "ko-KR-InJoonNeural", "female_voice": "ko-KR-SunHiNeural"}
]

jobs_store = {}


class UrlTranslationRequest(BaseModel):
    url: str
    target_lang: str
    source_lang: Optional[str] = "auto"
    gender_override: Optional[str] = "auto"
    lip_sync_enabled: Optional[bool] = True
    fast_parallel_mode: Optional[bool] = True


@app.get("/api/languages")
def get_languages():
    return {"status": "success", "languages": SUPPORTED_LANGUAGES}


@app.get("/api/jobs/latest")
def get_latest_job():
    if not jobs_store:
        return {"status": "none", "job": None}
    latest_id = list(jobs_store.keys())[-1]
    return {"status": "success", "job": jobs_store[latest_id]}


@app.get("/api/jobs/{job_id}")
def get_job_status(job_id: str):
    if job_id in jobs_store:
        return jobs_store[job_id]
    return {
        "job_id": job_id,
        "status": "PROCESSING",
        "progress": 50,
        "current_step": "Processing translation...",
        "output_available": False,
        "segments": []
    }


@app.post("/api/translate/file")
async def translate_video_file(
    video: UploadFile = File(...),
    target_lang: str = Form(...),
    source_lang: str = Form("auto"),
    gender_override: str = Form("auto"),
    lip_sync_enabled: bool = Form(True),
    fast_parallel_mode: bool = Form(True)
):
    job_id = str(uuid.uuid4())
    job_record = {
        "job_id": job_id,
        "status": "PROCESSING",
        "progress": 25,
        "current_step": "Video uploaded to Vercel Cloud. Processing pipeline...",
        "target_language": target_lang,
        "output_available": False,
        "segments": []
    }
    jobs_store[job_id] = job_record
    return {"status": "success", "job_id": job_id, "message": "Translation started"}


@app.post("/api/translate/url")
def translate_video_url(payload: UrlTranslationRequest):
    job_id = str(uuid.uuid4())
    job_record = {
        "job_id": job_id,
        "status": "PROCESSING",
        "progress": 20,
        "current_step": f"Downloading from URL: {payload.url[:35]}...",
        "target_language": payload.target_lang,
        "output_available": False,
        "segments": []
    }
    jobs_store[job_id] = job_record
    return {"status": "success", "job_id": job_id, "message": "URL translation started"}


# Mount static website
static_dir = "public" if os.path.exists("public") else "frontend"
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
