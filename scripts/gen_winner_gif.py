#!/usr/bin/env python3
"""
Genera brand/winner_announce.gif — animación de pick ganador ProGol CR.
Usa solo Pillow (sin fuentes externas, usa fuente bitmap por defecto).
"""
import os, math
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "brand", "winner_announce.gif")

W, H = 600, 400
FRAMES = 24
DURATION = 80  # ms por frame

# Colores ProGol CR
GREEN  = (0, 200, 100)
DARK   = (10, 20, 15)
GOLD   = (255, 200, 50)
WHITE  = (255, 255, 255)
DKGREEN= (0, 130, 60)

try:
    font_big   = ImageFont.truetype("C:/Windows/Fonts/arialbd.ttf", 52)
    font_med   = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   28)
    font_small = ImageFont.truetype("C:/Windows/Fonts/arial.ttf",   20)
except Exception:
    font_big = font_med = font_small = ImageFont.load_default()

def draw_frame(i):
    img  = Image.new("RGB", (W, H), DARK)
    draw = ImageDraw.Draw(img)

    t = i / FRAMES  # 0..1

    # Fondo: efecto de onda verde
    for y in range(H):
        wave = int(10 * math.sin(y * 0.05 + t * 2 * math.pi))
        shade = int(15 + 8 * math.sin(y * 0.02 + t * math.pi))
        draw.line([(0, y), (W, y)], fill=(0, shade, shade // 2))

    # Círculo pulsante central
    pulse = 1 + 0.08 * math.sin(t * 2 * math.pi)
    r = int(110 * pulse)
    cx, cy = W // 2, H // 2 - 20
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DKGREEN, outline=GREEN, width=4)

    # Trofeo / check animado
    check_r = int(60 * pulse)
    draw.ellipse([cx - check_r, cy - check_r, cx + check_r, cy + check_r],
                 fill=GREEN, outline=GOLD, width=3)
    # Check mark
    pts = [
        (cx - 25, cy),
        (cx - 8,  cy + 20),
        (cx + 28, cy - 20),
    ]
    draw.line(pts, fill=WHITE, width=6, joint="curve")

    # Partículas tipo confetti
    import random
    rng = random.Random(i * 37)
    for _ in range(18):
        px = rng.randint(0, W)
        py = int((rng.randint(0, H) + i * 12) % H)
        size = rng.randint(3, 7)
        color = rng.choice([GOLD, GREEN, WHITE, (200, 50, 200)])
        draw.ellipse([px, py, px + size, py + size], fill=color)

    # Texto "¡PICK GANADOR!" con brillo pulsante
    alpha_t = int(200 + 55 * math.sin(t * 2 * math.pi))
    bright = (min(alpha_t, 255), 255, min(alpha_t, 255))
    draw.text((W // 2, 30), "¡PICK GANADOR!", fill=bright,
              font=font_big, anchor="mt", stroke_width=2, stroke_fill=DARK)

    # Logo texto ProGol CR
    draw.text((W // 2, H - 50), "ProGol CR", fill=GREEN,
              font=font_med, anchor="mt", stroke_width=1, stroke_fill=DARK)
    draw.text((W // 2, H - 22), "Queremos que todos ganen 🐕", fill=WHITE,
              font=font_small, anchor="mt")

    return img

frames = [draw_frame(i) for i in range(FRAMES)]
frames[0].save(
    OUT,
    save_all=True,
    append_images=frames[1:],
    loop=0,
    duration=DURATION,
    optimize=False,
)
print(f"GIF generado: {OUT} ({os.path.getsize(OUT)//1024} KB)")
