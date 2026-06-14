"""
doradobet.py — Doradobet account integration via VirtualSoft Lobby API.

Handles login, session caching, and account status for the War Room.
IMPORTANT: Read-only. Never places bets or moves money.
"""
import json
import os
import time
import urllib.request
import urllib.parse
import urllib.error

HERE = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(HERE, ".env.txt")
SESSION_PATH = os.path.join(HERE, "doradobet_session.json")

VS_LOBBY = "https://partnerapi.virtualsoft.tech/Lobby/Api"
INTEGRATION = "doradobetcr"
UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# In-memory session cache
_session = {
    "auth_token": "",
    "user_id": "",
    "username": "",
    "logged_in": False,
    "login_ts": 0,
    "error": "",
}

SESSION_TTL = 3600  # re-login after 1 hour


def _read_creds():
    creds = {}
    if not os.path.exists(ENV_PATH):
        return creds
    with open(ENV_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                k, v = line.split("=", 1)
                k, v = k.strip(), v.strip()
                if v:
                    creds[k] = v
    return creds


def _vs_post(payload, auth_token=""):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(VS_LOBBY, data=data, method="POST")
    req.add_header("Content-Type", "application/json")
    req.add_header("User-Agent", UA)
    req.add_header("Origin", "https://doradobet.com")
    req.add_header("Referer", "https://doradobet.com/")
    if auth_token:
        req.add_header("swarm-session", auth_token)
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except Exception as e:
        return {"error": str(e)}


def _save_session():
    try:
        with open(SESSION_PATH, "w") as f:
            json.dump(_session, f)
    except Exception:
        pass


def _load_saved_session():
    try:
        if os.path.exists(SESSION_PATH):
            with open(SESSION_PATH) as f:
                saved = json.load(f)
            if saved.get("logged_in") and time.time() - saved.get("login_ts", 0) < SESSION_TTL:
                _session.update(saved)
                return True
    except Exception:
        pass
    return False


def login():
    """Login to Doradobet and cache the session. Returns {logged_in, username, error}."""
    global _session

    # Use cached session if still fresh
    if _session["logged_in"] and time.time() - _session["login_ts"] < SESSION_TTL:
        return {"logged_in": True, "username": _session["username"], "user_id": _session["user_id"]}

    # Try saved session file
    if _load_saved_session():
        return {"logged_in": True, "username": _session["username"], "user_id": _session["user_id"]}

    creds = _read_creds()
    username = creds.get("DORADOBET_USERNAME", "")
    password = creds.get("DORADOBET_PASSWORD", "")

    if not username or not password:
        _session["error"] = "Credentials not set in .env.txt"
        return {"logged_in": False, "error": _session["error"]}

    resp = _vs_post({
        "command": "login",
        "params": {
            "username": username,
            "password": password,
            "typeApp": 1,
            "in_app": True,
            "device_fount": "web",
            "site_id": 0,
            "isMobile": "",
            "country": "cr",
            "vrsn": "1781214593",
        },
        "rid": "wr_login",
        "wid": "warroom",
    })

    if resp.get("code") == 0:
        d = resp.get("data", {})
        _session.update({
            "auth_token": d.get("auth_token", ""),
            "user_id": d.get("user_id", ""),
            "username": username,
            "logged_in": True,
            "login_ts": time.time(),
            "error": "",
        })
        _save_session()
        return {"logged_in": True, "username": username, "user_id": _session["user_id"]}
    elif resp.get("code") == 1811:
        # Rate limited — if we have a cached session use it
        if _session["auth_token"]:
            return {"logged_in": True, "username": _session["username"], "user_id": _session["user_id"]}
        err = "Rate limited — try again in 60s"
        _session["error"] = err
        return {"logged_in": False, "error": err}
    else:
        err = resp.get("error") or resp.get("msg") or f"code {resp.get('code')}"
        _session["error"] = str(err)
        return {"logged_in": False, "error": str(err)}


def status():
    """Return current session status without triggering a new login."""
    if _session["logged_in"] and time.time() - _session["login_ts"] < SESSION_TTL:
        return {
            "logged_in": True,
            "username": _session["username"],
            "user_id": _session["user_id"],
        }
    # Try loaded session silently
    if _load_saved_session():
        return {
            "logged_in": True,
            "username": _session["username"],
            "user_id": _session["user_id"],
        }
    return {"logged_in": False, "username": "", "user_id": ""}


def ensure_logged_in():
    """Login if not already. Returns True on success."""
    result = login()
    return result.get("logged_in", False)


def get_account_balance():
    """Fetch the user's Doradobet balance. Returns {balance, currency} or {}."""
    auth = _session.get("auth_token", "")
    if not auth:
        return {}
    resp = _vs_post({
        "command": "get_user",
        "params": {"auth_token": auth},
        "rid": "wr_balance",
        "wid": "warroom",
    }, auth_token=auth)
    if resp.get("code") == 0:
        d = resp.get("data") or {}
        return {
            "balance": d.get("balance", d.get("Balance")),
            "currency": d.get("currency_name") or d.get("CurrencyName") or "CRC",
        }
    return {}


def match_doradobet_url(home: str, away: str) -> str:
    """Return the Doradobet deep link for a World Cup match."""
    return "https://doradobet.com/deportes/soccer/world/world-cup"
