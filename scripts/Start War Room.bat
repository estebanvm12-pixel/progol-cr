@echo off
title World Cup 2026 - War Room
cd /d "%~dp0"
echo Starting the World Cup 2026 War Room...
echo A browser window will open at http://127.0.0.1:8765
echo Close this window (or press Ctrl+C) to stop the app.
echo.
python server.py
pause
