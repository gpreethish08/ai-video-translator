-- ====================================================================
-- AI Video Translator Database Schema
-- Multi-database support: SQLite 3 / PostgreSQL 14+ / MySQL 8+
-- ====================================================================

-- 0. Users & Authentication (Google / Gmail OAuth)
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(64) PRIMARY KEY,
    email VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    avatar_url TEXT DEFAULT NULL,
    auth_provider VARCHAR(50) DEFAULT 'google',
    plan_tier VARCHAR(50) DEFAULT 'free',
    credits_remaining INTEGER DEFAULT 10,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 1. Supported Languages Catalog
CREATE TABLE IF NOT EXISTS supported_languages (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    native_name VARCHAR(100) NOT NULL,
    default_male_voice VARCHAR(100) NOT NULL,
    default_female_voice VARCHAR(100) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 2. Projects & Translation Jobs
CREATE TABLE IF NOT EXISTS translation_jobs (
    id VARCHAR(64) PRIMARY KEY,
    title VARCHAR(255) DEFAULT 'Untitled Video Translation',
    input_source_type VARCHAR(20) NOT NULL, -- 'FILE' or 'URL'
    input_url TEXT DEFAULT NULL,
    original_filename VARCHAR(255) DEFAULT NULL,
    original_video_path TEXT NOT NULL,
    original_duration_seconds REAL DEFAULT 0.0,
    source_language VARCHAR(10) DEFAULT 'auto',
    target_language VARCHAR(10) NOT NULL,
    detected_source_language VARCHAR(10) DEFAULT NULL,
    status VARCHAR(50) DEFAULT 'QUEUED', -- QUEUED, DOWNLOADING, EXTRACTING, TRANSCRIBING, DIARIZING, TRANSLATING, SYNTHESIZING, LIPSYNCING, COMPLETED, FAILED
    progress_percentage INTEGER DEFAULT 0,
    current_step VARCHAR(100) DEFAULT 'Job Initialized',
    error_message TEXT DEFAULT NULL,
    output_video_path TEXT DEFAULT NULL,
    output_duration_seconds REAL DEFAULT 0.0,
    lip_sync_enabled BOOLEAN DEFAULT TRUE,
    fast_parallel_mode BOOLEAN DEFAULT TRUE,
    speaker_gender_override VARCHAR(20) DEFAULT 'auto', -- 'auto', 'male', 'female'
    file_size_bytes BIGINT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP DEFAULT NULL
);

-- 3. Speaker Diarization and Voice Segments
CREATE TABLE IF NOT EXISTS speaker_segments (
    id VARCHAR(64) PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL,
    segment_index INTEGER NOT NULL,
    start_time REAL NOT NULL,
    end_time REAL NOT NULL,
    duration REAL NOT NULL,
    original_text TEXT NOT NULL,
    translated_text TEXT DEFAULT NULL,
    detected_gender VARCHAR(10) DEFAULT 'MALE', -- 'MALE' or 'FEMALE'
    pitch_mean_hz REAL DEFAULT 0.0,
    assigned_voice_id VARCHAR(100) DEFAULT NULL,
    synthesized_audio_path TEXT DEFAULT NULL,
    status VARCHAR(30) DEFAULT 'PENDING',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES translation_jobs(id) ON DELETE CASCADE
);

-- 4. Download and Export Logs
CREATE TABLE IF NOT EXISTS download_logs (
    id VARCHAR(64) PRIMARY KEY,
    job_id VARCHAR(64) NOT NULL,
    ip_address VARCHAR(50) DEFAULT '127.0.0.1',
    user_agent TEXT DEFAULT NULL,
    download_format VARCHAR(20) DEFAULT 'mp4',
    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (job_id) REFERENCES translation_jobs(id) ON DELETE CASCADE
);

-- Indexing for performance
CREATE INDEX IF NOT EXISTS idx_jobs_status ON translation_jobs(status);
CREATE INDEX IF NOT EXISTS idx_jobs_created ON translation_jobs(created_at);
CREATE INDEX IF NOT EXISTS idx_segments_job ON speaker_segments(job_id);

-- Seed Data: Common Global Languages
INSERT OR IGNORE INTO supported_languages (code, name, native_name, default_male_voice, default_female_voice) VALUES
('en', 'English', 'English', 'en-US-GuyNeural', 'en-US-JennyNeural'),
('es', 'Spanish', 'Español', 'es-ES-AlvaroNeural', 'es-ES-ElviraNeural'),
('fr', 'French', 'Français', 'fr-FR-HenriNeural', 'fr-FR-DeniseNeural'),
('de', 'German', 'Deutsch', 'de-DE-ConradNeural', 'de-DE-KatjaNeural'),
('hi', 'Hindi', 'हिन्दी', 'hi-IN-MadhurNeural', 'hi-IN-SwaraNeural'),
('ta', 'Tamil', 'தமிழ்', 'ta-IN-ValluvarNeural', 'ta-IN-PallaviNeural'),
('te', 'Telugu', 'తెలుగు', 'te-IN-MohanNeural', 'te-IN-ShrutiNeural'),
('ja', 'Japanese', '日本語', 'ja-JP-KeitaNeural', 'ja-JP-NanamiNeural'),
('zh', 'Chinese (Mandarin)', '中文', 'zh-CN-YunxiNeural', 'zh-CN-XiaoxiaoNeural'),
('ar', 'Arabic', 'العربية', 'ar-SA-HamedNeural', 'ar-SA-ZariyahNeural'),
('ru', 'Russian', 'Русский', 'ru-RU-DmitryNeural', 'ru-RU-SvetlanaNeural'),
('pt', 'Portuguese', 'Português', 'pt-BR-AntonioNeural', 'pt-BR-FranciscaNeural'),
('it', 'Italian', 'Italiano', 'it-IT-DiegoNeural', 'it-IT-ElsaNeural'),
('ko', 'Korean', '한국어', 'ko-KR-InJoonNeural', 'ko-KR-SunHiNeural'),
('bn', 'Bengali', 'বাংলা', 'bn-IN-BashkarNeural', 'bn-IN-TanishaaNeural'),
('mr', 'Marathi', 'मराठी', 'mr-IN-ManoharNeural', 'mr-IN-AarohiNeural'),
('tr', 'Turkish', 'Türkçe', 'tr-TR-AhmetNeural', 'tr-TR-EmelNeural'),
('vi', 'Vietnamese', 'Tiếng Việt', 'vi-VN-NamMinhNeural', 'vi-VN-HoaiMyNeural'),
('id', 'Indonesian', 'Bahasa Indonesia', 'id-ID-ArdiNeural', 'id-ID-GadisNeural'),
('nl', 'Dutch', 'Nederlands', 'nl-NL-MaartenNeural', 'nl-NL-ColetteNeural'),
('pl', 'Polish', 'Polski', 'pl-PL-MarekNeural', 'pl-PL-ZofiaNeural'),
('uk', 'Ukrainian', 'Українська', 'uk-UA-OstapNeural', 'uk-UA-PolinaNeural'),
('ur', 'Urdu', 'اردو', 'ur-PK-AsadNeural', 'ur-PK-UzmaNeural'),
('gu', 'Gujarati', 'ગુજરાતી', 'gu-IN-NiranjanNeural', 'gu-IN-DhwaniNeural'),
('kn', 'Kannada', 'ಕನ್ನಡ', 'kn-IN-GaganNeural', 'kn-IN-SapnaNeural'),
('ml', 'Malayalam', 'മലയാളം', 'ml-IN-MidhunNeural', 'ml-IN-SobhanaNeural');
