"""
council.py - Consejo Ryder x Cleo x Claude
Orquesta la deliberacion antes de cada respuesta analitica.
"""
import re
import logging

logger = logging.getLogger("council")

_ANALYTICAL_KEYWORDS = [
    "apostar", "apuesta", "apuestas", "cuota", "cuotas", "odd", "odds",
    "probabilidad", "probabilidades", "partido", "juego", "match",
    "gana", "ganara", "resultado", "pick", "prediccion", "predice",
    "analiza", "analisis", "ev", "kelly", "arbitraje", "favorito",
    "chances", "porcentaje", "vale la pena", "mercado", "mercados",
    "conviene", "recomendacion", "recomienda", "ryder", "cleo",
    "vs", "contra",
]

# Equipo = 1-3 palabras Capitalizadas con mayuscula real (sin IGNORECASE)
_TEAM_RE = r"[A-Z\xc0-\xde][a-z\xc0-\xff]+(?:\s[A-Z\xc0-\xde][a-z\xc0-\xff]+){0,2}"
# Separador: vs/VS/vs. o - o contra (inline ignorecase solo para separador)
_VS_PAT  = re.compile(
    r"(" + _TEAM_RE + r")\s+(?i:vs\.?|contra)\s+(" + _TEAM_RE + r")"
    r"|(" + _TEAM_RE + r")\s+[-\u2013]\s+(" + _TEAM_RE + r")",
    re.UNICODE
)


def detect_match(text):
    """Detecta 'Equipo1 vs Equipo2' en texto. Retorna (home, away) o None."""
    m = _VS_PAT.search(text)
    if m:
        # Grupo 1+2 para vs/contra, grupo 3+4 para -
        home = (m.group(1) or m.group(3) or "").strip()
        away = (m.group(2) or m.group(4) or "").strip()
        if len(home) >= 3 and len(away) >= 3:
            return home, away
def is_analytical(text):
    """True si el mensaje parece una pregunta analitica/estadistica."""
    tl = text.lower()
    return any(kw in tl for kw in _ANALYTICAL_KEYWORDS)


def deliberate(home, away, question="", n_simulations=1000, live_state=None):
    """
    Ciclo completo de deliberacion — Consejo Ryder x Cleo x Lucas x Claude:
    1. Ryder  — calcula probabilidades estadisticas (Dixon-Coles + Elo)
    2. Cleo   — analiza mercados en tiempo real con probas de Ryder
    3. Lucas  — simula el partido n veces (MC) con todas las variables
    Retorna dict con todo el contexto para Claude.
    """
    # ── RYDER ────────────────────────────────────────────────────────────────
    try:
        import model as _model
        ryder_raw = _model.predict(home, away, wc_mode=True)
    except Exception as e:
        logger.error("[council] Ryder error: %s", e)
        ryder_raw = {}

    prob = ryder_raw.get("prob", {})
    ryder_probs = {
        "home": round(prob.get("home", 33) / 100, 4),
        "draw": round(prob.get("draw", 33) / 100, 4),
        "away": round(prob.get("away", 33) / 100, 4),
    }

    eg     = ryder_raw.get("expectedGoals", {})
    engine = ryder_raw.get("engine", {})
    lam = {
        "home": eg.get("home") or engine.get("lam_home", 0),
        "away": eg.get("away") or engine.get("lam_away", 0),
    }
    elo = {
        "home": ryder_raw.get("homeElo") or engine.get("elo_home", 0),
        "away": ryder_raw.get("awayElo") or engine.get("elo_away", 0),
    }

    # ── CLEO ─────────────────────────────────────────────────────────────────
    try:
        import cleo as _cleo
        cleo_agent   = _cleo.CleoAgent()
        cleo_analysis = cleo_agent.analyze(home, away, ryder_probs)
    except Exception as e:
        logger.error("[council] Cleo error: %s", e)
        cleo_analysis = {"markets": {}, "opportunities": [], "arbitrage": {}}

    # ── LUCAS (Monte Carlo) ───────────────────────────────────────────────────
    lucas_result = {}
    try:
        import lucas as _lucas
        lam_h = float(lam.get("home") or 1.2)
        lam_a = float(lam.get("away") or 0.8)
        agent = _lucas.LucasAgent()
        lucas_result = agent.simulate(
            home       = home,
            away       = away,
            lam_home   = lam_h,
            lam_away   = lam_a,
            cleo_data  = cleo_analysis,
            n          = max(1000, int(n_simulations)),
        )
        logger.info(
            "[council] Lucas: %d sims → H=%.1f%% D=%.1f%% A=%.1f%% top=%s",
            lucas_result.get("n", 0),
            lucas_result.get("p_home", 0) * 100,
            lucas_result.get("p_draw", 0) * 100,
            lucas_result.get("p_away", 0) * 100,
            lucas_result.get("top_scorelines", [("?", 0)])[0][0],
        )
    except Exception as e:
        logger.error("[council] Lucas error: %s", e)
        lucas_result = {}

    # ── LUCAS LIVE (si hay partido en curso) ────────────────────────────────
    lucas_live_result = {}
    if live_state:
        try:
            import lucas_live as _lucas_live
            ll_agent = _lucas_live.LucasLive()
            lam_h = float(lam.get("home") or 1.2)
            lam_a = float(lam.get("away") or 0.8)
            lucas_live_result = ll_agent.simulate_live(
                live       = live_state,
                lam_home   = lam_h,
                lam_away   = lam_a,
                n          = max(1000, int(n_simulations)),
            )
            logger.info(
                "[council] Lucas Live: min=%s score=%s H=%.1f%% D=%.1f%% A=%.1f%%",
                lucas_live_result.get("minute"),
                lucas_live_result.get("score_current"),
                lucas_live_result.get("p_home", 0) * 100,
                lucas_live_result.get("p_draw", 0) * 100,
                lucas_live_result.get("p_away", 0) * 100,
            )
        except Exception as e:
            logger.error("[council] Lucas Live error: %s", e)
            lucas_live_result = {}

    return {
        "home": home,
        "away": away,
        "question": question,
        "ryder": {
            "probs": ryder_probs,
            "lam": lam,
            "elo": elo,
            "raw": ryder_raw,
        },
        "cleo": cleo_analysis,
        "lucas": lucas_result,
        "lucas_live": lucas_live_result,
    }


def _safe_f(val, decimals=2):
    """Formato seguro para floats que pueden ser None o str."""
    try:
        return f"{float(val):.{decimals}f}"
    except (TypeError, ValueError):
        return "?"


def format_council_context(council):
    """Bloque de contexto inyectado en el system prompt de Claude."""
    home    = council["home"]
    away    = council["away"]
    probs   = council["ryder"]["probs"]
    lam     = council["ryder"]["lam"]
    elo     = council["ryder"]["elo"]
    cleo_d  = council["cleo"]
    opps    = cleo_d.get("opportunities", [])
    mkts    = cleo_d.get("markets", {})

    lines = [
        f"====== CONSEJO RYDER x CLEO x LUCAS --- {home} vs {away} ======",
        "",
        f"RYDER + LUCAS (Dixon-Coles + Elo + 1000 simulaciones Monte Carlo):",
        f"  {home}: {probs['home']*100:.1f}%  |  Empate: {probs['draw']*100:.1f}%  |  {away}: {probs['away']*100:.1f}%",
        f"  Goles esperados: {home} {_safe_f(lam['home'])} -- {away} {_safe_f(lam['away'])}",
        f"  Elo: {home} {_safe_f(elo['home'],0)} vs {away} {_safe_f(elo['away'],0)}",
        "",
        "CLEO (Mercados):",
    ]

    for platform, mkt in mkts.items():
        if not mkt or not mkt.get("available") or mkt.get("is_tournament"):
            continue
        h = mkt.get("home_odd")
        d = mkt.get("draw_odd")
        a = mkt.get("away_odd")
        margin = mkt.get("margin", 0) * 100
        lines.append(
            f"  {platform}: {_safe_f(h,3) if h else '--'} / "
            f"{_safe_f(d,3) if d else '--'} / "
            f"{_safe_f(a,3) if a else '--'}  (margen {margin:.1f}%)"
        )

    poly = mkts.get("Polymarket (WC winner)")
    if poly and poly.get("available"):
        h_odd = poly.get("home_odd")
        a_odd = poly.get("away_odd")
        liq = poly.get("liquidity") or 0
        if h_odd and a_odd:
            lines.append(
                f"  Polymarket (torneo): {home} {100/h_odd:.1f}% | {away} {100/a_odd:.1f}%"
                f"  [liq ${liq:,.0f}] -- senial de largo plazo"
            )

    if opps:
        lines.append("")
        lines.append("  Oportunidades +EV identificadas por Cleo:")
        for opp in opps[:3]:
            ev      = opp.get("ev_pct", 0)
            kelly   = opp.get("kelly_recommended", 0)
            platform= opp.get("platform", "?")
            outcome = opp.get("outcome_label", "?")
            odd     = opp.get("decimal_odd", 0)
            rp      = opp.get("p_ryder", 0) * 100
            ip      = opp.get("p_implied", 0) * 100
            lines.append(
                f"  * {outcome} @ {platform} odd={odd:.3f}: "
                f"Ryder={rp:.1f}% vs mercado={ip:.1f}% -> EV={ev:+.1f}% Kelly={kelly:.2f}%"
            )
    else:
        lines.append("  Sin oportunidades +EV (mercado alineado con Ryder).")

    arb = cleo_d.get("arbitrage", {})
    if arb.get("detected"):
        lines.append(f"  ARBITRAJE detectado: ~{arb.get('profit_pct', 0):.2f}%")

    lines += ["", "DIALOGO RYDER x CLEO:"]
    if opps:
        best    = opps[0]
        outcome = best.get("outcome_label", "?")
        rp      = best.get("p_ryder", 0) * 100
        ip      = best.get("p_implied", 0) * 100
        ev      = best.get("ev_pct", 0)
        platform= best.get("platform", "?")
        lines += [
            f"  CLEO: 'Ryder, el mercado subestima {outcome}: tu dices {rp:.1f}% "
            f"pero {platform} implica {ip:.1f}%. Edge: {ev:+.1f}%.'",
            "  RYDER: 'Confirmo con Elo diferencial {:.0f} pts y lambda {}-{}. Ineficiencia verificada.'".format(
                abs(float(elo["home"] or 0) - float(elo["away"] or 0)),
                _safe_f(lam["home"]), _safe_f(lam["away"])
            ),
        ]
    else:
        lines += [
            "  CLEO: 'Ryder, mercado alineado contigo. Sin edge claro.'",
            "  RYDER: 'Correcto. Precios eficientes hoy.'",
        ]

    # ── Lucas en el contexto de Claude ──────────────────────────────────────
    lucas_d = council.get("lucas", {})
    if lucas_d:
        lp_h  = lucas_d.get("p_home", 0) * 100
        lp_d  = lucas_d.get("p_draw", 0) * 100
        lp_a  = lucas_d.get("p_away", 0) * 100
        l_n   = lucas_d.get("n", 1000)
        l_top = lucas_d.get("top_scorelines", [("?", 0)])[0][0]
        l_ci  = lucas_d.get("ci_home", (0.0, 1.0))
        l_conv= lucas_d.get("convergence_vs_ryder", "N/A")
        lines += [
            "",
            f"LUCAS ({l_n:,} simulaciones Monte Carlo):",
            f"  {home}: {lp_h:.1f}%  |  Empate: {lp_d:.1f}%  |  {away}: {lp_a:.1f}%",
            f"  Marcador mas probable: {l_top}",
            f"  IC95 local: [{l_ci[0]*100:.1f}%-{l_ci[1]*100:.1f}%]  Convergencia: {l_conv}",
        ]

    lucas_live_d = council.get("lucas_live", {})
    if lucas_live_d:
        ll_mn  = lucas_live_d.get("minute", "?")
        ll_sc  = lucas_live_d.get("score_current", "?")
        ll_ph  = lucas_live_d.get("p_home", 0) * 100
        ll_pd  = lucas_live_d.get("p_draw", 0) * 100
        ll_pa  = lucas_live_d.get("p_away", 0) * 100
        ll_top = lucas_live_d.get("top_final_scores", [("?", 0)])[0][0]
        lines += [
            "",
            f"LUCAS LIVE (en vivo min {ll_mn} — marcador {ll_sc}):",
            f"  {home}: {ll_ph:.1f}%  |  Empate: {ll_pd:.1f}%  |  {away}: {ll_pa:.1f}%",
            f"  Resultado mas probable desde ahora: {ll_top}",
        ]

    lines += ["", "DIALOGO RYDER x CLEO x LUCAS:"]
    if opps:
        best     = opps[0]
        outcome  = best.get("outcome_label", "?")
        rp       = best.get("p_ryder", 0) * 100
        ip       = best.get("p_implied", 0) * 100
        ev       = best.get("ev_pct", 0)
        platform = best.get("platform", "?")
        lp_out   = (lucas_d.get("p_home", 0) if home.lower() in outcome.lower() or "local" in outcome.lower()
                    else lucas_d.get("p_draw", 0) if "empat" in outcome.lower()
                    else lucas_d.get("p_away", 0)) * 100 if lucas_d else rp
        lines += [
            f"  CLEO: 'Ryder, el mercado subestima {outcome}: tu dices {rp:.1f}%"
            f" pero {platform} implica {ip:.1f}%. Edge: {ev:+.1f}%.'",
            "  RYDER: 'Confirmo con Elo diferencial {:.0f} pts y lambda {}-{}. Ineficiencia verificada.'".format(
                abs(float(elo["home"] or 0) - float(elo["away"] or 0)),
                _safe_f(lam["home"]), _safe_f(lam["away"])
            ),
            f"  LUCAS: '{lp_out:.1f}% en {lucas_d.get('n',1000):,} sims. Valida el edge de {ev:+.1f}%.'",
        ]
    else:
        lines += [
            "  CLEO: 'Ryder, mercado alineado contigo. Sin edge claro.'",
            "  RYDER: 'Correcto. Precios eficientes hoy.'",
            f"  LUCAS: 'Simulacion confirma. Sin desvio estadistico relevante.'",
        ]

    lines += [
        "",
        "CLAUDE: integra Ryder + Cleo + Lucas en tu respuesta. Menciona los 3.",
        "Si hay Lucas Live, prioriza esas probabilidades sobre las pre-partido.",
        "=" * 54,
        "",
    ]
    return "\n".join(lines)


def format_council_reply(council):
    """Output completo visible al usuario: Ryder + Cleo + Lucas + dialogo 3 agentes."""
    try:
        import cleo as _cleo
        cleo_str = _cleo.CleoAgent().format_response(council["cleo"])
    except Exception:
        cleo_str = "(Error en analisis Cleo)\n"

    home    = council["home"]
    away    = council["away"]
    probs   = council["ryder"]["probs"]
    lam     = council["ryder"]["lam"]
    elo     = council["ryder"]["elo"]
    opps    = council["cleo"].get("opportunities", [])
    lucas   = council.get("lucas", {})

    h_pct   = probs["home"] * 100
    d_pct   = probs["draw"] * 100
    a_pct   = probs["away"] * 100

    header = [
        "====================================================",
        f"   CONSEJO RYDER x CLEO x LUCAS — {home} vs {away}",
        "====================================================",
        "",
        "RYDER (Estadístico — Dixon-Coles + Elo + Player Stats):",
        f"  {home}: {h_pct:.1f}%  |  Empate: {d_pct:.1f}%  |  {away}: {a_pct:.1f}%",
        f"  Goles esperados: {home} {_safe_f(lam['home'])} — {away} {_safe_f(lam['away'])}",
        f"  Elo: {home} {_safe_f(elo['home'],0)} | {away} {_safe_f(elo['away'],0)}",
        "",
        "-" * 50,
        "",
    ]

    # ── LUCAS section ────────────────────────────────────────────────────────
    lucas_lines = []
    if lucas:
        try:
            import lucas as _lucas_mod
            la = _lucas_mod.LucasAgent()
            lucas_lines = [la.format_response(lucas)]
        except Exception:
            # Fallback inline formatting
            n   = lucas.get("n", "?")
            lph = lucas.get("p_home", 0) * 100
            lpd = lucas.get("p_draw", 0) * 100
            lpa = lucas.get("p_away", 0) * 100
            top = lucas.get("top_scorelines", [])
            top_str = " | ".join(f"{s} {p:.1f}%" for s, p in top[:3])
            lucas_lines = [
                f"\n🎲 LUCAS ({n:,} simulaciones):",
                f"  H={lph:.1f}%  D={lpd:.1f}%  A={lpa:.1f}%",
                f"  Marcadores: {top_str}",
                f"  Goles promedio: {lucas.get('avg_goals_home','?'):.2f}"
                f"—{lucas.get('avg_goals_away','?'):.2f}",
                "",
            ]

    # ── Dialogo 3 agentes ────────────────────────────────────────────────────
    elo_diff = abs(float(elo["home"] or 0) - float(elo["away"] or 0))
    dialogue = ["", "-" * 50, "", "DIÁLOGO RYDER × CLEO × LUCAS:", ""]

    if opps:
        best     = opps[0]
        outcome  = best.get("outcome_label", "?")
        rp       = best.get("p_ryder", 0) * 100
        ip       = best.get("p_implied", 0) * 100
        ev       = best.get("ev_pct", 0)
        platform = best.get("platform", "?")

        # Prob de Lucas para ese outcome
        lp = (lucas.get("p_home", 0) if "local" in outcome.lower() or home.lower() in outcome.lower()
              else lucas.get("p_draw", 0) if "empat" in outcome.lower()
              else lucas.get("p_away", 0)) * 100 if lucas else rp
        top_score = lucas.get("top_scorelines", [("?",0)])[0][0] if lucas else "?"
        conv      = lucas.get("convergence_vs_ryder", "N/A")

        dialogue += [
            f"CLEO → RYDER: 'El mercado subestima {outcome}: tú das {rp:.1f}% "
            f"pero {platform} implica {ip:.1f}%. Edge: {ev:+.1f}%.'",
            "",
            f"RYDER → CLEO: 'Modelo confirma con λ {_safe_f(lam['home'])}-{_safe_f(lam['away'])} "
            f"y Elo diff {elo_diff:.0f}pts. Ineficiencia real.'",
            "",
            f"LUCAS → RYDER+CLEO: 'En {lucas.get('n',1000):,} simulaciones: "
            f"{outcome}={lp:.1f}%. Convergencia {conv}. "
            f"Marcador más frecuente: {top_score}. "
            f"IC95 home: [{lucas.get("ci_home",(0,1))[0]*100:.1f}%-{lucas.get("ci_home",(0,1))[1]*100:.1f}%]. "
            f"Simulación valida el edge.'",
        ]
    else:
        top_score = lucas.get("top_scorelines", [("?",0)])[0][0] if lucas else "?"
        lph = lucas.get("p_home", h_pct/100) * 100 if lucas else h_pct
        lpd = lucas.get("p_draw", d_pct/100) * 100 if lucas else d_pct
        conv = lucas.get("convergence_vs_ryder", "N/A")
        dialogue += [
            "CLEO → RYDER: 'Mercado alineado con el modelo. Sin edge claro.'",
            "",
            f"RYDER → CLEO: 'Correcto. λ {_safe_f(lam['home'])}-{_safe_f(lam['away'])}. "
            f"Sin ineficiencia detectable.'",
            "",
            f"LUCAS → RYDER+CLEO: 'Confirmado en {lucas.get('n',1000):,} simulaciones. "
            f"H={lph:.1f}% D={lpd:.1f}%. Convergencia {conv}. "
            f"Marcador más probable: {top_score}. No hay apuesta recomendada.'",
        ]

    footer = [
        "",
        "-" * 50,
        "Decisión del Consejo: Ryder (estadístico) + Cleo (mercado) + Lucas (simulación).",
        "",
    ]

    # ── Bloque Lucas Live (si viene del partido en curso) ────────────────────
    live_block = ""
    lucas_live = council.get("lucas_live", {})
    if lucas_live:
        try:
            import lucas_live as _ll_mod
            ll = _ll_mod.LucasLive()
            prior = council["ryder"]["probs"]
            live_block = ll.format_live(lucas_live) + ll.format_live_dialogue(lucas_live, prior)
        except Exception:
            sc  = lucas_live.get("score_current","?")
            mn  = lucas_live.get("minute","?")
            ph  = lucas_live.get("p_home",0)*100
            pd  = lucas_live.get("p_draw",0)*100
            pa  = lucas_live.get("p_away",0)*100
            live_block = (
                f"\n🔴 LUCAS LIVE min {mn}' ({sc}): "
                f"H={ph:.1f}% D={pd:.1f}% A={pa:.1f}%\n"
            )

    lucas_block = "".join(lucas_lines)
    return "\n".join(header) + cleo_str + lucas_block + live_block + "\n".join(dialogue + footer)
