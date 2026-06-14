"""
Utilidades compartidas para generación de imágenes ProGol CR.
- Descarga de banderas por ISO code (flagcdn.com)
- Fuentes con soporte de emoji (Segoe UI Emoji)
- Dibujo de logo ProGol CR
"""
import os, io, urllib.request
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.join(os.path.dirname(__file__), "..")

# ── Colores ProGol CR ──────────────────────────────────────────────────────────
BG      = (8, 18, 12)
GREEN   = (0, 210, 100)
GOLD    = (255, 205, 50)
WHITE   = (255, 255, 255)
GRAY    = (150, 165, 158)
DKGREEN = (0, 80, 35)
ROWBG   = (16, 30, 20)
ROWBG2  = (12, 24, 16)

# ── Mapeo equipo → ISO 2 letras ────────────────────────────────────────────────
TEAM_ISO = {
    "Germany": "de", "France": "fr", "Spain": "es", "Brazil": "br",
    "Argentina": "ar", "Portugal": "pt", "Netherlands": "nl", "England": "gb-eng",
    "Italy": "it", "Belgium": "be", "Croatia": "hr", "Uruguay": "uy",
    "Mexico": "mx", "USA": "us", "Canada": "ca", "Japan": "jp",
    "South Korea": "kr", "Australia": "au", "Morocco": "ma", "Senegal": "sn",
    "Ghana": "gh", "Cameroon": "cm", "Nigeria": "ng", "Egypt": "eg",
    "Tunisia": "tn", "Algeria": "dz", "Ivory Coast": "ci", "Turkey": "tr",
    "Türkiye": "tr", "Switzerland": "ch", "Denmark": "dk", "Sweden": "se",
    "Norway": "no", "Poland": "pl", "Serbia": "rs", "Hungary": "hu",
    "Romania": "ro", "Austria": "at", "Czech Republic": "cz", "Slovakia": "sk",
    "Ukraine": "ua", "Greece": "gr", "Scotland": "gb-sct", "Wales": "gb-wls",
    "Ireland": "ie", "Colombia": "co", "Chile": "cl", "Ecuador": "ec",
    "Peru": "pe", "Bolivia": "bo", "Venezuela": "ve", "Paraguay": "py",
    "Costa Rica": "cr", "Panama": "pa", "Honduras": "hn", "El Salvador": "sv",
    "Haiti": "ht", "Jamaica": "jm", "Cuba": "cu",
    "Saudi Arabia": "sa", "Iran": "ir", "Iraq": "iq", "Qatar": "qa",
    "South Africa": "za", "New Zealand": "nz", "China": "cn", "India": "in",
    "Curacao": "cw", "Curaçao": "cw", "North Macedonia": "mk", "Albania": "al",
    "Kosovo": "xk", "Georgia": "ge", "Israel": "il",
    "Mali": "ml", "Senegal": "sn", "Togo": "tg", "Gambia": "gm",
}

_flag_cache = {}

def flag_url(team_name):
    iso = TEAM_ISO.get(team_name)
    if not iso:
        return None
    return f"https://flagcdn.com/w80/{iso}.png"

def get_flag(team_name, w=80, h=54):
    """Descarga y redimensiona la bandera del equipo."""
    url = flag_url(team_name)
    if not url:
        return None
    key = (team_name, w, h)
    if key in _flag_cache:
        return _flag_cache[key]
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ProGolCR/1.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = r.read()
        img = Image.open(io.BytesIO(data)).convert("RGBA")
        img = img.resize((w, h), Image.LANCZOS)
        _flag_cache[key] = img
        return img
    except Exception:
        return None

def paste_flag(canvas, team_name, x, y, w=80, h=54, with_border=True):
    """Pega la bandera en el canvas con borde redondeado opcional."""
    flag = get_flag(team_name, w, h)
    draw = ImageDraw.Draw(canvas)
    if flag:
        # Borde redondeado: crear máscara
        mask = Image.new("L", (w, h), 0)
        ImageDraw.Draw(mask).rounded_rectangle([0, 0, w, h], radius=6, fill=255)
        bg = Image.new("RGBA", (w, h), (14, 28, 18, 255))
        bg.paste(flag, (0, 0), flag if flag.mode == "RGBA" else None)
        canvas.paste(bg, (x, y), mask)
        if with_border:
            draw.rounded_rectangle([x, y, x+w, y+h], radius=6, outline=DKGREEN, width=2)
    else:
        # Placeholder
        draw.rounded_rectangle([x, y, x+w, y+h], radius=6, fill=DKGREEN, outline=GREEN, width=2)
        draw.text((x+w//2, y+h//2), "?", fill=WHITE, font=font(22, True), anchor="mm")

def font(size, bold=False):
    paths = [
        "C:/Windows/Fonts/" + ("arialbd.ttf" if bold else "arial.ttf"),
        "C:/Windows/Fonts/Arial.ttf",
    ]
    for p in paths:
        try: return ImageFont.truetype(p, size)
        except Exception: pass
    return ImageFont.load_default()

def emoji_font(size=20):
    """Fuente con soporte de emoji (Segoe UI Emoji)."""
    try: return ImageFont.truetype("C:/Windows/Fonts/seguiemj.ttf", size)
    except Exception: return font(size)

def draw_progol_logo(draw, x, y):
    """Dibuja el logo ProGol CR (escudo + texto)."""
    sw, sh = 20, 26
    pts = [(x,y),(x+sw*2,y),(x+sw*2,y+sh*.72),(x+sw,y+sh),(x,y+sh*.72)]
    draw.polygon(pts, fill=DKGREEN, outline=GREEN)
    draw.text((x+sw, y+3), "P", fill=GOLD, font=font(16, True), anchor="mt")
    draw.text((x+sw*2+6, y+1),  "ProGol", fill=WHITE, font=font(18, True))
    draw.text((x+sw*2+6, y+22), "CR",     fill=GREEN, font=font(16, True))

def draw_footer(draw, W, H):
    """Footer estándar ProGol CR."""
    draw.line([(16, H-50), (W-16, H-50)], fill=DKGREEN, width=1)
    draw.text((W//2, H-42), "Queremos que todos ganen",
              fill=GREEN, font=font(15, True), anchor="mt")
    draw.text((W//2, H-20), "ProGol CR  ·  Picks  ·  Analisis  ·  Copa del Mundo 2026",
              fill=GRAY, font=font(12), anchor="mt")
