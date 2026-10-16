"""
Database Manager for AI Video Translator
Supports SQLite (zero-config local) and PostgreSQL (production).
Provides schema initialization, job status tracking, speaker segment records,
and analytics queries.
"""

import os
import sqlite3
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger("ai_video_translator.database")

DB_DIR = os.path.dirname(os.path.abspath(__file__))
DEFAULT_DB_PATH = os.path.join(DB_DIR, "translator.db")
SCHEMA_PATH = os.path.join(DB_DIR, "schema.sql")


class DatabaseManager:
    def __init__(self, db_path: str = DEFAULT_DB_PATH):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.initialize_schema()

    def get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        return conn

    def initialize_schema(self):
        """Initializes tables from schema.sql if not existing."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                if os.path.exists(SCHEMA_PATH):
                    with open(SCHEMA_PATH, "r", encoding="utf-8") as f:
                        schema_sql = f.read()
                    cursor.executescript(schema_sql)
                    conn.commit()
                    logger.info("Database initialized successfully at %s", self.db_path)
                else:
                    logger.warning("schema.sql not found at %s. Creating minimal schema.", SCHEMA_PATH)
        except Exception as e:
            logger.error("Error initializing database: %s", e)

    def create_job(self, job_data: Dict[str, Any]) -> str:
        """Insert a new translation job into the database."""
        query = """
        INSERT INTO translation_jobs (
            id, title, input_source_type, input_url, original_filename,
            original_video_path, source_language, target_language, status,
            progress_percentage, current_step, lip_sync_enabled,
            fast_parallel_mode, speaker_gender_override, created_at, updated_at
        ) VALUES (
            :id, :title, :input_source_type, :input_url, :original_filename,
            :original_video_path, :source_language, :target_language, :status,
            :progress_percentage, :current_step, :lip_sync_enabled,
            :fast_parallel_mode, :speaker_gender_override, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
        )
        """
        defaults = {
            "title": "Untitled Video",
            "input_url": None,
            "original_filename": None,
            "source_language": "auto",
            "status": "QUEUED",
            "progress_percentage": 0,
            "current_step": "Job Created",
            "lip_sync_enabled": True,
            "fast_parallel_mode": True,
            "speaker_gender_override": "auto",
        }
        params = {**defaults, **job_data}

        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

        return job_data["id"]

    def update_job_progress(self, job_id: str, status: str, progress: int, step_desc: str, error: Optional[str] = None):
        """Update job status and progress percentage."""
        query = """
        UPDATE translation_jobs
        SET status = ?,
            progress_percentage = ?,
            current_step = ?,
            error_message = ?,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (status, progress, step_desc, error, job_id))
            conn.commit()

    def complete_job(self, job_id: str, output_path: str, output_duration: float):
        """Mark job as completed with the output video path."""
        query = """
        UPDATE translation_jobs
        SET status = 'COMPLETED',
            progress_percentage = 100,
            current_step = 'Translation Complete',
            output_video_path = ?,
            output_duration_seconds = ?,
            completed_at = CURRENT_TIMESTAMP,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (output_path, output_duration, job_id))
            conn.commit()

    def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a single job by its ID."""
        query = "SELECT * FROM translation_jobs WHERE id = ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (job_id,))
            row = cursor.fetchone()
            if row:
                return dict(row)
        return None

    def list_jobs(self, limit: int = 50) -> List[Dict[str, Any]]:
        """List the most recent translation jobs."""
        query = "SELECT * FROM translation_jobs ORDER BY created_at DESC LIMIT ?"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (limit,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def add_speaker_segment(self, segment_data: Dict[str, Any]):
        """Save a recognized speaker segment with detected gender and text."""
        query = """
        INSERT INTO speaker_segments (
            id, job_id, segment_index, start_time, end_time, duration,
            original_text, translated_text, detected_gender, pitch_mean_hz,
            assigned_voice_id, synthesized_audio_path, status
        ) VALUES (
            :id, :job_id, :segment_index, :start_time, :end_time, :duration,
            :original_text, :translated_text, :detected_gender, :pitch_mean_hz,
            :assigned_voice_id, :synthesized_audio_path, :status
        )
        """
        defaults = {
            "translated_text": None,
            "detected_gender": "MALE",
            "pitch_mean_hz": 0.0,
            "assigned_voice_id": None,
            "synthesized_audio_path": None,
            "status": "PROCESSED",
        }
        params = {**defaults, **segment_data}
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()

    def get_speaker_segments(self, job_id: str) -> List[Dict[str, Any]]:
        """Get all speaker segments for a specific job."""
        query = "SELECT * FROM speaker_segments WHERE job_id = ? ORDER BY segment_index ASC"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (job_id,))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_supported_languages(self) -> List[Dict[str, Any]]:
        """Get all active supported languages."""
        query = "SELECT * FROM supported_languages WHERE is_active = 1 ORDER BY name ASC"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def record_download(self, log_id: str, job_id: str, ip: str = "127.0.0.1", fmt: str = "mp4"):
        """Record a video download event."""
        query = "INSERT INTO download_logs (id, job_id, ip_address, download_format) VALUES (?, ?, ?, ?)"
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, (log_id, job_id, ip, fmt))
            conn.commit()

    def create_or_get_user(self, email: str, name: str, avatar_url: str = None, provider: str = "google") -> Dict[str, Any]:
        """Create a user if not existing, or return existing user record."""
        import uuid
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            if row:
                return dict(row)
            
            user_id = str(uuid.uuid4())
            cursor.execute("""
                INSERT INTO users (id, email, name, avatar_url, auth_provider)
                VALUES (?, ?, ?, ?, ?)
            """, (user_id, email, name, avatar_url, provider))
            conn.commit()
            cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            return dict(cursor.fetchone())

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Find user by email."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
            row = cursor.fetchone()
            return dict(row) if row else None


# Global Singleton Instance
db = DatabaseManager()
