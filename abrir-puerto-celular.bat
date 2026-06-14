@echo off
echo ===================================================
echo   ProGol CR -- Abrir acceso desde celular
echo ===================================================
echo.
netsh advfirewall firewall delete rule name="ProGolCR-8765" >nul 2>&1
netsh advfirewall firewall add rule name="ProGolCR-8765" dir=in action=allow protocol=TCP localport=8765
if %errorlevel%==0 (
    echo [OK] Puerto 8765 abierto en el firewall de Windows
) else (
    echo [ERROR] Ejecuta este archivo como Administrador:
    echo         clic derecho → "Ejecutar como administrador"
    pause
    exit /b 1
)
echo.
echo Ahora desde el celular (misma WiFi) ve a:
for /f "tokens=2 delims=:" %%a in ('ipconfig ^| findstr /i "IPv4"') do (
    set ip=%%a
    set ip=!ip: =!
    echo   http://!ip!:8765
)
echo.
echo Si no ves la IP arriba, busca tu IP en Configuracion de Red
echo y ve a   http://TU_IP:8765   desde el celular.
echo.
pause
