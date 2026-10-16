# AI Video Translator - Requirements & System Specification

An end-to-end, full-stack AI system designed to translate videos of up to 40 minutes into global languages with authentic neural voiceovers, automatic speaker gender detection, lip-sync preservation, and Google / Gmail authentication.

---

## 1. System Requirements & Architecture Overview

The system is organized into a clean 3-tier architecture:
- **Frontend**: Responsive single-page application built with HTML5, CSS3, Vanilla JS, Google Identity Services SDK, and Web Speech API audio-ducking engine.
- **Backend**: High-performance FastAPI server running on Python 3.10+ with asynchronous background worker queues, Whisper STT, F0 pitch-based gender detection, Neural TTS, and Wav2Lip pipeline.
- **Database**: Relational SQLite / PostgreSQL database tracking user accounts, jobs, speaker segments, and download metrics.
- **Cloud Edge Serverless**: Vercel Python runtime (`api/index.py`) providing instantaneous cloud previews and serverless REST endpoints.

```
ai-video-translator/
├── frontend/ (and public/)
│   ├── index.html        # Modern UI with dual input, auth modal, player, and audio switcher
│   ├── style.css         # Dark-themed responsive design & glassmorphism styling
│   └── app.js            # Video upload, YouTube handler, speech sync, and auth logic
├── backend/
│   ├── app.py            # FastAPI REST API endpoints
│   ├── config.py         # Language catalog, voice models, directories
│   └── pipeline/
│       ├── audio_extractor.py   # 16kHz audio extraction & YouTube (yt-dlp) downloader
│       ├── speech_to_text.py    # OpenAI Whisper transcription with timestamps
│       ├── speaker_diarization.py# Voice pitch analysis (F0) & male/female classification
│       ├── text_translator.py   # Multi-engine translation (Helsinki-NLP / DeepL / Google)
│       ├── voice_synthesizer.py # Edge-TTS neural speech synthesis
│       ├── lip_sync_engine.py   # Wav2Lip / SadTalker face alignment & lip sync
│       └── orchestrator.py      # Async pipeline manager & progress broadcaster
├── database/
│   ├── schema.sql        # Database tables (users, jobs, segments, downloads)
│   ├── db_manager.py     # SQLite/PostgreSQL connection pool & query methods
│   └── translator.db     # SQLite local database
├── api/
│   └── index.py          # Vercel Serverless entrypoint
├── requirements.txt      # Python dependencies
├── vercel.json           # Vercel deployment configuration
├── start.bat             # 1-click Windows runner
└── REQUIREMENTS.md       # System specification & setup guide
```

---

## 2. Functional Requirements

### 2.1 Video Input Requirements
1. **Direct Video Upload**:
   - Supports MP4, MKV, MOV, WebM, AVI formats.
   - Handles long video inputs up to **40 minutes**.
   - Client-side drag-and-drop and file browser picker.
2. **Online URL Input**:
   - Supports YouTube, Vimeo, and direct video URL links.
   - Extracts video streams using `yt-dlp` with automatic JS runtime parsing.

### 2.2 Audio & Translation Output Requirements
1. **Target Language Neural Audio**:
   - Supports 25+ global languages including Tamil (`ta`), Hindi (`hi`), Spanish (`es`), French (`fr`), German (`de`), Telugu (`te`), Japanese (`ja`), Chinese (`zh`), Arabic (`ar`), and English (`en`).
   - Translates spoken dialogue segment-by-segment with sub-second timestamp synchronization.
2. **Speaker Gender Detection**:
   - Performs acoustic pitch analysis using Praat/librosa fundamental frequency ($F_0$).
   - Pitch thresholds:
     - Female voice: $F_0 > 165 \text{ Hz}$ (Average ~ $210 \text{ Hz}$).
     - Male voice: $F_0 \le 165 \text{ Hz}$ (Average ~ $120 \text{ Hz}$).
   - Assigns corresponding male/female neural voices per speaker segment.
3. **Dual-Track Audio Switcher**:
   - **🔊 Translated Neural Audio Track**: Automatically ducks the original video background audio down to 5% volume and plays the target language speech utterance with matching male/female pitch.
   - **🔈 Original Audio Track**: Lets users switch back to inspect the original source audio at 100% volume.
4. **Live Translated Subtitles**:
   - Dynamic caption overlay floating over the video synchronized with current playback time.

### 2.3 Lip-Sync Synchronization
- Synchronizes character mouth and facial movements to match translated target audio using Wav2Lip / SadTalker deep generative models.

### 2.4 Video Download Option
- Generates downloadable finalized `.mp4` video files with the neural translated audio track muxed in.
- Provides immediate 1-click download button upon completion.

---

## 3. User Authentication Requirements (Gmail / Google Sign-In)

The application provides Google OAuth 2.0 / Gmail authentication for user identity, progress saving, and credit management:

### 3.1 Authentication Features
- **1-Click Google / Gmail Sign-In**: Uses Google Identity Services (`https://accounts.google.com/gsi/client`).
- **Standard Email / Password**: Fallback sign-in and sign-up for non-Google users.
- **Session Persistence**: User profile, avatar, email, and subscription plan saved in local storage and database.
- **Interactive Profile Menu**: Displays user initials/avatar, full name, email, and sign-out button.

### 3.2 Configuring Google OAuth 2.0 in Google Cloud Console
To configure your own Google OAuth Client ID for production or local development:
1. Go to the [Google Cloud Console](https://console.cloud.google.com/).
2. Create a new project named `AI Video Translator`.
3. Navigate to **APIs & Services > Credentials**.
4. Click **Create Credentials > OAuth client ID**.
5. Select **Application type**: `Web application`.
6. Add the following to **Authorized JavaScript origins**:
   - `http://localhost:8000`
   - `http://127.0.0.1:8000`
   - `https://ai-video-translator-lpr6.vercel.app` (your Vercel domain)
7. Add the following to **Authorized redirect URIs**:
   - `http://localhost:8000/api/auth/google/callback`
   - `https://ai-video-translator-lpr6.vercel.app/api/auth/google/callback`
8. Copy the **Client ID** and update `data-client_id` in `index.html` or set the environment variable:
   ```bash
   GOOGLE_CLIENT_ID="your-client-id.apps.googleusercontent.com"
   ```

---

## 4. Hardware & Software Prerequisites

### 4.1 System Prerequisites
- **Operating System**: Windows 10/11, macOS, or Linux (Ubuntu 20.04+).
- **Python**: Version 3.10 or 3.11 recommended.
- **FFmpeg**: Installed and accessible in system `PATH`.
- **Node.js**: Node 18+ (used by `yt-dlp` JavaScript extractor for YouTube stream extraction).
- **GPU (Optional but recommended for full local Wav2Lip)**: NVIDIA GPU with CUDA 11.8+ and 6GB+ VRAM.

### 4.2 Python Dependencies (`requirements.txt`)
- `fastapi`, `uvicorn`, `pydantic` - Web framework and ASGI server.
- `openai-whisper` or `faster-whisper` - Speech-to-text recognition.
- `edge-tts` - High-fidelity Microsoft Neural TTS speech generation.
- `transformers`, `torch` - Translation models and deep learning pipelines.
- `librosa`, `soundfile`, `praat-parselmouth` - Pitch and gender detection.
- `yt-dlp` - High-speed video downloader with JS challenge bypass.
- `opencv-python` - Video frame processing for lip-sync.

---

## 5. Running the Application

### 5.1 Local Execution (Windows)
Double-click `start.bat` or run in terminal:
```bash
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
```
Open your browser at `http://127.0.0.1:8000`.

### 5.2 Vercel Cloud Deployment
Deploy to Vercel production:
```bash
npx vercel --prod --yes
```
Live Production URL: [https://ai-video-translator-lpr6.vercel.app](https://ai-video-translator-lpr6.vercel.app)
