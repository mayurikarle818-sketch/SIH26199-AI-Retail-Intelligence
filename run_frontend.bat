@echo off
cd /d "%~dp0"
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
pause
