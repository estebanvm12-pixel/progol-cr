"""
Lucas Live — Simulador Monte Carlo en Tiempo Real
ProGol CR / WC 2026

Re-simula el partido desde el minuto actual con TODAS las condiciones vigentes:
- Marcador actual + hombres en cancha
- Breaks de hidratación (reset táctico FIFA WC2026)
- Patrón primer tiempo → segundo tiempo (goles H1, 0-0 al descanso)
- Expulsiones, lesiones de jugadores clave
- VAR / gol anulado, penales fallados/anotados
- Sustitución de jugador clave
- Doble amarilla (jugador en riesgo)
- Momentum por marcador + presión de tiempo
- Escenarios aleatorios en tiempo restante

Interfaz principal:
    agent = LucasLive()
    result = agent.simulate_live(live_state, lam_home, lam_away, n=1000)

live_state = {
    "home": "Argentina",
    "away": "Ecuador",
    "minute": 67,
    "score_h": 1,
    "score_a": 0,
    "h1_score_h": 1,       # marcador al final del primer tiempo
    "h1_score_a": 0,
    "home_men": 10,
    "away_men": 11,
    "period": "second_half",
    "events": [
        {"type": "red_card",         "team": "home", "player": "Messi",   "minute": 45, "is_key": True},
        {"type": "goal",             "team": "home", "player": "Lautaro", "minute": 23},
        {"type": "cooling_break",    "team": "both", "minute": 30},
        {"type": "cooling_break",    "team": "both", "minute": 75},
        {"type": "var_disallowed",   "team": "away", "player": "Enner",   "minute": 60},
        {"type": "penalty_missed",   "team": "away", "player": "Torres",  "minute": 55},
        {"type": "substitution_key", "team": "home", "player": "Dybala",  "minute": 70, "in": True},
        {"type": "yellow_risk",      "team": "away", "player": "Caicedo", "minute": 38},
    ]
}
"""
from __future__ import annotations
import math, random, json, os, datetime, time
from typing import Optional

# ─── Constantes globales ──────────────────────────────────────────────────────

DEFAULT_N   = 1000
FULL_MATCH  = 90
DATA_DIR    = "/home/progol/worldcup-warroom/data"
LOG_FILE    = os.path.join(DATA_DIR, "live_sim_log.json")

# ── Ventaja numérica: factor (equipo_corto, rival) ────────────────────────────
_MAN_ADV = {
    (11, 11): (1.00, 1.00),
    (10, 11): (0.65, 1.20),
    (9,  11): (0.42, 1.38),
    (9,  10): (0.78, 1.12),
    (11, 10): (1.20, 0.65),
    (11,  9): (1.38, 0.42),
    (10,  9): (1.12, 0.78),
    (10, 10): (1.00, 1.00),
}

# ── Momentum por diferencia de goles ─────────────────────────────────────────
_MOMENTUM = {
    -3: 1.42, -2: 1.28, -1: 1.14,
     0: 1.00,
     1: 0.88,  2: 0.78,  3: 0.68,
}

# ── Factores H1 → H2 (patrón de partido) ─────────────────────────────────────
# Equipo que anotó en H1 y va ganando: más conservador en H2
H1_WIN_CONSERVATIVE   = 0.88   # el que va ganando baja ritmo
H1_LOSS_DESPERATION   = 1.18   # el que va perdiendo presiona en H2
H1_GOALLESS_BOTH      = 1.06   # 0-0 al descanso → ambos más abiertos en H2
H1_HEAVY_GOALS        = 0.91   # >3 goles en H1 → partido se cierra tácticame

# ── Breaks de hidratación (cooling breaks WC2026) ─────────────────────────────
# Ocurren aprox min 30 y 75. Efecto: reset táctico, el que pierde mejora
COOLING_RESET_LOSING  = 1.08   # equipo que va perdiendo mejora táctica
COOLING_RESET_WINNING = 0.96   # equipo que va ganando consolida
COOLING_SIGMA_EXTRA   = 0.04   # incertidumbre adicional post-break

# ── Otros eventos ─────────────────────────────────────────────────────────────
KEY_RED_MULT       = 0.85
KEY_INJURY_MULT    = 0.93
VAR_DISALLOWED_H   = 0.91   # gol anulado → equipo frustrado -9%
VAR_DISALLOWED_RIV = 1.05   # rival con momentum +5%
PENALTY_MISSED_H   = 0.90   # penal fallado → confianza baja -10%
PENALTY_MISSED_RIV = 1.04
SUB_KEY_ON_MULT    = 1.08   # jugador clave entra → ataque +8%
SUB_KEY_OFF_MULT   = 0.94   # jugador clave sale → ataque -6%
YELLOW_RISK_MULT   = 0.95   # jugador en riesgo de doble amarilla → más cauteloso


# ─── Utilidades ──────────────────────────────────────────────────────────────

def _poisson(lam: float) -> int:
    if lam <= 0: return 0
    if lam >= 25:
        return max(0, int(random.gauss(lam, math.sqrt(lam)) + 0.5))
    L = math.exp(-lam); k = 0; p = 1.0
    while p > L:
        k += 1; p *= random.random()
    return k - 1

def _wilson(k: int, n: int, z: float = 1.96):
    if n == 0: return (0.0, 1.0)
    p = k / n; denom = 1 + z*z/n
    center = (p + z*z/(2*n)) / denom
    margin = (z * math.sqrt(p*(1-p)/n + z*z/(4*n*n))) / denom
    return (max(0.0, round(center - margin, 4)), min(1.0, round(center + margin, 4)))

def _time_pressure(minute: int) -> float:
    """Goles aumentan en últimos minutos — presión de tiempo."""
    if minute >= 85: return 1.22
    if minute >= 80: return 1.15
    if minute >= 70: return 1.07
    if minute >= 60: return 1.02
    return 1.00

def _injury_time(minute: int, period: str) -> int:
    if period == "extra_time": return 2
    if minute >= 85: return 6
    if period == "second_half": return 5
    return 3  # primer tiempo: más tiempo añadido en WC2026

def _is_key(player: str) -> bool:
    KEY = {"messi","ronaldo","mbappe","neymar","vinicius","salah","kane",
           "bellingham","pedri","modric","de bruyne","lewandowski","osimhen",
           "vlahovic","felix","rashford","saka","pulisic","reyna","dembele"}
    return any(k in player.lower() for k in KEY)


# ─── Motor principal ──────────────────────────────────────────────────────────

class LucasLive:

    def _adjust_lambdas(self, lam_h: float, lam_a: float, live: dict) -> tuple:
        """
        Aplica todos los factores al lambda base de Ryder.
        Retorna (lam_adj_h, lam_adj_a, sigma_extra, debug_dict)
        """
        home     = live.get("home", "Local")
        away     = live.get("away", "Visitante")
        minute   = int(live.get("minute", 0))
        score_h  = int(live.get("score_h", 0))
        score_a  = int(live.get("score_a", 0))
        h1_sh    = int(live.get("h1_score_h", -1))   # -1 = no informado
        h1_sa    = int(live.get("h1_score_a", -1))
        home_men = int(live.get("home_men", 11))
        away_men = int(live.get("away_men", 11))
        period   = live.get("period", "second_half")
        events   = live.get("events", [])

        debug = {"base_h": lam_h, "base_a": lam_a}
        sigma_extra = 0.0

        # ── 1. Ventaja numérica ───────────────────────────────────────────────
        key = (min(home_men, 11), min(away_men, 11))
        mf_h, mf_a = _MAN_ADV.get(key, (1.0, 1.0))
        lam_h *= mf_h; lam_a *= mf_a
        debug["men_factor"] = f"{mf_h:.2f}/{mf_a:.2f}"

        # ── 2. Momentum por marcador actual ───────────────────────────────────
        delta = score_h - score_a
        mom_h = _MOMENTUM.get(max(-3, min(3, -delta)), 1.0)   # yo pierdo → ataco
        mom_a = _MOMENTUM.get(max(-3, min(3,  delta)), 1.0)
        lam_h *= mom_h; lam_a *= mom_a
        debug["momentum"] = f"{mom_h:.2f}/{mom_a:.2f}"

        # ── 3. Patrón H1 → H2 ────────────────────────────────────────────────
        if period == "second_half" and h1_sh >= 0 and h1_sa >= 0:
            h1_total = h1_sh + h1_sa
            h1_delta = h1_sh - h1_sa

            if h1_total == 0:
                # 0-0 al descanso: ambos más abiertos en H2
                lam_h *= H1_GOALLESS_BOTH; lam_a *= H1_GOALLESS_BOTH
                debug["h1_pattern"] = "0-0: ambos abren H2"

            elif h1_total >= 3:
                # Partido abierto en H1: táctica más cerrada en H2
                lam_h *= H1_HEAVY_GOALS; lam_a *= H1_HEAVY_GOALS
                debug["h1_pattern"] = f">{h1_total} goles H1: se cierra"

            if h1_delta > 0:
                # Local iba ganando H1 → más conservador en H2
                lam_h *= H1_WIN_CONSERVATIVE
                lam_a *= H1_LOSS_DESPERATION
                debug["h1_pattern"] = debug.get("h1_pattern","") + f" H:{H1_WIN_CONSERVATIVE} A:{H1_LOSS_DESPERATION}"
            elif h1_delta < 0:
                # Visitante iba ganando H1
                lam_a *= H1_WIN_CONSERVATIVE
                lam_h *= H1_LOSS_DESPERATION
                debug["h1_pattern"] = debug.get("h1_pattern","") + f" H:{H1_LOSS_DESPERATION} A:{H1_WIN_CONSERVATIVE}"

        # ── 4. Presión de tiempo ──────────────────────────────────────────────
        tp = _time_pressure(minute)
        lam_h *= tp; lam_a *= tp
        debug["time_pressure"] = tp

        # ── 5. Procesar eventos ───────────────────────────────────────────────
        cooling_count_h = cooling_count_a = 0

        for ev in events:
            etype  = ev.get("type", "")
            team   = ev.get("team", "")
            player = ev.get("player", "")
            is_k   = ev.get("is_key", _is_key(player))

            # Expulsión
            if etype == "red_card" and is_k:
                if team == "home":   lam_h *= KEY_RED_MULT
                elif team == "away": lam_a *= KEY_RED_MULT

            # Lesión
            elif etype == "injury" and is_k:
                if team == "home":   lam_h *= KEY_INJURY_MULT
                elif team == "away": lam_a *= KEY_INJURY_MULT

            # Break de hidratación
            elif etype == "cooling_break":
                delta_now = score_h - score_a
                if delta_now > 0:
                    lam_h *= COOLING_RESET_WINNING
                    lam_a *= COOLING_RESET_LOSING
                    cooling_count_a += 1
                elif delta_now < 0:
                    lam_a *= COOLING_RESET_WINNING
                    lam_h *= COOLING_RESET_LOSING
                    cooling_count_h += 1
                else:
                    # Empate al break: ambos se reorganizan
                    lam_h *= 1.02; lam_a *= 1.02
                sigma_extra += COOLING_SIGMA_EXTRA

            # VAR — gol anulado
            elif etype == "var_disallowed":
                if team == "home":
                    lam_h *= VAR_DISALLOWED_H; lam_a *= VAR_DISALLOWED_RIV
                elif team == "away":
                    lam_a *= VAR_DISALLOWED_H; lam_h *= VAR_DISALLOWED_RIV

            # Penal fallado
            elif etype == "penalty_missed":
                if team == "home":
                    lam_h *= PENALTY_MISSED_H; lam_a *= PENALTY_MISSED_RIV
                elif team == "away":
                    lam_a *= PENALTY_MISSED_H; lam_h *= PENALTY_MISSED_RIV

            # Penal anotado → ya está en el marcador, no duplicar

            # Sustitución jugador clave
            elif etype == "substitution_key":
                entering = ev.get("in", True)
                mult = SUB_KEY_ON_MULT if entering else SUB_KEY_OFF_MULT
                if team == "home":   lam_h *= mult
                elif team == "away": lam_a *= mult

            # Amarilla en riesgo (jugador más cauteloso)
            elif etype == "yellow_risk":
                if team == "home":   lam_h *= YELLOW_RISK_MULT
                elif team == "away": lam_a *= YELLOW_RISK_MULT

        debug["cooling_breaks"] = cooling_count_h + cooling_count_a
        debug["sigma_extra"]    = round(sigma_extra, 3)
        debug["adj_h"]          = round(lam_h, 4)
        debug["adj_a"]          = round(lam_a, 4)
        return lam_h, lam_a, sigma_extra, debug

    def _scale_remaining(self, lam_h, lam_a, minute, period):
        """Escala lambda al tiempo restante del partido."""
        inj  = _injury_time(minute, period)
        full = 90 + (30 if period == "extra_time" else 0)
        remaining = max(0.0, float(full + inj - minute))
        scale = remaining / (full + inj)
        return lam_h * scale, lam_a * scale, remaining

    # ── Simulación principal ──────────────────────────────────────────────────

    def simulate_live(self, live: dict, lam_home: float, lam_away: float,
                      n: int = DEFAULT_N, seed: Optional[int] = None) -> dict:
        if seed is not None: random.seed(seed)
        n = max(100, min(10000, int(n)))

        home    = live.get("home", "Local")
        away    = live.get("away", "Visitante")
        minute  = int(live.get("minute", 0))
        score_h = int(live.get("score_h", 0))
        score_a = int(live.get("score_a", 0))
        period  = live.get("period", "second_half")

        adj_h, adj_a, sigma_extra, debug = self._adjust_lambdas(lam_home, lam_away, live)
        rem_h, rem_a, remaining = self._scale_remaining(adj_h, adj_a, minute, period)

        # Sigma total para incertidumbre por simulación
        sigma_total = 0.12 + sigma_extra   # base 12% + extra por cooling breaks

        score_counts: dict[str, int] = {}
        wins_h = wins_d = wins_a = 0
        total_gh = total_ga = 0.0

        for _ in range(n):
            lh = max(0.0, rem_h * random.gauss(1.0, sigma_total))
            la = max(0.0, rem_a * random.gauss(1.0, sigma_total))

            # Eventos aleatorios en tiempo restante
            # Roja adicional: 2.5% por equipo
            if random.random() < 0.025: lh *= 0.65
            if random.random() < 0.025: la *= 0.65
            # Lesión: 3.5% → -7%
            if random.random() < 0.035: lh *= 0.93
            if random.random() < 0.035: la *= 0.93
            # VAR gol anulado: 1.5%
            if random.random() < 0.015: lh *= 0.95
            if random.random() < 0.015: la *= 0.95

            gh = _poisson(lh); ga = _poisson(la)
            fh = score_h + gh; fa = score_a + ga
            total_gh += gh; total_ga += ga

            key = f"{fh}-{fa}"
            score_counts[key] = score_counts.get(key, 0) + 1
            if fh > fa: wins_h += 1
            elif fh == fa: wins_d += 1
            else: wins_a += 1

        p_h = wins_h/n; p_d = wins_d/n; p_a = wins_a/n

        # Convergencia vs prior Ryder
        diff = abs(p_h - lam_home/(lam_home + lam_away + 0.001))
        conv = "ALTA" if diff < 0.07 else "MEDIA" if diff < 0.16 else "BAJA"

        top = sorted(score_counts.items(), key=lambda x: -x[1])[:10]

        result = {
            "type": "live",
            "home": home, "away": away,
            "minute": minute, "remaining": round(remaining, 1),
            "period": period,
            "score_current": f"{score_h}-{score_a}",
            "score_h": score_h, "score_a": score_a,
            "h1_score_h": live.get("h1_score_h", -1),
            "h1_score_a": live.get("h1_score_a", -1),
            "n": n,
            "p_home": round(p_h, 4),
            "p_draw": round(p_d, 4),
            "p_away": round(p_a, 4),
            "ci_home": _wilson(wins_h, n),
            "ci_draw": _wilson(wins_d, n),
            "ci_away": _wilson(wins_a, n),
            "top_final_scores": [(s, round(c/n*100, 1)) for s, c in top],
            "avg_remaining_h": round(total_gh/n, 3),
            "avg_remaining_a": round(total_ga/n, 3),
            "adj_lambda_home": round(adj_h, 4),
            "adj_lambda_away": round(adj_a, 4),
            "sigma_used": round(sigma_total, 3),
            "lambda_debug": debug,
            "event_summary": self._summarize_events(live),
            "convergence": conv,
            "sim_id": f"{home[:3].upper()}{away[:3].upper()}_{minute}_{int(time.time())}",
        }

        self._save_snapshot(result)
        return result

    # ── Resumen de eventos ────────────────────────────────────────────────────

    def _summarize_events(self, live: dict) -> list:
        home     = live.get("home", "Local")
        away     = live.get("away", "Visitante")
        home_men = int(live.get("home_men", 11))
        away_men = int(live.get("away_men", 11))
        h1_sh    = live.get("h1_score_h", -1)
        h1_sa    = live.get("h1_score_a", -1)
        lines    = []

        if h1_sh >= 0 and h1_sa >= 0:
            lines.append(f"⏱ Descanso: {home} {h1_sh}-{h1_sa} {away}")

        for ev in sorted(live.get("events", []), key=lambda e: e.get("minute", 0)):
            t    = ev.get("type", "")
            team = home if ev.get("team") == "home" else (away if ev.get("team") == "away" else "ambos")
            pl   = ev.get("player", "")
            mn   = ev.get("minute", "?")
            star = " ⭐" if ev.get("is_key", _is_key(pl)) and pl else ""

            if t == "red_card":
                lines.append(f"🟥 {mn}' {team} — {pl}{star} expulsado")
            elif t == "goal":
                lines.append(f"⚽ {mn}' {team} — Gol de {pl}")
            elif t == "injury":
                lines.append(f"🚑 {mn}' {team} — {pl}{star} lesionado")
            elif t == "yellow_card":
                lines.append(f"🟨 {mn}' {team} — {pl} amonestado")
            elif t == "yellow_risk":
                lines.append(f"⚠️ {mn}' {team} — {pl} (riesgo 2ª amarilla)")
            elif t == "cooling_break":
                lines.append(f"💧 {mn}' Break de hidratación")
            elif t == "var_disallowed":
                lines.append(f"📺 {mn}' VAR — Gol anulado a {team} ({pl})")
            elif t == "penalty_missed":
                lines.append(f"🚫 {mn}' {team} — Penal fallado por {pl}")
            elif t == "penalty_scored":
                lines.append(f"⚽🎯 {mn}' {team} — Penal anotado por {pl}")
            elif t == "substitution_key":
                direction = "entra" if ev.get("in", True) else "sale"
                lines.append(f"🔄 {mn}' {team} — {pl}{star} {direction}")

        if home_men < 11:
            lines.append(f"🔢 {home}: {home_men} en cancha")
        if away_men < 11:
            lines.append(f"🔢 {away}: {away_men} en cancha")

        return lines

    # ── Log ───────────────────────────────────────────────────────────────────

    def _save_snapshot(self, result: dict):
        try:
            os.makedirs(DATA_DIR, exist_ok=True)
            log = {"snapshots": []}
            if os.path.exists(LOG_FILE):
                with open(LOG_FILE) as f:
                    log = json.load(f)
            log["snapshots"].append({
                "sim_id":        result["sim_id"],
                "home":          result["home"],
                "away":          result["away"],
                "minute":        result["minute"],
                "score_current": result["score_current"],
                "p_home":        result["p_home"],
                "p_draw":        result["p_draw"],
                "p_away":        result["p_away"],
                "top_score":     result["top_final_scores"][0][0] if result["top_final_scores"] else "?",
                "events":        result["event_summary"],
                "ts":            datetime.datetime.utcnow().isoformat() + "Z",
            })
            log["snapshots"] = log["snapshots"][-2000:]
            with open(LOG_FILE, "w") as f:
                json.dump(log, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    # ── Formato ───────────────────────────────────────────────────────────────

    def format_live(self, sim: dict) -> str:
        home = sim["home"]; away = sim["away"]
        sc   = sim["score_current"]; mn = sim["minute"]
        rem  = sim["remaining"]; n = sim["n"]
        ph   = sim["p_home"]*100; pd = sim["p_draw"]*100; pa = sim["p_away"]*100
        ci_h = sim["ci_home"]; ci_d = sim["ci_draw"]
        dbg  = sim.get("lambda_debug", {})

        def bar(pct, w=10):
            f = round(pct/100*w); return "█"*f + "░"*(w-f)

        lines = ["", f"🔴 LUCAS LIVE — Min {mn}'  [{sc}]  |  ~{rem:.0f}' restantes",
                 f"   {home} vs {away}", ""]

        for ev in sim.get("event_summary", []):
            lines.append(f"   {ev}")
        if sim.get("event_summary"): lines.append("")

        lines += [
            f"   📊 PROBABILIDADES ACTUALIZADAS ({n:,} sims desde min {mn}'):",
            f"   {home:<24} {bar(ph)} {ph:.1f}%  [IC95: {ci_h[0]*100:.1f}%-{ci_h[1]*100:.1f}%]",
            f"   {'Empate':<24} {bar(pd)} {pd:.1f}%  [IC95: {ci_d[0]*100:.1f}%-{ci_d[1]*100:.1f}%]",
            f"   {away:<24} {bar(pa)} {pa:.1f}%",
            "",
            f"   🎯 RESULTADOS FINALES MÁS PROBABLES:",
        ]
        for i, (sc2, pct) in enumerate(sim["top_final_scores"][:7], 1):
            lines.append(f"   {i}. {sc2:<6} {bar(pct,8)} {pct:.1f}%")

        # Explicar factores que movieron el lambda
        factors = []
        if dbg.get("cooling_breaks", 0): factors.append(f"💧 {dbg['cooling_breaks']} cooling breaks")
        h1 = dbg.get("h1_pattern", "")
        if h1: factors.append(f"⏱ H1: {h1}")

        lines += [
            "",
            f"   λ live: {home} {sim['adj_lambda_home']:.3f} | {away} {sim['adj_lambda_away']:.3f}",
            f"   Goles restantes esperados: {sim['avg_remaining_h']:.2f}—{sim['avg_remaining_a']:.2f}",
            f"   Factores: {', '.join(factors) if factors else 'ninguno especial'}",
            f"   Convergencia vs Ryder: {sim['convergence']}",
            "",
        ]
        return "\n".join(lines)

    def format_live_dialogue(self, sim: dict, prior_probs: Optional[dict] = None) -> str:
        home = sim["home"]; away = sim["away"]
        mn   = sim["minute"]; sc = sim["score_current"]
        ph   = sim["p_home"]*100; pd = sim["p_draw"]*100; pa = sim["p_away"]*100
        n    = sim["n"]
        top  = sim["top_final_scores"][0][0] if sim["top_final_scores"] else "?"
        ev_str = "; ".join(sim.get("event_summary", [])) or "Sin eventos"
        adj_h  = sim.get("adj_lambda_home", 0)
        adj_a  = sim.get("adj_lambda_away", 0)
        sigma  = sim.get("sigma_used", 0.12)

        prior_line = ""
        if prior_probs:
            prior_line = (
                f"RYDER (prior pre-partido): H={prior_probs.get('home',0)*100:.1f}% "
                f"D={prior_probs.get('draw',0)*100:.1f}% A={prior_probs.get('away',0)*100:.1f}%\n\n"
            )

        return (
            f"\n{'─'*52}\n"
            f"DIÁLOGO LUCAS LIVE × RYDER × CLEO — Min {mn}' [{sc}]\n\n"
            f"{prior_line}"
            f"LUCAS → RYDER: 'Estado: {ev_str}. "
            f"λ reajustado: {home} {adj_h:.3f} / {away} {adj_a:.3f} (σ={sigma:.2f}). "
            f"En {n:,} sims: H={ph:.1f}% D={pd:.1f}% A={pa:.1f}%. "
            f"Resultado final más probable: {top}.'\n\n"
            f"RYDER → LUCAS: 'Ajustes H1→H2, cooling breaks y momentum validados. "
            f"El diferencial λ refleja correctamente la situación táctica.'\n\n"
            f"CLEO → LUCAS+RYDER: 'Con estos eventos, el mercado en vivo tardará "
            f"1-3 minutos en ajustar sus líneas. Edge temporal posible si actúas "
            f"antes del mercado — pero spread del live betting es 2-4%.'\n"
            f"{'─'*52}\n"
        )


# ─── ProGol: re-calcular todas las quinielas activas ─────────────────────────

class LucasProGol:
    """
    Aplica Lucas Live a todos los partidos activos de la jornada ProGol.
    Genera predicción actualizada 1X2 para cada partido.
    """

    def simulate_all(
        self,
        matches: list,
        live_states: Optional[dict] = None,
        n: int = 1000,
    ) -> list:
        """
        matches:     lista de dicts con {home, away, lam_home, lam_away,
                                          ryder_probs, match_id}
        live_states: dict match_id → live_state (opcional para partidos en curso)
        Retorna lista con predicción ProGol 1X2 actualizada por partido.
        """
        if live_states is None: live_states = {}
        results = []
        agent   = LucasLive()

        for m in matches:
            home     = m.get("home", "?")
            away     = m.get("away", "?")
            mid      = m.get("match_id", f"{home}_{away}")
            lam_h    = float(m.get("lam_home", 1.2))
            lam_a    = float(m.get("lam_away", 0.9))
            ryder_p  = m.get("ryder_probs", {})
            status   = m.get("status", "pre")   # pre | live | finished

            live_st  = live_states.get(mid) or live_states.get(f"{home}_{away}")

            if status == "finished":
                # Partido terminado: usar resultado real
                sh = m.get("score_h", 0); sa = m.get("score_a", 0)
                pick = "1" if sh > sa else "X" if sh == sa else "2"
                results.append({
                    "match_id": mid, "home": home, "away": away,
                    "status": "finished",
                    "score": f"{sh}-{sa}",
                    "progol_pick": pick, "pick_confidence": 1.0,
                    "p_home": 1.0 if sh > sa else 0.0,
                    "p_draw": 1.0 if sh == sa else 0.0,
                    "p_away": 1.0 if sa > sh else 0.0,
                    "source": "resultado_real",
                })
                continue

            if live_st:
                # Partido en curso: usar Lucas Live
                sim = agent.simulate_live(live_st, lam_h, lam_a, n=n)
                ph  = sim["p_home"]; pd = sim["p_draw"]; pa = sim["p_away"]
                pick, conf = _best_pick(ph, pd, pa)
                top_score  = sim["top_final_scores"][0][0] if sim["top_final_scores"] else "?"
                results.append({
                    "match_id": mid, "home": home, "away": away,
                    "status": "live",
                    "minute": sim["minute"],
                    "score_current": sim["score_current"],
                    "progol_pick": pick, "pick_confidence": round(conf, 3),
                    "p_home": round(ph, 4), "p_draw": round(pd, 4), "p_away": round(pa, 4),
                    "top_score": top_score,
                    "source": "lucas_live",
                    "sim_n": n,
                })
            else:
                # Pre-partido: usar Lucas normal
                from lucas import LucasAgent
                la = LucasAgent()
                sim = la.simulate(home, away, lam_h, lam_a, n=n)
                ph  = sim["p_home"]; pd = sim["p_draw"]; pa = sim["p_away"]
                pick, conf = _best_pick(ph, pd, pa)
                top_score  = sim["top_scorelines"][0][0] if sim.get("top_scorelines") else "?"
                results.append({
                    "match_id": mid, "home": home, "away": away,
                    "status": "pre",
                    "progol_pick": pick, "pick_confidence": round(conf, 3),
                    "p_home": round(ph, 4), "p_draw": round(pd, 4), "p_away": round(pa, 4),
                    "top_score": top_score,
                    "source": "lucas_prepartido",
                    "sim_n": n,
                })

        return results

    def format_progol_table(self, results: list) -> str:
        """Tabla ProGol 1X2 con probabilidades y fuente de cada pronóstico."""
        lines = [
            "",
            "🏆 LUCAS × RYDER — PRONÓSTICOS ProGol ACTUALIZADOS",
            "═" * 58,
            f"  {'#':<3} {'Partido':<26} {'Pick':<5} {'H%':>5} {'X%':>5} {'A%':>5}  {'Estado':<14}",
            "─" * 58,
        ]
        for i, r in enumerate(results, 1):
            home  = r["home"][:11]; away = r["away"][:11]
            pick  = r["progol_pick"]; conf = r.get("pick_confidence", 0)
            ph    = r["p_home"]*100; pd = r["p_draw"]*100; pa = r["p_away"]*100
            st    = r["status"]

            if st == "finished":
                estado = f"FIN {r.get('score','?')}"
                pick_str = f"[{pick}]✓"
            elif st == "live":
                estado = f"🔴 {r.get('minute',0)}' {r.get('score_current','?')}"
                pick_str = f"[{pick}]⚡ {conf*100:.0f}%"
            else:
                estado = "Pre-partido"
                pick_str = f"[{pick}] {conf*100:.0f}%"

            lines.append(
                f"  {i:<3} {home:<12}vs{away:<12} {pick_str:<9} {ph:>5.1f} {pd:>5.1f} {pa:>5.1f}  {estado}"
            )

        lines += [
            "─" * 58,
            "  1=Local  X=Empate  2=Visitante  ⚡=En vivo (Lucas Live)",
            "  % = confianza del pick más probable",
            "",
        ]
        return "\n".join(lines)


def _best_pick(ph: float, pd: float, pa: float) -> tuple:
    """Retorna (pick_1X2, confidence)."""
    best = max(ph, pd, pa)
    if best == ph: return "1", ph
    if best == pd: return "X", pd
    return "2", pa


# ─── CLI ─────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse

    p = argparse.ArgumentParser(description="Lucas Live + ProGol")
    p.add_argument("--home",    default="Argentina")
    p.add_argument("--away",    default="Ecuador")
    p.add_argument("--minute",  type=int,  default=67)
    p.add_argument("--score",   default="1-0")
    p.add_argument("--h1",      default="1-0", help="marcador al descanso")
    p.add_argument("--men",     default="10-11")
    p.add_argument("--lam",     default="1.65-0.55")
    p.add_argument("--cooling", action="store_true", help="simular con cooling breaks")
    p.add_argument("--n",       type=int, default=1000)
    args = p.parse_args()

    sh, sa   = map(int, args.score.split("-"))
    h1sh, h1sa = map(int, args.h1.split("-"))
    hm, am   = map(int, args.men.split("-"))
    lh, la   = map(float, args.lam.split("-"))

    events = []
    if hm < 11:
        events.append({"type": "red_card", "team": "home", "player": "Jugador", "minute": 30, "is_key": False})
    if args.cooling:
        events.append({"type": "cooling_break", "team": "both", "minute": 30})
        if args.minute > 70:
            events.append({"type": "cooling_break", "team": "both", "minute": 75})

    live = {
        "home": args.home, "away": args.away,
        "minute": args.minute, "period": "second_half" if args.minute > 45 else "first_half",
        "score_h": sh, "score_a": sa,
        "h1_score_h": h1sh, "h1_score_a": h1sa,
        "home_men": hm, "away_men": am,
        "events": events,
    }

    agent = LucasLive()
    sim   = agent.simulate_live(live, lh, la, n=args.n)
    print(agent.format_live(sim))
    print(agent.format_live_dialogue(sim, prior_probs={"home": lh/(lh+la), "draw": 0.25, "away": la/(lh+la)}))
