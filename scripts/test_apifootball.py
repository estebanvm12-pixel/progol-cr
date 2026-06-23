"""Test API-Football endpoints available with our key."""
import json, urllib.request, urllib.parse

with open("config.json") as f:
    cfg = json.load(f)

API_KEY = cfg["apifootball_key"].strip()
BASE = "https://v3.football.api-sports.io"

HEADERS = {
    "x-apisports-key": API_KEY,
    "Accept": "application/json",
}

def get(endpoint, params=None):
    url = f"{BASE}/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url, headers=HEADERS)
    with urllib.request.urlopen(req, timeout=15) as r:
        body = r.read()
        return json.loads(body)

# 1. Account status
print("=== Account Status ===")
try:
    r = get("status")
    print(json.dumps(r, indent=2)[:800])
except Exception as e:
    print("  Error:", e)

# 2. World Cup leagues
print("\n=== World Cup 2026 league ===")
try:
    r = get("leagues", {"search": "World Cup"})
    print(json.dumps(r.get("response", [])[:3], indent=2)[:800])
except Exception as e:
    print("  Error:", e)

# 3. Test player search (Neymar)
print("\n=== Player: Neymar ===")
try:
    r = get("players", {"search": "Neymar", "league": "1", "season": "2024"})
    print("errors:", r.get("errors"))
    print("results:", r.get("results"))
    resp = r.get("response", [])
    if resp:
        p = resp[0]
        print(json.dumps(p, indent=2)[:600])
except Exception as e:
    print("  Error:", e)
