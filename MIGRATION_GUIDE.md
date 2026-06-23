# ProGolCR — Guía de Migración a Linux

**Destino:** Ubuntu 24.04 LTS Desktop en VM  
**Tiempo estimado:** 45–60 minutos  
**Preparado:** 2026-06-16

---

## Requisitos de la VM

| Recurso | Valor |
|---|---|
| **OS** | Ubuntu 24.04 LTS Desktop (64-bit) |
| **CPU** | 4 cores (mínimo 2) |
| **RAM** | 8 GB (mínimo 4 GB) |
| **Disco** | 80 GB SSD (mínimo 40 GB) |
| **Red** | Adaptador en modo Bridged (para acceso LAN) |
| **Display** | Resolución mínima 1024×768 |

**Descargar ISO:** [ubuntu.com/download/desktop](https://ubuntu.com/download/desktop)  
Archivo: `ubuntu-24.04.x-desktop-amd64.iso`

---

## PASO 1 — Crear la VM

En VMware / VirtualBox / Hyper-V:
1. Nueva VM → Linux → Ubuntu 64-bit
2. 4 CPUs, 8 GB RAM, 80 GB disco (VDI/VMDK dinámico)
3. Red: **Bridged Adapter** (necesario para LAN y localtunnel)
4. Habilitar aceleración 3D si está disponible
5. Montar ISO y arrancar → instalar Ubuntu Desktop normalmente
6. Usuario durante instalación: `progolcr` / password fuerte
7. Marcar "Iniciar sesión automáticamente"

---

## PASO 2 — Setup inicial (en la VM)

Abre una terminal en la VM:

```bash
# Descargar el repo (o copiar via USB/SCP)
git clone <tu-repo-url> /home/progolcr/worldcup-warroom
cd /home/progolcr/worldcup-warroom

# O si no tienes git configurado aún, copiar desde Windows:
# En Windows (PowerShell):
# scp -r C:\Users\esteb\worldcup-warroom progolcr@<IP-VM>:/home/progolcr/
```

Luego ejecutar el setup:
```bash
cd /home/progolcr/worldcup-warroom
bash scripts/setup_linux.sh
```

Esto instala: Python 3.12, Node 20, Chrome, localtunnel, ufw, fail2ban, cron, logrotate.

---

## PASO 3 — Copiar archivos sensibles (NO están en git)

**En Windows (PowerShell)**, desde `C:\Users\esteb\worldcup-warroom`:

```powershell
# Obtener IP de la VM primero (en la VM: ip addr show)
$VM_IP = "192.168.x.x"   # cambiar por la IP real

# Copiar archivos sensibles via SCP
scp config.json                       progolcr@${VM_IP}:/home/progolcr/worldcup-warroom/
scp data/users.json                   progolcr@${VM_IP}:/home/progolcr/worldcup-warroom/data/
scp data/players_stats.json           progolcr@${VM_IP}:/home/progolcr/worldcup-warroom/data/
scp data/elo_overrides.json           progolcr@${VM_IP}:/home/progolcr/worldcup-warroom/data/
scp data/brier_scores.json            progolcr@${VM_IP}:/home/progolcr/worldcup-warroom/data/
scp data/calibration_log.json         progolcr@${VM_IP}:/home/progolcr/worldcup-warroom/data/
scp data/wc2026_tournament_stats.json progolcr@${VM_IP}:/home/progolcr/worldcup-warroom/data/
scp data/wc2026_squads.json           progolcr@${VM_IP}:/home/progolcr/worldcup-warroom/data/
```

⚠️ **NUNCA** copiar estos archivos por email, Telegram, WhatsApp o pastebin.

---

## PASO 4 — Security hardening (en la VM, como root)

```bash
sudo bash /home/progolcr/worldcup-warroom/scripts/setup_linux_hardening.sh
```

Esto configura: UFW firewall, SSH sin passwords, fail2ban, sysctl kernel hardening, ClamAV, actualizaciones automáticas.

⚠️ **IMPORTANTE:** Antes de activar SSH sin passwords, agrega tu clave pública:
```bash
mkdir -p ~/.ssh
# Pegar aquí tu clave pública (la de tu PC Windows):
# cat >> ~/.ssh/authorized_keys
chmod 700 ~/.ssh && chmod 600 ~/.ssh/authorized_keys
```

---

## PASO 5 — Instalar servicio y cron jobs

```bash
cd /home/progolcr/worldcup-warroom

# Instalar como servicio systemd (arranca al boot)
sudo cp progolcr.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable progolcr
sudo systemctl start progolcr

# Instalar cron jobs de automatización
bash scripts/setup_crontab.sh
```

---

## PASO 6 — Verificar migración

```bash
bash /home/progolcr/worldcup-warroom/scripts/migrate_from_windows.sh
```

Esto verifica: archivos presentes, config.json con keys, imports Python, smoke test del servidor, servicios activos, cron jobs.

**Esperado:** 0 errores, algunos avisos menores aceptables.

---

## PASO 7 — Arrancar localtunnel (URL pública)

```bash
# Arrancar localtunnel (en background)
nohup lt --port 8765 --subdomain progolcr > /home/progolcr/worldcup-warroom/logs/tunnel.log 2>&1 &

# Ver la URL
cat /home/progolcr/worldcup-warroom/logs/tunnel.log
```

La URL será algo como: `https://progolcr.loca.lt`

---

## PASO 8 — Verificar todo funciona

1. Abrir Chrome en la VM → `http://127.0.0.1:8765`
2. Login con DeadRyder / Samuel2024!
3. Verificar que aparecen partidos del día
4. Probar chat con Ryder
5. Verificar URL pública desde el celular

---

## Post-migración

Una vez confirmado que todo funciona en Linux:
- Detener el server en Windows
- El server de Windows puede quedar como backup

### Estructura de logs en Linux
```
/home/progolcr/worldcup-warroom/logs/
  server.log              ← servidor principal
  server_error.log        ← errores del servidor
  fetch_player_stats.log  ← pipeline stats jugadores (2am)
  recalibrate.log         ← calibración Elo (4am)
  wc2026_stats.log        ← stats torneo (cada 3h)
  calibration.log         ← calibración diaria medianoche
  tunnel.log              ← localtunnel URL
```

### Comandos útiles diarios
```bash
# Estado del servidor
sudo systemctl status progolcr

# Ver logs en tiempo real
tail -f /home/progolcr/worldcup-warroom/logs/server.log

# Reiniciar servidor
sudo systemctl restart progolcr

# Ver cron jobs
crontab -l

# Estado del firewall
sudo ufw status verbose

# Ver procesos de ProGolCR
ps aux | grep python
```

---

## Archivos creados para esta migración

| Archivo | Propósito |
|---|---|
| `scripts/setup_linux.sh` | Instala todo el stack de software |
| `scripts/setup_linux_hardening.sh` | Security hardening completo |
| `scripts/setup_crontab.sh` | Instala los 4 cron jobs de automatización |
| `scripts/migrate_from_windows.sh` | Verificación post-migración |
| `progolcr.service` | Servicio systemd (auto-start en boot) |
| `MIGRATION_GUIDE.md` | Esta guía |

---

*Preparado automáticamente por Claude Code — 2026-06-16*
