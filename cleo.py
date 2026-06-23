"""
cleo.py — Agente Cleo: Estratega de Mercados de Predicción y Arbitraje
Sistema: ProGol CR / Mundial 2026
Versión: 1.0.0

Dependencias: solo stdlib Python 3.8+
Integración: usa model.predict() de Ryder como baseline de probabilidades
"""

import os
import json
import time
import logging
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime, timezone
from typing import Optional

# ── Logging con prefijo [cleo] ────────────────────────────────────────────────
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger("[cleo]")

# ── Constantes ─────────────────────────────────────────────────────────────────
CACHE_TTL = 300             # segundos — igual que el resto del sistema
MAX_KELLY_CAP = 0.15        # 15% bankroll máximo por pick
KELLY_FRACTION = 0.25       # 1/4 Kelly como default conservador
MIN_EV_REPORT = 2.0         # EV% mínimo para reportar oportunidad
MIN_EV_RECOMMEND = 5.0      # EV% mínimo para recomendar activamente
MIN_LIQUIDITY_WARN = 5000   # USD — alerta de slippage en Polymarket

POLYMARKET_BASE = "https://gamma-api.polymarket.com"
KALSHI_BASE     = "https://trading-api.kalshi.com/trade-api/v2"
CONFIG_PATH     = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")
HISTORY_PATH    = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "picks_history.json")

VERSION = "1.0.0"


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES MATEMÁTICAS
# ══════════════════════════════════════════════════════════════════════════════

def devig_multiplicativo(odds_list: list) -> list:
    """
    Elimina el margen (vig) de una lista de odds decimales.
    Retorna lista de probabilidades verdaderas que suman 1.0.

    Args:
        odds_list: [home_odd, draw_odd, away_odd] en formato decimal europeo

    Returns:
        [p_home, p_draw, p_away] normalizadas (suman 1.0)
    """
    if not odds_list or None in odds_list or any(o <= 0 for o in odds_list):
        return []
    p_brutas = [1.0 / o for o in odds_list]
    total = sum(p_brutas)
    if total == 0:
        return []
    return [round(p / total, 6) for p in p_brutas]


def devig_shin(odds_list: list) -> list:
    """
    Método Shin para devig. Más preciso en mercados asimétricos.
    Usar cuando algún outcome tiene p_bruta < 0.15.

    Args:
        odds_list: lista de odds decimales

    Returns:
        lista de probabilidades verdaderas normalizadas
    """
    if not odds_list or None in odds_list or any(o <= 0 for o in odds_list):
        return []

    p_brutas = [1.0 / o for o in odds_list]
    n = len(p_brutas)
    total = sum(p_brutas)

    if total <= 1.0:
        # Sin vig o con odds favorables — retornar directamente
        return [round(p / total, 6) for p in p_brutas]

    # Aproximación de z (parámetro Shin)
    min_p = min(p_brutas)
    denominator = total - n * min_p
    if denominator == 0:
        return devig_multiplicativo(odds_list)  # fallback

    z = (total - 1.0) / denominator
    z = max(0.0, min(z, 0.5))  # clamp z entre 0 y 0.5

    p_shin = []
    for p in p_brutas:
        discriminant = z ** 2 + 4 * (1 - z) * p / total
        if discriminant < 0:
            p_shin.append(p / total)
            continue
        p_true = (discriminant ** 0.5 - z) / (2 * (1 - z)) if (1 - z) != 0 else p / total
        p_shin.append(round(p_true, 6))

    # Renormalizar por seguridad
    total_shin = sum(p_shin)
    if total_shin > 0:
        p_shin = [round(p / total_shin, 6) for p in p_shin]

    return p_shin


def calculate_ev(p_ryder: float, decimal_odd: float) -> float:
    """
    Expected Value de una apuesta.

    EV = p_ryder * (decimal_odd - 1) - (1 - p_ryder)
       = p_ryder * decimal_odd - 1

    Returns:
        EV como porcentaje (ej: 13.1 para +13.1%)
    """
    if decimal_odd <= 1.0 or p_ryder <= 0:
        return -100.0
    return round((p_ryder * decimal_odd - 1) * 100, 4)


def calculate_kelly(p_ryder: float, decimal_odd: float) -> float:
    """
    Kelly Criterion completo.

    f* = (p * b - (1-p)) / b  donde b = decimal_odd - 1

    Returns:
        Fracción del bankroll (0.0 a 1.0). Nunca negativo.
    """
    if decimal_odd <= 1.0 or p_ryder <= 0:
        return 0.0
    b = decimal_odd - 1.0
    f = (p_ryder * b - (1.0 - p_ryder)) / b
    return max(0.0, round(f, 6))


def kelly_recommended(p_ryder: float, decimal_odd: float) -> float:
    """
    Kelly fraccional con cap de seguridad.
    Usa 1/4 Kelly con máximo de MAX_KELLY_CAP.

    Returns:
        Fracción recomendada del bankroll (0.0 a MAX_KELLY_CAP)
    """
    k = calculate_kelly(p_ryder, decimal_odd)
    return round(min(k * KELLY_FRACTION, MAX_KELLY_CAP), 4)


def detect_arbitrage(markets: dict) -> dict:
    """
    Detecta arbitraje cross-platform.
    Busca los mejores odds para cada outcome en todas las plataformas disponibles.

    Args:
        markets: dict de dicts con datos normalizados por plataforma

    Returns:
        dict con detected (bool), arb_sum, profit_pct, best_odds
    """
    outcome_keys = [("home", "home_odd"), ("draw", "draw_odd"), ("away", "away_odd")]
    best = {}

    for outcome, key in outcome_keys:
        best_odd = None
        best_plat = None
        for platform, data in markets.items():
            if not data or not data.get("available"):
                continue
            odd = data.get(key)
            if odd and odd > 1.0:
                if best_odd is None or odd > best_odd:
                    best_odd = odd
                    best_plat = platform
        best[outcome] = {"odd": best_odd, "platform": best_plat}

    # Solo calcular arb si tenemos los 3 outcomes
    if any(v["odd"] is None for v in best.values()):
        return {
            "detected": False,
            "arb_sum": None,
            "profit_pct": 0.0,
            "best_odds": best,
            "warning": None
        }

    arb_sum = sum(1.0 / v["odd"] for v in best.values())
    profit_pct = round((1.0 - arb_sum) / arb_sum * 100, 2) if arb_sum < 1.0 else 0.0

    return {
        "detected": arb_sum < 1.0,
        "arb_sum": round(arb_sum, 4),
        "profit_pct": profit_pct,
        "best_odds": best,
        "warning": (
            "Requiere ejecución simultánea. Slippage y límites de apuesta "
            "pueden erosionar la ganancia teórica."
        ) if arb_sum < 1.0 else None
    }


# ══════════════════════════════════════════════════════════════════════════════
# UTILIDADES HTTP
# ══════════════════════════════════════════════════════════════════════════════

def _http_get(url: str, headers: Optional[dict] = None, timeout: int = 8) -> Optional[dict]:
    """
    HTTP GET con manejo de errores silencioso.

    Returns:
        dict parseado de JSON, o None si falla
    """
    try:
        req = urllib.request.Request(url, headers=headers or {})
        req.add_header("User-Agent", "ProGolCR-Cleo/1.0")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw)
    except urllib.error.HTTPError as e:
        logger.warning(f"[cleo] HTTP {e.code} en {url}")
        return None
    except urllib.error.URLError as e:
        logger.warning(f"[cleo] URL error en {url}: {e.reason}")
        return None
    except json.JSONDecodeError:
        logger.warning(f"[cleo] JSON inválido desde {url}")
        return None
    except Exception as e:
        logger.warning(f"[cleo] Error inesperado en {url}: {e}")
        return None


def _load_config() -> dict:
    """Carga config.json. Retorna dict vacío si no existe."""
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def _now_utc() -> str:
    """Timestamp ISO 8601 en UTC."""
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ══════════════════════════════════════════════════════════════════════════════
# CACHE SIMPLE CON TTL
# ══════════════════════════════════════════════════════════════════════════════

_cache = {}  # { "key": {"data": ..., "ts": float} }


def _cache_get(key: str) -> Optional[dict]:
    """Retorna valor cacheado si aún válido (TTL = CACHE_TTL segundos)."""
    entry = _cache.get(key)
    if entry and (time.time() - entry["ts"]) < CACHE_TTL:
        return entry["data"]
    return None


def _cache_set(key: str, data: dict):
    """Guarda dato en cache con timestamp actual."""
    _cache[key] = {"data": data, "ts": time.time()}


# ══════════════════════════════════════════════════════════════════════════════
# CLASE CLEOPLATAFORMA — ESTRUCTURA NORMALIZADA
# ══════════════════════════════════════════════════════════════════════════════

def _make_market_dict(
    platform: str,
    home_odd: Optional[float],
    draw_odd: Optional[float],
    away_odd: Optional[float],
    margin: float = 0.0,
    liquidity: Optional[float] = None,
    available: bool = True,
    note: str = "",
    is_tournament: bool = False
) -> dict:
    """Construye el dict normalizado de datos de mercado."""
    return {
        "platform": platform,
        "home_odd": home_odd,
        "draw_odd": draw_odd,
        "away_odd": away_odd,
        "margin": round(margin, 4),
        "liquidity": liquidity,
        "available": available,
        "note": note,
        "is_tournament": is_tournament,
        "timestamp": _now_utc()
    }


def _calculate_margin(odds_list: list) -> float:
    """Calcula el margen (overround) como fracción 0-1."""
    if None in odds_list or not odds_list:
        return 0.0
    p_brutas = [1.0 / o for o in odds_list if o and o > 0]
    if not p_brutas:
        return 0.0
    overround = sum(p_brutas) - 1.0
    return round(overround / sum(p_brutas), 4)


# ══════════════════════════════════════════════════════════════════════════════
# FETCHERS DE PLATAFORMAS
# ══════════════════════════════════════════════════════════════════════════════

# Cache global de mercados Polymarket WC — se carga una vez y se reutiliza
_poly_wc_markets_cache = {"data": None, "ts": 0}
POLY_WC_CACHE_TTL = 600  # 10 min


def _load_polymarket_wc_markets():
    """Carga todos los mercados WC2026 de Polymarket y los cachea globalmente."""
    global _poly_wc_markets_cache
    now = time.time()
    if _poly_wc_markets_cache["data"] and (now - _poly_wc_markets_cache["ts"]) < POLY_WC_CACHE_TTL:
        return _poly_wc_markets_cache["data"]

    url = f"{POLYMARKET_BASE}/markets?active=true&limit=200&tag=world-cup-2026"
    data = _http_get(url)
    if not data:
        return []

    markets = data if isinstance(data, list) else []
    # Solo conservar los de WC (filtro por texto)
    wc = [m for m in markets if any(
        k in m.get("question", "").lower()
        for k in ["world cup", "fifa", "mundial", "copa del mundo"]
    )]
    _poly_wc_markets_cache = {"data": wc, "ts": now}
    logger.info(f"[cleo] Polymarket WC cache: {len(wc)} mercados cargados")
    return wc


def fetch_polymarket(home: str, away: str) -> dict:
    """
    Obtiene precios de Polymarket WC 2026 para ambos equipos.

    Polymarket tiene mercados de ganador del torneo (binarios YES/NO, alta liquidez).
    No hay mercados 1X2 por partido individual. Esta función retorna:
    - home_odd: equivalente decimal de P(home gana el torneo)
    - away_odd: equivalente decimal de P(away gana el torneo)
    - Liquidez millonaria en USD

    Returns:
        dict normalizado con odds de torneo (señal de largo plazo)
    """
    cache_key = f"polymarket_{home}_{away}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    logger.info(f"[cleo] Polymarket fetch: {home} vs {away}")

    wc_markets = _load_polymarket_wc_markets()

    home_price = None
    away_price = None
    home_liq = 0.0
    away_liq = 0.0

    home_lower = home.lower()
    away_lower = away.lower()

    for market in wc_markets:
        question = market.get("question", "").lower()
        outcomes_raw = market.get("outcomes", [])
        outcomes = json.loads(outcomes_raw) if isinstance(outcomes_raw, str) else outcomes_raw
        prices_raw = market.get("outcomePrices", [])
        prices = json.loads(prices_raw) if isinstance(prices_raw, str) else prices_raw
        liq = float(market.get("liquidity") or 0)

        # Match equipo: buscar nombre en la pregunta
        is_home_market = home_lower in question
        is_away_market = away_lower in question

        if not is_home_market and not is_away_market:
            continue

        # Extraer precio YES
        for i, oc in enumerate(outcomes):
            if oc.lower() == "yes" and i < len(prices):
                try:
                    p = float(prices[i])
                    if 0 < p < 1:
                        if is_home_market and home_price is None:
                            home_price = p
                            home_liq = liq
                        elif is_away_market and away_price is None:
                            away_price = p
                            away_liq = liq
                        break
                except (ValueError, TypeError):
                    pass

        if home_price and away_price:
            break

    def safe_dec(p):
        if p and 0 < p < 1:
            return round(1.0 / p, 4)
        return None

    home_odd = safe_dec(home_price)
    away_odd = safe_dec(away_price)
    total_liq = home_liq + away_liq
    available = home_odd is not None or away_odd is not None

    note = "Mercados de torneo WC2026 (ganador del Mundial) — alta liquidez, señal de largo plazo."
    if not available:
        note = f"Sin mercados de torneo en Polymarket para {home} o {away}."

    result = _make_market_dict(
        "Polymarket (WC winner)",
        home_odd, None, away_odd,
        margin=0.0,
        liquidity=total_liq if total_liq > 0 else None,
        available=available,
        note=note,
        is_tournament=True
    )
    _cache_set(cache_key, result)
    logger.info(f"[cleo] Polymarket OK: {home}={home_price} ({home_odd}) {away}={away_price} ({away_odd}) liq=${total_liq:,.0f}")
    return result


def fetch_kalshi(home: str, away: str) -> dict:
    """
    Obtiene precios de Kalshi (solo referencial — requiere cuenta USA para operar).

    Usa endpoint público read-only de Kalshi.
    Kalshi tiende a tener mercados de ganador del torneo más que partido específico.

    Returns:
        dict normalizado de mercado (always note: referencial, no operable desde CR)
    """
    cache_key = f"kalshi_{home}_{away}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    logger.info(f"[cleo] Kalshi fetch (referencial): {home} vs {away}")

    # Buscar serie FIFA en Kalshi
    url = f"{KALSHI_BASE}/markets?series_ticker=FIFA&limit=100"
    data = _http_get(url, timeout=6)

    home_odd = None
    draw_odd = None
    away_odd = None
    home_lower = home.lower()
    away_lower = away.lower()

    if data:
        markets_list = data.get("markets", [])
        for market in markets_list:
            title = market.get("title", "").lower()
            if home_lower not in title and away_lower not in title:
                continue

            yes_ask = market.get("yes_ask") or market.get("yes_bid")
            no_ask  = market.get("no_ask")  or market.get("no_bid")

            try:
                yes_price = float(yes_ask) if yes_ask else None
                no_price  = float(no_ask)  if no_ask  else None
            except (ValueError, TypeError):
                continue

            # Kalshi es binario: mapear yes_price a home, no_price a away
            if yes_price and 0 < yes_price < 1:
                home_odd = round(1.0 / yes_price, 4)
            if no_price and 0 < no_price < 1:
                away_odd = round(1.0 / no_price, 4)
            break

    available = home_odd is not None

    result = _make_market_dict(
        "Kalshi (ref)",
        home_odd, draw_odd, away_odd,
        margin=0.02,  # spread típico estimado
        liquidity=None,
        available=available,
        note="Solo referencial. Requiere cuenta USA verificada para operar. No disponible desde CR."
    )
    _cache_set(cache_key, result)
    logger.info(f"[cleo] Kalshi ref: home={home_odd} (referencial)")
    return result


def fetch_doradobet(home: str, away: str) -> dict:
    """
    Obtiene odds reales del mercado via ESPN/DraftKings (consenso de mercado).

    Doradobet usa VirtualSoft Swarm (WebSocket) para odds en tiempo real — no
    accesible via HTTP simple. En su lugar, usamos ESPN/DraftKings que cubre todos
    los partidos del WC 2026 sin API key y refleja el consenso de mercado.

    La sesión Doradobet activa (doradobet_session.json) se usa para verificar
    que tenemos acceso válido. Los precios vienen de ESPN/DK.

    Returns:
        dict normalizado de mercado con odds reales del mercado
    """
    cache_key = f"doradobet_{home}_{away}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    logger.info(f"[cleo] DraftKings/ESPN odds fetch: {home} vs {away}")

    # Verificar sesión Doradobet activa
    session_ok = False
    doro_session_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "doradobet_session.json")
    try:
        with open(doro_session_path) as f:
            sess = json.load(f)
        session_ok = sess.get("logged_in", False)
    except Exception:
        pass

    # Obtener odds via ESPN/DK — cubre WC 2026 sin key
    try:
        import sys as _sys
        _mod_dir = os.path.dirname(os.path.abspath(__file__))
        if _mod_dir not in _sys.path:
            _sys.path.insert(0, _mod_dir)
        import integrations as _integ

        odds_data = _integ.get_match_odds(home, away)

        if not odds_data:
            result = _make_market_dict(
                "DraftKings/ESPN", None, None, None, available=False,
                note=f"Sin odds disponibles para {home} vs {away} en ESPN/DK."
            )
            _cache_set(cache_key, result)
            return result

        # get_match_odds retorna dict con best_home, best_draw, best_away en decimal
        home_odd = odds_data.get("best_home")
        draw_odd = odds_data.get("best_draw")
        away_odd = odds_data.get("best_away")

        # También puede estar en bookmakers list
        if not home_odd:
            bks = odds_data.get("bookmakers", [])
            for bk in bks:
                for mkt in (bk.get("markets") or []):
                    if mkt.get("key") in ("h2h", "1x2"):
                        outcomes_list = mkt.get("outcomes", [])
                        for oc in outcomes_list:
                            name = oc.get("name", "").lower()
                            price = oc.get("price")
                            if price:
                                try:
                                    price = float(price)
                                    if home.lower() in name:
                                        home_odd = home_odd or price
                                    elif away.lower() in name:
                                        away_odd = away_odd or price
                                    elif "draw" in name:
                                        draw_odd = draw_odd or price
                                except (ValueError, TypeError):
                                    pass

        odds_list = [o for o in [home_odd, draw_odd, away_odd] if o]
        margin = _calculate_margin(odds_list) if len(odds_list) >= 2 else 0.04

        platform_label = "DraftKings" if odds_data.get("source") == "espn-dk" else "Mercado (ESPN)"
        doro_note = " | Sesión Doradobet activa ✓" if session_ok else " | Sesión Doradobet no verificada"

        result = _make_market_dict(
            platform_label,
            home_odd, draw_odd, away_odd,
            margin=margin,
            liquidity=None,
            available=bool(home_odd or away_odd),
            note=f"Odds de mercado en tiempo real (ESPN/DraftKings){doro_note}"
        )
        _cache_set(cache_key, result)
        logger.info(f"[cleo] DK/ESPN OK: {home_odd}/{draw_odd}/{away_odd} margen={margin:.1%}")
        return result

    except Exception as e:
        logger.warning(f"[cleo] ESPN/DK fetch error: {e}")
        result = _make_market_dict(
            "DraftKings/ESPN", None, None, None, available=False,
            note=f"Error obteniendo odds: {e}"
        )
        _cache_set(cache_key, result)
        return result


def _parse_doradobet_html(html: str, home: str, away: str) -> tuple:
    """
    Parsea el HTML de Doradobet buscando odds para el partido.

    Estrategia:
    - Buscar el nombre de los equipos en el HTML
    - Extraer los 3 valores numéricos decimales más cercanos

    Returns:
        (home_odd, draw_odd, away_odd) — cada uno float o None
    """
    import re

    home_lower = home.lower()
    away_lower = away.lower()
    html_lower = html.lower()

    # Verificar que el partido está en la página
    if home_lower not in html_lower and away_lower not in html_lower:
        return None, None, None

    # Buscar sección del partido
    # Patrón genérico: valores decimales tipo "1.70" "3.90" "5.50" cerca de los equipos
    # Ajustar este regex según el layout real de Doradobet en producción

    # Buscar el índice donde aparece el equipo home
    idx = html_lower.find(home_lower)
    if idx == -1:
        idx = html_lower.find(away_lower)
    if idx == -1:
        return None, None, None

    # Tomar un bloque de 2000 chars alrededor del partido
    snippet = html[max(0, idx - 200): min(len(html), idx + 2000)]

    # Buscar todos los decimales con formato X.XX o XX.XX (odds deportivas)
    pattern = r'\b(\d{1,2}\.\d{2})\b'
    matches = re.findall(pattern, snippet)

    # Filtrar valores en rango razonable para odds deportivas (1.01 a 50.0)
    odds_found = []
    for m in matches:
        val = float(m)
        if 1.01 <= val <= 50.0:
            odds_found.append(val)

    # Eliminar duplicados preservando orden
    seen = set()
    odds_unique = []
    for o in odds_found:
        if o not in seen:
            seen.add(o)
            odds_unique.append(o)

    if len(odds_unique) >= 3:
        return odds_unique[0], odds_unique[1], odds_unique[2]
    elif len(odds_unique) == 2:
        return odds_unique[0], None, odds_unique[1]
    elif len(odds_unique) == 1:
        return odds_unique[0], None, None

    return None, None, None


# ── Stubs para v2 ──────────────────────────────────────────────────────────────

def fetch_betcris(home: str, away: str) -> dict:
    """Stub — implementar en v2 con scraping HTML público de betcris.com"""
    logger.info(f"[cleo] Betcris: stub (v2)")
    return _make_market_dict("Betcris", None, None, None, available=False, note="Stub — disponible en v2")


def fetch_codere(home: str, away: str) -> dict:
    """Stub — implementar en v2 con scraping HTML de codere.com.co / codere.cr"""
    logger.info(f"[cleo] Codere: stub (v2)")
    return _make_market_dict("Codere", None, None, None, available=False, note="Stub — disponible en v2")


def fetch_bodog(home: str, away: str) -> dict:
    """Stub — implementar en v2"""
    logger.info(f"[cleo] Bodog: stub (v2)")
    return _make_market_dict("Bodog", None, None, None, available=False, note="Stub — disponible en v2")


def fetch_manifold(home: str, away: str) -> dict:
    """
    Obtiene precios de Manifold Markets (solo referencial — dinero virtual).
    No se usa en cálculos de EV/Kelly.
    """
    cache_key = f"manifold_{home}_{away}"
    cached = _cache_get(cache_key)
    if cached:
        return cached

    query = urllib.parse.quote(f"{home} {away} world cup")
    url = f"https://api.manifold.markets/v0/search-markets?term={query}&limit=5"
    data = _http_get(url)

    result = _make_market_dict(
        "Manifold", None, None, None,
        available=False,
        note="Solo referencial (mana virtual). No incluido en cálculos EV/Kelly."
    )

    if data and isinstance(data, list) and len(data) > 0:
        market = data[0]
        prob = market.get("probability")
        if prob and 0 < prob < 1:
            home_odd = round(1.0 / float(prob), 4)
            result = _make_market_dict(
                "Manifold (ref)", home_odd, None, None,
                available=True,
                note="Dinero virtual (mana). Solo referencial. No usar para EV/Kelly."
            )

    _cache_set(cache_key, result)
    return result


# ══════════════════════════════════════════════════════════════════════════════
# CLASE PRINCIPAL: CleoAgent
# ══════════════════════════════════════════════════════════════════════════════



# -- Calibracion de sesgo del modelo ------------------------------------------
_bias_cache = {"data": None, "ts": 0}
_BIAS_CACHE_TTL = 3600  # refrescar cada hora


def _load_model_bias():
    """Analiza historial de predicciones para detectar sesgo sistematico."""
    global _bias_cache
    import time as _time_mod
    now = _time_mod.time()
    if _bias_cache["data"] and (now - _bias_cache["ts"]) < _BIAS_CACHE_TTL:
        return _bias_cache["data"]

    brier_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data", "brier_scores.json")
    try:
        with open(brier_path) as f:
            import json as _json_bias
            data = _json_bias.load(f)
        scores = data.get("scores", [])
        with_probs = [s for s in scores if s.get("p_draw") is not None]

        if len(with_probs) < 5:
            # Datos insuficientes: usar estimado empirico de 41 partidos WC2026
            bias = {
                "n_calibrated": len(scores),
                "n_with_probs": len(with_probs),
                "draw_correction_strong": 1.6,
                "draw_correction_medium": 1.25,
                "draw_actual_rate": 0.29,
                "draw_predicted_avg": 0.14,
                "source": "empirical_41matches",
            }
        else:
            draws_total = sum(1 for s in with_probs if s.get("actual") == "D")
            draw_rate_actual = draws_total / len(with_probs)
            draw_rate_predicted = sum(s.get("p_draw", 0) for s in with_probs) / len(with_probs)
            global_factor = draw_rate_actual / draw_rate_predicted if draw_rate_predicted > 0 else 1.0
            strong_fav = [s for s in with_probs if s.get("p_home", 0) > 0.65]
            if strong_fav:
                draws_s = sum(1 for s in strong_fav if s.get("actual") == "D")
                rate_s = draws_s / len(strong_fav)
                pred_s = sum(s.get("p_draw", 0) for s in strong_fav) / len(strong_fav)
                factor_strong = rate_s / pred_s if pred_s > 0 else global_factor
            else:
                factor_strong = global_factor
            bias = {
                "n_calibrated": len(scores),
                "n_with_probs": len(with_probs),
                "draw_correction_strong": round(min(factor_strong, 2.5), 3),
                "draw_correction_medium": round(min(global_factor, 2.0), 3),
                "draw_actual_rate": round(draw_rate_actual, 3),
                "draw_predicted_avg": round(draw_rate_predicted, 3),
                "source": "calibration_log",
            }

        _bias_cache = {"data": bias, "ts": now}
        return bias
    except Exception as e:
        logger.warning(f"[cleo] bias load error: {e}")
        return {
            "draw_correction_strong": 1.6,
            "draw_correction_medium": 1.25,
            "source": "fallback",
        }


def _apply_draw_correction(ryder_probs, elo_home, elo_away):
    """
    Corrige el sesgo del modelo: subestima empates cuando hay gran diferencia Elo.
    Retorna (probs_corregidas, nota_str) o (probs_originales, None) si no aplica.
    """
    bias = _load_model_bias()
    p_home = ryder_probs.get("home", 0.33)
    p_draw = ryder_probs.get("draw", 0.33)
    p_away = ryder_probs.get("away", 0.33)

    elo_diff = abs(float(elo_home or 0) - float(elo_away or 0))

    if elo_diff >= 400 and p_draw < 0.20:
        factor = bias.get("draw_correction_strong", 1.6)
        label = "fuerte"
    elif elo_diff >= 200 and p_draw < 0.25:
        factor = bias.get("draw_correction_medium", 1.25)
        label = "medio"
    else:
        return ryder_probs, None

    new_draw = min(p_draw * factor, 0.45)
    reduction = new_draw - p_draw
    total_ha = p_home + p_away
    if total_ha > 0:
        new_home = max(0, p_home - reduction * (p_home / total_ha))
        new_away = max(0, p_away - reduction * (p_away / total_ha))
    else:
        new_home, new_away = p_home, p_away

    total = new_home + new_draw + new_away
    corrected = {
        "home": round(new_home / total, 4),
        "draw": round(new_draw / total, 4),
        "away": round(new_away / total, 4),
    }
    note = (
        f"Correccion sesgo {label}: p_draw {p_draw*100:.1f}%"
        f"->{corrected['draw']*100:.1f}% "
        f"(factor {factor:.2f}, Elo diff {elo_diff:.0f}pts)"
    )
    return corrected, note

class CleoAgent:
    """
    Agente Cleo — Estratega de Mercados de Predicción y Arbitraje.

    Integración con ProGol CR:
        cleo = CleoAgent()
        result = cleo.analyze("España", "Marruecos", ryder_probs)
        print(cleo.format_response(result))

    O con Ryder interno:
        result = cleo.analyze_with_ryder("España", "Marruecos")
    """

    def __init__(self, ryder_model=None):
        """
        Args:
            ryder_model: instancia del modelo Ryder (opcional).
                         Si se proporciona, cleo puede llamar a model.predict() directamente.
        """
        self.ryder_model = ryder_model
        self.version = VERSION
        logger.info(f"[cleo] CleoAgent v{VERSION} inicializado")

    # ── Análisis principal ─────────────────────────────────────────────────────

    def analyze(self, home: str, away: str, ryder_probs: dict) -> dict:
        """
        Análisis completo de mercados para un partido.

        Args:
            home: nombre equipo local (ej: "España")
            away: nombre equipo visitante (ej: "Marruecos")
            ryder_probs: probabilidades de Ryder
                         {"home": 0.543, "draw": 0.265, "away": 0.192}

        Returns:
            dict con análisis completo: markets, opportunities, arbitrage, warnings
        """
        logger.info(f"[cleo] Analizando: {home} vs {away}")

        # Correccion de sesgo: modelo subestima empates con Elo diff alto
        try:
            import model as _m_bias
            _r = _m_bias.predict(home, away, wc_mode=True)
            _elo_h = _r.get("homeElo") or _r.get("engine", {}).get("elo_home", 0)
            _elo_a = _r.get("awayElo") or _r.get("engine", {}).get("elo_away", 0)
            ryder_probs_corrected, bias_note = _apply_draw_correction(ryder_probs, _elo_h, _elo_a)
            if bias_note:
                logger.info(f"[cleo] {bias_note}")
        except Exception as _be:
            ryder_probs_corrected = ryder_probs
            bias_note = None

        result = {
            "match": f"{home} vs {away}",
            "timestamp": _now_utc(),
            "ryder_probs_raw": ryder_probs,
            "ryder_probs": ryder_probs_corrected,
            "ryder_probs_corrected": ryder_probs_corrected != ryder_probs,
            "bias_note": bias_note,
            "markets": {},
            "opportunities": [],
            "arbitrage": None,
            "warnings": [],
            "version": self.version
        }
        ryder_probs = ryder_probs_corrected

        # ── PASO 1: Fetch paralelo de mercados ────────────────────────────────
        # (threading opcional — en v1 hacemos secuencial para mantener stdlib only)

        polymarket = fetch_polymarket(home, away)
        kalshi     = fetch_kalshi(home, away)
        doradobet  = fetch_doradobet(home, away)
        betcris    = fetch_betcris(home, away)
        codere     = fetch_codere(home, away)
        bodog      = fetch_bodog(home, away)

        all_markets_raw = [polymarket, kalshi, doradobet, betcris, codere, bodog]
        active_markets = {
            m["platform"]: m for m in all_markets_raw
            if m and m.get("available", False)
        }

        result["markets"] = {
            m["platform"]: m for m in all_markets_raw if m
        }

        # ── PASO 2: Warnings de plataformas ──────────────────────────────────

        if not polymarket.get("available"):
            result["warnings"].append(
                "Polymarket no disponible — verificar conexión o intentar con VPN."
            )
        if not doradobet.get("available"):
            w = doradobet.get("note", "Doradobet no disponible.")
            result["warnings"].append(w)
        if kalshi.get("available"):
            result["warnings"].append(
                "Kalshi: precios referenciales. Requiere cuenta USA para operar. "
                "No disponible desde CR."
            )

        if not active_markets:
            result["warnings"].append(
                "Sin mercados activos disponibles. Verificar conectividad."
            )
            return result

        # ── PASO 3: Calcular oportunidades EV + Kelly ─────────────────────────

        outcomes = [
            ("home", "home_odd", home),
            ("draw", "draw_odd", "Empate"),
            ("away", "away_odd", away)
        ]

        opportunities = []

        for outcome_key, odd_key, outcome_label in outcomes:
            p_ryder = ryder_probs.get(outcome_key, 0)
            if p_ryder <= 0:
                continue

            for platform, market in active_markets.items():
                # No calcular EV contra mercados de torneo — probabilidades incomparables
                if market.get("is_tournament"):
                    continue
                # No calcular EV contra mercados de torneo — probabilidades incomparables
                if market.get("is_tournament"):
                    continue
                odd = market.get(odd_key)
                if not odd or odd <= 1.0:
                    continue

                # Devig
                all_odds = [market.get("home_odd"), market.get("draw_odd"), market.get("away_odd")]
                outcome_idx = ["home", "draw", "away"].index(outcome_key)

                if None not in all_odds and all(o > 0 for o in all_odds):
                    # Elegir método: Shin si hay underdog pronunciado
                    min_p_bruta = min(1/o for o in all_odds)
                    if min_p_bruta < 0.15:
                        p_devigadas = devig_shin(all_odds)
                    else:
                        p_devigadas = devig_multiplicativo(all_odds)
                    p_impl = p_devigadas[outcome_idx] if p_devigadas else 1.0 / odd
                else:
                    p_impl = 1.0 / odd  # fallback sin devig completo

                ev = calculate_ev(p_ryder, odd)
                kelly_rec = kelly_recommended(p_ryder, odd)

                if ev < MIN_EV_REPORT:
                    continue

                # Clasificación
                if ev >= 10.0:
                    tier = "🟢 FUERTE"
                elif ev >= 5.0:
                    tier = "🟡 MODERADA"
                else:
                    tier = "🟠 DÉBIL"

                # Nota de liquidez
                liq = market.get("liquidity")
                liq_note = ""
                if liq and liq < MIN_LIQUIDITY_WARN:
                    liq_note = f"⚠️ Liquidez baja (${liq:,.0f})"

                opportunities.append({
                    "outcome": outcome_key,
                    "outcome_label": outcome_label,
                    "platform": platform,
                    "decimal_odd": round(odd, 4),
                    "p_implied": round(p_impl, 4),
                    "p_ryder": round(p_ryder, 4),
                    "ev_pct": round(ev, 2),
                    "kelly_recommended": kelly_rec,
                    "kelly_full": round(calculate_kelly(p_ryder, odd), 4),
                    "tier": tier,
                    "liquidity": liq,
                    "liquidity_note": liq_note
                })

        # Ordenar por EV descendente
        opportunities.sort(key=lambda x: x["ev_pct"], reverse=True)
        result["opportunities"] = opportunities

        # ── PASO 4: Detectar arbitraje ────────────────────────────────────────

        match_only_markets = {p: m for p, m in active_markets.items() if not (m or {}).get("is_tournament")}
        result["arbitrage"] = detect_arbitrage(match_only_markets)

        return result

    def analyze_with_ryder(self, home: str, away: str) -> dict:
        """
        Versión integrada: llama a model.predict() de Ryder y luego analiza.
        Requiere que se haya pasado ryder_model al constructor.

        Returns:
            dict de analyze() o error si no hay modelo Ryder disponible
        """
        if not self.ryder_model:
            return {
                "error": "No hay modelo Ryder configurado. "
                         "Pasar ryder_model al constructor o usar analyze() con probabilidades manuales.",
                "match": f"{home} vs {away}"
            }

        try:
            ryder_probs = self.ryder_model.predict(home, away)
            # Normalizar claves si el modelo usa nombres diferentes
            normalized = {
                "home": ryder_probs.get("home", ryder_probs.get("1", 0)),
                "draw": ryder_probs.get("draw", ryder_probs.get("X", 0)),
                "away": ryder_probs.get("away", ryder_probs.get("2", 0))
            }
            logger.info(f"[cleo] Ryder probs: {normalized}")
            return self.analyze(home, away, normalized)
        except Exception as e:
            logger.warning(f"[cleo] Error llamando a Ryder: {e}")
            return {
                "error": f"Error al obtener probabilidades de Ryder: {e}",
                "match": f"{home} vs {away}"
            }

    # ── Formateo de respuesta ──────────────────────────────────────────────────

    def format_response(self, analysis: dict) -> str:
        """
        Convierte el dict de analyze() en string formateado para el chat.

        Returns:
            str con el análisis completo listo para mostrar
        """
        if "error" in analysis:
            return f"⚠️ CLEO ERROR: {analysis['error']}"

        match = analysis.get("match", "Partido desconocido")
        ts    = analysis.get("timestamp", "")
        rp    = analysis.get("ryder_probs", {})
        opps  = analysis.get("opportunities", [])
        arb   = analysis.get("arbitrage", {})
        warns = analysis.get("warnings", [])
        mkts  = analysis.get("markets", {})

        lines = []
        lines.append(f"\n🎯 CLEO — Análisis de Mercados: {match}")
        lines.append("═" * 56)
        lines.append("")

        # Probabilidades Ryder
        lines.append("📊 PROBABILIDADES RYDER (baseline):")
        home_pct  = rp.get("home", 0) * 100
        draw_pct  = rp.get("draw", 0) * 100
        away_pct  = rp.get("away", 0) * 100
        parts = match.split(" vs ")
        h_label = parts[0] if len(parts) == 2 else "Local"
        a_label = parts[1] if len(parts) == 2 else "Visitante"
        lines.append(f"   {h_label} {home_pct:.1f}% | Empate {draw_pct:.1f}% | {a_label} {away_pct:.1f}%")
        lines.append(f"   Fuente: Dixon-Coles + Elo · ProGol CR · {ts}")
        lines.append("")

        # Tabla de mercados
        lines.append("💹 MERCADOS COMPARADOS:")
        header = f"{'Plataforma':<18} {'Local':<10} {'Empate':<10} {'Visitante':<10} {'Margen':<8}"
        lines.append(header)
        lines.append("─" * 56)
        match_mkts = {p: m for p, m in mkts.items() if not m.get("is_tournament")}
        tourney_mkts = {p: m for p, m in mkts.items() if m.get("is_tournament") and m.get("available")}
        for platform, mkt in match_mkts.items():
            if not mkt:
                continue
            h_odd = mkt.get("home_odd")
            d_odd = mkt.get("draw_odd")
            a_odd = mkt.get("away_odd")
            margin_pct = mkt.get("margin", 0) * 100

            h_str = f"{h_odd:.3f}" if h_odd else "—"
            d_str = f"{d_odd:.3f}" if d_odd else "—"
            a_str = f"{a_odd:.3f}" if a_odd else "—"
            m_str = f"{margin_pct:.1f}%"

            avail = "✓" if mkt.get("available") else "✗"
            lines.append(f"{avail} {platform:<16} {h_str:<10} {d_str:<10} {a_str:<10} {m_str:<8}")
        lines.append("")

        # Señal de largo plazo: Polymarket WC winner
        if tourney_mkts:
            lines.append("🔭 POLYMARKET — Señal de torneo (probabilidad de ganar el WC completo):")
            for platform, mkt in tourney_mkts.items():
                h_odd = mkt.get("home_odd")
                a_odd = mkt.get("away_odd")
                liq = mkt.get("liquidity")
                try:
                    liq_str = f"${float(liq):,.0f}" if liq else "N/A"
                except Exception:
                    liq_str = "N/A"
                h_p = f"{round(1/h_odd*100,1)}%" if h_odd else "—"
                a_p = f"{round(1/a_odd*100,1)}%" if a_odd else "—"
                lines.append(f"   {h_label}: {h_p} | {a_label}: {a_p} | Liquidez: {liq_str}")
                lines.append(f"   (no son comparables con odds de partido — señal de fortaleza general)")
            lines.append("")

        # Oportunidades +EV
        if opps:
            lines.append("⚡ OPORTUNIDADES +EV:")
            lines.append("─" * 56)
            for i, opp in enumerate(opps, 1):
                tier = opp["tier"]
                label = opp["outcome_label"]
                plat  = opp["platform"]
                ev    = opp["ev_pct"]
                kr    = opp["kelly_recommended"] * 100
                odd   = opp["decimal_odd"]
                p_imp = opp["p_implied"] * 100
                p_ry  = opp["p_ryder"] * 100
                liq_n = opp.get("liquidity_note", "")

                lines.append(f"{i}. {tier} — {label} · {plat}")
                lines.append(f"   Odd decimal: {odd:.3f} | Implícita (devigada): {p_imp:.1f}%")
                lines.append(f"   Ryder: {p_ry:.1f}% | EV = {ev:+.1f}%")
                lines.append(f"   Kelly recomendado: {kr:.1f}% del bankroll (1/4 Kelly, cap 15%)")
                if liq_n:
                    lines.append(f"   {liq_n}")
                lines.append("")
        else:
            lines.append("⚡ OPORTUNIDADES +EV:")
            lines.append("   Sin oportunidades de valor positivo en este partido.")
            lines.append("   (EV < 2% en todas las plataformas disponibles)")
            lines.append("")

        # Arbitraje
        if arb:
            lines.append("🔄 ARBITRAJE CROSS-PLATFORM:")
            if arb.get("detected"):
                profit = arb.get("profit_pct", 0)
                lines.append(f"   ✅ ARBITRAJE DETECTADO — Ganancia garantizada: ~{profit:.1f}%")
                best = arb.get("best_odds", {})
                for oc, info in best.items():
                    label = {"home": h_label, "draw": "Empate", "away": a_label}.get(oc, oc)
                    odd = info.get("odd")
                    plat = info.get("platform", "—")
                    contrib = round(1.0 / odd, 3) if odd else "—"
                    lines.append(f"   Mejor {label}: {plat} {odd:.3f} → contribución {contrib}")
                sum_arb = arb.get("arb_sum", 0)
                lines.append(f"   Suma arb: {sum_arb:.4f} < 1.0 ✓")
                lines.append(f"   ⚠️  {arb.get('warning', '')}")
            else:
                sum_arb = arb.get("arb_sum")
                if sum_arb:
                    lines.append(f"   Sin arbitraje — suma de mejores odds: {sum_arb:.4f} ≥ 1.0")
                else:
                    lines.append("   Sin suficientes mercados para detectar arbitraje.")
            lines.append("")

        # Recomendación
        lines.append("💡 RECOMENDACIÓN CLEO:")
        if opps:
            top = opps[0]
            lines.append(
                f"   Mejor oportunidad: {top['outcome_label']} en {top['platform']} "
                f"(EV {top['ev_pct']:+.1f}%)."
            )
            kr = top['kelly_recommended'] * 100
            lines.append(f"   Fracción sugerida: {kr:.1f}% del bankroll.")

            # Advertencia sobre casas con vig alto
            for plat, mkt in mkts.items():
                if mkt and mkt.get("available") and mkt.get("margin", 0) > 0.07:
                    m_pct = mkt.get("margin", 0) * 100
                    lines.append(
                        f"   {plat} tiene vig alto ({m_pct:.1f}%). "
                        f"Evaluar solo donde el devig genere EV real."
                    )
        else:
            lines.append(f"   Sin valor claro en este partido con las plataformas disponibles.")
            lines.append(f"   Considerar abstenerse o esperar movimiento de líneas.")
        lines.append("")

        # Avisos
        all_warns = warns.copy()
        all_warns.append(
            "EV positivo ≠ ganancia garantizada. Basado en modelo Ryder "
            "(Dixon-Coles + Elo). Factores no modelados pueden afectar el resultado."
        )
        if all_warns:
            lines.append("⚠️  AVISOS:")
            for w in all_warns:
                lines.append(f"   • {w}")
            lines.append("")

        lines.append("═" * 56)
        lines.append(f"[cleo] v{VERSION} · ProGol CR · {ts}")
        lines.append("EV positivo no garantiza resultado. Juegue con responsabilidad.")
        lines.append("")

        return "\n".join(lines)

    # ── Historial de picks ─────────────────────────────────────────────────────

    def save_pick(self, analysis: dict) -> bool:
        """
        Guarda el pick top de un análisis en picks_history.json.

        Returns:
            True si se guardó correctamente, False si error
        """
        try:
            # Cargar historial existente
            try:
                with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except (FileNotFoundError, json.JSONDecodeError):
                history = {"picks": []}

            opps = analysis.get("opportunities", [])
            top = opps[0] if opps else None

            pick_id = f"cleo_{analysis['timestamp'].replace(':', '').replace('-', '')[:15]}"

            entry = {
                "id": pick_id,
                "match": analysis.get("match"),
                "analysis_ts": analysis.get("timestamp"),
                "ryder_probs": analysis.get("ryder_probs"),
                "top_pick": top,
                "arbitrage_detected": analysis.get("arbitrage", {}).get("detected", False),
                "result": None,
                "actual_winner": None,
                "pick_correct": None,
                "calibration_note": None
            }

            history["picks"].append(entry)

            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

            logger.info(f"[cleo] Pick guardado: {pick_id}")
            return True

        except Exception as e:
            logger.warning(f"[cleo] Error guardando pick: {e}")
            return False

    def update_result(self, pick_id: str, actual_winner: str) -> bool:
        """
        Actualiza el resultado real de un pick (para calibración en v3).

        Args:
            pick_id: ID del pick (ej: "cleo_20260705T143200")
            actual_winner: "home" / "draw" / "away"

        Returns:
            True si se actualizó, False si no encontró el pick
        """
        try:
            with open(HISTORY_PATH, "r", encoding="utf-8") as f:
                history = json.load(f)

            for pick in history.get("picks", []):
                if pick["id"] == pick_id:
                    pick["actual_winner"] = actual_winner
                    pick["result"] = "resolved"
                    top = pick.get("top_pick")
                    if top:
                        pick["pick_correct"] = (top.get("outcome") == actual_winner)
                    break
            else:
                logger.warning(f"[cleo] Pick {pick_id} no encontrado en historial")
                return False

            with open(HISTORY_PATH, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=2, ensure_ascii=False)

            logger.info(f"[cleo] Resultado actualizado: {pick_id} → {actual_winner}")
            return True

        except Exception as e:
            logger.warning(f"[cleo] Error actualizando resultado: {e}")
            return False


# ══════════════════════════════════════════════════════════════════════════════
# PUNTO DE ENTRADA — CLI y prueba rápida
# ══════════════════════════════════════════════════════════════════════════════

def main():
    """
    Punto de entrada CLI para prueba rápida.
    Uso: python cleo.py "España" "Marruecos" 0.543 0.265 0.192
    """
    import sys

    if len(sys.argv) < 6:
        print("Uso: python cleo.py <local> <visitante> <p_home> <p_draw> <p_away>")
        print("Ejemplo: python cleo.py España Marruecos 0.543 0.265 0.192")
        sys.exit(1)

    home  = sys.argv[1]
    away  = sys.argv[2]
    p_h   = float(sys.argv[3])
    p_d   = float(sys.argv[4])
    p_a   = float(sys.argv[5])

    ryder_probs = {"home": p_h, "draw": p_d, "away": p_a}

    cleo = CleoAgent()
    result = cleo.analyze(home, away, ryder_probs)
    print(cleo.format_response(result))

    # Guardar pick automáticamente si hay oportunidades
    if result.get("opportunities"):
        cleo.save_pick(result)
        print(f"\n[cleo] Pick guardado en {HISTORY_PATH}")


if __name__ == "__main__":
    main()
