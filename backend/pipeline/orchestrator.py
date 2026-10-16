"""
Pipeline Orchestrator
Coordinates end-to-end execution of the video translation pipeline:
1. Input retrieval (file or URL)
2. Audio extraction & duration check (up to 40 mins)
3. Speech transcription with word/sentence timestamps
4. Speaker diarization & male/female voice gender detection
5. Multi-language neural translation
6. Voice synthesis with pitch/tempo time alignment
7. Lip-sync synchronization
8. Final video assembly and download packaging
"""

import os
import sys
import uuid
import logging
from pathlib import Path
from typing import Dict, Any, Callable

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config import UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR, MAX_VIDEO_DURATION_SECONDS
from database.db_manager import db
from backend.pipeline.audio_extractor import AudioVideoExtractor
from backend.pipeline.transcription import TranscriptionEngine
from backend.pipeline.gender_detector import GenderDetector
from backend.pipeline.translator import TranslationEngine
from backend.pipeline.voice_synthesizer import VoiceSynthesizer
from backend.pipeline.lip_sync import LipSyncEngine
from backend.pipeline.video_assembler import VideoAssembler

logger = logging.getLogger("ai_video_translator.orchestrator")


class TranslationOrchestrator:
    def __init__(self):
        self.extractor = AudioVideoExtractor()
        self.transcriber = TranscriptionEngine(model_size="base")
        self.gender_detector = GenderDetector()
        self.translator = TranslationEngine()
        self.synthesizer = VoiceSynthesizer()
        self.lip_syncer = LipSyncEngine()
        self.assembler = VideoAssembler()

    def process_job(self, job_id: str, progress_callback: Callable[[int, str], None] = None) -> Dict[str, Any]:
        """Runs the entire translation pipeline for a given job ID."""
        def update_progress(pct: int, desc: str):
            logger.info("[Job %s] %d%% - %s", job_id, pct, desc)
            db.update_job_progress(job_id, status="PROCESSING", progress=pct, step_desc=desc)
            if progress_callback:
                progress_callback(pct, desc)

        job = db.get_job(job_id)
        if not job:
            raise ValueError(f"Job {job_id} not found in database")

        target_lang = job["target_language"]
        gender_override = job.get("speaker_gender_override", "auto")
        lip_sync_enabled = bool(job.get("lip_sync_enabled", True))
        fast_parallel = bool(job.get("fast_parallel_mode", True))

        temp_job_dir = TEMP_DIR / job_id
        temp_job_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Step 1: Input Acquisition
            update_progress(5, "Acquiring input video...")
            video_input_path = job["original_video_path"]
            if job["input_source_type"] == "URL" and not os.path.exists(video_input_path):
                video_input_path = self.extractor.download_url_video(
                    job["input_url"], str(UPLOAD_DIR), job_id
                )
                db.update_job_progress(job_id, status="PROCESSING", progress=10, step_desc="Video downloaded successfully")

            # Validate duration (<= 40 minutes)
            update_progress(12, "Inspecting video format and duration...")
            meta = self.extractor.get_video_metadata(video_input_path)
            duration = meta.get("duration", 0.0)
            if duration > MAX_VIDEO_DURATION_SECONDS:
                raise ValueError(f"Video duration ({duration/60:.1f} mins) exceeds maximum limit of 40 minutes.")

            # Step 2: Audio Demuxing
            update_progress(20, "Extracting high-resolution 16kHz audio track...")
            raw_audio_path = str(temp_job_dir / "extracted_audio.wav")
            self.extractor.extract_audio(video_input_path, raw_audio_path)

            # Step 3: Transcription
            update_progress(35, "Transcribing speech and extracting timestamps...")
            transcription_result = self.transcriber.transcribe(
                raw_audio_path, forced_lang=job.get("source_language", "auto")
            )
            detected_src_lang = transcription_result.get("detected_language", "en")
            segments = transcription_result.get("segments", [])

            # Step 4: Speaker Diarization & Gender Detection
            update_progress(50, "Detecting speaker gender (Male / Female) and vocal pitch...")
            for idx, seg in enumerate(segments):
                gender_info = self.gender_detector.detect_gender_from_wav(
                    raw_audio_path, start_sec=seg["start"], end_sec=seg["end"]
                )
                seg["detected_gender"] = gender_info["gender"]
                seg["pitch_mean_hz"] = gender_info["pitch_mean_hz"]

                # Store segment in database
                db.add_speaker_segment({
                    "id": str(uuid.uuid4()),
                    "job_id": job_id,
                    "segment_index": idx,
                    "start_time": seg["start"],
                    "end_time": seg["end"],
                    "duration": seg["end"] - seg["start"],
                    "original_text": seg["text"],
                    "detected_gender": seg["detected_gender"],
                    "pitch_mean_hz": seg["pitch_mean_hz"]
                })

            # Step 5: Multi-Language Neural Translation
            update_progress(65, f"Translating speech segments into '{target_lang}'...")
            translated_segments = self.translator.translate_segments(
                segments, source_lang=detected_src_lang, target_lang=target_lang
            )

            # Step 6: Voice Synthesis with Pitch & Tempo Alignment
            update_progress(78, "Synthesizing gender-matched voice and synchronizing speech tempo...")
            master_audio_path = str(temp_job_dir / "translated_master_audio.wav")
            self.synthesizer.build_full_audio_track(
                segments=translated_segments,
                total_duration=duration,
                output_track_wav=master_audio_path,
                target_lang=target_lang,
                gender_override=gender_override
            )

            # Step 7 & 8: Lip-Sync Synchronization & Final Assembly
            final_output_path = str(OUTPUT_DIR / f"{job_id}_translated.mp4")
            if lip_sync_enabled:
                update_progress(88, "Synchronizing lip movement with translated speech (Wav2Lip)...")
                synced_video = str(temp_job_dir / "lip_synced.mp4")
                self.lip_syncer.synchronize_lips(
                    video_input_path, master_audio_path, synced_video, fast_mode=fast_parallel
                )
                if os.path.exists(synced_video) and os.path.getsize(synced_video) > 1000:
                    update_progress(95, "Finalizing output video for streaming and download...")
                    import shutil
                    shutil.copyfile(synced_video, final_output_path)
                else:
                    update_progress(95, "Multiplexing final video stream for streaming and download...")
                    self.assembler.assemble_final_video(
                        video_input=video_input_path,
                        audio_input=master_audio_path,
                        output_file=final_output_path
                    )
            else:
                update_progress(95, "Multiplexing final video stream for streaming and download...")
                self.assembler.assemble_final_video(
                    video_input=video_input_path,
                    audio_input=master_audio_path,
                    output_file=final_output_path
                )

            # Complete job in database
            db.complete_job(job_id, final_output_path, duration)
            logger.info("[Job %s] 100%% - Translation completed successfully! Output: %s", job_id, final_output_path)
            if progress_callback:
                progress_callback(100, "Translation completed successfully! Video ready for download.")

            return {
                "job_id": job_id,
                "status": "COMPLETED",
                "output_video_path": final_output_path,
                "duration": duration,
                "segments_count": len(translated_segments)
            }

        except Exception as e:
            logger.error("Job %s failed: %s", job_id, e, exc_info=True)
            db.update_job_progress(job_id, status="FAILED", progress=0, step_desc="Error encountered", error=str(e))
            raise
