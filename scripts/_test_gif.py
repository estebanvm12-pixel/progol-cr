import json, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import telegram_bot as b, urllib.request

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    cfg = json.load(f)
TOKEN = cfg["telegram_bot_token"]
CHAT  = cfg["telegram_chat_id"]
GIF   = os.path.join(os.path.dirname(__file__), "..", "brand", "winner_announce.gif")

print(f"GIF size: {os.path.getsize(GIF)//1024} KB")

# Patch _send_animation to print full response
import urllib.error
try:
    url = f"https://api.telegram.org/bot{TOKEN}/sendAnimation"
    with open(GIF, "rb") as f:
        file_bytes = f.read()
    boundary = "----ProGolBoundary"
    body  = f"--{boundary}\r\nContent-Disposition: form-data; name=\"chat_id\"\r\n\r\n{CHAT}\r\n"
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"caption\"\r\n\r\nTest GIF ProGol CR\r\n"
    body += f"--{boundary}\r\nContent-Disposition: form-data; name=\"animation\"; filename=\"winner_announce.gif\"\r\nContent-Type: image/gif\r\n\r\n"
    body_bytes = body.encode("utf-8") + file_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")
    req = urllib.request.Request(url, data=body_bytes,
                                 headers={"Content-Type": f"multipart/form-data; boundary={boundary}",
                                          "User-Agent": "ProGolCR/1.0"})
    with urllib.request.urlopen(req, timeout=30) as r:
        print("HTTP", r.status)
        print(r.read().decode("utf-8")[:300])
except urllib.error.HTTPError as e:
    print("HTTP Error:", e.code, e.read().decode())
except Exception as e:
    print("Error:", e)
