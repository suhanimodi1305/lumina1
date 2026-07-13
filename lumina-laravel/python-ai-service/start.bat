@echo off
echo Starting Lumina AI Service on port 8001...
cd /d %~dp0
call ..\.venv-1\Scripts\activate.bat
uvicorn main:app --host 0.0.0.0 --port 8001 --reload
pause
