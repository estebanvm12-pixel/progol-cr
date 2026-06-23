import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import telegram_bot as b

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    cfg = json.load(f)
TOKEN = cfg["telegram_bot_token"]
CHAT  = cfg["telegram_chat_id"]

# Test partidos filtrados
rows, today = b._today_matches(8)
print("Partidos del dia (sin terminados):")
for r in rows:
    print(f"  {r['home']} vs {r['away']}")

# Test pick gratis con conf correcta
pick = b._get_free_pick()
print()
print(pick[:400])
print()

# Enviar al Telegram
b._send(TOKEN, CHAT, "--- TEST conf + filtro ---")
b._send(TOKEN, CHAT, pick)

# Enviar GIF
print("Enviando GIF...")
ok = b.send_winner_announcement(TOKEN, CHAT, "Alemania vs Curacao", "Gana Alemania", "3-0 FT")
print("GIF ok:", ok)
