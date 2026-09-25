@echo off
cd /d "%~dp0"
call ".venv\Scripts\activate.bat" 2>nul
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8003 --reload
pause
