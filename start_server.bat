@echo off
title Smart WiFi Bandwidth Sharing - Server
cd /d "%~dp0"

echo ============================================
echo   Smart WiFi Bandwidth Sharing - Server
echo   Logs: server.log in this folder
echo   Keep this window open (minimized is fine)
echo ============================================

:loop
".venv\Scripts\python.exe" -m backend.app >> "%~dp0server.log" 2>&1
echo [%date% %time%] Server stopped unexpectedly. Restarting in 5 seconds... >> "%~dp0server.log"
timeout /t 5 /nobreak >nul
goto loop