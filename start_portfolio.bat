@echo off
echo ===================================================
echo   Prince Portfolio - Startup Script
echo ===================================================
echo.

:: Check if port 8000 is already in use
netstat -ano | findstr :8000 > nul
if %errorlevel% equ 0 (
    echo [INFO] Portfolio server is ALREADY running on port 8000. Skipping server startup.
) else (
    echo Starting FastAPI Server in a new window...
    start cmd /k "title Portfolio Server && .venv\Scripts\activate && uvicorn main:app --host 127.0.0.1 --port 8000"
    timeout /t 3 /nobreak > nul
)

echo Starting ngrok Tunnel in a new window...
start cmd /k "title ngrok Tunnel && C:\Users\01\AppData\Local\Microsoft\WinGet\Packages\Ngrok.Ngrok_Microsoft.Winget.Source_8wekyb3d8bbwe\ngrok.exe http 127.0.0.1:8000"

echo.
echo ===================================================
echo   SUCCESS!
echo   1. The "Portfolio Server" runs your site backend (if it wasn't already running).
echo   2. The "ngrok Tunnel" window displays your public link.
echo   
echo   - Look for the "Forwarding" URL (e.g., https://xxxx.ngrok-free.app).
echo   - Share that link with your clients!
echo   - Keep BOTH windows open to keep your site online.
echo ===================================================
echo.
pause
