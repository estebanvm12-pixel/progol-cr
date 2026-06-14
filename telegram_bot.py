#!/usr/bin/env python3
"""
ProGol CR — Bot de ventas Telegram
Flujo: cliente elige producto → paga SINPE → envía comprobante →
       Esteban aprueba con un botón → bot entrega los picks automáticamente.

Corre como hilo de fondo dentro de server.py (start_bot_thread)
o como proceso independiente: python telegram_bot.py
"""

import json
import os
import sys
import time
import threading
import urllib.request
import urllib.parse
import urllib.error
import datetime

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")

# ── Productos ──────────────────────────────────────────────────────────────────
PRODUCTS = {
    "free": {
        "name": "Pick Gratis del Día",
        "price": 0,
        "desc": "El pick más seguro del modelo — gratis siempre.",
        "emoji": "🆓",
    },
    "pro": {
        "name": "Pro del Día",
        "price": 500,
        "desc": "Todos los picks del día (3 por partido) + Parlay Seguro + Parlay Valor.",
        "emoji": "⚡",
    },
    "premium": {
        "name": "Premium del Día",
        "price": 1000,
        "desc": "Todo Pro + Quiniela completa + Goleadores esperados + Ryder Deep-Dive.",
        "emoji": "👑",
    },
    "quiniela": {
        "name": "Quiniela del Día",
        "price": 300,
        "desc": "Predicción 1X2 de todos los partidos del día con probabilidades.",
        "emoji": "📋",
    },
    "partido": {
        "name": "Picks de un Partido",
        "price": 200,
        "desc": "Los 3 picks del modelo para un partido específico.",
        "emoji": "⚽",
    },
    "parlay": {
        "name": "Parlay Armado",
        "price": 250,
        "desc": "Una combinada lista (3–5 patas) con cuota total y probabilidad.",
        "emoji": "🎯",
    },
    "goleadores": {
        "name": "Datos de Goleadores",
        "price": 300,
        "desc": "Goles esperados por jugador + probabilidad de anotar (todos los partidos).",
        "emoji": "🥅",
    },
    "informe": {
        "name": "Informe Mundial",
        "price": 400,
        "desc": "Tabla de grupos + clasificación Elo + proyección de quién avanza.",
        "emoji": "📊",
    },
    "deepdive": {
        "name": "Ryder Deep-Dive",
        "price": 350,
        "desc": "Análisis táctico profundo de un partido específico.",
        "emoji": "🧠",
    },
}

# Combos
COMBOS = {
    "combo_mundial": {
        "name": "Combo Mundial Completo",
        "price": 800,
        "desc": "Quiniela + Informe Mundial + Pick gratis destacado. Ideal para jornada completa.",
        "emoji": "🌍",
        "includes": ["quiniela", "informe"],
    },
    "combo_apostador": {
        "name": "Combo Apostador",
        "price": 650,
        "desc": "Todos los picks del día + Parlay armado. Para apostar con criterio.",
        "emoji": "💰",
        "includes": ["pro", "parlay"],
    },
    "combo_total": {
        "name": "Combo Total ProGol",
        "price": 1200,
        "desc": "TODO: picks, quiniela, goleadores, parlays, deep-dive, informe. El máximo.",
        "emoji": "🏆",
        "includes": ["premium", "informe"],
    },
}

# Estado de conversación por chat_id
_state = {}   # {chat_id: {"step": str, "product_key": str, "username": str}}
_lock = threading.Lock()

# ── API helpers ────────────────────────────────────────────────────────────────
def _cfg():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _api(token, method, payload=None, files=None):
    url = f"https://api.telegram.org/bot{token}/{method}"
    if payload:
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data,
                                     headers={"Content-Type": "application/json",
                                              "User-Agent": "ProGolCR/1.0"})
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "ProGolCR/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode("utf-8"))
    except Exception as e:
        print(f"[bot] API error {method}: {e}")
        return {}

def _send(token, chat_id, text, reply_markup=None, parse_mode="Markdown"):
    payload = {"chat_id": chat_id, "text": text, "parse_mode": parse_mode}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    return _api(token, "sendMessage", payload)

def _answer_callback(token, callback_id, text=""):
    _api(token, "answerCallbackQuery", {"callback_query_id": callback_id, "text": text})

def _edit_message(token, chat_id, message_id, text, reply_markup=None):
    payload = {"chat_id": chat_id, "message_id": message_id,
               "text": text, "parse_mode": "Markdown"}
    if reply_markup:
        payload["reply_markup"] = reply_markup
    _api(token, "editMessageText", payload)

# ── Generadores de contenido ───────────────────────────────────────────────────
def _get_free_pick():
    """Genera el pick gratis del día usando el modelo Poisson."""
    try:
        sys.path.insert(0, HERE)
        import model, db
        db.init_db()
        today = datetime.date.today().isoformat()
        conn = db.get_conn()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.execute(
            "SELECT DISTINCT home, away FROM matches "
            "WHERE date=? AND status='Scheduled' AND home!='' AND away!='' LIMIT 6",
            (today,)
        )
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return "No hay partidos programados para hoy."
        best = None
        best_conf = 0
        for r in rows:
            try:
                pred = model.predict(r["home"], r["away"])
                conf = pred.get("conf", 0)
                if conf > best_conf:
                    best_conf = conf
                    best = (r["home"], r["away"], pred)
            except Exception:
                continue
        if not best:
            return "No se pudo calcular el pick del día."
        home, away, p = best
        prob = p["prob"]
        eg = p["expectedGoals"]
        if prob["home"] >= prob["away"] and prob["home"] >= prob["draw"]:
            pick_text = f"{home} gana"
            pick_prob = prob["home"] / 100
        elif prob["draw"] >= prob["home"] and prob["draw"] >= prob["away"]:
            pick_text = "Empate"
            pick_prob = prob["draw"] / 100
        else:
            pick_text = f"{away} gana"
            pick_prob = prob["away"] / 100
        conf_int = int(p.get("conf", 0) / 10)
        fair_odds = round(1 / pick_prob, 2) if pick_prob > 0 else 0
        return (
            f"🐕 *PICK GRATIS DEL DÍA — ProGol CR*\n"
            f"📅 {today}\n\n"
            f"⚽ *{home} vs {away}*\n"
            f"🎯 Pick: *{pick_text}*\n"
            f"📊 Probabilidad modelo: *{pick_prob:.0%}*\n"
            f"💰 Cuota justa: *{fair_odds}*\n"
            f"🔥 Confianza Ryder: *{conf_int}/10*\n\n"
            f"_Modelo Dixon-Coles + Elo · ProGol CR_"
        )
    except Exception as e:
        return f"Pick del día temporalmente no disponible ({e})."

def _get_pro_picks():
    """Genera picks Pro del día — todos los partidos."""
    try:
        sys.path.insert(0, HERE)
        import model, db
        db.init_db()
        today = datetime.date.today().isoformat()
        conn = db.get_conn()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.execute(
            "SELECT DISTINCT home, away FROM matches "
            "WHERE date=? AND status='Scheduled' AND home!='' AND away!='' LIMIT 8",
            (today,)
        )
        rows = cur.fetchall()
        conn.close()
        if not rows:
            return "No hay partidos programados para hoy."
        lines = [f"⚡ *PICKS PRO DEL DÍA — ProGol CR*\n📅 {today}\n"]
        parlays_safe = []
        for r in rows:
            try:
                p = model.predict(r["home"], r["away"])
                prob = p["prob"]
                eg = p["expectedGoals"]
                h, a = r["home"], r["away"]
                # Pick 1: resultado
                if prob["home"] >= 60:
                    r1 = f"{h} gana ({prob['home']/100:.0%})"
                elif prob["home"] + prob["draw"] >= 70:
                    r1 = f"Doble oportunidad {h} ({(prob['home']+prob['draw'])/100:.0%})"
                else:
                    r1 = f"X o {a} ({(prob['draw']+prob['away'])/100:.0%})"
                # Pick 2: goles
                if p.get("over25", 0) >= 55:
                    r2 = f"Más 2.5 goles ({p['over25']/100:.0%})"
                else:
                    r2 = f"Menos 2.5 goles ({p['under25']/100:.0%})"
                # Pick 3: BTTS
                btts = p.get("btts", 0)
                r3 = f"Ambos marcan: {'Sí' if btts > 50 else 'No'} ({btts/100:.0%})"
                lines.append(f"⚽ *{h} vs {a}*")
                lines.append(f"  1️⃣ {r1}")
                lines.append(f"  2️⃣ {r2}")
                lines.append(f"  3️⃣ {r3}\n")
                if prob["home"] >= 65 or (prob["home"] + prob["draw"]) >= 75:
                    parlays_safe.append((h, a, r1, prob["home"]/100))
            except Exception:
                continue
        # Parlay seguro
        if parlays_safe:
            lines.append("━━━━━━━━━━━━━━━━━━━━━━━")
            lines.append("🎯 *PARLAY SEGURO DEL DÍA*")
            for ph, pa, pick, prob in parlays_safe[:3]:
                lines.append(f"  • {ph} vs {pa}: {pick}")
            combo_odds = round(1.0, 2)
            for _, _, _, pr in parlays_safe[:3]:
                combo_odds *= round(1 / pr * 0.91, 2)
            lines.append(f"  💰 Cuota combinada aprox: *{combo_odds:.2f}*")
        lines.append("\n_ProGol CR · Análisis cuantitativo · No es consejo financiero_")
        return "\n".join(lines)
    except Exception as e:
        return f"Error generando picks Pro: {e}"

def _get_premium_picks():
    """Picks Premium — todo incluido."""
    pro = _get_pro_picks()
    try:
        sys.path.insert(0, HERE)
        import model, db
        today = datetime.date.today().isoformat()
        conn = db.get_conn()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.execute(
            "SELECT DISTINCT home, away FROM matches "
            "WHERE date=? AND status='Scheduled' AND home!='' AND away!='' LIMIT 8",
            (today,)
        )
        rows = cur.fetchall()
        conn.close()
        quiniela = [f"\n👑 *PREMIUM EXCLUSIVO*\n\n📋 *QUINIELA DEL DÍA*"]
        goleadores = ["\n🥅 *GOLES ESPERADOS (xG)*"]
        for r in rows:
            try:
                p = model.predict(r["home"], r["away"])
                prob = p["prob"]
                eg = p["expectedGoals"]
                h, a = r["home"], r["away"]
                if prob["home"] > prob["away"] and prob["home"] > prob["draw"]:
                    res = f"1 ({prob['home']/100:.0%})"
                elif prob["draw"] >= prob["home"] and prob["draw"] >= prob["away"]:
                    res = f"X ({prob['draw']/100:.0%})"
                else:
                    res = f"2 ({prob['away']/100:.0%})"
                quiniela.append(f"  {h} vs {a}: *{res}*")
                goleadores.append(f"  {h} xG: *{eg['home']:.1f}* | {a} xG: *{eg['away']:.1f}*")
            except Exception:
                continue
        return pro + "\n" + "\n".join(quiniela) + "\n" + "\n".join(goleadores)
    except Exception as e:
        return pro + f"\n\n[Premium extra no disponible: {e}]"

def _get_quiniela():
    try:
        sys.path.insert(0, HERE)
        import model, db
        db.init_db()
        today = datetime.date.today().isoformat()
        conn = db.get_conn()
        conn.row_factory = __import__("sqlite3").Row
        cur = conn.execute(
            "SELECT DISTINCT home, away FROM matches "
            "WHERE date=? AND status='Scheduled' AND home!='' AND away!='' LIMIT 10",
            (today,)
        )
        rows = cur.fetchall()
        conn.close()
        lines = [f"📋 *QUINIELA COMPLETA — {today}*\n_ProGol CR_\n"]
        for i, r in enumerate(rows, 1):
            try:
                p = model.predict(r["home"], r["away"])
                prob = p["prob"]
                h, a = r["home"], r["away"]
                if prob["home"] > prob["away"] and prob["home"] > prob["draw"]:
                    res, pct = "1", prob["home"]
                elif prob["draw"] >= prob["home"] and prob["draw"] >= prob["away"]:
                    res, pct = "X", prob["draw"]
                else:
                    res, pct = "2", prob["away"]
                lines.append(f"{i}. {h} vs {a}  →  *{res}* ({pct/100:.0%})")
            except Exception:
                lines.append(f"{i}. {r['home']} vs {r['away']}  →  ?")
        lines.append("\n_Modelo Dixon-Coles + Elo · ProGol CR_")
        return "\n".join(lines)
    except Exception as e:
        return f"Error generando quiniela: {e}"

CONTENT_MAP = {
    "free": _get_free_pick,
    "pro": _get_pro_picks,
    "premium": _get_premium_picks,
    "quiniela": _get_quiniela,
    "combo_mundial": lambda: _get_quiniela() + "\n\n" + "📊 *INFORME MUNDIAL*\nVer app en /informe",
    "combo_apostador": _get_pro_picks,
    "combo_total": _get_premium_picks,
    "partido": lambda: "Para picks de un partido específico, decime cuál partido te interesa.",
    "parlay": _get_pro_picks,
    "goleadores": lambda: _get_premium_picks(),
    "informe": lambda: "📊 *INFORME MUNDIAL 2026*\nVer clasificación y proyección en la app.",
    "deepdive": lambda: "🧠 Decime el partido para el que querés el análisis profundo de Ryder.",
}

# ── Teclados inline ────────────────────────────────────────────────────────────
def _main_menu_keyboard():
    return {
        "inline_keyboard": [
            [{"text": "🆓 Pick Gratis (₡0)", "callback_data": "buy:free"}],
            [
                {"text": "⚡ Pro (₡500/día)", "callback_data": "buy:pro"},
                {"text": "👑 Premium (₡1,000/día)", "callback_data": "buy:premium"},
            ],
            [
                {"text": "📋 Quiniela (₡300)", "callback_data": "buy:quiniela"},
                {"text": "⚽ Un Partido (₡200)", "callback_data": "buy:partido"},
            ],
            [
                {"text": "🎯 Parlay (₡250)", "callback_data": "buy:parlay"},
                {"text": "🥅 Goleadores (₡300)", "callback_data": "buy:goleadores"},
            ],
            [{"text": "━━ COMBOS ━━", "callback_data": "noop"}],
            [{"text": "🌍 Combo Mundial ₡800", "callback_data": "buy:combo_mundial"}],
            [{"text": "💰 Combo Apostador ₡650", "callback_data": "buy:combo_apostador"}],
            [{"text": "🏆 Combo Total ProGol ₡1,200", "callback_data": "buy:combo_total"}],
        ]
    }

def _approval_keyboard(buyer_chat_id, product_key):
    return {
        "inline_keyboard": [[
            {"text": "✅ Aprobar y enviar", "callback_data": f"approve:{buyer_chat_id}:{product_key}"},
            {"text": "❌ Rechazar", "callback_data": f"reject:{buyer_chat_id}:{product_key}"},
        ]]
    }

# ── Handlers ───────────────────────────────────────────────────────────────────
def _handle_message(token, owner_chat_id, msg):
    chat_id = str(msg["chat"]["id"])
    text = msg.get("text", "").strip()
    username = msg.get("from", {}).get("username", "")
    first_name = msg.get("from", {}).get("first_name", "Cliente")

    with _lock:
        state = _state.get(chat_id, {"step": "idle"})

    # Comandos
    if text in ("/start", "/menu", "/comprar", "/picks"):
        with _lock:
            _state[chat_id] = {"step": "menu", "username": username or first_name}
        _send(token, chat_id,
              f"🐕 *¡Hola {first_name}!* Bienvenido a *ProGol CR*\n\n"
              f"Usamos matemática real (Dixon-Coles + Elo) para generar picks del Mundial 2026.\n\n"
              f"Elegí un producto 👇",
              reply_markup=_main_menu_keyboard())
        return

    if text == "/estado":
        _send(token, chat_id, "📊 Tus compras de hoy: ninguna aún. Usá /comprar para ver el menú.")
        return

    # Esperando comprobante de pago
    if state.get("step") == "waiting_sinpe":
        product_key = state.get("product_key", "")
        prod = {**PRODUCTS, **COMBOS}.get(product_key, {})
        _send(token, chat_id,
              "✅ *Comprobante recibido.* Estamos verificando el pago.\n"
              "En menos de 5 minutos recibís la confirmación. 🐕")
        # Notificar al dueño
        buyer_name = f"@{username}" if username else first_name
        notif = (
            f"💰 *Nuevo pago recibido*\n"
            f"👤 {buyer_name} (chat: `{chat_id}`)\n"
            f"{prod.get('emoji','📦')} Producto: *{prod.get('name','?')}*\n"
            f"💵 Precio: *₡{prod.get('price',0):,}*\n\n"
            f"¿Aprobás el envío?"
        )
        _send(token, owner_chat_id, notif,
              reply_markup=_approval_keyboard(chat_id, product_key))
        with _lock:
            _state[chat_id] = {"step": "pending_approval", "product_key": product_key,
                                "username": username or first_name}
        return

    # Idle — mostrar menú
    if state.get("step") == "idle":
        _send(token, chat_id,
              "¡Hola! Usá /comprar para ver los productos de ProGol CR 🐕⚽")


def _handle_callback(token, owner_chat_id, cb):
    chat_id = str(cb["message"]["chat"]["id"])
    message_id = cb["message"]["message_id"]
    data = cb.get("data", "")
    cb_id = cb["id"]

    if data == "noop":
        _answer_callback(token, cb_id)
        return

    # ── Comprar producto ──────────────────────────────────────────────────────
    if data.startswith("buy:"):
        product_key = data.split(":", 1)[1]
        all_products = {**PRODUCTS, **COMBOS}
        prod = all_products.get(product_key)
        if not prod:
            _answer_callback(token, cb_id, "Producto no encontrado")
            return
        _answer_callback(token, cb_id)
        if prod["price"] == 0:
            # Entregar gratis inmediatamente
            content = CONTENT_MAP.get(product_key, lambda: "")()
            _send(token, chat_id, content)
            with _lock:
                _state[chat_id] = {"step": "idle"}
            return
        # Iniciar flujo de pago
        with _lock:
            _state[chat_id] = {"step": "waiting_sinpe", "product_key": product_key}
        msg = (
            f"{prod['emoji']} *{prod['name']}*\n"
            f"_{prod['desc']}_\n\n"
            f"💰 Precio: *₡{prod['price']:,}*\n\n"
            f"📱 *Realizá el SINPE:*\n"
            f"Número: *8561-0677*\n"
            f"Nombre: *Esteban V.*\n"
            f"Monto: *₡{prod['price']:,}*\n\n"
            f"Luego enviame el comprobante (foto o número de transacción) 👇"
        )
        _send(token, chat_id, msg)
        return

    # ── Aprobar pago (solo el dueño puede hacer esto) ─────────────────────────
    if data.startswith("approve:") and chat_id == str(owner_chat_id):
        _, buyer_chat_id, product_key = data.split(":", 2)
        _answer_callback(token, cb_id, "✅ Enviando picks...")
        all_products = {**PRODUCTS, **COMBOS}
        prod = all_products.get(product_key, {})
        # Generar y enviar el contenido al comprador
        content_fn = CONTENT_MAP.get(product_key, lambda: "Producto no disponible.")
        try:
            content = content_fn()
        except Exception as e:
            content = f"Error generando contenido: {e}"
        _send(token, buyer_chat_id, content)
        _send(token, buyer_chat_id,
              "🎉 *¡Gracias por confiar en ProGol CR!*\n"
              "Cualquier consulta escribinos. Ryder está aquí para ayudarte 🐕⚽")
        # Editar mensaje de aprobación
        _edit_message(token, chat_id, message_id,
                      f"✅ *Aprobado y enviado*\n"
                      f"Comprador: `{buyer_chat_id}`\n"
                      f"Producto: {prod.get('emoji','')} {prod.get('name','')}")
        with _lock:
            _state[buyer_chat_id] = {"step": "idle"}
        return

    # ── Rechazar pago ─────────────────────────────────────────────────────────
    if data.startswith("reject:") and chat_id == str(owner_chat_id):
        _, buyer_chat_id, product_key = data.split(":", 2)
        _answer_callback(token, cb_id, "❌ Pago rechazado")
        _send(token, buyer_chat_id,
              "❌ No pudimos verificar tu pago. "
              "Por favor contactanos directamente para resolverlo.")
        _edit_message(token, chat_id, message_id, "❌ *Rechazado*")
        with _lock:
            _state[buyer_chat_id] = {"step": "idle"}
        return

    _answer_callback(token, cb_id)


# ── Loop principal ─────────────────────────────────────────────────────────────
def run_bot(token, owner_chat_id, stop_event=None):
    offset = 0
    print(f"[bot] Iniciando polling (owner={owner_chat_id})")
    while not (stop_event and stop_event.is_set()):
        try:
            result = _api(token, "getUpdates", {"offset": offset, "timeout": 25})
            for update in result.get("result", []):
                offset = update["update_id"] + 1
                if "message" in update:
                    try:
                        _handle_message(token, owner_chat_id, update["message"])
                    except Exception as e:
                        print(f"[bot] message error: {e}")
                elif "callback_query" in update:
                    try:
                        _handle_callback(token, owner_chat_id, update["callback_query"])
                    except Exception as e:
                        print(f"[bot] callback error: {e}")
        except Exception as e:
            print(f"[bot] polling error: {e}")
            time.sleep(5)


def start_bot_thread(cfg):
    """Llamar desde server.py para iniciar el bot como hilo de fondo."""
    token = (cfg.get("telegram_bot_token") or "").strip()
    owner_chat_id = (cfg.get("telegram_chat_id") or "").strip()
    if not token or not owner_chat_id:
        print("[bot] Telegram no configurado — bot inactivo")
        return None
    stop = threading.Event()
    t = threading.Thread(target=run_bot, args=(token, owner_chat_id, stop), daemon=True)
    t.start()
    print(f"[bot] Bot de ventas activo — enviá /start al bot de Telegram")
    return stop


if __name__ == "__main__":
    cfg = {}
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"Error cargando config: {e}")
        sys.exit(1)
    token = cfg.get("telegram_bot_token", "").strip()
    owner = cfg.get("telegram_chat_id", "").strip()
    if not token or not owner:
        print("Configurá telegram_bot_token y telegram_chat_id en config.json")
        sys.exit(1)
    run_bot(token, owner)
