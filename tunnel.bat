@echo off
title ProGol CR — Tunnel Publico
echo.
echo ============================================================
echo   ProGol CR — Acceso Publico (cualquier red / celular)
echo ============================================================
echo.
echo Iniciando servidor + tunnel publico...
echo Esto puede tardar 10-20 segundos en generar el link.
echo.
echo IMPORTANTE: Deja esta ventana abierta mientras clients usan la app.
echo Para cerrar: presiona Ctrl+C
echo.

cd /d "%~dp0"
python server.py --tunnel

pause
