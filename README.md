# 🎙️ AI Video Translator Studio 2.0

An ultra-modern, authentic spoken video translation studio with neural voice synthesis. Built for high performance, zero-lag large video playback, multi-language speech translation, and serverless deployment on Vercel.

---

## ✨ Features

- **Instant 1-Click Demo (🇮🇳 ➔ 🇬🇧)**: Load everyday Hindi conversational video dialogue and watch it accurately translate to English with clear neural voice synthesis.
- **Large File Support (Up to 2 GB)**: Bypass Vercel's `4.5 MB` `413 Request Entity Too Large` limit. Large files are played client-side via `URL.createObjectURL` with zero upload lag, while spoken audio dialogue is extracted and translated.
- **Authentic Multi-Language Translation**:
  - Translates dynamically between Hindi, English, Tamil, Telugu, Spanish, French, German, Japanese, Chinese, Arabic, Russian, Portuguese, Italian, Korean, Marathi, and Bengali.
  - Multi-provider fallback: Google Translate + MyMemory Translation.
  - **Zero Hardcoded Tamil**: Spoken neural voice strictly matches your chosen target language.
- **Dynamic Neural Speech Synthesis**:
  - Google Neural Text-to-Speech synthesis with chunked streaming.
  - High fidelity MP3 audio track synchronized to video playback.
- **SubRip (.SRT) Subtitle Generator**:
  - Live karaoke/highlight subtitles during playback.
  - One-click `.SRT` subtitle file download.
- **YouTube & Online Video Support**:
  - Extract real spoken dialogue captions directly from YouTube videos using `youtube-transcript-api`.
- **1-Click Google / Gmail & Email Authentication**:
  - Seamless authentication simulation for Pro tier video translations.

---

## 🛠️ Project Structure

```
├── api/
│   ├── index.py           # FastAPI Serverless backend router
│   └── requirements.txt   # Python runtime dependencies
├── index.html             # Responsive studio UI with transparent dropzone
├── style.css              # Modern dark theme styles
├── app.js                 # Safe upload, Web Audio, playback & sync logic
├── vercel.json            # Vercel serverless routing configuration
├── .gitignore             # Python, node, and temp file exclusions
└── README.md              # Project documentation
```

---

## 🚀 Getting Started

### 1. Local Development

To run the backend locally with Uvicorn:

```bash
# Install Python dependencies
pip install -r api/requirements.txt

# Start FastAPI server
uvicorn api.index:app --reload --port 8000
```

Open `http://localhost:8000` in your web browser.

### 2. Deploy to Vercel

```bash
# Deploy to production
npx vercel --prod
```

The project is preconfigured with `vercel.json` to route `/api/*` to `/api/index.py` serverless functions.

---

## 🔒 Security & Privacy

- Temporary audio memory buffers are freed after processing.
- No personal user video binaries are stored permanently on server disks.
- Safe client-side video streaming via `URL.createObjectURL(file)`.

---

## 📄 License

MIT License. Open source and free to use.
