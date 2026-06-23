"""
Re-calibra los ratings Elo del modelo usando stats de jugadores 2024-25.

Lógica:
  - Para cada seleccion con datos de jugadores, calcula el "squad xG rate"
    sumando xG de los tops atacantes/mediocampistas del squad.
  - Compara con el baseline del modelo (lambda esperada para esa seleccion).
  - Si el squad tiene xG muy superior/inferior al baseline, aplica un ajuste
    suave (+/- hasta 30 puntos Elo) en los overrides.
  - NO sobreescribe overrides generados por resultados reales (calibrate_date).

Uso:
  python scripts/recalibrate_with_player_stats.py
"""
import json, os, sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, ROOT)

import model as _model
from analysis.players import squad_summary, stats_coverage

ELO_OVERRIDES_PATH = os.path.join(ROOT, "data", "elo_overrides.json")
PLAYER_ELO_PATH    = os.path.join(ROOT, "data", "player_elo_adjustments.json")

# Only adjust if squad coverage is at least this %
MIN_COVERAGE = 30
# Max Elo nudge from player data
MAX_NUDGE = 30

# Expected xG per 90 per squad (based on ~3 top attackers contributing)
# These are league-average baselines for comparison
SQUAD_XG_BASELINE = 0.22  # goals per game PER PLAYER (avg of top 8), typical WC squad


def load_overrides():
    try:
        with open(ELO_OVERRIDES_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_overrides(data):
    with open(ELO_OVERRIDES_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def load_player_adjustments():
    try:
        with open(PLAYER_ELO_PATH, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_player_adjustments(data):
    with open(PLAYER_ELO_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def compute_squad_xg(nation):
    """
    Returns estimated squad xG contribution from top 8 outfield players.
    Uses xG from player stats; falls back to goals if xG missing.
    """
    summary = squad_summary(nation, top_n=8)
    if summary["coverage"] < MIN_COVERAGE:
        return None, summary["coverage"]

    total_xg = 0.0
    players_counted = 0
    for p in summary["top_players"]:
        xg = p.get("xg")
        goals = p.get("goals")
        mp = p.get("mp") or 1
        if xg is not None and mp > 5:
            # xG per game, annualized to ~38 games
            xg_per_game = xg / mp
            total_xg += xg_per_game * 38
            players_counted += 1
        elif goals is not None and mp > 5:
            # Use goals as proxy for xG
            g_per_game = goals / mp
            total_xg += g_per_game * 38 * 0.85  # goals undercount chances
            players_counted += 1

    if players_counted < 2:
        return None, summary["coverage"]

    # Normalize to per-game rate
    squad_xg_per_game = (total_xg / players_counted) / 38
    return squad_xg_per_game, summary["coverage"]


NATIONS_32 = [
    "Argentina", "Brazil", "France", "England", "Germany", "Spain", "Portugal",
    "Netherlands", "Italy", "Morocco", "Japan", "USA", "Mexico", "Canada",
    "Uruguay", "Colombia", "Ecuador", "Senegal", "Australia", "Saudi Arabia",
    "Qatar", "Switzerland", "Belgium", "Croatia", "Denmark", "Poland",
    "Serbia", "Cameroon", "Ghana", "South Korea", "Iran", "Ivory Coast",
]


def main():
    cov = stats_coverage()
    print(f"Cobertura de jugadores: {cov['cached']}/{cov['total_players']} ({cov['pct']}%)")

    overrides = load_overrides()
    prev_adjustments = load_player_adjustments()
    new_adjustments = {}
    adjusted = 0

    print(f"\n{'Selección':<20} {'xG/game':>8} {'Cobert':>7} {'Base Elo':>9} {'Nudge':>7} {'New Elo':>9}")
    print("-" * 65)

    for nation in NATIONS_32:
        squad_xg, coverage = compute_squad_xg(nation)
        n_key = nation.lower()
        base_elo = _model.RATINGS.get(n_key) or _model.DEFAULT_RATING

        if squad_xg is None:
            print(f"  {nation:<20} {'N/A':>8} {coverage:>6}%  (datos insuficientes)")
            continue

        # Compute nudge: how much better/worse than baseline xG?
        delta = squad_xg - SQUAD_XG_BASELINE
        # Scale: +0.3 xG/game -> +MAX_NUDGE Elo, -0.3 -> -MAX_NUDGE
        nudge = round(max(-MAX_NUDGE, min(MAX_NUDGE, delta * (MAX_NUDGE / 0.3))), 1)

        # Get current effective Elo (from real-match calibration)
        current_elo = overrides.get(n_key) or base_elo

        # Remove old player adjustment, apply new one
        old_player_nudge = prev_adjustments.get(n_key, {}).get("nudge", 0)
        new_elo = round(current_elo - old_player_nudge + nudge, 1)

        new_adjustments[n_key] = {"nudge": nudge, "squad_xg": round(squad_xg, 3), "coverage": coverage}
        overrides[n_key] = new_elo
        adjusted += 1

        arrow = "+" if nudge >= 0 else ""
        print(f"  {nation:<20} {squad_xg:>8.3f} {coverage:>6}%  {base_elo:>8}  {arrow}{nudge:>5}  {new_elo:>8}")

    save_overrides(overrides)
    save_player_adjustments(new_adjustments)
    print(f"\nListo — {adjusted} selecciones re-calibradas con datos de jugadores.")
    print(f"Elo overrides guardados en data/elo_overrides.json")


if __name__ == "__main__":
    main()
