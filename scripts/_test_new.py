import json, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import telegram_bot as b

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    cfg = json.load(f)
TOKEN = cfg["telegram_bot_token"]
CHAT  = cfg["telegram_chat_id"]

print("Import OK")

# Test partidos de hoy
partidos = b._get_partidos_hoy()
print(partidos[:300])
print()

# Enviar
b._send(TOKEN, CHAT, "--- TEST: Partidos de Hoy + Menu con nuevo boton ---")
b._send(TOKEN, CHAT, partidos)
time.sleep(1)

# Enviar menu con el nuevo boton de partidos
b._send(TOKEN, CHAT,
    "Nuevo menu con boton Partidos de Hoy:",
    reply_markup=b._main_menu())

print("Listo")
