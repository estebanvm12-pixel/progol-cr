#!/bin/bash
# ============================================================
# ProGolCR — Linux Security Hardening
# Equivalente de security_hardening_admin.ps1 para Ubuntu 24.04
# Ejecutar como: sudo bash setup_linux_hardening.sh
# ============================================================
set -e

log() { echo "[$(date '+%H:%M:%S')] $*"; }

if [ "$EUID" -ne 0 ]; then
    echo "ERROR: Ejecutar como root: sudo bash $0"
    exit 1
fi

log "=== ProGolCR Linux Security Hardening ==="

# ── 1. UFW Firewall ─────────────────────────────────────────
log "[1] Configurando UFW firewall..."
ufw --force reset
ufw default deny incoming
ufw default allow outgoing

# SSH — solo desde LAN (cambiar IP si es diferente)
ufw allow from 192.168.0.0/16 to any port 22 proto tcp comment "SSH LAN only"
# ProGolCR server — solo localhost (localtunnel maneja externo)
ufw allow from 127.0.0.1 to any port 8765 proto tcp comment "ProGolCR localhost"
# Bloquear acceso externo directo al servidor
ufw deny 8765/tcp comment "Block direct external access"
ufw deny 8501/tcp comment "Block Streamlit"

ufw --force enable
ufw status verbose
log "  OK — Firewall configurado"

# ── 2. SSH Hardening ─────────────────────────────────────────
log "[2] Endureciendo SSH..."
SSHD="/etc/ssh/sshd_config"
cp "$SSHD" "${SSHD}.backup.$(date +%Y%m%d)"

# Deshabilitar login por password (solo SSH keys)
sed -i 's/^#*PasswordAuthentication.*/PasswordAuthentication no/' "$SSHD"
sed -i 's/^#*PermitRootLogin.*/PermitRootLogin no/' "$SSHD"
sed -i 's/^#*X11Forwarding.*/X11Forwarding no/' "$SSHD"
sed -i 's/^#*MaxAuthTries.*/MaxAuthTries 3/' "$SSHD"
sed -i 's/^#*LoginGraceTime.*/LoginGraceTime 20/' "$SSHD"

# Si no existe ClientAliveInterval, agregarlo
grep -q "ClientAliveInterval" "$SSHD" || echo "ClientAliveInterval 300" >> "$SSHD"
grep -q "ClientAliveCountMax" "$SSHD" || echo "ClientAliveCountMax 2" >> "$SSHD"

systemctl restart ssh
log "  OK — SSH endurecido (solo key auth)"

# ── 3. Fail2ban — brute force protection ─────────────────────
log "[3] Configurando fail2ban..."
apt install -y -qq fail2ban

cat > /etc/fail2ban/jail.local <<'EOF'
[DEFAULT]
bantime  = 900
findtime = 300
maxretry = 5
backend  = systemd

[sshd]
enabled = true
port    = 22
filter  = sshd
logpath = /var/log/auth.log
maxretry = 3
bantime  = 3600
EOF

systemctl enable fail2ban
systemctl restart fail2ban
log "  OK — fail2ban activo (SSH: 3 intentos, ban 1h)"

# ── 4. Deshabilitar servicios innecesarios ───────────────────
log "[4] Desactivando servicios no necesarios..."
DISABLE_SERVICES=(
    "cups"        # impresoras
    "avahi-daemon" # mDNS/Bonjour
    "bluetooth"
    "whoopsie"    # Ubuntu crash reporter
    "apport"      # crash reporter
)
for svc in "${DISABLE_SERVICES[@]}"; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        systemctl stop "$svc" && systemctl disable "$svc"
        log "  Desactivado: $svc"
    fi
done
log "  OK"

# ── 5. Kernel hardening (sysctl) ────────────────────────────
log "[5] Hardening del kernel (sysctl)..."
cat > /etc/sysctl.d/99-progolcr.conf <<'EOF'
# Protección contra IP spoofing
net.ipv4.conf.all.rp_filter = 1
net.ipv4.conf.default.rp_filter = 1

# Ignorar ICMP broadcast
net.ipv4.icmp_echo_ignore_broadcasts = 1

# Protección SYN flood
net.ipv4.tcp_syncookies = 1
net.ipv4.tcp_max_syn_backlog = 2048
net.ipv4.tcp_synack_retries = 2

# No aceptar ICMP redirects
net.ipv4.conf.all.accept_redirects = 0
net.ipv6.conf.all.accept_redirects = 0

# No enviar ICMP redirects
net.ipv4.conf.all.send_redirects = 0

# Deshabilitar IPv6 si no se usa
net.ipv6.conf.all.disable_ipv6 = 1
net.ipv6.conf.default.disable_ipv6 = 1

# Protección contra buffer overflow básico
kernel.randomize_va_space = 2
EOF
sysctl -p /etc/sysctl.d/99-progolcr.conf >> /dev/null
log "  OK"

# ── 6. Permisos de archivos críticos ────────────────────────
log "[6] Securizando permisos de archivos ProGolCR..."
PROGOL_DIR="/home/progolcr/worldcup-warroom"
if [ -d "$PROGOL_DIR" ]; then
    chmod 750 "$PROGOL_DIR"
    # config.json y users.json: solo el usuario progolcr
    [ -f "$PROGOL_DIR/config.json" ]       && chmod 600 "$PROGOL_DIR/config.json"
    [ -f "$PROGOL_DIR/data/users.json" ]   && chmod 600 "$PROGOL_DIR/data/users.json"
    [ -d "$PROGOL_DIR/data" ]              && chmod 750 "$PROGOL_DIR/data"
    [ -d "$PROGOL_DIR/logs" ]              && chmod 750 "$PROGOL_DIR/logs"
    chown -R progolcr:progolcr "$PROGOL_DIR"
    log "  OK — permisos aplicados"
else
    log "  AVISO — $PROGOL_DIR no encontrado aún, aplicar permisos después de copiar archivos"
fi

# ── 7. Automatic security updates ───────────────────────────
log "[7] Activando actualizaciones de seguridad automáticas..."
apt install -y -qq unattended-upgrades
cat > /etc/apt/apt.conf.d/50unattended-upgrades <<'EOF'
Unattended-Upgrade::Allowed-Origins {
    "${distro_id}:${distro_codename}-security";
};
Unattended-Upgrade::AutoFixInterruptedDpkg "true";
Unattended-Upgrade::MinimalSteps "true";
Unattended-Upgrade::Remove-Unused-Dependencies "true";
Unattended-Upgrade::Automatic-Reboot "false";
EOF
systemctl enable unattended-upgrades
log "  OK — actualizaciones de seguridad automáticas"

# ── 8. Iniciar Windows Defender equiv: ClamAV ───────────────
log "[8] Instalando ClamAV (antivirus)..."
apt install -y -qq clamav clamav-daemon
systemctl stop clamav-freshclam 2>/dev/null || true
freshclam --quiet 2>/dev/null || log "  AVISO — freshclam necesita conexión para actualizar firmas"
systemctl enable clamav-daemon
systemctl start clamav-daemon 2>/dev/null || true
log "  OK — ClamAV instalado"

# ── Resumen ──────────────────────────────────────────────────
echo ""
echo "=============================================="
echo "  ProGolCR Security Hardening completado"
echo "=============================================="
echo "  Firewall (UFW):     $(ufw status | head -1)"
echo "  fail2ban:           $(systemctl is-active fail2ban)"
echo "  SSH password auth:  DESACTIVADO (solo keys)"
echo "  Kernel sysctl:      APLICADO"
echo ""
echo "  IMPORTANTE:"
echo "  - SSH solo acepta claves. Agrega tu clave publica a:"
echo "    /home/progolcr/.ssh/authorized_keys"
echo "    antes de cerrar esta sesión."
echo "=============================================="
