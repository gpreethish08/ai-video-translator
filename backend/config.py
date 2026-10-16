"""
Configuration settings for AI Video Translator
"""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
BACKEND_DIR = BASE_DIR / "backend"

# Storage Directories
UPLOAD_DIR = BACKEND_DIR / "uploads"
OUTPUT_DIR = BACKEND_DIR / "outputs"
TEMP_DIR = BACKEND_DIR / "temp"

for directory in [UPLOAD_DIR, OUTPUT_DIR, TEMP_DIR]:
    directory.mkdir(parents=True, exist_ok=True)

# Performance & Video Constraints
MAX_VIDEO_DURATION_MINUTES = 40
MAX_VIDEO_DURATION_SECONDS = MAX_VIDEO_DURATION_MINUTES * 60  # 2400 seconds
CHUNK_DURATION_SECONDS = 300  # 5-minute chunks for parallel processing
MAX_CONCURRENT_CHUNKS = 4

# Audio Processing Specs
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1

# Supported Global Languages & Voice Mapping (Male & Female Neural Voices)
SUPPORTED_LANGUAGES = {
    "en": {"name": "English", "male_voice": "en-US-GuyNeural", "female_voice": "en-US-JennyNeural"},
    "es": {"name": "Spanish", "male_voice": "es-ES-AlvaroNeural", "female_voice": "es-ES-ElviraNeural"},
    "fr": {"name": "French", "male_voice": "fr-FR-HenriNeural", "female_voice": "fr-FR-DeniseNeural"},
    "de": {"name": "German", "male_voice": "de-DE-ConradNeural", "female_voice": "de-DE-KatjaNeural"},
    "hi": {"name": "Hindi", "male_voice": "hi-IN-MadhurNeural", "female_voice": "hi-IN-SwaraNeural"},
    "ta": {"name": "Tamil", "male_voice": "ta-IN-ValluvarNeural", "female_voice": "ta-IN-PallaviNeural"},
    "te": {"name": "Telugu", "male_voice": "te-IN-MohanNeural", "female_voice": "te-IN-ShrutiNeural"},
    "ja": {"name": "Japanese", "male_voice": "ja-JP-KeitaNeural", "female_voice": "ja-JP-NanamiNeural"},
    "zh": {"name": "Chinese (Mandarin)", "male_voice": "zh-CN-YunxiNeural", "female_voice": "zh-CN-XiaoxiaoNeural"},
    "ar": {"name": "Arabic", "male_voice": "ar-SA-HamedNeural", "female_voice": "ar-SA-ZariyahNeural"},
    "ru": {"name": "Russian", "male_voice": "ru-RU-DmitryNeural", "female_voice": "ru-RU-SvetlanaNeural"},
    "pt": {"name": "Portuguese", "male_voice": "pt-BR-AntonioNeural", "female_voice": "pt-BR-FranciscaNeural"},
    "it": {"name": "Italian", "male_voice": "it-IT-DiegoNeural", "female_voice": "it-IT-ElsaNeural"},
    "ko": {"name": "Korean", "male_voice": "ko-KR-InJoonNeural", "female_voice": "ko-KR-SunHiNeural"},
    "bn": {"name": "Bengali", "male_voice": "bn-IN-BashkarNeural", "female_voice": "bn-IN-TanishaaNeural"},
    "mr": {"name": "Marathi", "male_voice": "mr-IN-ManoharNeural", "female_voice": "mr-IN-AarohiNeural"},
    "tr": {"name": "Turkish", "male_voice": "tr-TR-AhmetNeural", "female_voice": "tr-TR-EmelNeural"},
    "vi": {"name": "Vietnamese", "male_voice": "vi-VN-NamMinhNeural", "female_voice": "vi-VN-HoaiMyNeural"},
    "id": {"name": "Indonesian", "male_voice": "id-ID-ArdiNeural", "female_voice": "id-ID-GadisNeural"},
    "nl": {"name": "Dutch", "male_voice": "nl-NL-MaartenNeural", "female_voice": "nl-NL-ColetteNeural"},
    "pl": {"name": "Polish", "male_voice": "pl-PL-MarekNeural", "female_voice": "pl-PL-ZofiaNeural"},
    "uk": {"name": "Ukrainian", "male_voice": "uk-UA-OstapNeural", "female_voice": "uk-UA-PolinaNeural"},
    "ur": {"name": "Urdu", "male_voice": "ur-PK-AsadNeural", "female_voice": "ur-PK-UzmaNeural"},
    "gu": {"name": "Gujarati", "male_voice": "gu-IN-NiranjanNeural", "female_voice": "gu-IN-DhwaniNeural"},
    "kn": {"name": "Kannada", "male_voice": "kn-IN-GaganNeural", "female_voice": "kn-IN-SapnaNeural"},
    "ml": {"name": "Malayalam", "male_voice": "ml-IN-MidhunNeural", "female_voice": "ml-IN-SobhanaNeural"}
}

# Gender Detection Pitch Boundaries (in Hertz)
MALE_PITCH_THRESHOLD_MAX = 165.0   # Typically 85 - 165 Hz
FEMALE_PITCH_THRESHOLD_MIN = 165.0 # Typically 165 - 265 Hz
