import sys, os, json, urllib.request, urllib.parse
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

with open(os.path.join(os.path.dirname(__file__), "..", "config.json")) as f:
    cfg = json.load(f)

token   = cfg.get("telegram_bot_token", "").strip()
chat_id = cfg.get("telegram_chat_id", "").strip()
url     = cfg.get("current_tunnel_url", "N/A")

msg = (
    f"🐕 *Ryder ProGol CR está online*\n"
    f"🔗 {url}\n"
    f"⚽ Listo para analizar partidos\n"
    f"🕐 Prueba manual desde scripts/test_telegram_notify.py"
)

params = urllib.parse.urlencode({
    "chat_id":    chat_id,
    "text":       msg,
    "parse_mode": "Markdown",
})
req = urllib.request.Request(
    f"https://api.telegram.org/bot{token}/sendMessage?{params}",
    headers={"User-Agent": "ProGolCR/1.0"},
)
try:
    with urllib.request.urlopen(req, timeout=10) as r:
        body = r.read().decode("utf-8", errors="ignore")
        print("Respuesta:", body[:300])
except Exception as e:
    print("Error:", e)
