_FINAL> Get-Content .\run_backend.bat
cd /d "%~dp0"
call ".venv\Scripts\activate.bat" 2>nul
python -m uvicorn backend.app:app --host 127.0.0.1 --port 8003 --reload
pause
PS C:\Users\Admin\Desktop\RetailEdge_SIH26179_FINAL_FIXED (1)\RetailEdge_SIH26179_FINAL> Get-Content .\run_frontend.bat
@echo off 
cd /d "%~dp0"
python -m http.server 5500 --bind 127.0.0.1 --directory frontend
pause
PS C:\Users\Admin\Desktop\RetailEdge_SIH26179_FINAL_FIXED (1)\RetailEdge_SIH26179_FINAL>