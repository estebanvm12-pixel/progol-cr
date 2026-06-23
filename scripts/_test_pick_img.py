import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import telegram_bot as b

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    cfg = json.load(f)
TOKEN = cfg["telegram_bot_token"]
CHAT  = cfg["telegram_chat_id"]

b._send(TOKEN, CHAT, "--- TEST: Pick gratis como imagen ---")
b._send_free_pick_img(TOKEN, CHAT)
print("Listo")
