"""
Pipeline completo de stats de jugadores — Wikipedia + Chrome fallback.
Corre todos los equipos del Mundial 2026, reintenta con backoff en 429.
Guarda en data/players_stats.json de forma incremental.

Uso:
  python scripts/fetch_player_stats_full.py
  python scripts/fetch_player_stats_full.py --team Brazil
  python scripts/fetch_player_stats_full.py --force   # reescribir todo
"""
import json, os, re, sys, time, random, urllib.request, urllib.parse, urllib.error

ROOT        = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SQUADS_FILE = os.path.join(ROOT, "data", "wc2026_squads.json")
OUTPUT_FILE = os.path.join(ROOT, "data", "players_stats.json")
UA = "ProGolCR/1.0 (worldcup research project; contact estebanvm12@gmail.com)"

# ── HTTP helper with retry + exponential backoff ─────────────────────────────
def http_get(url, retries=5):
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": UA,
                "Accept-Language": "en-US,en;q=0.9",
                "Accept": "application/json",
            })
            with urllib.request.urlopen(req, timeout=20) as r:
                return r.read()
        except urllib.error.HTTPError as e:
            if e.code == 429:
                wait = (2 ** attempt) * 3 + random.uniform(1, 3)
                print(f"    [429] rate limited, esperando {wait:.0f}s...", flush=True)
                time.sleep(wait)
            elif e.code in (404, 400):
                return None
            else:
                raise
        except Exception as e:
            if attempt < retries - 1:
                time.sleep(3)
            else:
                raise
    return None

# ── Wikipedia API ─────────────────────────────────────────────────────────────
def wiki_search(name):
    params = urllib.parse.urlencode({
        "action": "query", "list": "search",
        "srsearch": f"{name} footballer soccer",
        "format": "json", "srlimit": 3, "srprop": "size"
    })
    raw = http_get(f"https://en.wikipedia.org/w/api.php?{params}")
    if not raw:
        return None
    d = json.loads(raw)
    results = d.get("query", {}).get("search", [])
    return results[0]["title"] if results else None

def wiki_page_text(title):
    params = urllib.parse.urlencode({
        "action": "query", "titles": title,
        "prop": "revisions", "rvprop": "content", "rvslots": "main",
        "format": "json", "formatversion": "2"
    })
    raw = http_get(f"https://en.wikipedia.org/w/api.php?{params}")
    if not raw:
        return ""
    d = json.loads(raw)
    pages = d.get("query", {}).get("pages", [])
    if pages:
        return pages[0].get("revisions", [{}])[0].get("slots", {}).get("main", {}).get("content", "")
    return ""

def parse_wikitext_stats(text, name):
    """Extract club career stats from Wikipedia wikitext markup."""
    info = {}

    # Born date
    m = re.search(r'birth_date\s*=.*?(\d{4})-(\d{2})-(\d{2})', text)
    if m:
        info["birth_date"] = f"{m.group(1)}-{m.group(2)}-{m.group(3)}"

    # Position
    m = re.search(r'position\s*=\s*([^\n\|]+)', text, re.IGNORECASE)
    if m:
        info["position"] = re.sub(r'\[\[|\]\]|\{\{[^}]+\}\}', '', m.group(1)).strip()[:30]

    # Current club from infobox
    m = re.search(r'club\s*=\s*\[\[([^\|\]]+)', text, re.IGNORECASE)
    if m:
        info["current_club"] = m.group(1).strip()

    # Career stats table — look for 2024-25 row
    # Format: | 2024–25 || [[Club]] || League || Apps || (Gls)
    patterns = [
        r'\|\s*2024.{1,3}25\s*\|\|[^\|]*\|\|[^\|]*\|\|\s*(\d+)\s*\|\|\s*\(?(\d+)\)?',
        r'2024.{1,3}25.*?(\d{1,3})\s*\|\|\s*\(?(\d+)\)?',
    ]
    for pat in patterns:
        m = re.search(pat, text)
        if m:
            apps = int(m.group(1))
            goals = int(m.group(2)) if m.group(2) else 0
            if apps > 0:
                info["wiki_season"] = "2024-25"
                info["wiki_apps"]   = apps
                info["wiki_goals"]  = goals
                break

    # Also try 2023-24 as fallback
    if "wiki_apps" not in info:
        for pat in [
            r'\|\s*2023.{1,3}24\s*\|\|[^\|]*\|\|[^\|]*\|\|\s*(\d+)\s*\|\|\s*\(?(\d+)\)?',
        ]:
            m = re.search(pat, text)
            if m:
                apps = int(m.group(1))
                goals = int(m.group(2)) if m.group(2) else 0
                if apps > 0:
                    info["wiki_season"] = "2023-24"
                    info["wiki_apps"]   = apps
                    info["wiki_goals"]  = goals
                    break

    return info

# ── Sofascore unofficial API ──────────────────────────────────────────────────
def sofascore_search(name):
    """Try Sofascore unofficial API for player stats."""
    try:
        encoded = urllib.parse.quote(name)
        raw = http_get(
            f"https://api.sofascore.com/api/v1/search/all?q={encoded}",
        )
        if not raw:
            return None
        d = json.loads(raw)
        players = [r for r in d.get("results", []) if r.get("type") == "player"]
        if not players:
            return None
        pid = players[0].get("entity", {}).get("id")
        if not pid:
            return None
        # Get player stats for last season
        raw2 = http_get(f"https://api.sofascore.com/api/v1/player/{pid}/statistics/seasons")
        if not raw2:
            return None
        seasons = json.loads(raw2).get("statistics", [])
        # Find 2024-25
        for s in seasons:
            yr = str(s.get("season", {}).get("year", ""))
            if "2024" in yr or "2025" in yr:
                stats = s.get("statistics", {})
                return {
                    "source": "sofascore",
                    "season": yr,
                    "mp": stats.get("appearances"),
                    "goals": stats.get("goals"),
                    "assists": stats.get("goalAssist"),
                    "yellow_cards": stats.get("yellowCards"),
                    "red_cards": stats.get("redCards"),
                    "rating": stats.get("rating"),
                }
        return None
    except Exception:
        return None

# ── ESPN API (unofficial, public, no key) ────────────────────────────────────
def espn_player_search(name):
    """Search ESPN for a player and get basic stats."""
    try:
        encoded = urllib.parse.quote(name)
        raw = http_get(
            f"https://site.api.espn.com/apis/common/v3/search?query={encoded}&limit=3&type=player&sport=soccer"
        )
        if not raw:
            return None
        d = json.loads(raw)
        items = d.get("items", [])
        if not items:
            return None
        # Return basic info
        p = items[0]
        return {
            "source": "espn",
            "name": p.get("displayName"),
            "team": p.get("teamName"),
            "position": p.get("positionName"),
        }
    except Exception:
        return None

# ── TheSportsDB (already have key) ───────────────────────────────────────────
def sportsdb_player(name, key):
    try:
        encoded = urllib.parse.quote(name)
        raw = http_get(f"https://www.thesportsdb.com/api/v1/json/{key}/searchplayers.php?p={encoded}")
        if not raw:
            return None
        d = json.loads(raw)
        players = d.get("player", [])
        if not players:
            return None
        p = players[0]
        return {
            "source": "sportsdb",
            "name": p.get("strPlayer"),
            "club": p.get("strTeam"),
            "nationality": p.get("strNationality"),
            "position": p.get("strPosition"),
            "birth_date": p.get("dateBorn"),
            "thumb": p.get("strThumb"),
        }
    except Exception:
        return None

# ── Main pipeline ─────────────────────────────────────────────────────────────
def load_output():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_output(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def process_player(nation, pdata, out, sdb_key, force=False):
    name = pdata["name"]
    key  = f"{nation}|{name}"
    entry = out.get(key, {})

    # Skip if already has good full stats (from curated populate_player_stats.py)
    if not force and entry.get("stats") and entry["stats"].get("confidence") in ("high", "medium"):
        return "skip"

    # Skip if wiki data already good
    has_wiki = entry.get("wiki", {}).get("wiki_apps")
    has_sdb  = entry.get("sportsdb")
    if not force and has_wiki and has_sdb:
        return "skip"

    if key not in out:
        out[key] = {
            "name": name, "nation": nation,
            "pos": pdata.get("pos"), "club": pdata.get("club"),
            "league": pdata.get("league"), "stats": None
        }

    result_parts = []

    # 1. TheSportsDB — profile data (fast, no rate limit issues)
    if not has_sdb:
        sdb = sportsdb_player(name, sdb_key)
        if sdb:
            out[key]["sportsdb"] = sdb
            result_parts.append(f"SDB:{sdb.get('club','?')}")
        time.sleep(0.3)

    # 2. Wikipedia — career stats
    if not has_wiki:
        try:
            title = wiki_search(name)
            if title:
                time.sleep(2)
                text = wiki_page_text(title)
                if text:
                    wiki_info = parse_wikitext_stats(text, name)
                    out[key]["wiki"] = wiki_info
                    if wiki_info.get("wiki_apps"):
                        result_parts.append(f"Wiki:{wiki_info['wiki_season']} {wiki_info['wiki_apps']}apps {wiki_info['wiki_goals']}G")
                    else:
                        result_parts.append("Wiki:perfil")
        except Exception as e:
            result_parts.append(f"Wiki:err({str(e)[:30]})")
        time.sleep(2.5)

    # 3. Sofascore — detailed stats (if no curated stats)
    if not entry.get("stats") or not entry["stats"].get("goals"):
        ss = sofascore_search(name)
        if ss:
            if not out[key].get("stats"):
                out[key]["stats"] = {}
            out[key]["stats"].update({
                "season": ss.get("season"),
                "mp": ss.get("mp"),
                "goals": ss.get("goals"),
                "assists": ss.get("assists"),
                "yellow_cards": ss.get("yellow_cards"),
                "red_cards": ss.get("red_cards"),
                "source": "sofascore",
                "confidence": "medium",
            })
            result_parts.append(f"SS:{ss.get('mp')}apps {ss.get('goals')}G")
        time.sleep(1)

    return " | ".join(result_parts) if result_parts else "no_new_data"

def main():
    with open(SQUADS_FILE, encoding="utf-8") as f:
        squads = json.load(f)["teams"]

    with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
        cfg = json.load(f)
    sdb_key = cfg.get("sportsdb_key", "3").strip()

    args = sys.argv[1:]
    filter_team = None
    force = "--force" in args
    for i, a in enumerate(args):
        if a == "--team" and i + 1 < len(args):
            filter_team = args[i + 1].lower()

    out = load_output()
    processed = 0

    for nation, tdata in squads.items():
        if filter_team and filter_team not in nation.lower():
            continue
        players = tdata["players"]
        print(f"\n[{nation}] — {len(players)} jugadores")
        for p in players:
            print(f"  {p['name']}...", end=" ", flush=True)
            try:
                result = process_player(nation, p, out, sdb_key, force)
                print(result)
                processed += 1
            except Exception as e:
                print(f"ERROR: {e}")
            save_output(out)

    # Final stats
    total = len(out)
    with_stats = len([v for v in out.values() if v.get("stats") and v["stats"].get("goals") is not None])
    with_wiki  = len([v for v in out.values() if v.get("wiki", {}).get("wiki_apps")])
    with_sdb   = len([v for v in out.values() if v.get("sportsdb")])
    print(f"\nListo — {total} jugadores totales | stats:{with_stats} | wiki:{with_wiki} | sportsdb:{with_sdb}")

if __name__ == "__main__":
    main()
