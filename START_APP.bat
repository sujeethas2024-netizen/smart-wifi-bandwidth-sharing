@echo off
title Smart WiFi Bandwidth Sharing
cd /d "%~dp0"

rem ============================================================
rem   ONE-CLICK PERMANENT LAUNCHER
rem   * Auto-builds the frontend the first time only
rem   * Starts the server (website + API)
rem   * Shows PERMANENT links: localhost + WiFi network IP
rem   * Opens your browser automatically
rem   * Auto-restarts the server if it ever stops
rem ============================================================

echo.
echo   ==============================================
echo     SMART WIFI BANDWIDTH SHARING - LAUNCHER
echo   ==============================================
echo.

rem -- 1. Make sure the Python virtual environment exists ------
if not exist ".venv\Scripts\python.exe" (
    echo   [setup] Creating Python environment ^(first run only^)...
    python -m venv .venv
    if errorlevel 1 goto :error
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 goto :error
)

rem -- 2. Make sure the frontend is built -----------------------
if not exist "frontend\dist\index.html" (
    echo   [setup] Building frontend ^(first run only, 1-2 min^)...
    pushd frontend
    if not exist "node_modules" call npm install
    call npm run build
    if errorlevel 1 (popd & goto :error)
    popd
)

rem -- 3. Allow phones on the WiFi to reach the server ----------
rem     One-time admin prompt ONLY if the firewall rule is missing.
netsh advfirewall firewall show rule name="SmartWiFi-5000" >nul 2>&1
if errorlevel 1 (
    echo.
    echo   [one-time setup] Opening the firewall so phones can connect...
    echo   ^>^>^> Windows will show a permission popup - click YES ^<^<^<
    powershell -NoProfile -Command "Start-Process -FilePath '%~dp0_firewall_setup.bat' -Verb RunAs -Wait"
)

rem -- 4. Detect this PC's WiFi/LAN IP automatically ------------
set "LAN_IP="
for /f "delims=" %%i in ('.venv\Scripts\python.exe _lan_ip.py') do set "LAN_IP=%%i"
if not defined LAN_IP set "LAN_IP=127.0.0.1"

rem -- 5. Show the PERMANENT links ------------------------------
color 0A
echo.
echo   ==============================================================
echo                  YOUR LINKS  ^(always the same^)
echo   ==============================================================
echo.
echo      On this PC ........  http://localhost:5000
echo.
echo      On WiFi devices ...  http://%LAN_IP%:5000
echo                           ^(phone / laptop on same WiFi^)
echo.
echo   ==============================================================
echo      Tip: bookmark these links - they NEVER change.
echo      Keep this window open while using the app.
echo   ==============================================================
echo.

rem -- 6. Open the browser automatically ------------------------
rem     (small delay so the server is ready when the page loads)
timeout /t 2 /nobreak >nul
start "" "http://localhost:5000"

rem -- 7. Run the server (auto-restarts if it ever stops) -------
:loop
".venv\Scripts\python.exe" -m backend.app
echo.
echo   [%date% %time%]  Server stopped - restarting in 5 seconds...
timeout /t 5 /nobreak >nul
goto :loop

:error
color 0C
echo.
echo   [ERROR] Setup failed. Read the messages above.
echo   Common fixes: install Python from python.org, or Node.js
echo   from nodejs.org, then run this file again.
echo.
pause
exit /b 1