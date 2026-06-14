#!/usr/bin/env python3
"""Genera brand/pick_gratis.png — imagen del pick gratis del dia."""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT  = os.path.join(ROOT, "brand", "pick_gratis.png")

from PIL import Image, ImageDraw
from img_utils import (BG, GREEN, GOLD, WHITE, GRAY, DKGREEN,
                       font, paste_flag, draw_progol_logo, draw_footer)

W = 600

def generar(home_es, away_es, pick_text, prob_pct, conf, fair,
            hora_cr, canal, home_badge_url, away_badge_url, today,
            home_name="", away_name=""):

    PAD   = 20
    FLAG_W, FLAG_H = 110, 73

    # ── Calcular altura total antes de crear la imagen ──
    H = (
        16           # margen top
        + 34         # titulo "PICK GRATIS DEL DIA"
        + 8          # gap
        + 18         # subtitulo fecha
        + 14         # gap + linea
        + FLAG_H     # banderas
        + 8          # gap
        + 22         # nombres equipos
        + 16         # gap
        + 18         # label "PICK DE RYDER"
        + 10         # gap
        + 40         # texto pick grande
        + 14         # gap
        + 12         # barra confianza
        + 6          # gap
        + 16         # texto confianza
        + 10         # gap
        + 16         # probabilidad + cuota
        + 16         # gap + linea
        + (20 if hora_cr else 0)  # hora y canal
        + 8
        + 16         # "Analizado por Ryder"
        + 8
        + 18         # "/comprar"
        + 54         # footer
        + 16         # margen bottom
    )

    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Fondo gradiente
    for y in range(H):
        s = int(8 + 10 * math.sin(y * 0.013))
        draw.line([(0, y), (W, y)], fill=(0, s, s//3))

    y = 16  # cursor

    # ── Header ──
    draw_progol_logo(draw, PAD, y)
    draw.text((W//2, y), "PICK GRATIS DEL DIA",
              fill=GREEN, font=font(28, True), anchor="mt",
              stroke_width=2, stroke_fill=(0,35,10))
    y += 34

    draw.text((W//2, y), f"Copa del Mundo 2026  |  {today}",
              fill=GRAY, font=font(15), anchor="mt")
    y += 22

    draw.line([(PAD, y), (W-PAD, y)], fill=DKGREEN, width=1)
    y += 14

    # ── Banderas ──
    cx = W // 2
    flag_x_h = cx - FLAG_W - 48
    flag_x_a = cx + 48

    paste_flag(img, home_name or home_es, flag_x_h, y, FLAG_W, FLAG_H)
    draw.text((cx, y + FLAG_H//2), "VS", fill=GOLD, font=font(30, True), anchor="mm")
    paste_flag(img, away_name or away_es, flag_x_a, y, FLAG_W, FLAG_H)
    y += FLAG_H + 8

    # ── Nombres ──
    draw.text((flag_x_h + FLAG_W//2, y), home_es,
              fill=WHITE, font=font(17, True), anchor="mt")
    draw.text((flag_x_a + FLAG_W//2, y), away_es,
              fill=WHITE, font=font(17, True), anchor="mt")
    y += 28

    # ── Separador antes del pick ──
    draw.line([(PAD, y), (W-PAD, y)], fill=DKGREEN, width=1)
    y += 12

    # ── Caja pick (dibujada después de saber el alto del contenido) ──
    box_top = y
    y += 10

    draw.text((cx, y), "PICK DE RYDER", fill=GREEN, font=font(15, True), anchor="mt")
    y += 24

    draw.text((cx, y), pick_text, fill=WHITE,
              font=font(34, True), anchor="mt", stroke_width=1, stroke_fill=DKGREEN)
    y += 46

    # Barra de confianza
    bar_total = 220
    bar_filled = int(bar_total * conf / 10)
    bx = cx - bar_total//2
    draw.rounded_rectangle([bx, y, bx+bar_total, y+12], radius=6, fill=(0,40,18))
    if bar_filled > 0:
        draw.rounded_rectangle([bx, y, bx+bar_filled, y+12], radius=6, fill=GREEN)
    y += 16

    draw.text((cx, y), f"Confianza Ryder: {conf}/10",
              fill=GRAY, font=font(13), anchor="mt")
    y += 20

    draw.text((cx, y), f"Probabilidad: {prob_pct}%     Cuota justa: {fair}",
              fill=GRAY, font=font(13), anchor="mt")
    y += 16

    box_bottom = y + 10
    draw.rounded_rectangle([PAD, box_top, W-PAD, box_bottom],
                           radius=12, outline=GREEN, width=2)
    y = box_bottom + 14

    # ── Hora y canal ──
    draw.line([(PAD, y), (W-PAD, y)], fill=DKGREEN, width=1)
    y += 12

    if hora_cr:
        draw.text((cx, y), f"Hora: {hora_cr} CR     Canal: {canal}",
                  fill=WHITE, font=font(15, True), anchor="mt")
        y += 22

    draw.text((cx, y), "Analizado por Ryder, el scout de ProGol CR",
              fill=GRAY, font=font(14), anchor="mt")
    y += 22

    draw.text((cx, y), "Para picks completos escribe /comprar",
              fill=GREEN, font=font(14, True), anchor="mt")
    y += 22

    # ── Footer ──
    draw.line([(PAD, y+8), (W-PAD, y+8)], fill=DKGREEN, width=1)
    draw.text((cx, y+16), "Queremos que todos ganen",
              fill=GREEN, font=font(15, True), anchor="mt")
    draw.text((cx, y+36), "ProGol CR  |  Picks  |  Analisis  |  Copa del Mundo 2026",
              fill=GRAY, font=font(12), anchor="mt")

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
