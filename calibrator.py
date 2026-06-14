#!/usr/bin/env python3
"""
ProGol CR — Motor de Calibración Diaria (CLASIFICADO)
=====================================================
Actualiza los ratings Elo con resultados reales del Mundial 2026.
Fuente: ESPN API (gratuita, sin clave).
Solo Esteban Venegas tiene acceso a este módulo.

Metodología:
  • K=32 para partidos de WC (alta volatilidad, torneo corto)
  • K=20 para amistosos / clasificatorias
  • K=16 para ligas regulares
  • Brier Score para medir precisión del modelo en tiempo real
  • Log-loss acumulado para calibración de probabilidades
"""

import json
import math
import urllib.request
import urllib.error
import datetime
import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))

# Import model from same directory
sys.path.insert(0, _HERE)
import model as _model

# Log file for calibration history
_LOG_PATH = os.path.join(_HERE, "data", "calibration_log.json")
_BRIER_PATH = os.path.join(_HERE, "data", "brier_scores.json")

os.makedirs(os.path.join(_HERE, "data"), exist_ok=True)

# ── ESPN fetch ──────────────────────────────────────────────────────────────

ESPN_LEAGUES_CALIBRATE = [
    "fifa.world",
    "concacaf.nations.league",
    "uefa.euro",
    "conmebol.america",
]

def _espn_scoreboard(league, date_str_ymd):
    """Fetch ESPN scoreboard. date_str_ymd = 'YYYYMMDD'."""
    url = (
        f"https://site.api.espn.com/apis/site/v2/sports/soccer/"
        f"{league}/scoreboard?dates={date_str_ymd}&limit=50"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "ProGolCR-Calibrator/2.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except Exception:
        return None


def _extract_finished(data):
    """Return list of {home, away, score_h, score_a, league} from ESPN data."""
    results = []
    for ev in (data or {}).get("events", []):
        comp = ev.get("competitions", [{}])[0]
        status_name = comp.get("status", {}).get("type", {}).get("name", "")
        if status_name not in ("STATUS_FINAL", "STATUS_FULL_TIME", "STATUS_FT"):
            continue
        competitors = comp.get("competitors", [])
        home = next((c for c in competitors if c.get("homeAway") == "home"), None)
        away = next((c for c in competitors if c.get("homeAway") == "away"), None)
        if not home or not away:
            continue
        try:
            results.append({
                "home": home["team"]["displayName"],
                "away": away["team"]["displayName"],
                "score_h": int(home.get("score", 0) or 0),
                "score_a": int(away.get("score", 0) or 0),
                "league": ev.get("name", ""),
            })
        except Exception:
            continue
    return results


# ── Brier Score tracking ────────────────────────────────────────────────────

def _compute_brier(pred, score_h, score_a):
    """
    Brier score for 3-outcome prediction.
    Returns 0 (perfect) to 2 (worst).
    """
    p = pred.get("prob", {})
    p_h = p.get("home", 33.3) / 100
    p_d = p.get("draw", 33.3) / 100
    p_a = p.get("away", 33.3) / 100
    # Actual outcomes
    if score_h > score_a:
        a_h, a_d, a_a = 1, 0, 0
    elif score_h < score_a:
        a_h, a_d, a_a = 0, 0, 1
    else:
        a_h, a_d, a_a = 0, 1, 0
    return round((p_h - a_h)**2 + (p_d - a_d)**2 + (p_a - a_a)**2, 4)


def _load_brier():
    try:
        with open(_BRIER_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return {"scores": [], "n": 0, "mean": None, "total": 0.0}


def _save_brier(data):
    with open(_BRIER_PATH, "w") as f:
        json.dump(data, f, indent=2)


def _update_brier(home, away, score_h, score_a):
    """Compute and persist Brier score for this match."""
    try:
        pred = _model.predict(home, away)
        bs = _compute_brier(pred, score_h, score_a)
        data = _load_brier()
        data["scores"].append({"match": f"{home} v {away}", "brier": bs, "result": f"{score_h}-{score_a}"})
        data["n"] += 1
        data["total"] = round(data["total"] + bs, 4)
        data["mean"] = round(data["total"] / data["n"], 4)
        data["scores"] = data["scores"][-200:]  # keep last 200
        _save_brier(data)
        return bs
    except Exception:
        return None


# ── Calibration log ─────────────────────────────────────────────────────────

def _load_log():
    try:
        with open(_LOG_PATH, "r") as f:
            return json.load(f)
    except Exception:
        return []


def _append_log(entries):
    log = _load_log()
    log.extend(entries)
    log = log[-500:]  # keep last 500 events
    with open(_LOG_PATH, "w") as f:
        json.dump(log, f, indent=2)


# ── Already-processed guard ─────────────────────────────────────────────────

_PROCESSED_PATH = os.path.join(_HERE, "data", "processed_matches.json")


def _load_processed():
    try:
        with open(_PROCESSED_PATH, "r") as f:
            return set(json.load(f))
    except Exception:
        return set()


def _save_processed(processed):
    with open(_PROCESSED_PATH, "w") as f:
        json.dump(sorted(processed), f)


# ── Main calibration function ───────────────────────────────────────────────

def calibrate_date(date_str, k_wc=32, k_other=20, verbose=False):
    """
    Calibrate Elo ratings from finished matches on date_str ('YYYY-MM-DD').
    Returns list of processed matches with Elo changes and Brier scores.
    """
    d = datetime.datetime.strptime(date_str, "%Y-%m-%d")
    espn_date = d.strftime("%Y%m%d")
    processed = _load_processed()
    log_entries = []
    results_out = []

    for league in ESPN_LEAGUES_CALIBRATE:
        data = _espn_scoreboard(league, espn_date)
        matches = _extract_finished(data)
        is_wc = league == "fifa.world"
        k = k_wc if is_wc else k_other

        for m in matches:
            key = f"{date_str}|{m['home']}|{m['away']}"
            if key in processed:
                continue  # already updated

            # Get Elo BEFORE update (for logging)
            overrides = _model._load_elo_overrides()
            h_key = m["home"].lower().strip()
            a_key = m["away"].lower().strip()
            old_h = overrides.get(h_key) or _model.RATINGS.get(h_key) or _model.DEFAULT_RATING
            old_a = overrides.get(a_key) or _model.RATINGS.get(a_key) or _model.DEFAULT_RATING

            # Brier score (uses pre-match ratings)
            brier = _update_brier(m["home"], m["away"], m["score_h"], m["score_a"])

            # Update Elo
            new_h, new_a = _model.update_elo_after_match(
                m["home"], m["away"], m["score_h"], m["score_a"], k=k
            )

            entry = {
                "ts": datetime.datetime.utcnow().isoformat(),
                "date": date_str,
                "league": m["league"],
                "home": m["home"],
                "away": m["away"],
                "result": f"{m['score_h']}-{m['score_a']}",
                "k": k,
                "elo_home_before": old_h, "elo_home_after": new_h,
                "elo_away_before": old_a, "elo_away_after": new_a,
                "brier": brier,
            }
            log_entries.append(entry)
            results_out.append(entry)
            processed.add(key)

            if verbose:
                print(f"  ✓ {m['home']} {m['score_h']}-{m['score_a']} {m['away']}  "
                      f"Elo: {old_h}→{new_h} / {old_a}→{new_a}  Brier: {brier}")

    _save_processed(processed)
    if log_entries:
        _append_log(log_entries)

    return results_out


def calibrate_yesterday(verbose=False):
    yesterday = (datetime.datetime.utcnow() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
    return calibrate_date(yesterday, verbose=verbose)


def calibrate_today(verbose=False):
    today = datetime.datetime.utcnow().strftime("%Y-%m-%d")
    return calibrate_date(today, verbose=verbose)


def get_model_accuracy():
    """Return current Brier score stats."""
    data = _load_brier()
    if data["n"] == 0:
        return None
    # Brier score interpretation: 0.0 = perfect, 0.667 = random, lower is better
    random_baseline = 0.667
    skill_score = round((1 - data["mean"] / random_baseline) * 100, 1)
    return {
        "n_matches": data["n"],
        "mean_brier": data["mean"],
        "skill_score_pct": skill_score,
        "last_5": data["scores"][-5:],
    }


def get_calibration_log(n=20):
    return _load_log()[-n:]


if __name__ == "__main__":
    print("═" * 60)
    print("  ProGol CR — Calibrador Diario")
    print("═" * 60)
    print(f"\nFecha: {datetime.datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC")
    print("\n▸ Procesando ayer...")
    r = calibrate_yesterday(verbose=True)
    print(f"\n▸ Procesando hoy...")
    r2 = calibrate_today(verbose=True)
    total = len(r) + len(r2)
    print(f"\n✓ {total} partido(s) procesado(s)")
    acc = get_model_accuracy()
    if acc:
        print(f"\n📊 Precisión acumulada del modelo:")
        print(f"   Brier Score: {acc['mean_brier']} (0 = perfecto, 0.667 = azar)")
        print(f"   Skill Score: {acc['skill_score_pct']}% sobre el azar")
        print(f"   Muestra: {acc['n_matches']} partidos")
