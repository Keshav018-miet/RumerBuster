@echo off
title RumorBuster Server & Cloudflare Tunnel
echo ========================================================
echo Starting RumorBuster Flask Server and Cloudflare Tunnel...
echo ========================================================
cd /d "%~dp0"

echo [1/2] Starting Flask Backend...
start "RumorBuster Flask Backend" cmd /k "python app.py"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Cloudflare Public Tunnel...
start "Cloudflare Tunnel" cmd /k "cloudflared_new.exe tunnel --url http://127.0.0.1:5000"

echo.
echo Both Flask and Cloudflare Tunnel are now running!
echo Check the Cloudflare Tunnel terminal window for your live URL.
pause
