import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import telegram_bot as b

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    cfg = json.load(f)
TOKEN = cfg["telegram_bot_token"]
CHAT  = cfg["telegram_chat_id"]

# Enviar GIF actualizado
b._send(TOKEN, CHAT, "--- GIF actualizado con logo ---")
b.send_winner_announcement(TOKEN, CHAT, "Alemania vs Curacao", "Gana Alemania", "3-0 FT")

# Simular mensaje de usuario nuevo (deberia mostrar menu)
import time; time.sleep(2)
b._send(TOKEN, CHAT, "--- Test: mensaje cualquiera ahora muestra menu ---")
# Simular el handler directamente
fake_msg = {"chat": {"id": CHAT}, "text": "hola", "from": {"first_name": "Esteban", "username": "DeadRyder"}}
b._handle_message(TOKEN, CHAT, fake_msg)
print("Listo")
