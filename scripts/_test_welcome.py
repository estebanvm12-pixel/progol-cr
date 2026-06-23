import json, sys, os, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import telegram_bot as b

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    cfg = json.load(f)
TOKEN = cfg["telegram_bot_token"]
CHAT  = cfg["telegram_chat_id"]

b._send(TOKEN, CHAT, "--- TEST: Bienvenida primera vez (/start) ---")

# Simular /start de un usuario nuevo
fake_start = {
    "chat": {"id": CHAT},
    "text": "/start",
    "from": {"first_name": "Esteban", "username": "DeadRyder"}
}
b._handle_message(TOKEN, CHAT, fake_start)
time.sleep(2)

# Simular click en boton (callback)
# Esto prueba que _handle_callback no lanza excepcion
b._send(TOKEN, CHAT, "--- TEST: Menu al volver a escribir ---")
fake_msg = {
    "chat": {"id": CHAT},
    "text": "hola de nuevo",
    "from": {"first_name": "Esteban", "username": "DeadRyder"}
}
b._handle_message(TOKEN, CHAT, fake_msg)
print("Listo")
