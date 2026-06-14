#!/usr/bin/env python3
"""Genera brand/pick_gratis.png — imagen del pick gratis del dia."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT  = os.path.join(ROOT, "brand", "pick_gratis.png")

from PIL import Image, ImageDraw
from img_utils import (BG, GREEN, GOLD, WHITE, GRAY, DKGREEN,
                       font, emoji_font, paste_flag, draw_progol_logo, draw_footer)

CHANNELS = {
    "FIFA World Cup": "ESPN / Teletica",
    "UEFA Champions": "ESPN",
    "default":        "ESPN / Fox Sports",
}

def generar(home_es, away_es, pick_text, prob_pct, conf, fair,
            hora_cr, canal, home_badge_url, away_badge_url, today,
            home_name="", away_name=""):

    W, H = 600, 480
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Fondo gradiente sutil
    for y in range(H):
        s = int(8 + 10 * math.sin(y * 0.013))
        draw.line([(0, y), (W, y)], fill=(0, s, s//3))

    # ── Header ──
    draw_progol_logo(draw, 18, 18)
    draw.text((W//2, 20), "PICK GRATIS DEL DIA", fill=GREEN,
              font=font(28, True), anchor="mt", stroke_width=2, stroke_fill=(0,35,10))
    draw.text((W//2, 56), f"Copa del Mundo 2026  |  {today}",
              fill=GRAY, font=font(15), anchor="mt")
    draw.line([(16, 82), (W-16, 82)], fill=DKGREEN, width=1)

    # ── Banderas + nombres ──
    FLAG_W, FLAG_H = 100, 66
    flag_y = 96

    # Local — bandera izquierda
    flag_x_h = W//2 - FLAG_W - 55
    paste_flag(img, home_name or home_es, flag_x_h, flag_y, FLAG_W, FLAG_H)
    draw.text((flag_x_h + FLAG_W//2, flag_y + FLAG_H + 8),
              home_es, fill=WHITE, font=font(17, True), anchor="mt")

    # VS
    draw.text((W//2, flag_y + FLAG_H//2), "VS",
              fill=GOLD, font=font(30, True), anchor="mm")

    # Visitante — bandera derecha
    flag_x_a = W//2 + 55
    paste_flag(img, away_name or away_es, flag_x_a, flag_y, FLAG_W, FLAG_H)
    draw.text((flag_x_a + FLAG_W//2, flag_y + FLAG_H + 8),
              away_es, fill=WHITE, font=font(17, True), anchor="mt")

    # ── Caja pick ──
    bx, by, bw, bh = 24, 210, W-48, 120
    draw.rounded_rectangle([bx, by, bx+bw, by+bh], radius=14,
                           fill=(0, 45, 20), outline=GREEN, width=2)

    draw.text((W//2, by+12), "PICK DE RYDER", fill=GREEN,
              font=font(16, True), anchor="mt")

    draw.text((W//2, by+36), pick_text, fill=WHITE,
              font=font(32, True), anchor="mt", stroke_width=1, stroke_fill=DKGREEN)

    # Stars sin emoji — barras de confianza
    bar_w_total = 200
    bar_filled  = int(bar_w_total * conf / 10)
    bbar_x = W//2 - bar_w_total//2
    bbar_y = by + 82
    draw.rounded_rectangle([bbar_x, bbar_y, bbar_x+bar_w_total, bbar_y+12],
                           radius=6, fill=(0,40,18))
    if bar_filled > 0:
        draw.rounded_rectangle([bbar_x, bbar_y, bbar_x+bar_filled, bbar_y+12],
                               radius=6, fill=GREEN)
    draw.text((W//2, bbar_y+18), f"Confianza Ryder: {conf}/10",
              fill=GRAY, font=font(13), anchor="mt")

    # Stats
    draw.text((W//2, by+102),
              f"Probabilidad: {prob_pct}%     Cuota justa: {fair}",
              fill=GRAY, font=font(13), anchor="mt")

    # ── Info hora y canal ──
    draw.line([(16, 346), (W-16, 346)], fill=DKGREEN, width=1)

    info_y = 358
    if hora_cr:
        draw.text((W//2, info_y),
                  f"Hora: {hora_cr} (Costa Rica)     Canal: {canal}",
                  fill=WHITE, font=font(16, True), anchor="mt")
        info_y += 30

    draw.text((W//2, info_y),
              "Analizado por Ryder, el scout de ProGol CR",
              fill=GRAY, font=font(14), anchor="mt")
    draw.text((W//2, info_y+22),
              "Para picks completos escribe /comprar",
              fill=GREEN, font=font(14, True), anchor="mt")

    draw_footer(draw, W, H)
    img.save(OUT, "PNG", optimize=True)
    return OUT


if __name__ == "__main__":
    out = generar(
        home_es="Alemania", away_es="Curazao",
        pick_text="Gana Alemania",
        prob_pct=84, conf=9, fair=1.2,
        hora_cr="11:00 AM", canal="ESPN / Teletica",
        home_badge_url="", away_badge_url="",
        today="2026-06-14",
        home_name="Germany", away_name="Curacao"
    )
    print(f"Guardado: {out}")
