@echo off
title ProGol CR
cd /d "%~dp0\.."
echo Iniciando ProGol CR...
echo Abre http://127.0.0.1:8765 en tu navegador
echo Presiona Ctrl+C para detener.
echo.
python server.py
pause
