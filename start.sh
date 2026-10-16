#!/bin/bash
set -e

echo "==================================================="
echo "      Starting AI Video Translator Studio"
echo "==================================================="

echo "[1/3] Checking dependencies..."
python3 -m pip install -r backend/requirements.txt

echo "[2/3] Initializing Database..."
python3 -c "from database.db_manager import db; print('Database ready.')"

echo "[3/3] Launching FastAPI Web Application..."
echo "Application running at: http://localhost:8000"
python3 -m uvicorn backend.app:app --host 0.0.0.0 --port 8000 --reload
