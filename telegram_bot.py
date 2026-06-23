#!/usr/bin/env python3
"""
ProGol CR — Bot de ventas Telegram
Flujo: cliente elige producto → paga SINPE → envía comprobante →
       Esteban aprueba con un botón → bot entrega los picks automáticamente.
"""

import json, os, sys, time, threading, urllib.request, urllib.parse, urllib.error
import datetime, io

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH   = os.path.join(HERE, "config.json")
MASCOTA_PATH  = os.path.join(HERE, "brand", "mascota.jpg")
WINNER_GIF    = os.path.join(HERE, "brand", "winner_announce.gif")

# ── Nombres en español ─────────────────────────────────────────────────────────
TEAM_ES = {
    "Germany": "Alemania", "France": "Francia", "Spain": "España",
    "Brazil": "Brasil", "Argentina": "Argentina", "Portugal": "Portugal",
    "Netherlands": "Países Bajos", "England": "Inglaterra", "Italy": "Italia",
    "Belgium": "Bélgica", "Croatia": "Croacia", "Uruguay": "Uruguay",
    "Mexico": "México", "USA": "Estados Unidos", "Canada": "Canadá",
    "Japan": "Japón", "South Korea": "Corea del Sur", "Australia": "Australia",
    "Morocco": "Marruecos", "Senegal": "Senegal", "Ghana": "Ghana",
    "Cameroon": "Camerún", "Nigeria": "Nigeria", "Egypt": "Egipto",
    "Tunisia": "Túnez", "Algeria": "Argelia", "Ivory Coast": "Costa de Marfil",
    "Turkey": "Turquía", "Switzerland": "Suiza", "Denmark": "Dinamarca",
    "Sweden": "Suecia", "Norway": "Noruega", "Poland": "Polonia",
    "Serbia": "Serbia", "Hungary": "Hungría", "Romania": "Rumanía",
    "Austria": "Austria", "Czech Republic": "República Checa",
    "Slovakia": "Eslovaquia", "Ukraine": "Ucrania", "Greece": "Grecia",
    "Scotland": "Escocia", "Wales": "Gales", "Ireland": "Irlanda",
    "Colombia": "Colombia", "Chile": "Chile", "Ecuador": "Ecuador",
    "Peru": "Perú", "Bolivia": "Bolivia", "Venezuela": "Venezuela",
    "Paraguay": "Paraguay", "Costa Rica": "Costa Rica", "Panama": "Panamá",
    "Honduras": "Honduras", "El Salvador": "El Salvador", "Haiti": "Haití",
    "Jamaica": "Jamaica", "Cuba": "Cuba", "Trinidad and Tobago": "Trinidad y Tobago",
    "Saudi Arabia": "Arabia Saudita", "Iran": "Irán", "Iraq": "Irak",
    "Qatar": "Catar", "United Arab Emirates": "Emiratos Árabes",
    "South Africa": "Sudáfrica", "Zimbabwe": "Zimbabue", "Zambia": "Zambia",
    "New Zealand": "Nueva Zelanda", "China": "China", "India": "India",
    "Indonesia": "Indonesia", "Thailand": "Tailandia", "Vietnam": "Vietnam",
    "Curacao": "Curazao", "Bosnia-Herzegovina": "Bosnia-Herzegovina",
    "North Macedonia": "Macedonia del Norte", "Albania": "Albania",
    "Kosovo": "Kosovo", "Georgia": "Georgia", "Armenia": "Armenia",
    "Azerbaijan": "Azerbaiyán", "Israel": "Israel", "Syria": "Siria",
    "Jordan": "Jordania", "Kuwait": "Kuwait", "Bahrain": "Baréin",
    "Oman": "Omán", "Yemen": "Yemen", "Lebanon": "Líbano",
    "Mali": "Malí", "Burkina Faso": "Burkina Faso", "Guinea": "Guinea",
    "Cape Verde": "Cabo Verde", "Benin": "Benín", "Congo": "Congo",
    "Tanzania": "Tanzania", "Uganda": "Uganda", "Rwanda": "Ruanda",
    "Angola": "Angola", "Mozambique": "Mozambique", "Madagascar": "Madagascar",
    "Gabon": "Gabón", "Togo": "Togo", "Gambia": "Gambia",
}

def es(name):
    """Traduce nombre de equipo al español."""
    return TEAM_ES.get(name, name)

# ── Productos ──────────────────────────────────────────────────────────────────
PRODUCTS = {
    "free":       {"name": "Pick Gratis del Día",    "price": 0,    "emoji": "🆓"},
    "pro":        {"name": "Pro del Día",             "price": 500,  "emoji": "⚡"},
    "premium":    {"name": "Premium del Día",         "price": 1000, "emoji": "👑"},
    "quiniela":   {"name": "Quiniela del Día",        "price": 300,  "emoji": "📋"},
    "partido":    {"name": "Picks de un Partido",     "price": 200,  "emoji": "⚽"},
    "parlay":     {"name": "Parlay Armado",           "price": 250,  "emoji": "🎯"},
    "goleadores": {"name": "Datos de Goleadores",     "price": 300,  "emoji": "🥅"},
    "informe":    {"name": "Informe Mundial",          "price": 400,  "emoji": "📊"},
    "deepdive":   {"name": "Ryder Pro — Análisis Profundo", "price": 350, "emoji": "🧠"},
}

COMBOS = {
    "combo_mundial":    {"name": "Combo Mundial Completo",  "price": 800,  "emoji": "🌍"},
    "combo_apostador":  {"name": "Combo Apostador",         "price": 650,  "emoji": "💰"},
    "combo_total":      {"name": "Combo Total ProGol",      "price": 1200, "emoji": "🏆"},
}

_state = {}
_lock  = threading.Lock()
_group_chat_id = None   # se llena desde config o cuando el bot entra al grupo

def _save_group_chat_id(chat_id):
    """Guarda el group_chat_id en config.json si no estaba."""
    global _group_chat_id
    _group_chat_id = chat_id
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
        if not cfg.get("group_chat_id"):
            cfg["group_chat_id"] = chat_id
            with open(CONFIG_PATH, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2, ensure_ascii=False)
            print(f"[bot] group_chat_id guardado: {chat_id}")
    except Exception as e:
        print(f"[bot] no se pudo guardar group_chat_id: {e}")

# ── API helpers ────────────────────────────────────────────────────────────────
def _cfg():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _api(token, method, payload=None):
    url  = f"https://api.telegram.org/bot{token}/{method}"
    data = json.dumps(payload).encode("utf-8") if payload else None
    hdrs = {"Content-Type": "application/json", "User-Agent": "ProGolCR/1.0"}
    req  = urllib.request.Request(url, data=data, headers=hdrs)
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[bot] API error {method}: {e}")
        return {}

def _send(token, chat_id, text, reply_markup=None, parse_mode="Markdown"):
    p = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        p["reply_markup"] = reply_markup
    return _api(token, "sendMessage", p)

def _send_animation(token, chat_id, file_path, caption=""):
    """Envía un GIF animado (sendAnimation) con caption."""
    try:
        url = f"https://api.telegram.org/bot{token}/sendAnimation"
        with open(file_path, "rb") as f:
            file_bytes = f.read()
        fname = os.path.basename(file_path)
        boundary = "----ProGolBoundary"
        body  = f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n"
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"parse_mode\"\r\n\r\nMarkdown\r\n"
        if caption:
            body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n"
        body += (f"--{boundary}\r\nContent-Disposition: form-data; name=\"animation\"; "
                 f"filename=\"{fname}\"\r\nContent-Type: image/gif\r\n\r\n")
        body_bytes = body.encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
        req = urllib.request.Request(url, data=body_bytes,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                                              "User-Agent": "ProGolCR/1.0"})
        with urllib.request.urlopen(req, timeout=30) as r:
            result = json.loads(r.read().decode("utf-8"))
            return result.get("ok", False)
    except Exception as e:
        print(f"[bot] send_animation error: {e}")
        return False

def _send_photo(token, chat_id, caption="", file_path=None):
    """Envía una imagen (file_path o mascota.jpg por defecto) con caption."""
    try:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        img_path = file_path if file_path and os.path.exists(file_path) else MASCOTA_PATH
        with open(img_path, "rb") as f:
            photo_bytes = f.read()
        fname = os.path.basename(img_path)
        boundary = "----ProGolBoundary2"
        body  = f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{chat_id}\r\n"
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"parse_mode\"\r\n\r\nMarkdown\r\n"
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\n{caption}\r\n"
        mime = "image/png" if fname.endswith(".png") else "image/jpeg"
        body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"photo\"; filename=\"{fname}\"\r\nContent-Type: {mime}\r\n\r\n"
        body_bytes = body.encode("utf-8") + photo_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
        req = urllib.request.Request(url, data=body_bytes,
                                     headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                                              "User-Agent": "ProGolCR/1.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            result = json.loads(r.read().decode("utf-8"))
            return result.get("ok", False)
    except Exception as e:
        print(f"[bot] send_photo error: {e}")
        return False

def _answer_callback(token, cb_id, text=""):
    _api(token, "answerCallbackQuery", {"callback_query_id": cb_id, "text": text})

def _edit_message(token, chat_id, msg_id, text, reply_markup=None):
    p = {"chat_id": chat_id, "message_id": msg_id, "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        p["reply_markup"] = reply_markup
    _api(token, "editMessageText", p)

# ── Generadores de picks ───────────────────────────────────────────────────────
def _today_matches(limit=8):
    sys.path.insert(0, HERE)
    import db
    db.init_db()
    today = datetime.date.today().isoformat()
    conn = db.get_conn()
    conn.row_factory = __import__("sqlite3").Row
    # Excluye partidos donde ya existe alguna fila con status Finished/Live/FT
    cur = conn.execute(
        "SELECT DISTINCT home, away FROM matches "
        "WHERE date=? AND home!='' AND away!='' "
        "AND NOT EXISTS ("
        "  SELECT 1 FROM matches m2 "
        "  WHERE m2.home=matches.home AND m2.away=matches.away "
        "  AND m2.status IN ('Finished','Live','FT','AET','PEN')"
        ") LIMIT ?",
        (today, limit)
    )
    rows = cur.fetchall()
    conn.close()
    return rows, today

def _best_pick_data():
    """Devuelve dict con todos los datos del mejor pick del día, o None."""
    import db, sqlite3, model
    db.init_db()
    today = datetime.date.today().isoformat()
    conn  = db.get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT home, away, kickoff_utc, competition, home_badge, away_badge "
        "FROM matches WHERE date=? AND home!='' AND away!='' "
        "AND NOT EXISTS (SELECT 1 FROM matches m2 WHERE m2.home=matches.home "
        "AND m2.away=matches.away AND m2.status IN ('Finished','Live','FT','AET','PEN')) "
        "GROUP BY home, away ORDER BY kickoff_utc LIMIT 8",
        (today,)
    )
    rows = cur.fetchall()
    conn.close()
    best, best_conf = None, 0
    for r in rows:
        try:
            pred = model.predict(r["home"], r["away"])
            if pred.get("conf", 0) > best_conf:
                best_conf = pred["conf"]
                best = (dict(r), pred)
        except Exception:
            continue
    if not best:
        return None
    row, p = best
    prob   = p["prob"]
    h_es   = es(row["home"])
    a_es   = es(row["away"])
    if prob["home"] >= prob["away"] and prob["home"] >= prob["draw"]:
        pick_text, pick_prob = f"Gana {h_es}", prob["home"]
    elif prob["draw"] >= prob["home"] and prob["draw"] >= prob["away"]:
        pick_text, pick_prob = "Empate", prob["draw"]
    else:
        pick_text, pick_prob = f"Gana {a_es}", prob["away"]
    conf = int(round(p.get("conf", 0)))
    fair = round(100 / pick_prob, 2) if pick_prob > 0 else 0
    # Hora CR
    hora_cr, canal = "", "ESPN / Teletica"
    if row.get("kickoff_utc"):
        try:
            k  = row["kickoff_utc"].replace("Z","").replace("T"," ")[:16]
            dt = datetime.datetime.strptime(k, "%Y-%m-%d %H:%M")
            dt_cr = dt - datetime.timedelta(hours=6)
            hora_cr = dt_cr.strftime("%I:%M %p")
        except Exception:
            pass
    return {
        "home": row["home"], "away": row["away"],
        "home_es": h_es, "away_es": a_es,
        "pick_text": pick_text, "prob_pct": int(pick_prob),
        "conf": conf, "fair": fair,
        "hora_cr": hora_cr, "canal": canal, "today": today,
        "home_badge": row.get("home_badge",""),
        "away_badge": row.get("away_badge",""),
    }

def _get_free_pick():
    """Texto plano del pick gratis (fallback)."""
    d = _best_pick_data()
    if not d:
        return "No hay partidos programados para hoy."
    stars = "⭐" * min(d["conf"], 10)
    hora  = f"\n🕐 {d['hora_cr']} CR · 📺 {d['canal']}" if d["hora_cr"] else ""
    return (
        f"🐕 *PICK GRATIS DEL DÍA*\n"
        f"📅 {d['today']} · Copa del Mundo 2026\n\n"
        f"⚽ *{d['home_es']} vs {d['away_es']}*{hora}\n\n"
        f"🎯 Pick: *{d['pick_text']}*\n"
        f"📊 Probabilidad: *{d['prob_pct']}%*\n"
        f"💰 Cuota justa: *{d['fair']}*\n"
        f"🔥 Confianza Ryder: *{d['conf']}/10* {stars}\n\n"
        f"_Analizado por Ryder, el scout de ProGol CR 🐕_\n\n"
        f"¿Querés todos los picks del día? Escribí /comprar"
    )

def _send_free_pick_img(token, chat_id):
    """Genera imagen del pick gratis y la envía con mensaje de hype CR."""
    d = _best_pick_data()
    if not d:
        _send(token, chat_id, "No hay partidos programados para hoy.")
        return
    img_path = None
    try:
        import importlib.util
        spec = importlib.util.spec_from_file_location(
            "gen_pick_img", os.path.join(HERE, "scripts", "gen_pick_img.py"))
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        img_path = mod.generar(
            home_es=d["home_es"], away_es=d["away_es"],
            pick_text=d["pick_text"], prob_pct=d["prob_pct"],
            conf=d["conf"], fair=d["fair"],
            home_name=d["home"], away_name=d["away"],
            hora_cr=d["hora_cr"], canal=d["canal"],
            home_badge_url=d["home_badge"], away_badge_url=d["away_badge"],
            today=d["today"]
        )
    except Exception as e:
        print(f"[bot] gen_pick_img error: {e}")

    import random
    hype_msgs = [
        f"Ryder analizó todos los partidos de hoy y este es el pick con mayor valor matematico. 🔥\n\n*{d['pick_text']}* — {d['prob_pct']}% de probabilidad.\n\nEsta pick es gratis. Los 10 restantes del dia estan en /comprar 👇",
        f"Todos los dias demuestro que el analisis matematico gana. 💚\n\n*{d['pick_text']}* — Ryder lo dice con {d['conf']}/10 de confianza.\n\nQueres el paquete completo? /comprar 👇",
        f"Pick gratuito de hoy ya esta listo. 📊\n\n*{d['pick_text']}* — Probabilidad real: {d['prob_pct']}%\nCuota justa segun Ryder: {d['fair']}\n\nPara los picks completos del dia: /comprar 👇",
        f"Hoy Ryder tiene claridad total en este partido. 🎯\n\n*{d['pick_text']}* con {d['prob_pct']}% de respaldo matematico.\n\nSi queres todos los picks de hoy: /comprar 👇",
    ]

    if img_path and os.path.exists(img_path):
        caption = f"*PICK GRATUITO DEL DIA* 🐕\n_ProGol CR · Analisis con modelo matematico_"
        img_ok = _send_photo(token, chat_id, caption, file_path=img_path)
        if img_ok:
            time.sleep(0.6)
            _send(token, chat_id, random.choice(hype_msgs))
            return
    # Fallback texto
    _send(token, chat_id, _get_free_pick())

def _get_pro_picks():
    rows, today = _today_matches(8)
    if not rows:
        return "No hay partidos programados para hoy."
    import model
    lines = [f"⚡ *PICKS PRO DEL DÍA*\n📅 {today} · Copa del Mundo 2026\n_Analizado por Ryder · ProGol CR_\n"]
    parlays_safe = []
    for r in rows:
        try:
            p = model.predict(r["home"], r["away"])
            prob = p["prob"]
            h, a = es(r["home"]), es(r["away"])
            if prob["home"] >= 60:
                r1 = f"{h} gana ({prob['home']/100:.0%})"
            elif prob["home"] + prob["draw"] >= 70:
                r1 = f"Doble oportunidad {h} ({(prob['home']+prob['draw'])/100:.0%})"
            else:
                r1 = f"Doble oportunidad {a} o empate ({(prob['draw']+prob['away'])/100:.0%})"
            r2 = (f"Más de 2.5 goles ({p.get('over25',0)/100:.0%})"
                  if p.get("over25", 0) >= 55
                  else f"Menos de 2.5 goles ({p.get('under25',0)/100:.0%})")
            btts = p.get("btts", 0)
            r3 = f"Ambos marcan: {'Sí' if btts > 50 else 'No'} ({btts/100:.0%})"
            lines.append(f"⚽ *{h} vs {a}*")
            lines.append(f"  1️⃣ {r1}")
            lines.append(f"  2️⃣ {r2}")
            lines.append(f"  3️⃣ {r3}\n")
            if prob["home"] >= 65 or (prob["home"] + prob["draw"]) >= 75:
                parlays_safe.append((h, a, r1, prob["home"] / 100))
        except Exception:
            continue
    if parlays_safe:
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("🎯 *PARLAY SEGURO DEL DÍA*")
        for ph, pa, pick, _ in parlays_safe[:3]:
            lines.append(f"  • {ph} vs {pa}: {pick}")
        odds = 1.0
        for _, _, _, pr in parlays_safe[:3]:
            odds *= round(1 / pr * 0.91, 2)
        lines.append(f"  💰 Cuota combinada: *{odds:.2f}*\n")
    lines.append("💚 *Queremos que todos ganen. Apostá con criterio.*")
    lines.append("_ProGol CR · No es consejo financiero_")
    return "\n".join(lines)

def _get_quiniela():
    rows, today = _today_matches(12)
    if not rows:
        return "No hay partidos programados para hoy."
    import model
    lines = [
        f"📋 *QUINIELA DEL DÍA*",
        f"📅 {today} · Copa del Mundo 2026",
        f"_Analizado por Ryder · ProGol CR_\n",
        f"*Local · Visitante → Predicción (probabilidad)*\n",
    ]
    for i, r in enumerate(rows, 1):
        try:
            p = model.predict(r["home"], r["away"])
            prob = p["prob"]
            h, a = es(r["home"]), es(r["away"])
            if prob["home"] > prob["away"] and prob["home"] > prob["draw"]:
                res, pct = f"Gana {h}", prob["home"]
            elif prob["draw"] >= prob["home"] and prob["draw"] >= prob["away"]:
                res, pct = "Empate", prob["draw"]
            else:
                res, pct = f"Gana {a}", prob["away"]
            lines.append(f"{i}. {h} vs {a}")
            lines.append(f"   → *{res}* ({pct/100:.0%})\n")
        except Exception:
            lines.append(f"{i}. {es(r['home'])} vs {es(r['away'])} → ?\n")
    lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
    lines.append("💚 *Queremos que todos ganen.*")
    lines.append("_ProGol CR · No es consejo financiero_")
    return "\n".join(lines)

def _get_premium_picks():
    pro = _get_pro_picks()
    rows, today = _today_matches(8)
    import model
    extra = [
        "\n━━━━━━━━━━━━━━━━━━━━━━━",
        "👑 *EXCLUSIVO RYDER PRO*\n",
        "📋 *QUINIELA DEL DÍA*",
        "_Local vs Visitante — predicción con probabilidad_\n",
    ]
    goles = ["\n🥅 *GOLES ESPERADOS*", "_xG = goles que el partido debería producir según Ryder_\n"]
    for i, r in enumerate(rows, 1):
        try:
            p = model.predict(r["home"], r["away"])
            prob = p["prob"]
            eg = p["expectedGoals"]
            h, a = es(r["home"]), es(r["away"])
            if prob["home"] > prob["away"] and prob["home"] > prob["draw"]:
                res, pct = f"Gana {h}", prob["home"]
            elif prob["draw"] >= prob["home"] and prob["draw"] >= prob["away"]:
                res, pct = "Empate", prob["draw"]
            else:
                res, pct = f"Gana {a}", prob["away"]
            extra.append(f"{i}. *{h} vs {a}* → {res} ({pct/100:.0%})")
            goles.append(f"• {h} {eg['home']:.1f} — {eg['away']:.1f} {a}")
        except Exception:
            continue
    extra.append("")
    extra += goles
    extra.append("\n💚 *Ryder Pro analizó cada partido. Queremos que ganes.*")
    extra.append("_ProGol CR · No es consejo financiero_")
    return pro + "\n".join(extra)

def _get_deepdive(match_hint=""):
    return (
        f"🧠 *RYDER PRO — ANÁLISIS PROFUNDO*\n"
        f"{'⚽ ' + match_hint if match_hint else ''}\n\n"
        f"Este análisis es generado en tiempo real por RyderPro.\n\n"
        f"Para recibir tu análisis profundo de un partido específico:\n"
        f"1️⃣ Indicame el partido que te interesa\n"
        f"2️⃣ Ryder genera el análisis completo:\n"
        f"   • Alineaciones probables\n"
        f"   • Jugadores clave y sus estadísticas\n"
        f"   • Debilidades del rival a explotar\n"
        f"   • Marcador más probable y alternativas\n"
        f"   • Los 3 picks con mayor valor del partido\n"
        f"   • Riesgo principal a considerar\n\n"
        f"_Solo disponible en el plan Premium · RyderPro_\n"
        f"💚 ProGol CR quiere que ganes con información real."
    )

def _get_informe():
    return (
        f"📊 *INFORME MUNDIAL 2026*\n"
        f"_Analizado por Ryder · ProGol CR_\n\n"
        f"Este informe incluye:\n"
        f"• Tabla de posiciones de todos los grupos\n"
        f"• Clasificación de fuerza de cada equipo según Ryder\n"
        f"• Proyección de equipos que avanzan a octavos\n"
        f"• Los 5 equipos con mayor valor de apuesta esta semana\n"
        f"• Sorpresas del torneo hasta ahora\n\n"
        f"💡 *Para la quiniela de fase eliminatoria* (octavos, cuartos, semis, final) "
        f"Ryder genera un PDF completo con las predicciones de cada llave.\n"
        f"Escribí /quiniela\\_eliminatoria para solicitarlo.\n\n"
        f"💚 ProGol CR · Queremos que todos ganen."
    )

ESPN_WC_API = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

# ── Plan Gurú ─────────────────────────────────────────────────────────────────

import re as _re

def _parse_budget(text):
    """Extrae monto en colones del mensaje. Ej: 'Tengo 5000' → 5000."""
    t = text.replace("₡","").replace(",","").replace(".","")
    m = _re.search(r'\b(\d{3,6})\b', t)
    return int(m.group(1)) if m else None

def _extract_team_filter(text):
    """Detecta si el mensaje menciona un equipo específico."""
    txt = text.lower()
    for eng, esp in TEAM_ES.items():
        if eng.lower() in txt or esp.lower() in txt:
            return eng
    return None

def _guru_picks(budget, team_filter=None):
    """Genera picks del día con el modelo de Ryder y arma el plan de apuesta."""
    import db as _db, sqlite3
    _db.init_db()
    today_cr   = datetime.date.today()
    window_start = datetime.datetime(today_cr.year, today_cr.month, today_cr.day, 6, 0)
    window_end   = window_start + datetime.timedelta(hours=24)
    ws = window_start.strftime("%Y-%m-%dT%H:%M")
    we = window_end.strftime("%Y-%m-%dT%H:%M")

    conn = _db.get_conn()
    conn.row_factory = sqlite3.Row
    cur  = conn.execute(
        "SELECT home, away, kickoff_utc, competition FROM matches "
        "WHERE home!='' AND away!='' "
        "AND ( (kickoff_utc >= ? AND kickoff_utc < ?) OR (kickoff_utc='' AND date=?) ) "
        "AND status NOT IN ('Finished','FT','AET','PEN') "
        "GROUP BY home, away ORDER BY kickoff_utc",
        (ws, we, today_cr.isoformat())
    )
    rows = [dict(r) for r in cur.fetchall()]
    conn.close()

    # Si no hay partidos en DB, traer del ESPN
    if not rows:
        espn, _ = _fetch_espn_today()
        rows = [{"home": r["home"], "away": r["away"],
                 "kickoff_utc": r["kickoff_utc"], "competition": r["competition"]}
                for r in espn if r.get("status") != "Finished"]

    picks = []
    for r in rows:
        try:
            p    = model.predict(r["home"], r["away"])
            prob = p["prob"]
            # Elegir el outcome con mayor probabilidad
            home_p, draw_p, away_p = prob["home"], prob["draw"], prob["away"]
            if home_p >= draw_p and home_p >= away_p:
                outcome = f"Gana {es(r['home'])}"
                outcome_p = home_p
                market_key = "home"
            elif away_p >= home_p and away_p >= draw_p:
                outcome = f"Gana {es(r['away'])}"
                outcome_p = away_p
                market_key = "away"
            else:
                outcome = "Empate"
                outcome_p = draw_p
                market_key = "draw"
            # Cuota implícita justa con margen de casa típico
            fair_odd = round(1 / (outcome_p / 100) * 0.91, 2)  # ~9% margen casas CR
            hora = ""
            if r.get("kickoff_utc"):
                try:
                    k  = r["kickoff_utc"].replace("Z","").replace("T"," ")[:16]
                    dt = datetime.datetime.strptime(k, "%Y-%m-%d %H:%M")
                    hora = (dt - datetime.timedelta(hours=6)).strftime("%I:%M %p")
                except Exception:
                    pass
            picks.append({
                "home": r["home"], "away": r["away"],
                "outcome": outcome, "prob": outcome_p,
                "odd": fair_odd, "hora": hora,
                "market_key": market_key,
                "is_target": (team_filter and (
                    team_filter.lower() in r["home"].lower() or
                    team_filter.lower() in r["away"].lower()
                )),
            })
        except Exception:
            continue

    picks.sort(key=lambda x: (-x["prob"], not x.get("is_target", False)))
    return picks


def _send_guru_plan(token, chat_id, budget, team_filter=None):
    """Arma y envía el Plan Gurú para el presupuesto dado."""
    picks = _guru_picks(budget, team_filter)
    if not picks:
        _send(token, chat_id, "No hay partidos disponibles para hoy todavía. Intentá más tarde.")
        return

    today_str = datetime.date.today().strftime("%d/%m/%Y")

    # Si hay filtro de equipo, ponemos ese pick primero y lo marcamos como ATREVIDA
    target_pick = next((p for p in picks if p.get("is_target")), None)
    safe_picks   = [p for p in picks if not p.get("is_target") and p["prob"] >= 70][:3]
    bold_pick    = target_pick or next((p for p in picks if p not in safe_picks and p["prob"] >= 55), None)

    # Distribución del presupuesto: 75% combo seguro, 25% atrevida
    budget_safe  = round(budget * 0.75)
    budget_bold  = budget - budget_safe

    lines = [
        f"🧿 *PLAN GURÚ — ₡{budget:,}*",
        f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "",
    ]

    # COMBO SEGURO
    if safe_picks:
        combined_odd = 1.0
        for p in safe_picks:
            combined_odd *= p["odd"]
        combined_odd = round(combined_odd, 2)
        retorno_safe = round(budget_safe * combined_odd)
        ganancia_safe = retorno_safe - budget_safe

        lines += [
            f"📦 *COMBO SEGURO — ₡{budget_safe:,} apostados*",
        ]
        for p in safe_picks:
            hora_txt = f" · {p['hora']} CR" if p["hora"] else ""
            lines.append(f"• *{es(p['home'])} vs {es(p['away'])}*{hora_txt}")
            lines.append(f"  {p['outcome']} @ {p['odd']} ({p['prob']:.0f}% probabilidad)")
        lines += [
            f"Cuota combinada: {combined_odd}",
            f"✅ Retorno si entra: ₡{retorno_safe:,} (ganancia: +₡{ganancia_safe:,})",
            "",
        ]

    # APUESTA ATREVIDA
    if bold_pick:
        retorno_bold = round(budget_bold * bold_pick["odd"])
        ganancia_bold = retorno_bold - budget_bold
        hora_txt = f" · {bold_pick['hora']} CR" if bold_pick["hora"] else ""
        lines += [
            f"⚡ *APUESTA ATREVIDA — ₡{budget_bold:,} apostados*",
            f"• *{es(bold_pick['home'])} vs {es(bold_pick['away'])}*{hora_txt}",
            f"  {bold_pick['outcome']} @ {bold_pick['odd']} ({bold_pick['prob']:.0f}% probabilidad)",
            f"✅ Retorno si entra: ₡{retorno_bold:,} (ganancia: +₡{ganancia_bold:,})",
            "",
        ]

    # RESUMEN
    lines += ["📊 *RESUMEN*"]
    lines.append(f"Invertís: ₡{budget:,}")
    if safe_picks:
        lines.append(f"Si entra el combo seguro: ₡{retorno_safe:,} (+₡{ganancia_safe:,})")
    if bold_pick and safe_picks:
        total_retorno = retorno_safe + retorno_bold
        total_ganancia = total_retorno - budget
        lines.append(f"Si entran combo + atrevida: ₡{total_retorno:,} (+₡{total_ganancia:,})")
    lines.append(f"Peor caso (todo falla): -₡{budget:,}")
    lines += [
        "",
        "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
        "_Análisis de Ryder · ProGol CR_",
        "_La decisión final siempre es tuya._",
    ]

    _send(token, chat_id, "\n".join(lines))

def _fetch_espn_today():
    """Consulta el ESPN API y retorna partidos de HOY en hora CR (UTC-6)."""
    today_cr = datetime.date.today()
    # Ventana UTC que cubre el día completo en CR
    window_start = datetime.datetime(today_cr.year, today_cr.month, today_cr.day, 6, 0)  # 00:00 CR = 06:00 UTC
    window_end   = window_start + datetime.timedelta(hours=24)

    results = []
    seen_ids = set()
    # Fechas UTC a consultar (el día de hoy y el siguiente para cubrir partidos nocturnos)
    for utc_date in [today_cr, today_cr + datetime.timedelta(days=1)]:
        compact = utc_date.strftime("%Y%m%d")
        url = f"{ESPN_WC_API}?dates={compact}&limit=50"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "ProGolCR-Bot/1.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for ev in (data.get("events") or []):
                eid = ev.get("id")
                if not eid or eid in seen_ids:
                    continue
                seen_ids.add(eid)
                try:
                    comp = (ev.get("competitions") or [{}])[0]
                    competitors = comp.get("competitors") or []
                    home_c = next((c for c in competitors if c.get("homeAway") == "home"), None)
                    away_c = next((c for c in competitors if c.get("homeAway") == "away"), None)
                    if not home_c or not away_c:
                        continue
                    kickoff_utc = ev.get("date") or ""
                    if not kickoff_utc:
                        continue
                    # Verificar que está dentro de la ventana CR
                    ko_str = kickoff_utc.replace("Z", "").replace("T", " ")[:16]
                    ko_dt  = datetime.datetime.strptime(ko_str, "%Y-%m-%d %H:%M")
                    if not (window_start <= ko_dt < window_end):
                        continue
                    ko_cr  = ko_dt - datetime.timedelta(hours=6)
                    hora   = ko_cr.strftime("%I:%M %p")
                    status_obj = comp.get("status") or {}
                    status_type = (status_obj.get("type") or {}).get("name", "STATUS_SCHEDULED")
                    if status_type in ("STATUS_FINAL", "STATUS_FULL_TIME"):
                        status = "Finished"
                    elif status_type in ("STATUS_IN_PROGRESS", "STATUS_HALFTIME"):
                        status = "Live"
                    else:
                        status = "Scheduled"
                    home_team = (home_c.get("team") or {})
                    away_team = (away_c.get("team") or {})
                    home_name = home_team.get("displayName") or home_team.get("name") or ""
                    away_name = away_team.get("displayName") or away_team.get("name") or ""
                    results.append({
                        "home": home_name,
                        "away": away_name,
                        "home_es": es(home_name),
                        "away_es": es(away_name),
                        "kickoff_utc": kickoff_utc,
                        "hora_cr": hora,
                        "status": status,
                        "competition": "FIFA World Cup 2026",
                        "home_badge": (home_team.get("logos") or [{}])[0].get("href", "") if home_team.get("logos") else home_team.get("logo", ""),
                        "away_badge": (away_team.get("logos") or [{}])[0].get("href", "") if away_team.get("logos") else away_team.get("logo", ""),
                    })
                except Exception:
                    continue
        except Exception:
            pass
    results.sort(key=lambda m: m.get("kickoff_utc") or "")
    return results, today_cr.isoformat()


def _fetch_partidos_rows(limit=8):
    """Devuelve lista de dicts con partidos de HOY según hora CR (UTC-6).
    Consulta el ESPN API directamente para evitar desfases con la DB local.
    """
    rows, today = _fetch_espn_today()
    # Filtrar terminados
    rows = [r for r in rows if r.get("status") != "Finished"]
    return rows[:limit], today

def _send_partidos_img(token, chat_id):
    """Genera imagen de partidos y la envía como foto. Fallback a texto."""
    rows, today = _fetch_partidos_rows()
    if not rows:
        _send(token, chat_id, f"📅 No hay partidos programados para hoy ({today}).")
        return
    # Enriquecer con cuotas reales
    try:
        from integrations import get_match_odds
        for r in rows:
            od = get_match_odds(r.get("home", ""), r.get("away", ""))
            if od and od.get("best_home") and od.get("best_away"):
                r["odds_line"] = (f"1:{od['best_home']:.2f}"
                                  f"  X:{od['best_draw']:.2f}"
                                  f"  2:{od['best_away']:.2f}")
    except Exception as _oe:
        print(f"[bot] odds enrich error: {_oe}")
    img_path = None
    try:
        import importlib.util, os as _os
        spec = importlib.util.spec_from_file_location(
            "gen_partidos_img",
            _os.path.join(HERE, "scripts", "gen_partidos_img.py")
        )
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        img_path = mod.generar(rows, today)
    except Exception as e:
        print(f"[bot] gen_partidos_img error: {e}")
    if img_path and os.path.exists(img_path):
        caption = "⚽ *Partidos de hoy* · Para picks detallados: /comprar\n_ProGol CR — Inteligencia Deportiva_"
        # GIF → sendAnimation, PNG → sendPhoto
        ok = _send_photo(token, chat_id, caption, file_path=img_path)
        if ok:
            return
    # Fallback texto
    lines = [f"📅 *PARTIDOS DE HOY* — {today}\n"]
    for r in rows:
        lines.append(f"⚽ *{r['home_es']} vs {r['away_es']}*")
        if r["hora_cr"]:
            lines.append(f"   🕐 {r['hora_cr']} CR")
        lines.append("")
    lines.append("Para picks detallados: /comprar 👇")
    _send(token, chat_id, "\n".join(lines))

# ── Documentos corporativos (comando secreto) ──────────────────────────────────
def _html_to_text(path):
    """Extrae texto plano de un HTML quitando tags y CSS."""
    import re
    try:
        with open(path, encoding="utf-8") as f:
            html = f.read()
        # Eliminar <style> y <script>
        html = re.sub(r'<style[^>]*>.*?</style>', '', html, flags=re.DOTALL|re.IGNORECASE)
        html = re.sub(r'<script[^>]*>.*?</script>', '', html, flags=re.DOTALL|re.IGNORECASE)
        # Convertir algunos tags a saltos de línea
        html = re.sub(r'<(h[1-6]|p|li|tr|div|br)[^>]*>', '\n', html, flags=re.IGNORECASE)
        html = re.sub(r'</?(strong|b)>', '*', html, flags=re.IGNORECASE)
        # Quitar todos los demás tags
        html = re.sub(r'<[^>]+>', '', html)
        # Decodificar entidades HTML básicas
        html = html.replace('&amp;', '&').replace('&lt;', '<').replace('&gt;', '>')
        html = html.replace('&nbsp;', ' ').replace('&#13;', '').replace('&mdash;', '—')
        html = html.replace('&ldquo;', '"').replace('&rdquo;', '"').replace('&bull;', '•')
        # Limpiar espacios y líneas vacías excesivas
        lines = [l.strip() for l in html.splitlines()]
        lines = [l for l in lines if l]
        # Colapsar más de 2 líneas vacías seguidas
        out, prev_blank = [], 0
        for l in lines:
            if not l:
                prev_blank += 1
                if prev_blank <= 1:
                    out.append(l)
            else:
                prev_blank = 0
                out.append(l)
        return '\n'.join(out)
    except Exception as e:
        return f"[Error leyendo {os.path.basename(path)}: {e}]"

def _send_corp_docs(token, chat_id):
    """Envía todos los documentos corporativos de ProGol CR en partes."""
    cfg = _load_config()

    # ── 1. Portada ──
    _send(token, chat_id,
        "🔐 *DOCUMENTOS CORPORATIVOS — ProGol CR*\n"
        "_Acceso restringido · Solo para uso interno_\n\n"
        "Enviando todos los documentos en orden...")
    time.sleep(0.8)

    docs = [
        ("📋 ESTRATEGIA DE NEGOCIO 2026",
         os.path.join(HERE, "docs", "estrategia.html")),
        ("🎯 PITCH DECK / PRESENTACIÓN",
         os.path.join(HERE, "marketing", "pitch.html")),
        ("📊 REPORTE / ANÁLISIS COMPETITIVO",
         os.path.join(HERE, "marketing", "report.html")),
        ("🌍 ANÁLISIS DE MERCADO",
         os.path.join(HERE, "docs", "mercado.html")),
        ("🎨 BRAND GUIDE — ProGol CR",
         os.path.join(HERE, "docs", "progol-cr-brand.html")),
        ("🛒 PICKS & PRODUCTOS",
         os.path.join(HERE, "marketing", "picks.html")),
    ]

    for title, path in docs:
        if not os.path.exists(path):
            continue
        text = _html_to_text(path)
        # Telegram max 4096 chars por mensaje
        MAX = 3800
        header = f"━━━━━━━━━━━━━━━━━━━━━━━\n*{title}*\n━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        full = header + text
        # Enviar en chunks si es necesario
        chunk = ""
        for line in full.splitlines(keepends=True):
            if len(chunk) + len(line) > MAX:
                if chunk.strip():
                    _send(token, chat_id, chunk)
                    time.sleep(0.4)
                chunk = line
            else:
                chunk += line
        if chunk.strip():
            _send(token, chat_id, chunk)
            time.sleep(0.5)

    # ── 2. Config técnica (sin claves) ──
    _send(token, chat_id,
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "⚙️ *CONFIGURACIÓN TÉCNICA*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        f"• Servidor: puerto 8765 (local)\n"
        f"• Túnel: localtunnel (URL cambia al reiniciar)\n"
        f"• Base de datos: SQLite (data/wc2026.db)\n"
        f"• Bot Telegram: @progolcr_bot\n"
        f"• Grupo comunidad: {_group_chat_id or 'no configurado'}\n"
        f"• Modelo IA: Dixon-Coles + Elo (Ryder)\n"
        f"• Startup: VBS en Windows Startup\n\n"
        "⚠️ *Las claves API y contraseñas NO se envían por Telegram.*\n"
        "Están guardadas en `config.json` en la PC (nunca en git).\n"
        "Para verlas: abrí `config.json` directamente en la máquina."
    )
    time.sleep(0.5)

    # ── 3. Usuarios activos ──
    try:
        import db as _db
        _db.init_db()
        conn = _db.get_conn()
        conn.row_factory = __import__('sqlite3').Row
        users = conn.execute(
            "SELECT username, role, created_at FROM users ORDER BY created_at DESC LIMIT 20"
        ).fetchall()
        conn.close()
        if users:
            lines = ["━━━━━━━━━━━━━━━━━━━━━━━\n👥 *USUARIOS REGISTRADOS*\n━━━━━━━━━━━━━━━━━━━━━━━\n"]
            for u in users:
                lines.append(f"• `{u['username']}` — {u['role']} (desde {(u['created_at'] or '')[:10]})")
            _send(token, chat_id, "\n".join(lines))
            time.sleep(0.4)
    except Exception as e:
        _send(token, chat_id, f"[No se pudo leer usuarios: {e}]")

    # ── 4. Proyecciones financieras ──
    _send(token, chat_id,
        "━━━━━━━━━━━━━━━━━━━━━━━\n"
        "💰 *PROYECCIONES FINANCIERAS 2026*\n"
        "━━━━━━━━━━━━━━━━━━━━━━━\n\n"
        "*Planes y precios:*\n"
        "• Scout (Pro del día) — ₡500/pick\n"
        "• Pro Plan — ₡3,500/mes\n"
        "• Premium — ₡6,000/mes\n"
        "• Elite — ₡10,000/mes\n\n"
        "*SINPE:* 8561-0677 (Esteban Venegas)\n\n"
        "*Meta Fase 1 (Jun-Jul 2026):*\n"
        "• 50 usuarios Scout → ₡175,000/mes\n"
        "• 20 Pro → ₡70,000/mes\n"
        "• 10 Premium → ₡60,000/mes\n"
        "• *Total estimado: ₡305,000/mes*\n\n"
        "*Meta Fase 2 (Mundial en marcha):*\n"
        "• 200 usuarios activos\n"
        "• ₡1,200,000+/mes\n"
        "• Expansión: WhatsApp + web pública\n\n"
        "💚 ProGol CR · Inteligencia deportiva costarricense"
    )

    _send(token, chat_id,
        "✅ *Todos los documentos enviados.*\n"
        "_Este mensaje es confidencial. No reenviar sin autorización._\n\n"
        "💚 ProGol CR — Queremos que todos ganen.")

def _load_config():
    try:
        with open(CONFIG_PATH) as f:
            return json.load(f)
    except Exception:
        return {}

def _get_goleadores():
    rows, today = _today_matches(8)
    if not rows:
        return "No hay partidos programados para hoy."
    import model
    lines = [
        f"🥅 *GOLES ESPERADOS POR PARTIDO*",
        f"📅 {today} · Analizado por Ryder\n",
        f"_xG = cuántos goles debería producir el partido_\n",
    ]
    for r in rows:
        try:
            p = model.predict(r["home"], r["away"])
            eg = p["expectedGoals"]
            h, a = es(r["home"]), es(r["away"])
            total = eg["home"] + eg["away"]
            over = p.get("over25", 0) / 100
            lines.append(f"⚽ *{h} vs {a}*")
            lines.append(f"   {h}: *{eg['home']:.1f} goles esperados*")
            lines.append(f"   {a}: *{eg['away']:.1f} goles esperados*")
            lines.append(f"   Total esperado: *{total:.1f}* — Más 2.5: {over:.0%}\n")
        except Exception:
            continue
    lines.append("💚 Ryder analiza cada partido. ProGol CR quiere que ganes.")
    lines.append("_No es consejo financiero_")
    return "\n".join(lines)

# ── Mapa de contenido ──────────────────────────────────────────────────────────
CONTENT_MAP = {
    "free":            _get_free_pick,
    "pro":             _get_pro_picks,
    "premium":         _get_premium_picks,
    "quiniela":        _get_quiniela,
    "parlay":          _get_pro_picks,
    "goleadores":      _get_goleadores,
    "informe":         _get_informe,
    "deepdive":        _get_deepdive,
    "partido":         lambda: "Decime qué partido querés analizar y te mando los picks específicos. ⚽",
    "combo_mundial":   lambda: _get_quiniela() + "\n\n" + _get_informe(),
    "combo_apostador": _get_pro_picks,
    "combo_total":     _get_premium_picks,
}

# ── Teclados ───────────────────────────────────────────────────────────────────
def _main_menu():
    return {"inline_keyboard": [
        [{"text": "📅 Partidos de Hoy (Gratis)", "callback_data": "partidos"}],
        [{"text": "🆓 Pick Gratis del Día",       "callback_data": "buy:free"}],
        [{"text": "⚡ Pro del Día — ₡500",        "callback_data": "buy:pro"},
         {"text": "👑 Premium — ₡1,000",          "callback_data": "buy:premium"}],
        [{"text": "📋 Quiniela — ₡300",           "callback_data": "buy:quiniela"},
         {"text": "⚽ Un Partido — ₡200",         "callback_data": "buy:partido"}],
        [{"text": "🎯 Parlay — ₡250",             "callback_data": "buy:parlay"},
         {"text": "🥅 Goleadores — ₡300",         "callback_data": "buy:goleadores"}],
        [{"text": "🧠 Ryder Pro Deep-Dive — ₡350","callback_data": "buy:deepdive"}],
        [{"text": "📊 Informe Mundial — ₡400",    "callback_data": "buy:informe"}],
        [{"text": "── COMBOS ──",                  "callback_data": "noop"}],
        [{"text": "🌍 Combo Mundial ₡800",         "callback_data": "buy:combo_mundial"}],
        [{"text": "💰 Combo Apostador ₡650",       "callback_data": "buy:combo_apostador"}],
        [{"text": "🏆 Combo Total ProGol ₡1,200", "callback_data": "buy:combo_total"}],
        [{"text": "💚 Apoyar a ProGol CR",         "callback_data": "donate"}],
    ]}

def _approval_kb(buyer_chat_id, product_key):
    return {"inline_keyboard": [[
        {"text": "✅ Aprobar y enviar", "callback_data": f"approve:{buyer_chat_id}:{product_key}"},
        {"text": "❌ Rechazar",         "callback_data": f"reject:{buyer_chat_id}:{product_key}"},
    ]]}

# ── Mensaje de ganador (cuando un pick pega) ───────────────────────────────────
def send_winner_announcement(token, channel_or_chat, match, pick, result):
    """
    Llama esto cuando un pick gratis del día acertó.
    Envía GIF animado ProGol CR con mensaje de celebración.
    """
    caption = (
        f"🎉 *¡PICK GANADOR!*\n\n"
        f"⚽ *{match}*\n"
        f"✅ Pick: *{pick}*\n"
        f"📊 Resultado: *{result}*\n\n"
        f"💚 *Queremos que todos ganen.*\n"
        f"Ryder lo vio venir. Mañana hay más.\n\n"
        f"¿Querés los picks completos del día? Escribí /comprar\n"
        f"_ProGol CR · El análisis que te da ventaja_ 🐕"
    )
    gif_path = WINNER_GIF if os.path.exists(WINNER_GIF) else None
    if gif_path:
        _send_animation(token, channel_or_chat, gif_path, caption)
    else:
        _send_photo(token, channel_or_chat, caption)

BIENVENIDA = """\
🐕 *¡Bienvenido a ProGol CR, {first}!*

Somos la comunidad costarricense de análisis deportivo para la Copa del Mundo 2026.
Ryder, nuestro scout, analiza cada partido para que apostés con criterio.

━━━━━━━━━━━━━━━━━━━━━━━
📖 *¿Cómo usar el bot?*

📅 *Partidos de Hoy* — Ve todos los partidos del día, hora CR y canal
🆓 *Pick Gratis* — Recibí el mejor pick del día sin costo
⚡ *Pro / 👑 Premium* — Picks completos con análisis de Ryder
📋 *Quiniela* — Pronóstico de todos los partidos
🧠 *Ryder Pro* — Análisis profundo de un partido
📊 *Informe Mundial* — Panorama completo del torneo
💰 *Combos* — Paquetes con descuento

━━━━━━━━━━━━━━━━━━━━━━━
⌨️ *Comandos rápidos:*

/menu — Ver el menú de productos
/partidos — Partidos de hoy con hora y canal
/comprar — Lo mismo que el menú
/donar — Apoyar a ProGol CR

━━━━━━━━━━━━━━━━━━━━━━━
💚 *Queremos que todos ganen.*
_ProGol CR · No es consejo financiero_
"""

def _is_group(msg):
    return msg.get("chat", {}).get("type") in ("group", "supergroup", "channel")

def _bot_username(token):
    try:
        r = _api(token, "getMe", {})
        return r.get("result", {}).get("username", "")
    except Exception:
        return ""

def _welcome(token, chat_id, first, is_new=False):
    """Envía bienvenida completa (primera vez) o menú simple (regresa)."""
    if is_new:
        _send(token, chat_id, BIENVENIDA.format(first=first or "campeón"))
        time.sleep(0.5)
    _send(token, chat_id,
          f"👇 *Elegí tu producto:*",
          reply_markup=_main_menu())

def _group_welcome(token, chat_id, title):
    """Mensaje de bienvenida cuando el bot entra a un grupo."""
    _send(token, chat_id,
          f"🐕 *¡Hola a todos en {title}!*\n\n"
          f"Soy el bot de *ProGol CR*, tu comunidad de análisis para la Copa del Mundo 2026.\n\n"
          f"*¿Qué puedo hacer acá?*\n"
          f"📅 /partidos — Partidos de hoy con hora CR y canal\n"
          f"🆓 /pick — Pick gratis del día\n"
          f"📋 /quiniela — Quiniela del día\n"
          f"🛒 /comprar — Ver todos los productos con precios\n"
          f"❓ /ayuda — Cómo funciona ProGol CR\n\n"
          f"💚 *Queremos que todos ganen.*\n"
          f"_ProGol CR · No es consejo financiero_")

# ── Handlers ───────────────────────────────────────────────────────────────────
def _handle_message(token, owner_chat_id, msg):
    chat_id   = str(msg["chat"]["id"])
    text      = msg.get("text", "").strip()
    first     = msg.get("from", {}).get("first_name", "")
    username  = msg.get("from", {}).get("username", "")
    is_group  = _is_group(msg)

    # Bot agregado a un grupo nuevo
    new_members = msg.get("new_chat_members", [])
    if new_members:
        bot_info = _api(token, "getMe", {})
        bot_id   = bot_info.get("result", {}).get("id")
        if any(m.get("id") == bot_id for m in new_members):
            group_title = msg["chat"].get("title", "el grupo")
            _group_welcome(token, chat_id, group_title)
            # Guardar group_chat_id en config si no está
            _save_group_chat_id(chat_id)
        return

    # En grupos: solo responder a comandos explícitos (no a cualquier mensaje)
    if is_group and not text.startswith("/"):
        return

    # Normalizar comando (remover @botname si viene en grupo)
    cmd = text.split("@")[0].lower() if text.startswith("/") else text.lower()

    with _lock:
        state  = _state.get(chat_id, {"step": "idle"})
        is_new = not is_group and state.get("step") == "idle" and "welcomed" not in state

    # /id — responde el chat_id (grupo o privado)
    if cmd == "/id":
        tipo = "grupo" if is_group else "chat privado"
        _send(token, chat_id, f"ID de este {tipo}: `{chat_id}`")
        if is_group:
            _save_group_chat_id(chat_id)
            _send(token, chat_id, "Grupo registrado en ProGol CR.")
        return

    # Plan Gurú — detectar "Tengo X" o "Tengo X para [partido]" en privado (solo owner)
    if not is_group and chat_id == str(owner_chat_id):
        tl = text.lower()
        if ("tengo" in tl or "presupuesto" in tl) and _re.search(r'\d{3,6}', text.replace(",","").replace(".","").replace("₡","")):
            budget = _parse_budget(text)
            if budget and budget >= 500:
                team_filter = _extract_team_filter(text)
                _send(token, chat_id, "Analizando con Ryder...")
                _send_guru_plan(token, chat_id, budget, team_filter)
                return

    # /link — envía el URL público de la app
    if cmd == "/link":
        cfg_now = _load_config()
        url = cfg_now.get("current_tunnel_url", "").strip()
        if url:
            _send(token, chat_id,
                  f"🔗 *ProGol CR — App*\n\n{url}\n\n"
                  f"Abrí ese link en el navegador para acceder a la app.")
        else:
            _send(token, chat_id,
                  "El servidor no tiene un link público activo en este momento. "
                  "Asegurate de que el servidor esté corriendo con tunnel activo.")
        return

    # /grupos — desde chat privado del owner, lista los chats donde esta el bot
    if cmd == "/grupos" and chat_id == str(owner_chat_id):
        gid = _group_chat_id or "no configurado"
        _send(token, chat_id,
              f"Group chat ID actual: `{gid}`\n\n"
              f"Para configurar manualmente el grupo:\n"
              f"1. Saca el bot del grupo\n"
              f"2. Vuelve a agregarlo\n"
              f"3. Escribe /id en el grupo\n\n"
              f"O enviame el ID manualmente con:\n/setgrupo -1001234567890")
        return

    if cmd.startswith("/setgrupo") and chat_id == str(owner_chat_id):
        parts = text.split()
        if len(parts) == 2:
            gid = parts[1]
            _save_group_chat_id(gid)
            _send(token, chat_id, f"Grupo configurado: `{gid}`")
        return

    # Clave secreta — documentos corporativos (solo owner, solo privado)
    if not is_group and chat_id == str(owner_chat_id):
        cfg_now = _load_config()
        secret  = cfg_now.get("corp_secret", "").strip().lower()
        if secret and text.strip().lower() == secret:
            _send(token, chat_id, "🔐 Verificando identidad...")
            time.sleep(0.5)
            _send_corp_docs(token, chat_id)
            return

    # Comandos de info
    if cmd in ("/partidos", "/hoy"):
        _send_partidos_img(token, chat_id)
        return

    if cmd in ("/pick", "/free"):
        _send_free_pick_img(token, chat_id)
        if not is_group:
            time.sleep(0.5)
            _send(token, chat_id, "¿Querés más picks? 👇", reply_markup=_main_menu())
        return

    if cmd == "/quiniela":
        _send(token, chat_id, _get_quiniela())
        return

    if cmd == "/ayuda":
        _send(token, chat_id, BIENVENIDA.format(first=first or "campeón"))
        return

    if cmd == "/donar":
        _send(token, chat_id,
              f"💚 *Gracias por apoyar a ProGol CR*\n\n"
              f"*SINPE Móvil:* 8561-0677 (Esteban V.)\n"
              f"Cualquier monto es bienvenido.\n\n"
              f"💚 ProGol CR quiere que todos ganen.")
        return

    # En grupos: /comprar manda al DM privado con el bot
    if is_group and cmd in ("/comprar", "/menu", "/picks"):
        bot_un = _bot_username(token)
        link   = f"https://t.me/{bot_un}" if bot_un else "el bot"
        _send(token, chat_id,
              f"🛒 Para comprar picks escribile directo al bot en privado:\n"
              f"👉 {link}\n\n"
              f"_Ahí podés ver todos los productos y pagar de forma segura._")
        return

    # Chat privado: flujo normal
    # Esperando comprobante de pago
    if state.get("step") == "waiting_sinpe":
        product_key = state.get("product_key", "")
        all_prod    = {**PRODUCTS, **COMBOS}
        prod        = all_prod.get(product_key, {})
        _send(token, chat_id,
              f"✅ *Comprobante recibido.* Verificando el pago.\n"
              f"En menos de 5 minutos recibís todo. 🐕")
        buyer_name = f"@{username}" if username else (first or chat_id)
        _send(token, owner_chat_id,
              f"💰 *Nuevo pago*\n"
              f"👤 {buyer_name} (chat: `{chat_id}`)\n"
              f"{prod.get('emoji','')} *{prod.get('name',product_key)}*\n"
              f"💵 ₡{prod.get('price',0):,}\n\nAprobás el envío?",
              reply_markup=_approval_kb(chat_id, product_key))
        with _lock:
            _state[chat_id] = {"step": "pending_approval", "product_key": product_key}
        return

    # /start → bienvenida completa primera vez
    if text == "/start" or is_new:
        with _lock:
            _state[chat_id] = {"step": "menu", "welcomed": True, "username": username or first}
        _welcome(token, chat_id, first, is_new=True)
        return

    # /menu, /comprar, /picks o cualquier otro mensaje → menú directo
    with _lock:
        _state[chat_id] = {"step": "menu", "welcomed": True, "username": username or first}
    _welcome(token, chat_id, first, is_new=False)

def _handle_callback(token, owner_chat_id, cb):
    chat_id    = str(cb["message"]["chat"]["id"])
    message_id = cb["message"]["message_id"]
    data       = cb.get("data", "")
    cb_id      = cb["id"]

    # SIEMPRE responder al callback primero para quitar el spinner de Telegram
    try:
        _answer_callback(token, cb_id)
    except Exception:
        pass

def _handle_callback(token, owner_chat_id, cb):
    chat_id    = str(cb["message"]["chat"]["id"])
    message_id = cb["message"]["message_id"]
    data       = cb.get("data", "")
    cb_id      = cb["id"]

    if data == "noop":
        return

    # Partidos de hoy
    if data == "partidos":
        _send_partidos_img(token, chat_id)
        return

    # Donación
    if data == "donate":
        _send(token, chat_id,
              f"💚 *Gracias por apoyar ProGol CR*\n\n"
              f"*SINPE Móvil:* 8561-0677 (Esteban V.)\n"
              f"Cualquier monto nos ayuda. Ryder sigue trabajando por vos 🐕\n\n"
              f"¡Compartí el canal con alguien y esa también es una donación!")
        return

    # Comprar producto
    if data.startswith("buy:"):
        key  = data.split(":", 1)[1]
        prod = {**PRODUCTS, **COMBOS}.get(key)
        if not prod:
            return
        if prod["price"] == 0:
            if key == "free":
                _send_free_pick_img(token, chat_id)
            else:
                content = CONTENT_MAP.get(key, lambda: "")()
                _send(token, chat_id, content)
            with _lock:
                _state[chat_id] = {"step": "idle"}
            return
        with _lock:
            _state[chat_id] = {"step": "waiting_sinpe", "product_key": key}
        _send(token, chat_id,
              f"{prod['emoji']} *{prod['name']}*\n\n"
              f"💰 Precio: *₡{prod['price']:,}*\n\n"
              f"📱 Realizá el SINPE a:\n"
              f"Número: *8561-0677*\n"
              f"Nombre: *Esteban V.*\n"
              f"Monto: *₡{prod['price']:,}*\n\n"
              f"Luego enviame el comprobante (foto o número de transacción) 👇\n"
              f"_En menos de 5 minutos tenés todo. 🐕_")
        return

    # Aprobar (solo el dueño)
    if data.startswith("approve:") and chat_id == str(owner_chat_id):
        _, buyer_id, key = data.split(":", 2)
        prod = {**PRODUCTS, **COMBOS}.get(key, {})
        try:
            content = CONTENT_MAP.get(key, lambda: "Contenido no disponible.")()
        except Exception as e:
            content = f"Error generando contenido: {e}"
        _send(token, buyer_id, content)
        _send(token, buyer_id,
              f"🎉 *¡Listo! Aquí están tus picks.*\n"
              f"💚 Ryder los analizó uno por uno. Queremos que ganes.\n\n"
              f"Si el pick pega, contanos — nos alegra saber que te fue bien. 🐕\n"
              f"_ProGol CR · /comprar para el próximo día_")
        _edit_message(token, chat_id, message_id,
                      f"✅ Enviado a `{buyer_id}` — {prod.get('emoji','')} {prod.get('name','')}")
        with _lock:
            _state[buyer_id] = {"step": "idle"}
        return

    # Rechazar
    if data.startswith("reject:") and chat_id == str(owner_chat_id):
        _, buyer_id, _ = data.split(":", 2)
        _send(token, buyer_id,
              f"❌ No pudimos verificar tu pago.\n"
              f"Escribinos directamente y lo resolvemos. 🐕")
        _edit_message(token, chat_id, message_id, "❌ Rechazado")
        with _lock:
            _state[buyer_id] = {"step": "idle"}
        return

# ── Pre-match promo scheduler ──────────────────────────────────────────────────
_sent_promos = set()   # set de "home|away|date" ya enviados

def _promo_loop(token, owner_chat_id, stop_event):
    """Revisa cada 5 min si hay partidos mundialistas en la próxima hora y envía promo."""
    while not (stop_event and stop_event.is_set()):
        try:
            sys.path.insert(0, HERE)
            import db, sqlite3
            db.init_db()
            now_utc = datetime.datetime.utcnow()
            today   = now_utc.date().isoformat()
            conn    = db.get_conn()
            conn.row_factory = sqlite3.Row
            # Partidos mundialistas con kickoff en los próximos 30-75 min
            cur = conn.execute(
                "SELECT DISTINCT home, away, kickoff_utc, competition FROM matches "
                "WHERE date=? AND home!='' AND away!='' "
                "AND (competition LIKE '%World Cup%' OR competition LIKE '%FIFA%' OR is_wc=1) "
                "AND status='Scheduled' "
                "ORDER BY kickoff_utc",
                (today,)
            )
            rows = cur.fetchall()
            conn.close()
            for r in rows:
                key = f"{r['home']}|{r['away']}|{today}"
                if key in _sent_promos:
                    continue
                if not r["kickoff_utc"]:
                    continue
                try:
                    k = r["kickoff_utc"].replace("Z", "").replace("T", " ")[:16]
                    kick = datetime.datetime.strptime(k, "%Y-%m-%d %H:%M")
                    mins_to_kick = (kick - now_utc).total_seconds() / 60
                    if 30 <= mins_to_kick <= 75:
                        h, a = es(r["home"]), es(r["away"])
                        # Hora CR (UTC-6)
                        kick_cr = kick - datetime.timedelta(hours=6)
                        hora_cr = kick_cr.strftime("%I:%M %p")
                        # Predicción rápida
                        pick_txt = ""
                        try:
                            import model
                            p = model.predict(r["home"], r["away"])
                            prob = p["prob"]
                            if prob["home"] > prob["away"] and prob["home"] > prob["draw"]:
                                pick_txt = f"\n🔮 Ryder ve a *{h}* como favorito ({prob['home']/100:.0%})"
                            elif prob["draw"] >= prob["home"] and prob["draw"] >= prob["away"]:
                                pick_txt = f"\n🔮 Ryder proyecta *empate* ({prob['draw']/100:.0%})"
                            else:
                                pick_txt = f"\n🔮 Ryder ve a *{a}* como favorito ({prob['away']/100:.0%})"
                        except Exception:
                            pass
                        import random
                        intros = [
                            f"En {int(mins_to_kick)} minutos arranca y Ryder ya tiene el analisis listo. 🔥",
                            f"Faltan {int(mins_to_kick)} minutos. Este es el partido del dia. 🎯",
                            f"ProGol CR tiene el pick para este partido. Quedan {int(mins_to_kick)} minutos. ⏱",
                        ]
                        ctas = [
                            "Queres el pick completo con probabilidades y cuota justa? Escribi /comprar antes del pitazo.",
                            "El analisis completo de Ryder esta en /comprar. No apostes sin verlo.",
                            "Todos los picks del dia con analisis matematico estan en /comprar.",
                        ]
                        msg = (
                            f"⚽ *{h} vs {a}*\n"
                            f"🏆 Copa del Mundo 2026 · {hora_cr} CR\n\n"
                            f"{random.choice(intros)}"
                            f"{pick_txt}\n\n"
                            f"{random.choice(ctas)}\n\n"
                            f"💚 *ProGol CR · Queremos que todos ganen*"
                        )
                        targets = [owner_chat_id]
                        if _group_chat_id and _group_chat_id != owner_chat_id:
                            targets.append(_group_chat_id)
                        for target in targets:
                            _api(token, "sendMessage", {
                                "chat_id": target,
                                "text": msg,
                                "parse_mode": "Markdown",
                            })
                        _sent_promos.add(key)
                        print(f"[bot] Promo enviada: {h} vs {a} en {int(mins_to_kick)} min")
                except Exception as e:
                    print(f"[bot] promo error {r['home']}: {e}")
        except Exception as e:
            print(f"[bot] promo loop error: {e}")
        # Revisar cada 5 minutos
        for _ in range(60):
            if stop_event and stop_event.is_set():
                return
            time.sleep(5)

# ── Loop de polling ────────────────────────────────────────────────────────────
def run_bot(token, owner_chat_id, stop_event=None):
    offset = 0
    conflict_backoff = 5
    print(f"[bot] Polling activo (owner={owner_chat_id})")
    # Cerrar cualquier sesión de polling/webhook anterior para evitar 409
    try:
        _api(token, "deleteWebhook", {"drop_pending_updates": True})
        print("[bot] Webhook eliminado + updates pendientes descartados")
    except Exception:
        pass
    time.sleep(1)  # dar tiempo a que otras instancias detecten el cierre
    # Limpiar updates acumulados para que botones viejos no fallen
    try:
        res = _api(token, "getUpdates", {"offset": -1, "timeout": 1})
        if res.get("result"):
            offset = res["result"][-1]["update_id"] + 1
            print(f"[bot] Saltando {len(res['result'])} updates acumulados, offset={offset}")
    except Exception:
        pass
    while not (stop_event and stop_event.is_set()):
        try:
            res = _api(token, "getUpdates", {"offset": offset, "timeout": 25})
            conflict_backoff = 5  # reset on success
            for update in res.get("result", []):
                offset = update["update_id"] + 1
                try:
                    if "message" in update:
                        _handle_message(token, owner_chat_id, update["message"])
                    elif "callback_query" in update:
                        _handle_callback(token, owner_chat_id, update["callback_query"])
                except Exception as e:
                    print(f"[bot] handler error: {e}")
        except Exception as e:
            err = str(e)
            if "409" in err or "Conflict" in err:
                # Another instance polling — back off and let it win or timeout
                print(f"[bot] 409 conflicto — esperando {conflict_backoff}s para reconectar...")
                time.sleep(conflict_backoff)
                conflict_backoff = min(conflict_backoff * 2, 60)  # exp backoff up to 60s
            else:
                print(f"[bot] polling error: {e}")
                time.sleep(5)

def start_bot_thread(cfg):
    global _group_chat_id
    token    = (cfg.get("telegram_bot_token") or "").strip()
    owner_id = (cfg.get("telegram_chat_id") or "").strip()
    if not token or not owner_id:
        print("[bot] Telegram no configurado — bot inactivo")
        return None
    # Cargar group_chat_id si ya estaba guardado
    _group_chat_id = (cfg.get("group_chat_id") or "").strip() or None
    if _group_chat_id:
        print(f"[bot] Grupo configurado: {_group_chat_id}")
    stop = threading.Event()
    threading.Thread(target=run_bot,     args=(token, owner_id, stop), daemon=True).start()
    threading.Thread(target=_promo_loop, args=(token, owner_id, stop), daemon=True).start()
    print("[bot] Bot de ventas activo — enviá /start al bot de Telegram")
    print("[bot] Scheduler de promos activo (revisa cada 5 min)")
    return stop

if __name__ == "__main__":
    cfg = {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        sys.exit(f"Error config: {e}")
    run_bot(cfg.get("telegram_bot_token", ""), cfg.get("telegram_chat_id", ""))
