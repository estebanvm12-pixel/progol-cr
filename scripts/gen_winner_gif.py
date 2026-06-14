#!/usr/bin/env python3
"""
Genera brand/winner_announce.gif — animación de pick ganador ProGol CR.
Usa solo Pillow.
"""
import os, math, random
from PIL import Image, ImageDraw, ImageFont

OUT = os.path.join(os.path.dirname(__file__), "..", "brand", "winner_announce.gif")

W, H = 600, 420
FRAMES   = 30
DURATION = 70   # ms por frame

GREEN   = (0, 210, 100)
DARK    = (8, 18, 12)
GOLD    = (255, 205, 50)
WHITE   = (255, 255, 255)
DKGREEN = (0, 110, 50)
LIME    = (140, 255, 100)

def _font(path, size):
    try:    return ImageFont.truetype(path, size)
    except: return ImageFont.load_default()

font_logo  = _font("C:/Windows/Fonts/arialbd.ttf", 44)   # "ProGol CR"
font_sub   = _font("C:/Windows/Fonts/arialbd.ttf", 18)   # "PICKS · ANÁLISIS · MUNDO 2026"
font_big   = _font("C:/Windows/Fonts/arialbd.ttf", 54)   # "¡PICK GANADOR!"
font_small = _font("C:/Windows/Fonts/arial.ttf",   18)

def _logo_block(draw, cx, y0, pulse):
    """Dibuja el logo ProGol CR con escudo minimalista."""
    # Escudo
    sw = int(36 * pulse)
    sh = int(44 * pulse)
    sx, sy = cx - sw - 8, y0 - sh // 2
    pts = [
        (sx, sy), (sx + sw * 2, sy),
        (sx + sw * 2, sy + sh * 0.7),
        (sx + sw, sy + sh),
        (sx, sy + sh * 0.7),
    ]
    draw.polygon(pts, fill=DKGREEN, outline=GREEN)
    # "P" dentro del escudo
    draw.text((sx + sw, sy + sh * 0.18), "P", fill=GOLD,
              font=_font("C:/Windows/Fonts/arialbd.ttf", int(28 * pulse)),
              anchor="mt")
    # Texto "ProGol CR"
    draw.text((cx + 20, y0 - 20), "ProGol", fill=WHITE,
              font=_font("C:/Windows/Fonts/arialbd.ttf", int(34 * pulse)),
              anchor="lt", stroke_width=1, stroke_fill=DARK)
    draw.text((cx + 20, y0 + 16), "CR", fill=GREEN,
              font=_font("C:/Windows/Fonts/arialbd.ttf", int(30 * pulse)),
              anchor="lt", stroke_width=1, stroke_fill=DARK)

def draw_frame(i):
    img  = Image.new("RGB", (W, H), DARK)
    draw = ImageDraw.Draw(img)
    t    = i / FRAMES

    # --- Fondo con gradiente animado ---
    for y in range(H):
        shade = int(12 + 10 * math.sin(y * 0.015 + t * 2 * math.pi))
        draw.line([(0, y), (W, y)], fill=(0, shade, shade // 3))

    # --- Confetti ---
    rng = random.Random(i * 53)
    for _ in range(22):
        px = rng.randint(0, W)
        py = int((rng.randint(0, H) + i * 14) % H)
        sz = rng.randint(3, 8)
        color = rng.choice([GOLD, GREEN, WHITE, LIME, (200, 80, 220)])
        draw.ellipse([px, py, px + sz, py + sz], fill=color)

    # --- Título "¡PICK GANADOR!" pulsante ---
    glow = int(180 + 75 * math.sin(t * 2 * math.pi))
    draw.text((W // 2, 28), "¡PICK GANADOR!", fill=(min(glow, 255), 255, 100),
              font=font_big, anchor="mt", stroke_width=3, stroke_fill=(0, 40, 0))

    # --- Círculo central pulsante con check ---
    pulse = 1 + 0.07 * math.sin(t * 2 * math.pi)
    cx, cy = W // 2, H // 2 + 10
    r = int(98 * pulse)
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=DKGREEN, outline=GREEN, width=5)
    ri = int(68 * pulse)
    draw.ellipse([cx - ri, cy - ri, cx + ri, cy + ri], fill=GREEN, outline=GOLD, width=3)
    # Check mark
    off = int(pulse * 1)
    draw.line([(cx - 26 + off, cy + 2), (cx - 8, cy + 26), (cx + 30, cy - 22)],
              fill=WHITE, width=7, joint="curve")

    # --- Logo ProGol CR (abajo izquierda + derecha) ---
    logo_y = H - 55
    # Escudo
    sw, sh = 22, 28
    sx, sy = 24, logo_y
    pts = [(sx, sy), (sx+sw*2, sy), (sx+sw*2, sy+sh*.7), (sx+sw, sy+sh), (sx, sy+sh*.7)]
    draw.polygon(pts, fill=DKGREEN, outline=GREEN)
    draw.text((sx + sw, sy + 2), "P", fill=GOLD,
              font=_font("C:/Windows/Fonts/arialbd.ttf", 18), anchor="mt")
    draw.text((sx + sw * 2 + 8, logo_y + 2),  "ProGol", fill=WHITE,
              font=_font("C:/Windows/Fonts/arialbd.ttf", 22), anchor="lt")
    draw.text((sx + sw * 2 + 8, logo_y + 26), "CR",     fill=GREEN,
              font=_font("C:/Windows/Fonts/arialbd.ttf", 20), anchor="lt")

    # Tagline derecha
    glow2 = int(160 + 80 * math.sin(t * 2 * math.pi + 1))
    draw.text((W - 16, logo_y + 4),  "Queremos que", fill=(glow2, 255, glow2),
              font=font_small, anchor="rt")
    draw.text((W - 16, logo_y + 24), "todos ganen 🐕",  fill=WHITE,
              font=font_small, anchor="rt")

    # Línea separadora
    draw.line([(16, H - 62), (W - 16, H - 62)], fill=DKGREEN, width=1)

    return img

print("Generando frames...")
frames = [draw_frame(i) for i in range(FRAMES)]
frames[0].save(
    OUT,
    save_all=True,
    append_images=frames[1:],
    loop=0,
    duration=DURATION,
    optimize=True,
)
print(f"GIF generado: {OUT} ({os.path.getsize(OUT)//1024} KB)")
