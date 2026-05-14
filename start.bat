@echo off
chcp 65001 >nul
title Physics Search

set ROOT=%~dp0
set PORT=8765

echo ============================================
echo     Physics Knowledge Search System
echo ============================================
echo.

:: 1. check python
python --version >nul 2>&1
if errorlevel 1 (
    echo [FAIL] Python not found! Please install Python 3.10+
    pause
    exit /b 1
)
echo [OK] Python ready

:: 2. check BGE model
if not exist "D:\bge-large-zh-v1.5" (
    echo [FAIL] BGE model not found at D:\bge-large-zh-v1.5
    echo        Please copy the model folder to D:\
    pause
    exit /b 1
)
echo [OK] BGE model ready

:: 3. chdir to backend
cd /d "%ROOT%backend"

:: 4. setup venv if needed
if not exist "venv\Scripts\python.exe" (
    echo.
    echo === First run: installing dependencies (5-10 min) ===
    echo.

    echo [1/4] Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo [FAIL] Failed to create virtual environment
        pause
        exit /b 1
    )

    echo [2/4] Installing base dependencies...
    venv\Scripts\pip install -r requirements.txt
    if errorlevel 1 (
        echo [FAIL] pip install failed
        pause
        exit /b 1
    )

    echo [3/4] Installing sentence-transformers...
    venv\Scripts\pip install sentence-transformers
    if errorlevel 1 (
        echo [FAIL] pip install failed
        pause
        exit /b 1
    )

    echo [4/4] Installing PyTorch...
    venv\Scripts\pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu
    if errorlevel 1 (
        echo [FAIL] pip install failed
        pause
        exit /b 1
    )

    echo.
    echo [OK] All dependencies installed!
) else (
    echo [OK] Virtual environment ready
)

:: 5. try to free port (kill old process if any)
echo [CHECK] Checking port %PORT%...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%PORT%"') do (
    echo [INFO] Port %PORT% is in use by PID %%p, stopping it...
    taskkill /f /pid %%p >nul 2>&1
    timeout /t 2 /nobreak >nul
)

:: 6. start backend (via helper bat to avoid Chinese path in command line)
echo.
echo [START] Launching backend server (port %PORT%)...
start "backend" /d "%ROOT%backend" run.bat

:: 7. wait
echo [WAIT] Waiting for server...
timeout /t 5 /nobreak >nul

:: 8. test connection
python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:%PORT%/api/health')" >nul 2>&1
if errorlevel 1 (
    echo [WARN] Server may not be ready yet - check the backend window for errors
) else (
    echo [OK] Server is running
)

echo.
echo ============================================
echo   Open browser:
echo   http://localhost:%PORT%
echo   Close this window to stop
echo ============================================
echo.
pause
