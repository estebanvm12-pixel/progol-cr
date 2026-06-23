"""
Scraper de stats desde Wikipedia — gratis, sin bloqueos, tablas bien estructuradas.
Busca la tabla de estadisticas de carrera de cada jugador y extrae temporada 2024-25.
"""
import json, os, re, time, urllib.request, urllib.parse
from html.parser import HTMLParser

ROOT        = os.path.join(os.path.dirname(__file__), "..")
SQUADS_FILE = os.path.join(ROOT, "data", "wc2026_squads.json")
OUTPUT_FILE = os.path.join(ROOT, "data", "players_stats.json")
UA = "ProGolCR/1.0 (worldcup-warroom; educational project)"

def wiki_search(name):
    """Search Wikipedia for a footballer and return the article URL."""
    params = urllib.parse.urlencode({
        "action": "query", "list": "search", "srsearch": f"{name} footballer",
        "format": "json", "srlimit": 3
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=15) as r:
        data = json.loads(r.read())
    results = data.get("query", {}).get("search", [])
    if results:
        return results[0]["title"]
    return None

def wiki_get_html(title):
    """Get full HTML of a Wikipedia article."""
    params = urllib.parse.urlencode({
        "action": "parse", "page": title, "prop": "text",
        "format": "json", "disabletoc": 1
    })
    url = f"https://en.wikipedia.org/w/api.php?{params}"
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=20) as r:
        data = json.loads(r.read())
    return data.get("parse", {}).get("text", {}).get("*", "")

def extract_stats_from_html(html, player_name):
    """Extract club career stats table — goals, appearances, seasons."""
    # Remove HTML tags for text extraction
    clean = re.sub(r'<[^>]+>', ' ', html)
    clean = re.sub(r'&amp;', '&', clean)
    clean = re.sub(r'&nbsp;', ' ', clean)
    clean = re.sub(r'\s+', ' ', clean)

    # Look for 2024-25 season stats in career table
    # Pattern: season year near numbers that look like appearances/goals
    patterns_24_25 = [
        r'2024.{0,5}25.{0,200}?(\d{1,3})\s*\(?(\d{1,3})?\)?',  # "2024-25  38 (12)"
    ]

    # Try to find infobox stats (birth date, position, clubs)
    info = {}

    # Birth date
    bdate = re.search(r'born\s*\((\d{4}-\d{2}-\d{2})\)', clean, re.IGNORECASE)
    if bdate:
        info["birth_date"] = bdate.group(1)

    # Position
    pos_m = re.search(r'Position\s*([A-Za-z\s/]+?)(?:Club|National|Career)', clean)
    if pos_m:
        info["wiki_position"] = pos_m.group(1).strip()[:30]

    # Current club
    club_m = re.search(r'Current club\s*([A-Za-z\s\.]+?)(?:\n|Years|Number)', clean)
    if club_m:
        info["wiki_club"] = club_m.group(1).strip()[:40]

    # Look for season stats table rows with 2024
    # Wikipedia career stats: Season | Club | League | Apps | Goals
    rows_24 = re.findall(r'2024.{0,3}25\s+([A-Za-z\s\.]+?)\s+(\d{1,3})\s*\(?(\d*)?\)?', clean)
    if rows_24:
        best = rows_24[0]
        info["wiki_season"] = "2024-25"
        info["wiki_club_stat"] = best[0].strip()[:40]
        info["wiki_apps"] = int(best[1]) if best[1] else None
        info["wiki_goals"] = int(best[2]) if best[2] else 0

    return info

def load_output():
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_output(data):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    import sys
    with open(SQUADS_FILE, encoding="utf-8") as f:
        squads = json.load(f)["teams"]

    filter_team = None
    args = sys.argv[1:]
    for i, a in enumerate(args):
        if a == "--team" and i+1 < len(args):
            filter_team = args[i+1].lower()

    out = load_output()
    enriched = 0

    for nation, tdata in squads.items():
        if filter_team and filter_team not in nation.lower():
            continue
        print(f"\n[{nation}]")
        for p in tdata["players"]:
            key = f"{nation}|{p['name']}"
            entry = out.get(key, {})
            # Skip if already has good stats
            if entry.get("stats") and entry["stats"].get("goals") is not None:
                print(f"  [skip] {p['name']}")
                continue

            print(f"  Wikipedia: {p['name']}...", end=" ", flush=True)
            try:
                title = wiki_search(p["name"])
                if not title:
                    print("no encontrado")
                    continue
                time.sleep(0.5)
                html = wiki_get_html(title)
                info = extract_stats_from_html(html, p["name"])

                if key not in out:
                    out[key] = {"name": p["name"], "nation": nation, "pos": p.get("pos"),
                                "club": p.get("club"), "league": p.get("league"), "stats": None}
                out[key]["wiki"] = info
                enriched += 1

                apps  = info.get("wiki_apps")
                goals = info.get("wiki_goals")
                print(f"OK | {info.get('wiki_season','?')} | {apps} partidos | {goals} goles")
                save_output(out)
                time.sleep(3.5)
            except Exception as e:
                print(f"ERROR: {e}")

    print(f"\nListo - {enriched} jugadores enriquecidos con Wikipedia")

if __name__ == "__main__":
    main()
