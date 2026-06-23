"""
Liga CR Scraper v2 — ProGol CR
Fuente primaria: API-Football (RapidAPI) — tiene Liga Promerica (league_id=233)
Fallback: TheSportsDB (free, no key)

Genera:
  data/liga_cr_standings.json
  data/liga_cr_fixtures.json
  data/liga_cr_players.json

Cron: 0 6 * * * python3 /home/progol/worldcup-warroom/scraper_ligacr_v2.py
"""
import json, os, time, urllib.request, urllib.error, urllib.parse

HERE     = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "data")
os.makedirs(DATA_DIR, exist_ok=True)

# ── Config ────────────────────────────────────────────────────────────────────
try:
    with open(os.path.join(HERE, "config.json")) as f:
        _cfg = json.load(f)
except Exception:
    _cfg = {}

APIFOOTBALL_KEY = _cfg.get("apifootball_key", "").strip()

# API-Football league IDs
LIGA_CR_ID  = 233   # Costa Rica Primera Division (UNAFUT)
CURRENT_YEAR = 2025  # Temporada 2025-2026 → API usa año de inicio = 2025

# TheSportsDB fallback (free, league ID for Costa Rica Primera División)
SPORTSDB_LIGA_CR = "4384"

# ── Helpers ───────────────────────────────────────────────────────────────────
def _apifootball(endpoint: str, params: dict) -> dict:
    """Call API-Football via RapidAPI."""
    base = "https://v3.football.api-sports.io"
    url  = f"{base}/{endpoint}?{urllib.parse.urlencode(params)}"
    req  = urllib.request.Request(url, headers={
        "x-apisports-key": APIFOOTBALL_KEY,
    })
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        errors = data.get("errors", {})
        if errors and errors != [] and errors != {}:
            print(f"  [API-Football error] {errors}")
            return {}
        return data
    except urllib.error.HTTPError as e:
        print(f"  [HTTP {e.code}] {url}")
        return {}
    except Exception as e:
        print(f"  [error] {e}")
        return {}


def _sportsdb(endpoint: str) -> dict:
    """TheSportsDB free tier (no key needed)."""
    url = f"https://www.thesportsdb.com/api/v1/json/3/{endpoint}"
    req = urllib.request.Request(url, headers={"User-Agent": "ProGolCR/2.0"})
    try:
        with urllib.request.urlopen(req, timeout=12) as r:
            return json.loads(r.read().decode())
    except Exception as e:
        print(f"  [sportsdb error] {e}")
        return {}


# ── Standings ─────────────────────────────────────────────────────────────────
def fetch_standings() -> list:
    print("  [API-Football] standings...")
    data = _apifootball("standings", {"league": LIGA_CR_ID, "season": CURRENT_YEAR})
    rows = []
    for entry in data.get("response", []):
        for group in entry.get("league", {}).get("standings", []):
            for r in group:
                team = r.get("team", {})
                all_ = r.get("all", {})
                rows.append({
                    "position":       r.get("rank"),
                    "team_id":        team.get("id"),
                    "team":           team.get("name"),
                    "logo":           team.get("logo"),
                    "played":         all_.get("played"),
                    "wins":           all_.get("win"),
                    "draws":          all_.get("draw"),
                    "losses":         all_.get("lose"),
                    "goals_for":      all_.get("goals", {}).get("for"),
                    "goals_against":  all_.get("goals", {}).get("against"),
                    "goal_diff":      r.get("goalsDiff"),
                    "points":         r.get("points"),
                    "form":           r.get("form"),
                    "description":    r.get("description"),
                })
    if rows:
        print(f"  ✓ {len(rows)} equipos via API-Football")
        return rows

    # Fallback TheSportsDB
    print("  [fallback] TheSportsDB standings...")
    data2 = _sportsdb(f"lookuptable.php?l={SPORTSDB_LIGA_CR}&s=2025-2026")
    rows2 = []
    for r in (data2.get("table") or []):
        rows2.append({
            "position":      int(r.get("intRank", 0)),
            "team":          r.get("strTeam"),
            "played":        int(r.get("intPlayed", 0)),
            "wins":          int(r.get("intWin", 0)),
            "draws":         int(r.get("intDraw", 0)),
            "losses":        int(r.get("intLoss", 0)),
            "goals_for":     int(r.get("intGoalsFor", 0)),
            "goals_against": int(r.get("intGoalsAgainst", 0)),
            "goal_diff":     int(r.get("intGoalDifference", 0)),
            "points":        int(r.get("intPoints", 0)),
        })
    print(f"  ✓ {len(rows2)} equipos via TheSportsDB")
    return rows2


# ── Fixtures ──────────────────────────────────────────────────────────────────
def fetch_fixtures() -> list:
    print("  [API-Football] fixtures...")
    data = _apifootball("fixtures", {
        "league": LIGA_CR_ID,
        "season": CURRENT_YEAR,
        "last":   30,
    })
    fixtures = []
    for f in data.get("response", []):
        fix = f.get("fixture", {})
        teams = f.get("teams", {})
        goals = f.get("goals", {})
        score = f.get("score", {})
        fixtures.append({
            "id":         fix.get("id"),
            "date":       fix.get("date"),
            "timestamp":  fix.get("timestamp"),
            "status":     fix.get("status", {}).get("short"),
            "status_long": fix.get("status", {}).get("long"),
            "venue":      fix.get("venue", {}).get("name"),
            "home_id":    teams.get("home", {}).get("id"),
            "home":       teams.get("home", {}).get("name"),
            "home_logo":  teams.get("home", {}).get("logo"),
            "away_id":    teams.get("away", {}).get("id"),
            "away":       teams.get("away", {}).get("name"),
            "away_logo":  teams.get("away", {}).get("logo"),
            "home_score": goals.get("home"),
            "away_score": goals.get("away"),
            "ht_home":    score.get("halftime", {}).get("home"),
            "ht_away":    score.get("halftime", {}).get("away"),
            "round":      f.get("league", {}).get("round"),
        })

    # Also get upcoming
    data2 = _apifootball("fixtures", {
        "league": LIGA_CR_ID,
        "season": CURRENT_YEAR,
        "next":   10,
    })
    for f in data2.get("response", []):
        fix = f.get("fixture", {})
        teams = f.get("teams", {})
        fixtures.append({
            "id":         fix.get("id"),
            "date":       fix.get("date"),
            "timestamp":  fix.get("timestamp"),
            "status":     "NS",
            "home_id":    teams.get("home", {}).get("id"),
            "home":       teams.get("home", {}).get("name"),
            "away_id":    teams.get("away", {}).get("id"),
            "away":       teams.get("away", {}).get("name"),
            "round":      f.get("league", {}).get("round"),
        })

    if fixtures:
        print(f"  ✓ {len(fixtures)} partidos via API-Football")
        return fixtures

    # Fallback TheSportsDB
    print("  [fallback] TheSportsDB events...")
    data3 = _sportsdb(f"eventsseason.php?id={SPORTSDB_LIGA_CR}&s=2025-2026")
    fixtures2 = []
    for e in (data3.get("events") or []):
        fixtures2.append({
            "id":         e.get("idEvent"),
            "date":       e.get("dateEvent"),
            "home":       e.get("strHomeTeam"),
            "away":       e.get("strAwayTeam"),
            "home_score": e.get("intHomeScore"),
            "away_score": e.get("intAwayScore"),
            "status":     "FT" if e.get("intHomeScore") is not None else "NS",
            "round":      e.get("intRound"),
        })
    print(f"  ✓ {len(fixtures2)} partidos via TheSportsDB")
    return fixtures2


# ── Top Scorers ───────────────────────────────────────────────────────────────
def fetch_top_scorers() -> list:
    print("  [API-Football] top scorers...")
    data = _apifootball("players/topscorers", {
        "league": LIGA_CR_ID,
        "season": CURRENT_YEAR,
    })
    scorers = []
    for entry in data.get("response", []):
        p   = entry.get("player", {})
        st  = (entry.get("statistics") or [{}])[0]
        scorers.append({
            "player_id":   p.get("id"),
            "name":        p.get("name"),
            "photo":       p.get("photo"),
            "nationality": p.get("nationality"),
            "age":         p.get("age"),
            "team":        st.get("team", {}).get("name"),
            "team_id":     st.get("team", {}).get("id"),
            "goals":       st.get("goals", {}).get("total", 0),
            "assists":     st.get("goals", {}).get("assists", 0),
            "appearances": st.get("games", {}).get("appearences", 0),
            "minutes":     st.get("games", {}).get("minutes", 0),
            "yellow_cards": st.get("cards", {}).get("yellow", 0),
            "red_cards":   st.get("cards", {}).get("red", 0),
        })
    print(f"  ✓ {len(scorers)} goleadores")
    return scorers


# ── Team Stats (for Ryder calibration) ───────────────────────────────────────
def fetch_team_stats(team_ids: list) -> list:
    """Estadísticas de cada equipo para calibrar λ en Ryder."""
    stats = []
    for tid in team_ids[:10]:  # max 10 equipos
        time.sleep(0.5)
        data = _apifootball("teams/statistics", {
            "league": LIGA_CR_ID,
            "season": CURRENT_YEAR,
            "team":   tid,
        })
        r = data.get("response", {})
        if not r:
            continue
        fix  = r.get("fixtures", {})
        goals = r.get("goals", {})
        gf   = goals.get("for", {}).get("average", {})
        ga   = goals.get("against", {}).get("average", {})
        stats.append({
            "team_id":          r.get("team", {}).get("id"),
            "team":             r.get("team", {}).get("name"),
            "played_home":      fix.get("played", {}).get("home", 0),
            "played_away":      fix.get("played", {}).get("away", 0),
            "wins_home":        fix.get("wins", {}).get("home", 0),
            "wins_away":        fix.get("wins", {}).get("away", 0),
            "avg_goals_for_home":     float(gf.get("home") or 0),
            "avg_goals_for_away":     float(gf.get("away") or 0),
            "avg_goals_against_home": float(ga.get("home") or 0),
            "avg_goals_against_away": float(ga.get("away") or 0),
            "form":             r.get("form"),
            "clean_sheets_home": r.get("clean_sheet", {}).get("home", 0),
            "clean_sheets_away": r.get("clean_sheet", {}).get("away", 0),
            "failed_to_score_home": r.get("failed_to_score", {}).get("home", 0),
        })
        print(f"    ✓ {r.get('team',{}).get('name','?')}: avg_gf_h={gf.get('home')} avg_gf_a={gf.get('away')}")
    return stats


def compute_ryder_lambdas(team_stats: list) -> dict:
    """
    Calcula ataque/defensa normalizado para el modelo Ryder de Liga CR.
    Formato: {team_name: {"attack_h": x, "defense_h": x, "attack_a": x, "defense_a": x}}
    """
    if not team_stats:
        return {}
    avg_gf_h = sum(t["avg_goals_for_home"] for t in team_stats) / len(team_stats) or 1.2
    avg_gf_a = sum(t["avg_goals_for_away"] for t in team_stats) / len(team_stats) or 1.0
    lambdas = {}
    for t in team_stats:
        name = t["team"]
        lambdas[name] = {
            "attack_home":   round(t["avg_goals_for_home"] / avg_gf_h, 4) if avg_gf_h else 1.0,
            "defense_home":  round(t["avg_goals_against_home"] / avg_gf_a, 4) if avg_gf_a else 1.0,
            "attack_away":   round(t["avg_goals_for_away"] / avg_gf_a, 4) if avg_gf_a else 1.0,
            "defense_away":  round(t["avg_goals_against_home"] / avg_gf_h, 4) if avg_gf_h else 1.0,
            "form":          t.get("form", ""),
        }
    return lambdas


# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    print("=" * 55)
    print("  ProGol CR — Liga Promerica Scraper v2")
    print("  Fuente: API-Football + TheSportsDB fallback")
    print("=" * 55)

    print("\n[1/4] Standings...")
    standings = fetch_standings()

    print("\n[2/4] Fixtures...")
    fixtures = fetch_fixtures()

    print("\n[3/4] Top Scorers...")
    scorers = fetch_top_scorers()

    team_ids = [r["team_id"] for r in standings if r.get("team_id")]
    print(f"\n[4/4] Team stats ({len(team_ids)} equipos)...")
    team_stats = fetch_team_stats(team_ids) if team_ids else []
    ryder_lambdas = compute_ryder_lambdas(team_stats)

    # ── Guardar ───────────────────────────────────────────────────────────────
    ts = int(time.time())

    with open(os.path.join(DATA_DIR, "liga_cr_standings.json"), "w") as f:
        json.dump({
            "updated":      ts,
            "league_id":    LIGA_CR_ID,
            "season":       CURRENT_YEAR,
            "standings":    standings,
            "top_scorers":  scorers[:20],
            "team_stats":   team_stats,
            "ryder_lambdas": ryder_lambdas,
        }, f, indent=2, ensure_ascii=False)

    with open(os.path.join(DATA_DIR, "liga_cr_fixtures.json"), "w") as f:
        json.dump({"updated": ts, "fixtures": fixtures}, f, indent=2, ensure_ascii=False)

    with open(os.path.join(DATA_DIR, "liga_cr_players.json"), "w") as f:
        json.dump({"updated": ts, "top_scorers": scorers}, f, indent=2, ensure_ascii=False)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"""
✅ Liga CR guardada:
   standings: {len(standings)} equipos
   fixtures:  {len(fixtures)} partidos
   scorers:   {len(scorers)} goleadores
   ryder_lambdas: {len(ryder_lambdas)} equipos calibrados
""")
    if standings:
        print(f"{'#':<3} {'Equipo':<25} {'PJ':<4} {'PTS':<4} {'GD':<5} {'Forma'}")
        for r in sorted(standings, key=lambda x: x.get("position") or 99):
            form = r.get("form","")[-5:] if r.get("form") else ""
            print(f"{r.get('position','?'):<3} {str(r.get('team','?')):<25} {str(r.get('played','?')):<4} {str(r.get('points','?')):<4} {str(r.get('goal_diff','?')):<5} {form}")

    if scorers:
        print("\nTOP GOLEADORES:")
        for i, s in enumerate(scorers[:8], 1):
            print(f"  {i}. {s['name']} ({s['team']}) — {s['goals']} goles")

    if ryder_lambdas:
        print("\nRYDER LAMBDAS (ataque home / ataque away):")
        for team, vals in sorted(ryder_lambdas.items()):
            print(f"  {team:<28} λ_home={vals['attack_home']:.3f}  λ_away={vals['attack_away']:.3f}  forma={vals['form'][-5:] if vals['form'] else '?'}")


if __name__ == "__main__":
    main()
