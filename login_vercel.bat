@echo off
echo ===================================================
echo   Prince Portfolio - Vercel Login Assistant
echo ===================================================
echo.
echo This script will help you log in to your Vercel account.
echo.
echo 1. When the prompt asks "? Log in to Vercel", press Enter.
echo 2. Your web browser will open automatically.
echo 3. Click "Authorize" or log in using your GitHub account.
echo.
echo Press any key to start...
pause > nul

echo.
"C:\Program Files\nodejs\npx.cmd" vercel login

echo.
echo ===================================================
echo   Login completed! You can close this window.
echo   Please reply "logged in" in the chat.
echo ===================================================
echo.
pause
