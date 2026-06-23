#!/bin/bash
# ============================================================
# ProGolCR — Linux VM Setup Script
# Ubuntu 24.04 LTS Desktop
# Ejecutar como: bash setup_linux.sh
# ============================================================
set -e

PROGOL_USER="progolcr"
PROGOL_DIR="/home/$PROGOL_USER/worldcup-warroom"
LOGFILE="/tmp/progolcr_setup.log"

log() { echo "[$(date '+%H:%M:%S')] $*" | tee -a "$LOGFILE"; }

log "=== ProGolCR Linux Setup ==="
log "Usuario: $PROGOL_USER | Directorio: $PROGOL_DIR"

# ── 0. Crear usuario si no existe ────────────────────────────
if ! id "$PROGOL_USER" &>/dev/null; then
    log "Creando usuario $PROGOL_USER..."
    sudo useradd -m -s /bin/bash "$PROGOL_USER"
    sudo usermod -aG sudo "$PROGOL_USER"
    log "  OK — usuario creado (sin password; acceso solo por SSH key)"
else
    log "  Usuario $PROGOL_USER ya existe — OK"
fi

# ── 1. Sistema base ─────────────────────────────────────────
log "[1] Actualizando sistema..."
sudo apt update -qq && sudo apt upgrade -y -qq
sudo apt install -y -qq \
    curl wget git unzip zip \
    python3.12 python3.12-venv python3-pip python3.12-dev \
    build-essential libssl-dev libffi-dev \
    ufw cron fail2ban \
    openssh-server \
    fonts-liberation libappindicator3-1 libasound2 libatk-bridge2.0-0 \
    libatk1.0-0 libcups2 libdbus-1-3 libgdk-pixbuf2.0-0 libnspr4 libnss3 \
    libx11-xcb1 libxcomposite1 libxdamage1 libxrandr2 xdg-utils \
    xvfb x11vnc net-tools htop jq
log "  OK — paquetes base instalados"

# ── 2. Python — alias python3.12 -> python3 ─────────────────
log "[2] Configurando Python..."
sudo update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.12 1
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3.12 1
python --version
log "  OK"

# ── 3. Node.js 20 + localtunnel ─────────────────────────────
log "[3] Instalando Node.js 20 + localtunnel..."
if ! command -v node &>/dev/null; then
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash - >> "$LOGFILE" 2>&1
    sudo apt install -y -qq nodejs
fi
node --version
sudo npm install -g localtunnel >> "$LOGFILE" 2>&1
lt --version
log "  OK"

# ── 4. Google Chrome (estable) ──────────────────────────────
log "[4] Instalando Google Chrome..."
if ! command -v google-chrome &>/dev/null; then
    CHROME_DEB="/tmp/google-chrome-stable.deb"
    wget -q "https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb" -O "$CHROME_DEB"
    sudo dpkg -i "$CHROME_DEB" >> "$LOGFILE" 2>&1 || sudo apt -f install -y -qq
    rm -f "$CHROME_DEB"
fi
google-chrome --version
log "  OK"

# ── 5. Crear directorio de proyecto ─────────────────────────
log "[5] Preparando directorio del proyecto..."
sudo mkdir -p "$PROGOL_DIR"
sudo chown -R "$PROGOL_USER:$PROGOL_USER" "/home/$PROGOL_USER"
# Crear subdirectorios que el server espera
sudo -u "$PROGOL_USER" mkdir -p \
    "$PROGOL_DIR/data" \
    "$PROGOL_DIR/logs" \
    "$PROGOL_DIR/frontend" \
    "$PROGOL_DIR/scripts" \
    "$PROGOL_DIR/analysis" \
    "$PROGOL_DIR/brand"
log "  OK — $PROGOL_DIR listo"

# ── 6. Variables de entorno (no guardar keys en .bashrc) ─────
log "[6] Configurando entorno..."
PROFILE_D="/etc/profile.d/progolcr.sh"
sudo tee "$PROFILE_D" > /dev/null <<'EOF'
# ProGolCR environment
export PROGOLCR_DIR="/home/progolcr/worldcup-warroom"
export PYTHONPATH="$PROGOLCR_DIR:$PYTHONPATH"
export PYTHONDONTWRITEBYTECODE=1
export PYTHONUNBUFFERED=1
EOF
source "$PROFILE_D"
log "  OK"

# ── 7. Instalar servicio systemd ─────────────────────────────
log "[7] Instalando servicio systemd..."
if [ -f "$PROGOL_DIR/progolcr.service" ]; then
    sudo cp "$PROGOL_DIR/progolcr.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl enable progolcr.service
    log "  OK — servicio habilitado (arranca al boot)"
else
    log "  AVISO — progolcr.service no encontrado, instalar manualmente después de copiar archivos"
fi

# ── 8. Cron jobs ────────────────────────────────────────────
log "[8] Instalando cron jobs..."
if [ -f "$PROGOL_DIR/scripts/setup_crontab.sh" ]; then
    sudo -u "$PROGOL_USER" bash "$PROGOL_DIR/scripts/setup_crontab.sh"
    log "  OK — cron jobs instalados"
else
    log "  AVISO — setup_crontab.sh no encontrado, instalar después de copiar archivos"
fi

# ── 9. Logs directory con logrotate ─────────────────────────
log "[9] Configurando logrotate..."
sudo tee /etc/logrotate.d/progolcr > /dev/null <<EOF
$PROGOL_DIR/logs/*.log {
    daily
    rotate 14
    compress
    missingok
    notifempty
    create 0640 $PROGOL_USER $PROGOL_USER
}
EOF
log "  OK"

# ── Resumen ──────────────────────────────────────────────────
echo ""
echo "=============================================="
echo "  ProGolCR Setup completado"
echo "=============================================="
echo "  Python:      $(python --version 2>&1)"
echo "  Node:        $(node --version)"
echo "  Chrome:      $(google-chrome --version)"
echo "  Proyecto:    $PROGOL_DIR"
echo ""
echo "  SIGUIENTE PASO:"
echo "  1. Copiar archivos del proyecto (ver MIGRATION_GUIDE.md)"
echo "  2. Copiar config.json y data/ via SCP"
echo "  3. bash $PROGOL_DIR/scripts/setup_linux_hardening.sh"
echo "  4. bash $PROGOL_DIR/scripts/migrate_from_windows.sh"
echo "  5. sudo systemctl start progolcr"
echo "=============================================="
echo ""
log "Setup completado. Ver $LOGFILE para detalles."
