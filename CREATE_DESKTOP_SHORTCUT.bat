@echo off
cd /d "%~dp0"

rem ============================================================
rem   Run this ONCE - it puts a "Smart WiFi App" shortcut on
rem   your Desktop. After that, just double-click the desktop
rem   icon any time to launch the app with both links.
rem ============================================================

powershell -NoProfile -Command "$ws = New-Object -ComObject WScript.Shell; $lnk = $ws.CreateShortcut([Environment]::GetFolderPath('Desktop') + '\Smart WiFi App.lnk'); $lnk.TargetPath = '%~dp0START_APP.bat'; $lnk.WorkingDirectory = '%~dp0'; $lnk.Description = 'Launch Smart WiFi Bandwidth Sharing (localhost + network)'; $lnk.Save()"

if exist "%USERPROFILE%\Desktop\Smart WiFi App.lnk" (
    echo.
    echo   [OK] Desktop shortcut created:  "Smart WiFi App"
    echo        Double-click it any time to start the app.
) else if exist "%OneDrive%\Desktop\Smart WiFi App.lnk" (
    echo.
    echo   [OK] Desktop shortcut created:  "Smart WiFi App"
    echo        Double-click it any time to start the app.
) else (
    echo.
    echo   [!] Could not verify shortcut. Check your Desktop.
)

echo.
pause