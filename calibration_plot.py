"""
Paso 5 — Calibration Plot Semanal ProGol CR
Genera curva de calibración desde brier_scores.json y la envía por Telegram.
Ejecución: python3 calibration_plot.py
Cron: cada domingo 08:00 CR time (14:00 UTC)
"""
import json, math, os, sys, datetime, urllib.request, urllib.parse, io

DATA_DIR  = "/home/progol/worldcup-warroom/data"
BRIER_F   = os.path.join(DATA_DIR, "brier_scores.json")
OUT_IMG   = "/tmp/calibration_plot.png"
CFG_F     = "/home/progol/worldcup-warroom/config.json"

# ─── Cargar config ────────────────────────────────────────────────────────────
with open(CFG_F) as f:
    _cfg = json.load(f)
TG_TOKEN  = _cfg.get("telegram_bot_token") or _cfg.get("TELEGRAM_BOT_TOKEN", "")
TG_CHAT   = str(_cfg.get("telegram_chat_id") or _cfg.get("TELEGRAM_CHAT_ID", ""))

# ─── Cargar datos ─────────────────────────────────────────────────────────────
with open(BRIER_F) as f:
    brier = json.load(f)

scores = brier.get("scores", [])
n_total = len(scores)

if n_total < 5:
    print(f"Solo {n_total} partidos calibrados — necesitamos al menos 5 para graficar.")
    sys.exit(0)

# ─── Construir curva de calibración ───────────────────────────────────────────
# Para cada outcome (H/D/A) agrupamos predicciones en bins de 10%
# y calculamos freq real en ese bin.

BINS = [0.0, 0.10, 0.20, 0.30, 0.40, 0.50, 0.60, 0.70, 0.80, 0.90, 1.01]
BIN_LABELS = ["0-10", "10-20", "20-30", "30-40", "40-50",
               "50-60", "60-70", "70-80", "80-90", "90-100"]

def build_calibration(scores, pred_key, actual_key):
    """
    pred_key:   "p_home" | "p_draw" | "p_away"
    actual_key: "actual_home" | (derived)
    """
    bins_pred   = [[] for _ in range(len(BINS)-1)]
    bins_actual = [[] for _ in range(len(BINS)-1)]

    for s in scores:
        p = s.get(pred_key)
        if p is None:
            continue
        sh = s.get("score_h", 0)
        sa = s.get("score_a", 0)
        if actual_key == "actual_home":
            actual = 1 if sh > sa else 0
        elif actual_key == "actual_draw":
            actual = 1 if sh == sa else 0
        else:  # actual_away
            actual = 1 if sa > sh else 0

        for i in range(len(BINS)-1):
            if BINS[i] <= p < BINS[i+1]:
                bins_pred[i].append(p)
                bins_actual[i].append(actual)
                break

    x_mean = []
    y_freq = []
    y_count = []
    for i in range(len(BINS)-1):
        if bins_pred[i]:
            x_mean.append(sum(bins_pred[i]) / len(bins_pred[i]))
            y_freq.append(sum(bins_actual[i]) / len(bins_actual[i]))
            y_count.append(len(bins_actual[i]))
        else:
            x_mean.append(None)
            y_freq.append(None)
            y_count.append(0)
    return x_mean, y_freq, y_count


cal_h = build_calibration(scores, "p_home", "actual_home")
cal_d = build_calibration(scores, "p_draw", "actual_draw")
cal_a = build_calibration(scores, "p_away", "actual_away")

# ─── Generar imagen SVG → PNG (sin matplotlib) ───────────────────────────────
# Usamos SVG puro para no depender de librerías de plotting
# Tamaño: 700×500 px

W, H_IMG = 700, 520
MARGIN = {"top": 50, "right": 30, "bottom": 70, "left": 65}
PLOT_W = W - MARGIN["left"] - MARGIN["right"]
PLOT_H = H_IMG - MARGIN["top"] - MARGIN["bottom"]

def to_px(x, y):
    """Convierte coordenadas [0,1]×[0,1] a píxeles SVG."""
    px = MARGIN["left"] + x * PLOT_W
    py = MARGIN["top"] + (1 - y) * PLOT_H
    return px, py

def polyline(x_vals, y_vals, color, dash=""):
    pts = []
    for x, y in zip(x_vals, y_vals):
        if x is None or y is None:
            continue
        px, py = to_px(x, y)
        pts.append(f"{px:.1f},{py:.1f}")
    if not pts:
        return ""
    d_attr = f'stroke-dasharray="{dash}"' if dash else ""
    return f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="2.5" {d_attr}/>'

def circles(x_vals, y_vals, counts, color):
    elems = []
    for x, y, c in zip(x_vals, y_vals, counts):
        if x is None or y is None or c == 0:
            continue
        px, py = to_px(x, y)
        r = min(4 + c, 12)
        elems.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{r}" fill="{color}" opacity="0.75"/>')
        elems.append(f'<text x="{px:.1f}" y="{py-r-3:.1f}" text-anchor="middle" font-size="9" fill="{color}">{c}</text>')
    return "\n".join(elems)

# Diagonal perfecta
diag_pts = " ".join(f"{to_px(v,v)[0]:.1f},{to_px(v,v)[1]:.1f}" for v in [0,0.1,0.2,0.3,0.4,0.5,0.6,0.7,0.8,0.9,1.0])

# Ejes
def axis_lines():
    lines = []
    # Gridlines
    for v in [0.2, 0.4, 0.6, 0.8, 1.0]:
        x1, y1 = to_px(0, v); x2, y2 = to_px(1, v)
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#ddd" stroke-width="1"/>')
        lines.append(f'<text x="{x1-8:.1f}" y="{y1+4:.1f}" text-anchor="end" font-size="11" fill="#666">{int(v*100)}%</text>')
    for v in [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]:
        x1, y1 = to_px(v, 0); x2, y2 = to_px(v, 1)
        lines.append(f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#eee" stroke-width="1"/>')
    for v in [0, 0.2, 0.4, 0.6, 0.8, 1.0]:
        px, py = to_px(v, 0)
        lines.append(f'<text x="{px:.1f}" y="{py+18:.1f}" text-anchor="middle" font-size="11" fill="#666">{int(v*100)}%</text>')
    return "\n".join(lines)

# Métricas clave
mean_bs = brier.get("mean_brier", 0)
shr     = brier.get("score_hit_rate", 0)
today   = datetime.date.today().isoformat()

# SVG completo
svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H_IMG}" style="background:#fff;font-family:Arial,sans-serif;">

  <!-- Título -->
  <text x="{W//2}" y="30" text-anchor="middle" font-size="15" font-weight="bold" fill="#222">
    ProGol CR — Curva de Calibración ({n_total} partidos · {today})
  </text>

  <!-- Grid y ejes -->
  {axis_lines()}

  <!-- Diagonal perfecta -->
  <polyline points="{diag_pts}" fill="none" stroke="#bbb" stroke-width="1.5" stroke-dasharray="6,4"/>
  <text x="{to_px(0.82,0.88)[0]:.1f}" y="{to_px(0.82,0.88)[1]:.1f}" font-size="10" fill="#aaa" transform="rotate(-45,{to_px(0.82,0.88)[0]:.1f},{to_px(0.82,0.88)[1]:.1f})">Calibración perfecta</text>

  <!-- Curvas -->
  {polyline([x for x in cal_h[0] if x is not None], [y for y in cal_h[1] if y is not None], "#2563eb")}
  {polyline([x for x in cal_d[0] if x is not None], [y for y in cal_d[1] if y is not None], "#f59e0b")}
  {polyline([x for x in cal_a[0] if x is not None], [y for y in cal_a[1] if y is not None], "#dc2626")}

  <!-- Puntos con conteo -->
  {circles(cal_h[0], cal_h[1], cal_h[2], "#2563eb")}
  {circles(cal_d[0], cal_d[1], cal_d[2], "#f59e0b")}
  {circles(cal_a[0], cal_a[1], cal_a[2], "#dc2626")}

  <!-- Borde del plot -->
  <rect x="{MARGIN['left']}" y="{MARGIN['top']}" width="{PLOT_W}" height="{PLOT_H}" fill="none" stroke="#ccc" stroke-width="1"/>

  <!-- Labels de ejes -->
  <text x="{MARGIN['left'] + PLOT_W//2}" y="{H_IMG - 10}" text-anchor="middle" font-size="12" fill="#555">Probabilidad predicha (%)</text>
  <text x="14" y="{MARGIN['top'] + PLOT_H//2}" text-anchor="middle" font-size="12" fill="#555" transform="rotate(-90,14,{MARGIN['top'] + PLOT_H//2})">Frecuencia real (%)</text>

  <!-- Leyenda -->
  <rect x="{MARGIN['left']+10}" y="{MARGIN['top']+10}" width="170" height="70" fill="white" opacity="0.85" rx="4"/>
  <line x1="{MARGIN['left']+20}" y1="{MARGIN['top']+27}" x2="{MARGIN['left']+40}" y2="{MARGIN['top']+27}" stroke="#2563eb" stroke-width="2.5"/>
  <text x="{MARGIN['left']+45}" y="{MARGIN['top']+31}" font-size="12" fill="#2563eb">Local (H)</text>
  <line x1="{MARGIN['left']+20}" y1="{MARGIN['top']+45}" x2="{MARGIN['left']+40}" y2="{MARGIN['top']+45}" stroke="#f59e0b" stroke-width="2.5"/>
  <text x="{MARGIN['left']+45}" y="{MARGIN['top']+49}" font-size="12" fill="#f59e0b">Empate (D)</text>
  <line x1="{MARGIN['left']+20}" y1="{MARGIN['top']+63}" x2="{MARGIN['left']+40}" y2="{MARGIN['top']+63}" stroke="#dc2626" stroke-width="2.5"/>
  <text x="{MARGIN['left']+45}" y="{MARGIN['top']+67}" font-size="12" fill="#dc2626">Visitante (A)</text>

  <!-- Métricas -->
  <text x="{W - MARGIN['right'] - 10}" y="{MARGIN['top']+20}" text-anchor="end" font-size="11" fill="#444">Brier: {mean_bs:.3f} (vs 0.667 azar)</text>
  <text x="{W - MARGIN['right'] - 10}" y="{MARGIN['top']+36}" text-anchor="end" font-size="11" fill="#444">Score exacto: {shr*100:.1f}%</text>
  <text x="{W - MARGIN['right'] - 10}" y="{MARGIN['top']+52}" text-anchor="end" font-size="11" fill="#888">Números = partidos en bin</text>
</svg>"""

# Guardar SVG
svg_path = OUT_IMG.replace(".png", ".svg")
with open(svg_path, "w") as f:
    f.write(svg)
print(f"SVG guardado: {svg_path}")

# Intentar convertir a PNG con cairosvg o rsvg-convert
png_path = OUT_IMG
converted = False

try:
    import cairosvg
    cairosvg.svg2png(url=svg_path, write_to=png_path, scale=2.0)
    converted = True
    print(f"PNG (cairosvg): {png_path}")
except ImportError:
    pass

if not converted:
    import subprocess
    r = subprocess.run(["rsvg-convert", "-w", "1400", "-h", "1040", svg_path, "-o", png_path],
                       capture_output=True)
    if r.returncode == 0:
        converted = True
        print(f"PNG (rsvg-convert): {png_path}")

if not converted:
    # Enviar SVG directamente por Telegram como documento
    print("No hay conversor PNG — enviando SVG como documento")
    png_path = svg_path

# ─── Enviar por Telegram ──────────────────────────────────────────────────────
if not TG_TOKEN or not TG_CHAT:
    print("Sin credenciales Telegram — solo guardando imagen localmente")
    sys.exit(0)

caption = (
    f"📊 *ProGol CR — Calibración Semanal* ({today})\n"
    f"Partidos calibrados: {n_total}\n"
    f"Brier Score: {mean_bs:.3f} (azar=0.667 → {(1-mean_bs/0.667)*100:.0f}% mejor)\n"
    f"Score exacto: {shr*100:.1f}%\n\n"
    f"📌 Curva cerca de la diagonal = modelo bien calibrado.\n"
    f"🔵 Local  🟡 Empate  🔴 Visitante"
)

with open(png_path, "rb") as img_file:
    img_data = img_file.read()

boundary = "----ProGolBoundary7x9z"
body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{TG_CHAT}\r\n'
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'
    f'--{boundary}\r\nContent-Disposition: form-data; name="parse_mode"\r\n\r\nMarkdown\r\n'
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="photo"; filename="calibration.png"\r\n'
    f"Content-Type: image/png\r\n\r\n"
).encode() + img_data + f"\r\n--{boundary}--\r\n".encode()

url = f"https://api.telegram.org/bot{TG_TOKEN}/sendPhoto"
req = urllib.request.Request(url, data=body,
      headers={"Content-Type": f"multipart/form-data; boundary={boundary}"})
try:
    resp = urllib.request.urlopen(req, timeout=30)
    resp_data = json.loads(resp.read())
    if resp_data.get("ok"):
        print("Telegram: enviado OK")
    else:
        print("Telegram error:", resp_data)
except Exception as e:
    # Fallback: enviar SVG como documento
    print(f"sendPhoto falló ({e}), intentando sendDocument con SVG...")
    with open(svg_path, "rb") as sf:
        svg_data = sf.read()
    boundary2 = "----ProGolBoundary2"
    body2 = (
        f"--{boundary2}\r\n"
        f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{TG_CHAT}\r\n'
        f"--{boundary2}\r\n"
        f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'
        f'--{boundary2}\r\nContent-Disposition: form-data; name="parse_mode"\r\n\r\nMarkdown\r\n'
        f"--{boundary2}\r\n"
        f'Content-Disposition: form-data; name="document"; filename="calibration.svg"\r\n'
        f"Content-Type: image/svg+xml\r\n\r\n"
    ).encode() + svg_data + f"\r\n--{boundary2}--\r\n".encode()
    url2 = f"https://api.telegram.org/bot{TG_TOKEN}/sendDocument"
    req2 = urllib.request.Request(url2, data=body2,
           headers={"Content-Type": f"multipart/form-data; boundary={boundary2}"})
    resp2 = urllib.request.urlopen(req2, timeout=30)
    resp2_data = json.loads(resp2.read())
    print("sendDocument:", "OK" if resp2_data.get("ok") else resp2_data)
