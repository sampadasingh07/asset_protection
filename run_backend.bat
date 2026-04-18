@echo off
cd /d "%~dp0backend"
start "VeriLens Backend" cmd /k "python -m uvicorn app.main:app --host 127.0.0.1 --port 8000"
pause
