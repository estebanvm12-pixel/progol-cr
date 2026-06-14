@echo off
:: ProGol CR — Configurar inicio automático con Windows
:: Ejecutar como Administrador

title ProGol CR — Setup Autostart
echo.
echo ============================================================
echo   ProGol CR — Configurando inicio automatico con Windows
echo ============================================================
echo.

:: Get the project root (one level above scripts/)
set "APP_DIR=%~dp0.."
for %%I in ("%APP_DIR%") do set "APP_DIR=%%~fI"
set "PYTHON_EXE="

:: Find Python
for %%P in (python.exe) do set "PYTHON_EXE=%%~$PATH:P"
if "%PYTHON_EXE%"=="" (
    echo ERROR: Python no encontrado en PATH.
    echo Instala Python desde https://www.python.org y vuelve a intentar.
    pause
    exit /b 1
)

echo Python encontrado: %PYTHON_EXE%
echo Directorio app:   %APP_DIR%
echo.

:: Create the scheduled task XML
set "TASK_XML=%TEMP%\progol_autostart.xml"

(
echo ^<?xml version="1.0" encoding="UTF-16"?^>
echo ^<Task version="1.2" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task"^>
echo   ^<Triggers^>
echo     ^<LogonTrigger^>
echo       ^<Enabled^>true^</Enabled^>
echo       ^<Delay^>PT30S^</Delay^>
echo     ^</LogonTrigger^>
echo   ^</Triggers^>
echo   ^<Principals^>
echo     ^<Principal id="Author"^>
echo       ^<LogonType^>InteractiveToken^</LogonType^>
echo       ^<RunLevel^>HighestAvailable^</RunLevel^>
echo     ^</Principal^>
echo   ^</Principals^>
echo   ^<Settings^>
echo     ^<MultipleInstancesPolicy^>IgnoreNew^</MultipleInstancesPolicy^>
echo     ^<DisallowStartIfOnBatteries^>false^</DisallowStartIfOnBatteries^>
echo     ^<StopIfGoingOnBatteries^>false^</StopIfGoingOnBatteries^>
echo     ^<ExecutionTimeLimit^>PT0S^</ExecutionTimeLimit^>
echo     ^<Priority^>7^</Priority^>
echo   ^</Settings^>
echo   ^<Actions^>
echo     ^<Exec^>
echo       ^<Command^>%PYTHON_EXE%^</Command^>
echo       ^<Arguments^>"%APP_DIR%\server.py" --tunnel^</Arguments^>
echo       ^<WorkingDirectory^>%APP_DIR%^</WorkingDirectory^>
echo     ^</Exec^>
echo   ^</Actions^>
echo ^</Task^>
) > "%TASK_XML%"

:: Register the task
schtasks /Create /TN "ProGolCR_Autostart" /XML "%TASK_XML%" /F
if %ERRORLEVEL% EQU 0 (
    echo.
    echo ============================================================
    echo   LISTO! ProGol CR arrancara automaticamente al encender la PC.
    echo.
    echo   Cada vez que inicies sesion en Windows:
    echo     1. Espera 30 segundos
    echo     2. El servidor arranca con tunnel publico
    echo     3. Ryder te envia el link por WhatsApp automaticamente
    echo ============================================================
) else (
    echo.
    echo ERROR al registrar la tarea. Asegurate de ejecutar este .bat
    echo como Administrador (clic derecho → Ejecutar como administrador).
)

del "%TASK_XML%" 2>nul
echo.
pause
