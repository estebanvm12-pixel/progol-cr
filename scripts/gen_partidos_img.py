#!/usr/bin/env python3
"""Genera brand/partidos_hoy.png (y .gif animado) con los partidos del dia."""
import os, sys, math, datetime, io
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT_PNG = os.path.join(ROOT, "brand", "partidos_hoy.png")
OUT_GIF = os.path.join(ROOT, "brand", "partidos_hoy.gif")

from PIL import Image, ImageDraw, ImageFilter, ImageEnhance
from img_utils import (BG, GREEN, GOLD, WHITE, GRAY, DKGREEN,
                       font, get_flag, paste_flag, draw_footer)

# Paleta premium
C_BG       = (6, 14, 10)
C_CARD     = (14, 28, 20)
C_CARD2    = (10, 22, 15)
C_GREEN    = (0, 210, 90)
C_GREEN2   = (0, 255, 120)
C_GOLD     = (255, 210, 40)
C_GOLD2    = (255, 235, 120)
C_WHITE    = (240, 250, 245)
C_GRAY     = (120, 145, 130)
C_ACCENT   = (0, 170, 75)
C_BORDER   = (0, 60, 30)
C_GLOW     = (0, 100, 50)

W = 800

CHANNELS = {
    "FIFA World Cup": "ESPN / Teletica",
    "UEFA Champions": "ESPN / Star+",
    "La Liga":        "ESPN",
    "Premier":        "ESPN",
    "Bundesliga":     "ESPN / Star+",
    "Serie A":        "ESPN / Star+",
    "Nations League": "ESPN / Teletica",
    "default":        "ESPN / Fox Sports",
}

def _channel(competition):
    for k, v in CHANNELS.items():
        if k.lower() in (competition or "").lower():
            return v
    return CHANNELS["default"]

def _draw_gradient_bg(draw, W, H):
    """Fondo oscuro con gradiente sutil."""
    for y in range(H):
        t = y / H
        r = int(C_BG[0] + (12 - C_BG[0]) * t)
        g = int(C_BG[1] + (22 - C_BG[1]) * t)
        b = int(C_BG[2] + (14 - C_BG[2]) * t)
        draw.line([(0, y), (W, y)], fill=(r, g, b))

def _draw_glow_line(draw, x1, y, x2, color, width=2):
    """Línea con efecto glow."""
    r, g, b = color
    draw.line([(x1, y), (x2, y)], fill=(r//3, g//3, b//3), width=width+4)
    draw.line([(x1, y), (x2, y)], fill=(r//2, g//2, b//2), width=width+2)
    draw.line([(x1, y), (x2, y)], fill=color, width=width)

_LOGO_IMG = None

def _get_logo(size=110):
    """Carga logo transparente una sola vez y lo escala."""
    global _LOGO_IMG
    if _LOGO_IMG is None:
        logo_path = os.path.join(ROOT, "brand", "logo_progolcr_transparent.png")
        if os.path.exists(logo_path):
            try:
                _LOGO_IMG = Image.open(logo_path).convert("RGBA")
            except Exception:
                _LOGO_IMG = False
        else:
            _LOGO_IMG = False
    if not _LOGO_IMG:
        return None
    return _LOGO_IMG.resize((size, size), Image.LANCZOS)


def _draw_header(img, draw, W, fecha_str):
    """Header premium con escudo ProGolCR grande."""
    HDR_H = 130

    # Línea decorativa top
    _draw_glow_line(draw, 0, 0, W, C_GREEN, width=3)

    # Logo ProGolCR
    cx, cy = 60, 65
    logo = _get_logo(size=108)
    if logo:
        lx = cx - 54
        ly = cy - 54
        img.paste(logo, (lx, ly), logo)
    else:
        # fallback hexágono si no existe el logo
        r = 38
        pts = [(cx + r*math.cos(math.radians(i*60-30)),
                cy + r*math.sin(math.radians(i*60-30))) for i in range(6)]
        draw.polygon(pts, fill=(0, 50, 25))
        draw.polygon(pts, outline=C_GOLD, width=2)
        draw.text((cx, cy-8), "P", fill=C_GOLD, font=font(26, True), anchor="mm")
        draw.text((cx, cy+14), "CR", fill=C_GREEN, font=font(13, True), anchor="mm")

    # Nombre ProGol CR
    draw.text((122, 34), "ProGol", fill=C_WHITE, font=font(38, True))
    draw.text((122, 74), "CR", fill=C_GREEN, font=font(28, True))

    # Línea separadora del título
    sep_x = 240
    draw.line([(sep_x, 35), (sep_x, 95)], fill=C_BORDER, width=2)

    # Título PARTIDOS DE HOY
    draw.text((W//2 + 60, 42), "PARTIDOS DE HOY", fill=C_GREEN,
              font=font(34, True), anchor="mt", stroke_width=2, stroke_fill=(0,40,15))
    draw.text((W//2 + 60, 82), fecha_str, fill=C_GRAY, font=font(17), anchor="mt")

    # Badge "Copa del Mundo 2026"
    badge_x, badge_y = W - 20, 52
    badge_w, badge_h = 180, 30
    draw.rounded_rectangle([badge_x - badge_w, badge_y, badge_x, badge_y + badge_h],
                            radius=6, fill=(0, 45, 20), outline=C_GOLD, width=1)
    draw.text((badge_x - badge_w//2, badge_y + badge_h//2),
              "Copa del Mundo 2026", fill=C_GOLD, font=font(11, True), anchor="mm")

    # Línea divisora inferior
    _draw_glow_line(draw, 16, HDR_H - 4, W - 16, C_GREEN, width=2)

    return HDR_H

def _draw_match_card(img, draw, row, y, W, ROW_H, is_even):
    """Dibuja una tarjeta de partido premium."""
    MARGIN = 12
    FLAG_W, FLAG_H = 96, 64
    CARD_H = ROW_H - 6

    # Fondo de la tarjeta con borde redondeado
    card_color = C_CARD if is_even else C_CARD2
    draw.rounded_rectangle([MARGIN, y+3, W-MARGIN, y+CARD_H],
                            radius=10, fill=card_color)
    # Borde sutil
    draw.rounded_rectangle([MARGIN, y+3, W-MARGIN, y+CARD_H],
                            radius=10, outline=C_BORDER, width=1)

    # Línea verde izquierda (acento)
    draw.rounded_rectangle([MARGIN, y+3, MARGIN+4, y+CARD_H],
                            radius=2, fill=C_GREEN)

    home = row.get("home", "")
    away = row.get("away", "")
    h_es = row.get("home_es", home)
    a_es = row.get("away_es", away)
    hora  = row.get("hora_cr", "")
    canal = _channel(row.get("competition", ""))
    status = row.get("status", "Scheduled")

    flag_y = y + (ROW_H - FLAG_H) // 2

    # ── Equipo local (izquierda) ──
    paste_flag(img, home, MARGIN + 16, flag_y, FLAG_W, FLAG_H)
    draw.text((MARGIN + 16 + FLAG_W + 10, y + 22),
              h_es, fill=C_WHITE, font=font(19, True))

    # ── Centro: hora + VS + canal ──
    center_x = W // 2

    if status == "Live":
        # Indicador LIVE rojo
        draw.rounded_rectangle([center_x - 28, y + 18, center_x + 28, y + 36],
                                radius=4, fill=(180, 20, 20))
        draw.text((center_x, y + 27), "● EN VIVO", fill=C_WHITE,
                  font=font(10, True), anchor="mm")
    else:
        # Hora con estilo
        if hora:
            draw.text((center_x, y + 24), hora, fill=C_GOLD,
                      font=font(22, True), anchor="mt")

    # VS badge
    vs_y = y + 44 if hora else y + 34
    draw.rounded_rectangle([center_x - 20, vs_y, center_x + 20, vs_y + 20],
                            radius=4, fill=(0, 55, 25))
    draw.text((center_x, vs_y + 10), "VS", fill=C_GREEN,
              font=font(12, True), anchor="mm")

    # Cuotas reales (si disponibles)
    odds_line = row.get("odds_line", "")
    if odds_line:
        draw.text((center_x, vs_y + 26), odds_line,
                  fill=C_GOLD, font=font(10, True), anchor="mt")

    # Canal
    draw.text((center_x, y + ROW_H - 22), f"📺 {canal}",
              fill=C_GRAY, font=font(11), anchor="mt")

    # ── Equipo visitante (derecha) ──
    away_flag_x = W - MARGIN - 16 - FLAG_W
    paste_flag(img, away, away_flag_x, flag_y, FLAG_W, FLAG_H)
    draw.text((away_flag_x - 10, y + 22), a_es,
              fill=C_WHITE, font=font(19, True), anchor="rt")


def generar(rows, today):
    if not rows:
        return None

    ROW_H  = 112
    HDR_H  = 130
    FTR_H  = 65
    GAP    = 8

    try:
        d     = datetime.date.fromisoformat(today)
        dias  = ["Lunes","Martes","Miércoles","Jueves","Viernes","Sábado","Domingo"]
        meses = ["enero","febrero","marzo","abril","mayo","junio","julio",
                 "agosto","septiembre","octubre","noviembre","diciembre"]
        fecha_str = f"{dias[d.weekday()]} {d.day} de {meses[d.month-1]} {d.year}"
    except Exception:
        fecha_str = today

    H = HDR_H + ROW_H * len(rows) + GAP * (len(rows) - 1) + FTR_H + 16

    img  = Image.new("RGB", (W, H), C_BG)
    draw = ImageDraw.Draw(img)

    _draw_gradient_bg(draw, W, H)
    hdr_end = _draw_header(img, draw, W, fecha_str)

    for i, r in enumerate(rows):
        card_y = hdr_end + i * (ROW_H + GAP) + 8
        _draw_match_card(img, draw, r, card_y, W, ROW_H, i % 2 == 0)

    # Footer
    fy = H - FTR_H
    _draw_glow_line(draw, 16, fy + 8, W - 16, C_GREEN, width=1)
    draw.text((W//2, fy + 16), "Queremos que ganes", fill=C_GREEN,
              font=font(16, True), anchor="mt")
    draw.text((W//2, fy + 38), "Picks • Análisis • Inteligencia Deportiva",
              fill=C_GRAY, font=font(13), anchor="mt")
    _draw_glow_line(draw, 0, H - 3, W, C_GREEN, width=3)

    img.save(OUT_PNG, "PNG", optimize=True)
    return OUT_PNG


def _generar_gif(rows, today, fecha_str, H):
    """Genera GIF de 3 frames: aparición suave + pulso verde en el título."""
    try:
        ROW_H = 112
        HDR_H = 130
        FTR_H = 65
        GAP   = 8

        frames = []
        # 3 frames: normal, brillo en título, normal
        for frame_idx in range(4):
            img  = Image.new("RGB", (W, H), C_BG)
            draw = ImageDraw.Draw(img)
            _draw_gradient_bg(draw, W, H)

            # Header con pulso alternado en "PARTIDOS DE HOY"
            hdr_end = _draw_header_gif(img, draw, W, fecha_str, frame_idx)

            for i, r in enumerate(rows):
                card_y = hdr_end + i * (ROW_H + GAP) + 8
                _draw_match_card(img, draw, r, card_y, W, ROW_H, i % 2 == 0)

            fy = H - FTR_H
            _draw_glow_line(draw, 16, fy + 8, W - 16, C_GREEN, width=1)
            draw.text((W//2, fy + 16), "Queremos que ganes", fill=C_GREEN,
                      font=font(16, True), anchor="mt")
            draw.text((W//2, fy + 38), "Picks • Análisis • Inteligencia Deportiva",
                      fill=C_GRAY, font=font(13), anchor="mt")
            _draw_glow_line(draw, 0, H - 3, W, C_GREEN, width=3)

            frames.append(img.convert("P", palette=Image.ADAPTIVE, colors=256))

        # Duración: frame 0=80ms, 1=60ms (brillo), 2=80ms, 3=120ms (pausa)
        durations = [80, 60, 80, 120]
        frames[0].save(
            OUT_GIF, save_all=True, append_images=frames[1:],
            loop=0, duration=durations, optimize=True
        )
    except Exception as e:
        print(f"[gif] error: {e}")


def _draw_header_gif(img, draw, W, fecha_str, frame_idx):
    """Header igual que el normal pero con título que pulsa."""
    HDR_H = 130
    _draw_glow_line(draw, 0, 0, W, C_GREEN, width=3)

    cx, cy = 60, 65
    logo = _get_logo(size=108)
    if logo:
        img.paste(logo, (cx - 54, cy - 54), logo)
    else:
        r = 38
        pts = [(cx + r*math.cos(math.radians(i*60-30)),
                cy + r*math.sin(math.radians(i*60-30))) for i in range(6)]
        draw.polygon(pts, fill=(0, 50, 25))
        draw.polygon(pts, outline=C_GOLD, width=2)
        draw.text((cx, cy-8), "P", fill=C_GOLD, font=font(26, True), anchor="mm")
        draw.text((cx, cy+14), "CR", fill=C_GREEN, font=font(13, True), anchor="mm")

    draw.text((122, 34), "ProGol", fill=C_WHITE, font=font(38, True))
    draw.text((122, 74), "CR", fill=C_GREEN, font=font(28, True))

    sep_x = 240
    draw.line([(sep_x, 35), (sep_x, 95)], fill=C_BORDER, width=2)

    # Pulso: frame 1 usa color más brillante y stroke más intenso
    title_color = C_GREEN2 if frame_idx == 1 else C_GREEN
    stroke_col  = (0, 80, 30) if frame_idx == 1 else (0, 40, 15)
    draw.text((W//2 + 60, 42), "PARTIDOS DE HOY", fill=title_color,
              font=font(34, True), anchor="mt", stroke_width=2, stroke_fill=stroke_col)
    draw.text((W//2 + 60, 82), fecha_str, fill=C_GRAY, font=font(17), anchor="mt")

    badge_x, badge_y = W - 20, 52
    badge_w, badge_h = 180, 30
    draw.rounded_rectangle([badge_x - badge_w, badge_y, badge_x, badge_y + badge_h],
                            radius=6, fill=(0, 45, 20), outline=C_GOLD, width=1)
    draw.text((badge_x - badge_w//2, badge_y + badge_h//2),
              "Copa del Mundo 2026", fill=C_GOLD, font=font(11, True), anchor="mm")

    _draw_glow_line(draw, 16, HDR_H - 4, W - 16, C_GREEN, width=2)
    return HDR_H


if __name__ == "__main__":
    import db, sqlite3, datetime as dt
    sys.path.insert(0, ROOT)
    db.init_db()
    today_cr = dt.date.today()
    window_start = dt.datetime(today_cr.year, today_cr.month, today_cr.day, 6, 0)
    window_end   = window_start + dt.timedelta(hours=24)
    ws = window_start.strftime("%Y-%m-%dT%H:%M")
    we = window_end.strftime("%Y-%m-%dT%H:%M")
    today = today_cr.isoformat()
    conn  = db.get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT home, away, kickoff_utc, competition FROM matches "
        "WHERE home!='' AND away!='' "
        "AND ( (kickoff_utc >= ? AND kickoff_utc < ?) OR (kickoff_utc='' AND date=?) ) "
        "GROUP BY home, away ORDER BY kickoff_utc LIMIT 8",
        (ws, we, today)
    )
    import telegram_bot as tb
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        d["home_es"] = tb.es(d["home"])
        d["away_es"] = tb.es(d["away"])
        hora = ""
        if d.get("kickoff_utc"):
            try:
                k  = d["kickoff_utc"].replace("Z","").replace("T"," ")[:16]
                dtt = dt.datetime.strptime(k, "%Y-%m-%d %H:%M")
                hora = (dtt - dt.timedelta(hours=6)).strftime("%I:%M %p")
            except Exception: pass
        d["hora_cr"] = hora
        rows.append(d)
    conn.close()
    out = generar(rows, today)
    print(f"Generado: {out}")
