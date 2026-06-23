import json, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import telegram_bot as b

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    cfg = json.load(f)
TOKEN = cfg["telegram_bot_token"]
CHAT  = cfg["telegram_chat_id"]

print("Enviando imagen de partidos...")
b._send(TOKEN, CHAT, "--- TEST: Partidos del dia como imagen ---")
b._send_partidos_img(TOKEN, CHAT)
print("Listo")
