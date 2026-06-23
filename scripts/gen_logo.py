#!/usr/bin/env python3
"""
Genera brand/logo_progolcr.png — logo standalone premium de ProGol CR.
800x800px con monograma PR dorado en medallón circular.
"""
import os, sys, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

from PIL import Image, ImageDraw, ImageFilter, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT  = os.path.join(ROOT, "brand", "logo_progolcr.png")

W = H = 800

C_BG    = (6, 14, 10)
C_GREEN = (0, 215, 95)
C_GREEN2= (0, 255, 130)
C_GOLD  = (255, 210, 40)
C_GOLD2 = (255, 242, 140)
C_WHITE = (240, 252, 245)
C_DARK  = (0, 22, 10)
C_MID   = (0, 48, 24)


def hex_pts(cx, cy, r, rotation=0):
    pts = []
    for i in range(6):
        ang = math.radians(i * 60 + rotation)
        pts.append((cx + r * math.cos(ang), cy + r * math.sin(ang)))
    return pts


def generate():
    img = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    cx = cy = W // 2

    # ── 1. Fondo circular viñeta ────────────────────────────────────────────
    bg = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    bgd = ImageDraw.Draw(bg)
    for i in range(370, 0, -2):
        t = min(1, i / 320)
        r_ = int(C_BG[0] * t)
        g_ = int(C_BG[1] * t)
        b_ = int(C_BG[2] * t)
        a  = int(255 * min(1, i / 280))
        bgd.ellipse([cx-i, cy-i, cx+i, cy+i], fill=(r_, g_, b_, a))
    img = Image.alpha_composite(img, bg)

    # ── 2. Glow exterior verde del hexágono ─────────────────────────────────
    glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    gd   = ImageDraw.Draw(glow)
    for i in range(12, 0, -1):
        a = int(255 * (i / 12) * 0.15)
        pts = hex_pts(cx, cy, 295 + i * 9, rotation=0)
        gd.polygon(pts, fill=(C_GREEN[0], C_GREEN[1], C_GREEN[2], a))
    img = Image.alpha_composite(img, glow.filter(ImageFilter.GaussianBlur(32)))

    draw = ImageDraw.Draw(img)

    # ── 3. Hexágono principal con degradado ─────────────────────────────────
    shadow = [(x+7, y+9) for x, y in hex_pts(cx, cy, 295)]
    draw.polygon(shadow, fill=(0, 0, 0, 110))

    for i in range(295, 0, -3):
        t = i / 295
        r_ = int(C_DARK[0] + (C_MID[0] - C_DARK[0]) * t)
        g_ = int(C_DARK[1] + (C_MID[1] - C_DARK[1]) * t)
        b_ = int(C_DARK[2] + (C_MID[2] - C_DARK[2]) * t)
        draw.polygon(hex_pts(cx, cy, i), fill=(r_, g_, b_, 255))

    # Bordes dorado + verde
    for w in range(5, 0, -1):
        a = int(255 * (w / 5))
        draw.polygon(hex_pts(cx, cy, 295), fill=None,
                     outline=(C_GOLD[0], C_GOLD[1], C_GOLD[2], a), width=w)
    draw.polygon(hex_pts(cx, cy, 278), fill=None,
                 outline=(C_GREEN[0], C_GREEN[1], C_GREEN[2], 170), width=2)
    draw.polygon(hex_pts(cx, cy, 268), fill=None,
                 outline=(C_GOLD[0], C_GOLD[1], C_GOLD[2], 60), width=1)

    # Puntos dorados en vértices
    for sx, sy in hex_pts(cx, cy, 295):
        draw.ellipse([sx-5, sy-5, sx+5, sy+5], fill=C_GOLD)

    # ── 4. Medallón circular para el "PR" ───────────────────────────────────
    med_cy = cy - 98
    med_r  = 82

    # Glow dorado del medallón
    med_glow = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    mgd = ImageDraw.Draw(med_glow)
    for i in range(10, 0, -1):
        a = int(255 * (i / 10) * 0.20)
        mgd.ellipse([cx - med_r - i*6, med_cy - med_r - i*6,
                     cx + med_r + i*6, med_cy + med_r + i*6],
                    fill=(C_GOLD[0], C_GOLD[1], C_GOLD[2], a))
    img = Image.alpha_composite(img, med_glow.filter(ImageFilter.GaussianBlur(16)))
    draw = ImageDraw.Draw(img)

    # Sombra del medallón
    draw.ellipse([cx - med_r + 5, med_cy - med_r + 7,
                  cx + med_r + 5, med_cy + med_r + 7], fill=(0, 0, 0, 100))

    # Base del medallón — muy oscuro para que el dorado resalte
    for i in range(med_r, 0, -2):
        t = i / med_r
        r_ = int(4  * t)
        g_ = int(12 * t)
        b_ = int(6  * t)
        draw.ellipse([cx-i, med_cy-i, cx+i, med_cy+i], fill=(r_, g_, b_, 255))

    # Borde exterior dorado triple
    draw.ellipse([cx - med_r - 3, med_cy - med_r - 3,
                  cx + med_r + 3, med_cy + med_r + 3],
                 fill=None, outline=(C_GOLD[0], C_GOLD[1], C_GOLD[2], 80), width=2)
    draw.ellipse([cx - med_r, med_cy - med_r, cx + med_r, med_cy + med_r],
                 fill=None, outline=C_GOLD, width=3)
    draw.ellipse([cx - med_r + 7, med_cy - med_r + 7,
                  cx + med_r - 7, med_cy + med_r - 7],
                 fill=None, outline=(C_GREEN[0], C_GREEN[1], C_GREEN[2], 140), width=1)

    # Diamantes en los 4 puntos cardinales del medallón
    for ang_deg in [0, 90, 180, 270]:
        ang = math.radians(ang_deg)
        dx = cx + int((med_r + 1) * math.cos(ang))
        dy = med_cy + int((med_r + 1) * math.sin(ang))
        sz = 7
        draw.polygon([(dx, dy-sz), (dx+sz, dy), (dx, dy+sz), (dx-sz, dy)], fill=C_GOLD)

    # Cuatro estrellas pequeñas en diagonal
    for ang_deg in [45, 135, 225, 315]:
        ang = math.radians(ang_deg)
        dx = cx + int((med_r + 1) * math.cos(ang))
        dy = med_cy + int((med_r + 1) * math.sin(ang))
        draw.ellipse([dx-4, dy-4, dx+4, dy+4], fill=(C_GOLD[0], C_GOLD[1], C_GOLD[2], 160))

    # ── 5. Texto "PR" dorado ────────────────────────────────────────────────
    try:
        f_pr = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 88)
    except Exception:
        f_pr = ImageFont.load_default()

    # Sombra fuerte
    for dx, dy in [(-2,2),(2,2),(0,3),(-3,3),(3,3)]:
        draw.text((cx+dx, med_cy+dy), "PR", fill=(0, 0, 0, 200), font=f_pr, anchor="mm")
    # "PR" dorado brillante
    draw.text((cx, med_cy), "PR", fill=(255, 218, 50), font=f_pr, anchor="mm")

    # ── 6. Texto "ProGol" ───────────────────────────────────────────────────
    try:
        f_big = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 90)
        f_cr  = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 64)
        f_tag = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   21)
    except Exception:
        f_big = f_cr = f_tag = ImageFont.load_default()

    text_y = cy + 8

    draw.text((cx+3, text_y+4), "ProGol", fill=(0, 0, 0, 190), font=f_big, anchor="mt")
    draw.text((cx, text_y), "ProGol", fill=C_WHITE, font=f_big, anchor="mt")

    cr_y = text_y + 95
    draw.text((cx+3, cr_y+3), "CR", fill=(0, 0, 0, 150), font=f_cr, anchor="mt")
    draw.text((cx, cr_y), "CR", fill=C_GREEN2, font=f_cr, anchor="mt")

    # Línea dorada decorativa bajo CR
    line_y = cr_y + 68
    line_len = 210
    draw.line([(cx - line_len//2, line_y), (cx + line_len//2, line_y)],
              fill=C_GOLD, width=2)
    for px in [cx - line_len//2, cx + line_len//2]:
        draw.ellipse([px-4, line_y-4, px+4, line_y+4], fill=C_GOLD)

    draw.text((cx, line_y + 11), "INTELIGENCIA DEPORTIVA",
              fill=C_GOLD, font=f_tag, anchor="mt")

    # ── 7. Reflexión superior sutil ─────────────────────────────────────────
    reflex = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    rd     = ImageDraw.Draw(reflex)
    for i in range(280, 210, -4):
        t = (i - 210) / 70
        a = int(14 * t)
        rd.polygon(hex_pts(cx, cy - 8, i), fill=(255, 255, 255, a))
    img = Image.alpha_composite(img, reflex.filter(ImageFilter.GaussianBlur(10)))

    # ── Guardar ──────────────────────────────────────────────────────────────
    final = Image.new("RGB", (W, H), C_BG)
    final.paste(img, mask=img.split()[3])
    final.save(OUT, "PNG", optimize=True)
    print(f"Logo generado: {OUT}")

    out_t = OUT.replace(".png", "_transparent.png")
    img.save(out_t, "PNG", optimize=True)
    print(f"Transparente:  {out_t}")


if __name__ == "__main__":
    generate()
