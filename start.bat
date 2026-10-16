@echo off
:: Switch to the directory where start.bat is located
cd /d "%~dp0"

echo ===================================================
echo       Starting AI Video Translator Studio
echo ===================================================

echo [1/3] Checking Python dependencies...
python -m pip install -r backend/requirements.txt

echo [2/3] Initializing Database...
python -c "from database.db_manager import db; print('Database ready.')"

echo [3/3] Launching FastAPI Web Application...
echo.
echo Application will be available at: http://localhost:8000
echo.
python -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
pause
