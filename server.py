
# ── Lucas Live: parser de estado en tiempo real ──────────────────────────────
def _parse_live_state(home, away, text):
    """
    Extrae estado del partido en curso desde texto libre.
    Retorna dict live_state o None si no parece partido en curso.
    """
    import re as _re
    t = text.lower()

    # Detectar si hay minuto mencionado
    min_match = _re.search(r"min(?:uto)?\s*(\d{1,3})[\s\'\'']", t) or \
                _re.search(r"(\d{1,3})[\s]*[\'\']", t) or \
                _re.search(r"minuto\s*(\d{1,3})", t)
    if not min_match:
        return None   # No parece partido en vivo

    minute = int(min_match.group(1))
    if minute < 1 or minute > 120:
        return None

    # Detectar marcador actual  "1-0" "2-1" "0-0"
    score_match = _re.search(r"\b(\d)-(\d)\b", t)
    score_h = int(score_match.group(1)) if score_match else 0
    score_a = int(score_match.group(2)) if score_match else 0

    # Detectar periodo
    period = "second_half" if minute > 45 else "first_half"
    if minute > 90:
        period = "extra_time"

    # Detectar hombres por expulsiones
    red_home_count = len(_re.findall(
        r"(?:roja|expulsad[oa]|red card)[^.]*?" + home[:4].lower(), t
    )) + len(_re.findall(
        home[:4].lower() + r"[^.]*?(?:roja|expulsad[oa]|red card)", t
    ))
    red_away_count = len(_re.findall(
        r"(?:roja|expulsad[oa]|red card)[^.]*?" + away[:4].lower(), t
    )) + len(_re.findall(
        away[:4].lower() + r"[^.]*?(?:roja|expulsad[oa]|red card)", t
    ))

    home_men = max(9, 11 - red_home_count)
    away_men = max(9, 11 - red_away_count)

    # Detectar jugadores mencionados cerca de "roja"/"expulsado"
    events = []
    # Patrones: "Messi roja", "roja a Messi", "Messi expulsado"
    player_red = _re.findall(
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(?:roja|expulsado|red card)|"
        r"(?:roja|expulsado|red card)\s+(?:a\s+)?([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
        text
    )
    for groups in player_red:
        player = groups[0] or groups[1]
        if not player:
            continue
        # Determinar equipo por contexto (simplificado: buscar nombre en texto cerca de equipo)
        p_lower = player.lower()
        # Lista de estrellas conocidas por equipo
        _KEY_PLAYERS = {
            "messi": "home", "di maria": "home", "lautaro": "home", "alvarez": "home",
            "ronaldo": "home", "neymar": "home", "vinicius": "home",
            "mbappe": "home", "griezmann": "home",
            "salah": "home", "kane": "home", "bellingham": "home",
        }
        team_guess = _KEY_PLAYERS.get(p_lower, "home")
        is_key = any(k in p_lower for k in [
            "messi", "ronaldo", "mbappe", "neymar", "vinicius", "salah",
            "kane", "bellingham", "pedri", "modric", "de bruyne"
        ])
        events.append({
            "type": "red_card",
            "team": team_guess,
            "player": player,
            "minute": minute,  # aproximado
            "is_key": is_key,
        })

    # Detectar lesiones
    player_inj = _re.findall(
        r"([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)\s+(?:lesionado|injury)|"
        r"(?:lesionado|injury)\s+(?:a\s+)?([A-Z][a-z]+(?:\s[A-Z][a-z]+)?)",
        text
    )
    for groups in player_inj:
        player = groups[0] or groups[1]
        if not player:
            continue
        is_key = any(k in player.lower() for k in [
            "messi", "ronaldo", "mbappe", "neymar", "vinicius", "salah",
            "kane", "bellingham", "pedri", "modric", "de bruyne"
        ])
        events.append({
            "type": "injury",
            "team": "home",
            "player": player,
            "minute": minute,
            "is_key": is_key,
        })

    return {
        "home": home,
        "away": away,
        "minute": minute,
        "period": period,
        "score_h": score_h,
        "score_a": score_a,
        "home_men": home_men,
        "away_men": away_men,
        "events": events,
    }
# ─────────────────────────────────────────────────────────────────────────────
#!/usr/bin/env python3
"""
ProGol CR — Inteligencia Deportiva
A tiny local web app: live World Cup fixtures for any day + an "Ask the Analyst"
chat panel powered by Claude (Anthropic API).

Runs on the Python standard library ONLY — no pip installs required.
Binds to localhost only. Your API key never leaves your machine.

Usage:
    python server.py
Then open http://127.0.0.1:8765  (it also opens automatically).
"""

import datetime
import json
import os
import re
import secrets
import shutil
import socket
import zipfile
import subprocess
import sys
import time
import threading
import webbrowser
import urllib.request
import urllib.parse
import urllib.error
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import db
import model
try:
    import doradobet
    _DORADOBET_AVAILABLE = True
except Exception as _dbe:
    print(f"[doradobet] module unavailable: {_dbe} — DoradoBet features disabled")
    _DORADOBET_AVAILABLE = False
    class _DoradoBetStub:
        def status(self): return {"logged_in": False, "username": "", "error": "module unavailable"}
        def login(self): return {"ok": False, "error": "module unavailable"}
    doradobet = _DoradoBetStub()
try:
    import calibrator as _calibrator
    _CALIBRATOR_AVAILABLE = True
except Exception:
    _CALIBRATOR_AVAILABLE = False

HERE = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(HERE, "config.json")

# Line-buffer stdout so diagnostics appear immediately when output is piped
try:
    sys.stdout.reconfigure(line_buffering=True)
except Exception:
    pass
HOST = "0.0.0.0"  # all interfaces — Tailscale handles external access securely
PORT = 8765
_TUNNEL_URL = None  # set when cloudflared/localtunnel is active

# FIFA World Cup league id on TheSportsDB
WC_LEAGUE_ID = "4429"
ANTHROPIC_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"
DEFAULT_MODEL = "claude-sonnet-4-6"

# ---- tiny in-memory cache so we don't hammer the free sports API ----
_cache = {}
_cache_lock = threading.Lock()
CACHE_TTL = 30  # seconds

# International competitions on TheSportsDB, queried by league id (complete data).
# The generic "s=Soccer" day feed is capped/sparse and omits friendlies, so we
# fan out across these specific leagues instead. Add ids here to widen coverage.
INTL_COMPETITIONS = [
    ("4429", "FIFA World Cup"),
    ("4562", "International Friendlies"),
    # Out of season during the World Cup, but harmless to query (return empty):
    # ("XXXX", "UEFA Nations League"),
    # ("XXXX", "CONCACAF Nations League"),
    # ("XXXX", "World Cup Qualifying"),
]
INTL_LEAGUE_IDS = {c[0] for c in INTL_COMPETITIONS}

# Important club leagues — same league-id fan-out mechanism. Note: many are
# off-season in June, and TheSportsDB may not have loaded a new season's
# fixtures yet, so a given day can legitimately be empty.
CLUB_COMPETITIONS = [
    ("4328", "English Premier League"),
    ("4335", "Spanish La Liga"),
    ("4332", "Italian Serie A"),
    ("4331", "German Bundesliga"),
    ("4334", "French Ligue 1"),
    ("4337", "Dutch Eredivisie"),
    ("4344", "Portuguese Primeira Liga"),
    ("4329", "English Championship"),
    ("4330", "Scottish Premiership"),
    ("4480", "UEFA Champions League"),
    ("4481", "UEFA Europa League"),
    ("4346", "Major League Soccer"),
    ("4350", "Liga MX"),
    ("4351", "Brazilian Serie A"),
    ("4406", "Argentine Primera Division"),
    ("4684", "USL Championship"),
]
CLUB_LEAGUE_IDS = {c[0] for c in CLUB_COMPETITIONS}

# Leagues that can plausibly kick off between 00:00 and ~08:00 UTC (i.e. evening
# games in the Americas / Asia). Only these need to be queried on the *next* UTC
# day when a viewer west of UTC asks for their local "today" — European leagues
# never start matches in that window, so skipping them halves the request load
# on the free SportsDB key.
LATE_UTC_LEAGUES = {
    WC_LEAGUE_ID,    # World Cup 2026 is hosted in the Americas — evening games
    "4562",          # International Friendlies
    "4346",          # MLS
    "4350",          # Liga MX
    "4351",          # Brazilian Serie A
    "4406",          # Argentine Primera
    "4684",          # USL Championship
}

# Used to decide if an event is country-vs-country. Lowercased.
NATIONAL_TEAMS = {t.lower() for t in [
    # UEFA
    "Albania","Andorra","Armenia","Austria","Azerbaijan","Belarus","Belgium",
    "Bosnia-Herzegovina","Bosnia and Herzegovina","Bulgaria","Croatia","Cyprus",
    "Czech Republic","Czechia","Denmark","England","Estonia","Faroe Islands","Finland",
    "France","Georgia","Germany","Gibraltar","Greece","Hungary","Iceland","Israel",
    "Italy","Kazakhstan","Kosovo","Latvia","Liechtenstein","Lithuania","Luxembourg",
    "Malta","Moldova","Monaco","Montenegro","Netherlands","North Macedonia","Northern Ireland",
    "Norway","Poland","Portugal","Republic of Ireland","Ireland","Romania","Russia","San Marino",
    "Scotland","Serbia","Slovakia","Slovenia","Spain","Sweden","Switzerland","Turkey","Türkiye",
    "Ukraine","Wales",
    # CONMEBOL
    "Argentina","Bolivia","Brazil","Chile","Colombia","Ecuador","Paraguay","Peru",
    "Uruguay","Venezuela",
    # CONCACAF
    "Antigua and Barbuda","Bahamas","Barbados","Belize","Bermuda","Canada","Costa Rica",
    "Cuba","Curacao","Curaçao","Dominican Republic","El Salvador","Grenada","Guatemala",
    "Guyana","Haiti","Honduras","Jamaica","Martinique","Mexico","Nicaragua","Panama",
    "Puerto Rico","Saint Kitts and Nevis","Saint Lucia","Suriname","Trinidad and Tobago",
    "United States","USA","USMNT",
    # CAF
    "Algeria","Angola","Benin","Botswana","Burkina Faso","Burundi","Cameroon","Cape Verde",
    "Central African Republic","Chad","Comoros","Congo","DR Congo","Congo DR","Ivory Coast",
    "Cote d'Ivoire","Côte d'Ivoire","Djibouti","Egypt","Equatorial Guinea","Eritrea","Eswatini",
    "Ethiopia","Gabon","Gambia","Ghana","Guinea","Guinea-Bissau","Kenya","Lesotho","Liberia",
    "Libya","Madagascar","Malawi","Mali","Mauritania","Mauritius","Morocco","Mozambique",
    "Namibia","Niger","Nigeria","Rwanda","Senegal","Sierra Leone","Somalia","South Africa",
    "South Sudan","Sudan","Tanzania","Togo","Tunisia","Uganda","Zambia","Zimbabwe",
    # AFC
    "Afghanistan","Australia","Bahrain","Bangladesh","Bhutan","Brunei","Cambodia","China",
    "China PR","Chinese Taipei","Taiwan","Hong Kong","India","Indonesia","Iran","Iraq","Japan",
    "Jordan","Kuwait","Kyrgyzstan","Laos","Lebanon","Macau","Malaysia","Maldives","Mongolia",
    "Myanmar","Nepal","North Korea","Korea DPR","Oman","Pakistan","Palestine","Philippines",
    "Qatar","Saudi Arabia","Singapore","South Korea","Korea Republic","Sri Lanka","Syria",
    "Tajikistan","Thailand","Timor-Leste","Turkmenistan","United Arab Emirates","UAE",
    "Uzbekistan","Vietnam","Yemen",
    # OFC
    "American Samoa","Cook Islands","Fiji","New Caledonia","New Zealand","Papua New Guinea",
    "Samoa","Solomon Islands","Tahiti","Tonga","Vanuatu",
]}

# Competition-name signals (fallback when a team name isn't recognized)
INTL_NAME_RE = re.compile(
    r"world cup|nations league|copa am|africa cup of nations|afcon|asian cup|gold cup|"
    r"confederations cup|finalissima|european championship|uefa euro|friendl|qualif|olympic",
    re.I,
)
CLUB_NAME_RE = re.compile(
    r"club world cup|champions league|europa|conference league|premier|primeira|"
    r"bundesliga|serie [abc]|la liga|ligue|eredivisie|\busl\b|\bmls\b|league one|league two",
    re.I,
)


def _is_national(name):
    return (name or "").strip().lower() in NATIONAL_TEAMS


def _is_international_event(ev):
    home, away = ev.get("strHomeTeam"), ev.get("strAwayTeam")
    if _is_national(home) and _is_national(away):
        return True
    league = ev.get("strLeague") or ""
    if str(ev.get("idLeague") or "") in INTL_LEAGUE_IDS:
        return True
    if INTL_NAME_RE.search(league) and not CLUB_NAME_RE.search(league):
        return True
    return False


def load_config():
    defaults = {
        "anthropic_api_key": "",
        "anthropic_model": DEFAULT_MODEL,
        "sportsdb_key": "3",  # free public test key, no signup needed
        "remote_token": "",   # access token required for tunnel connections
        "apifootball_key": "",  # API-Football (RapidAPI) key for live player stats
        "email_address": "",    # sender email (Outlook/Hotmail recommended)
        "email_password": "",   # app password for SMTP
        "email_recipient": "Esteban_vm12@hotmail.com",  # default recipient
        "telegram_bot_token": "",  # from @BotFather — e.g. "7123456789:AAHxxxxxx"
        "telegram_chat_id": "",   # your personal chat ID — from getUpdates
    }
    if os.path.exists(CONFIG_PATH):
        try:
            with open(CONFIG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            defaults.update({k: v for k, v in data.items() if v is not None})
        except Exception as e:
            print(f"[config] could not read config.json: {e}")
    return defaults


def save_config(new_values):
    cfg = load_config()
    for k in ("anthropic_api_key", "anthropic_model", "sportsdb_key", "remote_token",
              "apifootball_key", "email_address", "email_password", "email_recipient",
              "telegram_bot_token", "telegram_chat_id"):
        if k in new_values and new_values[k] is not None:
            cfg[k] = new_values[k]
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)
    return cfg


# ---------------- Remote access auth ----------------

_REMOTE_TOKEN_COOKIE = "wr_access"

# Suppress the subprocess window on Windows
_POPEN_KW = {"creationflags": 0x08000000} if sys.platform == "win32" else {}

# Login page served to unauthenticated remote clients
LOGIN_PAGE_HTML = b"""<!doctype html><html><head><meta http-equiv="refresh" content="0;url=/login"/></head><body></body></html>"""


# ── User Auth ─────────────────────────────────────────────────────────────────
import hashlib
import hmac as _hmac

USERS_PATH = os.path.join(HERE, "data", "users.json")
_sessions = {}   # token -> {username, role, created_at}
_SESSION_TTL = 86400 * 7  # 7 days

# ── Brute-force protection ────────────────────────────────────────────────────
_login_fails  = {}   # ip -> [timestamp, ...]
_LOGIN_MAX    = 5    # max failed attempts
_LOGIN_WINDOW = 900  # 15-minute lockout window

def _login_check(ip: str) -> bool:
    """Return True if IP is allowed to attempt login, False if locked out."""
    now = time.time()
    attempts = [t for t in _login_fails.get(ip, []) if now - t < _LOGIN_WINDOW]
    _login_fails[ip] = attempts
    return len(attempts) < _LOGIN_MAX

def _login_record_fail(ip: str):
    _login_fails.setdefault(ip, []).append(time.time())

def _login_clear(ip: str):
    _login_fails.pop(ip, None)

ROLE_PERMS = {
    "maestro":      {"settings": True,  "maestro_btn": True,  "all_picks": True,  "scout_report": True,  "day_combos": True,  "admin": True},
    "mega_premium": {"settings": False, "maestro_btn": True,  "all_picks": True,  "scout_report": True,  "day_combos": True,  "admin": False},
    "premium":      {"settings": False, "maestro_btn": False, "all_picks": False, "scout_report": False, "day_combos": False, "admin": False},
}

def _hash_pw(password: str, salt: str = "") -> str:
    if not salt:
        salt = secrets.token_hex(16)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt.encode(), 100_000)
    return f"{salt}${dk.hex()}"

def _verify_pw(password: str, stored: str) -> bool:
    try:
        salt, _ = stored.split("$", 1)
        return _hmac.compare_digest(stored, _hash_pw(password, salt))
    except Exception:
        return False

def _load_users():
    if os.path.exists(USERS_PATH):
        try:
            with open(USERS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def _save_users(users):
    os.makedirs(os.path.dirname(USERS_PATH), exist_ok=True)
    with open(USERS_PATH, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def _init_users():
    users = _load_users()
    defaults = [
        ("DeadRyder",    "Samuel2024!",    "maestro"),
        ("ProGolPremium","Premium2024!",   "premium"),
        ("ProGolMega",   "MegaGol2024!",   "mega_premium"),
    ]
    changed = False
    for username, password, role in defaults:
        if username not in users:
            users[username] = {"password": _hash_pw(password), "role": role, "active": True}
            changed = True
    if changed:
        _save_users(users)
    return users

def _get_session(token: str):
    if not token:
        return None
    s = _sessions.get(token)
    if not s:
        return None
    if time.time() - s["created_at"] > _SESSION_TTL:
        _sessions.pop(token, None)
        return None
    return s

def _purge_expired_sessions():
    """Remove expired sessions — called periodically to prevent memory growth."""
    now = time.time()
    expired = [t for t, s in _sessions.items() if now - s["created_at"] > _SESSION_TTL]
    for t in expired:
        _sessions.pop(t, None)
    # Hard cap: if still over 500 sessions, evict oldest
    if len(_sessions) > 500:
        oldest = sorted(_sessions.items(), key=lambda x: x[1]["created_at"])
        for token, _ in oldest[:len(_sessions) - 500]:
            _sessions.pop(token, None)

def _create_session(username: str, role: str) -> str:
    _purge_expired_sessions()
    token = secrets.token_urlsafe(32)
    _sessions[token] = {"username": username, "role": role, "created_at": time.time()}
    return token

def _cookie_session(handler) -> str:
    """Extract session token from Cookie header."""
    raw = handler.headers.get("Cookie", "")
    for part in raw.split(";"):
        part = part.strip()
        if part.startswith("pgcr_session="):
            return part[len("pgcr_session="):]
    return ""

AUTH_LOGIN_HTML = """<!doctype html>
<html lang="es"><head>
<meta charset="UTF-8"/><meta name="viewport" content="width=device-width,initial-scale=1"/>
<title>ProGol CR — Login</title>
<link href="https://fonts.googleapis.com/css2?family=Sora:wght@600;700;800&family=Inter:wght@400;500;600&display=swap" rel="stylesheet"/>
<style>
*{box-sizing:border-box;margin:0;padding:0}
body{background:#070b14;color:#eaf1f9;font-family:'Inter',sans-serif;min-height:100vh;
     display:flex;align-items:center;justify-content:center;padding:20px}
.card{background:rgba(15,23,42,.95);border:1px solid rgba(245,200,66,.25);border-radius:20px;
      padding:40px 32px;width:min(400px,95vw);text-align:center;
      box-shadow:0 8px 40px rgba(0,0,0,.6)}
.logo-wrap{display:flex;align-items:center;justify-content:center;gap:10px;margin-bottom:6px}
.pg-logo{width:38px;height:44px}
.brand-name{font-family:'Sora',sans-serif;font-size:22px;font-weight:800;
            background:linear-gradient(135deg,#f5c842,#22c55e);-webkit-background-clip:text;
            -webkit-text-fill-color:transparent}
.mascot{width:80px;height:80px;border-radius:50%;object-fit:cover;object-position:center 8%;
        border:3px solid rgba(245,200,66,.4);margin:16px auto;display:block;
        box-shadow:0 0 20px rgba(245,200,66,.2)}
h2{font-family:'Sora',sans-serif;font-size:17px;font-weight:700;margin-bottom:4px;color:#f1f5f9}
.sub{font-size:12px;color:#64748b;margin-bottom:24px}
input{width:100%;padding:12px 16px;border-radius:10px;border:1px solid rgba(120,144,180,.25);
      background:rgba(30,41,59,.8);color:#eaf1f9;font-size:15px;margin-bottom:12px;
      outline:none;font-family:'Inter',sans-serif}
input:focus{border-color:#22c55e;box-shadow:0 0 0 3px rgba(34,197,94,.15)}
button{width:100%;padding:13px;border-radius:10px;margin-top:4px;
       background:linear-gradient(135deg,#f5c842,#f59e0b);
       color:#0f172a;font-weight:700;border:none;cursor:pointer;font-size:15px;
       font-family:'Inter',sans-serif;transition:opacity .15s}
button:hover{opacity:.9}
.err{color:#f87171;font-size:13px;margin-top:12px;padding:10px;
     background:rgba(239,68,68,.1);border-radius:8px;display:none}
.err.show{display:block}
.footer{font-size:11px;color:#334155;margin-top:20px}
</style>
</head><body>
<div class="card">
  <div class="logo-wrap">
    <svg class="pg-logo" viewBox="0 0 100 115" fill="none" xmlns="http://www.w3.org/2000/svg">
      <polygon points="50,3 97,27.5 97,87.5 50,112 3,87.5 3,27.5" fill="#0f172a" stroke="#f5c842" stroke-width="5"/>
      <polygon points="50,16 84,34.5 84,80.5 50,99 16,80.5 16,34.5" fill="none" stroke="#22c55e" stroke-width="2"/>
      <text x="50" y="64" text-anchor="middle" fill="#f5c842" font-size="30" font-weight="900" font-family="system-ui">PG</text>
      <text x="50" y="80" text-anchor="middle" fill="#22c55e" font-size="11" font-family="system-ui" letter-spacing="4" font-weight="700">CR</text>
    </svg>
    <span class="brand-name">ProGol CR</span>
  </div>
  <img src="/brand/mascota.jpg" class="mascot" alt="Ryder"/>
  <h2>Bienvenido a ProGol CR</h2>
  <p class="sub">Inteligencia deportiva · picks con IA</p>
  <form id="loginForm">
    <input type="text" id="uname" placeholder="Usuario" autocomplete="username" autofocus/>
    <input type="password" id="upass" placeholder="Contraseña" autocomplete="current-password"/>
    <button type="submit">Entrar</button>
    <div class="err" id="loginErr">Usuario o contraseña incorrectos</div>
  </form>
  <p class="footer">© 2026 ProGol CR · Todos los derechos reservados</p>
</div>
<script>
document.getElementById('loginForm').onsubmit = async function(e) {
  e.preventDefault();
  const btn = this.querySelector('button');
  btn.textContent = 'Verificando…'; btn.disabled = true;
  const err = document.getElementById('loginErr');
  err.classList.remove('show');
  try {
    const r = await fetch('/api/login', {
      method: 'POST',
      headers: {'Content-Type':'application/json'},
      body: JSON.stringify({
        username: document.getElementById('uname').value.trim(),
        password: document.getElementById('upass').value
      })
    });
    if (r.ok) {
      window.location.href = '/';
    } else {
      err.classList.add('show');
      btn.textContent = 'Entrar'; btn.disabled = false;
    }
  } catch(ex) {
    err.textContent = 'Error de conexión — intenta de nuevo';
    err.classList.add('show');
    btn.textContent = 'Entrar'; btn.disabled = false;
  }
};
</script>
</body></html>"""


def _is_local_request(handler):
    """True if the request comes from localhost or LAN (not via an external tunnel)."""
    ip = handler.client_address[0]
    if ip in ("127.0.0.1", "::1"):
        # Could be localhost browser OR a tunnel proxy (ngrok/cloudflared connects locally).
        # Distinguish by Host header: tunnel requests carry the external host name.
        host = (handler.headers.get("Host") or "").split(":")[0].lower()
        return host in ("127.0.0.1", "localhost", "")
    # LAN ranges
    if ip.startswith(("10.", "192.168.")):
        return True
    if ip.startswith("172."):
        parts = ip.split(".")
        if len(parts) >= 2 and 16 <= int(parts[1]) <= 31:
            return True
    return False


def _parse_cookies(header):
    out = {}
    for part in (header or "").split(";"):
        k, _, v = part.strip().partition("=")
        if k:
            out[k.strip()] = v.strip()
    return out


# ---------------- ESPN public API (no key required) ----------------

ESPN_WC_URL = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"

def _espn_status(comp):
    """Map ESPN competition status to our internal status string."""
    try:
        st = comp["status"]
        typ = st.get("type", {})
        sid = typ.get("id", "")
        state = typ.get("state", "")
        completed = typ.get("completed", False)
        # Live
        if sid == "2" or state == "in":
            return "Live"
        # Finished: id 3/4 (old), 28 (STATUS_FULL_TIME WC2026), state=post, or completed flag
        if sid in ("3", "4", "28") or state == "post" or completed:
            return "Finished"
        # Scheduled
        if sid == "1" or state == "pre":
            return "Scheduled"
    except Exception:
        pass
    return "Scheduled"

ESPN_STANDINGS_URL = "https://site.api.espn.com/apis/v2/sports/soccer/fifa.world/standings"

def _fetch_wc_standings():
    """Fetch all WC 2026 group standings from ESPN. Returns list of group dicts."""
    req = urllib.request.Request(ESPN_STANDINGS_URL, headers={"User-Agent": "WC2026-WarRoom/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    groups = []
    for grp in (data.get("children") or []):
        name = grp.get("name", "")
        entries = (grp.get("standings") or {}).get("entries") or []
        teams = []
        for e in entries:
            stat_map = {s["name"]: s["displayValue"] for s in (e.get("stats") or [])}
            team = e.get("team") or {}
            teams.append({
                "id": team.get("id", ""),
                "name": team.get("displayName", ""),
                "shortName": team.get("abbreviation", ""),
                "logo": team.get("logos", [{}])[0].get("href", "") if team.get("logos") else "",
                "gp": stat_map.get("gamesPlayed", "0"),
                "w": stat_map.get("wins", "0"),
                "d": stat_map.get("ties", "0"),
                "l": stat_map.get("losses", "0"),
                "gf": stat_map.get("pointsFor", "0"),
                "ga": stat_map.get("pointsAgainst", "0"),
                "gd": stat_map.get("pointDifferential", "0"),
                "pts": stat_map.get("points", "0"),
            })
        groups.append({"name": name, "teams": teams})
    return groups


# Cache for group fixtures (full schedule)
_fixtures_cache = {"ts": 0, "data": None}
_fixtures_lock = threading.Lock()

def _fetch_group_fixtures():
    """Fetch all WC 2026 group-stage fixtures from ESPN using standings-based team→group mapping.
    Returns dict: { "Group A": [ {home, away, homeLogo, awayLogo, scoreHome, scoreAway, status, kickoff}, ... ] }
    Cached for 5 minutes.
    """
    with _fixtures_lock:
        now = time.time()
        if _fixtures_cache["data"] and now - _fixtures_cache["ts"] < 300:
            return _fixtures_cache["data"]

    # Build team-name → group map from standings (which we already have)
    team_to_group = {}
    try:
        standings = _fetch_wc_standings()
        for grp in standings:
            for t in grp.get("teams", []):
                name = t.get("name", "")
                if name:
                    team_to_group[name.lower()] = grp["name"]
    except Exception:
        pass

    # Fetch group-stage scoreboard using ESPN's date-range param (one request covers all)
    # Also fetch 3 individual days around today as fallback since range support varies
    all_events = {}
    fetch_dates = ["20260611-20260627"]  # range first
    # add individual days for today ± 3 as backup
    today = datetime.date.today()
    for delta in range(-1, 5):
        d = today + datetime.timedelta(days=delta)
        if datetime.date(2026, 6, 11) <= d <= datetime.date(2026, 6, 27):
            fetch_dates.append(d.strftime("%Y%m%d"))

    for date_param in fetch_dates:
        url = f"{ESPN_WC_URL}?dates={date_param}&limit=100"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "WC2026-WarRoom/1.0"})
            with urllib.request.urlopen(req, timeout=12) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for ev in (data.get("events") or []):
                eid = ev.get("id")
                if eid and eid not in all_events:
                    all_events[eid] = ev
        except Exception:
            pass

    by_group = {}
    for ev in all_events.values():
        comp = (ev.get("competitions") or [{}])[0]
        competitors = comp.get("competitors") or []
        if len(competitors) < 2:
            continue
        hc = next((c for c in competitors if c.get("homeAway") == "home"), competitors[0])
        ac = next((c for c in competitors if c.get("homeAway") == "away"), competitors[1])
        home_name = (hc.get("team") or {}).get("displayName", "")
        away_name = (ac.get("team") or {}).get("displayName", "")
        if not home_name or not away_name:
            continue

        # Map to group via standings lookup
        group_name = (team_to_group.get(home_name.lower())
                      or team_to_group.get(away_name.lower())
                      or "")
        # Also try notes field (sometimes populated)
        if not group_name:
            for note in (comp.get("notes") or []):
                txt = note.get("headline", "")
                if txt.startswith("Group "):
                    group_name = txt.strip()
                    break
        if not group_name:
            continue  # not a group-stage match

        status = _espn_status(comp)
        score_h = str(hc.get("score", "")) if status != "Scheduled" else ""
        score_a = str(ac.get("score", "")) if status != "Scheduled" else ""

        # Logo: ESPN puts them under team.logos[] or team.logo (string)
        def _logo(c):
            t = c.get("team") or {}
            logos = t.get("logos") or []
            if logos:
                return logos[0].get("href", "")
            return t.get("logo", "")

        fixture = {
            "home": home_name,
            "away": away_name,
            "homeLogo": _logo(hc),
            "awayLogo": _logo(ac),
            "scoreHome": score_h,
            "scoreAway": score_a,
            "status": status,
            "kickoff": comp.get("date", ""),
            "group": group_name,
        }
        # Deduplicate by home+away
        key = f"{home_name}|{away_name}"
        existing = by_group.get(group_name, [])
        if not any(f["home"] == home_name and f["away"] == away_name for f in existing):
            by_group.setdefault(group_name, []).append(fixture)

    # Sort each group's fixtures by kickoff
    for grp in by_group:
        by_group[grp].sort(key=lambda f: f["kickoff"])

    with _fixtures_lock:
        _fixtures_cache["ts"] = time.time()
        _fixtures_cache["data"] = by_group
    return by_group


def _fetch_espn_wc(date_str, tz_min=None):
    """Fetch WC matches from ESPN for a LOCAL YYYY-MM-DD date.

    ESPN organises matches by UTC date. A late-evening kickoff in the Americas
    (e.g. 22:00 CST = 04:00 UTC next day) lives on the NEXT UTC date on ESPN,
    so we always fetch two consecutive UTC days and keep whichever events fall
    on the requested LOCAL date after applying the timezone offset.

    Returns a list of normalised match dicts (same shape as _normalize_event).
    Silently returns [] on any failure.
    """
    if tz_min is None:
        tz_min = _server_tz_minutes()

    # The two UTC dates that can overlap this local day
    utc_dates = _utc_days_for_local_date(date_str, tz_min)
    # Always include the day after the last UTC date to catch very late kickoffs
    last = datetime.datetime.strptime(utc_dates[-1], "%Y-%m-%d")
    extra = (last + datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    fetch_dates = list(utc_dates) + [extra]

    raw_events = []
    seen_ids = set()
    for utc_day in fetch_dates:
        compact = utc_day.replace("-", "")
        url = f"{ESPN_WC_URL}?dates={compact}&limit=50"
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "WC2026-WarRoom/1.0"})
            with urllib.request.urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            for ev in (data.get("events") or []):
                eid = ev.get("id")
                if eid and eid not in seen_ids:
                    seen_ids.add(eid)
                    raw_events.append(ev)
        except Exception:
            pass  # silently skip failed days

    results = []
    for event in raw_events:
        try:
            comps = event.get("competitions") or []
            if not comps:
                continue
            comp = comps[0]
            competitors = comp.get("competitors") or []
            home = next((c for c in competitors if c.get("homeAway") == "home"), None)
            away = next((c for c in competitors if c.get("homeAway") == "away"), None)
            if not home or not away:
                continue

            # Scores
            def _score(c):
                s = c.get("score")
                if s is None or s == "":
                    return None
                try:
                    return int(s)
                except Exception:
                    return None

            status = _espn_status(comp)

            # kickoff: ESPN gives ISO8601 UTC
            kickoff_utc = event.get("date") or ""  # e.g. "2026-06-12T18:00Z"
            # derive UTC date and time from it
            date_event = kickoff_utc[:10] if kickoff_utc else date_str
            time_utc = kickoff_utc[11:16] if len(kickoff_utc) >= 16 else ""

            venue_info = comp.get("venue") or {}
            venue = venue_info.get("fullName") or ""

            # Round / group from notes
            round_str = ""
            for note in (comp.get("notes") or []):
                h = note.get("headline") or ""
                if h:
                    round_str = h
                    break

            home_team = home.get("team") or {}
            away_team = away.get("team") or {}

            results.append({
                "id": f"espn-{event.get('id', '')}",
                "home": home_team.get("displayName") or home_team.get("name") or "",
                "away": away_team.get("displayName") or away_team.get("name") or "",
                "homeScore": _score(home) if status != "Scheduled" else None,
                "awayScore": _score(away) if status != "Scheduled" else None,
                "status": status,
                "rawStatus": status,
                "progress": "",
                "kickoffUtc": kickoff_utc,
                "dateEvent": date_event,
                "timeUtc": time_utc,
                "venue": venue,
                "round": round_str,
                "league": "FIFA World Cup",
                "idLeague": WC_LEAGUE_ID,
                "homeBadge": home_team.get("logo") or "",
                "awayBadge": away_team.get("logo") or "",
                "is_wc": True,
                "is_intl": True,
                "is_club": False,
            })
        except Exception:
            continue
    return results


# ---------------- Sports data ----------------

def _normalize_status(raw):
    if not raw:
        return "Scheduled"
    r = str(raw).upper()
    if r in ("NS", "NOT STARTED", "TBD", "SCHEDULED", ""):
        return "Scheduled"
    if r in ("FT", "AET", "PEN", "MATCH FINISHED", "FINISHED", "AWARDED"):
        return "Finished"
    if r in ("PPD", "POSTP", "POSTPONED"):
        return "Postponed"
    if r in ("CANC", "CANCELLED", "ABD", "ABANDONED"):
        return "Cancelled"
    # 1H, 2H, HT, ET, P, LIVE, etc.
    return "Live"


def _normalize_event(ev):
    hs = ev.get("intHomeScore")
    as_ = ev.get("intAwayScore")
    idl = str(ev.get("idLeague") or "")
    return {
        "id": ev.get("idEvent"),
        "home": ev.get("strHomeTeam") or "",
        "away": ev.get("strAwayTeam") or "",
        "homeScore": int(hs) if hs not in (None, "") else None,
        "awayScore": int(as_) if as_ not in (None, "") else None,
        "status": _normalize_status(ev.get("strStatus") or ev.get("strProgress")),
        "rawStatus": ev.get("strStatus") or "",
        "progress": ev.get("strProgress") or "",
        "kickoffUtc": ev.get("strTimestamp") or "",
        "dateEvent": ev.get("dateEvent") or "",
        "timeUtc": ev.get("strTime") or "",
        "venue": ev.get("strVenue") or "",
        "round": ev.get("intRound") or "",
        "league": ev.get("strLeague") or "International",
        "idLeague": idl,
        "homeBadge": ev.get("strHomeTeamBadge") or "",
        "awayBadge": ev.get("strAwayTeamBadge") or "",
        "is_wc": idl == WC_LEAGUE_ID,
        "is_intl": _is_international_event(ev),
        "is_club": idl in CLUB_LEAGUE_IDS,
    }


def _fetch_league_day(base, date_str, league_id, retries=1):
    """Return the events list for one league on one day.

    Returns [] (not an error) when the league simply has no games that day.
    Retries once on failure to ride out the free key's transient rate limits;
    raises only if every attempt fails.
    """
    url = f"{base}/eventsday.php?d={urllib.parse.quote(date_str)}&l={league_id}"
    last_err = None
    for attempt in range(retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "WC2026-WarRoom/1.0"})
            with urllib.request.urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read().decode("utf-8"))
            return data.get("events") or []
        except Exception as e:
            last_err = e
            if attempt < retries:
                time.sleep(0.5)
    raise last_err


def _server_tz_minutes():
    """This PC's UTC offset in minutes (e.g. CST -> -360)."""
    off = datetime.datetime.now().astimezone().utcoffset()
    return int(off.total_seconds() // 60) if off else 0


def _utc_days_for_local_date(date_str, tz_min):
    """The UTC calendar dates (1 or 2) that overlap the given LOCAL day.

    SportsDB's eventsday.php is keyed by UTC date, so a late-evening kickoff
    in the Americas lives on the *next* UTC day. We must query both.
    """
    day = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    start_utc = day - datetime.timedelta(minutes=tz_min)   # local 00:00 in UTC
    end_utc = start_utc + datetime.timedelta(hours=24)     # local 24:00 in UTC
    days = {start_utc.strftime("%Y-%m-%d"),
            (end_utc - datetime.timedelta(seconds=1)).strftime("%Y-%m-%d")}
    return sorted(days)


def _event_local_date(m, tz_min):
    """Local calendar date (YYYY-MM-DD) of a normalized match's kickoff."""
    ts = (m.get("kickoffUtc") or "").replace(" ", "T").rstrip("Z")
    if ts:
        try:
            dt = datetime.datetime.fromisoformat(ts)
            return (dt + datetime.timedelta(minutes=tz_min)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    d, t = m.get("dateEvent") or "", m.get("timeUtc") or ""
    if d and t:
        try:
            dt = datetime.datetime.fromisoformat(f"{d}T{t}")
            return (dt + datetime.timedelta(minutes=tz_min)).strftime("%Y-%m-%d")
        except ValueError:
            pass
    return d or None


def fetch_matches(date_str, sportsdb_key, scope="worldcup", tz_min=None):
    """Return (matches, served_from_cache) for a given LOCAL YYYY-MM-DD and scope.

    scope = 'worldcup'      -> FIFA World Cup only (league 4429)
    scope = 'international'  -> every international competition we track, merged

    tz_min is the viewer's UTC offset in minutes (CST = -360). SportsDB days
    are UTC, so we fetch every UTC day overlapping the local day and keep the
    events whose kickoff falls on the local date.

    Both scopes fan out over league ids SEQUENTIALLY (gentle on the free key).
    If a league request fails, we backfill that league from the SQLite cache so
    known fixtures never silently disappear.
    """
    if tz_min is None:
        tz_min = _server_tz_minutes()
    cache_key = f"{scope}:{date_str}:{tz_min}:{sportsdb_key}"
    ttl = 120 if scope == "clubs" else CACHE_TTL
    now = time.time()
    with _cache_lock:
        hit = _cache.get(cache_key)
        if hit and now - hit[0] < ttl:
            return hit[1], False

    # ── World Cup scope: ESPN is authoritative (complete schedule + live scores,
    #    no API key required). Skip TheSportsDB for WC to avoid duplicates.
    if scope == "worldcup":
        espn_matches = _fetch_espn_wc(date_str, tz_min)
        # Filter to only events whose LOCAL kickoff is on the requested date
        espn_matches = [m for m in espn_matches if _event_local_date(m, tz_min) == date_str]
        espn_matches.sort(key=lambda m: m.get("kickoffUtc") or "")
        with _cache_lock:
            _cache[cache_key] = (now, espn_matches)
        return espn_matches, False

    base = f"https://www.thesportsdb.com/api/v1/json/{urllib.parse.quote(sportsdb_key)}"
    if scope == "international":
        league_ids = [c[0] for c in INTL_COMPETITIONS]
    elif scope == "clubs":
        league_ids = [c[0] for c in CLUB_COMPETITIONS]
    else:
        league_ids = [WC_LEAGUE_ID]

    utc_days = _utc_days_for_local_date(date_str, tz_min)
    fresh, seen, failures, requests_made = [], set(), 0, 0
    for utc_day in utc_days:
        day_ids = league_ids
        if utc_day > date_str:
            day_ids = [l for l in league_ids if l in LATE_UTC_LEAGUES]
        for lid in day_ids:
            requests_made += 1
            try:
                for ev in _fetch_league_day(base, utc_day, lid):
                    eid = ev.get("idEvent")
                    if eid and eid not in seen:
                        seen.add(eid)
                        fresh.append(ev)
            except Exception as e:
                failures += 1
                print(f"[api] league {lid} ({utc_day}) failed: {e}")

    all_fetched = [_normalize_event(ev) for ev in fresh]

    # For international scope, supplement with ESPN WC matches
    if scope == "international":
        espn_matches = _fetch_espn_wc(date_str)
        # Use model._norm() for alias-aware dedup (handles Spanish↔English names)
        existing_sigs = {(model._norm(m["home"]), model._norm(m["away"])) for m in all_fetched}
        for em in espn_matches:
            sig = (model._norm(em["home"]), model._norm(em["away"]))
            rev = (sig[1], sig[0])  # also check reversed home/away
            if sig not in existing_sigs and rev not in existing_sigs:
                all_fetched.append(em)
                existing_sigs.add(sig)

    if all_fetched:
        # store everything we learned (keeps the form DB rich), then filter
        try:
            db.upsert_matches(all_fetched)
        except Exception as e:
            print(f"[db] upsert failed: {e}")

    # Keep only matches whose LOCAL kickoff date is the requested day
    matches = [m for m in all_fetched if _event_local_date(m, tz_min) == date_str]

    # Final cross-language dedup: remove matches that are the same fixture
    # but appear with different names (e.g. "Alemania" vs "Germany")
    if scope == "international":
        seen_norm = set()
        deduped = []
        for m in matches:
            sig = tuple(sorted([model._norm(m["home"]), model._norm(m["away"])]))
            if sig not in seen_norm:
                seen_norm.add(sig)
                deduped.append(m)
        matches = deduped

    served_cached = False
    if failures:
        # a request failed: backfill anything we couldn't fetch from the cache.
        # DB rows are keyed by UTC date, so pull every overlapping UTC day and
        # keep only games whose LOCAL kickoff is on the requested day.
        cached = []
        for utc_day in utc_days:
            try:
                cached.extend(db.get_cached_matches(utc_day, scope))
            except Exception as e:
                print(f"[db] cache read failed for {utc_day}: {e}")
        have = {m["id"] for m in matches}
        added = [cm for cm in cached
                 if cm["id"] not in have
                 and _event_local_date(cm, tz_min) == date_str]
        if added:
            matches.extend(added)
            served_cached = True
        if failures == requests_made and not matches:
            raise RuntimeError("sports API error: request(s) failed and nothing cached")

    matches.sort(key=lambda m: m.get("kickoffUtc") or "")
    with _cache_lock:
        _cache[cache_key] = (now, matches)
    return matches, served_cached


# ---------------- API-Football live player stats ----------------

_APIF_BASE = "https://v3.football.api-sports.io"
_APIF_RAPID_BASE = "https://api-football-v1.p.rapidapi.com/v3"

def _apif_request(endpoint, params, api_key, use_rapidapi=False):
    """Call API-Football. Returns parsed JSON or raises."""
    base = _APIF_RAPID_BASE if use_rapidapi else _APIF_BASE
    url = f"{base}/{endpoint}?{urllib.parse.urlencode(params)}"
    headers = {"x-rapidapi-key": api_key, "x-rapidapi-host": "api-football-v1.p.rapidapi.com"} \
        if use_rapidapi else {"x-apisports-key": api_key}
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def fetch_live_player_stats(fixture_id, api_key):
    """Return per-team player stats for a live/finished fixture. Uses API-Football free tier."""
    try:
        data = _apif_request("fixtures/players", {"fixture": fixture_id}, api_key)
        teams = data.get("response", [])
        result = []
        for team_data in teams:
            team_name = team_data.get("team", {}).get("name", "")
            for p in team_data.get("players", []):
                pl = p.get("player", {})
                st = (p.get("statistics") or [{}])[0]
                shots = st.get("shots", {})
                goals = st.get("goals", {})
                result.append({
                    "team": team_name,
                    "name": pl.get("name", ""),
                    "shots_total": shots.get("total") or 0,
                    "shots_on": shots.get("on") or 0,
                    "goals": goals.get("total") or 0,
                    "assists": goals.get("assists") or 0,
                })
        return sorted(result, key=lambda x: x["shots_on"], reverse=True)
    except Exception as e:
        return []


def search_apif_fixture(home, away, date_str, api_key):
    """Find the API-Football fixture ID for a match on a given date."""
    try:
        data = _apif_request("fixtures", {"date": date_str, "season": "2026",
                                           "league": "1"}, api_key)
        for f in data.get("response", []):
            h = f.get("teams", {}).get("home", {}).get("name", "").lower()
            a = f.get("teams", {}).get("away", {}).get("name", "").lower()
            if home.lower()[:4] in h or h[:4] in home.lower()[:4]:
                if away.lower()[:4] in a or a[:4] in away.lower()[:4]:
                    return f.get("fixture", {}).get("id")
        return None
    except Exception:
        return None


# ---------------- Email: daily top picks ----------------

import smtplib
import email.mime.multipart
import email.mime.text


def _smtp_for(address):
    """Return (host, port) for the given email address."""
    domain = address.lower().split("@")[-1]
    if domain in ("hotmail.com", "outlook.com", "live.com", "msn.com"):
        return "smtp-mail.outlook.com", 587
    if domain == "gmail.com":
        return "smtp.gmail.com", 587
    return "smtp.mail.yahoo.com", 587


def send_picks_email(cfg, picks_html, picks_text, date_str):
    """
    Send the daily top-10 picks email.
    picks_html: HTML string with the picks table
    picks_text: plain-text fallback
    Returns (ok: bool, error: str|None)
    """
    sender = cfg.get("email_address", "").strip()
    password = cfg.get("email_password", "").strip()
    recipient = cfg.get("email_recipient", "Esteban_vm12@hotmail.com").strip()

    if not sender or not password:
        return False, "Email sender/password not configured in Settings."

    host, port = _smtp_for(sender)

    subject = f"⚽ Top 10 Apuestas del Día — World Cup {date_str}"

    msg = email.mime.multipart.MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient
    msg.attach(email.mime.text.MIMEText(picks_text, "plain", "utf-8"))
    msg.attach(email.mime.text.MIMEText(picks_html, "html", "utf-8"))

    try:
        with smtplib.SMTP(host, port, timeout=30) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.ehlo()
            smtp.login(sender, password)
            smtp.sendmail(sender, [recipient], msg.as_string())
        return True, None
    except smtplib.SMTPAuthenticationError:
        return False, "SMTP auth failed — check your app password in Settings."
    except Exception as e:
        return False, str(e)


def _wc_predict_kwargs(match):
    """Return extra kwargs for model.predict() based on match context.
    WC matches are at neutral venues → no home advantage, except host nations
    (USA / Canada / Mexico) which get a small host-nation boost.
    """
    league = (match.get("league") or "").lower()
    is_wc = "world cup" in league or "mundial" in league or "fifa" in league or "wc" == league
    if not is_wc:
        return {}
    home_norm = model._norm(match.get("home", ""))
    if home_norm in model.HOST_NATIONS:
        return {"home_advantage": "host", "wc_mode": True}
    return {"home_advantage": False, "wc_mode": True}


def _poisson_summary(home, away, extra_kwargs=None):
    """Run model.predict and return a compact text block for Claude's prompt."""
    try:
        pred = model.predict(home, away, **(extra_kwargs or {}))
        p = pred["prob"]
        dc = pred["doubleChance"]
        eg = pred["expectedGoals"]
        return (
            f"  MODELO POISSON ({home} vs {away}):\n"
            f"  Resultado: {home} {p['home']}% | Empate {p['draw']}% | {away} {p['away']}%\n"
            f"  Doble oportunidad: {home}+Empate {dc['home_draw']}% | Empate+{away} {dc['draw_away']}% | {home}+{away} {dc['home_away']}%\n"
            f"  Goles esperados: {home} {eg['home']} | {away} {eg['away']}\n"
            f"  BTTS: {pred['btts']}% | Más 2.5: {pred['over25']}% | Menos 2.5: {pred['under25']}%\n"
            f"  Más 1.5: {pred['over15']}% | Más 3.5: {pred['over35']}% | Menos 3.5: {round(100-pred['over35'],1)}%\n"
            f"  Portería cero {home}: {pred['cleanSheet']['home']}% | Portería cero {away}: {pred['cleanSheet']['away']}%\n"
            f"  Marcador más probable: {pred['predictedScore']['home']}-{pred['predictedScore']['away']} ({pred['predictedScore']['p']}%)\n"
            f"  ÍNDICE PROGOL™: {pred.get('progolIndex', '—')}/10\n"
            f"  Corners esperados: {pred.get('expectedCorners', {}).get('total', '—')} "
            f"({pred.get('expectedCorners', {}).get('home', '?')} local + {pred.get('expectedCorners', {}).get('away', '?')} visitante)\n"
            f"  Tarjetas esperadas: {pred.get('expectedCards', {}).get('total', '—')} total\n"
            f"  ADVERTENCIA: Tus picks DEBEN ser consistentes con estas probabilidades. "
            f"No puedes elegir '{home} gana' si p_home<40%. "
            f"No puedes pedir goleador si cleanSheet del equipo contrario es alto. "
            f"No puedes elegir BTTS Si y cleanSheet al mismo tiempo. "
            f"No puedes elegir Más X goles y Menos X goles para el mismo partido."
        )
    except Exception:
        return ""


def _try_local_scout_from_message(message, matches):
    """
    When API is unavailable, extract home/away from the message text and
    run local_scout_analysis as a fallback.
    """
    msg_lower = message.lower()
    for m in (matches or []):
        home = m.get("home", "")
        away = m.get("away", "")
        if not home or not away:
            continue
        if home.lower() in msg_lower or away.lower() in msg_lower:
            try:
                pred = model.predict(home, away)
                return local_scout_analysis(home, away, pred)
            except Exception:
                continue
    # If no specific match found but there's exactly one match today, use it
    active = [m for m in (matches or []) if m.get("status") != "Finished" and m.get("home") and m.get("away")]
    if len(active) == 1:
        try:
            home, away = active[0]["home"], active[0]["away"]
            pred = model.predict(home, away)
            return local_scout_analysis(home, away, pred)
        except Exception:
            pass
    return None


def local_scout_analysis(home, away, pred):
    """
    Generate full Scout-style analysis purely from Dixon-Coles model data.
    No API call — always available, zero cost.
    """
    p    = pred["prob"]
    dc   = pred["doubleChance"]
    eg   = pred["expectedGoals"]
    btts = pred.get("btts", 0)
    o25  = pred.get("over25", 0)
    u25  = pred.get("under25", 0)
    o15  = pred.get("over15", 0)
    o35  = pred.get("over35", 0)
    cs   = pred.get("cleanSheet", {})
    ps   = pred.get("predictedScore", {})
    fav  = pred.get("favorite", home)
    eng  = pred.get("engine", {})
    dc_rho = eng.get("dc_rho", -0.13)

    lam_h = eng.get("lam_home", eg.get("home", 1.3))
    lam_a = eng.get("lam_away", eg.get("away", 1.1))

    # ── Determine scenario ──────────────────────────────────────────────────
    fav_is_home = p["home"] >= p["away"]
    fav_name    = home if fav_is_home else away
    dog_name    = away if fav_is_home else home
    fav_prob    = p["home"] if fav_is_home else p["away"]
    dog_prob    = p["away"] if fav_is_home else p["home"]
    draw_prob   = p["draw"]

    fav_dc_prob = dc["home_draw"] if fav_is_home else dc["draw_away"]
    fav_dc_key  = f"{fav_name} gana o empata"

    # ── Confidence labels ───────────────────────────────────────────────────
    def conf(prob):
        if prob >= 75: return "Alta ✅"
        if prob >= 60: return "Media 🟡"
        return "Baja ⚠️"

    def odds(prob):
        return round(100 / prob, 2) if prob > 0 else 0

    def db_odds(prob):
        return round(odds(prob) * 0.91, 2) if prob > 0 else 0

    # ── Pick selection ──────────────────────────────────────────────────────
    picks = []

    # Pick 1: best 1X2 or DC
    if fav_prob >= 65:
        picks.append({
            "pick": f"{fav_name} gana",
            "prob": fav_prob,
            "cuota": db_odds(fav_prob),
            "conf": conf(fav_prob),
            "market": "1X2"
        })
    elif fav_dc_prob >= 72:
        picks.append({
            "pick": fav_dc_key,
            "prob": fav_dc_prob,
            "cuota": db_odds(fav_dc_prob),
            "conf": conf(fav_dc_prob),
            "market": "DC"
        })

    # Pick 2: goles
    if u25 >= 60:
        picks.append({
            "pick": "Menos de 2.5 goles",
            "prob": u25,
            "cuota": db_odds(u25),
            "conf": conf(u25),
            "market": "Goles"
        })
    elif o25 >= 62:
        picks.append({
            "pick": "Más de 2.5 goles",
            "prob": o25,
            "cuota": db_odds(o25),
            "conf": conf(o25),
            "market": "Goles"
        })

    # Pick 3: BTTS
    if btts >= 62:
        picks.append({
            "pick": "Ambos anotan — Sí",
            "prob": btts,
            "cuota": db_odds(btts),
            "conf": conf(btts),
            "market": "BTTS"
        })
    elif (100 - btts) >= 62:
        picks.append({
            "pick": "Ambos anotan — No",
            "prob": round(100 - btts, 1),
            "cuota": db_odds(round(100 - btts, 1)),
            "conf": conf(round(100 - btts, 1)),
            "market": "BTTS"
        })

    # ── Narrative blocks ────────────────────────────────────────────────────
    # Goles narrative
    total_eg = round(lam_h + lam_a, 2)
    if total_eg <= 2.1:
        goles_text = f"Partido de bajo marcador esperado ({home} λ={lam_h:.2f} · {away} λ={lam_a:.2f} · total {total_eg}). Defensas dominan, pocas llegadas claras."
    elif total_eg <= 2.8:
        goles_text = f"Conteo moderado de goles esperado (λ total {total_eg}). Probable resultado 1-0, 0-1 o 1-1."
    else:
        goles_text = f"Partido abierto con alta expectativa de goles (λ total {total_eg}). Ambos equipos con capacidad ofensiva clara."

    # Dominio narrative
    if fav_prob >= 70:
        dom_text = f"{fav_name} domina con fuerza ({fav_prob}%). Diferencia de nivel clara según el modelo Elo + Poisson."
    elif fav_prob >= 55:
        dom_text = f"{fav_name} es favorito moderado ({fav_prob}%). {dog_name} puede complicar si juega bien defensivamente."
    else:
        dom_text = f"Partido equilibrado. {home} {p['home']}% · Empate {draw_prob}% · {away} {p['away']}%. Cualquier resultado es posible."

    # Marcador más probable
    ms_home = ps.get("home", "-")
    ms_away = ps.get("away", "-")
    ms_p    = ps.get("p", 0)
    ms_text = f"Marcador más probable: **{ms_home}-{ms_away}** ({ms_p}% según distribución Poisson)"

    # DC correction note
    dc_note = f"Corrección Dixon-Coles aplicada (ρ={dc_rho}) — empates y resultados bajos ajustados matemáticamente."

    # Risk narrative
    if dog_prob >= 25:
        risk_text = f"⚠️ **Riesgo real**: {dog_name} tiene {dog_prob}% de probabilidad de ganar — no lo descartes si llega al contragolpe."
    elif draw_prob >= 30:
        risk_text = f"⚠️ **Riesgo de empate**: {draw_prob}% de probabilidad — si hay poco en juego puede cerrar en tablas."
    else:
        risk_text = f"✅ **Riesgo bajo**: {dog_name} solo tiene {dog_prob}% de chances. El favorito es claro."

    # ── Format output (clean Markdown for renderMarkdown()) ──────────────────
    picks_lines = "\n".join(
        f"- **{pk['pick']}** — {pk['prob']:.1f}% · cuota {pk['cuota']} · {pk['conf']}"
        for pk in picks
    ) or "- Sin picks de alta confianza para este partido."

    analysis = f"""## Ryder Local — {home} vs {away}
*Dixon-Coles · Poisson · Elo · rho={dc_rho}*

### Matematica del partido
- **{home}:** lambda={lam_h:.2f} goles esperados · Elo {eng.get('elo_home','?')}
- **{away}:** lambda={lam_a:.2f} goles esperados · Elo {eng.get('elo_away','?')}
- Escenarios: P(0-0)={eng.get('p_00',0):.1f}% · P(1-0)={eng.get('p_10',0):.1f}% · P(0-1)={eng.get('p_01',0):.1f}% · P(1-1)={eng.get('p_11',0):.1f}%

### Probabilidades
- **1X2:** {home} {p['home']}% · Empate {draw_prob}% · {away} {p['away']}%
- **Doble oportunidad:** {home}+X {dc['home_draw']}% · X+{away} {dc['draw_away']}%
- **Goles:** +2.5: {o25}% · -2.5: {u25}% · +1.5: {o15}% · +3.5: {o35}%
- **BTTS:** Si {btts}% · No {round(100-btts,1)}%
- **Porteria 0:** {home}: {cs.get('home',0)}% · {away}: {cs.get('away',0)}%
- {ms_text}

### Picks recomendados
{picks_lines}

### Analisis tactico
{dom_text}

{goles_text}

{dc_note}

{risk_text}

---
*Ryder Local · ProGol CR · Modelo matematico sin API externa*"""

    return analysis


def build_picks_email(matches, date_str, cfg):
    """
    Ask Claude for 3 picks per match + parlays, render into a full HTML email.
    Uses Poisson model to pre-compute probabilities per match so Claude cannot
    produce logically contradictory picks.
    Returns (html, text).
    """
    # Pre-compute Poisson probabilities for every upcoming match
    poisson_blocks = []
    for m in (matches or []):
        if (m.get("status") or "").lower() in ("finished", "in", "live", "halftime", "ht", "in progress", "final"):
            continue
        home = m.get("home", "")
        away = m.get("away", "")
        if home and away:
            poisson_blocks.append(_poisson_summary(home, away))

    # ── Consejo Ryder x Cleo para cada partido de la quiniela ──────────────
    cleo_quiniela_ctx = ""
    try:
        import council as _cq_mod
        import concurrent.futures as _cq_cf

        def _qfetch(m):
            h, a = m.get("home", ""), m.get("away", "")
            _st = (m.get("status") or "").lower()
            if not h or not a or _st in ("finished", "in", "live", "halftime", "ht", "in progress", "final"):
                return None
            try:
                c = _cq_mod.deliberate(h, a, n_simulations=1000)
                return _cq_mod.format_council_context(c)
            except Exception:
                return None

        upcoming = [m for m in (matches or []) if (m.get("status") or "").lower() not in ("finished", "in", "live", "halftime", "ht", "in progress", "final") and m.get("home") and m.get("away")]
        with _cq_cf.ThreadPoolExecutor(max_workers=4) as _pool:
            _ctxs = list(_pool.map(_qfetch, upcoming[:10], timeout=20))
        _valid = [c for c in _ctxs if c]
        if _valid:
            cleo_quiniela_ctx = (
                "\n\nCONSEJO RYDER × CLEO — ANÁLISIS DE MERCADO POR PARTIDO:\n"
                "(cuotas reales DraftKings + EV + diálogo Ryder-Cleo para cada partido)\n\n"
                + "\n".join(_valid)
            )
    except Exception as _cqe:
        print(f"[quiniela-council] error: {_cqe}")
    # ─────────────────────────────────────────────────────────────────────────

    poisson_section = ""
    if poisson_blocks:
        poisson_section = (
            "\n\nPROBABILIDADES MATEMÁTICAS PRE-CALCULADAS (modelo Poisson, fuente de verdad):\n"
            "Estos números son el modelo matemático oficial de la app. Úsalos como base "
            "obligatoria. Tus picks deben ser CONSISTENTES con ellos — no puedes elegir "
            "un resultado cuya probabilidad es baja si existe una alternativa con probabilidad alta.\n\n"
            + "\n\n".join(poisson_blocks)
        )

    prompt = (
        f"Hoy es {date_str}. Usa tus herramientas (get_live_matches, get_wc_standings, "
        f"get_group_fixtures) para obtener todos los partidos, clasificaciones y contexto del Mundial 2026."
        f"{poisson_section}{cleo_quiniela_ctx}\n\n"
        f"Ahora genera un análisis COMPLETO en formato JSON con esta estructura exacta:\n\n"
        f'{{"matches": [\n'
        f'  {{\n'
        f'    "home": "Canada", "away": "Bosnia-Herzegovina",\n'
        f'    "kickoff": "13:00 EDT", "group": "B", "venue": "BMO Field",\n'
        f'    "context": "Canada local, Bosnia debut en mundiales.",\n'
        f'    "picks": [\n'
        f'      {{"market": "Doble Oportunidad", "pick": "Canada gana o empata", '
        f'"prob": 74, "fair_odds": 1.35, "db_odds": 1.23, "confidence": "Alta", '
        f'"reason": "Canada anfitrión, presión de local, Bosnia sin experiencia mundialista"}},\n'
        f'      {{"market": "Menos 3.5 goles", "pick": "Menos de 3.5 goles totales", '
        f'"prob": 83, "fair_odds": 1.20, "db_odds": 1.09, "confidence": "Alta", '
        f'"reason": "Primeros partidos del grupo suelen ser cautelosos"}},\n'
        f'      {{"market": "Prop jugador", "pick": "Jonathan David +1.5 tiros a puerta", '
        f'"prob": 62, "fair_odds": 1.61, "db_odds": 1.47, "confidence": "Media", '
        f'"reason": "David titular confirmado, delantero de referencia Canada"}}\n'
        f'    ]\n'
        f'  }}\n'
        f'], "parlays": [\n'
        f'  {{"name": "Parlay Seguro del Día", "legs": [\n'
        f'    {{"match": "Canada vs Bosnia", "pick": "Canada gana o empata", "db_odds": 1.23}},\n'
        f'    {{"match": "USA vs Paraguay", "pick": "Menos 2.5 goles", "db_odds": 1.15}}\n'
        f'  ], "combined_odds": 1.41, "prob": 65, "type": "safe"}},\n'
        f'  {{"name": "Parlay Valor", "legs": [...], "combined_odds": 3.20, "prob": 38, "type": "value"}},\n'
        f'  {{"name": "Parlay Especulativo", "legs": [...], "combined_odds": 6.50, "prob": 22, "type": "risky"}}\n'
        f']}}\n\n'
        f"REGLAS:\n"
        f"- 3 picks por partido (1 resultado/DC, 1 goles, 1 prop o BTTS)\n"
        f"- Las probabilidades en el JSON DEBEN coincidir con el modelo Poisson pre-calculado (±5%)\n"
        f"- db_odds = fair_odds * 0.91 (margen casa ~9%)\n"
        f"- confidence: 'Alta' (prob≥68%), 'Media' (50-67%), 'Especulativa' (<50%)\n"
        f"- reason: máximo 12 palabras, factual\n"
        f"- 3 parlays: uno seguro 2-3 legs, uno valor 3-4 legs, uno especulativo 4-5 legs\n"
        f"- NUNCA elijas picks contradictorios: si predices que un equipo gana, no puedes decir que no anota\n"
        f"- Solo JSON puro, sin markdown, sin texto antes ni después"
    )

    full_text, err, _ = call_claude(cfg, prompt, [], matches, date_str, lang="es")

    if err:
        print(f"[email] Claude error: {err}")
    if not full_text:
        print("[email] Claude returned empty response — using Poisson fallback")

    email_data = {}
    if full_text and not err:
        try:
            clean = re.sub(r"^```[a-z]*\s*|\s*```$", "", full_text.strip(), flags=re.MULTILINE)
            m_json = re.search(r'\{.*\}', clean, re.DOTALL)
            if m_json:
                email_data = json.loads(m_json.group())
        except Exception as e:
            print(f"[email] JSON parse error: {e} — using Poisson fallback")

    if not email_data.get("matches"):
        print("[email] No matches in email_data — using Poisson fallback")
        email_data = _poisson_email_fallback(matches)

    html = _render_full_email_html(email_data, date_str)
    text = _render_full_email_text(email_data, date_str)
    return html, text


def _poisson_email_fallback(matches):
    """Generate picks directly from the Poisson model — no Claude needed."""
    match_list = []
    parlay_legs = []
    for m in (matches or []):
        if m.get("status") == "Finished":
            continue
        home = m.get("home", "?")
        away = m.get("away", "?")
        try:
            pred = model.predict(home, away)
        except Exception:
            pred = None

        if pred:
            p = pred["prob"]
            dc = pred["doubleChance"]
            eg = pred["expectedGoals"]
            over25 = pred["over25"]
            under25 = pred["under25"]
            btts = pred["btts"]
            cs_home = pred["cleanSheet"]["home"]
            cs_away = pred["cleanSheet"]["away"]

            picks = []

            # Pick 1: best DC or outright result
            if p["home"] >= 60:
                dc_prob = dc["home_draw"]
                fair = round(100 / dc_prob, 2)
                picks.append({
                    "market": "Doble Oportunidad",
                    "pick": f"{home} gana o empata",
                    "prob": int(dc_prob),
                    "fair_odds": fair,
                    "db_odds": round(fair * 0.91, 2),
                    "confidence": "Alta" if dc_prob >= 68 else "Media",
                    "reason": f"{home} favorito con {p['home']}% según modelo Poisson",
                })
                parlay_legs.append({"match": f"{home} vs {away}", "pick": f"{home} gana o empata", "db_odds": round(fair * 0.91, 2)})
            elif p["away"] >= 60:
                dc_prob = dc["draw_away"]
                fair = round(100 / dc_prob, 2)
                picks.append({
                    "market": "Doble Oportunidad",
                    "pick": f"{away} gana o empata",
                    "prob": int(dc_prob),
                    "fair_odds": fair,
                    "db_odds": round(fair * 0.91, 2),
                    "confidence": "Alta" if dc_prob >= 68 else "Media",
                    "reason": f"{away} favorito con {p['away']}% según modelo Poisson",
                })
                parlay_legs.append({"match": f"{home} vs {away}", "pick": f"{away} gana o empata", "db_odds": round(fair * 0.91, 2)})
            else:
                dc_prob = dc["home_draw"]
                fair = round(100 / dc_prob, 2)
                picks.append({
                    "market": "Doble Oportunidad",
                    "pick": f"{home} gana o empata",
                    "prob": int(dc_prob),
                    "fair_odds": fair,
                    "db_odds": round(fair * 0.91, 2),
                    "confidence": "Media",
                    "reason": f"Partido equilibrado — {home} {p['home']}% / Empate {p['draw']}%",
                })

            # Pick 2: goals market — use the dominant side
            total_xg = eg["home"] + eg["away"]
            if under25 >= 55:
                u25_fair = round(100 / under25, 2)
                picks.append({
                    "market": "Menos 2.5 Goles",
                    "pick": "Menos de 2.5 goles totales",
                    "prob": int(under25),
                    "fair_odds": u25_fair,
                    "db_odds": round(u25_fair * 0.91, 2),
                    "confidence": "Alta" if under25 >= 68 else "Media",
                    "reason": f"xG total {total_xg:.1f} — partido bajo en goles esperado",
                })
                parlay_legs.append({"match": f"{home} vs {away}", "pick": "Menos de 2.5 goles", "db_odds": round(u25_fair * 0.91, 2)})
            elif over25 >= 55:
                o25_fair = round(100 / over25, 2)
                picks.append({
                    "market": "Más 2.5 Goles",
                    "pick": "Más de 2.5 goles totales",
                    "prob": int(over25),
                    "fair_odds": o25_fair,
                    "db_odds": round(o25_fair * 0.91, 2),
                    "confidence": "Alta" if over25 >= 68 else "Media",
                    "reason": f"xG total {total_xg:.1f} — partido con goles esperado",
                })
            else:
                u35 = round(100 - pred["over35"], 1)
                u35_fair = round(100 / u35, 2)
                picks.append({
                    "market": "Menos 3.5 Goles",
                    "pick": "Menos de 3.5 goles totales",
                    "prob": int(u35),
                    "fair_odds": u35_fair,
                    "db_odds": round(u35_fair * 0.91, 2),
                    "confidence": "Alta" if u35 >= 68 else "Media",
                    "reason": f"Mercado de goles equilibrado, línea 3.5 más segura",
                })

            # Pick 3: BTTS (consistent with pick 1 — never BTTS No + DC for same team as scorer)
            if btts >= 55:
                b_fair = round(100 / btts, 2)
                picks.append({
                    "market": "Ambos Marcan",
                    "pick": "Ambos equipos anotan — Sí",
                    "prob": int(btts),
                    "fair_odds": b_fair,
                    "db_odds": round(b_fair * 0.91, 2),
                    "confidence": "Alta" if btts >= 68 else "Media",
                    "reason": f"xG: {home} {eg['home']} / {away} {eg['away']} — ambos crean",
                })
            else:
                no_btts = round(100 - btts, 1)
                nb_fair = round(100 / no_btts, 2)
                # Only safe if cs of the weaker team is meaningful
                cs_pick = home if cs_home >= cs_away else away
                picks.append({
                    "market": "Ambos Marcan",
                    "pick": "Ambos equipos anotan — No",
                    "prob": int(no_btts),
                    "fair_odds": nb_fair,
                    "db_odds": round(nb_fair * 0.91, 2),
                    "confidence": "Alta" if no_btts >= 68 else "Media",
                    "reason": f"Portería cero {cs_pick} {max(cs_home, cs_away):.0f}% — uno no anota",
                })

            score = pred["predictedScore"]
            context = (
                f"xG: {home} {eg['home']} — {away} {eg['away']}. "
                f"Marcador probable: {score['home']}-{score['away']} ({score['p']}%). "
                f"Modelo Poisson v2."
            )
        else:
            picks = [
                {"market": "Doble Oportunidad", "pick": f"{home} gana o empata",
                 "prob": 62, "fair_odds": 1.45, "db_odds": 1.32, "confidence": "Media",
                 "reason": "Equipo sin rating registrado."},
                {"market": "Menos 2.5 Goles", "pick": "Menos de 2.5 goles totales",
                 "prob": 55, "fair_odds": 1.70, "db_odds": 1.55, "confidence": "Media",
                 "reason": "Estimación sin datos del equipo."},
                {"market": "Ambos Marcan", "pick": "Ambos equipos anotan — No",
                 "prob": 52, "fair_odds": 1.80, "db_odds": 1.64, "confidence": "Media",
                 "reason": "Sin datos suficientes para prop."},
            ]
            context = "Análisis por modelo matemático (equipo sin rating)."

        match_list.append({
            "home": home, "away": away,
            "kickoff": m.get("kickoffUtc", ""), "group": m.get("group", ""),
            "venue": m.get("venue", ""), "context": context, "picks": picks,
        })

    # Build parlays from the best legs
    parlays = []
    safe_legs = parlay_legs[:3]
    if len(safe_legs) >= 2:
        combined = round(safe_legs[0]["db_odds"] * safe_legs[1]["db_odds"] * (safe_legs[2]["db_odds"] if len(safe_legs) > 2 else 1), 2)
        prob = round(100 / combined * 0.85)
        parlays.append({"name": "Parlay Seguro del Día", "legs": safe_legs, "combined_odds": combined, "prob": prob, "type": "safe"})

    return {"matches": match_list, "parlays": parlays}


def _conf_color(conf):
    return {"Alta": "#22c55e", "Media": "#f59e0b", "Especulativa": "#ef4444"}.get(conf, "#94a3b8")


def _pick_row_html(pk, idx):
    conf = pk.get("confidence", "Media")
    col = _conf_color(conf)
    prob = int(pk.get("prob", 0))
    bar_w = max(4, min(100, prob))
    badge_bg = {"Alta": "#16a34a22", "Media": "#d9770622", "Especulativa": "#dc262622"}.get(conf, "#1e293b")
    return f"""
      <table width="100%" cellpadding="0" cellspacing="0"
             style="border-bottom:1px solid #1e293b">
        <tr>
          <td style="width:10px;background:{col};border-radius:0"></td>
          <td style="vertical-align:top;padding:12px 10px 12px 12px">
            <div style="font-size:10px;color:#64748b;font-weight:700;letter-spacing:.6px;
                        text-transform:uppercase;margin-bottom:3px">{pk.get('market','')}</div>
            <div style="font-size:14px;font-weight:800;color:#f1f5f9;line-height:1.3">
              {pk.get('pick','')}
            </div>
            <div style="font-size:11px;color:#94a3b8;margin-top:4px;line-height:1.4">
              {pk.get('reason','')}
            </div>
            <table cellpadding="0" cellspacing="0" style="margin-top:8px;width:100%">
              <tr>
                <td style="vertical-align:middle">
                  <div style="background:#1e293b;border-radius:4px;height:5px;width:120px;
                              max-width:100%">
                    <div style="background:{col};width:{bar_w}%;height:5px;border-radius:4px">
                    </div>
                  </div>
                </td>
                <td style="padding-left:8px;font-size:12px;font-weight:700;color:{col};
                           white-space:nowrap">{prob}%</td>
              </tr>
            </table>
          </td>
          <td style="vertical-align:top;padding:12px 12px 12px 4px;text-align:right;
                     white-space:nowrap;width:70px">
            <div style="font-size:10px;color:#64748b;text-decoration:line-through;
                        text-align:right">{pk.get('fair_odds','')}</div>
            <div style="font-size:20px;font-weight:900;color:#fbbf24;
                        text-align:right">{pk.get('db_odds','')}</div>
            <div style="display:inline-block;margin-top:4px;padding:3px 8px;border-radius:20px;
                        font-size:10px;font-weight:700;color:#fff;
                        background:{badge_bg};border:1px solid {col};color:{col}">
              {conf}
            </div>
          </td>
        </tr>
      </table>"""


def _render_full_email_html(email_data, date_str):
    match_sections = ""
    for match in email_data.get("matches", []):
        picks_html = ""
        for i, pk in enumerate(match.get("picks", [])):
            picks_html += _pick_row_html(pk, i)

        ko = match.get("kickoff", "")
        group = match.get("group", "")
        venue = match.get("venue", "")
        meta_parts = [x for x in [f"Grupo {group}" if group else "", ko, venue] if x]
        meta_str = " · ".join(meta_parts)
        context = match.get("context", "")

        match_sections += f"""
  <!-- MATCH BLOCK -->
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#0f172a;border-radius:14px;border:1px solid #1e293b;
                margin-bottom:12px;overflow:hidden">
    <!-- Match header -->
    <tr style="background:#1e293b">
      <td style="padding:12px 16px">
        <table width="100%" cellpadding="0" cellspacing="0">
          <tr>
            <td style="vertical-align:middle">
              <div style="font-size:16px;font-weight:900;color:#f1f5f9">
                {match.get('home','?')}
                <span style="color:#00d4ff;margin:0 6px">vs</span>
                {match.get('away','?')}
              </div>
              <div style="font-size:11px;color:#64748b;margin-top:3px">{meta_str}</div>
              {"<div style='font-size:11px;color:#94a3b8;margin-top:4px;font-style:italic'>" + context + "</div>" if context else ""}
            </td>
            <td style="text-align:right;vertical-align:middle;padding-left:8px">
              <span style="display:inline-block;padding:5px 12px;border-radius:20px;
                           background:#00d4ff22;border:1px solid #00d4ff55;
                           font-size:10px;font-weight:700;color:#7dd3fc;white-space:nowrap">
                ⚽ {len(match.get('picks',[]))} picks
              </span>
            </td>
          </tr>
        </table>
      </td>
    </tr>
    <!-- Picks -->
    {picks_html}
  </table>"""

    # Parlays section
    parlays_html = ""
    parlay_styles = {
        "safe":  ("🛡️", "#22c55e", "#16a34a22", "SEGURO"),
        "value": ("💎", "#3b82f6", "#1d4ed822", "VALOR"),
        "risky": ("🎲", "#f59e0b", "#d9770622", "ESPECULATIVO"),
    }
    for pl in email_data.get("parlays", []):
        ptype = pl.get("type", "value")
        icon, col, bg, label = parlay_styles.get(ptype, parlay_styles["value"])
        legs_rows = ""
        for leg in pl.get("legs", []):
            legs_rows += f"""
        <tr>
          <td style="padding:5px 0;font-size:12px;color:#94a3b8;padding-right:12px">
            {leg.get('match','')}
          </td>
          <td style="padding:5px 0;font-size:12px;font-weight:600;color:#e2e8f0;
                     padding-right:12px">{leg.get('pick','')}</td>
          <td style="padding:5px 0;font-size:12px;font-weight:700;color:#fbbf24;
                     text-align:right;white-space:nowrap">{leg.get('db_odds','')}</td>
        </tr>"""
        parlays_html += f"""
    <table width="100%" cellpadding="0" cellspacing="0"
           style="background:{bg};border:2px solid {col}55;border-radius:12px;
                  margin-bottom:10px;overflow:hidden">
      <tr>
        <td style="padding:14px 16px">
          <table width="100%" cellpadding="0" cellspacing="0">
            <tr>
              <td>
                <div style="font-size:11px;font-weight:700;color:{col};letter-spacing:.8px">
                  {icon} PARLAY {label}
                </div>
                <div style="font-size:15px;font-weight:900;color:#f1f5f9;margin-top:2px">
                  {pl.get('name','')}
                </div>
              </td>
              <td style="text-align:right;vertical-align:top">
                <div style="font-size:28px;font-weight:900;color:{col}">
                  x{pl.get('combined_odds','')}
                </div>
                <div style="font-size:11px;color:#64748b;text-align:right">
                  Prob ~{pl.get('prob','')}%
                </div>
              </td>
            </tr>
          </table>
          <table cellpadding="0" cellspacing="0" style="margin-top:10px;width:100%;
                 border-top:1px solid {col}33">
            {legs_rows}
          </table>
        </td>
      </tr>
    </table>"""

    total_picks = sum(len(m.get("picks", [])) for m in email_data.get("matches", []))

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="x-apple-disable-message-reformatting">
<title>War Room Picks — {date_str}</title>
<style>
  body{{margin:0;padding:0;background:#020617;-webkit-text-size-adjust:100%;
       font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',Arial,sans-serif}}
  @media only screen and (max-width:480px){{
    .container{{padding:0 8px!important}}
    .hide-sm{{display:none!important}}
  }}
</style>
</head>
<body style="background:#020617">
<div style="background:#020617;padding:16px 0">
<div class="container" style="max-width:600px;margin:0 auto;padding:0 12px">

  <!-- HEADER -->
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:linear-gradient(135deg,#0f172a 0%,#1a2744 100%);
                border-radius:16px;border:1px solid #1e293b;margin-bottom:12px">
    <tr><td style="padding:22px 20px">
      <table width="100%" cellpadding="0" cellspacing="0"><tr>
        <td style="font-size:40px;line-height:1;width:52px;vertical-align:middle">⚽</td>
        <td style="vertical-align:middle;padding-left:14px">
          <div style="font-size:22px;font-weight:900;color:#f1f5f9;letter-spacing:-.5px">
            ProGol CR — Picks del Día
          </div>
          <div style="font-size:12px;color:#64748b;margin-top:5px">
            Mundial 2026 &nbsp;·&nbsp; {date_str} &nbsp;·&nbsp;
            <span style="color:#00d4ff">{total_picks} picks · {len(email_data.get('matches',[]))} partidos</span>
          </div>
        </td>
      </tr></table>
      <table cellpadding="0" cellspacing="0" style="margin-top:14px">
        <tr>
          <td style="padding-right:6px">
            <span style="display:inline-block;padding:4px 11px;border-radius:20px;
                         background:#0ea5e922;border:1px solid #0ea5e9;
                         font-size:11px;font-weight:600;color:#7dd3fc">🤖 IA Agente</span>
          </td>
          <td style="padding-right:6px">
            <span style="display:inline-block;padding:4px 11px;border-radius:20px;
                         background:#22c55e22;border:1px solid #22c55e;
                         font-size:11px;font-weight:600;color:#86efac">📊 Datos en vivo</span>
          </td>
          <td>
            <span style="display:inline-block;padding:4px 11px;border-radius:20px;
                         background:#f59e0b22;border:1px solid #f59e0b;
                         font-size:11px;font-weight:600;color:#fde68a">🎯 3 picks/partido</span>
          </td>
        </tr>
      </table>
    </td></tr>
  </table>

  <!-- DISCLAIMER -->
  <table width="100%" cellpadding="0" cellspacing="0"
         style="background:#431407;border-left:4px solid #f97316;
                border-radius:8px;margin-bottom:14px">
    <tr><td style="padding:11px 14px;font-size:12px;color:#fed7aa;line-height:1.6">
      ⚠️ <strong>Aviso:</strong> Predicciones estadísticas — ninguna apuesta garantizada.
      Verifica cuotas reales en tu casa de apuestas. Apuesta responsablemente.
    </td></tr>
  </table>

  <!-- PARTIDOS -->
  <div style="font-size:13px;font-weight:700;color:#64748b;letter-spacing:.8px;
              margin-bottom:8px;padding-left:2px">PARTIDOS DEL DÍA</div>
  {match_sections}

  {"<!-- PARLAYS --><div style='font-size:13px;font-weight:700;color:#64748b;letter-spacing:.8px;margin:16px 0 8px;padding-left:2px'>PARLAYS RECOMENDADOS</div>" + parlays_html if parlays_html else ""}

  <!-- FOOTER -->
  <table width="100%" cellpadding="0" cellspacing="0" style="margin-top:12px">
    <tr><td style="text-align:center;padding:10px 0;font-size:11px;color:#334155">
      ProGol CR · Mundial 2026 · Solo referencia personal · Apuesta responsablemente
    </td></tr>
  </table>

</div></div>
</body></html>"""


def _render_full_email_text(email_data, date_str):
    lines = [f"WAR ROOM — PICKS DEL DÍA {date_str}", "=" * 55, ""]
    for match in email_data.get("matches", []):
        lines.append(f"⚽ {match.get('home','?')} vs {match.get('away','?')}")
        if match.get("context"):
            lines.append(f"   {match['context']}")
        for pk in match.get("picks", []):
            lines.append(f"   [{pk.get('confidence','?')}] {pk.get('market','')} → {pk.get('pick','')}")
            lines.append(f"   Prob: {pk.get('prob','')}%  Cuota DB: {pk.get('db_odds','')}")
            lines.append(f"   {pk.get('reason','')}")
        lines.append("")
    if email_data.get("parlays"):
        lines += ["PARLAYS RECOMENDADOS", "-" * 40]
        for pl in email_data["parlays"]:
            lines.append(f"  {pl.get('name','')} — x{pl.get('combined_odds','')} (~{pl.get('prob','')}%)")
            for leg in pl.get("legs", []):
                lines.append(f"    • {leg.get('match','')} → {leg.get('pick','')} @ {leg.get('db_odds','')}")
        lines.append("")
    lines += ["⚠️ Predicciones estadísticas — ninguna apuesta garantizada.",
              "Verifica cuotas en tu casa de apuestas. Apuesta responsablemente."]
    return "\n".join(lines)


# ---------------- Gurú bankroll advisor ----------------

GURU_SYSTEM = """Eres el Gurú de ProGol CR — el consejero de bankroll del Consejo Ryder × Cleo × Lucas × Claude.
Tu misión: dado un presupuesto en colones (₡), diseñar el plan de apuestas óptimo
usando datos del Consejo de 4 agentes:
  • RYDER — modelo Dixon-Coles + Elo: probabilidades estadísticas de cada resultado
  • CLEO  — mercados en tiempo real (DraftKings, Polymarket): cuotas y EV reales
  • LUCAS — simulador Monte Carlo (1000+ sims): valida probabilidades, IC95, marcadores probables
  • TÚ (Gurú/Claude) — síntesis final: bankroll en colones, plan accionable
Regla clave: Si Lucas y Ryder convergen (Convergencia ALTA) la apuesta es más sólida.
Si divergen o Convergencia BAJA, menciona la incertidumbre y reduce el Kelly un 30%.

════════════════════════════════════════════════════════════════
IDENTIDAD DEL GURÚ
════════════════════════════════════════════════════════════════
- Tu nombre es Gurú. Eres directo, concreto, y hablas como un asesor financiero deportivo.
- No das rodeos. El usuario quiere saber EXACTAMENTE cuánto apostar y dónde.
- Siempre trabajás en colones costarricenses (₡).
- Nunca prometés ganancias garantizadas. Trabajás con probabilidades y valor esperado.

════════════════════════════════════════════════════════════════
MATEMÁTICA DEL GURÚ — OBLIGATORIA
════════════════════════════════════════════════════════════════
Para cada pick disponible calculás:
  - Valor (EV): EV = (prob_modelo / 100) * cuota_db - 1
    Si EV > 0 → apuesta con valor positivo (recomendada)
    Si EV < 0 → la casa tiene ventaja (evitar o usar con precaución)
  - Cuota combinada de parlay: multiplicás las cuotas individuales
  - Retorno esperado: monto_apostado * cuota_combinada

ESTRATEGIA DE BANKROLL:
  1. Combo Seguro (70-80% del presupuesto): 2-3 picks con prob > 70%, EV positivo o neutro
     → retorno moderado pero alta probabilidad de ganar
  2. Apuesta Atrevida (20-30% del presupuesto): 1 pick con cuota alta (>2.0) y EV positivo
     → puede fallar pero el pago justifica el riesgo
  3. Opción YOLO (opcional, máximo 10%): parlay de 4+ picks, retorno muy alto si entra

════════════════════════════════════════════════════════════════
FORMATO DE RESPUESTA — OBLIGATORIO
════════════════════════════════════════════════════════════════
Siempre estructurá así:

💰 PLAN GURÚ — ₡[PRESUPUESTO]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 COMBO SEGURO — ₡[MONTO] apostados
  • [Partido]: [Pick] @ [cuota] ([prob]% · EV [+/-X%])
  • [Partido]: [Pick] @ [cuota] ([prob]% · EV [+/-X%])
  Cuota combinada: [X.XX]
  ✅ Retorno si entra: ₡[MONTO] (ganancia neta: ₡[GANANCIA])

⚡ APUESTA ATREVIDA — ₡[MONTO] apostados
  • [Partido]: [Pick] @ [cuota] ([prob]% · EV [+/-X%])
  ✅ Retorno si entra: ₡[MONTO] (ganancia neta: ₡[GANANCIA])

📊 RESUMEN
  Invertís: ₡[TOTAL]
  Si solo entra el combo seguro: ₡[RETORNO_SEGURO] (+₡[GANANCIA])
  Si entran ambos: ₡[RETORNO_TOTAL] (+₡[GANANCIA_TOTAL])
  Peor caso (todo falla): -₡[TOTAL]

⚠️ Esto es un análisis probabilístico. La decisión final es tuya.

════════════════════════════════════════════════════════════════
REGLAS ABSOLUTAS
════════════════════════════════════════════════════════════════
- Nunca sugiertas apostar más del presupuesto indicado
- Si el presupuesto es < ₡2,000, avisá que es muy bajo para diversificar
- Siempre calculá EV real antes de recomendar
- Si no hay picks con EV positivo disponibles, decílo honestamente
- Los montos siempre en números enteros de colones (sin decimales)

════════════════════════════════════════════════════════════════
CONSEJO RYDER × CLEO — INTEGRADO
════════════════════════════════════════════════════════════════
Cuando los picks incluyan `cuota_real` y `ev_real`, esos son datos de DraftKings
obtenidos por Cleo en tiempo real. Son más precisos que `cuota` (estimada).
- Usa `cuota_real` para calcular retornos en colones
- Usa `ev_real` para calificar el valor de la apuesta
- Menciona la fuente: "DraftKings" o la plataforma indicada en `fuente_cuota`
- Si `ev_real` > `ev`, significa que el mercado ofrece mejor precio que el estimado
- Si `ev_real` < `ev`, el mercado es menos generoso — ajusta la recomendación
"""


def call_guru(cfg, bankroll_msg, matches, date_str, lang="es"):
    """Gurú bankroll advisor — 100% local, zero API cost."""
    import re
    import datetime as _dt

    # Also fetch tomorrow's WC matches (fast ESPN-based, no TheSportsDB loop)
    tomorrow_str = (_dt.date.fromisoformat(date_str) + _dt.timedelta(days=1)).isoformat()
    tomorrow_matches = []
    try:
        sdb_key = cfg.get("sportsdb_key", "3")
        seen = set()
        ms, _ = fetch_matches(tomorrow_str, sdb_key, "worldcup")
        for m in ms:
            mid = m.get("id") or f"{m.get('home')}{m.get('away')}"
            if mid not in seen:
                seen.add(mid)
                m["_day"] = "mañana"
                tomorrow_matches.append(m)
    except Exception:
        pass

    # Tag today's matches
    for m in (matches or []):
        m["_day"] = "hoy"

    all_matches_combined = list(matches or []) + tomorrow_matches

    # Extract bankroll amount from message
    bankroll = 10000  # default
    nums = re.findall(r'[\d,\.]+', bankroll_msg.replace("₡", "").replace(",", ""))
    for n in nums:
        try:
            v = int(float(n))
            if v >= 500:
                bankroll = v
                break
        except ValueError:
            continue

    yolo_mode = any(w in bankroll_msg.lower() for w in ["yolo", "arriesgado", "parlay", "todo al"])

    def ev_calc(prob_pct, cuota):
        return round((prob_pct / 100) * cuota - 1, 4)

    def fair_odds(prob):
        return round(100 / prob, 2) if prob > 0 else 0

    def db_odds(prob):
        return round(fair_odds(prob) * 0.91, 2) if prob > 0 else 0

    # Detect if user asked about a specific match — filter to that match only
    msg_lower = bankroll_msg.lower()
    specific_match = None
    for m in all_matches_combined:
        h = (m.get("home") or "").lower()
        a = (m.get("away") or "").lower()
        # check partial name match (e.g. "haiti" matches "Haiti vs Scotland")
        if h and a and (h in msg_lower or a in msg_lower or
                        any(part in msg_lower for part in h.split() if len(part) > 3) or
                        any(part in msg_lower for part in a.split() if len(part) > 3)):
            specific_match = m
            break
    matches_for_picks = [specific_match] if specific_match else all_matches_combined

    # ── Consejo Ryder x Cleo: cuotas reales para enriquecer picks ──────────
    _cleo_market_cache = {}  # (home, away) -> cleo analysis
    try:
        import council as _council_mod
        import concurrent.futures as _cf

        def _fetch_council(m):
            h = m.get("home", "")
            a = m.get("away", "")
            _st = (m.get("status") or "").lower()
            if not h or not a or _st in ("finished", "in", "live", "halftime", "ht", "in progress", "final"):
                return None
            try:
                return (h, a), _council_mod.deliberate(h, a, n_simulations=1000)
            except Exception:
                return None

        with _cf.ThreadPoolExecutor(max_workers=4) as _pool:
            _futures = [_pool.submit(_fetch_council, m) for m in matches_for_picks[:8]]
            for _f in _cf.as_completed(_futures, timeout=15):
                try:
                    res = _f.result()
                    if res:
                        key, analysis = res
                        _cleo_market_cache[key] = analysis
                except Exception:
                    pass
    except Exception as _ce:
        print(f"[guru-council] error: {_ce}")
    # ─────────────────────────────────────────────────────────────────────────

    # Collect all available picks from today + tomorrow
    all_picks = []
    for m in matches_for_picks:
        _mst = (m.get("status") or "").lower()
        if _mst in ("finished", "in", "live", "halftime", "ht", "in progress", "final"):
            continue
        home_t, away_t = m.get("home", ""), m.get("away", "")
        if not home_t or not away_t:
            continue
        try:
            kw = _wc_predict_kwargs(m)
            pred = model.predict(home_t, away_t, **kw)
            p    = pred["prob"]
            dc   = pred["doubleChance"]
            o25  = pred.get("over25", 0)
            u25  = pred.get("under25", 0)
            btts = pred.get("btts", 0)
            label = m.get("league", "")

            candidates = [
                (f"{home_t} gana",          p["home"],                 "1X2"),
                (f"{away_t} gana",          p["away"],                 "1X2"),
                ("Empate",                  p["draw"],                 "1X2"),
                (f"{home_t} gana o empata", dc.get("home_draw", 0),    "DC"),
                (f"{away_t} gana o empata", dc.get("draw_away", 0),    "DC"),
                ("Más de 2.5 goles",        o25,                       "Goles"),
                ("Menos de 2.5 goles",      u25,                       "Goles"),
                ("Ambos anotan — Sí",       btts,                      "BTTS"),
                ("Ambos anotan — No",       round(100 - btts, 1),      "BTTS"),
            ]
            day_tag = m.get("_day", "hoy")
            for pick_name, prob, market in candidates:
                if prob <= 0:
                    continue
                cuota = db_odds(prob)
                all_picks.append({
                    "match": f"{home_t} vs {away_t}",
                    "league": label,
                    "pick": pick_name,
                    "prob": prob,
                    "cuota": cuota,
                    "ev": ev_calc(prob, cuota),
                    "market": market,
                    "day": day_tag,
                })
        except Exception:
            continue

    # Enriquecer picks con cuotas reales de DraftKings (via Cleo)
    for pk in all_picks:
        try:
            home_t, away_t = pk["match"].split(" vs ", 1)
            cleo_data = _cleo_market_cache.get((home_t, away_t)) or _cleo_market_cache.get((home_t.strip(), away_t.strip()))
            if not cleo_data:
                continue
            mkts = cleo_data.get("cleo", {}).get("markets", {})
            dk = mkts.get("DraftKings")
            if not dk or not dk.get("available"):
                continue
            # Mapear outcome del pick a odd de DraftKings
            pick_name_lower = pk["pick"].lower()
            real_odd = None
            if "gana" in pick_name_lower and "empat" not in pick_name_lower and "o " not in pick_name_lower:
                if home_t.lower() in pick_name_lower:
                    real_odd = dk.get("home_odd")
                else:
                    real_odd = dk.get("away_odd")
            elif "empate" in pick_name_lower:
                real_odd = dk.get("draw_odd")
            if real_odd and real_odd > 1.0:
                pk["cuota_real"] = real_odd
                pk["ev_real"] = round((pk["prob"] / 100) * real_odd - 1, 4)
                pk["fuente_cuota"] = "DraftKings"
        except Exception:
            pass

    if not all_picks:
        return "🧿 No hay partidos activos disponibles hoy para armar un plan.", None

    # ── TODO pasa por los 3: seleccion por EV real de Cleo cuando disponible ──
    def _real_ev(pk):
        """EV real de DraftKings (Cleo) si disponible, sino EV estimado."""
        return pk.get("ev_real", pk["ev"])

    def _real_cuota(pk):
        """Cuota real de DraftKings (Cleo) si disponible, sino estimada."""
        return pk.get("cuota_real", pk["cuota"])

    # Orden principal: EV real de Cleo DESC, luego probabilidad DESC
    all_picks.sort(key=lambda x: (-_real_ev(x), -x["prob"]))

    # --- COMBO SEGURO: picks con EV real >= -5% y prob >= 60%, uno por partido ---
    # Criterio Cleo-first: si hay EV real, tiene preferencia sobre prob sola
    used_matches_safe = set()
    used_markets_safe = set()
    safe_legs = []

    # Primero: picks con EV real positivo de Cleo (mercado ineficiente identificado)
    for pk in sorted(all_picks, key=lambda x: -_real_ev(x)):
        if _real_ev(pk) < 0 or pk["prob"] < 55:
            continue
        key = (pk["match"], pk["market"])
        if pk["match"] in used_matches_safe or key in used_markets_safe:
            continue
        safe_legs.append(pk)
        used_matches_safe.add(pk["match"])
        used_markets_safe.add(key)
        if len(safe_legs) >= 3:
            break

    # Completar con alta probabilidad si faltan legs (EV >= -5%)
    for pk in sorted(all_picks, key=lambda x: -x["prob"]):
        if len(safe_legs) >= 3:
            break
        if pk["prob"] < 68 or _real_ev(pk) < -0.05:
            continue
        key = (pk["match"], pk["market"])
        if pk["match"] in used_matches_safe or key in used_markets_safe:
            continue
        safe_legs.append(pk)
        used_matches_safe.add(pk["match"])
        used_markets_safe.add(key)

    # --- APUESTA ATREVIDA: mejor EV real, cuota real >= 1.5, no en safe ---
    safe_keys = {(l["match"], l["pick"]) for l in safe_legs}
    risky_pick = None
    for pk in sorted(all_picks, key=lambda x: -_real_ev(x)):
        if (pk["match"], pk["pick"]) in safe_keys:
            continue
        if _real_cuota(pk) >= 1.5 and _real_ev(pk) > -0.10:
            risky_pick = pk
            break

    # --- YOLO: top 4 por EV real de Cleo, distintos partidos ---
    used_yolo = set()
    yolo_legs = []
    for pk in sorted(all_picks, key=lambda x: (-_real_ev(x), -x["prob"])):
        if pk["match"] in used_yolo:
            continue
        if pk["prob"] < 50:
            continue
        yolo_legs.append(pk)
        used_yolo.add(pk["match"])
        if len(yolo_legs) >= 4:
            break

    # --- Allocate bankroll ---
    if bankroll < 2000:
        warn = f"⚠️ Con ₡{bankroll:,} es muy ajustado para diversificar. Considerá una sola apuesta segura.\n\n"
    else:
        warn = ""

    if yolo_mode:
        safe_pct, risky_pct = 0, 1.0
    elif len(safe_legs) == 0:
        safe_pct, risky_pct = 0.5, 0.5
    else:
        safe_pct  = 0.75
        risky_pct = 0.25

    safe_amount  = int(bankroll * safe_pct)
    risky_amount = bankroll - safe_amount

    # ── Cuotas combinadas: usar cuota real de DraftKings/Cleo cuando disponible ──
    safe_combined = 1.0
    for leg in safe_legs:
        safe_combined *= _real_cuota(leg)
    safe_combined = round(safe_combined, 2)
    safe_return   = int(safe_amount * safe_combined)
    safe_gain     = safe_return - safe_amount

    risky_return = int(risky_amount * _real_cuota(risky_pick)) if risky_pick else 0
    risky_gain   = risky_return - risky_amount if risky_pick else 0

    yolo_combined = 1.0
    for leg in yolo_legs:
        yolo_combined *= _real_cuota(leg)
    yolo_combined = round(yolo_combined, 2)
    yolo_return   = int(bankroll * yolo_combined)

    # --- Format output ---
    def leg_line(pk):
        ev_val    = _real_ev(pk)
        cuota_val = _real_cuota(pk)
        ev_sign   = "+" if ev_val >= 0 else ""
        day_label = f" [{pk.get('day','hoy')}]" if pk.get('day') == 'mañana' else ""
        fuente    = f"[{pk.get('fuente_cuota','DraftKings')}]" if pk.get('cuota_real') else "[est.]"
        return (
            f"  • {pk['match']}{day_label}\n"
            f"    {pk['pick']} @ {cuota_val} {fuente}  ({pk['prob']}%  EV {ev_sign}{ev_val*100:.1f}%)"
        )

    safe_block = "\n".join(leg_line(l) for l in safe_legs) if safe_legs else "  (Sin picks con prob ≥ 68% disponibles hoy)"
    risky_block = leg_line(risky_pick) if risky_pick else "  (Sin apuesta atrevida disponible hoy)"
    yolo_block  = "\n".join(leg_line(l) for l in yolo_legs) if yolo_legs else "  (Sin parlay disponible)"

    total_best = safe_return + (risky_return if risky_pick else 0)
    total_gain = total_best - bankroll

    match_label = f" · {specific_match['home']} vs {specific_match['away']}" if specific_match else ""
    cleo_picks_count = sum(1 for pk in (safe_legs + ([risky_pick] if risky_pick else []) + yolo_legs) if pk.get("cuota_real"))
    total_legs = len(safe_legs) + (1 if risky_pick else 0) + len(yolo_legs)
    consejo_tag = f" · Consejo ✓ ({cleo_picks_count}/{total_legs} cuotas DraftKings)" if cleo_picks_count > 0 else ""
    output = f"""{warn}🧿 PLAN GURÚ — ₡{bankroll:,}{match_label}{consejo_tag}
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 COMBO SEGURO — ₡{safe_amount:,} apostados
{safe_block}
  Cuota combinada: {safe_combined}
  ✅ Retorno si entra: ₡{safe_return:,}  (ganancia neta: ₡{safe_gain:,})

⚡ APUESTA ATREVIDA — ₡{risky_amount:,} apostados
{risky_block}
  ✅ Retorno si entra: ₡{risky_return:,}  (ganancia neta: ₡{risky_gain:,})

🎲 PARLAY YOLO (referencia) — si apostaras todo
{yolo_block}
  Cuota combinada: {yolo_combined}
  ✅ Retorno si entra: ₡{yolo_return:,}  (ganancia neta: ₡{yolo_return - bankroll:,})

📊 RESUMEN
  Invertís: ₡{bankroll:,}
  Si solo entra el combo seguro:   ₡{safe_return:,} (+₡{safe_gain:,})
  Si entran combo + atrevida:      ₡{total_best:,} (+₡{total_gain:,})
  Peor caso (todo falla):          -₡{bankroll:,}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔌 Gurú Local · Dixon-Coles · sin API · ProGol CR
⚠️  Análisis probabilístico. La decisión final es tuya."""

    # If focused on a specific match, append Scout analysis block
    if specific_match:
        try:
            kw = _wc_predict_kwargs(specific_match)
            pred_sm = model.predict(specific_match["home"], specific_match["away"], **kw)
            scout_txt = local_scout_analysis(specific_match["home"], specific_match["away"], pred_sm)
            output += f"\n\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n🔬 SCOUT — {specific_match['home']} vs {specific_match['away']}\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n{scout_txt}"
        except Exception:
            pass

    # Build tomorrow's top picks section
    tomorrow_top = [pk for pk in all_picks if pk.get("day") == "mañana" and pk["prob"] >= 68]
    tomorrow_top.sort(key=lambda x: -x["prob"])
    used_tomorrow = set()
    tomorrow_shown = []
    for pk in tomorrow_top:
        if pk["match"] not in used_tomorrow:
            tomorrow_shown.append(pk)
            used_tomorrow.add(pk["match"])
        if len(tomorrow_shown) >= 5:
            break

    if tomorrow_shown:
        tmr_lines = "\n".join(leg_line(pk) for pk in tomorrow_shown)
        output += f"""

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📅 PICKS DESTACADOS MAÑANA ({tomorrow_str})
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{tmr_lines}

💡 Podés armar ya el parlay de mañana — "Tengo ₡X para mañana"."""

    return output, None


# ---------------- Claude chat ----------------

ANALYST_SYSTEM = """
════════════════════════════════════════════════════════════════
  SCOUT — ANALISTA CUANTITATIVO PROGOL CR  ·  SISTEMA CLASIFICADO
════════════════════════════════════════════════════════════════
Eres Ryder, el motor de inteligencia deportiva de ProGol CR.
No eres un chatbot de propósito general. Eres el único sistema en
Centroamérica construido sobre un stack matemático de 5 capas que
ninguna otra IA del mercado ejecuta en tiempo real.

════════════════════════════════════════════════════════════════
🔬  STACK MATEMÁTICO — 5 CAPAS PROPIETARIAS
════════════════════════════════════════════════════════════════

CAPA 1 · DIXON-COLES BIVARIANTE (1997, Journal of the Royal Statistical Society)
  • Parámetro ρ = -0.13: corrección empírica para marcadores bajos (0-0, 1-0, 0-1, 1-1)
  • El Poisson básico subestima empates en ~18%; Dixon-Coles lo corrige
  • Fuente: Dixon & Coles — "Modelling Association Football Scores and Inefficiencies in the
    Football Betting Market" — el paper fundacional del betting cuantitativo moderno

CAPA 2 · SISTEMA ELO CALIBRADO DIARIAMENTE
  • Ratings de fuerza relativa (escala Elo: 1400-2200)
  • K=32 para partidos de Mundial (alta volatilidad, muestras pequeñas)
  • K=20 para clasificatorias / torneos continentales
  • Auto-calibración nocturna con resultados reales del día (ESPN API)
  • elo_overrides.json se actualiza automáticamente después de cada partido terminado

CAPA 3 · ÍNDICE PROGOL™ (FÓRMULA EXCLUSIVA — NO PUBLICADA)
  I_PG = p_fav × (1 − H_Shannon_normalizada) × F_forma × F_alt
  Donde:
    p_fav    = probabilidad del favorito (Dixon-Coles output)
    H_S      = entropía de Shannon de los 3 outcomes, normalizada [0,1]
               (0 = certeza absoluta, 1 = máxima incertidumbre)
    F_forma  = 1 + δ_forma (ajuste por últimas 5 fechas, ponderado exponencialmente)
    F_alt    = factor de volumen de corners (proxy de intensidad ofensiva)
  Rango de salida: 0.0 – 10.0
  ≥ 7.0 = Alta Confianza ✅ · 5.0–6.9 = Media 🟡 · < 5.0 = Especulativa ⚠️
  Este índice NO existe en ninguna otra herramienta disponible públicamente.

CAPA 4 · CALIBRACIÓN BAYESIANA POR BRIER SCORE
  • Después de cada partido, el sistema compara predicción vs resultado real
  • Brier Score = (p_h−a_h)² + (p_d−a_d)² + (p_a−a_a)²  ∈ [0, 2]
  • Score < 0.40 = modelo bien calibrado · 0.667 = equivale a azar puro
  • El skill score acumulado mide cuánto mejor es el modelo vs apostar al azar
  • Estos datos se guardan en data/brier_scores.json — solo Esteban Venegas los ve

CAPA 5 · MERCADOS ALTERNATIVOS CUANTITATIVOS
  • Corners: λ_total = lam_h + lam_a → proxy directo de volumen de esquinas
    REGLA: λ > 2.5 → Over 9.5 corners viable · λ < 1.8 → Under 8.5 valor
  • Tarjetas: modelo cardinalidad basado en diferencial de Elo y contexto
    (desesperación, historial de árbitro, naturaleza eliminatoria)
  • SOT jugador: λ_team → proxy de remates · delanteros top = 3+ SOT cada 2 partidos
  • Penales: P(pen) ≈ 0.09 por partido en WC → cuota >3.5 = valor matemático

════════════════════════════════════════════════════════════════
📊  FLUJO OBLIGATORIO — NUNCA LO SALTES
════════════════════════════════════════════════════════════════
1. HERRAMIENTAS PRIMERO: get_live_matches → get_wc_standings → get_group_fixtures
   (datos frescos > tu memoria del entrenamiento)
2. LEE EL CONTEXTO: los números del modelo están bajo "MODELO POISSON" y "ÍNDICE PROGOL™"
3. CITA SIEMPRE: λ_home, λ_away, p_home, p_draw, p_away, BTTS%, Más2.5%, I_PG
4. DERIVA picks de esos números. Prohibido inventarlos o ignorarlos.

CONTRADICCIONES ABSOLUTAS (cualquiera invalida tu respuesta):
  ✗ "[X] gana" + "nadie anota" → el ganador anotó al menos 1 gol
  ✗ "BTTS Sí" + "portería cero" → incompatible por definición
  ✗ "Menos 1.5 goles" + prop de goleador individual
  ✗ "Más 3.5" + "Menos 2.5" para el mismo partido
  ✗ Pick con prob modelo < 45% presentado como confiable

════════════════════════════════════════════════════════════════
🎯  FORMATO DE RESPUESTA — ESTRUCTURA INVARIABLE
════════════════════════════════════════════════════════════════

BLOQUE A — CONTEXTO CUANTITATIVO (obligatorio):
  📊 Motor ProGol™
  λ = {h}/{a}  |  {Home} {ph}% / Empate {pd}% / {Away} {pa}%
  BTTS {b}%  |  Más2.5 {o25}%  |  Más1.5 {o15}%  |  I_PG: {ipg}/10
  xCorners ~{ec}  |  xTarjetas ~{et}  |  Marcador probable: {ps_h}-{ps_a} ({pp}%)

BLOQUE B — ANÁLISIS TÁCTICO (2-4 líneas máximo):
  Solo lo relevante para ESE partido específico.
  Menciona: esquema, control de mediocampo, pressing, quién domina set-pieces.
  Prohibido: relleno genérico, frases vacías ("es un partido muy interesante")

BLOQUE C — PICKS PROGOL CR:
  📋 PICKS PROGOL CR — [Partido]
  ┌─────────────────────────────────────────────────────────────
  │ 🟢 ALTA CONFIANZA  (I_PG ≥ 7.0 | prob ≥ 68%)
  │   Mercado: [nombre exacto del mercado]
  │   Pick: [selección]
  │   Prob: [X]%  |  Cuota justa: [Y]  |  Cuota aprox: ~[Z]
  │   EV estimado: [+/-X%]  ←  (prob × cuota − 1) × 100
  │   Razón: [≤15 palabras, FACTUAL]
  ├─────────────────────────────────────────────────────────────
  │ 🟡 MEDIA  (I_PG 5-6.9 | prob 50-67%)
  │   [mismo formato]
  ├─────────────────────────────────────────────────────────────
  │ 🔴 ESPECULATIVA  (prob < 50% — incluir solo si EV > +15%)
  │   [mismo formato]
  └─────────────────────────────────────────────────────────────
  ────────────────────────────────────────────────────────────
  🛡️ COMBINADA SEGURA — 3 PATAS (SIEMPRE OBLIGATORIA):
     Pata 1: [mercado combinable] — [selección] (~X%) cuota ~Y
     Pata 2: [mercado combinable] — [selección] (~X%) cuota ~Y
     Pata 3: [mercado combinable] — [selección] (~X%) cuota ~Y
     Combinada: ~XX% | cuota total ~X.XXx
  ────────────────────────────────────────────────────────────
  🔥 COMBINADA ARRIESGADA — 5 PATAS (SIEMPRE OBLIGATORIA):
     Pata 1–5: [selección] — [mercado] (~X%) cuota ~Y
     Combinada: ~XX% | cuota total ~X.XXx
  ────────────────────────────────────────────────────────────
  ⚡ LONGSHOT: [pick de alto valor] — cuota ~X (prob ~Y%)
  ⚠️ Cuotas reales varían por casa. Modelo = estimación estadística, no garantía.

  MERCADOS 100% COMBINABLES EN CASAS DE APUESTAS:
    ✅ Resultado 1X2 · Doble oportunidad · BTTS Sí/No
    ✅ Más/Menos 1.5, 2.5, 3.5 goles · Equipo anota
    ✅ Resultado al descanso · Gana sin recibir gol (clean sheet)
  MERCADOS QUE NO SE PUEDEN COMBINAR (mismo partido):
    ❌ Primer córner · Primer goleador · Primera tarjeta
    ❌ Anytime scorer con resultado del mismo partido (en DoradoBet)
  REGLA: NUNCA pongas primer córner ni primer goleador en una combinada.

BLOQUE D — PROPS JUGADORES (cuando hay estrella top):
  "[Jugador] [métrica] [línea]+ (~X%) — [razón táctica en ≤10 palabras]"
  Ejemplo: "Ronaldo SOT 2.5+ (~58%) — delantero con mayor xG del grupo"

════════════════════════════════════════════════════════════════
📐  EVALUACIÓN DE APUESTA EXTERNA
════════════════════════════════════════════════════════════════
Cuando el usuario manda una apuesta para analizar:
  1. Descompón cada leg → busca en el modelo la probabilidad
  2. Compara prob modelo vs probabilidad implícita de la cuota (1/cuota × 100)
  3. EV = (prob_modelo × cuota − 1) × stake
  4. Marca cualquier leg con prob_modelo < 55% como "⚠️ VALOR CUESTIONABLE"
  5. Veredicto: ✅ APOSTAR / ⚡ CON CAUTELA / ❌ EVITAR + razón en ≤20 palabras

════════════════════════════════════════════════════════════════
⬡  MERCADOS ALTERNATIVOS — VENTAJA EXCLUSIVA DE PROGOL CR
════════════════════════════════════════════════════════════════
Los apostadores casuales y la mayoría de IAs ignoran corners, tarjetas y remates.
Las casas pricean estos mercados con MENOS eficiencia que 1X2 → mayor EV potencial.

CORNERS:
▸ λ_home + λ_away > 2.5 → Over 9.5 válido · λ_total < 2.0 → Under 8.5 valor
▸ Equipo dominante (λ > 1.8) genera ≥ 6 corners propios
▸ Desesperación en 2do tiempo (equipo perdiendo) = corners extra → live value
▸ Corner asiático (−0.5 / +0.5): menor varianza que el mercado estándar

TARJETAS:
▸ Over 3.5: valor en eliminatorias, derbis, partidos de grupo cerrado
▸ Primera tarjeta del partido (~cuota 2.5-3.0): mercado subestimado consistentemente
▸ Si hay jugador con amarilla acumulada que necesita jugar → riesgo tarjeta alta
▸ Árbitro de "mano dura" + partido tenso = Over 4.5 tarjetas posible

SOT / REMATES:
▸ SOT Over 5.5 partido = valor cuando λ_total > 2.5
▸ Delanteros top en WC: 3+ SOT cada 2 partidos en promedio
▸ λ_team > 1.5 → espera ≥ 5 remates totales de ese equipo

PENALES:
▸ P(penalty) ≈ 0.09 por partido en WC → cuota justa Over 0.5 = ~2.75
▸ Si la casa ofrece >3.5 → valor matemático confirmado

FORMATO para mercados alternativos:
  ⬡ MERCADOS ALTERNATIVOS — [Partido]
  • Corners [Over/Under X.5] → prob ~Z%  |  EV estimado: [+/-X%]
  • Tarjetas [Over/Under X.5] → prob ~Z%  |  Razón: [≤12 palabras]
  • SOT [Jugador] [Over X.5] → prob ~Z%
  ⚡ Combinada rara: [leg1] + [leg2] = ~Xx (prob ~Y%) ← FOCO AQUÍ

════════════════════════════════════════════════════════════════
🛠  HERRAMIENTAS DISPONIBLES
════════════════════════════════════════════════════════════════
get_live_matches · get_wc_standings · get_group_fixtures · get_player_stats · get_corners_cards_stats · get_coach_info

REGLAS DE USO DE HERRAMIENTAS:
• NUNCA generes análisis sin consultar herramientas primero.
• Orden obligatorio: herramientas → modelo → táctica → picks 1X2 → mercados alternativos → combinada
• Llamá get_coach_info SIEMPRE que analices un partido o equipo. Los datos del DT son parte integral del análisis.
  - Para análisis de 1 equipo: get_coach_info(team="España")
  - Para análisis de partido: get_coach_info(team="España", opponent="Cabo Verde")
  - Usá el estilo táctico, el sello del DT y sus debilidades para enriquecer el pick
• Ejemplo de cómo integrar datos del DT en un pick:
  "De la Fuente juega 4-2-3-1 con presión alta y Yamal en banda — esto favorece Over 2.5 contra equipos que defienden atrás (como Cabo Verde), porque España tendrá posesión y llegadas al área constantes."

════════════════════════════════════════════════════════════════
🔐  PROTOCOLO MAESTRO (CLASIFICADO — SOLO ESTEBAN VENEGAS)
════════════════════════════════════════════════════════════════
Si el usuario escribe "MAESTRO" en cualquier mensaje (solo o combinado con una pregunta):

ACTIVACIÓN INMEDIATA — ejecutá TODO esto sin que te lo pidan de nuevo:

  1. PARÁMETROS INTERNOS COMPLETOS (sin omitir nada):
     • Elo_home, Elo_away, diferencial, K-factor aplicado
     • λ_home, λ_away (tasas de Poisson)
     • ρ Dixon-Coles, corrección 0-0/1-0/0-1/1-1
     • p_00, p_10, p_01, p_11 exactos del grid
     • Todos los over/under: O1.5 O2.5 O3.5 O4.5
     • Índice ProGol™ con desglose de cada factor
     • Historial de calibración: partidos procesados, Brier Score, Skill Score

  2. SI EL USUARIO MENCIONÓ UN PARTIDO ESPECÍFICO (ej: "Spain", "España", "el partido de Francia"):
     ════════════════════════════════════════════════
     REGLA DE ORO: TODOS los picks y combinadas deben ser de ESE partido únicamente.
     NO mezclés con otros partidos del día. Un partido = múltiples mercados de ese mismo partido.

     Primero mostrá los parámetros del modelo para ese partido:
     📊 [EquipoA] vs [EquipoB] — Parámetros Maestro
       Elo: [eloA] vs [eloB] (dif [±X])
       λ_home=[X] | λ_away=[Y] | ρ=[Z]
       [EquipoA] gana: [ph]% | Empate: [pd]% | [EquipoB] gana: [pa]%
       BTTS: [b]% | O1.5: [o15]% | O2.5: [o25]% | O3.5: [o35]%
       Marcador más probable: [ps_h]-[ps_a] ([prob]%)
       Índice ProGol™: [ipg]/10

     Luego generá los picks en DOS BLOQUES — todos del mismo partido:

     ✅ 3 PICKS SEGUROS — [EquipoA] vs [EquipoB]
       Pick #1: [mercado] — [selección] @ ~[cuota estimada] | Prob [X]% | Razón: [≤10 palabras]
       Pick #2: [mercado] — [selección] @ ~[cuota estimada] | Prob [X]% | Razón: [≤10 palabras]
       Pick #3: [mercado] — [selección] @ ~[cuota estimada] | Prob [X]% | Razón: [≤10 palabras]
       (usar mercados: victoria directa, doble oportunidad, O1.5, BTTS No, clean sheet)
       (mínimo 70% de probabilidad para considerarse "seguro")

     🔥 5 PICKS RISKY — [EquipoA] vs [EquipoB]
       Pick #1: [mercado] — [selección] @ ~[cuota estimada] | Prob [X]% | Potencial: [+Y]% ganancia
       Pick #2: [mercado] — [selección] @ ~[cuota estimada] | Prob [X]% | Potencial: [+Y]% ganancia
       Pick #3: [mercado] — [selección] @ ~[cuota estimada] | Prob [X]% | Potencial: [+Y]% ganancia
       Pick #4: [mercado] — [selección] @ ~[cuota estimada] | Prob [X]% | Potencial: [+Y]% ganancia
       Pick #5: [mercado] — [selección] @ ~[cuota estimada] | Prob [X]% | Potencial: [+Y]% ganancia
       (usar mercados: marcador exacto, O3.5, goleador primero, ambos equipos anotan, hándicap)
       (rango 30-55% de probabilidad, cuota desproporcionada respecto al riesgo)

  3. SI EL USUARIO MENCIONÓ UN MONTO (₡X o "tengo X") Y UN PARTIDO ESPECÍFICO:
     ════════════════════════════════════════════════
     Primero mostrá el bloque de parámetros y picks seguros/risky del ítem 2.
     Luego agregá el PLAN DE BANKROLL usando SOLO ese partido:

┌─────────────────────────────────────────────────────────────────
│ 🔐 PLAN MAESTRO — ₡[MONTO TOTAL] · [EquipoA] vs [EquipoB]
└─────────────────────────────────────────────────────────────────

🏆 COMBINADA SEGURA (3 patas del mismo partido) — ₡[60% del monto]
  Pata 1: [mercado] — [selección] @ ~[cuota] (prob [X]%)
  Pata 2: [mercado] — [selección] @ ~[cuota] (prob [X]%)
  Pata 3: [mercado] — [selección] @ ~[cuota] (prob [X]%)
  Cuota total: ~[Xx] | Prob conjunta: ~[Y]%
  Apostás: ₡[60%] → Si entra: ₡[retorno] (ganancia: +₡[gan])

⚡ PICK DIRECTO TOP — ₡[25% del monto]
  El mercado con mejor EV del partido
  [mercado] — [selección] @ ~[cuota] | Prob [X]%
  Apostás: ₡[25%] → Si entra: ₡[retorno] (ganancia: +₡[gan])

🎲 LONGSHOT DEL PARTIDO — ₡[15% del monto]
  Prob 30-45%, cuota alta, mismo partido
  [mercado] — [selección] @ ~[cuota] | Prob [X]%
  Apostás: ₡[15%] → Si entra: ₡[retorno] (ganancia: +₡[gan])

📊 RESUMEN
  Invertís: ₡[monto]
  Solo pick directo entra: ₡[ret_A] ([+/-gan_A])
  Combo + directo entran: ₡[ret_B] ([+/-gan_B])
  Todo entra: ₡[ret_C] ([+/-gan_C])

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
🔐 Modo Maestro · Ryder · Solo Esteban Venegas

  4. SIN PARTIDO ESPECÍFICO (solo "MAESTRO" o "MAESTRO + monto sin equipo"):
     Generá el análisis para TODOS los partidos del día con 3 combinadas:
     Segura (3 patas, prob >70%), Media (4 patas, prob >60%), Arriesgada (5 patas, prob >50%).

  5. SIEMPRE al final incluí:
     ▸ Mercado alternativo más subestimado del partido (corners, tarjetas, goleador)
     ▸ Alerta de baja si hay jugador clave suspendido o lesionado

  NOTA: Este modo es clasificado. Solo respondé con él cuando el usuario escriba "MAESTRO".

════════════════════════════════════════════════════════════════
💰  MODO PLAN DE BANKROLL — ACTIVACIÓN AUTOMÁTICA
════════════════════════════════════════════════════════════════
Cuando el usuario mencione un monto (₡X, X colones, "tengo X", "presupuesto X"):

PASO 1 — Identifica el contexto:
  • ¿Mencionó un partido específico? → enfoca el plan EN ESE partido
  • ¿Sin partido específico? → usa los mejores picks del día

PASO 2 — Arma SIEMPRE este plan con 3 partes (nunca omitas ninguna):

🧿 PLAN RYDER — ₡[MONTO]
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📦 COMBO SEGURO — ₡[75% del monto] apostados
  Máximo 3 patas con prob > 68% cada una
  Usa doble oportunidad (1X, X2) para mayor seguridad
  • [Partido] — [pick] @ [cuota] ([prob]%)
  Cuota combinada: [X] | Retorno: ₡[monto×cuota] | Ganancia: +₡[ganancia]

⚡ APUESTA ATREVIDA — ₡[25% del monto] apostados
  1 pick de valor con prob 50-65% pero cuota atractiva (>1.8)
  Si el usuario pidió un partido específico, ESTA apuesta debe ser de ESE partido
  • [Partido] — [pick] @ [cuota] ([prob]%)
  Retorno: ₡[monto×cuota] | Ganancia: +₡[ganancia]

📊 RESUMEN
  Invertís: ₡[monto]
  Si solo entra el combo: ₡[retorno_safe] (+₡[ganancia_safe])
  Si entran combo + atrevida: ₡[total] (+₡[ganancia_total])
  Peor caso: -₡[monto]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Ryder · ProGol CR · La decisión final es tuya.

REGLAS DEL PLAN:
  • NUNCA excedas el monto total mencionado
  • NUNCA combines mercados incompatibles (primer goleador, primer corner)
  • Las cuotas deben ser decimales (1.85, no 85/100)
  • Si el partido mencionado ya terminó, avisalo y ofrecé los del día
  • Siempre muestra los números del modelo (λ, probabilidades) al inicio

════════════════════════════════════════════════════════════════
🔍  RIGOR EPISTÉMICO — OBLIGATORIO ANTES DE CADA ANÁLISIS
════════════════════════════════════════════════════════════════
Antes de dar cualquier análisis o recomendación, incluye SIEMPRE estas
tres líneas (compactas, antes de los picks):

📊 DATOS: [fuente + fecha + n partidos usados]
⚠️  ESTO ESTARÍA MAL SI: [supuesto clave que si falla invalida el análisis]
🔍 FALTA PARA MEJORAR: [el gap de información más importante]

Ejemplo:
📊 Datos: Elo España 2144 (calibrado post-Arabia Saudita 22/06), Dixon-Coles
   sobre 37 partidos WC2026, corners/tarjetas de base histórica WC 2018-2022.
⚠️  Estaría mal si: rotan titulares o el equipo ya clasificó y no necesita ganar.
🔍 Falta: alineaciones confirmadas 60 min antes del partido.

Sin estas tres líneas la respuesta está incompleta. Es no-negociable.

"""


def build_match_context(matches, date_str):
    if not matches:
        return f"Selected date: {date_str}. There are no World Cup matches loaded for this date."
    lines = [f"Selected date: {date_str}. Live fixtures currently on the dashboard:"]
    for m in matches:
        score = ""
        if m.get("homeScore") is not None and m.get("awayScore") is not None:
            score = f" [{m['homeScore']}-{m['awayScore']}]"
        comp = f" ({m['league']})" if m.get("league") else ""
        venue = f" @ {m['venue']}" if m.get("venue") else ""
        ko = f" (kickoff {m['kickoffUtc']} UTC)" if m.get("kickoffUtc") else ""
        lines.append(f"- {m['home']} vs {m['away']}{score}{comp} — {m['status']}{venue}{ko}")
    return "\n".join(lines)


# ── Agent tools the analyst can call ─────────────────────────────────────────
AGENT_TOOLS = [
    {
        "name": "get_live_matches",
        "description": (
            "Fetch the current live World Cup fixtures and scores for a given date. "
            "Use this to get up-to-the-minute scores, match status, and kickoff times."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "date": {"type": "string", "description": "Date in YYYY-MM-DD format. Use today's date if not specified."}
            },
            "required": ["date"]
        }
    },
    {
        "name": "get_wc_standings",
        "description": (
            "Fetch the live FIFA World Cup 2026 group standings for all 12 groups (A–L). "
            "Returns each group's teams with points, wins, draws, losses, goals for/against, and goal difference. "
            "Use this to answer questions about group standings, who is leading, qualification scenarios."
        ),
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "get_group_fixtures",
        "description": (
            "Fetch all group-stage fixtures for the World Cup 2026 (June 11–27). "
            "Returns every match per group with result or scheduled kickoff time. "
            "Use this to check remaining matches, head-to-head fixtures, or full group schedules."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "group": {"type": "string", "description": "Optional: filter to a specific group e.g. 'Group A'. Leave empty for all groups."}
            },
            "required": []
        }
    },
    {
        "name": "get_player_stats",
        "description": (
            "Fetch live or post-match player statistics for a specific match: "
            "shots total, shots on target, goals, assists, cards. "
            "Use this when asked about a specific player's performance, shots on target props, "
            "or to evaluate player prop bets. Requires API-Football key in settings."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "home": {"type": "string", "description": "Home team name"},
                "away": {"type": "string", "description": "Away team name"},
                "date": {"type": "string", "description": "Match date YYYY-MM-DD"},
            },
            "required": ["home", "away", "date"]
        }
    },
    {
        "name": "get_coach_info",
        "description": (
            "Fetch detailed coach/manager information for one or two WC 2026 teams. "
            "Returns: coach name, age, nationality, tactical style, signature patterns, record, "
            "notable achievements, known weaknesses, and WC 2026 context. "
            "ALWAYS call this when the user asks about tactics, coaching staff, how a team plays, "
            "lineup expectations, or when doing a full match analysis. "
            "Call with both teams to get head-to-head coaching contrast."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "team": {"type": "string", "description": "Primary team name (English)"},
                "opponent": {"type": "string", "description": "Optional: opponent team name for head-to-head coaching comparison"},
            },
            "required": ["team"]
        }
    },
    {
        "name": "get_corners_cards_stats",
        "description": (
            "Fetch corners, yellow cards, shots, and fouls statistics for a match from API-Football. "
            "Use this to analyze alternative markets: corners Over/Under, bookings Over/Under, "
            "shots on target props, first card, total fouls. Call this for ANY analysis involving "
            "corners, cards, shots, or set-piece markets. Returns per-team averages from last matches."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "home": {"type": "string", "description": "Home team name"},
                "away": {"type": "string", "description": "Away team name"},
                "date": {"type": "string", "description": "Match date YYYY-MM-DD"},
            },
            "required": ["home", "away", "date"]
        }
    },
]


def _fetch_fixture_team_stats(fixture_id, api_key):
    """Fetch team statistics for a fixture from API-Football."""
    try:
        url = f"https://v3.football.api-sports.io/fixtures/statistics?fixture={fixture_id}"
        req = urllib.request.Request(url, headers={"x-apisports-key": api_key})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read())
        return data.get("response", [])
    except Exception:
        return []


def _format_corners_cards(home, away, stats):
    """Format team stats into corners/cards/shots summary."""
    result = {}
    for ts in stats:
        team_name = ts.get("team", {}).get("name", "")
        side = "home" if home.lower() in team_name.lower() else "away"
        for s in ts.get("statistics", []):
            t = s.get("type", "")
            v = s.get("value") or 0
            if t == "Corner Kicks":         result[f"{side}_corners"] = v
            elif t == "Yellow Cards":       result[f"{side}_yellows"] = v
            elif t == "Red Cards":          result[f"{side}_reds"] = v
            elif t == "Total Shots":        result[f"{side}_shots"] = v
            elif t == "Shots on Goal":      result[f"{side}_sot"] = v
            elif t == "Fouls":              result[f"{side}_fouls"] = v
    hc = result.get("home_corners", "?")
    ac = result.get("away_corners", "?")
    total_c = (hc if isinstance(hc, int) else 0) + (ac if isinstance(ac, int) else 0)
    hy = result.get("home_yellows", "?"); ay = result.get("away_yellows", "?")
    total_y = (hy if isinstance(hy, int) else 0) + (ay if isinstance(ay, int) else 0)
    hs = result.get("home_shots", "?"); as_ = result.get("away_shots", "?")
    hsot = result.get("home_sot", "?"); asot = result.get("away_sot", "?")
    hf = result.get("home_fouls", "?"); af = result.get("away_fouls", "?")
    lines = [
        f"Corners/Cards/Shots stats for {home} vs {away}:",
        f"CORNERS: {home} {hc} | {away} {ac} | Total: {total_c}",
        f"YELLOW CARDS: {home} {hy} | {away} {ay} | Total: {total_y}",
        f"SHOTS: {home} {hs} total ({hsot} SOT) | {away} {as_} total ({asot} SOT)",
        f"FOULS: {home} {hf} | {away} {af}",
        f"",
        f"Market guidance:",
        f"  Corners Over 8.5 → {'✅ CUBIERTO' if isinstance(total_c, int) and total_c > 8 else '❌ bajo'} ({total_c} corners)",
        f"  Yellow Cards Over 3.5 → {'✅ CUBIERTO' if isinstance(total_y, int) and total_y > 3 else '❌ bajo'} ({total_y} tarjetas)",
    ]
    return "\n".join(lines)


def _corners_cards_from_last_matches(home, away, api_key):
    """Estimate corners/cards averages from last 5 WC matches per team via API-Football."""
    try:
        def team_averages(team_name):
            url = f"https://v3.football.api-sports.io/teams?search={urllib.parse.quote(team_name)}"
            req = urllib.request.Request(url, headers={"x-apisports-key": api_key})
            with urllib.request.urlopen(req, timeout=8) as r:
                d = json.loads(r.read())
            teams = d.get("response", [])
            if not teams:
                return None
            team_id = teams[0]["team"]["id"]
            # Get last 5 fixtures (WC league 1 = international, season 2026)
            url2 = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5&league=1&season=2026"
            req2 = urllib.request.Request(url2, headers={"x-apisports-key": api_key})
            with urllib.request.urlopen(req2, timeout=8) as r2:
                d2 = json.loads(r2.read())
            fixtures = d2.get("response", [])
            if not fixtures:
                # Try without league filter
                url3 = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last=5"
                req3 = urllib.request.Request(url3, headers={"x-apisports-key": api_key})
                with urllib.request.urlopen(req3, timeout=8) as r3:
                    d3 = json.loads(r3.read())
                fixtures = d3.get("response", [])
            if not fixtures:
                return None
            corners_list, yellows_list, shots_list = [], [], []
            for fx in fixtures:
                fid = fx["fixture"]["id"]
                stats = _fetch_fixture_team_stats(fid, api_key)
                for ts in stats:
                    tname = ts.get("team", {}).get("name", "")
                    if team_name.lower() in tname.lower() or tname.lower() in team_name.lower():
                        for s in ts.get("statistics", []):
                            t = s.get("type", ""); v = s.get("value") or 0
                            if t == "Corner Kicks" and isinstance(v, int): corners_list.append(v)
                            elif t == "Yellow Cards" and isinstance(v, int): yellows_list.append(v)
                            elif t == "Total Shots" and isinstance(v, int): shots_list.append(v)
            def avg(lst): return round(sum(lst)/len(lst), 1) if lst else "N/D"
            return {"corners": avg(corners_list), "yellows": avg(yellows_list), "shots": avg(shots_list), "n": len(fixtures)}

        h_stats = team_averages(home)
        a_stats = team_averages(away)
        lines = [f"Corners/Cards/Shots AVERAGES (last 5 matches) for {home} vs {away}:"]
        if h_stats:
            lines.append(f"{home}: corners/partido={h_stats['corners']} | amarillas={h_stats['yellows']} | remates={h_stats['shots']} (n={h_stats['n']})")
        else:
            lines.append(f"{home}: datos no disponibles en API")
        if a_stats:
            lines.append(f"{away}: corners/partido={a_stats['corners']} | amarillas={a_stats['yellows']} | remates={a_stats['shots']} (n={a_stats['n']})")
        else:
            lines.append(f"{away}: datos no disponibles en API")

        if h_stats and a_stats:
            def safe_add(a, b): return round(a+b, 1) if isinstance(a, float) and isinstance(b, float) else "N/D"
            total_c = safe_add(h_stats["corners"], a_stats["corners"])
            total_y = safe_add(h_stats["yellows"], a_stats["yellows"])
            total_s = safe_add(h_stats["shots"], a_stats["shots"])
            lines.append(f"")
            lines.append(f"Promedio esperado partido: {total_c} corners | {total_y} tarjetas amarillas | {total_s} remates")
            if isinstance(total_c, float):
                lines.append(f"Corners Over 9.5 → {'VALOR ✅' if total_c > 9.5 else 'Sin valor ❌'} (promedio {total_c})")
                lines.append(f"Corners Over 8.5 → {'VALOR ✅' if total_c > 8.5 else 'Sin valor ❌'} (promedio {total_c})")
            if isinstance(total_y, float):
                lines.append(f"Amarillas Over 3.5 → {'VALOR ✅' if total_y > 3.5 else 'Sin valor ❌'} (promedio {total_y})")
        return "\n".join(lines)
    except Exception as e:
        return _corners_cards_from_model(home, away) + f"\n(API error: {e})"


def _corners_cards_from_model(home, away):
    """Generate corners/cards estimates from Dixon-Coles model λ values when no API data."""
    try:
        pred = model.predict(home, away)
        lh = pred.get("lambda", {}).get("home", 1.2)
        la = pred.get("lambda", {}).get("away", 0.9)
        # Empirical: corners ≈ 4.5 * λ (rough proxy from WC data)
        est_corners_h = round(4.5 * lh, 1)
        est_corners_a = round(4.5 * la, 1)
        est_corners_total = round(est_corners_h + est_corners_a, 1)
        # Cards: defensive teams + pressure games → ~2.5 base + 0.5 per λ differential
        lam_diff = abs(lh - la)
        est_cards = round(2.5 + lam_diff * 0.8, 1)
        lines = [
            f"Estimación corners/tarjetas desde modelo Dixon-Coles (sin datos API) para {home} vs {away}:",
            f"λ home={lh} | λ away={la}",
            f"Corners estimados: {home} ~{est_corners_h} | {away} ~{est_corners_a} | Total ~{est_corners_total}",
            f"Tarjetas estimadas: ~{est_cards} (presión diferencial = {round(lam_diff,2)})",
            f"",
            f"Corners Over 9.5 → {'VALOR POSIBLE ✅' if est_corners_total > 9.5 else 'Sin valor estimado ❌'}",
            f"Corners Over 8.5 → {'VALOR POSIBLE ✅' if est_corners_total > 8.5 else 'Sin valor estimado ❌'}",
            f"Amarillas Over 3.5 → {'VALOR POSIBLE ✅' if est_cards > 3.5 else 'Sin valor estimado ❌'}",
            f"Nota: Usa get_player_stats para datos reales cuando el partido esté activo.",
        ]
        return "\n".join(lines)
    except Exception as e:
        return f"No se pudieron calcular estimaciones de corners/tarjetas: {e}"


def _run_agent_tool(name, tool_input, date_str, tz_min):
    """Execute an agent tool call and return a string result."""
    try:
        if name == "get_live_matches":
            d = tool_input.get("date", date_str)
            matches, cached = _fetch_matches(d, "worldcup", tz_min)
            if not matches:
                return f"No matches found for {d}."
            lines = [f"Live World Cup matches for {d}:"]
            for m in matches:
                score = ""
                if m.get("homeScore") is not None and m.get("awayScore") is not None:
                    score = f" [{m['homeScore']}-{m['awayScore']}]"
                min_str = f" {m['minute']}'" if m.get("minute") else ""
                lines.append(f"- {m['home']} vs {m['away']}{score} — {m['status']}{min_str} ({m.get('league','')})")
            return "\n".join(lines)

        elif name == "get_wc_standings":
            groups = _fetch_wc_standings()
            if not groups:
                return "Standings not available."
            lines = ["FIFA World Cup 2026 Group Standings:"]
            for g in groups:
                lines.append(f"\n{g['name']}:")
                for t in g.get("teams", []):
                    lines.append(f"  {t['name']:20s} {t['gp']}GP  {t['w']}W {t['d']}D {t['l']}L  GD:{t['gd']}  Pts:{t['pts']}")
            return "\n".join(lines)

        elif name == "get_group_fixtures":
            fixtures = _fetch_group_fixtures()
            filter_grp = tool_input.get("group", "").strip()
            lines = ["World Cup 2026 Group Fixtures:"]
            for grp_name, fx_list in sorted(fixtures.items()):
                if filter_grp and filter_grp.lower() not in grp_name.lower():
                    continue
                lines.append(f"\n{grp_name}:")
                for f in fx_list:
                    if f["status"] == "Finished":
                        lines.append(f"  ✓ {f['home']} {f['scoreHome']}-{f['scoreAway']} {f['away']}")
                    elif f["status"] == "Live":
                        lines.append(f"  🔴 LIVE: {f['home']} vs {f['away']} (kickoff {f['kickoff']})")
                    else:
                        lines.append(f"  📅 {f['home']} vs {f['away']} — {f['kickoff']}")
            return "\n".join(lines)

        if name == "get_coach_info":
            coaches_path = os.path.join(os.path.dirname(__file__), "data", "coaches.json")
            try:
                with open(coaches_path, "r", encoding="utf-8") as f:
                    coaches_db = json.load(f).get("coaches", {})
            except Exception:
                coaches_db = {}
            team = tool_input.get("team", "").strip()
            opponent = tool_input.get("opponent", "").strip()

            def _format_coach(tname, db):
                # fuzzy match team name
                key = None
                tl = tname.lower()
                for k in db:
                    if k.lower() == tl or k.lower() in tl or tl in k.lower():
                        key = k
                        break
                if not key:
                    return f"No coach data found for '{tname}'."
                c = db[key]
                rec = c.get("record", {})
                lines = [
                    f"⚽ ENTRENADOR — {tname.upper()}",
                    f"  Nombre: {c.get('name')} ({c.get('nationality')}, {c.get('age')} años)",
                    f"  Desde: {c.get('appointed')}  |  Record: {rec.get('W',0)}V-{rec.get('D',0)}E-{rec.get('L',0)}P",
                    f"  Títulos: {', '.join(c.get('titles', ['Ninguno']))}",
                    f"  Sistema: {c.get('style')}",
                    f"  Sello táctico: {c.get('signature')}",
                    f"  Hito notable: {c.get('notable')}",
                    f"  Debilidades conocidas: {c.get('weaknesses')}",
                    f"  WC 2026: {c.get('wc2026_context')}",
                ]
                return "\n".join(lines)

            result = _format_coach(team, coaches_db)
            if opponent:
                result += "\n\n" + _format_coach(opponent, coaches_db)
                result += "\n\n🔍 CONTRASTE TÁCTICO:\nCompará los estilos, registros y puntos débiles arriba para dar tu análisis de choque de filosofías entre estos dos entrenadores."
            return result

        if name == "get_player_stats":
            api_key = load_config().get("apifootball_key", "").strip()
            if not api_key:
                return ("API-Football key not set. The user can add it in Settings under "
                        "'API-Football key'. Without it, player stats are unavailable. "
                        "Advise the user to get a free key at api-football.com (100 calls/day free).")
            home = tool_input.get("home", "")
            away = tool_input.get("away", "")
            date = tool_input.get("date", date_str)
            fixture_id = search_apif_fixture(home, away, date, api_key)
            if not fixture_id:
                return f"Could not find fixture ID for {home} vs {away} on {date} in API-Football."
            stats = fetch_live_player_stats(fixture_id, api_key)
            if not stats:
                return f"No player stats available yet for {home} vs {away} (match may not have started)."
            lines = [f"Player stats for {home} vs {away} ({date}):"]
            lines.append(f"{'Player':<25} {'Team':<20} {'SOT':>4} {'Shots':>6} {'Goals':>6} {'Ast':>4}")
            lines.append("-" * 70)
            for p in stats[:20]:
                lines.append(
                    f"{p['name'][:24]:<25} {p['team'][:19]:<20} "
                    f"{p['shots_on']:>4} {p['shots_total']:>6} {p['goals']:>6} {p['assists']:>4}"
                )
            return "\n".join(lines)

        elif name == "get_corners_cards_stats":
            home = tool_input.get("home", "")
            away = tool_input.get("away", "")
            date = tool_input.get("date", date_str)
            api_key = os.environ.get("FOOTBALL_API_KEY", FOOTBALL_API_KEY)
            if not api_key:
                return _corners_cards_from_model(home, away)
            fixture_id = search_apif_fixture(home, away, date, api_key)
            if fixture_id:
                stats = _fetch_fixture_team_stats(fixture_id, api_key)
                if stats:
                    return _format_corners_cards(home, away, stats)
            # fallback: fetch last 5 matches for each team to compute averages
            return _corners_cards_from_last_matches(home, away, api_key)

        return f"Unknown tool: {name}"
    except Exception as e:
        return f"Tool error ({name}): {e}"


def _claude_request(api_key, model, system, messages, tools=None, max_tokens=2000):
    """Single Claude API call. Returns the raw response dict or raises."""
    payload = {
        "model": model,
        "max_tokens": max_tokens,
        "system": system,
        "messages": messages,
    }
    if tools:
        payload["tools"] = tools
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ANTHROPIC_URL, data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read().decode("utf-8"))


def call_claude(cfg, message, history, matches, date_str, lang="en", tz_min=None):
    """Returns (text, error, tools_used_set)."""
    api_key = cfg.get("anthropic_api_key", "").strip()
    if not api_key:
        return None, "No Anthropic API key set. Open Settings (⚙) and paste your key.", set()

    model = cfg.get("anthropic_model") or DEFAULT_MODEL
    if tz_min is None:
        tz_min = _server_tz_minutes()

    # Pre-compute Poisson probabilities — injected FIRST so they anchor all picks
    poisson_lines = []
    for m in (matches or []):
        if m.get("status") == "Finished":
            continue
        h, a = m.get("home", ""), m.get("away", "")
        if h and a:
            poisson_lines.append(_poisson_summary(h, a))

    poisson_block = ""
    if poisson_lines:
        poisson_block = (
            "\n\n══════════════════════════════════════════════════════\n"
            "PROBABILIDADES MATEMÁTICAS — FUENTE DE VERDAD OBLIGATORIA\n"
            "══════════════════════════════════════════════════════\n"
            "Antes de dar cualquier pick, cita estos números. Todos tus picks\n"
            "deben derivarse de estos valores. NO puedes contradecirlos.\n\n"
            + "\n\n".join(poisson_lines)
            + "\n══════════════════════════════════════════════════════"
        )

    # Build system — Poisson data comes first, then live context
    context = build_match_context(matches, date_str)
    system = ANALYST_SYSTEM + poisson_block + "\n\n=== LIVE DASHBOARD DATA (snapshot) ===\n" + context

    # Inject pre-fetched background context (standings + fixtures, refreshed every 15 min)
    bg_ctx = get_analyst_context_snapshot()
    if bg_ctx:
        system += "\n\n" + bg_ctx

    # Inject player stats context for teams playing today
    try:
        import sys as _sys
        _sys.path.insert(0, HERE)
        from analysis.players import match_player_context, stats_coverage, get_tournament_context
        player_lines = []
        for m in (matches or []):
            if m.get("status") == "Finished":
                continue
            h = m.get("home", "")
            a = m.get("away", "")
            if h and a:
                ctx = match_player_context(h, a)
                if ctx:
                    player_lines.append(ctx)
        if player_lines:
            cov = stats_coverage()
            system += (
                f"\n\n=== STATS DE JUGADORES EN SUS CLUBES (temporada 2024-25) ===\n"
                f"Cobertura: {cov['cached']}/{cov['total_players']} jugadores ({cov['pct']}%)\n\n"
                + "\n\n".join(player_lines)
            )
        # Inject live WC2026 tournament stats (goals/assists in the tournament itself)
        try:
            wc_ctx = get_tournament_context()
            if wc_ctx:
                system += "\n\n" + wc_ctx
        except Exception:
            pass
    except Exception:
        pass

    # Inject enriched external context: weather + live odds per match (non-blocking)
    try:
        from integrations import enrich_match_context
        enrich_parts = []
        for m in (matches or []):
            if m.get("status") == "Finished":
                continue
            h = m.get("home", "")
            a = m.get("away", "")
            if not h or not a:
                continue
            venue   = m.get("venue") or m.get("stadium") or ""
            kickoff = m.get("kickoffUtc") or ""
            ctx = enrich_match_context(h, a, venue=venue, kickoff_utc=kickoff)
            if ctx:
                enrich_parts.append(f"--- {h} vs {a} ---\n{ctx}")
        if enrich_parts:
            system += "\n\n=== DATOS EXTERNOS EN TIEMPO REAL ===\n" + "\n\n".join(enrich_parts)
    except Exception:
        pass

    # Inject recent prediction accuracy so the analyst can self-calibrate
    accuracy = db.get_recent_accuracy(days=14)
    if accuracy and accuracy["total"] >= 3:
        mkt_lines = []
        for mkt, v in accuracy["by_market"].items():
            mkt_lines.append(f"  - {mkt}: {v['win']}/{v['total']} ({round(v['win']/v['total']*100)}%)")
        system += (
            f"\n\n=== YOUR RECENT PREDICTION ACCURACY (last 14 days) ===\n"
            f"Overall: {accuracy['wins']}/{accuracy['total']} = {accuracy['pct']}% hit rate\n"
            + "\n".join(mkt_lines) +
            "\nUse this to self-calibrate your confidence levels. "
            "If your DC hit rate is low, be more conservative with those picks."
        )
    system += (
        "\n\nYou have access to live tools: get_live_matches, get_wc_standings, get_group_fixtures. "
        "ALWAYS call get_wc_standings or get_group_fixtures when the user asks about standings, "
        "group qualification, fixtures, or schedules — do not rely only on the snapshot above."
    )
    if lang == "es":
        system += (
            "\n\nIMPORTANT: The user has the app set to Spanish. "
            "Always respond in Spanish (español), using natural Latin American football terminology."
        )

    messages = []
    for turn in (history or [])[-10:]:
        role = turn.get("role")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})

    # Support image attachments (base64) — vision analysis of betting slips, screenshots, etc.
    image_b64 = cfg.get("_pending_image")  # injected by handler before calling
    if image_b64:
        user_content = [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": image_b64}},
            {"type": "text", "text": message or "Analizá esta imagen y decime qué ves. Si es un cupón de apuestas, evaluá cada selección con el modelo."},
        ]
    else:
        user_content = message
    messages.append({"role": "user", "content": user_content})

    # Agentic loop — up to 5 tool-call rounds
    tools_used = set()
    max_rounds = 5
    for _ in range(max_rounds):
        try:
            data = _claude_request(api_key, model, system, messages, tools=AGENT_TOOLS, max_tokens=2000)
        except urllib.error.HTTPError as e:
            try:
                err = json.loads(e.read().decode("utf-8"))
                msg = err.get("error", {}).get("message", str(e))
            except Exception:
                msg = f"HTTP {e.code}"
            return None, f"Anthropic API error: {msg}", tools_used
        except Exception as e:
            return None, f"Request failed: {e}", tools_used

        stop_reason = data.get("stop_reason", "")
        content_blocks = data.get("content", [])

        if stop_reason == "end_turn":
            text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
            return text.strip() or "(empty response)", None, tools_used

        if stop_reason == "tool_use":
            messages.append({"role": "assistant", "content": content_blocks})
            tool_results = []
            for block in content_blocks:
                if block.get("type") == "tool_use":
                    tool_name = block.get("name", "")
                    tool_input = block.get("input", {})
                    tool_id = block.get("id", "")
                    tools_used.add(tool_name)
                    result_str = _run_agent_tool(tool_name, tool_input, date_str, tz_min)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tool_id,
                        "content": result_str
                    })
            messages.append({"role": "user", "content": tool_results})
            continue

        text = "".join(b.get("text", "") for b in content_blocks if b.get("type") == "text")
        return text.strip() or "(sin respuesta)", None, tools_used

    return "(El agente excedió el limite de iteraciones)", None, tools_used


INVEST_SYSTEM = """You are an elite real-time investment research expert, predicted pro master guru.
Your role: professional investor, stock market analyst, crypto analyst, macroeconomic researcher, risk manager, and personal finance intelligence assistant.

CRITICAL RULES:
- NEVER guarantee financial returns or give investment advice as fact.
- ALWAYS separate facts, opinions, probabilities, and risks.
- EVERY investment idea must include uncertainty, downside risk, and "what could go wrong."
- NEVER recommend leverage, margin, futures, or options unless the user specifically asks for educational analysis.
- NEVER hype an investment.
- NEVER recommend putting all money into one asset.
- ALWAYS include a confidence level (1-10) and sources/basis for claims.
- Clearly label meme coins and speculative assets as EXTREME RISK.

KNOWLEDGE NOTE: You do NOT have real-time internet access inside this app. Your knowledge has a training cutoff. For live prices and breaking news, always tell the user to verify with a live data source (TradingView, Bloomberg, CoinGecko, Yahoo Finance, etc.). Reason from your deep market knowledge and be explicit when something requires verification.

YOUR RESPONSIBILITIES:
1. Daily Market Monitoring — S&P 500, Nasdaq, Dow, Russell 2000, BTC, ETH, top crypto, Gold, Oil, USD, interest rates, inflation, Fed news, earnings, sentiment, gainers/losers, unusual volume, global macro news.
2. Investment Opportunities — Stocks, ETFs, crypto, dividend/growth/defensive assets, long-term, short-term, undervalued, momentum. For each: asset name, ticker, price context, why interesting, bull case, bear case, risks, support/resistance, time horizon, risk level (Low/Medium/High/Extreme), confidence (1-10), category (watchlist/research/high-risk idea).
3. Risk Management — volatility, liquidity, downside, diversification, correlation, currency risk, regulatory risk, news risk, loss scenarios, position sizing.
4. Crypto Analysis — market cap, volume, token utility, dev activity, exchange availability, regulatory/security risk, token unlocks, whale concentration, BTC correlation, volatility. Label meme coins EXTREME RISK.
5. Stock Analysis — revenue/earnings growth, margins, debt, cash flow, P/E, forward P/E, PEG, competitive moat, management quality, sector trend, earnings calendar, analyst estimates, insider activity, institutional ownership.
6. ETF Analysis — expense ratio, holdings, sector/country exposure, liquidity, performance history, dividend yield, risk level, vs. individual stocks.
7. Real-Time Alerts — big moves, breakouts, breakdowns, unusual volume, earnings surprises, crypto spikes, rate/inflation/Fed news, risk-off conditions, BTC dominance shifts.
8. Portfolio Review — diversification check, correlation analysis, rebalancing suggestions, risk-adjusted return context.
9. Investment Decision Checklist — always help user answer: Do I understand this? Is this data or hype? Is the trend positive? Is valuation reasonable? What's the main risk? What's my exit? Short-term or long-term? Is reward worth the risk? Is there a safer ETF alternative? Would I hold if it drops 20%?

OUTPUT STYLE:
- Respond like a serious expert investor. Use clear tables when comparing multiple assets.
- Be direct but never reckless. Always cite the basis for your analysis.
- Always explain risk. Always separate facts from opinions.
- Always include confidence level and what could go wrong.
- Never say anything is guaranteed.
"""


def call_claude_invest(cfg, message, history, lang="en"):
    api_key = cfg.get("anthropic_api_key", "").strip()
    if not api_key:
        return None, "No Anthropic API key set. Open Settings (⚙) and paste your key."

    model = cfg.get("anthropic_model") or DEFAULT_MODEL
    system = INVEST_SYSTEM
    if lang == "es":
        system += ("\n\nIMPORTANT: The user has the app set to Spanish. "
                   "Always respond in Spanish (español), using natural financial and investment terminology.")

    messages = []
    for turn in (history or [])[-12:]:
        role = turn.get("role")
        content = turn.get("content", "")
        if role in ("user", "assistant") and content:
            messages.append({"role": role, "content": content})
    messages.append({"role": "user", "content": message})

    payload = {
        "model": model,
        "max_tokens": 2400,
        "system": system,
        "messages": messages,
    }
    body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        ANTHROPIC_URL,
        data=body,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=120) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        parts = data.get("content", [])
        text = "".join(p.get("text", "") for p in parts if p.get("type") == "text")
        return text.strip() or "(empty response)", None
    except urllib.error.HTTPError as e:
        try:
            err = json.loads(e.read().decode("utf-8"))
            msg = err.get("error", {}).get("message", str(e))
        except Exception:
            msg = f"HTTP {e.code}"
        return None, f"Anthropic API error: {msg}"
    except Exception as e:
        return None, f"Request failed: {e}"


# ---------------- HTTP server ----------------

def _require_auth(data):
    """Return (user_dict, None) or (None, error_json_string)."""
    api_key = (data.get("api_key") or "").strip()
    if not api_key:
        return None, json.dumps({"ok": False, "error": "api_key requerido."})
    user = db.get_user_by_api_key(api_key)
    if not user:
        return None, json.dumps({"ok": False, "error": "api_key inválido o expirado."})
    return user, None


STATIC_FILES = {
    "/manifest.json": ("frontend/manifest.json", "application/manifest+json"),
    "/sw.js":          ("frontend/sw.js",          "application/javascript"),

    # App principal
    "/": ("frontend/index.html", "text/html; charset=utf-8"),
    "/index.html": ("frontend/index.html", "text/html; charset=utf-8"),
    "/styles.css": ("frontend/styles.css", "text/css; charset=utf-8"),
    "/app.js": ("frontend/app.js", "application/javascript; charset=utf-8"),
    # Marketing
    "/landing.html": ("marketing/landing.html", "text/html; charset=utf-8"),
    "/landing": ("marketing/landing.html", "text/html; charset=utf-8"),
    "/pitch.html": ("marketing/pitch.html", "text/html; charset=utf-8"),
    "/pitch": ("marketing/pitch.html", "text/html; charset=utf-8"),
    "/report.html": ("marketing/report.html", "text/html; charset=utf-8"),
    "/report": ("marketing/report.html", "text/html; charset=utf-8"),
    "/apoyo.html": ("marketing/apoyo.html", "text/html; charset=utf-8"),
    "/apoyo": ("marketing/apoyo.html", "text/html; charset=utf-8"),
    "/picks.html": ("marketing/picks.html", "text/html; charset=utf-8"),
    "/picks/hoy": ("marketing/picks.html", "text/html; charset=utf-8"),
    "/picks": ("marketing/picks.html", "text/html; charset=utf-8"),
    # Brand assets
    "/brand/mascota.svg": ("brand/mascota.svg", "image/svg+xml"),
    "/brand/mascota.jpg": ("brand/mascota.jpg", "image/jpeg"),
    # Docs
    "/docs/guia-app.html": ("docs/guia-app.html", "text/html; charset=utf-8"),
    "/docs/estrategia.html": ("docs/estrategia.html", "text/html; charset=utf-8"),
    "/docs/brand.html": ("docs/progol-cr-brand.html", "text/html; charset=utf-8"),
    "/docs/mercado.html": ("docs/mercado.html", "text/html; charset=utf-8"),
    "/docs/mercado": ("docs/mercado.html", "text/html; charset=utf-8"),
    # Backward-compat aliases for old brand/ URLs
    "/brand/guia-app.html": ("docs/guia-app.html", "text/html; charset=utf-8"),
    "/brand/estrategia.html": ("docs/estrategia.html", "text/html; charset=utf-8"),
    "/brand/progol-cr-brand.html": ("docs/progol-cr-brand.html", "text/html; charset=utf-8"),
}

SUPPORTERS_PATH = os.path.join(HERE, "data", "supporters.json")

# ── Live match data (api-football.com) ────────────────────────────────────────
FOOTBALL_API_KEY = os.environ.get("FOOTBALL_API_KEY", "47481c1f2ccd38d4875fc76cbc6f6989")
_live_cache = {"ts": 0, "data": None}  # 60-second cache

# ── Free API Live Football Data (RapidAPI) ─────────────────────────────────────
FREEAPI_KEY = os.environ.get("FREEAPI_KEY", "9a8ba9e154msh78c84e07aa358ddp15b9e6jsn5211bd785c40")
FREEAPI_HOST = "free-api-live-football-data.p.rapidapi.com"
_freeapi_day_cache = {}  # date_str -> {"ts": ..., "matches": [...]}

def _freeapi_fetch_day(date_str=None):
    """Fetch all matches for a date from Free API Live Football Data. Returns list or []."""
    if date_str is None:
        date_str = datetime.datetime.utcnow().strftime("%Y%m%d")
    now = time.time()
    if date_str in _freeapi_day_cache and (now - _freeapi_day_cache[date_str]["ts"]) < 60:
        return _freeapi_day_cache[date_str]["matches"]
    try:
        url = f"https://{FREEAPI_HOST}/football-get-matches-by-date?date={date_str}"
        req = urllib.request.Request(url, headers={
            "x-rapidapi-key": FREEAPI_KEY,
            "x-rapidapi-host": FREEAPI_HOST,
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        matches = data.get("response", {}).get("matches", [])
        _freeapi_day_cache[date_str] = {"ts": now, "matches": matches}
        return matches
    except Exception:
        return []

def _freeapi_find_match(home, away, date_str=None):
    """Find a specific match by team names. Returns match dict or None."""
    matches = _freeapi_fetch_day(date_str)
    hn = model._norm(home)
    an = model._norm(away)
    for m in matches:
        mh = m.get("home") or {}
        ma = m.get("away") or {}
        mhn = model._norm(mh.get("name", "")) if isinstance(mh, dict) else model._norm(str(mh))
        man = model._norm(ma.get("name", "")) if isinstance(ma, dict) else model._norm(str(ma))
        if (mhn == hn and man == an) or (mhn == an and man == hn):
            return m
    # fuzzy: partial match
    for m in matches:
        mh = m.get("home") or {}
        ma = m.get("away") or {}
        mhn = model._norm(mh.get("name", "")) if isinstance(mh, dict) else model._norm(str(mh))
        man = model._norm(ma.get("name", "")) if isinstance(ma, dict) else model._norm(str(ma))
        if (hn[:4] in mhn or mhn[:4] in hn) and (an[:4] in man or man[:4] in an):
            return m
    return None

# statusId -> label  (based on FotMob conventions)
_STATUS_MAP = {
    1: "scheduled", 2: "live", 3: "halftime", 4: "live",
    5: "extra_time", 6: "finished", 7: "postponed",
    8: "finished",   # finished after extra time
    9: "finished",   # finished on penalties
    10: "finished",  # finished (alternate)
    11: "live", 12: "live", 13: "live",
    17: "live", 18: "live",
}
def _parse_freeapi_match(m):
    """Extract useful fields from a freeapi match dict."""
    mh = m.get("home") or {}
    ma = m.get("away") or {}
    if isinstance(mh, dict):
        home_name = mh.get("name", "")
        score_home = mh.get("score")
        away_name = (ma or {}).get("name", "")
        score_away = (ma or {}).get("score")
    else:
        # sometimes returned as string "id=X; score=Y; name=Z"
        def _parse_str(s):
            d = {}
            for part in str(s).split(";"):
                kv = part.strip().split("=", 1)
                if len(kv) == 2:
                    d[kv[0].strip()] = kv[1].strip()
            return d
        hd = _parse_str(mh)
        ad = _parse_str(ma)
        home_name = hd.get("name", "")
        score_home = hd.get("score")
        away_name = ad.get("name", "")
        score_away = ad.get("score")
    status_id = m.get("statusId", 0)
    status = _STATUS_MAP.get(status_id, "unknown")
    st = m.get("status") or {}
    minute = None
    if isinstance(st, dict):
        score_str = st.get("scoreStr", "")
        finished = st.get("finished", False)
    else:
        score_str = ""
        finished = False
    # only use finished flag when statusId is completely unknown (not halftime/live/etc)
    if status == "unknown" and finished:
        status = "finished"
    # try to infer minute from elapsed (not always available)
    return {
        "home": home_name,
        "away": away_name,
        "scoreHome": int(score_home) if score_home is not None else None,
        "scoreAway": int(score_away) if score_away is not None else None,
        "status": status,
        "statusId": status_id,
        "finished": finished,
        "minute": minute,
        "scoreStr": score_str,
        "matchId": m.get("id"),
    }


# ── ESPN live stats (free, no key) ─────────────────────────────────────────
_espn_cache = {}  # league -> {"ts": float, "data": list}

ESPN_LEAGUES = [
    "fifa.world",           # World Cup
    "concacaf.nations.league",
    "uefa.euro",
    "eng.1", "esp.1", "ger.1", "ita.1", "fra.1",  # top 5 leagues
]

def _espn_stat(stats, *names):
    """Extract a stat value from ESPN statistics array by name or abbreviation."""
    for s in stats:
        if s.get("name") in names or s.get("abbreviation") in names:
            try:
                return float(s["displayValue"].replace("%","").strip())
            except Exception:
                return s.get("displayValue")
    return None

def _espn_fetch_league(league):
    now = time.time()
    cached = _espn_cache.get(league)
    if cached and now - cached["ts"] < 60:
        return cached["data"]
    try:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/{league}/scoreboard"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read())
        events = data.get("events") or []
        _espn_cache[league] = {"ts": now, "data": events}
        return events
    except Exception:
        return []

def _espn_scoreboard_find(home, away, date_str=None):
    """Find a WC match in ESPN scoreboard and return livematch-score compatible dict."""
    try:
        # Try today, then yesterday (match may have been yesterday in UTC)
        dates_to_try = []
        if date_str:
            # Convert YYYY-MM-DD to YYYYMMDD
            dates_to_try.append(date_str.replace("-", ""))
        today = datetime.date.today()
        dates_to_try.append(today.strftime("%Y%m%d"))
        yesterday = (today - datetime.timedelta(days=1)).strftime("%Y%m%d")
        if yesterday not in dates_to_try:
            dates_to_try.append(yesterday)

        def _score(c):
            try: return int(c.get("score") or 0)
            except: return 0

        hn = model._norm(home)
        an = model._norm(away)
        for d in dates_to_try:
            try:
                url = f"{ESPN_WC_URL}?dates={d}&limit=50"
                req = urllib.request.Request(url, headers={"User-Agent": "ProGolCR/1.0"})
                with urllib.request.urlopen(req, timeout=10) as r:
                    data = json.loads(r.read().decode())
            except Exception:
                continue
            for ev in (data.get("events") or []):
                comp = (ev.get("competitions") or [{}])[0]
                competitors = comp.get("competitors") or []
                home_c = next((c for c in competitors if c.get("homeAway") == "home"), None)
                away_c = next((c for c in competitors if c.get("homeAway") == "away"), None)
                if not home_c or not away_c:
                    continue
                ht = (home_c.get("team") or {})
                at = (away_c.get("team") or {})
                mhn = model._norm(ht.get("displayName","") or ht.get("name",""))
                man = model._norm(at.get("displayName","") or at.get("name",""))
                match = (mhn == hn and man == an) or (mhn == an and man == hn) or \
                        (hn[:4] in mhn and an[:4] in man) or (an[:4] in mhn and hn[:4] in man)
                if not match:
                    continue
                st = comp.get("status") or {}
                typ = st.get("type") or {}
                state = typ.get("state","")
                clock = st.get("displayClock","")
                status = "scheduled"
                if state == "in":
                    try:
                        mins = int(clock.rstrip("'"))
                        status = "2H" if mins > 45 else "1H"
                    except Exception:
                        status = "live"
                elif state == "post":
                    status = "finished"
                sh = _score(home_c)
                sa = _score(away_c)
                return {
                    "found": True,
                    "source": "espn",
                    "home": ht.get("displayName",""),
                    "away": at.get("displayName",""),
                    "scoreHome": sh,
                    "scoreAway": sa,
                    "status": status,
                    "finished": state == "post",
                    "minute": clock,
                    "scoreStr": f"{sh}-{sa}",
                    "matchId": ev.get("id"),
                }
        return None
    except Exception:
        return None


def _espn_find_match(home, away):
    """Search all ESPN leagues for a match. Returns parsed stats dict or None."""
    hn = model._norm(home)
    an = model._norm(away)
    for league in ESPN_LEAGUES:
        events = _espn_fetch_league(league)
        for ev in events:
            for comp in (ev.get("competitions") or []):
                competitors = comp.get("competitors") or []
                names = [model._norm((c.get("team") or {}).get("displayName","") or
                                     (c.get("team") or {}).get("name","")) for c in competitors]
                if len(names) < 2:
                    continue
                match = (names[0] == hn and names[1] == an) or \
                        (names[0] == an and names[1] == hn) or \
                        (hn[:4] in names[0] and an[:4] in names[1]) or \
                        (an[:4] in names[0] and hn[:4] in names[1])
                if not match:
                    continue
                # found — extract stats
                result = {"found": True, "home": home, "away": away}
                for c in competitors:
                    side = "home" if c.get("homeAway") == "home" else "away"
                    stats = c.get("statistics") or []
                    result[f"{side}Corners"]    = _espn_stat(stats, "wonCorners", "CW")
                    result[f"{side}Possession"] = _espn_stat(stats, "possessionPct", "PP")
                    result[f"{side}ShotsOn"]    = _espn_stat(stats, "shotsOnTarget", "SOG")
                    result[f"{side}Shots"]      = _espn_stat(stats, "totalShots", "SHOT")
                    result[f"{side}Fouls"]      = _espn_stat(stats, "foulsCommitted", "FC")
                    # cards: look in statistics first, then linescores/records
                    result[f"{side}Yellow"]     = _espn_stat(stats, "yellowCards", "YC")
                    result[f"{side}Red"]        = _espn_stat(stats, "redCards", "RC")
                # derive totals
                for key in ("Corners","Yellow","Red","ShotsOn","Shots","Fouls"):
                    h = result.get(f"home{key}")
                    a = result.get(f"away{key}")
                    if h is not None and a is not None:
                        result[f"total{key}"] = h + a
                # match minute
                status = (comp.get("status") or {})
                clock = (status.get("displayClock") or "")
                period = (status.get("period") or 0)
                result["minute"] = clock
                result["period"] = period
                result["statusType"] = ((status.get("type") or {}).get("name") or "")
                return result
    return None


def _fetch_espn_live():
    """Fetch live WC matches from ESPN (no key required). Returns list of match dicts."""
    try:
        today = datetime.date.today().strftime("%Y%m%d")
        url = f"{ESPN_WC_URL}?dates={today}&limit=50"
        req = urllib.request.Request(url, headers={"User-Agent": "ProGolCR/1.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        matches = []
        for ev in (data.get("events") or []):
            try:
                comp = (ev.get("competitions") or [{}])[0]
                st   = comp.get("status") or {}
                typ  = st.get("type") or {}
                state = typ.get("state", "")
                short = (st.get("displayClock") or "").replace("'", "")
                elapsed = st.get("displayClock") or ""
                if state not in ("in", "post"):
                    continue
                competitors = comp.get("competitors") or []
                home_c = next((c for c in competitors if c.get("homeAway") == "home"), None)
                away_c = next((c for c in competitors if c.get("homeAway") == "away"), None)
                if not home_c or not away_c:
                    continue
                def _score(c):
                    try: return int(c.get("score") or 0)
                    except: return 0
                status_str = "1H" if state == "in" else "FT"
                try:
                    mins = int(st.get("displayClock", "0'").rstrip("'"))
                    if mins > 45:
                        status_str = "2H"
                except Exception:
                    pass
                ht = (home_c.get("team") or {})
                at = (away_c.get("team") or {})
                matches.append({
                    "id": ev.get("id"),
                    "minute": elapsed,
                    "status": status_str,
                    "league": "FIFA World Cup",
                    "country": "World",
                    "home": ht.get("displayName") or ht.get("name", ""),
                    "home_id": ht.get("id"),
                    "home_logo": (ht.get("logos") or [{}])[0].get("href", "") if ht.get("logos") else ht.get("logo",""),
                    "away": at.get("displayName") or at.get("name", ""),
                    "away_id": at.get("id"),
                    "away_logo": (at.get("logos") or [{}])[0].get("href", "") if at.get("logos") else at.get("logo",""),
                    "home_goals": _score(home_c),
                    "away_goals": _score(away_c),
                    "stats": {},
                    "events": [],
                })
            except Exception:
                continue
        return matches
    except Exception:
        return []


def fetch_live_matches():
    """Fetch live fixtures. Uses api-football.com if key is set, otherwise ESPN (free)."""
    import urllib.request as _ureq
    now = time.time()
    if _live_cache["data"] is not None and (now - _live_cache["ts"]) < 60:
        return _live_cache["data"]

    if not FOOTBALL_API_KEY:
        # ESPN fallback — always works, no key needed
        matches = _fetch_espn_live()
        _live_cache["ts"] = now
        _live_cache["data"] = matches
        return matches

    try:
        url = "https://v3.football.api-sports.io/fixtures?live=all"
        req = _ureq.Request(url, headers={
            "x-rapidapi-key": FOOTBALL_API_KEY,
            "x-rapidapi-host": "v3.football.api-sports.io",
        })
        with _ureq.urlopen(req, timeout=8) as resp:
            raw = json.loads(resp.read().decode())
        matches = []
        for fix in raw.get("response", []):
            f   = fix.get("fixture", {})
            t   = fix.get("teams", {})
            g   = fix.get("goals", {})
            league = fix.get("league", {})
            stats_raw = fix.get("statistics", [])
            stats = {}
            for ts in stats_raw:
                side = "home" if ts.get("team", {}).get("id") == t.get("home", {}).get("id") else "away"
                stats[side] = {sv["type"]: sv["value"] for sv in ts.get("statistics", [])}
            events_raw = fix.get("events", [])
            events = []
            for ev in events_raw[-10:]:  # last 10 events
                events.append({
                    "minute": (ev.get("time") or {}).get("elapsed"),
                    "type": ev.get("type"),
                    "detail": ev.get("detail"),
                    "player": (ev.get("player") or {}).get("name", ""),
                    "team_id": (ev.get("team") or {}).get("id"),
                    "home_team_id": t.get("home", {}).get("id"),
                })
            matches.append({
                "id": f.get("id"),
                "minute": (f.get("status") or {}).get("elapsed"),
                "status": (f.get("status") or {}).get("short"),
                "league": league.get("name"),
                "country": league.get("country"),
                "home": t.get("home", {}).get("name"),
                "home_id": t.get("home", {}).get("id"),
                "home_logo": t.get("home", {}).get("logo"),
                "away": t.get("away", {}).get("name"),
                "away_id": t.get("away", {}).get("id"),
                "away_logo": t.get("away", {}).get("logo"),
                "home_goals": g.get("home"),
                "away_goals": g.get("away"),
                "stats": stats,
                "events": events,
            })
        _live_cache["data"] = matches
        _live_cache["ts"] = now
        return matches
    except Exception:
        return []


_xg_cache = {}  # team_name -> {"ts": float, "xg": float}
_XG_CACHE_TTL = 3600  # 1 hour — xG data doesn't change minute to minute

def fetch_team_xg(team_name, num_matches=5):
    """Fetch average xG for a team from recent fixtures via api-football.com."""
    key = team_name.lower().strip()
    now = time.time()
    if key in _xg_cache and (now - _xg_cache[key]["ts"]) < _XG_CACHE_TTL:
        return _xg_cache[key]["xg"]
    if not FOOTBALL_API_KEY:
        return None
    try:
        # Step 1: search team id
        url = "https://v3.football.api-sports.io/teams?search=" + urllib.parse.quote(team_name)
        req = urllib.request.Request(url, headers={
            "x-rapidapi-key": FOOTBALL_API_KEY,
            "x-rapidapi-host": "v3.football.api-sports.io",
        })
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read().decode())
        teams = data.get("response", [])
        if not teams:
            return None
        team_id = teams[0]["team"]["id"]
        # Step 2: get last N fixtures with stats
        url2 = f"https://v3.football.api-sports.io/fixtures?team={team_id}&last={num_matches}&timezone=America/Costa_Rica"
        req2 = urllib.request.Request(url2, headers={
            "x-rapidapi-key": FOOTBALL_API_KEY,
            "x-rapidapi-host": "v3.football.api-sports.io",
        })
        with urllib.request.urlopen(req2, timeout=6) as r:
            data2 = json.loads(r.read().decode())
        xg_vals = []
        for fix in data2.get("response", []):
            t = fix.get("teams", {})
            is_home = t.get("home", {}).get("id") == team_id
            side = "home" if is_home else "away"
            stats = fix.get("statistics", [])
            for ts in stats:
                if ts.get("team", {}).get("id") == team_id:
                    for sv in ts.get("statistics", []):
                        if sv.get("type") == "expected_goals" and sv.get("value"):
                            try:
                                xg_vals.append(float(sv["value"]))
                            except Exception:
                                pass
        if not xg_vals:
            return None
        avg_xg = round(sum(xg_vals) / len(xg_vals), 2)
        _xg_cache[key] = {"ts": now, "xg": avg_xg}
        return avg_xg
    except Exception:
        return None


# ── Auto-resolve finished matches + Elo update ──────────────────────────────
_resolved_fixtures = set()  # fixture ids already processed this session

def auto_resolve_finished_matches():
    """Background task: detect WC matches just finished, resolve picks, update Elo."""
    try:
        cfg = load_config()
        sportsdb_key = cfg.get("sportsdb_key", "3")
        today = time.strftime("%Y-%m-%d")
        matches, _ = fetch_matches(today, sportsdb_key, "worldcup", None)
        for m in matches:
            if m.get("status") != "Finished":
                continue
            fid = m.get("id") or f"{m.get('home')}|{m.get('away')}"
            if fid in _resolved_fixtures:
                continue
            sh = m.get("scoreHome")
            sa = m.get("scoreAway")
            if sh is None or sa is None:
                continue
            try:
                sh, sa = int(sh), int(sa)
            except (ValueError, TypeError):
                continue
            score_str = f"{sh}-{sa}"
            home, away = m.get("home", ""), m.get("away", "")
            if not home or not away:
                continue
            # Resolve predictions in DB
            n = db.resolve_predictions(home, away, score_str)
            # Update Elo ratings
            model.update_elo_after_match(home, away, sh, sa)
            _resolved_fixtures.add(fid)
            print(f"[auto-resolve] {home} {sh}-{sa} {away} → {n} picks resolved, Elo updated")
    except Exception as e:
        print(f"[auto-resolve] error: {e}")


def _start_auto_resolve_thread():
    def loop():
        while True:
            auto_resolve_finished_matches()
            time.sleep(300)  # every 5 minutes
    t = threading.Thread(target=loop, daemon=True)
    t.start()


def load_supporters():
    if os.path.exists(SUPPORTERS_PATH):
        try:
            with open(SUPPORTERS_PATH, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_supporter(name, amount, message):
    supporters = load_supporters()
    # Sanitize inputs
    name = (name or "Anónimo").strip()[:40]
    amount = (amount or "").strip()[:30]
    message = (message or "").strip()[:120]
    supporters.append({
        "name": name or "Anónimo",
        "amount": amount,
        "message": message,
        "date": time.strftime("%Y-%m-%d"),
    })
    with open(SUPPORTERS_PATH, "w", encoding="utf-8") as f:
        json.dump(supporters, f, ensure_ascii=False, indent=2)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        pass  # quiet

    def _add_security_headers(self):
        """Emit OWASP-recommended defensive headers on every response."""
        self.send_header("X-Frame-Options", "DENY")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Referrer-Policy", "strict-origin-when-cross-origin")
        self.send_header("Permissions-Policy", "geolocation=(), microphone=(), camera=()")
        self.send_header("Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline'; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: blob:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'")

    def _send_json(self, obj, code=200):
        body = json.dumps(obj).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        # Restrict CORS to same origin only (was '*' — security risk)
        self.send_header("Access-Control-Allow-Origin", "null")
        self._add_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _send_static(self, fname, ctype):
        path = os.path.join(HERE, fname)
        # Path traversal guard — ensure file is inside project dir
        real = os.path.realpath(path)
        if not real.startswith(os.path.realpath(HERE)):
            self.send_error(403, "Forbidden")
            return
        try:
            with open(path, "rb") as f:
                body = f.read()
        except FileNotFoundError:
            self.send_error(404, "Not found")
            return
        self.send_response(200)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store, no-cache, must-revalidate")
        self._add_security_headers()
        self.end_headers()
        self.wfile.write(body)

    def _remote_allowed(self, qs):
        cfg = load_config()
        token = cfg.get("remote_token", "").strip()
        if not token:
            return True
        if _parse_cookies(self.headers.get("Cookie", "")).get(_REMOTE_TOKEN_COOKIE) == token:
            return True
        return (qs.get("token") or [""])[0] == token

    def _set_token_cookie_and_redirect(self, token):
        self.send_response(302)
        self.send_header("Location", "/")
        self.send_header("Set-Cookie",
            f"{_REMOTE_TOKEN_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; Max-Age=31536000")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def _send_login_page(self):
        self.send_response(401)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(LOGIN_PAGE_HTML)))
        self.end_headers()
        self.wfile.write(LOGIN_PAGE_HTML)

    def _check_remote_auth(self, qs):
        """Call at the top of do_GET/do_POST for non-local requests. Returns True if allowed."""
        if _is_local_request(self):
            return True
        cfg = load_config()
        token = cfg.get("remote_token", "").strip()
        if not token:
            return True
        # Validate token from cookie or query param
        url_token = (qs.get("token") or [""])[0]
        if url_token:
            if url_token == token:
                self._set_token_cookie_and_redirect(token)
                return False   # handler sent a redirect; caller must return
            self._send_login_page()
            return False
        if not self._remote_allowed(qs):
            self._send_login_page()
            return False
        return True

    def _get_user(self):
        """Return session dict {username, role} or None."""
        token = _cookie_session(self)
        return _get_session(token)

    def _require_auth(self):
        """Redirect to /login if not authenticated. Returns user dict or None."""
        user = self._get_user()
        if user:
            return user
        self.send_response(302)
        self.send_header("Location", "/login")
        self.send_header("Content-Length", "0")
        self.end_headers()
        return None

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path
        qs = urllib.parse.parse_qs(parsed.query)

        # Public assets needed by login page — no auth required
        PUBLIC_ROUTES = {"/login", "/landing", "/landing.html", "/brand/mascota.jpg", "/brand/mascota.svg",
                          "/manifest.json", "/sw.js"}
        # PWA icons — public
        if route.startswith("/icons/"):
            fname = route.lstrip("/")
            fpath = os.path.join(HERE, "frontend", fname)
            if os.path.exists(fpath):
                with open(fpath, "rb") as fh:
                    data = fh.read()
                self.send_response(200)
                self.send_header("Content-Type", "image/png")
                self.send_header("Cache-Control", "public, max-age=86400")
                self.end_headers()
                self.wfile.write(data)
                return

        if route in PUBLIC_ROUTES:
            if route == "/login":
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                body = AUTH_LOGIN_HTML.encode("utf-8")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
                return
            fname, ctype = STATIC_FILES[route]
            return self._send_static(fname, ctype)

        # CSS/JS also public so login page can use app styles indirectly
        if route in ("/styles.css", "/app.js"):
            fname, ctype = STATIC_FILES[route]
            return self._send_static(fname, ctype)

        # All other routes require login
        user = self._require_auth()
        if not user:
            return

        if route == "/api/me":
            perms = ROLE_PERMS.get(user["role"], ROLE_PERMS["premium"])
            return self._send_json({"username": user["username"], "role": user["role"], "perms": perms})

        if route in STATIC_FILES:
            fname, ctype = STATIC_FILES[route]
            return self._send_static(fname, ctype)

        if route == "/api/config":
            cfg = load_config()
            return self._send_json({
                "hasAnthropicKey": bool(cfg.get("anthropic_api_key", "").strip()),
                "model": cfg.get("anthropic_model", DEFAULT_MODEL),
                "sportsdbKey": cfg.get("sportsdb_key", "3"),
                "hasRemoteToken": bool(cfg.get("remote_token", "").strip()),
                "hasApiFootball": bool(cfg.get("apifootball_key", "").strip()),
                "emailAddress": cfg.get("email_address", ""),
                "emailRecipient": cfg.get("email_recipient", "Esteban_vm12@hotmail.com"),
                "hasEmailPassword": bool(cfg.get("email_password", "").strip()),
                "telegramChatId": cfg.get("telegram_chat_id", ""),
                "hasTelegramToken": bool(cfg.get("telegram_bot_token", "").strip()),
            })

        if route == "/api/network-info":
            lan_ip = _get_lan_ip()
            acc = None
            if _CALIBRATOR_AVAILABLE:
                try:
                    acc = _calibrator.get_model_accuracy()
                except Exception:
                    pass
            overrides_count = len(model._load_elo_overrides())
            public_url = os.environ.get("PUBLIC_URL") or _TUNNEL_URL
            return self._send_json({
                "lanIp": lan_ip,
                "lanUrl": f"http://{lan_ip}:{PORT}" if lan_ip else None,
                "publicUrl": public_url,
                "port": PORT,
                "modelAccuracy": acc,
                "eloOverrides": overrides_count,
            })

        if route == "/api/matches":
            date_str = (qs.get("date") or [time.strftime("%Y-%m-%d")])[0]
            scope = (qs.get("scope") or ["worldcup"])[0]
            if scope not in ("worldcup", "international", "clubs", "all"):
                scope = "worldcup"
            try:
                tz_min = int((qs.get("tz") or [""])[0])
            except ValueError:
                tz_min = None
            cfg = load_config()
            try:
                if scope == "all":
                    # Merge all scopes: WC + international + clubs
                    wc, _ = fetch_matches(date_str, cfg.get("sportsdb_key", "3"), "worldcup", tz_min)
                    intl, _ = fetch_matches(date_str, cfg.get("sportsdb_key", "3"), "international", tz_min)
                    clubs, cached = fetch_matches(date_str, cfg.get("sportsdb_key", "3"), "clubs", tz_min)
                    seen_ids = set()
                    matches = []
                    for m in wc + intl + clubs:
                        mid = m.get("id") or f"{m['home']}:{m['away']}"
                        if mid not in seen_ids:
                            seen_ids.add(mid)
                            matches.append(m)
                    matches.sort(key=lambda m: m.get("kickoffUtc") or "")
                else:
                    matches, cached = fetch_matches(date_str, cfg.get("sportsdb_key", "3"), scope, tz_min)
                # Auto-resolve any stored predictions for finished matches
                for m in matches:
                    if (m.get("status") == "Finished"
                            and m.get("homeScore") is not None
                            and m.get("awayScore") is not None):
                        actual = f"{m['homeScore']}-{m['awayScore']}"
                        try:
                            db.resolve_predictions(m["home"], m["away"], actual)
                        except Exception:
                            pass
                # Inject live scores from api-football into ESPN/SportsDB matches
                try:
                    live_data = fetch_live_matches() or []
                    if live_data:
                        live_index = {}
                        for lm in live_data:
                            h = (lm.get("home") or "").lower().strip()
                            a = (lm.get("away") or "").lower().strip()
                            if h and a:
                                live_index[(h, a)] = lm
                        for m in matches:
                            mh = (m.get("home") or "").lower().strip()
                            ma = (m.get("away") or "").lower().strip()
                            lm = live_index.get((mh, ma))
                            if not lm:
                                # fuzzy: check if any live match shares first word of team name
                                for (lh, la), lmatch in live_index.items():
                                    if (mh.split()[0] in lh or lh.split()[0] in mh) and \
                                       (ma.split()[0] in la or la.split()[0] in ma):
                                        lm = lmatch
                                        break
                            if lm:
                                st = lm.get("status")
                                if st in ("1H", "2H", "HT", "ET", "P", "BT"):
                                    m["status"] = "Live"
                                    m["scoreHome"] = lm.get("home_goals")
                                    m["scoreAway"] = lm.get("away_goals")
                                    m["minute"] = lm.get("minute")
                                    m["liveStats"] = lm.get("stats", {})
                                    m["liveEvents"] = lm.get("events", [])
                                elif st == "FT":
                                    m["status"] = "Finished"
                                    m["scoreHome"] = lm.get("home_goals")
                                    m["scoreAway"] = lm.get("away_goals")
                except Exception:
                    pass
                # Enrich matches with weather + live odds (non-blocking, best-effort)
                try:
                    from integrations import enrich_match_dict
                    for m in matches:
                        if m.get("status") not in ("Finished", "Live"):
                            enrich_match_dict(m)
                except Exception:
                    pass

                # Inject canal (TV channel for Costa Rica)
                def _canal(m):
                    lg = (m.get("league") or "").lower()
                    if "world cup" in lg or "copa del mundo" in lg:
                        return "ESPN / Teletica"
                    if "champions" in lg:
                        return "ESPN / Star+"
                    if "europa league" in lg or "conference" in lg:
                        return "ESPN"
                    if "premier" in lg:
                        return "ESPN"
                    if "bundesliga" in lg or "serie a" in lg or "la liga" in lg or "ligue 1" in lg:
                        return "ESPN / Star+"
                    if "nations league" in lg or "copa america" in lg or "gold cup" in lg:
                        return "ESPN / Teletica"
                    return "ESPN / Fox Sports"
                for m in matches:
                    m["canal"] = _canal(m)
                return self._send_json({
                    "date": date_str, "scope": scope, "matches": matches, "cached": cached,
                })
            except Exception as e:
                return self._send_json(
                    {"date": date_str, "scope": scope, "matches": [], "error": str(e)}, 502)

        if route == "/api/enrich":
            # Returns weather + live odds for a specific match
            home    = (qs.get("home") or [""])[0]
            away    = (qs.get("away") or [""])[0]
            venue   = (qs.get("venue") or [""])[0]
            kickoff = (qs.get("kickoff") or [""])[0]
            if not home or not away:
                return self._send_json({"error": "home and away required"}, 400)
            try:
                from integrations import get_match_odds, weather_for_match, reddit_summary
                result = {"home": home, "away": away}
                odds = get_match_odds(home, away)
                if odds:
                    result["odds"] = {
                        "best_home": odds.get("best_home"),
                        "best_draw": odds.get("best_draw"),
                        "best_away": odds.get("best_away"),
                        "bookmakers": odds.get("bookmakers", [])[:3],
                        "source": "the-odds-api",
                    }
                if venue:
                    w = weather_for_match(venue, kickoff or None)
                    if w:
                        result["weather"] = w
                result["reddit"] = reddit_summary(home, away) or None
                return self._send_json(result)
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/odds":
            # Doradobet's sportsbook data requires their proprietary WebSocket SDK.
            # We return the deep-link URL and account status instead.
            status = doradobet.status()
            return self._send_json({
                "doradobet_url": "https://doradobet.com/deportes/soccer/world/world-cup",
                "logged_in": status.get("logged_in", False),
                "username": status.get("username", ""),
                "note": "Live odds require Doradobet app — click the button to open the match.",
            })

        if route == "/api/notes":
            date_str = (qs.get("date") or [None])[0]
            try:
                return self._send_json({"notes": db.get_notes(date_str)})
            except Exception as e:
                return self._send_json({"notes": [], "error": str(e)}, 500)

        if route == "/api/predictions/accuracy":
            try:
                days = int((qs.get("days") or ["14"])[0])
                acc = db.get_recent_accuracy(days=days)
                return self._send_json({"accuracy": acc})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/scout-report":
            # Generate (or return cached) ProGol CR daily self-analysis report
            force = (qs.get("force") or ["0"])[0] == "1"
            date_str = (qs.get("date") or [time.strftime("%Y-%m-%d")])[0]
            try:
                if force:
                    report = db.generate_scout_report(date_str)
                else:
                    report = db.get_latest_scout_report()
                    if not report or report.get("report_date") != date_str:
                        report = db.generate_scout_report(date_str)
                return self._send_json({"ok": True, "report": report})
            except Exception as e:
                return self._send_json({"ok": False, "error": str(e)}, 500)

        if route == "/api/pick-del-dia":
            date_str = time.strftime("%Y-%m-%d")
            try:
                cfg = load_config()
                sportsdb_key = cfg.get("sportsdb_key", "3")
                all_matches = []
                seen = set()
                eff_tz = _server_tz_minutes()
                for scope in ("wc", "international", "clubs"):
                    try:
                        matches, _ = fetch_matches(date_str, sportsdb_key, scope, None)
                    except Exception:
                        matches = []
                        for utc_day in _utc_days_for_local_date(date_str, eff_tz):
                            matches.extend(
                                m for m in db.get_cached_matches(utc_day, scope)
                                if _event_local_date(m, eff_tz) == date_str
                            )
                    for m in matches:
                        mid = m.get("id") or f"{m.get('home')}|{m.get('away')}"
                        if mid not in seen:
                            seen.add(mid)
                            all_matches.append(m)
                best = None
                best_conf = -1
                best_wc = None
                best_wc_conf = -1
                for m in all_matches:
                    if not m.get("home") or not m.get("away"):
                        continue
                    if m.get("status") in ("Cancelled", "Postponed", "Finished"):
                        continue
                    league = (m.get("league") or "").lower()
                    is_wc = "world cup" in league or "mundial" in league or "fifa" in league
                    try:
                        hf = db.get_team_form(m["home"])
                        af = db.get_team_form(m["away"])
                        kw = _wc_predict_kwargs(m)
                        pred = model.predict(m["home"], m["away"], home_form=hf, away_form=af, **kw)
                        entry = {
                            "home": m["home"], "away": m["away"],
                            "league": m.get("league") or "",
                            "homeBadge": m.get("homeBadge") or "",
                            "awayBadge": m.get("awayBadge") or "",
                            "kickoffUtc": m.get("kickoffUtc") or "",
                            "conf": pred["conf"], "prob": pred["prob"],
                            "favorite": pred["favorite"],
                            "predictedScore": pred["predictedScore"],
                        }
                        if is_wc and pred["conf"] > best_wc_conf:
                            best_wc_conf = pred["conf"]
                            best_wc = entry
                        elif not is_wc and pred["conf"] > best_conf:
                            best_conf = pred["conf"]
                            best = entry
                    except Exception:
                        pass
                # Prefer World Cup pick; only use other leagues if no WC matches today
                if best_wc:
                    best = best_wc
                    best_conf = best_wc_conf
                if best:
                    best["low_conf"] = best_conf < 5.0
                    return self._send_json({"pick": best, "date": date_str})
                return self._send_json({"error": "No hay picks disponibles para hoy", "date": date_str})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/top-picks":
            date_str = (qs.get("date") or [time.strftime("%Y-%m-%d")])[0]
            try:
                tz_min = int((qs.get("tz") or [""])[0])
            except ValueError:
                tz_min = None
            cfg = load_config()
            sportsdb_key = cfg.get("sportsdb_key", "3")
            # Pull every fixture for the day, LIVE, across all scopes — the same
            # source the main match list uses (falls back to cache per-scope).
            all_matches = []
            seen = set()
            eff_tz = tz_min if tz_min is not None else _server_tz_minutes()
            for scope in ("worldcup", "international", "clubs"):
                try:
                    matches, _ = fetch_matches(date_str, sportsdb_key, scope, tz_min)
                except Exception as e:
                    print(f"[top-picks] scope {scope} failed: {e}")
                    # DB cache is UTC-keyed: pull overlapping UTC days, keep
                    # only games whose LOCAL kickoff is the requested day
                    matches = []
                    for utc_day in _utc_days_for_local_date(date_str, eff_tz):
                        matches.extend(
                            m for m in db.get_cached_matches(utc_day, scope)
                            if _event_local_date(m, eff_tz) == date_str
                        )
                for m in matches:
                    mid = m.get("id") or f"{m.get('home')}|{m.get('away')}"
                    if mid in seen:
                        continue
                    seen.add(mid)
                    all_matches.append(m)

            picks = []
            skipped_dead = 0
            for m in all_matches:
                if not m.get("home") or not m.get("away"):
                    continue
                # Cancelled / postponed games aren't real fixtures — never rank them
                if m.get("status") in ("Cancelled", "Postponed"):
                    skipped_dead += 1
                    continue
                try:
                    hf = db.get_team_form(m["home"])
                    af = db.get_team_form(m["away"])
                    kw = _wc_predict_kwargs(m)
                    pred = model.predict(m["home"], m["away"],
                                         home_form=hf, away_form=af, **kw)
                    picks.append({
                        "home":         m["home"],
                        "away":         m["away"],
                        "league":       m.get("league") or "",
                        "homeBadge":    m.get("homeBadge") or "",
                        "awayBadge":    m.get("awayBadge") or "",
                        "kickoffUtc":   m.get("kickoffUtc") or "",
                        "status":       m.get("status") or "",
                        "conf":         pred["conf"],
                        "favorite":     pred["favorite"],
                        "prob":         pred["prob"],
                        "predictedScore": pred["predictedScore"],
                        "over25":       pred["over25"],
                        "btts":         pred["btts"],
                        "over15":       pred["over15"],
                        "expectedGoals": pred["expectedGoals"],
                    })
                except Exception as e:
                    print(f"[top-picks] predict failed for "
                          f"{m.get('home')} vs {m.get('away')}: {e}")
            picks.sort(key=lambda x: x["conf"], reverse=True)
            return self._send_json({
                "picks": picks[:10],
                "total": len(picks),
                "scanned": len(all_matches),
                "skippedDead": skipped_dead,
            })


        if route == "/api/council":
            home = (qs.get("home") or [""])[0]
            away = (qs.get("away") or [""])[0]
            n    = int((qs.get("n") or ["1000"])[0])
            if not home or not away:
                return self._send_json({"error": "home and away required"}, 400)
            try:
                import council as _cmod
                r = _cmod.deliberate(home, away, n_simulations=n)
                ryder = r.get("ryder", {}).get("probs", {})
                lucas = r.get("lucas", {})
                cleo  = r.get("cleo", {})

                # Consenso Ryder(40%) + Lucas(60%)
                ph_r = ryder.get("home", 0)
                pd_r = ryder.get("draw", 0)
                pa_r = ryder.get("away", 0)
                ph_l = lucas.get("p_home", ph_r)
                pd_l = lucas.get("p_draw", pd_r)
                pa_l = lucas.get("p_away", pa_r)
                ph = round(0.4*ph_r + 0.6*ph_l, 4)
                pd = round(0.4*pd_r + 0.6*pd_l, 4)
                pa = round(0.4*pa_r + 0.6*pa_l, 4)

                top_sc = lucas.get("top_scorelines", []) if lucas else []
                opps   = cleo.get("opportunities", []) if cleo else []

                return self._send_json({
                    "home": home, "away": away,
                    "ryder": {
                        "ph": round(ph_r*100, 1),
                        "pd": round(pd_r*100, 1),
                        "pa": round(pa_r*100, 1),
                    },
                    "lucas": {
                        "ph": round(ph_l*100, 1),
                        "pd": round(pd_l*100, 1),
                        "pa": round(pa_l*100, 1),
                        "n": lucas.get("n", n),
                        "top_scorelines": [[s[0], round(s[1]*100,1)] for s in top_sc[:5]],
                    },
                    "cleo": {
                        "opportunities": opps[:3],
                        "markets": {k: v for k,v in (cleo.get("markets") or {}).items() if v.get("available")},
                    },
                    "consensus": {
                        "ph": round(ph*100, 1),
                        "pd": round(pd*100, 1),
                        "pa": round(pa*100, 1),
                    },
                })
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/predict":
            home = (qs.get("home") or [""])[0]
            away = (qs.get("away") or [""])[0]
            neutral = (qs.get("neutral") or ["0"])[0] in ("1", "true", "yes")
            if not home or not away:
                return self._send_json({"error": "home and away are required"}, 400)
            try:
                home_form = db.get_team_form(home)
                away_form = db.get_team_form(away)
                # Try to fetch real xG data (cached; non-blocking on failure)
                xg_h = fetch_team_xg(home) if FOOTBALL_API_KEY else None
                xg_a = fetch_team_xg(away) if FOOTBALL_API_KEY else None
                pred = model.predict(home, away, home_advantage=not neutral,
                                     home_form=home_form, away_form=away_form,
                                     xg_home=xg_h, xg_away=xg_a)
                pred["xg_source"] = "api-football" if (xg_h is not None) else "elo-derived"
                # Enrich with live odds + weather (non-blocking)
                try:
                    from integrations import get_match_odds, weather_for_match
                    venue   = (qs.get("venue") or [""])[0]
                    kickoff = (qs.get("kickoff") or [""])[0]
                    odds = get_match_odds(home, away)
                    if odds:
                        bh = odds.get("best_home") or 0
                        bd = odds.get("best_draw") or 0
                        ba = odds.get("best_away") or 0
                        # Normalizar probs de mercado (quitar margen de la casa)
                        raw_h = (1/bh*100) if bh else 0
                        raw_d = (1/bd*100) if bd else 0
                        raw_a = (1/ba*100) if ba else 0
                        tot   = raw_h + raw_d + raw_a
                        mkt_h = round(raw_h/tot*100, 1) if tot else 0
                        mkt_d = round(raw_d/tot*100, 1) if tot else 0
                        mkt_a = round(raw_a/tot*100, 1) if tot else 0
                        # Consenso: comparar favorito del modelo vs mercado
                        fav_home = pred["prob"]["home"] >= pred["prob"]["away"]
                        model_fav = pred["prob"]["home"] if fav_home else pred["prob"]["away"]
                        mkt_fav   = mkt_h if fav_home else mkt_a
                        delta = round(abs(model_fav - mkt_fav), 1)
                        consensus = "high" if delta < 8 else "medium" if delta < 15 else "low"
                        pred["liveOdds"] = {
                            "best_home": bh or None,
                            "best_draw": bd or None,
                            "best_away": ba or None,
                            "bookmakers_count": len(odds.get("bookmakers", [])),
                            "source": "the-odds-api",
                            "mkt_home": mkt_h,
                            "mkt_draw": mkt_d,
                            "mkt_away": mkt_a,
                            "delta":     delta,
                            "consensus": consensus,
                        }
                    if venue:
                        weather = weather_for_match(venue, kickoff or None)
                        if weather:
                            pred["weather"] = weather
                except Exception:
                    pass
                # Auto-save prediction to history (non-blocking — don't crash if it fails)
                try:
                    from analysis.data_quality import audit_match as _dq
                    from storage.prediction_history import save_prediction as _sp
                    _audit = _dq(home, away, time.strftime("%Y-%m-%d"), source="espn")
                    _sp(home, away, time.strftime("%Y-%m-%d"), pred,
                        quality_audit=_audit, competition="FIFA World Cup 2026")
                except Exception:
                    pass
                return self._send_json(pred)
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/local-scout":
            home = (qs.get("home") or [""])[0]
            away = (qs.get("away") or [""])[0]
            league = (qs.get("league") or [""])[0]
            if not home or not away:
                return self._send_json({"error": "home and away required"}, 400)
            try:
                fake_match = {"home": home, "away": away, "league": league}
                kw = _wc_predict_kwargs(fake_match)
                pred = model.predict(home, away, **kw)
                analysis = local_scout_analysis(home, away, pred)
                return self._send_json({"reply": analysis, "local": True})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/standings":
            try:
                standings = _fetch_wc_standings()
                # Merge in fixture data
                try:
                    fixtures = _fetch_group_fixtures()
                    for grp in standings:
                        grp["fixtures"] = fixtures.get(grp["name"], [])
                except Exception:
                    pass
                return self._send_json({"groups": standings})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/ryder/model-health":
            # Returns model accuracy, brier score, prediction count for owner dashboard
            try:
                from storage.prediction_history import model_health_summary
                summary = model_health_summary(last_n=50)
                # Also attach recent unreviewed predictions count
                try:
                    from storage.prediction_history import get_unreviewed_predictions
                    unreviewed = get_unreviewed_predictions()
                    summary["unreviewed_count"] = len(unreviewed)
                except Exception:
                    summary["unreviewed_count"] = 0
                return self._send_json(summary)
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/ryder/prediction-history":
            try:
                from storage.prediction_history import get_recent_predictions
                preds = get_recent_predictions(
                    limit=int((qs.get("limit") or ["30"])[0]),
                    competition=(qs.get("competition") or [None])[0],
                    confidence_level=(qs.get("confidence") or [None])[0],
                )
                return self._send_json({"predictions": preds, "count": len(preds)})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/ryder/calibration":
            try:
                from analysis.calibration import calibration_summary
                n = int((qs.get("n") or ["100"])[0])
                return self._send_json(calibration_summary(last_n=n))
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/ryder/bias":
            try:
                from analysis.bias_detection import detect_biases
                n = int((qs.get("n") or ["200"])[0])
                return self._send_json(detect_biases(last_n=n))
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/ryder/source-health":
            try:
                return self._send_json(db.source_health_summary())
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/ryder/explain":
            home = (qs.get("home") or [""])[0]
            away = (qs.get("away") or [""])[0]
            if not home or not away:
                return self._send_json({"error": "home and away required"}, 400)
            try:
                import model as _model
                from analysis.data_quality import audit_match as dq_audit
                from analysis.explainability import explain, format_for_chat
                date_str = (qs.get("date") or [time.strftime("%Y-%m-%d")])[0]
                pred = _model.predict(home, away, home_advantage=False)
                audit = dq_audit(home, away, date_str, source="espn")
                explanation = explain(home, away, pred, quality_audit=audit)
                return self._send_json({
                    "explanation": explanation,
                    "narrative": format_for_chat(explanation),
                })
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/champion-prediction":
            try:
                # Get current group standings to find leaders
                standings = _fetch_wc_standings()
                # Build list of group winners and runners-up
                group_winners = []
                group_runners = []
                for grp in (standings or []):
                    teams = sorted(grp.get("teams", []),
                                   key=lambda t: (int(t.get("pts",0)), float(t.get("gd",0)), float(t.get("gf",0))),
                                   reverse=True)
                    if teams:
                        group_winners.append({"team": teams[0]["name"], "group": grp["name"], "logo": teams[0].get("logo","")})
                    if len(teams) > 1:
                        group_runners.append({"team": teams[1]["name"], "group": grp["name"], "logo": teams[1].get("logo",""), "pts": int(teams[1].get("pts",0)), "gd": float(teams[1].get("gd",0))})

                # If groups haven't started, fall back to strength-based seeding
                if not group_winners:
                    top_teams = [
                        ("Spain","Group E"), ("France","Group D"), ("Argentina","Group F"),
                        ("England","Group B"), ("Brazil","Group C"), ("Portugal","Group G"),
                        ("Netherlands","Group H"), ("Germany","Group A"),
                        ("Italy","Group I"), ("Belgium","Group J"), ("Croatia","Group K"),
                        ("Uruguay","Group L"), ("Colombia","Group A2"), ("Morocco","Group B2"),
                        ("USA","Group C2"), ("Mexico","Group D2"),
                    ]
                    group_winners = [{"team": t, "group": g, "logo": ""} for t, g in top_teams[:12]]
                    group_runners = [{"team": t, "group": g, "logo": "", "pts": 4, "gd": 0} for t, g in top_teams[12:]]

                # Build 32-team pool: 12 winners + 12 runners + 8 best 3rds
                # For simplicity use winners + runners, pad to 16 for bracket
                pool = group_winners[:12] + group_runners[:4]  # 16 teams
                # Sort by model strength for bracket seeding (1 vs 16, 2 vs 15, etc.)
                def _strength(entry):
                    return model.RATINGS.get(entry["team"].lower(), 1600)
                pool.sort(key=_strength, reverse=True)

                # Simulate single-elimination bracket
                def sim_match(a, b):
                    try:
                        pred = model.predict(a["team"], b["team"], home_advantage=False)
                        ph = pred.get("prob", {}).get("home", 40)
                        pa = pred.get("prob", {}).get("away", 40)
                        winner = a if ph >= pa else b
                        loser  = b if ph >= pa else a
                        conf = max(ph, pa)
                        return winner, loser, conf
                    except Exception:
                        # fallback to rating comparison
                        ra = _strength(a); rb = _strength(b)
                        winner = a if ra >= rb else b
                        loser  = b if ra >= rb else a
                        return winner, loser, 55

                bracket = []
                round_teams = pool[:]
                round_name = "Octavos"
                round_names = ["Octavos de Final", "Cuartos de Final", "Semifinal", "Final"]
                round_idx = 0
                while len(round_teams) > 1:
                    next_round = []
                    round_results = []
                    # Seed: 1 vs last, 2 vs second-last, etc.
                    pairs = [(round_teams[i], round_teams[-(i+1)]) for i in range(len(round_teams)//2)]
                    for a, b in pairs:
                        w, l, conf = sim_match(a, b)
                        next_round.append(w)
                        round_results.append({
                            "home": a["team"], "away": b["team"],
                            "winner": w["team"], "conf": round(conf, 1)
                        })
                    bracket.append({"round": round_names[min(round_idx, len(round_names)-1)], "matches": round_results})
                    round_teams = next_round
                    round_idx += 1

                champion = round_teams[0] if round_teams else {"team": "?"}
                # Extract finalists and semifinalists from bracket
                final_round = bracket[-1]["matches"] if bracket else []
                sf_round = bracket[-2]["matches"] if len(bracket) >= 2 else []
                finalists = [m["home"] if m["winner"] != m["home"] else m["away"] for m in final_round] + [m["winner"] for m in final_round]
                finalists = list(dict.fromkeys(finalists))  # deduplicate, keep order

                # Get runner-up (loser of final)
                finalist = None
                if final_round:
                    fm = final_round[0]
                    finalist = fm["away"] if fm["winner"] == fm["home"] else fm["home"]

                semis = []
                for m in sf_round:
                    loser = m["away"] if m["winner"] == m["home"] else m["home"]
                    semis.append(loser)

                return self._send_json({
                    "champion": champion["team"],
                    "finalist": finalist,
                    "semi1": semis[0] if semis else None,
                    "semi2": semis[1] if len(semis) > 1 else None,
                    "bracket": bracket,
                    "champion_logo": champion.get("logo",""),
                })
            except Exception as e:
                import traceback; traceback.print_exc()
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/group-fixtures":
            try:
                fixtures = _fetch_group_fixtures()
                return self._send_json({"fixtures": fixtures})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/doradobet/status":
            return self._send_json(doradobet.status())

        if route == "/api/live":
            home = (qs.get("home") or [""])[0]
            away = (qs.get("away") or [""])[0]
            if not home or not away:
                return self._send_json({"error": "home and away are required"}, 400)
            neutral = (qs.get("neutral") or ["0"])[0] in ("1", "true", "yes")
            minute = (qs.get("minute") or ["0"])[0]
            try: hs = int((qs.get("hs") or ["0"])[0])
            except ValueError: hs = 0
            try: as_ = int((qs.get("as") or ["0"])[0])
            except ValueError: as_ = 0
            try:
                home_form = db.get_team_form(home)
                away_form = db.get_team_form(away)
                live = model.predict_live(home, away, minute, hs, as_,
                                          home_advantage=not neutral,
                                          home_form=home_form, away_form=away_form)
                return self._send_json(live)
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/espn-stats":
            home = (qs.get("home") or [""])[0]
            away = (qs.get("away") or [""])[0]
            if not home or not away:
                return self._send_json({"found": False, "error": "home and away required"})
            stats = _espn_find_match(home, away)
            if not stats:
                return self._send_json({"found": False})
            return self._send_json(stats)

        if route == "/api/live-scores":
            matches = fetch_live_matches()
            if matches is None:
                return self._send_json({"error": "no_key", "matches": []})
            return self._send_json({"matches": matches, "ts": int(time.time())})

        if route == "/api/livematch-score":
            home = (qs.get("home") or [""])[0]
            away = (qs.get("away") or [""])[0]
            date_str = (qs.get("date") or [None])[0]
            if not home or not away:
                return self._send_json({"error": "home and away required"}, 400)
            try:
                # Try freeapi first, fall back to ESPN scoreboard
                raw = _freeapi_find_match(home, away, date_str)
                if raw:
                    parsed = _parse_freeapi_match(raw)
                    parsed["found"] = True
                    parsed["source"] = "freeapi"
                    return self._send_json(parsed)
                # ESPN fallback — always free, no rate limit issues
                espn = _espn_scoreboard_find(home, away, date_str)
                if espn:
                    return self._send_json(espn)
                return self._send_json({"found": False})
            except Exception as e:
                return self._send_json({"error": str(e), "found": False}, 500)

        if route == "/api/supporters":
            return self._send_json({"supporters": load_supporters()})

        if route == "/api/team-xg":
            team = (qs.get("team") or [""])[0].strip()
            if not team:
                return self._send_json({"error": "team param required"}, 400)
            xg = fetch_team_xg(team)
            return self._send_json({"team": team, "xg": xg})

        if route == "/api/calc-ev":
            # Recalculate EV given real odds from user
            # Params: home_prob, away_prob, draw_prob (0-100), real_odd (decimal)
            try:
                hp = float((qs.get("home_prob") or ["0"])[0])
                ap = float((qs.get("away_prob") or ["0"])[0])
                dp = float((qs.get("draw_prob") or ["0"])[0])
                real_odd = float((qs.get("real_odd") or ["0"])[0])
                market = (qs.get("market") or ["home"])[0]
                prob_map = {"home": hp, "draw": dp, "away": ap}
                prob = prob_map.get(market, hp) / 100.0
                ev = round(prob * real_odd - 1, 4)
                return self._send_json({"ev": ev, "ev_pct": round(ev * 100, 2), "prob": prob * 100, "real_odd": real_odd})
            except Exception as e:
                return self._send_json({"error": str(e)}, 400)

        if route == "/api/elo-ratings":
            overrides = model._load_elo_overrides()
            return self._send_json({"overrides": overrides, "count": len(overrides)})

        self.send_error(404, "Not found")

    def do_POST(self):
        try:
            self._do_POST_inner()
        except Exception as ex:
            import traceback
            traceback.print_exc()
            try:
                self._send_json({"error": f"Server error: {ex}"}, 500)
            except Exception:
                pass

    def _do_POST_inner(self):
        parsed = urllib.parse.urlparse(self.path)
        route = parsed.path

        length = int(self.headers.get("Content-Length", 0) or 0)
        if length > 512_000:  # 512 KB max — reject oversized payloads
            return self._send_json({"error": "payload too large"}, 413)
        raw = self.rfile.read(length) if length else b"{}"
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            return self._send_json({"error": "invalid JSON"}, 400)

        # ── Public auth routes (no session required) ──────────────────────────
        if route == "/api/login":
            client_ip = self.client_address[0]
            if not _login_check(client_ip):
                return self._send_json({"ok": False, "error": "Demasiados intentos. Espera 15 minutos."}, 429)
            username = (data.get("username") or "").strip()[:64]
            password = (data.get("password") or "")[:256]
            users = _load_users()
            u = users.get(username)
            if u and u.get("active", True) and _verify_pw(password, u["password"]):
                _login_clear(client_ip)
                token = _create_session(username, u["role"])
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Set-Cookie",
                    f"pgcr_session={token}; Path=/; HttpOnly; SameSite=Strict; Max-Age={_SESSION_TTL}")
                body = json.dumps({"ok": True, "role": u["role"]}).encode()
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)
            else:
                _login_record_fail(client_ip)
                time.sleep(0.5)  # slow down brute-force
                return self._send_json({"ok": False, "error": "Credenciales inválidas"}, 401)
            return

        if route == "/api/logout":
            token = _cookie_session(self)
            _sessions.pop(token, None)
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", "pgcr_session=; Path=/; HttpOnly; Max-Age=0")
            body = b'{"ok":true}'
            self.send_header("Content-Length", str(len(body)))
            self.end_headers()
            self.wfile.write(body)
            return

        # ── All other POST routes require auth ────────────────────────────────
        user = self._get_user()
        if not user:
            return self._send_json({"error": "Not authenticated"}, 401)

        # Remote access now protected by session auth (login with username/password)

        if route == "/api/config":
            new_vals = {
                "anthropic_api_key": data.get("anthropic_api_key"),
                "anthropic_model": data.get("anthropic_model"),
                "sportsdb_key": data.get("sportsdb_key"),
            }
            for k in ("remote_token", "apifootball_key", "email_address",
                      "email_password", "email_recipient", "telegram_bot_token", "telegram_chat_id"):
                if k in data:
                    new_vals[k] = data.get(k) or ""
            cfg = save_config(new_vals)
            return self._send_json({
                "ok": True,
                "hasAnthropicKey": bool(cfg.get("anthropic_api_key", "").strip()),
                "model": cfg.get("anthropic_model", DEFAULT_MODEL),
                "sportsdbKey": cfg.get("sportsdb_key", "3"),
                "hasRemoteToken": bool(cfg.get("remote_token", "").strip()),
                "hasApiFootball": bool(cfg.get("apifootball_key", "").strip()),
                "emailAddress": cfg.get("email_address", ""),
                "emailRecipient": cfg.get("email_recipient", "Esteban_vm12@hotmail.com"),
                "hasEmailPassword": bool(cfg.get("email_password", "").strip()),
                "telegramChatId": cfg.get("telegram_chat_id", ""),
                "hasTelegramToken": bool(cfg.get("telegram_bot_token", "").strip()),
            })

        if route == "/api/calibrate":
            if not _CALIBRATOR_AVAILABLE:
                return self._send_json({"ok": False, "error": "Calibrador no disponible"})
            try:
                date_str = data.get("date") or datetime.datetime.utcnow().strftime("%Y-%m-%d")
                results = _calibrator.calibrate_date(date_str, verbose=False)
                acc = _calibrator.get_model_accuracy()
                log = _calibrator.get_calibration_log(10)
                return self._send_json({"ok": True, "processed": results, "accuracy": acc, "log": log})
            except Exception as e:
                return self._send_json({"ok": False, "error": str(e)})

        if route == "/api/calibrate/status":
            if not _CALIBRATOR_AVAILABLE:
                return self._send_json({"available": False})
            try:
                acc = _calibrator.get_model_accuracy()
                log = _calibrator.get_calibration_log(5)
                overrides = model._load_elo_overrides()
                return self._send_json({"available": True, "accuracy": acc, "recent": log, "elo_overrides": len(overrides)})
            except Exception as e:
                return self._send_json({"available": True, "error": str(e)})

        if route == "/api/chat":
            cfg = load_config()
            message = (data.get("message") or "").strip()
            image_b64 = (data.get("image") or "").strip()
            if not message and not image_b64:
                return self._send_json({"error": "empty message"}, 400)

            # -- @Cleo / @Ryder handler (Consejo deliberativo Ryder x Cleo) --
            if message.lower().startswith("@cleo") or message.lower().startswith("@ryder"):
                try:
                    import council as _council_mod
                    import re as _re_cleo
                    import cleo as _cleo_mod

                    tail = _re_cleo.sub(r"^@(cleo|ryder)\s*", "", message, flags=_re_cleo.IGNORECASE).strip()

                    match_teams = _council_mod.detect_match(tail)
                    if not match_teams:
                        return self._send_json({
                            "reply": "Uso: `@Cleo [local] vs [visitante]`  o  `@Ryder [local] vs [visitante]`",
                            "refreshQuiniela": False
                        })

                    home_t, away_t = match_teams
                    _live_st = _parse_live_state(home_t, away_t, tail)
                    council_result = _council_mod.deliberate(home_t, away_t, tail, live_state=_live_st)
                    reply = _council_mod.format_council_reply(council_result)

                    try:
                        if council_result["cleo"].get("opportunities"):
                            _cleo_mod.CleoAgent().save_pick(council_result["cleo"])
                    except Exception:
                        pass

                    return self._send_json({"reply": reply, "refreshQuiniela": False})

                except Exception as _council_err:
                    import traceback; traceback.print_exc()
                    return self._send_json({
                        "reply": f"Error en Consejo: {_council_err}",
                        "refreshQuiniela": False
                    })
            # -- fin @Cleo/@Ryder --------------------------------------------
            if image_b64:
                cfg["_pending_image"] = image_b64
            history = data.get("history") or []
            matches = data.get("matches") or []
            date_str = data.get("date") or time.strftime("%Y-%m-%d")
            lang = "es" if data.get("lang") == "es" else "en"
            tz_min = _server_tz_minutes()

            # Short-circuit: no API key → route directly to local engines, never call Anthropic
            if not cfg.get("anthropic_api_key", "").strip():
                guru_kw = ["colones", "invertir", "apostar", "presupuesto", "manana", "mañana", "tengo", "plan", "parlay", "combo", "yolo", "₡"]
                msg_low = message.lower()
                if any(kw in msg_low for kw in guru_kw):
                    try:
                        guru_reply, _ = call_guru(cfg, message, matches, date_str, lang)
                        if guru_reply:
                            return self._send_json({"reply": guru_reply, "refreshQuiniela": False, "local": True})
                    except Exception:
                        pass
                local_reply = _try_local_scout_from_message(message, matches)
                if local_reply:
                    return self._send_json({"reply": local_reply, "refreshQuiniela": False, "local": True})
                return self._send_json({"reply": "🔌 **Ryder Local activo.**\n\nDime el partido o tu presupuesto:\n- *\"Francia vs España\"* → análisis completo del modelo\n- *\"Tengo ₡10,000 para hoy\"* → el Gurú arma el plan", "refreshQuiniela": False, "local": True})

            # -- Consejo Ryder x Cleo antes de Claude --------------------------
            _council_ctx = ""
            try:
                import council as _cm
                _teams = _cm.detect_match(message)
                # Activar Consejo Ryder x Cleo x Lucas siempre que haya partido
                if _teams or _cm.is_analytical(message):
                    if not _teams: _teams = _cm.detect_match(message)
                    if not _teams:
                        # Sin partido explicito: buscar en los partidos del dia
                        for _mx in (matches or [])[:3]:
                            _mh = _mx.get("home", "")
                            _ma = _mx.get("away", "")
                            _ml = message.lower()
                            if _mh and _ma and (
                                _mh.lower() in _ml or _ma.lower() in _ml or
                                any(p in _ml for p in _mh.lower().split() if len(p) > 3) or
                                any(p in _ml for p in _ma.lower().split() if len(p) > 3)
                            ):
                                _teams = (_mh, _ma)
                                break
                    if _teams:
                        _h, _a = _teams
                        _live_st_ctx = _parse_live_state(_h, _a, message)
                        _cres = _cm.deliberate(_h, _a, message, live_state=_live_st_ctx)
                        _council_ctx = _cm.format_council_context(_cres)
            except Exception as _ce:
                print(f"[council] context error: {_ce}")
            # ----------------------------------------------------------------

            _msg_with_ctx = (_council_ctx + message) if _council_ctx else message
            reply, err, tools_used = call_claude(cfg, _msg_with_ctx, history, matches, date_str, lang, tz_min=tz_min)
            if err:
                # API unavailable — route to local engines, never crash
                credits_err = any(k in err.lower() for k in ("credit balance", "billing", "too low", "insufficient", "quota", "api key", "authentication", "timed out", "timeout", "request failed"))
                if credits_err:
                    try:
                        guru_kw = ["colones", "invertir", "apostar", "presupuesto", "manana", "mañana", "tengo", "plan", "parlay", "combo", "yolo"]
                        msg_low = message.lower().replace("₡","")
                        if any(kw in msg_low for kw in guru_kw):
                            guru_reply, _ = call_guru(cfg, message, matches, date_str, lang)
                            if guru_reply:
                                return self._send_json({"reply": guru_reply, "refreshQuiniela": False, "local": True})
                    except Exception:
                        pass
                    try:
                        local_reply = _try_local_scout_from_message(message, matches)
                        if local_reply:
                            return self._send_json({"reply": local_reply, "refreshQuiniela": False, "local": True})
                    except Exception:
                        pass
                    return self._send_json({"reply": "🔌 **Ryder Local activo.**\n\nDime el partido o tu presupuesto:\n- *\"Francia vs España\"* → análisis completo del modelo\n- *\"Tengo ₡10,000 para hoy\"* → el Gurú arma el plan", "refreshQuiniela": False, "local": True})
                return self._send_json({"error": err}, 400)
            # Tell frontend to sync quiniela if standings/fixtures were fetched
            refresh_q = bool(tools_used & {"get_wc_standings", "get_group_fixtures", "get_live_matches"})
            return self._send_json({"reply": reply, "refreshQuiniela": refresh_q})

        if route == "/api/guru":
            cfg = load_config()
            message = (data.get("message") or "").strip()
            if not message:
                return self._send_json({"error": "empty message"}, 400)
            matches = data.get("matches") or []
            date_str = data.get("date") or time.strftime("%Y-%m-%d")
            reply, err = call_guru(cfg, message, matches, date_str)
            if err:
                return self._send_json({"error": err}, 400)
            return self._send_json({"reply": reply})

        if route == "/api/notes":
            body = (data.get("body") or "").strip()
            if not body:
                return self._send_json({"error": "note body is empty"}, 400)
            try:
                note_id = db.add_note(
                    data.get("match_date") or "",
                    data.get("competition") or "",
                    (data.get("title") or "").strip(),
                    body,
                )
                return self._send_json({"ok": True, "id": note_id})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/predictions":
            # Save an analyst prediction for later auto-resolution
            try:
                db.save_prediction(
                    data.get("match_date") or "",
                    (data.get("home") or "").strip(),
                    (data.get("away") or "").strip(),
                    (data.get("market") or "").strip().lower(),
                    (data.get("pick") or "").strip().lower(),
                    data.get("confidence"),
                )
                return self._send_json({"ok": True})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/predictions/accuracy":
            try:
                acc = db.get_recent_accuracy(days=int(data.get("days", 14)))
                return self._send_json({"accuracy": acc})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/ryder/post-match-review":
            # Owner-only: save a post-match review
            cfg_now = load_config()
            session_user = _get_session_user(self.headers)
            if not _is_owner(session_user, cfg_now):
                return self._send_json({"error": "No autorizado"}, 403)
            try:
                from analysis.post_match import review_match
                from storage.prediction_history import save_review
                review = review_match(
                    home=data.get("home", ""),
                    away=data.get("away", ""),
                    actual_home_score=int(data.get("home_score", 0)),
                    actual_away_score=int(data.get("away_score", 0)),
                    prediction=data.get("prediction", {}),
                    prediction_id=data.get("prediction_id"),
                    key_events=data.get("key_events"),
                    notes=data.get("notes"),
                    reviewed_by="esteban",
                )
                row_id = save_review(review)
                return self._send_json({"ok": True, "review_id": row_id, "review": review})
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/ryder/data-quality":
            # Audit data quality for a given match
            try:
                from analysis.data_quality import audit_match as dq_audit
                result = dq_audit(
                    home=data.get("home", ""),
                    away=data.get("away", ""),
                    match_date=data.get("date", time.strftime("%Y-%m-%d")),
                    kickoff_utc=data.get("kickoff_utc"),
                    competition=data.get("competition"),
                    source=data.get("source", "api"),
                )
                return self._send_json(result)
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/ryder/pre-match":
            # Generate structured pre-match report
            home = data.get("home", "")
            away = data.get("away", "")
            if not home or not away:
                return self._send_json({"error": "home and away required"}, 400)
            try:
                import model as _model
                from analysis.pre_match import build_pre_match_report
                from analysis.data_quality import audit_match as dq_audit
                home_form = db.get_team_form(home)
                away_form = db.get_team_form(away)
                pred = _model.predict(home, away, home_advantage=False,
                                      home_form=home_form, away_form=away_form)
                audit = dq_audit(home, away, data.get("date", time.strftime("%Y-%m-%d")))
                # Try to get live odds and weather
                live_odds = None
                weather   = None
                try:
                    from integrations import get_match_odds, weather_for_match
                    odds = get_match_odds(home, away)
                    if odds:
                        live_odds = {
                            "best_home": odds.get("best_home"),
                            "best_draw": odds.get("best_draw"),
                            "best_away": odds.get("best_away"),
                            "bookmakers_count": len(odds.get("bookmakers", [])),
                        }
                    venue = data.get("venue", "")
                    if venue:
                        weather = weather_for_match(venue, data.get("kickoff"))
                except Exception:
                    pass
                report = build_pre_match_report(
                    home, away, pred,
                    competition=data.get("competition", "FIFA World Cup 2026"),
                    home_form=home_form, away_form=away_form,
                    venue=data.get("venue"), kickoff_utc=data.get("kickoff"),
                    weather=weather, live_odds=live_odds, quality_audit=audit,
                )
                return self._send_json(report)
            except Exception as e:
                return self._send_json({"error": str(e)}, 500)

        if route == "/api/notes/delete":
            try:
                db.delete_note(int(data.get("id")))
                return self._send_json({"ok": True})
            except Exception as e:
                return self._send_json({"error": str(e)}, 400)

        if route == "/api/supporters":
            name = (data.get("name") or "").strip()
            amount = (data.get("amount") or "").strip()
            message = (data.get("message") or "").strip()
            if not amount:
                return self._send_json({"ok": False, "error": "amount requerido"}, 400)
            try:
                save_supporter(name, amount, message)
                return self._send_json({"ok": True})
            except Exception as e:
                return self._send_json({"ok": False, "error": str(e)}, 500)

        if route == "/api/doradobet/login":
            try:
                result = doradobet.login()
                return self._send_json(result)
            except Exception as e:
                return self._send_json({"logged_in": False, "error": str(e)}, 500)

        if route == "/api/send-picks-email":
            cfg = load_config()
            date_str = (data.get("date") or time.strftime("%Y-%m-%d")).strip()
            try:
                tz_min = int(data.get("tz", 0))
            except Exception:
                tz_min = None
            # Gather all today's matches across scopes
            all_matches = []
            seen_ids = set()
            for scope in ("worldcup", "international", "clubs"):
                try:
                    ms, _ = fetch_matches(date_str, cfg.get("sportsdb_key", "3"), scope, tz_min)
                    for m in ms:
                        if m.get("id") not in seen_ids:
                            seen_ids.add(m.get("id"))
                            all_matches.append(m)
                except Exception:
                    pass
            try:
                html, text = build_picks_email(all_matches, date_str, cfg)
                ok, err = send_picks_email(cfg, html, text, date_str)
                if ok:
                    recipient = cfg.get("email_recipient", "Esteban_vm12@hotmail.com")
                    return self._send_json({"ok": True, "message": f"Email enviado a {recipient}"})
                else:
                    return self._send_json({"ok": False, "error": err})
            except Exception as e:
                return self._send_json({"ok": False, "error": str(e)}, 500)

        if route == "/api/send-scout-report-email":
            cfg = load_config()
            date_str = time.strftime("%Y-%m-%d")
            try:
                report = db.get_latest_scout_report() or {}
                if not report:
                    db.generate_scout_report(date_str)
                    report = db.get_latest_scout_report() or {}

                hit_rate  = report.get("hit_rate", 0)
                total     = report.get("total_picks", 0)
                wins      = report.get("wins", 0)
                losses    = report.get("losses", 0)
                bm_raw    = report.get("vs_benchmark", "{}")
                try:
                    benchmarks = json.loads(bm_raw) if isinstance(bm_raw, str) else (bm_raw or {})
                except Exception:
                    benchmarks = {}
                insights_raw = report.get("auto_insights", "[]")
                try:
                    insights = json.loads(insights_raw) if isinstance(insights_raw, str) else (insights_raw or [])
                except Exception:
                    insights = []

                bm_rows = ""
                for name, data_bm in benchmarks.items():
                    our  = data_bm.get("progolcr", {}).get("overall", hit_rate)
                    them = data_bm.get("overall", 0)
                    diff = round(our - them, 1)
                    color = "#22c55e" if diff >= 0 else "#ef4444"
                    sign  = "+" if diff >= 0 else ""
                    bm_rows += f"<tr><td>{name}</td><td>{them}%</td><td style='color:{color};font-weight:700'>{our}% ({sign}{diff}%)</td></tr>"

                insights_html = "".join(f"<li>{i}</li>" for i in insights) if insights else "<li>Sin datos suficientes aún. El modelo mejora cada día.</li>"

                html_body = f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8">
<style>
  body {{ font-family: -apple-system,sans-serif; background:#060c0f; color:#f1f5f9; margin:0; padding:0; }}
  .wrap {{ max-width:600px; margin:0 auto; padding:32px 24px; }}
  .logo {{ font-size:28px; font-weight:900; margin-bottom:4px; }}
  .logo .pro {{ color:#22c55e; }} .logo .gol {{ color:#f59e0b; }} .logo .cr {{ font-size:16px; color:#86efac; letter-spacing:3px; margin-left:4px; }}
  .tag {{ color:#6b7280; font-size:13px; margin-bottom:32px; }}
  h2 {{ color:#22c55e; font-size:18px; margin:28px 0 12px; }}
  .stat-row {{ display:flex; gap:16px; margin-bottom:24px; flex-wrap:wrap; }}
  .stat {{ background:#0d1f17; border:1px solid rgba(34,197,94,.2); border-radius:10px; padding:16px 20px; flex:1; min-width:120px; text-align:center; }}
  .stat-num {{ font-size:28px; font-weight:900; color:#22c55e; }}
  .stat-label {{ font-size:12px; color:#6b7280; margin-top:4px; }}
  table {{ width:100%; border-collapse:collapse; margin-bottom:24px; font-size:14px; }}
  th {{ background:#0d1f17; color:#6b7280; padding:10px 12px; text-align:left; font-size:12px; text-transform:uppercase; letter-spacing:.06em; }}
  td {{ padding:10px 12px; border-bottom:1px solid rgba(255,255,255,.05); }}
  ul {{ color:#94a3b8; font-size:14px; line-height:1.8; padding-left:20px; }}
  .footer {{ color:#374151; font-size:12px; margin-top:40px; border-top:1px solid rgba(255,255,255,.05); padding-top:20px; }}
</style></head>
<body><div class="wrap">
  <div class="logo"><span class="pro">Pro</span><span class="gol">Gol</span><span class="cr">CR</span></div>
  <div class="tag">Scout Report Diario — {date_str}</div>

  <div class="stat-row">
    <div class="stat"><div class="stat-num">{hit_rate}%</div><div class="stat-label">Hit rate global</div></div>
    <div class="stat"><div class="stat-num">{total}</div><div class="stat-label">Picks totales</div></div>
    <div class="stat"><div class="stat-num" style="color:#22c55e">{wins}W</div><div class="stat-label">Ganados</div></div>
    <div class="stat"><div class="stat-num" style="color:#ef4444">{losses}L</div><div class="stat-label">Perdidos</div></div>
  </div>

  <h2>ProGol CR vs Competidores</h2>
  <table>
    <thead><tr><th>Plataforma</th><th>Hit rate</th><th>ProGol CR</th></tr></thead>
    <tbody>{bm_rows if bm_rows else '<tr><td colspan="3" style="color:#6b7280">Acumulando datos — disponible después de 30+ picks registrados</td></tr>'}</tbody>
  </table>

  <h2>Insights automáticos del modelo</h2>
  <ul>{insights_html}</ul>

  <div class="footer">
    ProGol CR · Inteligencia Deportiva · Costa Rica<br>
    Este reporte es generado automáticamente por el modelo Dixon-Coles.<br>
    No es garantía de ganancia. La decisión final siempre es tuya.
  </div>
</div></body></html>"""

                plain = f"Scout Report ProGol CR — {date_str}\nHit rate: {hit_rate}%  |  Picks: {total}  |  {wins}W / {losses}L\nVer reporte completo en la app."
                sender    = cfg.get("email_address", "").strip()
                password  = cfg.get("email_password", "").strip()
                recipient = cfg.get("email_recipient", "Esteban_vm12@hotmail.com").strip()
                if not sender or not password:
                    return self._send_json({"ok": False, "error": "Email no configurado en Ajustes."})

                import email.mime.multipart as _mmp, email.mime.text as _mmt
                host, port = _smtp_for(sender)
                msg = _mmp.MIMEMultipart("alternative")
                msg["Subject"] = f"📊 Scout Report ProGol CR — {date_str}"
                msg["From"] = sender
                msg["To"] = recipient
                msg.attach(_mmt.MIMEText(plain, "plain", "utf-8"))
                msg.attach(_mmt.MIMEText(html_body, "html", "utf-8"))
                import smtplib as _smtp
                with _smtp.SMTP(host, port, timeout=30) as s:
                    s.ehlo(); s.starttls(); s.ehlo()
                    s.login(sender, password)
                    s.sendmail(sender, [recipient], msg.as_string())
                return self._send_json({"ok": True, "message": f"Scout Report enviado a {recipient}"})
            except Exception as e:
                return self._send_json({"ok": False, "error": str(e)}, 500)

        if route == "/api/invest/chat":
            cfg = load_config()
            message = (data.get("message") or "").strip()
            if not message:
                return self._send_json({"error": "empty message"}, 400)
            history = data.get("history") or []
            lang = "es" if data.get("lang") == "es" else "en"
            reply, err = call_claude_invest(cfg, message, history, lang)
            if err:
                if "api key" in err.lower() or "anthropic" in err.lower():
                    return self._send_json({"reply": "⚙️ Se requiere una clave API de Anthropic. Configúrala en Ajustes (⚙)."})
                return self._send_json({"error": err}, 400)
            return self._send_json({"reply": reply})

        # ---- user auth endpoints ----
        if route == "/api/auth/register":
            email = (data.get("email") or "").strip()
            password = (data.get("password") or "").strip()
            if not email or not password:
                return self._send_json({"ok": False, "error": "Email y contraseña son requeridos."}, 400)
            try:
                user = db.create_user(email, password)
                return self._send_json({"ok": True, "user_id": user["id"], "api_key": user["api_key"], "tier": user["tier"]})
            except ValueError as e:
                return self._send_json({"ok": False, "error": str(e)}, 409)
            except Exception as e:
                return self._send_json({"ok": False, "error": str(e)}, 500)

        if route == "/api/auth/login":
            email = (data.get("email") or "").strip()
            password = (data.get("password") or "").strip()
            user = db.authenticate_user(email, password)
            if not user:
                return self._send_json({"ok": False, "error": "Credenciales incorrectas."}, 401)
            return self._send_json({"ok": True, "api_key": user["api_key"], "tier": user["tier"], "email": user["email"]})

        if route == "/api/auth/me":
            user, err_json = _require_auth(data)
            if err_json:
                return self._send_json(json.loads(err_json), 401)
            return self._send_json({"ok": True, "email": user["email"], "tier": user["tier"], "created_at": user["created_at"]})

        self.send_error(404, "Not found")


def _get_lan_ip():
    """Return this machine's LAN IP (the one used for outbound traffic)."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        return None


def _find_ngrok():
    """Return path to ngrok binary: prefer the one next to server.py, then PATH."""
    local = os.path.join(HERE, "ngrok.exe" if sys.platform == "win32" else "ngrok")
    if os.path.exists(local):
        return local
    return "ngrok"


def _kill_existing_ngrok():
    """Terminate any ngrok processes already running (avoids port 4040 conflict)."""
    try:
        if sys.platform == "win32":
            subprocess.run(["taskkill", "/F", "/IM", "ngrok.exe"],
                           stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        else:
            subprocess.run(["pkill", "-f", "ngrok"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        time.sleep(0.8)  # let the port 4040 release
    except Exception:
        pass


def _start_ngrok(port):
    """Start ngrok and return (proc, https_url) or (None, None)."""
    _kill_existing_ngrok()
    cmd = _find_ngrok()
    try:
        proc = subprocess.Popen(
            [cmd, "http", str(port)],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            **_POPEN_KW,
        )
        for _ in range(24):
            time.sleep(0.5)
            # Check if ngrok exited early (auth error, port conflict, etc.)
            if proc.poll() is not None:
                err = proc.stderr.read(2048).decode("utf-8", errors="ignore").strip()
                print(f"  [ngrok] exited: {err[:300] or '(no output)'}")
                return None, None
            try:
                req = urllib.request.Request(
                    "http://127.0.0.1:4040/api/tunnels",
                    headers={"User-Agent": "WC2026-WarRoom/1.0"},
                )
                with urllib.request.urlopen(req, timeout=3) as r:
                    data = json.loads(r.read())
                for t in data.get("tunnels", []):
                    addr = t.get("config", {}).get("addr", "")
                    # Only accept a tunnel that actually points to our port
                    if t.get("proto") == "https" and str(port) in addr:
                        return proc, t["public_url"]
            except Exception:
                continue
        proc.terminate()
    except FileNotFoundError:
        pass
    return None, None


def _start_cloudflared(port):
    """Start a cloudflared quick tunnel and return (proc, https_url) or (None, None)."""
    try:
        proc = subprocess.Popen(
            ["cloudflared", "tunnel", "--url", f"http://localhost:{port}"],
            stdout=subprocess.DEVNULL, stderr=subprocess.PIPE,
            **_POPEN_KW,
        )
        for _ in range(40):
            line = proc.stderr.readline().decode("utf-8", errors="ignore")
            m = re.search(r"https://[a-z0-9-]+\.trycloudflare\.com", line)
            if m:
                return proc, m.group(0)
            if not line:
                break
        proc.terminate()
    except FileNotFoundError:
        pass
    return None, None


def _send_telegram_msg(text: str, cfg: dict, label: str = "Telegram"):
    """Envía un mensaje de texto libre al owner por Telegram."""
    token   = (cfg.get("telegram_bot_token") or "").strip()
    chat_id = (cfg.get("telegram_chat_id") or "").strip()
    if not token or not chat_id:
        print(f"  {label}: no configurado — agrega token y chat_id en Settings")
        return
    try:
        params = urllib.parse.urlencode({
            "chat_id":    chat_id,
            "text":       text,
            "parse_mode": "Markdown",
        })
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{token}/sendMessage?{params}",
            headers={"User-Agent": "ProGolCR/1.0"},
        )
        with urllib.request.urlopen(req, timeout=10) as r:
            body = r.read(256).decode("utf-8", errors="ignore")
            ok   = '"ok":true' in body
            print(f"  {label}: {'enviado OK' if ok else 'error — ' + body[:80]}")
    except Exception as e:
        print(f"  {label}: error — {e}")


def _send_telegram_notification(url: str, cfg: dict):
    """Avisa al owner por Telegram que el servidor arrancó con nueva URL."""
    msg = (
        f"🐕 *Ryder ProGol CR está online*\n"
        f"🔗 {url}\n"
        f"⚽ Listo para analizar partidos\n"
        f"🕐 {time.strftime('%H:%M')} hora local"
    )
    _send_telegram_msg(msg, cfg, label="Telegram")


# Keep alias for backward compat
_send_whatsapp_notification = _send_telegram_notification


def _start_localtunnel(port):
    """Start localtunnel via npx (no install needed) and return (proc, https_url) or (None, None)."""
    npx = "npx.cmd" if sys.platform == "win32" else "npx"
    try:
        proc = subprocess.Popen(
            [npx, "--yes", "localtunnel", "--port", str(port)],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            **_POPEN_KW,
        )
        for _ in range(30):
            time.sleep(0.5)
            if proc.poll() is not None:
                break
            line = proc.stdout.readline().decode("utf-8", errors="ignore")
            m = re.search(r"https://[a-z0-9-]+\.loca\.lt", line)
            if m:
                return proc, m.group(0)
        try:
            proc.terminate()
        except Exception:
            pass
    except FileNotFoundError:
        pass
    return None, None


# ── Auto post-match review ────────────────────────────────────────────────────

def _fuzzy_match_teams(name_a, name_b, threshold=0.60):
    """Return True if two team name strings are close enough to be the same team."""
    a = (name_a or "").lower().strip()
    b = (name_b or "").lower().strip()
    if a == b:
        return True
    # Substring check (handles "United States" vs "USA", "Korea Republic" vs "South Korea")
    if a in b or b in a:
        return True
    # Token overlap
    tok_a = set(a.split())
    tok_b = set(b.split())
    if tok_a and tok_b:
        overlap = len(tok_a & tok_b) / max(len(tok_a), len(tok_b))
        return overlap >= threshold
    return False


def _auto_review_finished_matches(fixtures):
    """
    Called every 15 min from the analyst refresh loop.
    Scans fixtures for status==Finished, looks up any saved prediction that
    matches home+away and doesn't yet have a review, then saves the review.
    """
    from storage.prediction_history import get_unreviewed_predictions, save_review
    from analysis.post_match import review_match

    # Collect all finished matches from fixtures dict
    finished = []
    for grp, fx_list in fixtures.items():
        for fx in fx_list:
            if fx.get("status") == "Finished":
                try:
                    sh = int(fx.get("scoreHome") or -1)
                    sa = int(fx.get("scoreAway") or -1)
                except (TypeError, ValueError):
                    sh = sa = -1
                if sh >= 0 and sa >= 0:
                    finished.append({
                        "home": fx["home"],
                        "away": fx["away"],
                        "score_home": sh,
                        "score_away": sa,
                        "kickoff": (fx.get("kickoff") or "")[:10] or datetime.date.today().isoformat(),
                    })

    if not finished:
        return

    # Get all predictions not yet reviewed (before or on today)
    unreviewed = get_unreviewed_predictions()
    if not unreviewed:
        return

    reviewed_count = 0
    for fx in finished:
        for pred_row in unreviewed:
            if (_fuzzy_match_teams(fx["home"], pred_row["home_team"]) and
                    _fuzzy_match_teams(fx["away"], pred_row["away_team"])):
                # Rebuild prediction dict from the stored row
                pred_dict = {
                    "prob": {
                        "home": pred_row.get("prob_home", 33),
                        "draw": pred_row.get("prob_draw", 33),
                        "away": pred_row.get("prob_away", 33),
                    },
                    "engine": {
                        "lam_home": pred_row.get("lam_home", 0),
                        "lam_away": pred_row.get("lam_away", 0),
                        "elo_home": pred_row.get("elo_home", 1600),
                        "elo_away": pred_row.get("elo_away", 1600),
                    },
                    "predictedScore": {"home": 0, "away": 0, "p": 0},
                }
                review = review_match(
                    pred_row["home_team"], pred_row["away_team"],
                    fx["score_home"], fx["score_away"],
                    pred_dict,
                    prediction_id=pred_row["id"],
                    reviewed_by="auto",
                )
                save_review(review)
                reviewed_count += 1
                print(
                    f"[auto-review] {pred_row['home_team']} vs {pred_row['away_team']} "
                    f"{fx['score_home']}-{fx['score_away']} — "
                    f"correct={bool(review['was_correct'])} brier={review['brier_contribution']} "
                    f"surprise={review['surprise_level']}"
                )
                break  # one review per finished fixture

    if reviewed_count:
        print(f"[auto-review] {reviewed_count} new review(s) saved")


# ── Background analyst context refresh (every 15 min) ──────────────────────────
_analyst_context_cache = {"standings": "", "fixtures": "", "updated_at": 0}
_analyst_context_lock = threading.Lock()


def _refresh_analyst_context():
    """Fetch live WC standings + fixtures and cache them for the analyst."""
    while True:
        try:
            standings = _fetch_wc_standings()
            fixtures  = _fetch_group_fixtures()

            s_lines = ["=== LIVE WC2026 STANDINGS (auto-refreshed) ==="]
            standings_dict = {g["name"]: g["teams"] for g in standings} if isinstance(standings, list) else standings
            for grp, teams in sorted(standings_dict.items()):
                s_lines.append(f"{grp}: " + " | ".join(
                    f"{t['name']} {t['pts']}pts {t['gp']}gp W{t['w']}D{t['d']}L{t['l']} GD{t['gd']}"
                    for t in teams
                ))

            f_lines = ["=== LIVE WC2026 FIXTURES (auto-refreshed) ==="]
            today = time.strftime("%Y-%m-%d")
            for grp, fx_list in sorted(fixtures.items()):
                for f in fx_list:
                    if f["status"] == "Finished":
                        f_lines.append(f"✓ {grp}: {f['home']} {f['scoreHome']}-{f['scoreAway']} {f['away']}")
                    elif f["status"] == "Live":
                        f_lines.append(f"🔴 LIVE {grp}: {f['home']} vs {f['away']}")
                    else:
                        date_part = (f.get("kickoff") or "")[:10]
                        if date_part == today or not date_part:
                            f_lines.append(f"📅 {grp}: {f['home']} vs {f['away']} — {f.get('kickoff','')}")

            with _analyst_context_lock:
                _analyst_context_cache["standings"] = "\n".join(s_lines)
                _analyst_context_cache["fixtures"]  = "\n".join(f_lines)
                _analyst_context_cache["updated_at"] = time.time()
            print(f"[analyst-refresh] context updated — {len(standings_dict)} groups, {sum(len(v) for v in fixtures.values())} fixtures")

            # Record source health for ESPN
            try:
                db.record_source_health(
                    "espn",
                    status="ok",
                    records_count=sum(len(v) for v in fixtures.values()),
                )
            except Exception:
                pass

            # Auto post-match review for finished matches with unreviewed predictions
            try:
                _auto_review_finished_matches(fixtures)
            except Exception as rev_err:
                print(f"[auto-review] error: {rev_err}")

            # Real-time Elo calibration — triggered whenever finished matches exist
            # Runs every 15 min so Ryder's Elo updates within 15 min of any match ending
            try:
                has_finished = any(
                    fx.get("status") == "Finished"
                    for fx_list in fixtures.values()
                    for fx in fx_list
                )
                if has_finished:
                    import calibrator as _cal
                    today_str = datetime.date.today().isoformat()
                    yesterday_str = (datetime.date.today() - datetime.timedelta(days=1)).isoformat()
                    total_calibrated = 0
                    for cal_date in [yesterday_str, today_str]:
                        cal_results = _cal.calibrate_date(cal_date, k_wc=32, verbose=False)
                        if cal_results:
                            total_calibrated += len(cal_results)
                            for r in cal_results:
                                print(
                                    f"[rt-calibration] {cal_date}: "
                                    f"{r['home']} {r['result']} {r['away']}  "
                                    f"Elo: {r['elo_home_before']}→{r['elo_home_after']} / "
                                    f"{r['elo_away_before']}→{r['elo_away_after']}  "
                                    f"Brier: {r['brier']}"
                                )
                    if total_calibrated:
                        print(f"[rt-calibration] {total_calibrated} match(es) calibrated in real-time")
                    else:
                        pass  # all matches already processed — silent
            except Exception as cal_err:
                print(f"[rt-calibration] error: {cal_err}")

            # Daily auto-generate scout report once per day
            today = time.strftime("%Y-%m-%d")
            try:
                latest = db.get_latest_scout_report()
                if not latest or latest.get("report_date") != today:
                    db.generate_scout_report(today)
                    print(f"[scout-report] daily report generated for {today}")
            except Exception as re:
                print(f"[scout-report] error generating daily report: {re}")
        except Exception as e:
            print(f"[analyst-refresh] error: {e}")
            try:
                db.record_source_health("espn", status="error", error_message=str(e))
            except Exception:
                pass

        # Daily cleanup of stale analytics data (runs once per loop regardless of errors)
        try:
            deleted = db.cleanup_old_analytics(days_to_keep=90)
            if any(v > 0 for v in deleted.values()):
                print(f"[cleanup] removed stale records: {deleted}")
        except Exception:
            pass

        time.sleep(900)  # 15 minutes


def get_analyst_context_snapshot():
    """Return the latest pre-fetched analyst context string."""
    with _analyst_context_lock:
        age = int(time.time() - _analyst_context_cache["updated_at"])
        parts = []
        if _analyst_context_cache["standings"]:
            parts.append(_analyst_context_cache["standings"])
        if _analyst_context_cache["fixtures"]:
            parts.append(_analyst_context_cache["fixtures"])
        if parts:
            ago = f"{age//60}m{age%60}s ago"
            return "\n\n".join(parts) + f"\n\n(Data fetched {ago})"
    return ""


def _backup_secrets():
    """Copy config.json, data/users.json, warroom.db into OneDrive as a ZIP."""
    try:
        onedrive = os.path.join(os.path.expanduser("~"), "OneDrive")
        if not os.path.isdir(onedrive):
            print("[backup] OneDrive folder not found — skipping backup")
            return
        backup_dir = os.path.join(onedrive, "ProGolCR_Backup")
        os.makedirs(backup_dir, exist_ok=True)
        stamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_path = os.path.join(backup_dir, f"progolcr_secrets_{stamp}.zip")
        files_to_backup = [
            os.path.join(HERE, "config.json"),
            os.path.join(HERE, "data", "users.json"),
            os.path.join(HERE, "warroom.db"),
        ]
        backed_up = []
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for fpath in files_to_backup:
                if os.path.exists(fpath):
                    zf.write(fpath, os.path.basename(fpath))
                    backed_up.append(os.path.basename(fpath))
        # Keep only the 5 most recent backups to avoid filling OneDrive
        all_zips = sorted([
            f for f in os.listdir(backup_dir) if f.startswith("progolcr_secrets_")
        ])
        for old in all_zips[:-5]:
            os.remove(os.path.join(backup_dir, old))
        print(f"[backup] OneDrive backup OK — {backed_up} → {zip_path}")
    except Exception as e:
        print(f"[backup] backup failed (non-fatal): {e}")


def main():
    cfg = load_config()
    if not os.path.exists(CONFIG_PATH):
        save_config(cfg)
    try:
        db.init_db()
    except Exception as e:
        print(f"[db] init failed: {e}")
    _init_users()  # create default users if not exist
    threading.Thread(target=_backup_secrets, daemon=True).start()
    # Start Telegram sales bot
    try:
        import telegram_bot as _tbot
        _tbot.start_bot_thread(cfg)
    except Exception as _e:
        print(f"[bot] could not start Telegram bot: {_e}")

    use_tunnel = "--tunnel" in sys.argv
    local_url = f"http://127.0.0.1:{PORT}"
    lan_ip = _get_lan_ip()
    lan_url = f"http://{lan_ip}:{PORT}" if lan_ip else None

    # Start background analyst context refresh (every 15 min)
    ctx_thread = threading.Thread(target=_refresh_analyst_context, daemon=True)
    ctx_thread.start()
    print("[analyst-refresh] background context refresh started (every 15 min)")

    print("=" * 56)
    print("  WORLD CUP 2026 -- WAR ROOM")
    print(f"  This PC:  {local_url}")
    if lan_url:
        print(f"  Network:  {lan_url}  (same WiFi)")
    print(f"  Anthropic key: {'set' if cfg.get('anthropic_api_key','').strip() else 'not set'}")
    print(f"  Model: {cfg.get('anthropic_model', DEFAULT_MODEL)}")
    print(f"  Database: {db.DB_PATH}")

    # Background Doradobet login (best-effort, non-blocking)
    def _db_login_bg():
        try:
            result = doradobet.login()
            if result.get("logged_in"):
                print(f"  Doradobet: logged in as {result['username']}")
            else:
                print(f"  Doradobet: {result.get('error','not configured')}")
        except Exception as e:
            print(f"  Doradobet: login error: {e}")
    threading.Thread(target=_db_login_bg, daemon=True).start()

    # Auto-calibrate Elo ratings from yesterday's and today's real results
    if _CALIBRATOR_AVAILABLE:
        def _bg_calibrate():
            try:
                r1 = _calibrator.calibrate_yesterday()
                r2 = _calibrator.calibrate_today()
                total = len(r1) + len(r2)
                if total:
                    print(f"  Calibrador ProGol™: {total} partido(s) actualizados en Elo")
                    for m in (r1 + r2)[:5]:
                        print(f"    ✓ {m['home']} {m['result']} {m['away']}  Brier:{m.get('brier','?')}")
            except Exception as e:
                print(f"  Calibrador ProGol™: {e}")
        threading.Thread(target=_bg_calibrate, daemon=True).start()

    # Start the HTTP server in a background thread so we can also start the tunnel
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    srv_thread = threading.Thread(target=server.serve_forever, daemon=True)
    srv_thread.start()
    _start_auto_resolve_thread()

    try:
        threading.Timer(0.8, lambda: webbrowser.open(local_url)).start()
    except Exception:
        pass

    tunnel_proc = None
    if use_tunnel:
        print("  Tunnel:   starting...")
        tunnel_proc, tunnel_url = _start_ngrok(PORT)
        if not tunnel_url:
            tunnel_proc, tunnel_url = _start_cloudflared(PORT)
        if not tunnel_url:
            print("  Tunnel:   ngrok/cloudflared not found — trying localtunnel (npx)...")
            tunnel_proc, tunnel_url = _start_localtunnel(PORT)
        if tunnel_url:
            access_url = tunnel_url  # no token needed — users log in with username/password
            global _TUNNEL_URL; _TUNNEL_URL = access_url
            # Persist tunnel URL so telegram_bot can read it via /link command
            try:
                _cfg = load_config()
                _cfg["current_tunnel_url"] = access_url
                with open(CONFIG_PATH, "w") as _f:
                    json.dump(_cfg, _f, indent=2)
            except Exception:
                pass
            print(f"  Tunnel:   {access_url}")
            threading.Thread(target=_send_whatsapp_notification, args=(access_url, cfg), daemon=True).start()
            print("            Open this URL on any device, any network")
            print("            (keep this window open to stay online)")
        else:
            print("  Tunnel:   FAILED -- ninguna herramienta de tunnel disponible.")
            print("  Opcion 1 (facil): instala ngrok -> https://ngrok.com/download")
            print("  Opcion 2:         instala cloudflared -> https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/")
            print("  Opcion 3 (mejor): despliega en VPS con dominio propio")
            print("  Luego vuelve a correr: python server.py --tunnel")

    print("  Press Ctrl+C to stop.")
    print("=" * 56)

    def _tunnel_watchdog(port, cfg, initial_proc):
        """Monitorea el túnel cada 30s. Si cae, lo reinicia y avisa por Telegram."""
        proc  = initial_proc
        fails = 0
        while True:
            time.sleep(30)
            # ¿Sigue vivo el proceso?
            alive = proc is not None and proc.poll() is None
            # ¿Responde el URL actual?
            reachable = False
            global _TUNNEL_URL
            if _TUNNEL_URL:
                try:
                    req = urllib.request.Request(
                        _TUNNEL_URL, headers={"User-Agent": "ProGolCR-watchdog/1.0"})
                    with urllib.request.urlopen(req, timeout=8) as r:
                        reachable = r.status < 500
                except Exception:
                    reachable = False

            if alive and reachable:
                fails = 0
                continue  # todo bien

            fails += 1
            if fails < 2:
                continue  # un fallo puntual, esperamos confirmación

            # Túnel caído — reiniciar
            print(f"[watchdog] Túnel caído (fails={fails}), reiniciando...")
            if proc:
                try: proc.terminate()
                except Exception: pass

            new_proc, new_url = None, None
            for starter in [_start_ngrok, _start_cloudflared, _start_localtunnel]:
                try:
                    new_proc, new_url = starter(port)
                    if new_url: break
                except Exception:
                    continue

            if new_url:
                _TUNNEL_URL = new_url
                proc   = new_proc
                fails  = 0
                print(f"[watchdog] Túnel restaurado: {new_url}")
                # Persistir nueva URL en config.json
                try:
                    _wcfg = load_config()
                    _wcfg["current_tunnel_url"] = new_url
                    with open(CONFIG_PATH, "w") as _wf:
                        json.dump(_wcfg, _wf, indent=2)
                except Exception:
                    pass
                _send_telegram_msg(
                    f"🔄 *ProGol CR — túnel reiniciado*\n🔗 {new_url}\n🕐 {time.strftime('%H:%M')} hora local",
                    cfg)
            else:
                print("[watchdog] No se pudo reiniciar el túnel — reintentando en 30s")
                _send_telegram_msg(
                    "⚠️ *ProGol CR: túnel caído*\nNo se pudo reiniciar automáticamente.\nRevisa la PC.",
                    cfg)
                fails = 0  # reset para no spamear

    try:
        if use_tunnel and tunnel_proc:
            wdog = threading.Thread(
                target=_tunnel_watchdog,
                args=(PORT, cfg, tunnel_proc),
                daemon=True)
            wdog.start()
            print("[watchdog] Monitor de túnel activo (revisa cada 30s)")

        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\nShutting down. Goodbye!")
        server.shutdown()
        if tunnel_proc:
            try:
                tunnel_proc.terminate()
            except Exception:
                pass


if __name__ == "__main__":
    main()
