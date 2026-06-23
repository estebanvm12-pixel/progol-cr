#!/bin/bash
# ============================================================
# ProGolCR — Verificación post-migración desde Windows
# Ejecutar después de copiar todos los archivos
# bash migrate_from_windows.sh
# ============================================================

PROGOL_DIR="/home/progolcr/worldcup-warroom"
PASS=0
FAIL=0
WARN=0

ok()   { echo "  [OK]   $*"; ((PASS++)); }
fail() { echo "  [FAIL] $*"; ((FAIL++)); }
warn() { echo "  [WARN] $*"; ((WARN++)); }
hdr()  { echo ""; echo "── $* ──────────────────────────────────────"; }

echo "=========================================="
echo "  ProGolCR Migration Verification"
echo "  $(date)"
echo "=========================================="

# ── 1. Archivos críticos ─────────────────────────────────────
hdr "Archivos críticos"
REQUIRED_FILES=(
    "server.py"
    "model.py"
    "calibrator.py"
    "db.py"
    "config.json"
    "frontend/app.js"
    "frontend/styles.css"
    "frontend/index.html"
    "data/wc2026_squads.json"
    "data/users.json"
    "analysis/players.py"
)
for f in "${REQUIRED_FILES[@]}"; do
    if [ -f "$PROGOL_DIR/$f" ]; then
        ok "$f"
    else
        fail "$f — FALTANTE"
    fi
done

# Archivos opcionales (se regeneran)
OPTIONAL_FILES=(
    "data/players_stats.json"
    "data/elo_overrides.json"
    "data/brier_scores.json"
    "data/wc2026_tournament_stats.json"
    "data/calibration_log.json"
)
for f in "${OPTIONAL_FILES[@]}"; do
    if [ -f "$PROGOL_DIR/$f" ]; then
        ok "$f (datos persistidos)"
    else
        warn "$f — no encontrado (se regenerará)"
    fi
done

# ── 2. Config.json — verificar keys presentes ────────────────
hdr "Configuración (config.json)"
if [ -f "$PROGOL_DIR/config.json" ]; then
    REQUIRED_KEYS=("anthropic_api_key" "sportsdb_key" "email_password")
    for key in "${REQUIRED_KEYS[@]}"; do
        if python3 -c "import json; d=json.load(open('$PROGOL_DIR/config.json')); assert d.get('$key','').strip(), '$key vacío'" 2>/dev/null; then
            ok "config.$key presente"
        else
            fail "config.$key faltante o vacío"
        fi
    done
    # Verificar permisos
    PERMS=$(stat -c "%a" "$PROGOL_DIR/config.json")
    if [ "$PERMS" = "600" ]; then
        ok "config.json permisos 600"
    else
        warn "config.json permisos $PERMS (debería ser 600) — ejecutar: chmod 600 config.json"
    fi
else
    fail "config.json NO encontrado — copiar manualmente via SCP"
fi

# ── 3. Python imports ────────────────────────────────────────
hdr "Python imports"
cd "$PROGOL_DIR"
IMPORTS=("json" "os" "re" "sys" "time" "threading" "math" "secrets" "urllib.request")
for mod in "${IMPORTS[@]}"; do
    if python3 -c "import $mod" 2>/dev/null; then
        ok "import $mod"
    else
        fail "import $mod"
    fi
done

# Módulos locales
LOCAL_MODS=("model" "calibrator" "db")
for mod in "${LOCAL_MODS[@]}"; do
    if python3 -c "import sys; sys.path.insert(0,'$PROGOL_DIR'); import $mod" 2>/dev/null; then
        ok "import $mod (local)"
    else
        fail "import $mod (local) — revisar dependencias"
    fi
done

# ── 4. Datos de squads ───────────────────────────────────────
hdr "Datos del Mundial"
SQUAD_COUNT=$(python3 -c "import json; d=json.load(open('$PROGOL_DIR/data/wc2026_squads.json')); print(len(d['teams']))" 2>/dev/null || echo "0")
if [ "$SQUAD_COUNT" -ge 32 ]; then
    ok "wc2026_squads.json — $SQUAD_COUNT equipos"
else
    fail "wc2026_squads.json — solo $SQUAD_COUNT equipos (esperado 32)"
fi

if [ -f "$PROGOL_DIR/data/players_stats.json" ]; then
    STATS_COUNT=$(python3 -c "import json; d=json.load(open('$PROGOL_DIR/data/players_stats.json')); print(len(d))" 2>/dev/null || echo "0")
    ok "players_stats.json — $STATS_COUNT jugadores"
fi

# ── 5. Smoke test — arrancar server 3 segundos ───────────────
hdr "Smoke test del servidor"
python3 -c "
import subprocess, time, urllib.request, sys, os
os.chdir('$PROGOL_DIR')
p = subprocess.Popen(['python3', 'server.py'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
time.sleep(3)
try:
    r = urllib.request.urlopen('http://127.0.0.1:8765/', timeout=5)
    print('HTTP', r.status)
    p.terminate()
    sys.exit(0)
except Exception as e:
    p.terminate()
    out, err = p.communicate(timeout=2)
    print('ERROR:', e)
    if err: print(err.decode()[:300])
    sys.exit(1)
" && ok "Servidor responde en http://127.0.0.1:8765/" || fail "Servidor no responde — revisar logs"

# ── 6. Servicios del sistema ─────────────────────────────────
hdr "Servicios del sistema"
for svc in "cron" "fail2ban" "ufw"; do
    if systemctl is-active --quiet "$svc" 2>/dev/null; then
        ok "$svc activo"
    else
        warn "$svc no activo — ejecutar: sudo systemctl start $svc"
    fi
done

if systemctl is-enabled --quiet "progolcr" 2>/dev/null; then
    ok "progolcr.service habilitado en boot"
else
    warn "progolcr.service no habilitado — ejecutar: sudo systemctl enable progolcr"
fi

# ── 7. Cron jobs ─────────────────────────────────────────────
hdr "Cron jobs"
CRON_COUNT=$(crontab -u progolcr -l 2>/dev/null | grep -c "fetch_player_stats\|recalibrate\|wc2026" || echo "0")
if [ "$CRON_COUNT" -ge 3 ]; then
    ok "$CRON_COUNT cron jobs de ProGolCR instalados"
else
    warn "Solo $CRON_COUNT cron jobs — ejecutar: bash scripts/setup_crontab.sh"
fi

# ── Resultado final ──────────────────────────────────────────
echo ""
echo "=========================================="
echo "  RESULTADO: $PASS OK | $WARN avisos | $FAIL errores"
echo "=========================================="
if [ $FAIL -eq 0 ]; then
    echo "  ✓ MIGRACIÓN EXITOSA — ProGolCR listo para producción"
    echo "  Iniciar: sudo systemctl start progolcr"
    echo "  URL local: http://127.0.0.1:8765"
    echo "  URL pública: lt --port 8765 --subdomain progolcr"
else
    echo "  ✗ HAY $FAIL ERRORES — resolver antes de ir a producción"
    echo "  Ver detalle arriba"
fi
echo "=========================================="
