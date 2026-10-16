"""
AI Video Translator Application Entrypoint
Exposes FastAPI application from backend.app for local and cloud deployment.
"""

from backend.app import app

if __name__ == "__main__":
    import uvicorn
    print("Starting AI Video Translator Server at http://127.0.0.1:8000")
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
