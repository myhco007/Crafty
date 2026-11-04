@echo off
title CraftyKids - Starting Presentation Servers...
color 0A

echo ========================================================
echo        CRAFTYKIDS CAPSTONE PRESENTATION LAUNCHER
echo ========================================================
echo.
echo [1/2] Starting Django Development Server on port 8000...
start "CraftyKids - Django Server" cmd /k "cd /d "C:\CRAFTY CAPSTONE SYSTEM\Crafty" && ..\.venv\Scripts\python.exe manage.py runserver 8000"

timeout /t 3 /nobreak >nul

echo [2/2] Starting Cloudflare Public Tunnel...
start "CraftyKids - Cloudflare Tunnel (Look for link here)" cmd /k "cd /d "C:\CRAFTY CAPSTONE SYSTEM\Crafty" && cloudflared.exe tunnel --url http://localhost:8000"

echo.
echo ========================================================
echo Both servers have been launched in separate windows!
echo Check the "CraftyKids - Cloudflare Tunnel" window to copy your public presentation link!
echo Keep both windows OPEN during your presentation.
echo ========================================================
pause
