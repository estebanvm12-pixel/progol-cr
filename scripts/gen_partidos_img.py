#!/usr/bin/env python3
"""
Genera brand/partidos_hoy.png con los partidos del día.
Descarga badges de equipos, hora CR, canal, logo ProGol CR.
Llamado desde telegram_bot.py antes de enviar la imagen.
"""
import os, sys, math, datetime, io, urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
OUT  = os.path.join(ROOT, "brand", "partidos_hoy.png")

from PIL import Image, ImageDraw, ImageFont, ImageFilter, ImageOps

# ── Colores ProGol CR ──────────────────────────────────────────────────────────
BG      = (10, 20, 14)
GREEN   = (0, 210, 100)
GOLD    = (255, 205, 50)
WHITE   = (255, 255, 255)
GRAY    = (160, 170, 165)
DKGREEN = (0, 90, 40)
ROWBG   = (18, 32, 22)
ROWBG2  = (14, 26, 18)

# ── Canales típicos por competición ───────────────────────────────────────────
CHANNELS = {
    "FIFA World Cup":  "ESPN / Teletica",
    "UEFA Champions":  "ESPN",
    "La Liga":         "ESPN",
    "Premier League":  "ESPN",
    "default":         "ESPN / Fox Sports",
}

def _channel(competition):
    for k, v in CHANNELS.items():
        if k.lower() in (competition or "").lower():
            return v
    return CHANNELS["default"]

# ── Fuentes ────────────────────────────────────────────────────────────────────
def _f(size, bold=False):
    try:
        path = "C:/Windows/Fonts/" + ("arialbd.ttf" if bold else "arial.ttf")
        return ImageFont.truetype(path, size)
    except Exception:
        return ImageFont.load_default()

# ── Descarga y resize de badge ─────────────────────────────────────────────────
_badge_cache = {}

def _get_badge(url, size=64):
    if not url:
        return None
    if url in _badge_cache:
        return _badge_cache[url]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ProGolCR/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = r.read()
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        img = img.resize((size, size), Image.LANCZOS)
        _badge_cache[url] = img
        return img
    except Exception:
        return None

# ── Dibuja el escudo o placeholder ────────────────────────────────────────────
def _paste_badge(canvas, badge, x, y, size=64):
    if badge:
        # Máscara circular
        mask = Image.new("L", (size, size), 0)
        ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
        bg = Image.new("RGBA", (size, size), (18, 32, 22, 255))
        bg.paste(badge, (0, 0), badge if badge.mode == "RGBA" else None)
        canvas.paste(bg, (x, y), mask)
    else:
        # Círculo placeholder verde
        draw = ImageDraw.Draw(canvas)
        draw.ellipse([x, y, x + size, y + size], fill=DKGREEN, outline=GREEN, width=2)
        draw.text((x + size // 2, y + size // 2), "⚽", fill=WHITE,
                  font=_f(24), anchor="mm")

# ── Dibuja el logo ProGol CR ───────────────────────────────────────────────────
def _draw_logo(draw, x, y, w):
    # Escudo
    sw, sh = 28, 36
    pts = [(x, y), (x+sw*2, y), (x+sw*2, y+sh*.72), (x+sw, y+sh), (x, y+sh*.72)]
    draw.polygon(pts, fill=DKGREEN, outline=GREEN)
    draw.text((x+sw, y+4), "P", fill=GOLD,
              font=_f(20, bold=True), anchor="mt")
    # Texto
    draw.text((x+sw*2+10, y+2),  "ProGol", fill=WHITE, font=_f(22, bold=True))
    draw.text((x+sw*2+10, y+26), "CR",     fill=GREEN, font=_f(20, bold=True))

# ── Main ───────────────────────────────────────────────────────────────────────
def generar(rows, today):
    """rows: lista de dicts con home, away, kickoff_utc, competition, home_badge, away_badge"""
    if not rows:
        return None

    ROW_H  = 90
    PAD    = 18
    HDR_H  = 110
    FTR_H  = 60
    W      = 600
    H      = HDR_H + ROW_H * len(rows) + FTR_H + PAD

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # ── Header ────────────────────────────────────────────────────────────────
    # Gradiente verde arriba
    for y in range(HDR_H):
        alpha = int(60 * (1 - y / HDR_H))
        draw.line([(0, y), (W, y)], fill=(0, max(alpha, 10), max(alpha // 2, 5)))

    # Logo
    _draw_logo(draw, PAD, 20, W)

    # Título
    draw.text((W // 2, 28), "PARTIDOS DE HOY", fill=GREEN,
              font=_f(30, bold=True), anchor="mt", stroke_width=2, stroke_fill=(0, 40, 10))

    # Fecha
    try:
        d = datetime.date.fromisoformat(today)
        fecha = d.strftime("%A %d de %B, %Y").capitalize()
    except Exception:
        fecha = today
    draw.text((W // 2, 66), fecha, fill=GRAY, font=_f(16), anchor="mt")

    # Línea separadora
    draw.line([(PAD, HDR_H - 6), (W - PAD, HDR_H - 6)], fill=DKGREEN, width=1)

    # ── Filas de partidos ─────────────────────────────────────────────────────
    for i, r in enumerate(rows):
        ry   = HDR_H + i * ROW_H
        fill = ROWBG if i % 2 == 0 else ROWBG2
        draw.rectangle([0, ry, W, ry + ROW_H], fill=fill)

        h_es = r.get("home_es", r["home"])
        a_es = r.get("away_es", r["away"])

        # Badges
        badge_h = _get_badge(r.get("home_badge"), 56)
        badge_a = _get_badge(r.get("away_badge"), 56)
        by      = ry + (ROW_H - 56) // 2

        # Nombre local (derecha del escudo)
        _paste_badge(img, badge_h, PAD, by, 56)
        draw.text((PAD + 64, ry + 14), h_es, fill=WHITE,
                  font=_f(18, bold=True))

        # "vs" centrado
        draw.text((W // 2, ry + ROW_H // 2), "VS", fill=GOLD,
                  font=_f(20, bold=True), anchor="mm")

        # Nombre visitante (izquierda del escudo derecho)
        _paste_badge(img, badge_a, W - PAD - 56, by, 56)
        draw.text((W - PAD - 64, ry + 14), a_es, fill=WHITE,
                  font=_f(18, bold=True), anchor="rt")

        # Hora + canal (centrado abajo)
        hora_txt = r.get("hora_cr", "")
        canal    = _channel(r.get("competition", ""))
        info     = f"🕐 {hora_txt}  •  📺 {canal}" if hora_txt else f"📺 {canal}"
        draw.text((W // 2, ry + ROW_H - 20), info, fill=GRAY,
                  font=_f(14), anchor="mb")

        # Línea inferior fina
        if i < len(rows) - 1:
            draw.line([(PAD, ry + ROW_H), (W - PAD, ry + ROW_H)], fill=(30, 50, 35), width=1)

    # ── Footer ────────────────────────────────────────────────────────────────
    fy = H - FTR_H
    draw.line([(PAD, fy + 6), (W - PAD, fy + 6)], fill=DKGREEN, width=1)
    draw.text((W // 2, fy + 18), "💚 Queremos que todos ganen", fill=GREEN,
              font=_f(16, bold=True), anchor="mt")
    draw.text((W // 2, fy + 40), "ProGol CR · Picks · Análisis · Copa del Mundo 2026",
              fill=GRAY, font=_f(13), anchor="mt")

    img.save(OUT, "PNG", optimize=True)
    return OUT


if __name__ == "__main__":
    import db, sqlite3, datetime
    db.init_db()
    today = datetime.date.today().isoformat()
    conn  = db.get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT home, away, kickoff_utc, competition, home_badge, away_badge "
        "FROM matches WHERE date=? AND home!='' AND away!='' "
        "AND NOT EXISTS (SELECT 1 FROM matches m2 WHERE m2.home=matches.home "
        "AND m2.away=matches.away AND m2.status IN ('Finished','Live','FT','AET','PEN')) "
        "GROUP BY home, away ORDER BY kickoff_utc LIMIT 8",
        (today,)
    )
    import importlib.util, sys
    spec = importlib.util.spec_from_file_location("telegram_bot", os.path.join(ROOT, "telegram_bot.py"))
    tb   = importlib.util.load_module_from_spec(spec) if False else None

    rows = []
    for r in cur.fetchall():
        d = dict(r)
        # Hora CR
        hora = ""
        if d["kickoff_utc"]:
            try:
                k  = d["kickoff_utc"].replace("Z", "").replace("T", " ")[:16]
                dt = datetime.datetime.strptime(k, "%Y-%m-%d %H:%M")
                dt_cr = dt - datetime.timedelta(hours=6)
                hora  = dt_cr.strftime("%I:%M %p")
            except Exception:
                pass
        d["hora_cr"] = hora
        # Nombres en español — importar es() del bot
        sys.path.insert(0, ROOT)
        import telegram_bot as bot
        d["home_es"] = bot.es(d["home"])
        d["away_es"] = bot.es(d["away"])
        rows.append(d)
    conn.close()

    out = generar(rows, today)
    print(f"Guardado: {out}")
