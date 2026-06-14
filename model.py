#!/usr/bin/env python3
"""
Match prediction engine for the World Cup War Room.

A transparent statistical model (the standard approach used in football
analytics): team strength ratings -> expected goals -> a Poisson score grid.
From that single grid we derive every market the dashboard shows:

  - win / draw / win probabilities (1X2)
  - most-likely scoreline + the top scorelines
  - expected goals per team
  - who scores first
  - first corner + expected corners
  - both teams to score, over/under 2.5
  - expected cards
  - a 1-10 confidence read

It is intentionally explainable, not a black box. These are MODEL ESTIMATES
with assumptions, never guarantees — the UI labels them as such.

Pure standard library (math only). No external dependencies.
"""

import json
import math
import os

# File where post-match Elo updates are persisted across restarts
_HERE = os.path.dirname(os.path.abspath(__file__))
_ELO_OVERRIDES_PATH = os.path.join(_HERE, "data", "elo_overrides.json")

def _load_elo_overrides():
    try:
        with open(_ELO_OVERRIDES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def _save_elo_overrides(overrides):
    with open(_ELO_OVERRIDES_PATH, "w", encoding="utf-8") as f:
        json.dump(overrides, f, indent=2)

def update_elo_after_match(home, away, score_h, score_a, k=32):
    """Update Elo ratings after a finished match. K=32 for WC matches."""
    overrides = _load_elo_overrides()
    h_key = home.lower().strip()
    a_key = away.lower().strip()
    # Get current effective ratings (override > base)
    r_h = overrides.get(h_key) or RATINGS.get(h_key) or DEFAULT_RATING
    r_a = overrides.get(a_key) or RATINGS.get(a_key) or DEFAULT_RATING
    # Expected scores
    e_h = 1.0 / (1.0 + 10 ** ((r_a - r_h) / 400.0))
    e_a = 1.0 - e_h
    # Actual scores
    if score_h > score_a:
        s_h, s_a = 1.0, 0.0
    elif score_h < score_a:
        s_h, s_a = 0.0, 1.0
    else:
        s_h, s_a = 0.5, 0.5
    overrides[h_key] = round(r_h + k * (s_h - e_h), 1)
    overrides[a_key] = round(r_a + k * (s_a - e_a), 1)
    _save_elo_overrides(overrides)
    return overrides[h_key], overrides[a_key]

# Elo-style strength ratings (approx. World Football Elo, 2025/26 ballpark).
# Used only to derive expected goals; tweak freely. Keys are lowercased.
RATINGS = {
    # Top tier
    "spain": 2120, "france": 2100, "argentina": 2085, "england": 2055,
    "brazil": 2045, "portugal": 2010, "netherlands": 2000, "germany": 1985,
    "italy": 1965, "belgium": 1955, "croatia": 1925, "uruguay": 1905,
    "colombia": 1885, "morocco": 1865, "switzerland": 1855, "austria": 1855,
    # Strong
    "senegal": 1840, "japan": 1835, "denmark": 1835, "norway": 1835,
    "ecuador": 1825, "nigeria": 1820, "serbia": 1820, "turkey": 1820,
    "ivory coast": 1805, "algeria": 1800, "ukraine": 1800, "sweden": 1800,
    "mexico": 1800, "usa": 1795, "egypt": 1795, "poland": 1790,
    "hungary": 1790, "czech republic": 1785, "czechia": 1785, "wales": 1785,
    "scotland": 1780, "iran": 1780, "cameroon": 1780, "mali": 1770,
    "greece": 1770, "chile": 1765, "tunisia": 1765, "bosnia-herzegovina": 1760,
    "canada": 1760, "south korea": 1775, "korea republic": 1775,
    # Mid
    "australia": 1745, "ghana": 1750, "paraguay": 1745, "dr congo": 1745,
    "peru": 1730, "romania": 1740, "slovakia": 1735, "slovenia": 1735,
    "south africa": 1685, "saudi arabia": 1700, "qatar": 1690, "iceland": 1705,
    "costa rica": 1700, "panama": 1700, "venezuela": 1700, "finland": 1715,
    "republic of ireland": 1720, "northern ireland": 1690, "albania": 1710,
    "georgia": 1715, "uzbekistan": 1665, "cape verde": 1665, "jamaica": 1685,
    "honduras": 1660, "bolivia": 1655, "iraq": 1660, "jordan": 1625,
    "uae": 1640, "united arab emirates": 1640, "bahrain": 1560, "oman": 1600,
    # Lower
    "curacao": 1600, "haiti": 1600, "new zealand": 1625, "guatemala": 1620,
    "el salvador": 1560, "trinidad and tobago": 1560, "grenada": 1420,
    "kazakhstan": 1560, "armenia": 1560, "moldova": 1470, "luxembourg": 1560,
    "kosovo": 1610, "north macedonia": 1640, "montenegro": 1600,
    "azerbaijan": 1510, "estonia": 1450, "malta": 1330, "gibraltar": 1230,
    "guyana": 1430, "suriname": 1470, "nicaragua": 1480,
}

# Club strength ratings for the important leagues (approx Elo, 2025/26). Lowercased.
CLUB_RATINGS = {
    "manchester city": 2080, "real madrid": 2075, "bayern munich": 2035, "arsenal": 2020,
    "liverpool": 2015, "barcelona": 2010, "paris saint-germain": 1995, "paris sg": 1995,
    "inter milan": 1975, "internazionale": 1975, "juventus": 1905, "napoli": 1900,
    "atletico madrid": 1945, "bayer leverkusen": 1930, "borussia dortmund": 1900,
    "ac milan": 1885, "atalanta": 1885, "rb leipzig": 1875, "chelsea": 1905,
    "tottenham": 1880, "tottenham hotspur": 1880, "manchester united": 1865, "aston villa": 1855,
    "newcastle": 1860, "newcastle united": 1860, "west ham": 1795, "west ham united": 1795,
    "brighton": 1810, "brighton and hove albion": 1810, "brentford": 1770, "crystal palace": 1765,
    "fulham": 1760, "bournemouth": 1750, "wolves": 1745, "wolverhampton": 1745,
    "nottingham forest": 1745, "everton": 1740, "real sociedad": 1825, "villarreal": 1825,
    "real betis": 1800, "athletic bilbao": 1820, "athletic club": 1820, "sevilla": 1790,
    "valencia": 1760, "girona": 1800, "as roma": 1850, "roma": 1850, "lazio": 1830,
    "fiorentina": 1830, "bologna": 1820, "eintracht frankfurt": 1820, "wolfsburg": 1765,
    "vfb stuttgart": 1820, "freiburg": 1780, "union berlin": 1770, "benfica": 1855,
    "porto": 1840, "fc porto": 1840, "sporting cp": 1855, "sporting lisbon": 1855,
    "ajax": 1800, "psv": 1845, "psv eindhoven": 1845, "feyenoord": 1825, "az alkmaar": 1770,
    "marseille": 1820, "monaco": 1825, "as monaco": 1825, "lille": 1805, "lyon": 1790,
    "nice": 1790, "galatasaray": 1825, "fenerbahce": 1820, "celtic": 1820, "rangers": 1795,
    # Americas
    "inter miami": 1760, "lafc": 1775, "los angeles fc": 1775, "la galaxy": 1745,
    "seattle sounders": 1750, "flamengo": 1855, "palmeiras": 1860, "botafogo": 1835,
    "fluminense": 1800, "atletico mineiro": 1810, "sao paulo": 1800, "corinthians": 1790,
    "internacional": 1800, "gremio": 1790, "boca juniors": 1805, "river plate": 1835,
    "club america": 1785, "monterrey": 1785, "tigres uanl": 1785, "tigres": 1785,
}

ALIASES = {
    "united states": "usa", "united states of america": "usa", "usmnt": "usa",
    "estados unidos": "usa", "canadá": "canada",
    "korea republic": "south korea", "korea dpr": "north korea",
    "corea del sur": "south korea", "corea del norte": "north korea",
    "czechia": "czech republic", "turkiye": "turkey", "türkiye": "turkey",
    "ivory coast (cote d'ivoire)": "ivory coast", "cote d'ivoire": "ivory coast",
    "côte d'ivoire": "ivory coast", "costa de marfil": "ivory coast",
    "bosnia and herzegovina": "bosnia-herzegovina",
    "bosnia y herzegovina": "bosnia-herzegovina",
    "república checa": "czech republic", "turquía": "turkey",
    "republic of ireland (ireland)": "republic of ireland", "ireland": "republic of ireland",
    "república de irlanda": "republic of ireland", "irlanda del norte": "northern ireland",
    "congo dr": "dr congo", "dr congo (congo)": "dr congo", "congo rd": "dr congo",
    "curaçao": "curacao", "curazao": "curacao", "china pr": "china",
    # Spanish national team names
    "alemania": "germany", "españa": "spain", "francia": "france",
    "países bajos": "netherlands", "holanda": "netherlands", "bélgica": "belgium",
    "croacia": "croatia", "marruecos": "morocco", "suiza": "switzerland",
    "japón": "japan", "dinamarca": "denmark", "noruega": "norway",
    "nigeria": "nigeria", "turquía": "turkey", "argelia": "algeria",
    "ucrania": "ukraine", "suecia": "sweden", "méxico": "mexico",
    "egipto": "egypt", "polonia": "poland", "hungría": "hungary",
    "gales": "wales", "escocia": "scotland", "irán": "iran",
    "camerún": "cameroon", "grecia": "greece", "túnez": "tunisia",
    "australia": "australia", "ghana": "ghana", "perú": "peru",
    "rumanía": "romania", "eslovaquia": "slovakia", "eslovenia": "slovenia",
    "sudáfrica": "south africa", "arabia saudita": "saudi arabia",
    "islandia": "iceland", "panamá": "panama", "finlandia": "finland",
    "albania": "albania", "nueva zelanda": "new zealand",
    "kazajistán": "kazakhstan", "moldavia": "moldova",
    "luxemburgo": "luxembourg", "macedonia del norte": "north macedonia",
    "azerbaiyán": "azerbaijan", "estonia": "estonia", "haití": "haiti",
    "brasil": "brazil", "italia": "italy", "portugal": "portugal",
    "senegal": "senegal", "colombia": "colombia", "uruguay": "uruguay",
    "serbia": "serbia", "ecuador": "ecuador",
}

DEFAULT_RATING = 1600
HOME_ADV_ELO = 35        # club football home advantage (not used for WC neutral venues)
HOST_ADV_ELO = 15        # reduced advantage for WC host nations (USA/Canada/Mexico)
HOST_NATIONS = {"usa", "united states", "canada", "mexico"}
MAXG = 10                # goals grid cap

# Form weights: index 0 = most recent result
_FORM_WEIGHTS = [1.0, 0.85, 0.70, 0.55, 0.40]


def _form_adjustment(results):
    """Return Elo delta from recent form. results: list of 'W'/'D'/'L', most-recent first."""
    delta = 0.0
    for i, res in enumerate((results or [])[:5]):
        w = _FORM_WEIGHTS[i]
        if res == "W":   delta += 18 * w
        elif res == "D": delta +=  6 * w
        elif res == "L": delta -= 12 * w
    return delta


def _norm(name):
    n = (name or "").strip().lower()
    return ALIASES.get(n, n)


def _lookup(team):
    """Return (rating, known) checking Elo overrides first, then static tables."""
    n = _norm(team)
    overrides = _load_elo_overrides()
    if n in overrides:
        return overrides[n], True
    if n in RATINGS:
        return RATINGS[n], True
    if n in CLUB_RATINGS:
        return CLUB_RATINGS[n], True
    return DEFAULT_RATING, False


def rating(team):
    return _lookup(team)[0]


def known(team):
    return _lookup(team)[1]


def _poisson_pmf(k, lam):
    return math.exp(-lam) * lam ** k / math.factorial(k)


def _expected_goals(elo_home, elo_away, wc_mode=False):
    dr = elo_home - elo_away
    sup = dr / 200.0                                   # ~200 Elo per 1 goal of supremacy
    avg = (elo_home + elo_away) / 2.0
    if wc_mode:
        # WC knockout-stage calibration: avg ~2.3 goals, stronger defenses, higher avg Elo
        base = 2.30
        quality_adj = max(-0.25, min(0.55, (avg - 1800) / 300.0 * 0.45))
    else:
        base = 2.5
        quality_adj = max(-0.3, min(0.8, (avg - 1700) / 300.0 * 0.6))
    total = base + quality_adj
    lam_h = max(0.18, total / 2 + sup / 2)
    lam_a = max(0.18, total / 2 - sup / 2)
    return lam_h, lam_a


def _elo_expected_score(elo_home, elo_away):
    """Classic Elo win-expectancy 0..1 — used for territory/corner share."""
    return 1.0 / (1.0 + 10 ** (-(elo_home - elo_away) / 400.0))


# Dixon-Coles low-score correction coefficient (ρ < 0 corrects for draw
# underestimation in standard bivariate Poisson). Empirically calibrated
# from football data: draws at 0-0 and 1-1 are more frequent than Poisson
# predicts; 1-0 and 0-1 are less frequent.
DC_RHO = -0.13


def _dc_tau(i, j, lam_h, lam_a, rho=DC_RHO):
    """Dixon-Coles correction factor for scorelines (i,j) ∈ {0,1}x{0,1}."""
    if i == 0 and j == 0:
        return 1.0 - lam_h * lam_a * rho
    elif i == 1 and j == 0:
        return 1.0 + lam_a * rho
    elif i == 0 and j == 1:
        return 1.0 + lam_h * rho
    elif i == 1 and j == 1:
        return 1.0 - rho
    return 1.0


def predict(home, away, home_advantage=True, home_form=None, away_form=None,
            xg_home=None, xg_away=None, wc_mode=False):
    base_h, known_h = _lookup(home)
    base_a, known_a = _lookup(away)
    low_data = not (known_h and known_a)

    # Apply recent-form nudge to effective ratings before building the goal model
    form_delta_h = _form_adjustment(home_form)
    form_delta_a = _form_adjustment(away_form)

    # Neutral-venue logic: WC matches → no home advantage (home_advantage=False).
    # Host nations (USA/Canada/Mexico) pass home_advantage="host" for reduced boost.
    if home_advantage == "host":
        adv = HOST_ADV_ELO
    else:
        adv = HOME_ADV_ELO if home_advantage else 0
    eh = base_h + adv + form_delta_h
    ea = base_a + form_delta_a

    if xg_home is not None and xg_away is not None:
        # Use real xG data to set λ directly (blended 70% xG, 30% model)
        lam_h_model, lam_a_model = _expected_goals(eh, ea, wc_mode=wc_mode)
        lam_h = round(0.7 * xg_home + 0.3 * lam_h_model, 3)
        lam_a = round(0.7 * xg_away + 0.3 * lam_a_model, 3)
    else:
        lam_h, lam_a = _expected_goals(eh, ea, wc_mode=wc_mode)

    # Dixon-Coles corrected score grid:
    # P(i,j) = τ(i,j,λ,μ,ρ) · Poisson(i,λ) · Poisson(j,μ)
    # The τ correction only applies to low-scoring cells (0-0, 1-0, 0-1, 1-1)
    grid = [[_poisson_pmf(i, lam_h) * _poisson_pmf(j, lam_a) * _dc_tau(i, j, lam_h, lam_a)
             for j in range(MAXG + 1)] for i in range(MAXG + 1)]
    s = sum(sum(row) for row in grid)
    grid = [[c / s for c in row] for row in grid]

    p_home = sum(grid[i][j] for i in range(MAXG + 1) for j in range(MAXG + 1) if i > j)
    p_draw = sum(grid[i][i] for i in range(MAXG + 1))
    p_away = sum(grid[i][j] for i in range(MAXG + 1) for j in range(MAXG + 1) if i < j)

    # top scorelines
    flat = [(i, j, grid[i][j]) for i in range(MAXG + 1) for j in range(MAXG + 1)]
    flat.sort(key=lambda t: t[2], reverse=True)
    top = [{"h": i, "a": j, "p": round(p * 100, 1)} for i, j, p in flat[:6]]
    ml = flat[0]

    btts  = sum(grid[i][j] for i in range(1, MAXG + 1) for j in range(1, MAXG + 1))
    over25 = sum(grid[i][j] for i in range(MAXG + 1) for j in range(MAXG + 1) if i + j >= 3)
    over15 = sum(grid[i][j] for i in range(MAXG + 1) for j in range(MAXG + 1) if i + j >= 2)
    over35 = sum(grid[i][j] for i in range(MAXG + 1) for j in range(MAXG + 1) if i + j >= 4)

    # who scores first (competing Poisson processes)
    p_nogoal = grid[0][0]
    rate = lam_h + lam_a
    sf_home = (lam_h / rate) * (1 - p_nogoal)
    sf_away = (lam_a / rate) * (1 - p_nogoal)

    # corners — driven by territorial dominance (Elo win-expectancy)
    # Scale base corners with total expected goals: more attacking → more corners
    w = _elo_expected_score(eh, ea)
    corner_share_h = 0.5 + (w - 0.5) * 0.7            # dampen toward 50/50
    base_corners = 8.2 + (lam_h + lam_a) * 0.90       # ~9.2-10.5 depending on match tempo
    corners_h = base_corners * corner_share_h
    corners_a = base_corners * (1 - corner_share_h)

    # cards — more when the match is competitive (close in strength)
    closeness = 1 - abs(w - 0.5) * 2
    total_cards = 3.1 + 1.5 * closeness
    cards_h = total_cards * (0.5 - (w - 0.5) * 0.25)   # underdog tends to foul a touch more
    cards_a = total_cards - cards_h

    # clean sheet: Poisson P(score=0) for each side
    cs_home = math.exp(-lam_a)   # P(away scores 0) → home keeps clean sheet
    cs_away = math.exp(-lam_h)   # P(home scores 0) → away keeps clean sheet

    # win to nil (win AND opponent scores 0)
    wtn_home = sum(grid[i][0] for i in range(1, MAXG + 1))
    wtn_away = sum(grid[0][j] for j in range(1, MAXG + 1))

    # double chance
    dc_1x = p_home + p_draw
    dc_x2 = p_draw + p_away
    dc_12 = p_home + p_away

    # half-time result: first half ≈ 47 % of match goals (empirical average)
    ht_lam_h, ht_lam_a = lam_h * 0.47, lam_a * 0.47
    HT_MAXG = 6
    ht_ph = ht_pd = ht_pa = ht_s = 0.0
    for i in range(HT_MAXG):
        for j in range(HT_MAXG):
            p = _poisson_pmf(i, ht_lam_h) * _poisson_pmf(j, ht_lam_a)
            ht_s += p
            if i > j:    ht_ph += p
            elif i == j: ht_pd += p
            else:         ht_pa += p
    if ht_s > 0:
        ht_ph /= ht_s; ht_pd /= ht_s; ht_pa /= ht_s

    # confidence — probability edge + rating gap + form data quality
    elo_gap = abs(eh - ea)
    edge = max(p_home, p_draw, p_away)
    conf = 3 + (edge - 0.34) * 12
    if elo_gap > 250: conf += 0.5
    if elo_gap > 450: conf += 0.5
    form_games = len((home_form or [])[:5]) + len((away_form or [])[:5])
    if form_games >= 6: conf += 0.3
    confidence = max(1, min(10, round(conf)))
    if low_data:
        confidence = min(confidence, 4)

    favorite = home if p_home > p_away else away
    form_adjusted = form_delta_h != 0.0 or form_delta_a != 0.0

    # ── Índice ProGol™ (propietario) ────────────────────────────────────────
    # Combina: probabilidad del favorito × (1 - entropía Shannon normalizada)
    # × factor forma × ajuste mercado alternativo (corners/tarjetas)
    # Rango 0-10. Scores ≥7 = alta confianza, ≥5 = media, <5 = especulativa.
    # Fórmula exclusiva ProGol CR — no publicada.
    _probs_vec = [max(0.001, p) for p in [p_home, p_draw, p_away]]
    _h_shannon = -sum(p * math.log2(p) for p in _probs_vec) / math.log2(3)  # 0=certeza, 1=azar
    _fav_prob = max(p_home, p_away)
    _form_factor = 1.0 + min(0.15, abs(form_delta_h - form_delta_a) / 100)
    _alt_edge = 1.0 + max(0, (corners_h + corners_a - 9.0) / 20)  # corners volume bonus
    progol_index = round(max(0.0, min(10.0, _fav_prob * (1 - _h_shannon) * _form_factor * _alt_edge * 10)), 2)
    # ─────────────────────────────────────────────────────────────────────────

    return {
        "home": home, "away": away,
        "homeElo": base_h, "awayElo": base_a, "lowData": low_data,
        "homeAdvantage": home_advantage,
        "expectedGoals": {"home": round(lam_h, 2), "away": round(lam_a, 2)},
        "prob": {"home": round(p_home * 100, 1), "draw": round(p_draw * 100, 1),
                  "away": round(p_away * 100, 1)},
        "predictedScore": {"home": ml[0], "away": ml[1], "p": round(ml[2] * 100, 1)},
        "topScores": top,
        "btts": round(btts * 100, 1),
        "over25": round(over25 * 100, 1),
        "under25": round((1 - over25) * 100, 1),
        "over15": round(over15 * 100, 1),
        "over35": round(over35 * 100, 1),
        "scoreFirst": {"home": round(sf_home * 100, 1), "away": round(sf_away * 100, 1),
                        "none": round(p_nogoal * 100, 1)},
        "firstCorner": {"home": round(corner_share_h * 100, 1),
                         "away": round((1 - corner_share_h) * 100, 1)},
        "expectedCorners": {"home": round(corners_h, 1), "away": round(corners_a, 1),
                             "total": round(corners_h + corners_a, 1)},
        "expectedCards": {"home": round(cards_h, 1), "away": round(cards_a, 1),
                          "total": round(total_cards, 1)},
        "cleanSheet": {"home": round(cs_home * 100, 1), "away": round(cs_away * 100, 1)},
        "winToNil": {"home": round(wtn_home * 100, 1), "away": round(wtn_away * 100, 1)},
        "doubleChance": {
            "home_draw": round(dc_1x * 100, 1),
            "draw_away": round(dc_x2 * 100, 1),
            "home_away": round(dc_12 * 100, 1),
        },
        "halfTime": {
            "home": round(ht_ph * 100, 1),
            "draw": round(ht_pd * 100, 1),
            "away": round(ht_pa * 100, 1),
        },
        "formRecord": {
            "home": list(home_form or [])[:5],
            "away": list(away_form or [])[:5],
        },
        "favorite": favorite,
        "confidence": confidence,
        "conf": round(max(1.0, min(10.0, conf)), 2),
        "progolIndex": progol_index,
        "model": "Dixon-Coles · Poisson · Elo · ProGol™" + (" · form-adjusted" if form_adjusted else ""),
        "engine": {
            "lam_home": round(lam_h, 3),
            "lam_away": round(lam_a, 3),
            "dc_rho": DC_RHO,
            "elo_home": round(eh, 0),
            "elo_away": round(ea, 0),
            "p_00": round(grid[0][0] * 100, 2),
            "p_10": round(grid[1][0] * 100, 2),
            "p_01": round(grid[0][1] * 100, 2),
            "p_11": round(grid[1][1] * 100, 2),
        },
    }


def _parse_minute(raw):
    """Best-effort current match minute from TheSportsDB strProgress ('67', 'HT', '45+2')."""
    if raw is None:
        return 0
    s = str(raw).strip().upper()
    if s in ("HT", "HALF TIME", "HALFTIME"):
        return 45
    if s in ("FT", "AET", "PEN"):
        return 90
    digits = "".join(ch for ch in s.split("+")[0] if ch.isdigit())
    try:
        return max(0, min(95, int(digits)))
    except ValueError:
        return 0


def predict_live(home, away, minute, home_score, away_score,
                 home_advantage=True, home_form=None, away_form=None, wc_mode=False):
    """In-play model: re-projects the rest of the match from the current
    scoreline + clock. Uses the pre-match per-team goal rates, scales them by
    the time remaining, and tilts for game state (a trailing side pushes, the
    leader sits deeper)."""
    base_h, known_h = _lookup(home)
    base_a, known_a = _lookup(away)
    low_data = not (known_h and known_a)
    form_delta_h = _form_adjustment(home_form)
    form_delta_a = _form_adjustment(away_form)
    if home_advantage == "host":
        adv = HOST_ADV_ELO
    else:
        adv = HOME_ADV_ELO if home_advantage else 0
    eh = base_h + adv + form_delta_h
    ea = base_a + form_delta_a
    lam_h, lam_a = _expected_goals(eh, ea, wc_mode=wc_mode)  # full-match goal expectations

    minute = _parse_minute(minute) if not isinstance(minute, int) else max(0, min(95, minute))
    hs = max(0, int(home_score or 0))
    as_ = max(0, int(away_score or 0))

    # Fraction of regulation time still to play (small stoppage cushion at the death)
    rem = max(0.0, (90 - minute) / 90.0)
    if 0 < rem < 0.06:
        rem = 0.06
    rh = lam_h * rem
    ra = lam_a * rem

    # Game-state tilt: the trailing team commits more, the leader protects.
    diff = hs - as_                                # +ve => home leads
    if rem > 0 and diff != 0:
        tilt = max(-0.35, min(0.35, -diff * 0.12)) # each goal of lead ~12% intent swing
        rh *= (1 + tilt)
        ra *= (1 - tilt)
    rh = max(0.01, rh)
    ra = max(0.01, ra)

    # Remaining-goals distribution for each side
    RG = 7
    gh = [_poisson_pmf(i, rh) for i in range(RG + 1)]
    ga = [_poisson_pmf(j, ra) for j in range(RG + 1)]
    sh, sa = sum(gh), sum(ga)
    gh = [x / sh for x in gh]
    ga = [x / sa for x in ga]

    p_home = p_draw = p_away = 0.0
    over15 = over25 = over35 = btts_p = 0.0
    final_dist = {}
    cur_total = hs + as_
    for i in range(RG + 1):
        for j in range(RG + 1):
            p = gh[i] * ga[j]
            fh, fa = hs + i, as_ + j
            if fh > fa:   p_home += p
            elif fh == fa: p_draw += p
            else:          p_away += p
            tot = fh + fa
            if tot >= 2: over15 += p
            if tot >= 3: over25 += p
            if tot >= 4: over35 += p
            if fh >= 1 and fa >= 1: btts_p += p
            final_dist[(fh, fa)] = final_dist.get((fh, fa), 0.0) + p

    # Next goal (competing Poisson over the remaining time)
    rate = rh + ra
    p_no_more = gh[0] * ga[0]
    if rate > 0:
        next_home = (rh / rate) * (1 - p_no_more)
        next_away = (ra / rate) * (1 - p_no_more)
    else:
        next_home = next_away = 0.0

    flat = sorted(final_dist.items(), key=lambda kv: kv[1], reverse=True)
    top = [{"h": k[0], "a": k[1], "p": round(v * 100, 1)} for k, v in flat[:5]]

    # corners and cards — scale full-match estimate by time remaining
    w = _elo_expected_score(eh, ea)
    corner_share_h = 0.5 + (w - 0.5) * 0.7
    base_corners = 8.2 + (lam_h + lam_a) * 0.90
    c_h = base_corners * corner_share_h
    c_a = base_corners * (1 - corner_share_h)
    closeness = 1 - abs(w - 0.5) * 2
    total_cards = 3.1 + 1.5 * closeness
    cards_h = total_cards * (0.5 - (w - 0.5) * 0.25)
    cards_a = total_cards - cards_h

    leader = home if diff > 0 else away if diff < 0 else None
    return {
        "home": home, "away": away,
        "minute": minute, "homeScore": hs, "awayScore": as_,
        "leader": leader, "lowData": low_data,
        "remGoals": {"home": round(rh, 2), "away": round(ra, 2), "total": round(rh + ra, 2)},
        "nextGoal": {"home": round(next_home * 100, 1),
                      "away": round(next_away * 100, 1),
                      "none": round(p_no_more * 100, 1)},
        "prob": {"home": round(p_home * 100, 1), "draw": round(p_draw * 100, 1),
                  "away": round(p_away * 100, 1)},
        "liveOver15": round(over15 * 100, 1),
        "liveOver25": round(over25 * 100, 1),
        "liveOver35": round(over35 * 100, 1),
        "liveUnder25": round((1 - over25) * 100, 1),
        "liveBtts": round(btts_p * 100, 1),
        "bttsResolved": hs >= 1 and as_ >= 1,
        "curTotal": cur_total,
        "topScores": top,
        "favorite": home if p_home > p_away else away,
        "expectedCorners": {
            "home": round(c_h, 1), "away": round(c_a, 1),
            "total": round(c_h + c_a, 1),
            "remHome": round(c_h * rem, 1), "remAway": round(c_a * rem, 1),
            "remTotal": round((c_h + c_a) * rem, 1),
        },
        "expectedCards": {
            "home": round(cards_h, 1), "away": round(cards_a, 1),
            "total": round(total_cards, 1),
            "remTotal": round(total_cards * rem, 1),
        },
    }


if __name__ == "__main__":
    import json, sys
    h = sys.argv[1] if len(sys.argv) > 1 else "England"
    a = sys.argv[2] if len(sys.argv) > 2 else "Costa Rica"
    print(json.dumps(predict(h, a), indent=2))
