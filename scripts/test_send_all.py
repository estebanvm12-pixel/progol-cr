#!/usr/bin/env python3
"""
Envía todos los productos de prueba al chat de Esteban.
Uso: python scripts/test_send_all.py
"""
import sys, os, json, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import telegram_bot as b

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    cfg = json.load(f)

TOKEN = cfg["telegram_bot_token"]
CHAT  = cfg["telegram_chat_id"]

def send(text):
    b._send(TOKEN, CHAT, text)
    time.sleep(1.5)

print("Enviando todos los productos de prueba...")

# Separador de inicio
send("━━━━━━━━━━━━━━━━━━━━━━━\n🐕 *PRUEBA COMPLETA — ProGol CR*\nEnviando todos los productos para revisión.\n━━━━━━━━━━━━━━━━━━━━━━━")
time.sleep(1)

products_to_test = [
    ("🆓 PICK GRATIS",    b._get_free_pick),
    ("⚡ PRO DEL DÍA",    b._get_pro_picks),
    ("👑 PREMIUM",        b._get_premium_picks),
    ("📋 QUINIELA",       b._get_quiniela),
    ("🥅 GOLEADORES",     b._get_goleadores),
    ("📊 INFORME MUNDIAL",b._get_informe),
    ("🧠 RYDER PRO DEEP-DIVE", b._get_deepdive),
]

for label, fn in products_to_test:
    print(f"  -> {label}")
    try:
        content = fn()
        send(f"╔══ *{label}* ══╗\n\n{content}")
    except Exception as e:
        send(f"❌ Error en {label}: {e}")
    time.sleep(2)

# Combos
print("  → COMBOS")
send("━━━━━━━━━━━━━━━━━━━━━━━\n🎁 *COMBOS*\n━━━━━━━━━━━━━━━━━━━━━━━")
time.sleep(1)

combos = [
    ("🌍 Combo Mundial (₡800)",       "combo_mundial"),
    ("💰 Combo Apostador (₡650)",     "combo_apostador"),
    ("🏆 Combo Total ProGol (₡1200)", "combo_total"),
]
for label, key in combos:
    print(f"  -> {label}")
    try:
        fn = b.CONTENT_MAP[key]
        send(f"╔══ *{label}* ══╗\n\n{fn()}")
    except Exception as e:
        send(f"❌ Error en {label}: {e}")
    time.sleep(2)

# Winner announcement con foto
print("  → Winner announcement (foto)")
b.send_winner_announcement(TOKEN, CHAT,
    match="España vs Francia",
    pick="Gana España",
    result="2-1 ✅")
time.sleep(2)

# Menú de compra
print("  → Menú principal")
b._send(TOKEN, CHAT,
    "📲 *ASÍ SE VE EL MENÚ AL ESCRIBIR /comprar:*",
    reply_markup=b._main_menu())

send("━━━━━━━━━━━━━━━━━━━━━━━\n✅ *Prueba completa.* Revisá todo arriba y decime qué ajustar.\n━━━━━━━━━━━━━━━━━━━━━━━")

print("Listo!")
