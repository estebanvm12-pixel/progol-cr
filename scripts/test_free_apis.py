"""Test all free football data sources."""
import json, urllib.request, urllib.parse, urllib.error

with open("config.json", encoding="utf-8") as f:
    cfg = json.load(f)

def get(url, headers=None):
    req = urllib.request.Request(url, headers=headers or {"User-Agent": "ProGolCR/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read()), r.status
    except urllib.error.HTTPError as e:
        return {"error": e.code, "msg": e.read().decode()[:200]}, e.code
    except Exception as e:
        return {"error": str(e)}, 0

# 1. TheSportsDB
print("=== TheSportsDB ===")
sdb_key = cfg.get("sportsdb_key", "").strip()
# Free tier uses key "3" or actual key
url = f"https://www.thesportsdb.com/api/v1/json/{sdb_key}/searchplayers.php?p=Mbappe"
r, code = get(url)
print(f"Status: {code}")
players = r.get("player", [])
if players:
    p = players[0]
    print(f"  Found: {p.get('strPlayer')} | Club: {p.get('strTeam')} | Nationality: {p.get('strNationality')}")
    print(f"  Keys available: {[k for k in p.keys() if p[k]][:15]}")
else:
    print("  No results:", str(r)[:200])

# 2. football-data.org (free tier)
print("\n=== football-data.org ===")
url2 = "https://api.football-data.org/v4/competitions/WC/teams"
r2, code2 = get(url2, {"X-Auth-Token": "dummy", "User-Agent": "ProGolCR/1.0"})
print(f"Status: {code2} | Keys: {list(r2.keys())[:5]}")

# 3. API-Football remaining requests
print("\n=== API-Football quota check ===")
af_key = cfg.get("apifootball_key", "").strip()
url3 = "https://v3.football.api-sports.io/status"
r3, code3 = get(url3, {"x-apisports-key": af_key})
reqs = r3.get("response", {})
if isinstance(reqs, list) and reqs:
    reqs = reqs[0]
req_info = reqs.get("requests", {}) if isinstance(reqs, dict) else {}
print(f"  Status: {code3} | Requests used today: {req_info.get('current','?')} / {req_info.get('limit_day','?')}")

# 4. Open-meteo style: transfermarkt unofficial
print("\n=== Sofascore unofficial ===")
url4 = "https://api.sofascore.com/api/v1/player/search?q=Vinicius+Junior"
r4, code4 = get(url4, {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
print(f"  Status: {code4} | Keys: {list(r4.keys())[:5]}")

# 5. ESPN API (unofficial but public)
print("\n=== ESPN unofficial API ===")
url5 = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/summary"
r5, code5 = get(url5)
print(f"  Status: {code5} | Keys: {list(r5.keys())[:5]}")

# 6. FIFA World Cup 2026 official data endpoint
print("\n=== FIFA stats unofficial ===")
url6 = "https://api.fifa.com/api/v3/players?IdSeason=2026&IdCompetition=17"
r6, code6 = get(url6, {"User-Agent": "Mozilla/5.0", "Origin": "https://www.fifa.com"})
print(f"  Status: {code6} | Keys: {list(r6.keys())[:5] if isinstance(r6, dict) else str(r6)[:100]}")
