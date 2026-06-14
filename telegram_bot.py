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

def _get_free_pick():
    rows, today = _today_matches(6)
    if not rows:
        return "No hay partidos programados para hoy."
    import model
    best, best_conf = None, 0
    for r in rows:
        try:
            pred = model.predict(r["home"], r["away"])
            if pred.get("conf", 0) > best_conf:
                best_conf = pred["conf"]
                best = (r["home"], r["away"], pred)
        except Exception:
            continue
    if not best:
        return "No se pudo generar el pick de hoy."
    home, away, p = best
    prob = p["prob"]
    h_es, a_es = es(home), es(away)
    if prob["home"] >= prob["away"] and prob["home"] >= prob["draw"]:
        pick_text, pick_prob = f"{h_es} gana", prob["home"] / 100
    elif prob["draw"] >= prob["home"] and prob["draw"] >= prob["away"]:
        pick_text, pick_prob = "Empate", prob["draw"] / 100
    else:
        pick_text, pick_prob = f"{a_es} gana", prob["away"] / 100
    conf = int(round(p.get("conf", 0)))
    fair = round(1 / pick_prob, 2) if pick_prob > 0 else 0
    stars = "⭐" * min(conf, 10)
    return (
        f"🐕 *PICK GRATIS DEL DÍA*\n"
        f"📅 {today} · Copa del Mundo 2026\n\n"
        f"⚽ *{h_es} vs {a_es}*\n\n"
        f"🎯 Pick: *{pick_text}*\n"
        f"📊 Probabilidad: *{pick_prob:.0%}*\n"
        f"💰 Cuota justa: *{fair}*\n"
        f"🔥 Confianza Ryder: *{conf}/10* {stars}\n\n"
        f"_Analizado por Ryder, el scout de ProGol CR 🐕_\n\n"
        f"¿Querés todos los picks del día? Escribí /comprar"
    )

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

def _fetch_partidos_rows(limit=8):
    """Devuelve lista de dicts con datos de partidos de hoy (sin terminados)."""
    import db, sqlite3
    db.init_db()
    today = datetime.date.today().isoformat()
    conn  = db.get_conn()
    conn.row_factory = sqlite3.Row
    cur = conn.execute(
        "SELECT home, away, kickoff_utc, competition, home_badge, away_badge "
        "FROM matches WHERE date=? AND home!='' AND away!='' "
        "AND NOT EXISTS ("
        "  SELECT 1 FROM matches m2 "
        "  WHERE m2.home=matches.home AND m2.away=matches.away "
        "  AND m2.status IN ('Finished','Live','FT','AET','PEN')"
        ") GROUP BY home, away ORDER BY kickoff_utc LIMIT ?",
        (today, limit)
    )
    rows = []
    for r in cur.fetchall():
        d = dict(r)
        d["home_es"] = es(d["home"])
        d["away_es"] = es(d["away"])
        hora = ""
        if d["kickoff_utc"]:
            try:
                k  = d["kickoff_utc"].replace("Z", "").replace("T", " ")[:16]
                dt = datetime.datetime.strptime(k, "%Y-%m-%d %H:%M")
                dt_cr = dt - datetime.timedelta(hours=6)
                hora  = dt_cr.strftime("%I:%M %p")
            except Exception:
                pass
        d["hora_cr"] = hora
        rows.append(d)
    conn.close()
    return rows, today

def _send_partidos_img(token, chat_id):
    """Genera imagen de partidos y la envía como foto. Fallback a texto."""
    rows, today = _fetch_partidos_rows()
    if not rows:
        _send(token, chat_id, f"📅 No hay partidos programados para hoy ({today}).")
        return
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
        caption = "⚽ *Partidos de hoy* · Para picks detallados: /comprar 👇\n_ProGol CR_"
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

# ── Handlers ───────────────────────────────────────────────────────────────────
def _handle_message(token, owner_chat_id, msg):
    chat_id   = str(msg["chat"]["id"])
    text      = msg.get("text", "").strip()
    first     = msg.get("from", {}).get("first_name", "")
    username  = msg.get("from", {}).get("username", "")

    with _lock:
        state = _state.get(chat_id, {"step": "idle"})

    # Comandos principales
    if text in ("/partidos", "/hoy"):
        _send_partidos_img(token, chat_id)
        return

    if text in ("/start", "/menu", "/comprar", "/picks"):
        with _lock:
            _state[chat_id] = {"step": "menu", "username": username or first}
        _send(token, chat_id,
              f"🐕 *¡Hola {first or 'campeón'}!* Bienvenido a *ProGol CR*\n\n"
              f"Ryder analizó los partidos del día. Elegí tu producto 👇",
              reply_markup=_main_menu())
        return

    if text == "/donar":
        _send(token, chat_id,
              f"💚 *Gracias por apoyar a ProGol CR*\n\n"
              f"Tu donación ayuda a mantener a Ryder analizando cada partido.\n\n"
              f"*SINPE Móvil:* 8561-0677 (Esteban V.)\n"
              f"Cualquier monto es bienvenido — el proyecto es de la comunidad.\n\n"
              f"Si querés que sigamos creciendo, compartí el canal con alguien.\n"
              f"💚 ProGol CR quiere que todos ganen.")
        return

    # Esperando comprobante
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

    # Cualquier otro mensaje → mostrar menú
    with _lock:
        _state[chat_id] = {"step": "menu", "username": username or first}
    _send(token, chat_id,
          f"🐕 *¡Hola {first or 'campeón'}!* Bienvenido a *ProGol CR*\n\n"
          f"Ryder analizó los partidos del día. Elegí tu producto 👇",
          reply_markup=_main_menu())

def _handle_callback(token, owner_chat_id, cb):
    chat_id    = str(cb["message"]["chat"]["id"])
    message_id = cb["message"]["message_id"]
    data       = cb.get("data", "")
    cb_id      = cb["id"]

    if data == "noop":
        _answer_callback(token, cb_id)
        return

    # Partidos de hoy
    if data == "partidos":
        _answer_callback(token, cb_id, "Cargando partidos...")
        _send_partidos_img(token, chat_id)
        return

    # Donación
    if data == "donate":
        _answer_callback(token, cb_id)
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
            _answer_callback(token, cb_id, "Producto no encontrado")
            return
        _answer_callback(token, cb_id)
        if prod["price"] == 0:
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
        _answer_callback(token, cb_id, "✅ Enviando...")
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
        _answer_callback(token, cb_id, "❌ Rechazado")
        _send(token, buyer_id,
              f"❌ No pudimos verificar tu pago.\n"
              f"Escribinos directamente y lo resolvemos. 🐕")
        _edit_message(token, chat_id, message_id, "❌ Rechazado")
        with _lock:
            _state[buyer_id] = {"step": "idle"}
        return

    _answer_callback(token, cb_id)

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
                        msg = (
                            f"⚽🔔 *¡PARTIDO EN {int(mins_to_kick)} MINUTOS!*\n\n"
                            f"🏆 *Copa del Mundo 2026*\n"
                            f"*{h} vs {a}*\n"
                            f"🕐 {hora_cr} (hora Costa Rica){pick_txt}\n\n"
                            f"💡 ¿Querés los picks completos para este partido?\n"
                            f"Escribí /comprar y Ryder te da todo antes del pitazo.\n\n"
                            f"💚 *ProGol CR · Queremos que todos ganen* 🐕"
                        )
                        _api(token, "sendMessage", {
                            "chat_id": owner_chat_id,
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
    print(f"[bot] Polling activo (owner={owner_chat_id})")
    # Limpiar updates acumulados para que botones viejos no fallen
    res = _api(token, "getUpdates", {"offset": -1, "timeout": 1})
    if res.get("result"):
        offset = res["result"][-1]["update_id"] + 1
        print(f"[bot] Saltando {len(res['result'])} updates acumulados, offset={offset}")
    while not (stop_event and stop_event.is_set()):
        try:
            res = _api(token, "getUpdates", {"offset": offset, "timeout": 25})
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
            print(f"[bot] polling error: {e}")
            time.sleep(5)

def start_bot_thread(cfg):
    token    = (cfg.get("telegram_bot_token") or "").strip()
    owner_id = (cfg.get("telegram_chat_id") or "").strip()
    if not token or not owner_id:
        print("[bot] Telegram no configurado — bot inactivo")
        return None
    stop = threading.Event()
    threading.Thread(target=run_bot,      args=(token, owner_id, stop), daemon=True).start()
    threading.Thread(target=_promo_loop,  args=(token, owner_id, stop), daemon=True).start()
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
