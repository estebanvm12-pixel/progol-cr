"""
Scraper de stats EN VIVO del Mundial 2026 — goles y asistencias del torneo.
Fuente: ESPN API + khelnow fallback.
Fusiona con players_stats.json para dar contexto completo a Ryder.

Uso: python scripts/fetch_wc2026_live_stats.py
"""
import json, os, re, time, urllib.request, urllib.parse

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
TOURNAMENT_FILE = os.path.join(ROOT, "data", "wc2026_tournament_stats.json")
PLAYERS_FILE    = os.path.join(ROOT, "data", "players_stats.json")
UA = "ProGolCR/1.0 (worldcup-warroom)"


def _get(url):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception:
        return None


def fetch_espn_scorers():
    """Fetch top scorers from ESPN WC2026 stats API."""
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard"
    data = _get(url)
    if not data:
        return []

    scorers = []
    for event in data.get("events", []):
        for comp in event.get("competitions", []):
            for competitor in comp.get("competitors", []):
                team = competitor.get("team", {}).get("displayName", "")
                for stat in competitor.get("statistics", []):
                    pass  # ESPN scoreboard doesn't have player stats
    return scorers


def fetch_espn_leaders():
    """Fetch goal/assist leaders from ESPN WC2026 leaders API."""
    results = {"scorers": [], "assisters": []}

    for cat, key in [("goals", "scorers"), ("assists", "assisters")]:
        url = f"https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/leaders?limit=30&stat={cat}"
        data = _get(url)
        if not data:
            continue
        for leader in data.get("leaders", []):
            for item in leader.get("leaders", []):
                athlete = item.get("athlete", {})
                team_obj = item.get("team", {})
                results[key].append({
                    "player": athlete.get("displayName", ""),
                    "team": team_obj.get("displayName", ""),
                    "value": item.get("value", 0),
                })
    return results


def load_tournament():
    try:
        with open(TOURNAMENT_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"top_scorers": [], "top_assists": []}


def save_tournament(data):
    with open(TOURNAMENT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def load_players():
    try:
        with open(PLAYERS_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_players(data):
    with open(PLAYERS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def merge_tournament_stats_into_players(tournament, players):
    """Add WC2026 tournament goals/assists into players_stats.json entries."""
    # Build lookup: player name (lower) -> {goals, assists}
    wc_goals = {}
    wc_assists = {}

    for s in tournament.get("top_scorers", []):
        name = s["player"].lower()
        wc_goals[name] = s.get("goals", 0)

    for s in tournament.get("top_assists", []):
        name = s["player"].lower()
        wc_assists[name] = s.get("assists", 0)

    updated = 0
    for key, entry in players.items():
        pname = entry.get("name", "").lower()
        g = wc_goals.get(pname, 0)
        a = wc_assists.get(pname, 0)
        if g > 0 or a > 0:
            if not entry.get("wc2026"):
                entry["wc2026"] = {}
            entry["wc2026"]["goals"]   = g
            entry["wc2026"]["assists"] = a
            entry["wc2026"]["updated"] = time.strftime("%Y-%m-%d")
            updated += 1

    return updated


def main():
    print("Fetching WC2026 live stats from ESPN...")
    leaders = fetch_espn_leaders()

    tournament = load_tournament()
    import datetime
    tournament["_meta"]["updated"] = datetime.date.today().isoformat()

    if leaders["scorers"]:
        print(f"  ESPN: {len(leaders['scorers'])} scorers, {len(leaders['assisters'])} assisters")
        # Merge ESPN data over existing manual data
        existing_names = {s["player"].lower() for s in tournament["top_scorers"]}
        for s in leaders["scorers"]:
            name = s["player"]
            if name.lower() not in existing_names:
                tournament["top_scorers"].append({
                    "player": name,
                    "team": s["team"],
                    "goals": int(s["value"]),
                    "assists": 0,
                })
            else:
                # Update goal count
                for ts in tournament["top_scorers"]:
                    if ts["player"].lower() == name.lower():
                        ts["goals"] = max(ts["goals"], int(s["value"]))
        save_tournament(tournament)
        print("  Tournament stats updated.")
    else:
        print("  ESPN leaders API not available — keeping existing manual data.")

    # Merge into players_stats.json
    players = load_players()
    updated = merge_tournament_stats_into_players(tournament, players)
    save_players(players)
    print(f"  {updated} jugadores con goles/asistencias del Mundial 2026 en players_stats.json")

    # Print current leaders
    print("\n=== LÍDERES ACTUALES WC2026 ===")
    print("Goleadores:")
    for s in sorted(tournament["top_scorers"], key=lambda x: x["goals"], reverse=True)[:10]:
        print(f"  {s['player']} ({s['team']}): {s['goals']}G")
    print("Asistentes:")
    for s in sorted(tournament.get("top_assists", []), key=lambda x: x["assists"], reverse=True)[:5]:
        print(f"  {s['player']} ({s['team']}): {s['assists']}A")


if __name__ == "__main__":
    main()
