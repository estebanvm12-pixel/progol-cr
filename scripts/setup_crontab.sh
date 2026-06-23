#!/bin/bash
# ============================================================
# ProGolCR — Instalar cron jobs en Linux
# Reemplaza Windows Task Scheduler
# Ejecutar como el usuario progolcr: bash setup_crontab.sh
# ============================================================

PROGOL_DIR="/home/progolcr/worldcup-warroom"
LOG_DIR="$PROGOL_DIR/logs"
mkdir -p "$LOG_DIR"

# Leer crontab actual (sin sobreescribir otras entradas)
CURRENT_CRON=$(crontab -l 2>/dev/null | grep -v "ProGolCR" || true)

# Definir nuevos jobs
NEW_JOBS="
# ── ProGolCR Automation ──────────────────────────────────────
# Stats de jugadores en clubes — 2am diario
0 2 * * * cd $PROGOL_DIR && python3 scripts/fetch_player_stats_full.py >> $LOG_DIR/fetch_player_stats.log 2>&1

# Re-calibración Elo con datos de jugadores — 4am diario (después del fetch)
0 4 * * * cd $PROGOL_DIR && python3 scripts/recalibrate_with_player_stats.py >> $LOG_DIR/recalibrate.log 2>&1

# Stats en vivo del torneo WC2026 — cada 3 horas
0 */3 * * * cd $PROGOL_DIR && python3 scripts/fetch_wc2026_live_stats.py >> $LOG_DIR/wc2026_stats.log 2>&1

# Calibración diaria con resultados reales — medianoche
0 0 * * * cd $PROGOL_DIR && python3 -c \"import calibrator; calibrator.calibrate_yesterday(verbose=True)\" >> $LOG_DIR/calibration.log 2>&1

# Limpiar logs viejos — domingo 3am
0 3 * * 0 find $LOG_DIR -name '*.log' -mtime +30 -delete
# ── fin ProGolCR ─────────────────────────────────────────────
"

# Instalar crontab combinado
(echo "$CURRENT_CRON"; echo "$NEW_JOBS") | crontab -

echo "Cron jobs instalados:"
crontab -l | grep -A1 "ProGolCR"
echo ""
echo "Para ver todos los jobs: crontab -l"
echo "Para ver logs: tail -f $LOG_DIR/fetch_player_stats.log"
