#!/usr/bin/env python3
"""Genera brand/partidos_hoy.png con los partidos del dia y banderas."""
import os, sys, math, datetime
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.dirname(__file__))

ROOT = os.path.join(os.path.dirname(__file__), "..")
OUT  = os.path.join(ROOT, "brand", "partidos_hoy.png")

from PIL import Image, ImageDraw
from img_utils import (BG, GREEN, GOLD, WHITE, GRAY, DKGREEN, ROWBG, ROWBG2,
                       font, paste_flag, draw_progol_logo, draw_footer)

CHANNELS = {
    "FIFA World Cup": "ESPN / Teletica",
    "UEFA Champions": "ESPN",
    "La Liga":        "ESPN",
    "default":        "ESPN / Fox Sports",
}

def _channel(competition):
    for k, v in CHANNELS.items():
        if k.lower() in (competition or "").lower():
            return v
    return CHANNELS["default"]

def generar(rows, today):
    if not rows:
        return None

    ROW_H = 88
    HDR_H = 108
    FTR_H = 58
    W     = 620

    try:
        d     = datetime.date.fromisoformat(today)
        fecha = d.strftime("%A %d de %B %Y").capitalize()
    except Exception:
        fecha = today

    H = HDR_H + ROW_H * len(rows) + FTR_H + 8
    img  = Image.new("RGB", (W, H), BG)
    draw = ImageDraw.Draw(img)

    # Fondo gradiente
    for y in range(H):
        s = int(8 + 10 * math.sin(y * 0.01))
        draw.line([(0, y), (W, y)], fill=(0, s, s//3))

    # ── Header ──
    draw_progol_logo(draw, 16, 18)
    draw.text((W//2, 18), "PARTIDOS DE HOY", fill=GREEN,
              font=font(30, True), anchor="mt", stroke_width=2, stroke_fill=(0,35,10))
    draw.text((W//2, 58), fecha, fill=GRAY, font=font(16), anchor="mt")
    draw.line([(16, HDR_H-6), (W-16, HDR_H-6)], fill=DKGREEN, width=1)

    FLAG_W, FLAG_H = 72, 48

    # ── Filas ──
    for i, r in enumerate(rows):
        ry   = HDR_H + i * ROW_H
        fill = ROWBG if i % 2 == 0 else ROWBG2
        draw.rectangle([0, ry, W, ry+ROW_H], fill=fill)

        home = r.get("home","")
        away = r.get("away","")
        h_es = r.get("home_es", home)
        a_es = r.get("away_es", away)

        flag_y = ry + (ROW_H - FLAG_H)//2

        # Bandera local
        paste_flag(img, home, 16, flag_y, FLAG_W, FLAG_H)
        draw.text((16 + FLAG_W + 8, ry + 14), h_es,
                  fill=WHITE, font=font(17, True))

        # VS
        draw.text((W//2, ry + ROW_H//2), "VS",
                  fill=GOLD, font=font(20, True), anchor="mm")

        # Bandera visitante
        paste_flag(img, away, W - 16 - FLAG_W, flag_y, FLAG_W, FLAG_H)
        draw.text((W - 16 - FLAG_W - 8, ry + 14), a_es,
                  fill=WHITE, font=font(17, True), anchor="rt")

        # Hora + canal
        hora  = r.get("hora_cr", "")
        canal = _channel(r.get("competition",""))
        info  = f"{hora} CR   |   {canal}" if hora else canal
        draw.text((W//2, ry + ROW_H - 20), info,
                  fill=GRAY, font=font(13), anchor="mb")

        if i < len(rows)-1:
            draw.line([(16, ry+ROW_H), (W-16, ry+ROW_H)], fill=(25,45,30), width=1)

    draw_footer(draw, W, H)
    img.save(OUT, "PNG", optimize=True)
    return OUT


if __name__ == "__main__":
    import db, sqlite3, datetime as dt
    sys.path.insert(0, ROOT)
    db.init_db()
    today = dt.date.today().isoformat()
    conn  = db.get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT home, away, kickoff_utc, competition FROM matches "
        "WHERE date=? AND home!='' AND away!='' "
        "AND NOT EXISTS (SELECT 1 FROM matches m2 WHERE m2.home=matches.home "
        "AND m2.away=matches.away AND m2.status IN ('Finished','Live','FT','AET','PEN')) "
        "GROUP BY home, away ORDER BY kickoff_utc LIMIT 8", (today,)
    )
    import telegram_bot as tb
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        d["home_es"] = tb.es(d["home"])
        d["away_es"] = tb.es(d["away"])
        if d.get("kickoff_utc"):
            try:
                k = d["kickoff_utc"].replace("Z","").replace("T"," ")[:16]
                dtt = dt.datetime.strptime(k, "%Y-%m-%d %H:%M") - dt.timedelta(hours=6)
                d["hora_cr"] = dtt.strftime("%I:%M %p")
            except Exception:
                d["hora_cr"] = ""
        rows.append(d)
    conn.close()
    out = generar(rows, today)
    print(f"Guardado: {out}")
