@echo off
chcp 65001 >nul
title backend

cd /d "%~dp0"

echo [INFO] Starting server, please wait...
echo.

venv\Scripts\python -m uvicorn main:app --host 0.0.0.0 --port 8765

echo [FAIL] Server exited unexpectedly
pause
