"""
Genera stats de jugadores del Mundial 2026 usando Claude API.
Claude conoce la temporada 2024-25 completa hasta agosto 2025.
Guarda en data/players_stats.json — no sobreescribe entradas ya obtenidas.

Uso:
  python scripts/fetch_player_stats.py               # todos los equipos
  python scripts/fetch_player_stats.py --team Brazil # solo un equipo
  python scripts/fetch_player_stats.py --force       # reescribir todo
"""
import json, os, sys, time, urllib.request, urllib.parse

ROOT        = os.path.join(os.path.dirname(__file__), "..")
SQUADS_FILE = os.path.join(ROOT, "data", "wc2026_squads.json")
OUTPUT_FILE = os.path.join(ROOT, "data", "players_stats.json")

with open(os.path.join(ROOT, "config.json"), encoding="utf-8") as f:
    cfg = json.load(f)

OPENAI_KEY = cfg["openai_api_key"].strip()
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

SCHEMA = {
    "name": "string — nombre del jugador",
    "season": "string — ej: 2024-25",
    "club": "string — club en la temporada 2024-25",
    "league": "string — liga donde jugó",
    "pos": "string — GK | DF | MF | FW",
    "mp": "int — partidos jugados",
    "starts": "int — partidos como titular",
    "min": "int — minutos totales",
    "goals": "int — goles",
    "assists": "int — asistencias",
    "xg": "float — expected goals",
    "xa": "float — expected assists",
    "shots": "int — tiros totales",
    "shots_on_target": "int — tiros a puerta",
    "key_passes": "int — pases clave",
    "dribbles_completed": "int — regates completados",
    "tackles": "int — entradas",
    "interceptions": "int — intercepciones",
    "save_pct": "float | null — % paradas (solo porteros)",
    "clean_sheets": "int | null — porterias a cero (solo porteros)",
    "yellow_cards": "int",
    "red_cards": "int",
    "form_note": "string — 1-2 frases sobre su forma reciente, lesiones o noticias importantes",
    "confidence": "string — high | medium | low (confianza en los datos)"
}

def call_openai(prompt: str) -> str:
    body = json.dumps({
        "model": "gpt-4o",
        "max_tokens": 4096,
        "messages": [
            {"role": "system", "content": "Eres un analista experto de futbol. Responde solo con JSON valido, sin texto adicional."},
            {"role": "user", "content": prompt}
        ]
    }).encode("utf-8")
    req = urllib.request.Request(
        OPENAI_URL,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENAI_KEY}",
        }
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            resp = json.loads(r.read())
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="ignore")
        raise ValueError(f"API error {e.code}: {err_body[:400]}") from e
    return resp["choices"][0]["message"]["content"]

def fetch_team_stats(nation: str, players: list) -> dict:
    """Ask Claude for all players of a team in one batch call."""
    player_list = "\n".join(
        f"- {p['name']} ({p['pos']}) — club declarado: {p['club']}, liga: {p['league']}"
        for p in players
    )
    schema_str = json.dumps(SCHEMA, indent=2, ensure_ascii=False)
    prompt = f"""Eres un analista de fútbol experto. Necesito los stats oficiales de la temporada 2024-2025
(o la temporada más reciente disponible antes del Mundial 2026) de los siguientes jugadores de la selección de {nation}.

Jugadores:
{player_list}

Para cada jugador, devuelve un objeto JSON con los siguientes campos:
{schema_str}

Responde SOLO con un JSON array válido con exactamente {len(players)} objetos, uno por jugador, en el mismo orden.
Si un jugador estuvo lesionado o tuvo poca actividad, inclúyelo igual con los datos disponibles y confidence="low".
No incluyas explicaciones, solo el JSON."""

    raw = call_openai(prompt)
    # Extract JSON array from response
    raw = raw.strip()
    start = raw.find("[")
    end   = raw.rfind("]") + 1
    if start == -1 or end == 0:
        raise ValueError("No JSON array in response")
    return json.loads(raw[start:end])

def load_output() -> dict:
    if os.path.exists(OUTPUT_FILE):
        with open(OUTPUT_FILE, encoding="utf-8") as f:
            return json.load(f)
    return {}

def save_output(data: dict):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

def main():
    with open(SQUADS_FILE, encoding="utf-8") as f:
        squads = json.load(f)["teams"]

    args = sys.argv[1:]
    filter_team = None
    force = "--force" in args
    for i, a in enumerate(args):
        if a == "--team" and i + 1 < len(args):
            filter_team = args[i + 1].lower()

    out = load_output()
    total_new = 0

    for nation, tdata in squads.items():
        if filter_team and filter_team not in nation.lower():
            continue

        players = tdata["players"]
        # Check which players still need data
        pending = []
        for p in players:
            key = f"{nation}|{p['name']}"
            if force or key not in out:
                pending.append(p)

        if not pending:
            print(f"[{nation}] ya completo ({len(players)} jugadores)")
            continue

        print(f"[{nation}] consultando {len(pending)} jugadores a Claude...", flush=True)
        try:
            stats_list = fetch_team_stats(nation, pending)
            for p, stats in zip(pending, stats_list):
                key = f"{nation}|{p['name']}"
                out[key] = {
                    "name":   p["name"],
                    "nation": nation,
                    "pos":    p.get("pos"),
                    "club":   p.get("club"),
                    "league": p.get("league"),
                    "stats":  stats,
                }
                g  = stats.get("goals", 0) or 0
                a  = stats.get("assists", 0) or 0
                mp = stats.get("mp", 0) or 0
                print(f"  + {p['name']}: {int(mp)} partidos, {int(g)}G {int(a)}A")
                total_new += 1
            save_output(out)
            time.sleep(2)  # small pause between teams
        except Exception as e:
            import traceback
            print(f"  ERROR en {nation}: {e}")
            traceback.print_exc()
            save_output(out)

    print(f"\nListo - {total_new} jugadores nuevos. Total en cache: {len(out)}")

if __name__ == "__main__":
    main()
