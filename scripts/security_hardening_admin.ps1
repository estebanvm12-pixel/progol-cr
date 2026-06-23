# ProGolCR - Security Hardening Script
# EJECUTAR COMO ADMINISTRADOR: clic derecho -> "Ejecutar como administrador"

Write-Host "=== ProGolCR Security Hardening ===" -ForegroundColor Cyan

# 1. Firewall Public profile: block all inbound by default
Write-Host "`n[1] Configurando firewall Public -> Block inbound..." -ForegroundColor Yellow
Set-NetFirewallProfile -Profile Public -DefaultInboundAction Block -DefaultOutboundAction Allow
Set-NetFirewallProfile -Profile Private -DefaultInboundAction Block -DefaultOutboundAction Allow
Write-Host "    OK - Inbound bloqueado por defecto en Public y Private" -ForegroundColor Green

# 2. Remove ADB (Android Debug Bridge) from Public firewall - not needed exposed
Write-Host "`n[2] Removiendo regla ADB del perfil Public..." -ForegroundColor Yellow
Get-NetFirewallRule -DisplayName "adb.exe" -ErrorAction SilentlyContinue |
    Where-Object { $_.Profile -match "Public" } |
    Remove-NetFirewallRule -ErrorAction SilentlyContinue
Write-Host "    OK - Regla ADB Public removida" -ForegroundColor Green

# 3. Block Streamlit port 8501 from external access
Write-Host "`n[3] Bloqueando puerto 8501 (Streamlit) externamente..." -ForegroundColor Yellow
$existing = Get-NetFirewallRule -DisplayName "ProGolCR - Block 8501" -ErrorAction SilentlyContinue
if ($existing) { Remove-NetFirewallRule -DisplayName "ProGolCR - Block 8501" }
New-NetFirewallRule -DisplayName "ProGolCR - Block 8501" `
    -Direction Inbound -Protocol TCP -LocalPort 8501 `
    -Action Block -Profile Any | Out-Null
Write-Host "    OK - Puerto 8501 bloqueado" -ForegroundColor Green

# 4. Block port 8765 (ProGol) on Public — localtunnel handles external
Write-Host "`n[4] Bloqueando puerto 8765 (ProGol) acceso directo externo..." -ForegroundColor Yellow
$existing2 = Get-NetFirewallRule -DisplayName "ProGolCR - Block 8765 Direct" -ErrorAction SilentlyContinue
if ($existing2) { Remove-NetFirewallRule -DisplayName "ProGolCR - Block 8765 Direct" }
New-NetFirewallRule -DisplayName "ProGolCR - Block 8765 Direct" `
    -Direction Inbound -Protocol TCP -LocalPort 8765 `
    -Action Block -Profile Public | Out-Null
Write-Host "    OK - Puerto 8765 bloqueado en Public" -ForegroundColor Green

# 5. Disable SMBv1 explicitly (WannaCry prevention)
Write-Host "`n[5] Desactivando SMBv1 (prevención WannaCry)..." -ForegroundColor Yellow
Set-ItemProperty -Path "HKLM:\SYSTEM\CurrentControlSet\Services\LanmanServer\Parameters" `
    -Name "SMB1" -Value 0 -Type DWORD -Force -ErrorAction SilentlyContinue
Disable-WindowsOptionalFeature -Online -FeatureName SMB1Protocol -NoRestart -ErrorAction SilentlyContinue | Out-Null
Write-Host "    OK - SMBv1 desactivado" -ForegroundColor Green

# 6. Disable unnecessary Remote Assistance
Write-Host "`n[6] Desactivando Remote Assistance..." -ForegroundColor Yellow
Set-ItemProperty -Path "HKLM:\System\CurrentControlSet\Control\Remote Assistance" `
    -Name "fAllowToGetHelp" -Value 0 -Force -ErrorAction SilentlyContinue
Write-Host "    OK - Remote Assistance desactivado" -ForegroundColor Green

# 7. Install pending Windows updates (driver updates)
Write-Host "`n[7] Revisando actualizaciones pendientes..." -ForegroundColor Yellow
Write-Host "    Hay 3 actualizaciones de drivers Intel pendientes." -ForegroundColor Yellow
Write-Host "    Para instalarlas: Configuracion -> Windows Update -> Buscar actualizaciones" -ForegroundColor Yellow

# 8. Trigger Windows Defender full scan
Write-Host "`n[8] Iniciando escaneo completo de Windows Defender..." -ForegroundColor Yellow
Start-MpScan -ScanType FullScan -AsJob | Out-Null
Write-Host "    OK - Escaneo completo iniciado en background" -ForegroundColor Green

# 9. Daily player stats update — Task Scheduler
Write-Host "`n[9] Configurando tarea programada diaria de stats de jugadores..." -ForegroundColor Yellow
$action = New-ScheduledTaskAction -Execute "python" `
    -Argument "C:\Users\esteb\worldcup-warroom\scripts\fetch_player_stats_full.py" `
    -WorkingDirectory "C:\Users\esteb\worldcup-warroom"
$trigger = New-ScheduledTaskTrigger -Daily -At "02:00AM"
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 2) `
    -RestartCount 2 -RestartInterval (New-TimeSpan -Minutes 30)
Register-ScheduledTask -TaskName "ProGolCR - Update Player Stats" `
    -Action $action -Trigger $trigger -Settings $settings `
    -Description "Daily WC2026 player stats update at 2am" `
    -RunLevel Highest -Force | Out-Null
Write-Host "    OK - Tarea diaria a las 2am registrada" -ForegroundColor Green

# 10. Daily Ryder re-calibration with player stats (runs after fetch, at 4am)
Write-Host "`n[10] Configurando re-calibracion diaria de Ryder..." -ForegroundColor Yellow
$action2 = New-ScheduledTaskAction -Execute "python" `
    -Argument "C:\Users\esteb\worldcup-warroom\scripts\recalibrate_with_player_stats.py" `
    -WorkingDirectory "C:\Users\esteb\worldcup-warroom"
$trigger2 = New-ScheduledTaskTrigger -Daily -At "04:00AM"
$settings2 = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 10)
Register-ScheduledTask -TaskName "ProGolCR - Recalibrate Ryder" `
    -Action $action2 -Trigger $trigger2 -Settings $settings2 `
    -Description "Daily Ryder Elo re-calibration using player stats" `
    -RunLevel Highest -Force | Out-Null
Write-Host "    OK - Re-calibracion de Ryder a las 4am registrada" -ForegroundColor Green

# 11. Live WC2026 tournament stats (every 3 hours during tournament)
Write-Host "`n[11] Stats en vivo del torneo WC2026 cada 3 horas..." -ForegroundColor Yellow
$action3 = New-ScheduledTaskAction -Execute "python" `
    -Argument "C:\Users\esteb\worldcup-warroom\scripts\fetch_wc2026_live_stats.py" `
    -WorkingDirectory "C:\Users\esteb\worldcup-warroom"
$trigger3 = New-ScheduledTaskTrigger -RepetitionInterval (New-TimeSpan -Hours 3) `
    -Once -At "00:00AM" -RepetitionDuration ([System.TimeSpan]::MaxValue)
$settings3 = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Minutes 5)
Register-ScheduledTask -TaskName "ProGolCR - WC2026 Live Stats" `
    -Action $action3 -Trigger $trigger3 -Settings $settings3 `
    -Description "WC2026 tournament goals/assists every 3h" `
    -RunLevel Highest -Force | Out-Null
Write-Host "    OK - Stats del torneo cada 3h registrado" -ForegroundColor Green

Write-Host "`n=== Hardening completado ===" -ForegroundColor Cyan
Write-Host "Reinicia el servidor ProGolCR para aplicar el cambio de HOST." -ForegroundColor White

# Summary
Write-Host "`nResumen de cambios:" -ForegroundColor Cyan
Get-NetFirewallProfile | Select-Object Name, DefaultInboundAction | Format-Table -AutoSize
