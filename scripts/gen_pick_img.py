#!/usr/bin/env python3
"""
Genera brand/pick_gratis.png — imagen del pick gratis del día.
"""
import os, sys, math, datetime, io, urllib.request

ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, ROOT)
OUT  = os.path.join(ROOT, "brand", "pick_gratis.png")

from PIL import Image, ImageDraw, ImageFont

BG      = (8, 18, 12)
GREEN   = (0, 210, 100)
GOLD    = (255, 205, 50)
WHITE   = (255, 255, 255)
GRAY    = (150, 165, 158)
DKGREEN = (0, 90, 40)
MIDGREEN= (0, 140, 60)

def _f(size, bold=False):
    try:
        return ImageFont.truetype("C:/Windows/Fonts/" + ("arialbd.ttf" if bold else "arial.ttf"), size)
    except Exception:
        return ImageFont.load_default()

def _badge(url, size=80):
    if not url: return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ProGolCR/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = r.read()
        img = Image.open(io.BytesIO(data)).convert("RGBA").resize((size, size), Image.LANCZOS)
        return img
    except Exception:
        return None

def _paste_circle(canvas, badge, x, y, size):
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse([0, 0, size, size], fill=255)
    bg = Image.new("RGBA", (size, size), (14, 28, 18, 255))
    if badge:
        bg.paste(badge, (0, 0), badge)
    else:
        d = ImageDraw.Draw(bg)
        d.ellipse([4, 4, size-4, size-4], fill=DKGREEN, outline=GREEN, width=2)
        d.text((size//2, size//2), "⚽", fill=WHITE, font=_f(28), anchor="mm")
    canvas.paste(bg, (x, y), mask)

def generar(home_es, away_es, pick_text, prob_pct, conf, fair,
            hora_cr, canal, home_badge_url, away_badge_url, today):
    W, H = 600, 460
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Fondo gradiente
    for y in range(H):
        shade = int(8 + 12 * math.sin(y * 0.012))
        draw.line([(0, y), (W, y)], fill=(0, shade, shade // 3))

    # ── Header ProGol CR ──
    # Escudo
    sw, sh = 22, 28
    sx, sy = 20, 18
    pts = [(sx,sy),(sx+sw*2,sy),(sx+sw*2,sy+sh*.72),(sx+sw,sy+sh),(sx,sy+sh*.72)]
    draw.polygon(pts, fill=DKGREEN, outline=GREEN)
    draw.text((sx+sw, sy+3), "P", fill=GOLD, font=_f(18, True), anchor="mt")
    draw.text((sx+sw*2+8, sy+2),  "ProGol", fill=WHITE, font=_f(20, True))
    draw.text((sx+sw*2+8, sy+24), "CR",     fill=GREEN, font=_f(18, True))

    # Título
    draw.text((W//2, 22), "🐕 PICK GRATIS DEL DÍA", fill=GREEN,
              font=_f(26, True), anchor="mt", stroke_width=2, stroke_fill=(0,40,10))
    draw.text((W//2, 54), f"Copa del Mundo 2026 · {today}", fill=GRAY,
              font=_f(15), anchor="mt")

    draw.line([(20, 82), (W-20, 82)], fill=DKGREEN, width=1)

    # ── Badges y equipos ──
    badge_h = _badge(home_badge_url, 90)
    badge_a = _badge(away_badge_url, 90)

    # Local
    _paste_circle(img, badge_h, 60, 100, 90)
    draw.text((60+45, 200), home_es, fill=WHITE, font=_f(20, True), anchor="mt")

    # VS
    draw.text((W//2, 138), "VS", fill=GOLD, font=_f(32, True), anchor="mm")

    # Visitante
    _paste_circle(img, badge_a, W-60-90, 100, 90)
    draw.text((W-60-45, 200), away_es, fill=WHITE, font=_f(20, True), anchor="mt")

    # ── Caja del pick ──
    bx, by, bw, bh = 30, 225, W-60, 115
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=12, fill=(0,50,25), outline=GREEN, width=2)

    draw.text((W//2, by+14), "🎯 PICK DE RYDER", fill=GREEN, font=_f(16, True), anchor="mt")
    draw.text((W//2, by+38), pick_text, fill=WHITE,
              font=_f(28, True), anchor="mt", stroke_width=1, stroke_fill=DKGREEN)

    # Stats
    stars = "⭐" * min(conf, 10)
    draw.text((W//2, by+76), f"Probabilidad: {prob_pct}%   ·   Cuota justa: {fair}   ·   Confianza: {conf}/10",
              fill=GRAY, font=_f(13), anchor="mt")
    draw.text((W//2, by+96), stars[:conf], fill=GOLD, font=_f(14), anchor="mt")

    # ── Info partido ──
    draw.line([(20, 354), (W-20, 354)], fill=DKGREEN, width=1)

    info_y = 364
    if hora_cr:
        draw.text((W//2, info_y), f"🕐  {hora_cr} (hora Costa Rica)   ·   📺 {canal}",
                  fill=WHITE, font=_f(16, True), anchor="mt")
        info_y += 26

    draw.text((W//2, info_y), "Para picks completos: /comprar", fill=GREEN,
              font=_f(15), anchor="mt")

    # ── Footer ──
    draw.line([(20, H-52), (W-20, H-52)], fill=DKGREEN, width=1)
    draw.text((W//2, H-44), "💚 Queremos que todos ganen", fill=GREEN,
              font=_f(15, True), anchor="mt")
    draw.text((W//2, H-22), "ProGol CR · Picks · Análisis · Copa del Mundo 2026",
              fill=GRAY, font=_f(12), anchor="mt")

    img.save(OUT, "PNG", optimize=True)
    return OUT


if __name__ == "__main__":
    # Test con datos de ejemplo
    generar(
        home_es="Alemania", away_es="Curaçao",
        pick_text="Gana Alemania",
        prob_pct=84, conf=9, fair=1.2,
        hora_cr="11:00 AM", canal="ESPN / Teletica",
        home_badge_url="https://a.espncdn.com/i/teamlogos/countries/500/ger.png",
        away_badge_url="https://r2.thesportsdb.com/images/media/team/badge/itygvb1600955363.png",
        today=str(__import__("datetime").date.today())
    )
    print(f"Guardado: {OUT}")
