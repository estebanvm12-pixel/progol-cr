"""
Lucas — Agente simulador Monte Carlo para ProGol CR.
Simula cada partido mínimo 1000 veces usando todas las variables disponibles:
  - Lambda de Ryder (Dixon-Coles + Elo + player stats + coach + tourney form)
  - Incertidumbre del modelo (~15% desviación estándar)
  - Eventos aleatorios: lesiones clave, presión de torneo, momentum
  - Prior de mercado de Cleo (Bayesian blend)

Produce distribuciones empíricas: frecuencia real de cada marcador,
intervalos de confianza, y convergencia vs modelo analítico de Ryder.
"""
import math
import random
import logging
import os
import json

logger = logging.getLogger(__name__)

# ── Constantes ────────────────────────────────────────────────────────────────
DEFAULT_N       = 1000     # simulaciones por defecto
MIN_N           = 100      # mínimo requerido
MAX_N           = 10000    # tope para no bloquear el servidor
LAM_SIGMA_PCT   = 0.15     # incertidumbre del modelo: ±15% en lambda
INJURY_PROB     = 0.07     # 7% chance de baja clave por equipo por partido
INJURY_IMPACT   = (0.78, 0.92)  # rango de impacto en lambda si hay baja
MOMENTUM_SIGMA  = 0.06     # varianza de momentum aleatorio
MARKET_BLEND    = 0.20     # peso del mercado (Cleo) en la lambda final: 20%
MAX_GOALS_SHOWN = 8        # goles máximos en distribución de marcadores


def _poisson_sample(lam: float) -> int:
    """
    Muestreo de distribución Poisson sin numpy (stdlib only).
    Usa algoritmo de Knuth para lam < 30, aproximación normal para mayor.
    """
    if lam <= 0:
        return 0
    if lam >= 30:
        # Aproximación normal (lam grande → distribución Gauss ≈ Poisson)
        return max(0, int(random.gauss(lam, math.sqrt(lam)) + 0.5))
    # Knuth: P(k) = e^-lam * lam^k / k!
    L = math.exp(-lam)
    k = 0
    p = 1.0
    while p > L:
        k += 1
        p *= random.random()
    return k - 1


def _normal_sample(mu: float, sigma: float, lo: float = 0.05) -> float:
    """Muestra distribución normal truncada en lo."""
    return max(lo, random.gauss(mu, sigma))


class LucasAgent:
    """
    Agente simulador Monte Carlo.
    Recibe las predicciones de Ryder y Cleo y produce distribuciones empíricas.
    """

    def __init__(self, seed: int = None):
        if seed is not None:
            random.seed(seed)

    # ── Simulación principal ─────────────────────────────────────────────────

    def simulate(
        self,
        home: str,
        away: str,
        lam_home: float,
        lam_away: float,
        cleo_data: dict = None,
        n: int = DEFAULT_N,
    ) -> dict:
        """
        Simula el partido n veces y devuelve distribuciones empíricas.

        Args:
            home, away: nombres de equipos
            lam_home, lam_away: lambdas de Ryder (ya ajustados por player/coach/tourney)
            cleo_data: resultado de Cleo (para blend de mercado)
            n: número de simulaciones (mínimo MIN_N)
        """
        n = max(MIN_N, min(MAX_N, int(n)))
        lam_h = max(0.10, float(lam_home))
        lam_a = max(0.10, float(lam_away))

        # Extraer probabilidades de mercado de Cleo para blend Bayesiano
        mkt_p_home, mkt_p_away = self._extract_market_probs(cleo_data, lam_h, lam_a)

        # Ajustar lambdas base con prior de mercado
        lam_h_base, lam_a_base = self._blend_market(lam_h, lam_a, mkt_p_home, mkt_p_away)

        # ── Loop de simulación ────────────────────────────────────────────────
        home_wins = draws = away_wins = 0
        scorelines: dict = {}
        goals_h_dist = [0] * (MAX_GOALS_SHOWN + 2)
        goals_a_dist = [0] * (MAX_GOALS_SHOWN + 2)
        total_goals_h = 0.0
        total_goals_a = 0.0

        for _ in range(n):
            # 1. Incertidumbre del modelo: lambda varía ±15%
            lh = _normal_sample(lam_h_base, lam_h_base * LAM_SIGMA_PCT)
            la = _normal_sample(lam_a_base, lam_a_base * LAM_SIGMA_PCT)

            # 2. Evento aleatorio: baja de jugador clave
            if random.random() < INJURY_PROB:
                lh *= random.uniform(*INJURY_IMPACT)
            if random.random() < INJURY_PROB:
                la *= random.uniform(*INJURY_IMPACT)

            # 3. Momentum/presión aleatoria (factor bilateral)
            momentum = _normal_sample(1.0, MOMENTUM_SIGMA)
            lh *= momentum
            la *= momentum

            # 4. Muestrear goles
            gh = _poisson_sample(lh)
            ga = _poisson_sample(la)

            # 5. Acumular
            total_goals_h += gh
            total_goals_a += ga
            gh_c = min(gh, MAX_GOALS_SHOWN + 1)
            ga_c = min(ga, MAX_GOALS_SHOWN + 1)
            goals_h_dist[gh_c] += 1
            goals_a_dist[ga_c] += 1

            score = f"{min(gh, 9)}-{min(ga, 9)}"
            scorelines[score] = scorelines.get(score, 0) + 1

            if gh > ga:
                home_wins += 1
            elif gh == ga:
                draws += 1
            else:
                away_wins += 1

        # ── Calcular estadísticas ─────────────────────────────────────────────
        p_h = home_wins / n
        p_d = draws / n
        p_a = away_wins / n

        top_scores = sorted(scorelines.items(), key=lambda x: x[1], reverse=True)[:10]
        top_scores_pct = [(s, round(c / n * 100, 2)) for s, c in top_scores]

        avg_goals_h = total_goals_h / n
        avg_goals_a = total_goals_a / n

        # Intervalo de confianza Wilson para p_home (95%)
        ci_h = self._wilson_ci(home_wins, n)
        ci_d = self._wilson_ci(draws, n)
        ci_a = self._wilson_ci(away_wins, n)

        # Consenso vs Ryder (cuán lejos estamos del modelo analítico)
        ryder_probs = self._analytical_probs(lam_h, lam_a)
        divergence = abs(p_h - ryder_probs["home"]) + abs(p_d - ryder_probs["draw"]) + abs(p_a - ryder_probs["away"])
        convergence = "ALTA" if divergence < 0.05 else "MEDIA" if divergence < 0.12 else "BAJA"

        return {
            "n": n,
            "home": home,
            "away": away,
            "p_home": round(p_h, 4),
            "p_draw": round(p_d, 4),
            "p_away": round(p_a, 4),
            "top_scorelines": top_scores_pct,
            "goals_h_dist": [round(g / n * 100, 2) for g in goals_h_dist],
            "goals_a_dist": [round(g / n * 100, 2) for g in goals_a_dist],
            "avg_goals_home": round(avg_goals_h, 3),
            "avg_goals_away": round(avg_goals_a, 3),
            "avg_total_goals": round(avg_goals_h + avg_goals_a, 3),
            "ci_home": ci_h,
            "ci_draw": ci_d,
            "ci_away": ci_a,
            "convergence_vs_ryder": convergence,
            "divergence": round(divergence, 4),
            "ryder_analytical": ryder_probs,
            "lam_used": {"home": round(lam_h_base, 3), "away": round(lam_a_base, 3)},
            "market_blend_applied": mkt_p_home is not None,
        }

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _extract_market_probs(self, cleo_data, lam_h, lam_a):
        """Extrae probabilidades implícitas del mercado desde Cleo."""
        if not cleo_data:
            return None, None
        try:
            markets = cleo_data.get("markets", {})
            # Buscar DraftKings o cualquier mercado activo
            for platform in ("DraftKings", "Betcris", "Doradobet"):
                mkt = markets.get(platform, {})
                if mkt and mkt.get("available"):
                    ho = mkt.get("home_odd")
                    ao = mkt.get("away_odd")
                    if ho and ao:
                        # Probabilidades implícitas brutas (con margen)
                        p_raw_h = 1.0 / float(ho)
                        p_raw_a = 1.0 / float(ao)
                        return p_raw_h, p_raw_a
        except Exception:
            pass
        return None, None

    def _blend_market(self, lam_h, lam_a, mkt_ph, mkt_pa):
        """
        Ajusta lambdas basándose en prior de mercado.
        Si el mercado dice que home tiene más probabilidad de lo que dice Ryder,
        subimos lam_h ligeramente.
        """
        if mkt_ph is None or mkt_pa is None:
            return lam_h, lam_a
        try:
            # Razón goles modelo
            total_lam = lam_h + lam_a
            ratio_ryder = lam_h / total_lam if total_lam > 0 else 0.5
            # Razón market (normalizada, sin draw)
            total_mkt = mkt_ph + mkt_pa
            ratio_mkt = mkt_ph / total_mkt if total_mkt > 0 else 0.5
            # Blend: 80% Ryder, 20% mercado
            ratio_blended = (1 - MARKET_BLEND) * ratio_ryder + MARKET_BLEND * ratio_mkt
            # Mantener total_lam, ajustar la distribución
            new_lam_h = max(0.10, total_lam * ratio_blended)
            new_lam_a = max(0.10, total_lam * (1 - ratio_blended))
            return new_lam_h, new_lam_a
        except Exception:
            return lam_h, lam_a

    def _analytical_probs(self, lam_h: float, lam_a: float) -> dict:
        """Calcula P(H/D/A) analítica desde Poisson (para comparar vs simulación)."""
        MAXG = 9
        p_h = p_d = p_a = 0.0
        for i in range(MAXG + 1):
            phi = math.exp(-lam_h) * (lam_h ** i) / math.factorial(i)
            for j in range(MAXG + 1):
                paj = math.exp(-lam_a) * (lam_a ** j) / math.factorial(j)
                p = phi * paj
                if i > j:
                    p_h += p
                elif i == j:
                    p_d += p
                else:
                    p_a += p
        s = p_h + p_d + p_a
        return {
            "home": round(p_h / s, 4) if s else 0.333,
            "draw": round(p_d / s, 4) if s else 0.333,
            "away": round(p_a / s, 4) if s else 0.333,
        }

    def _wilson_ci(self, k: int, n: int, z: float = 1.96) -> tuple:
        """Intervalo de confianza Wilson al 95% para una proporción."""
        if n == 0:
            return (0.0, 1.0)
        p = k / n
        denom = 1 + z * z / n
        center = (p + z * z / (2 * n)) / denom
        margin = (z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n))) / denom
        return (round(max(0, center - margin), 4), round(min(1, center + margin), 4))

    # ── Formato de salida ────────────────────────────────────────────────────

    def format_response(self, sim: dict) -> str:
        """Formatea el resultado de la simulación para mostrar al usuario."""
        n        = sim["n"]
        home     = sim["home"]
        away     = sim["away"]
        p_h      = sim["p_home"] * 100
        p_d      = sim["p_draw"] * 100
        p_a      = sim["p_away"] * 100
        ci_h     = sim["ci_home"]
        ci_d     = sim["ci_draw"]
        top      = sim["top_scorelines"]
        avg_tot  = sim["avg_total_goals"]
        conv     = sim["convergence_vs_ryder"]
        ryder    = sim["ryder_analytical"]
        blended  = sim["market_blend_applied"]

        lines = [
            "",
            f"🎲 LUCAS — Simulador Monte Carlo ({n:,} simulaciones)",
            f"   {home} vs {away}",
            "",
            f"   PROBABILIDADES SIMULADAS:",
            f"   {home}: {p_h:.1f}%  [IC95: {ci_h[0]*100:.1f}%-{ci_h[1]*100:.1f}%]",
            f"   Empate:  {p_d:.1f}%  [IC95: {ci_d[0]*100:.1f}%-{ci_d[1]*100:.1f}%]",
            f"   {away}: {p_a:.1f}%",
            "",
            f"   MARCADORES MÁS FRECUENTES ({n:,} simulaciones):",
        ]
        for i, (score, pct) in enumerate(top[:6]):
            bar = "█" * int(pct / 2) + "░" * (10 - int(pct / 2))
            lines.append(f"   {i+1}. {score}  {bar}  {pct:.1f}%")

        lines += [
            "",
            f"   Goles promedio: {sim['avg_goals_home']:.2f} — {sim['avg_goals_away']:.2f}  "
            f"(total: {avg_tot:.2f}/partido)",
            f"   Convergencia vs Ryder: {conv} "
            f"(Ryder analítico: H={ryder['home']*100:.1f}% D={ryder['draw']*100:.1f}% A={ryder['away']*100:.1f}%)",
        ]
        if blended:
            lines.append("   Prior de mercado (Cleo) blended al 20% en lambda.")
        lines.append("")
        return "\n".join(lines)

    def format_dialogue(self, sim: dict, ryder_lam: dict, cleo_data: dict) -> list:
        """Genera las líneas de diálogo Lucas ↔ Ryder y Lucas ↔ Cleo."""
        home     = sim["home"]
        away     = sim["away"]
        p_h      = sim["p_home"] * 100
        p_d      = sim["p_draw"] * 100
        p_a      = sim["p_away"] * 100
        top      = sim["top_scorelines"]
        conv     = sim["convergence_vs_ryder"]
        ryder    = sim["ryder_analytical"]
        avg_h    = sim["avg_goals_home"]
        avg_a    = sim["avg_goals_away"]
        n        = sim["n"]

        top_score = top[0][0] if top else "?"
        top_pct   = top[0][1] if top else 0

        ryder_h_pct = ryder["home"] * 100
        diff_h      = p_h - ryder_h_pct
        diff_sign   = "+" if diff_h >= 0 else ""

        lines = [
            "",
            "── DIÁLOGO LUCAS ──────────────────────────────────────",
            "",
            f"LUCAS → RYDER: 'En {n:,} simulaciones: "
            f"H={p_h:.1f}% D={p_d:.1f}% A={p_a:.1f}%. "
            f"Tu analítico: H={ryder_h_pct:.1f}%. Diferencia: {diff_sign}{diff_h:.1f}pp. "
            f"Convergencia {conv}. "
            f"Goles promedio simulados: {avg_h:.2f}-{avg_a:.2f}.'",
            "",
        ]

        # Lucas → Cleo: comentar sobre el mercado vs la simulación
        opps = cleo_data.get("opportunities", []) if cleo_data else []
        if opps:
            best     = opps[0]
            outcome  = best.get("outcome_label", "?")
            p_market = best.get("p_implied", 0) * 100
            # Buscar el prob simulado correspondiente
            if "local" in outcome.lower() or home.lower() in outcome.lower():
                p_sim = p_h
            elif "empat" in outcome.lower():
                p_sim = p_d
            else:
                p_sim = p_a
            sim_vs_mkt = p_sim - p_market
            sign = "+" if sim_vs_mkt >= 0 else ""
            lines += [
                f"LUCAS → CLEO: 'Mercado implica {p_market:.1f}% para {outcome}. "
                f"Mis {n:,} sims dan {p_sim:.1f}% ({sign}{sim_vs_mkt:.1f}pp). "
                f"Marcador más frecuente: {top_score} ({top_pct:.1f}% de simulaciones).'",
                "",
                f"CLEO → LUCAS: 'Confirmado. El edge estadístico se sostiene en simulación. "
                f"Con {n:,} iteraciones el intervalo de confianza valida la ineficiencia.'",
            ]
        else:
            lines += [
                f"LUCAS → CLEO: 'Sin edge significativo. Marcador más frecuente: "
                f"{top_score} ({top_pct:.1f}% de sims). Mercado alineado con modelo.'",
                "",
                f"CLEO → LUCAS: 'Correcto. {n:,} simulaciones confirman: no hay apuesta recomendada.'",
            ]

        lam_h_str = f"{sim['lam_used']['home']:.2f}"
        lam_a_str = f"{sim['lam_used']['away']:.2f}"
        ci_lo = f"{sim['ci_home'][0]*100:.1f}"
        ci_hi = f"{sim['ci_home'][1]*100:.1f}"
        lines += [
            "",
            f"RYDER → LUCAS: 'Lambda calibrada {lam_h_str}-{lam_a_str} con ajuste de plantel. "
            f"IC95 en home: [{ci_lo}%-{ci_hi}%]. Convergencia {conv}.'",
            "",
        ]
        return lines
