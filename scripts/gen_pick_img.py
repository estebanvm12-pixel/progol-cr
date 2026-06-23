#!/usr/bin/env python3
"""Genera brand/pick_gratis.png"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT  = os.path.join(ROOT, "brand", "pick_gratis.png")

from PIL import Image, ImageDraw
from img_utils import BG, GREEN, GOLD, WHITE, GRAY, DKGREEN, font, paste_flag

W    = 600
PAD  = 24
FLAG_W, FLAG_H = 110, 73

def _draw(img, draw, home_es, away_es, pick_text, prob_pct, conf, fair,
          hora_cr, canal, today, home_name, away_name):

    y = 16

    # ── ProGol logo (esquina izq) ──
    sw, sh = 18, 24
    pts = [(PAD,y),(PAD+sw*2,y),(PAD+sw*2,y+sh*.72),(PAD+sw,y+sh),(PAD,y+sh*.72)]
    draw.polygon(pts, fill=DKGREEN, outline=GREEN)
    draw.text((PAD+sw, y+3), "P", fill=GOLD, font=font(14, True), anchor="mt")
    draw.text((PAD+sw*2+6, y+1),  "ProGol", fill=WHITE, font=font(16, True))
    draw.text((PAD+sw*2+6, y+20), "CR",     fill=GREEN, font=font(14, True))

    # ── Titulo centrado ──
    draw.text((W//2, y), "PICK GRATIS DEL DIA",
              fill=GREEN, font=font(27, True), anchor="mt",
              stroke_width=2, stroke_fill=(0,30,8))
    y += 38

    draw.text((W//2, y), f"Copa del Mundo 2026  |  {today}",
              fill=GRAY, font=font(14), anchor="mt")
    y += 20

    draw.line([(PAD, y), (W-PAD, y)], fill=DKGREEN, width=1)
    y += 18

    # ── Banderas y equipos ──
    cx = W // 2
    fx_h = cx - FLAG_W - 44
    fx_a = cx + 44

    paste_flag(img, home_name or home_es, fx_h, y, FLAG_W, FLAG_H)
    draw.text((cx, y + FLAG_H//2), "VS", fill=GOLD, font=font(28, True), anchor="mm")
    paste_flag(img, away_name or away_es, fx_a, y, FLAG_W, FLAG_H)
    y += FLAG_H + 10

    draw.text((fx_h + FLAG_W//2, y), home_es,
              fill=WHITE, font=font(16, True), anchor="mt")
    draw.text((fx_a + FLAG_W//2, y), away_es,
              fill=WHITE, font=font(16, True), anchor="mt")
    y += 26

    draw.line([(PAD, y), (W-PAD, y)], fill=DKGREEN, width=1)
    y += 18

    # ── Pick box — primero el fondo, luego el texto encima ──
    box_x1, box_x2 = PAD, W - PAD
    box_y1 = y
    box_h_est = 10 + 20 + 8 + 42 + 12 + 14 + 8 + 16 + 8 + 16 + 10  # estimado
    draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y1 + box_h_est],
                           radius=12, fill=(0, 42, 18), outline=GREEN, width=2)
    y += 12

    draw.text((cx, y), "PICK DE RYDER", fill=GREEN, font=font(15, True), anchor="mt")
    y += 24

    draw.text((cx, y), pick_text, fill=WHITE,
              font=font(34, True), anchor="mt",
              stroke_width=1, stroke_fill=(0, 25, 8))
    y += 46

    # Barra confianza
    bar_w = 220
    bx = cx - bar_w//2
    draw.rounded_rectangle([bx, y, bx+bar_w, y+12], radius=6, fill=(0,30,12))
    filled = max(4, int(bar_w * conf / 10))
    draw.rounded_rectangle([bx, y, bx+filled, y+12], radius=6, fill=GREEN)
    y += 16

    draw.text((cx, y), f"Confianza Ryder: {conf}/10",
              fill=GRAY, font=font(13), anchor="mt")
    y += 20

    draw.text((cx, y), f"Probabilidad: {prob_pct}%     |     Cuota justa: {fair}",
              fill=GRAY, font=font(13), anchor="mt")
    y += 20

    # Ajustar caja si el contenido fue mas alto de lo estimado
    actual_box_h = y + 10 - box_y1
    if actual_box_h > box_h_est:
        draw.rounded_rectangle([box_x1, box_y1, box_x2, box_y1 + actual_box_h],
                               radius=12, fill=(0, 42, 18), outline=GREEN, width=2)
    y += 10

    draw.line([(PAD, y), (W-PAD, y)], fill=DKGREEN, width=1)
    y += 16

    # ── Hora y canal ──
    if hora_cr:
        draw.text((cx, y), f"Hora: {hora_cr} (Costa Rica)  |  Canal: {canal}",
                  fill=WHITE, font=font(15, True), anchor="mt")
        y += 24

    draw.text((cx, y), "Analizado por Ryder, el scout de ProGol CR",
              fill=GRAY, font=font(14), anchor="mt")
    y += 22

    draw.text((cx, y), "Para picks completos escribe /comprar",
              fill=GREEN, font=font(14, True), anchor="mt")
    y += 28

    # ── Footer ──
    draw.line([(PAD, y), (W-PAD, y)], fill=DKGREEN, width=1)
    y += 10
    draw.text((cx, y), "Queremos que todos ganen",
              fill=GREEN, font=font(15, True), anchor="mt")
    y += 22
    draw.text((cx, y), "ProGol CR  |  Picks  |  Analisis  |  Copa del Mundo 2026",
              fill=GRAY, font=font(12), anchor="mt")
    y += 20

    return y  # altura usada


def generar(home_es, away_es, pick_text, prob_pct, conf, fair,
            hora_cr, canal, home_badge_url, away_badge_url, today,
            home_name="", away_name=""):

    # Pase en seco para calcular la altura real
    dummy = Image.new("RGB", (W, 1200), BG)
    h_used = _draw(dummy, ImageDraw.Draw(dummy),
                   home_es, away_es, pick_text, prob_pct, conf, fair,
                   hora_cr, canal, today, home_name, away_name)

    H = h_used + 16

    # Pase real con la imagen del tamaño correcto
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)
    for y in range(H):
        s = int(8 + 10 * math.sin(y * 0.013))
        draw.line([(0, y), (W, y)], fill=(0, s, s//3))

    _draw(img, draw, home_es, away_es, pick_text, prob_pct, conf, fair,
          hora_cr, canal, today, home_name, away_name)

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
    print(f"Guardado: {out}  size={__import__('PIL.Image', fromlist=['Image']).Image.open(out).size}")
