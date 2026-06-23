#!/usr/bin/env python3
"""
ProGol CR — Integraciones externas gratuitas
- The Odds API     → cuotas reales de casas de apuestas (key requerida)
- Open-Meteo       → clima en la cancha (sin key)
- football-data.org → fixtures y standings adicionales (key requerida)
- Reddit           → sentimiento público antes del partido (sin key)
"""

import json, os, urllib.request, urllib.parse, urllib.error, datetime, time

HERE = os.path.dirname(os.path.abspath(__file__))
_cfg_cache = {}
_cfg_ts    = 0

def _cfg():
    global _cfg_cache, _cfg_ts
    now = time.time()
    if now - _cfg_ts > 60:
        try:
            with open(os.path.join(HERE, "config.json")) as f:
                _cfg_cache = json.load(f)
        except Exception:
            pass
        _cfg_ts = now
    return _cfg_cache

def _get(url, headers=None, timeout=8):
    req = urllib.request.Request(url, headers={"User-Agent": "ProGolCR/1.0", **(headers or {})})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode())

# ── Caché simple en memoria ────────────────────────────────────────────────────
_cache = {}  # key → (timestamp, data)

def _cached(key, fn, ttl=300):
    now = time.time()
    if key in _cache and now - _cache[key][0] < ttl:
        return _cache[key][1]
    try:
        data = fn()
        _cache[key] = (now, data)
        return data
    except Exception as e:
        print(f"[integrations] {key} error: {e}")
        return _cache.get(key, (0, None))[1]  # devuelve caché viejo si hay

# ══════════════════════════════════════════════════════════════════════════════
# 1. THE ODDS API — cuotas reales de casas de apuestas
#    Registro gratuito: https://the-odds-api.com  (500 req/mes gratis)
#    Agregar en config.json: "odds_api_key": "TU_KEY"
# ══════════════════════════════════════════════════════════════════════════════

ODDS_SPORTS = ["soccer_fifa_world_cup", "soccer_uefa_european_championship",
               "soccer_usa_mls", "soccer_conmebol_copa_america"]

def fetch_odds(sport="soccer_fifa_world_cup"):
    """Devuelve lista de partidos con cuotas H2H de múltiples casas."""
    key = _cfg().get("odds_api_key", "")
    if not key:
        return None
    url = (f"https://api.the-odds-api.com/v4/sports/{sport}/odds/"
           f"?apiKey={key}&regions=eu,us&markets=h2h,totals&oddsFormat=decimal")
    return _cached(f"odds_{sport}", lambda: _get(url), ttl=180)

# ─── ESPN/DraftKings odds — sin key, cubre WC 2026 ────────────────────────
_espn_ev_cache  = {}
_espn_dk_cache  = {}

def _ml_to_dec(ml):
    """American moneyline -> decimal odds."""
    if ml is None: return None
    try:
        ml = float(ml)
        return round(ml/100+1, 4) if ml > 0 else round(100/abs(ml)+1, 4)
    except Exception: return None

def _espn_event_index(date_str):
    if date_str in _espn_ev_cache:
        return _espn_ev_cache[date_str]
    compact = date_str.replace("-","")
    url = "https://site.api.espn.com/apis/site/v2/sports/soccer/fifa.world/scoreboard?dates="+compact+"&limit=50"
    try:
        data = _get(url)
        idx = {}
        for ev in data.get("events",[]):
            eid = str(ev.get("id",""))
            comp = (ev.get("competitions") or [{}])[0]
            teams = comp.get("competitors",[])
            names = [t.get("team",{}).get("displayName","").lower() for t in teams]
            if len(names)==2: idx[tuple(sorted(names))] = eid
            shorts = [t.get("team",{}).get("shortDisplayName","").lower() for t in teams]
            if len(shorts)==2: idx[tuple(sorted(shorts))] = eid
        _espn_ev_cache[date_str] = idx
        return idx
    except Exception as e:
        print("[espn-odds] index error: "+str(e))
        _espn_ev_cache[date_str] = {}
        return {}

def _fetch_dk_odds(ev_id):
    now = time.time()
    if ev_id in _espn_dk_cache:
        ts,val = _espn_dk_cache[ev_id]
        if now-ts < 600: return val
    base = "http://sports.core.api.espn.com/v2/sports/soccer/leagues/fifa.world"
    url = base+"/events/"+ev_id+"/competitions/"+ev_id+"/odds/100?lang=en&region=us"
    try:
        data = _get(url)
        ho = data.get("homeTeamOdds") or {}
        ao = data.get("awayTeamOdds") or {}
        dr = data.get("drawOdds") or {}
        h_dec = (ho.get("current") or {}).get("moneyLine",{}).get("decimal") or _ml_to_dec(ho.get("moneyLine"))
        a_dec = (ao.get("current") or {}).get("moneyLine",{}).get("decimal") or _ml_to_dec(ao.get("moneyLine"))
        d_dec = _ml_to_dec(dr.get("moneyLine"))
        result = {
            "best_home": round(h_dec,2) if h_dec else None,
            "best_away": round(a_dec,2) if a_dec else None,
            "best_draw": round(d_dec,2) if d_dec else None,
            "over_under": data.get("overUnder"),
            "over_odds":  data.get("overOdds"),
            "under_odds": data.get("underOdds"),
            "bookmakers": [{"bookmaker":"DraftKings","home":h_dec,"draw":d_dec,"away":a_dec}],
            "source": "espn-dk",
        }
        _espn_dk_cache[ev_id] = (now,result)
        return result
    except Exception as e:
        print("[espn-odds] fetch error ev="+str(ev_id)+": "+str(e))
        _espn_dk_cache[ev_id] = (now,None)
        return None

def get_espn_match_odds(home, away):
    """Busca cuotas de DraftKings via ESPN para un partido del WC 2026 (sin key)."""
    import datetime as _dt
    today = _dt.date.today()
    for delta in range(-1,3):
        d = (today + _dt.timedelta(days=delta)).isoformat()
        idx = _espn_event_index(d)
        hl,al = home.lower(),away.lower()
        ev_id = idx.get(tuple(sorted([hl,al])))
        if not ev_id:
            for (k1,k2),eid in idx.items():
                if (hl[:4] in k1 or k1[:4] in hl) and (al[:4] in k2 or k2[:4] in al):
                    ev_id=eid; break
                if (hl[:4] in k2 or k2[:4] in hl) and (al[:4] in k1 or k1[:4] in al):
                    ev_id=eid; break
        if ev_id:
            return _fetch_dk_odds(ev_id)
    return None


def get_match_odds(home, away):
    """Cuotas: 1) ESPN/DraftKings (sin key, WC 2026), 2) The Odds API (key)."""
    try:
        espn = get_espn_match_odds(home, away)
        if espn and espn.get("best_home"):
            return espn
    except Exception as e:
        print("[espn-odds] "+str(e))
    for sport in ODDS_SPORTS:
        data = fetch_odds(sport)
        if not data: continue
        hl,al = home.lower(),away.lower()
        for ev in data:
            eh = (ev.get("home_team") or "").lower()
            ea = (ev.get("away_team") or "").lower()
            if (hl[:4] in eh or eh[:4] in hl) and (al[:4] in ea or ea[:4] in al):
                books = []
                for bk in (ev.get("bookmakers") or [])[:5]:
                    for mkt in (bk.get("markets") or []):
                        if mkt.get("key")=="h2h":
                            outs = {o["name"]:o["price"] for o in mkt.get("outcomes",[])}
                            books.append({"bookmaker":bk.get("title"),"home":outs.get(ev["home_team"]),"draw":outs.get("Draw"),"away":outs.get(ev["away_team"])})
                return {"home":ev.get("home_team"),"away":ev.get("away_team"),"commence":ev.get("commence_time"),"bookmakers":books,
                        "best_home":max((b["home"] for b in books if b.get("home")),default=None),
                        "best_draw":max((b["draw"] for b in books if b.get("draw")),default=None),
                        "best_away":max((b["away"] for b in books if b.get("away")),default=None)}
    return None
def odds_summary(home, away):
    """Texto listo para inyectar en el contexto de Ryder."""
    d = get_match_odds(home, away)
    if not d:
        return ""
    lines = [f"CUOTAS REALES ({home} vs {away}):"]
    for b in d.get("bookmakers", [])[:3]:
        lines.append(f"  {b['bookmaker']}: 1={b['home']} X={b['draw']} 2={b['away']}")
    if d.get("best_home"):
        lines.append(f"  Mejor cuota: 1={d['best_home']} X={d['best_draw']} 2={d['best_away']}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# 2. OPEN-METEO — clima en la cancha (sin key, 100% gratis)
#    https://open-meteo.com
# ══════════════════════════════════════════════════════════════════════════════

# Coordenadas de estadios del Mundial 2026
WC_VENUES = {
    # USA
    "MetLife Stadium":          (40.8135, -74.0745),
    "AT&T Stadium":             (32.7473, -97.0945),
    "SoFi Stadium":             (33.9535, -118.3392),
    "Levi's Stadium":           (37.4033, -121.9697),
    "Hard Rock Stadium":        (25.9580, -80.2389),
    "Arrowhead Stadium":        (39.0489, -94.4839),
    "Gillette Stadium":         (42.0909, -71.2643),
    "Lincoln Financial Field":  (39.9008, -75.1675),
    "Seattle":                  (47.5952, -122.3316),
    "Dallas":                   (32.7473, -97.0945),
    "Los Angeles":               (33.9535, -118.3392),
    "New York":                 (40.8135, -74.0745),
    "San Francisco":            (37.4033, -121.9697),
    "Miami":                    (25.9580, -80.2389),
    "Kansas City":              (39.0489, -94.4839),
    "Boston":                   (42.0909, -71.2643),
    "Philadelphia":             (39.9008, -75.1675),
    # Canada
    "BC Place":                 (49.2768, -123.1118),
    "BMO Field":                (43.6332, -79.4181),
    "Vancouver":                (49.2768, -123.1118),
    "Toronto":                  (43.6332, -79.4181),
    # Mexico
    "Estadio Azteca":           (19.3029, -99.1505),
    "Estadio AKRON":            (20.6868, -103.4572),
    "Estadio Monterrey":        (25.6694, -100.2437),
    "Mexico City":              (19.3029, -99.1505),
    "Guadalajara":              (20.6868, -103.4572),
    "Monterrey":                (25.6694, -100.2437),
}

def _venue_coords(venue_str):
    if not venue_str:
        return None
    v = venue_str.strip()
    if v in WC_VENUES:
        return WC_VENUES[v]
    for name, coords in WC_VENUES.items():
        if name.lower() in v.lower() or v.lower() in name.lower():
            return coords
    return None

def fetch_weather(lat, lon, dt_utc=None):
    """
    Devuelve condiciones climáticas para lat/lon en dt_utc (datetime UTC).
    Si dt_utc es None usa la hora actual.
    """
    if dt_utc is None:
        dt_utc = datetime.datetime.utcnow()
    date_str = dt_utc.strftime("%Y-%m-%d")
    hour     = dt_utc.hour
    url = (f"https://api.open-meteo.com/v1/forecast"
           f"?latitude={lat}&longitude={lon}"
           f"&hourly=temperature_2m,precipitation_probability,windspeed_10m,weathercode"
           f"&timezone=UTC&start_date={date_str}&end_date={date_str}")
    key = f"weather_{lat:.2f}_{lon:.2f}_{date_str}"
    data = _cached(key, lambda: _get(url), ttl=1800)
    if not data:
        return None
    try:
        h = data["hourly"]
        i = min(hour, len(h["temperature_2m"]) - 1)
        code = h["weathercode"][i]
        desc = _wmo_desc(code)
        return {
            "temp_c":       round(h["temperature_2m"][i], 1),
            "precip_pct":   h["precipitation_probability"][i],
            "wind_kmh":     round(h["windspeed_10m"][i], 1),
            "condition":    desc,
            "code":         code,
        }
    except Exception:
        return None

def weather_for_match(venue, kickoff_utc=None):
    """Atajo: coordenadas desde nombre del estadio."""
    coords = _venue_coords(venue)
    if not coords:
        return None
    dt = None
    if kickoff_utc:
        try:
            iso = kickoff_utc.replace("Z", "").replace("T", " ")[:16]
            dt  = datetime.datetime.strptime(iso, "%Y-%m-%d %H:%M")
        except Exception:
            pass
    return fetch_weather(coords[0], coords[1], dt)

def weather_summary(venue, kickoff_utc=None):
    """Texto listo para inyectar en el contexto de Ryder."""
    w = weather_for_match(venue, kickoff_utc)
    if not w:
        return ""
    rain = f" — lluvia {w['precip_pct']}%" if w['precip_pct'] > 30 else ""
    wind = f" — viento fuerte {w['wind_kmh']} km/h" if w['wind_kmh'] > 30 else ""
    return f"CLIMA EN CANCHA: {w['temp_c']}°C, {w['condition']}{rain}{wind}"

def _wmo_desc(code):
    codes = {
        0: "despejado", 1: "mayormente despejado", 2: "parcialmente nublado",
        3: "nublado", 45: "niebla", 48: "niebla con hielo",
        51: "llovizna leve", 53: "llovizna moderada", 55: "llovizna intensa",
        61: "lluvia leve", 63: "lluvia moderada", 65: "lluvia intensa",
        71: "nieve leve", 73: "nieve moderada", 75: "nieve intensa",
        80: "chubascos leves", 81: "chubascos moderados", 82: "chubascos intensos",
        95: "tormenta", 96: "tormenta con granizo", 99: "tormenta severa",
    }
    return codes.get(code, f"código {code}")


# ══════════════════════════════════════════════════════════════════════════════
# 3. FOOTBALL-DATA.ORG — fixtures y standings adicionales
#    Registro gratuito: https://www.football-data.org/client/register
#    10 ligas gratis. Agregar en config.json: "football_data_key": "TU_KEY"
# ══════════════════════════════════════════════════════════════════════════════

FD_BASE = "https://api.football-data.org/v4"
FD_COMPS = {
    "worldcup":      "WC",
    "champions":     "CL",
    "premier":       "PL",
    "laliga":        "PD",
    "bundesliga":    "BL1",
    "serie_a":       "SA",
    "ligue1":        "FL1",
}

def _fd_get(path):
    key = _cfg().get("football_data_key", "")
    if not key:
        return None
    return _get(f"{FD_BASE}{path}", headers={"X-Auth-Token": key})

def fetch_fd_matches(date_str, competition="WC"):
    """Partidos de football-data.org para una fecha."""
    def _call():
        return _fd_get(f"/competitions/{competition}/matches?dateFrom={date_str}&dateTo={date_str}")
    return _cached(f"fd_{competition}_{date_str}", _call, ttl=600)

def fetch_fd_standings(competition="WC"):
    """Tabla de posiciones de una competición."""
    return _cached(f"fd_standings_{competition}",
                   lambda: _fd_get(f"/competitions/{competition}/standings"),
                   ttl=1800)

def fd_standings_summary(competition="WC"):
    """Texto con tabla de posiciones para Ryder."""
    data = fetch_fd_standings(competition)
    if not data:
        return ""
    lines = [f"TABLA ({competition}) — football-data.org:"]
    for group in (data.get("standings") or [])[:4]:
        gname = group.get("group") or group.get("stage", "")
        for t in (group.get("table") or [])[:4]:
            team = t.get("team", {}).get("name", "")
            pts  = t.get("points", 0)
            gd   = t.get("goalDifference", 0)
            lines.append(f"  {gname} P{t.get('position','-')} {team}: {pts}pts GD{gd:+d}")
    return "\n".join(lines[:20])


# ══════════════════════════════════════════════════════════════════════════════
# 4. REDDIT — sentimiento público antes del partido (sin key)
#    Usa la API pública JSON de Reddit — no requiere registro.
# ══════════════════════════════════════════════════════════════════════════════

REDDIT_SUBS = ["soccer", "worldcup", "football"]

def fetch_reddit_sentiment(home, away, limit=8):
    """
    Busca los posts más relevantes sobre el partido en Reddit.
    Devuelve lista de {title, score, url, sub}.
    """
    query = urllib.parse.quote(f"{home} {away}")
    results = []
    for sub in REDDIT_SUBS:
        url = (f"https://www.reddit.com/r/{sub}/search.json"
               f"?q={query}&sort=hot&limit={limit}&restrict_sr=1&t=week")
        def _call(u=url, s=sub):
            data = _get(u)
            posts = []
            for ch in (data.get("data", {}).get("children") or []):
                p = ch.get("data", {})
                if p.get("score", 0) < 10:
                    continue
                posts.append({
                    "title": p.get("title", ""),
                    "score": p.get("score", 0),
                    "comments": p.get("num_comments", 0),
                    "sub":   s,
                    "url":   f"https://reddit.com{p.get('permalink','')}",
                })
            return sorted(posts, key=lambda x: x["score"], reverse=True)[:3]
        data = _cached(f"reddit_{sub}_{home}_{away}", _call, ttl=600)
        if data:
            results.extend(data)
    return sorted(results, key=lambda x: x["score"], reverse=True)[:5]

def reddit_summary(home, away):
    """Texto listo para inyectar en el contexto de Ryder."""
    posts = fetch_reddit_sentiment(home, away)
    if not posts:
        return ""
    lines = [f"SENTIMIENTO REDDIT ({home} vs {away}):"]
    for p in posts[:4]:
        lines.append(f"  [{p['score']} pts] {p['title'][:80]}")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
# Función unificada — contexto enriquecido para Ryder
# ══════════════════════════════════════════════════════════════════════════════

def enrich_match_context(home, away, venue=None, kickoff_utc=None):
    """
    Devuelve string con toda la info externa disponible para un partido.
    Usar para inyectar en el system prompt de Ryder.
    """
    parts = []

    weather = weather_summary(venue, kickoff_utc) if venue else ""
    if weather:
        parts.append(weather)

    odds = odds_summary(home, away)
    if odds:
        parts.append(odds)

    reddit = reddit_summary(home, away)
    if reddit:
        parts.append(reddit)

    return "\n\n".join(parts)


def enrich_match_dict(m):
    """
    Agrega campos weather/odds/reddit al dict de un partido (para /api/matches).
    Solo agrega lo que esté disponible sin bloquear.
    """
    venue      = m.get("venue") or m.get("stadium") or ""
    kickoff    = m.get("kickoffUtc") or ""
    home, away = m.get("home", ""), m.get("away", "")

    # Clima
    if venue:
        w = weather_for_match(venue, kickoff)
        if w:
            m["weather"] = w

    # Cuotas
    odds = get_match_odds(home, away)
    if odds:
        m["odds"] = {
            "best_home": odds.get("best_home"),
            "best_draw": odds.get("best_draw"),
            "best_away": odds.get("best_away"),
            "bookmakers_count": len(odds.get("bookmakers", [])),
        }

    return m
