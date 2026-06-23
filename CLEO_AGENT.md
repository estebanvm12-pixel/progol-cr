# CLEO_AGENT.md
# Especificación Completa del Agente Cleo — ProGol CR / Mundial 2026
# Sistema: ProGol CR · Módulo: Mercados & Arbitraje
# Versión: 1.0.0 · Fecha: 2026-06-22

---

## ÍNDICE

1. [Identidad y Personalidad](#1-identidad-y-personalidad)
2. [Fuentes de Datos](#2-fuentes-de-datos)
3. [Motor de Arbitraje y +EV](#3-motor-de-arbitraje-y-ev)
4. [Función Principal: cleo_analyze()](#4-función-principal-cleo_analyze)
5. [Estructura de Respuesta](#5-estructura-de-respuesta)
6. [Integración con ProGol CR](#6-integración-con-progol-cr)
7. [Módulo cleo.py — Arquitectura](#7-módulo-cleopy--arquitectura)
8. [Consideraciones de Riesgo y Compliance](#8-consideraciones-de-riesgo-y-compliance)
9. [Roadmap](#9-roadmap)

---

## 1. IDENTIDAD Y PERSONALIDAD

### Nombre
**Cleo** — Estratega de Mercados de Predicción y Arbitraje Deportivo

### Rol en el Ecosistema ProGol CR

```
RYDER                          CLEO
──────────────────             ──────────────────────────────
Ve el partido                  Ve el mercado
Modela el fútbol               Modela la ineficiencia
Produce p(home/draw/away)      Compara p_ryder vs p_implícita
Dixon-Coles + Elo              EV, Kelly, Arbitraje
Output: probabilidades         Output: oportunidades de valor
```

Ryder es la fuente de verdad estadística. Cleo es la capa de explotación de mercado.
Cleo **no modela fútbol** — usa las probabilidades de Ryder como baseline y detecta
dónde el mercado está equivocado respecto a ese baseline.

### Personalidad y Tono

- **Analítica y directa.** No rodea. Dice el EV, la fracción Kelly y el riesgo.
- **Habla el idioma del mercado:** spread, liquidez, vig, implied probability, devig, arbitrage.
- **Escéptica por diseño:** nunca dice "esto va a ganar". Siempre dice "esto tiene valor esperado positivo basado en el modelo Ryder, que tiene sus propios supuestos".
- **Orientada a proceso:** un pick malo con buen EV sigue siendo correcto. Un resultado bueno con EV negativo sigue siendo un error.
- **Sin garantías. Jamás.** EV positivo ≠ ganancia garantizada. Esto siempre está presente.

### Diferencia fundamental con Ryder

| Dimensión         | Ryder                          | Cleo                                   |
|-------------------|--------------------------------|----------------------------------------|
| Pregunta          | ¿Quién gana?                   | ¿Dónde hay valor?                      |
| Input             | Datos históricos, xG, Elo      | Precios de mercado, odds en tiempo real|
| Output            | p(1), p(X), p(2)               | EV%, Kelly%, oportunidades de arb      |
| Actualización     | Pre-partido / en vivo          | Tiempo real (scraping/API cada 5 min)  |
| Responsabilidad   | Precisión estadística          | Identificación de ineficiencias        |

---

## 2. FUENTES DE DATOS

### 2.1 Polymarket

**Tipo:** Mercado de predicción cripto (USDC sobre Polygon)
**URL Base:** `https://gamma-api.polymarket.com`
**Regulación:** No regulado USA. Accesible desde LATAM (verificar VPN si geobloqueado).

#### Endpoint principal

```
GET https://gamma-api.polymarket.com/markets?active=true&tag=soccer
```

#### Endpoint de evento específico (por slug)

```
GET https://gamma-api.polymarket.com/markets?slug=fifa-world-cup-2026-spain-vs-morocco
```

#### Estructura de respuesta

```json
{
  "id": "0x...",
  "question": "Will Spain win vs Morocco?",
  "outcomePrices": ["0.48", "0.52"],
  "outcomes": ["Yes", "No"],
  "volume": 125000,
  "liquidity": 45000,
  "endDate": "2026-07-05T20:00:00Z"
}
```

#### Formato de probabilidad implícita
- **Formato nativo:** decimal 0–1 (ya es probabilidad implícita directa)
- **Sin vig:** Polymarket es un AMM (Automated Market Maker), el spread está implícito en la liquidez, no en un margen de libro
- **Margen efectivo:** típicamente 0–2% según liquidez del mercado

#### Latencia
- ~200–800ms por request HTTP
- Cache recomendado: 300s (mismo TTL del resto del sistema)

#### Limitaciones
- Mercados binarios principalmente (Sí/No por outcome). Para 1X2 se necesitan 3 mercados separados
- Puede no existir mercado para todos los partidos (liquidez baja en fases grupales)
- Requiere wallet Polygon para operar. Solo lectura sin wallet
- **Geobloqueo:** Polymarket bloqueó IPs de USA. Desde CR debería funcionar, pero puede variar. Cleo advierte si el request falla

#### Búsqueda de mercados

```
GET https://gamma-api.polymarket.com/markets?active=true&limit=100
```
Filtrar por `question` buscando nombres de equipos (búsqueda fuzzy sobre `question`).

---

### 2.2 Kalshi

**Tipo:** Mercado de predicción regulado (CFTC, USA)
**URL Base:** `https://trading-api.kalshi.com/trade-api/v2`
**Regulación:** Regulado CFTC. **Solo opera para residentes USA con cuenta verificada.**

#### Endpoint de mercados de fútbol

```
GET https://trading-api.kalshi.com/trade-api/v2/markets?series_ticker=FIFA
```

#### Endpoint de mercado específico

```
GET https://trading-api.kalshi.com/trade-api/v2/markets/{market_ticker}
```

#### Estructura de respuesta (simplificada)

```json
{
  "ticker": "FIFA-W26-ESP",
  "title": "Spain to win FIFA World Cup 2026?",
  "yes_bid": 0.51,
  "yes_ask": 0.53,
  "no_bid": 0.47,
  "no_ask": 0.49,
  "volume": 8200,
  "open_interest": 12000
}
```

#### Formato de probabilidad implícita
- **Formato nativo:** decimal 0–1 (mid price = (bid + ask) / 2)
- **Spread:** bid/ask spread actúa como vig implícito (típicamente 2–4%)

#### Latencia
- ~300–1000ms
- Requiere header `Authorization: Bearer {kalshi_token}` para ciertos endpoints

#### Limitaciones
- **Solo USA.** Sin cuenta verificada, algunos endpoints son read-only públicos
- Cleo puede **mostrar precios** de Kalshi pero **no puede operar** desde CR
- Mercados de Kalshi tienden a ser más líquidos que Polymarket en eventos grandes
- No siempre tiene mercado 1X2 (más orientado a ganador/avance de torneo)

#### Modo de uso en Cleo
Cleo usa Kalshi solo para **referencia de precio** (benchmark de mercado USA).
Nunca redirige al usuario a operar en Kalshi desde CR.

---

### 2.3 Doradobet

**Tipo:** Casa de apuestas deportiva latinoamericana
**URL Base:** `https://www.doradobet.com`
**Regulación:** Licenciada en jurisdicciones LATAM. **El usuario tiene cuenta activa.**

#### Método de obtención de precios
Doradobet no tiene API pública documentada. Cleo usa **scraping de la página de mercados en vivo** usando la sesión guardada en `config.json`.

#### Configuración de sesión (config.json)

```json
{
  "doradobet": {
    "session_cookie": "SESSION_TOKEN_AQUI",
    "user_agent": "Mozilla/5.0 ...",
    "base_url": "https://www.doradobet.com",
    "sports_path": "/sports/soccer/",
    "last_refresh": "2026-06-22T00:00:00Z"
  }
}
```

#### Endpoint interno (scraping)

```
GET https://www.doradobet.com/sports/soccer/world-cup/
Cookie: {session_cookie}
```

#### Estructura de datos scrapeada (HTML → dict)

```python
{
  "home_team": "España",
  "away_team": "Marruecos",
  "home_win_decimal": 1.70,
  "draw_decimal": 3.90,
  "away_win_decimal": 5.50,
  "market": "1X2",
  "timestamp": "2026-06-22T14:30:00Z"
}
```

#### Formato de probabilidad implícita
- **Formato nativo:** odds decimales europeas (ej: 1.70 = cuota decimal)
- **Conversión:** `p_impl_bruta = 1 / decimal_odd`
- **Con vig típico:** 6–10% en partidos regulares, hasta 12% en mercados exóticos
- **Devig:** método multiplicativo o Shin (ver Sección 3)

#### Latencia
- ~1–3 segundos (scraping HTML)
- Puede fallar si la sesión expira → Cleo notifica al usuario

#### Limitaciones
- Sesión expira periódicamente (requiere re-login manual por el usuario)
- Layout puede cambiar sin aviso (scraping frágil)
- No tiene API pública, solo scraping
- Mercados en vivo tienen actualización más lenta

---

### 2.4 Betcris, Codere, Bodog (secundarias)

**Método:** Scraping HTML sin sesión (odds públicas visibles sin cuenta en muchos casos)

| Casa       | URL Base                   | Formato Odds | Vig Típico | Nota                          |
|------------|----------------------------|--------------|------------|-------------------------------|
| Betcris    | betcris.com                | Decimal/Americana | 6–8%  | Scraping público posible      |
| Codere     | codere.com.co / .cr        | Decimal      | 7–9%       | Versión CR disponible         |
| Bodog      | bodog.eu / bodog.ag        | Americana    | 5–7%       | Tiene API interna no pública  |

**Implementación en v1:** Cleo incluye stubs para estas casas. Implementación real en v2.

---

### 2.5 Manifold Markets

**Tipo:** Mercado de predicción con moneda virtual (mana/créditos)
**URL Base:** `https://api.manifold.markets/v0`
**Regulación:** Sin dinero real. Solo uso referencial.

```
GET https://api.manifold.markets/v0/search-markets?term=spain+morocco+world+cup
```

**Uso en Cleo:** Solo referencial para confirmar sentimiento de mercado. No se incluye en cálculos de EV/Kelly por ser dinero virtual.

---

## 3. MOTOR DE ARBITRAJE Y +EV

### 3.1 Probabilidad Implícita Bruta

Para odds decimales (Doradobet, Betcris, Codere):

```
p_impl_bruta = 1 / decimal_odd
```

Ejemplo: Doradobet España a 1.70
```
p_impl_bruta(España) = 1 / 1.70 = 0.5882 (58.82%)
```

La suma de p_impl_bruta para los 3 outcomes > 1.0 → el exceso es el **margen (vig)**.

```
overround = p_impl_bruta(1) + p_impl_bruta(X) + p_impl_bruta(2) - 1.0
margen% = overround / (1 + overround) * 100
```

### 3.2 Devig — Probabilidad Implícita Real

#### Método Multiplicativo (default en Cleo)

```python
def devig_multiplicativo(odds_list):
    """
    odds_list: lista de odds decimales [home_odd, draw_odd, away_odd]
    Retorna probabilidades verdaderas sin vig.
    """
    p_brutas = [1/o for o in odds_list]
    total = sum(p_brutas)
    return [p / total for p in p_brutas]
```

Ejemplo:
```
Doradobet: 1.70 / 3.90 / 5.50
p_brutas: 0.5882 / 0.2564 / 0.1818 → suma = 1.0264 (vig = 2.64%)
p_devigadas: 0.5733 / 0.2499 / 0.1772 (suman 1.0 exacto)
```

#### Método Shin (alternativo, más preciso)

El modelo Shin distribuye el margen proporcionalmente a la incertidumbre:

```python
def devig_shin(odds_list):
    """
    Implementación del método Shin para devig.
    Más robusto para mercados asimétricos (un outcome muy favorito).
    """
    p_brutas = [1/o for o in odds_list]
    n = len(p_brutas)
    total = sum(p_brutas)
    
    # Encontrar z (parámetro Shin) iterativamente
    # z ≈ (total - 1) / (total - n * min(p_brutas))  [aproximación]
    z_approx = (total - 1) / (total - n * min(p_brutas))
    
    p_shin = []
    for p in p_brutas:
        p_true = (((z_approx**2 + 4*(1-z_approx)*p/total)**0.5) - z_approx) / (2*(1-z_approx))
        p_shin.append(p_true)
    
    return p_shin
```

**Cuándo usar Shin:** Cuando hay un outcome con p_bruta < 0.15 (underdog pronunciado). En el resto de casos, multiplicativo es suficiente.

### 3.3 Expected Value (EV)

```
EV = (p_ryder * ganancia_neta) - ((1 - p_ryder) * apuesta)
```

Para una apuesta de 1 unidad en odds decimales `d`:
```
ganancia_neta = d - 1
EV = p_ryder * (d - 1) - (1 - p_ryder) * 1
EV = p_ryder * d - 1
```

Expresado como porcentaje:
```
EV% = (p_ryder * d - 1) * 100
```

**Interpretación:**
- `EV% > 0`: valor positivo (+EV). El modelo Ryder cree que el mercado subestima este outcome.
- `EV% > 5%`: oportunidad relevante. Incluir en recomendaciones.
- `EV% > 10%`: oportunidad fuerte. Prioridad alta.
- `EV% < 0`: sin valor. No apostar.

**Ejemplo:**
```
Ryder: España 54.3% (p_ryder = 0.543)
Polymarket: España 0.48 → implied odd = 1/0.48 = 2.083 decimal

EV% = (0.543 * 2.083 - 1) * 100
EV% = (1.131 - 1) * 100
EV% = +13.1%  ✅ Fuerte oportunidad
```

### 3.4 Kelly Criterion

La fracción óptima del bankroll a apostar:

```
f* = (p * b - (1-p)) / b
```

Donde:
- `p` = probabilidad Ryder del outcome
- `b` = ganancia neta por unidad (= decimal_odd - 1)
- `f*` = fracción del bankroll (entre 0 y 1)

```python
def kelly(p_ryder, decimal_odd):
    b = decimal_odd - 1
    f = (p_ryder * b - (1 - p_ryder)) / b
    return max(0.0, f)  # Kelly nunca negativo
```

**Kelly fraccional (Cleo usa 1/4 Kelly por default):**

Kelly completo es teóricamente óptimo pero con varianza extrema en la práctica.
Cleo recomienda **Kelly/4** como fracción prudente para uso real.

```
f_recomendado = kelly(p_ryder, decimal_odd) / 4
```

**Cap de seguridad:** Cleo **nunca recomienda más del 15% del bankroll** en un solo pick, independientemente del Kelly calculado.

```python
f_final = min(f_recomendado, 0.15)
```

### 3.5 Arbitraje Cross-Platform

El arbitraje existe cuando la suma de las mejores odds disponibles en distintas plataformas, para todos los outcomes de un evento, produce ganancia garantizada.

**Condición de arbitraje:**

```
suma_arb = (1/mejor_odd_home) + (1/mejor_odd_draw) + (1/mejor_odd_away)
Si suma_arb < 1.0 → arbitraje existe
```

**Ganancia garantizada por unidad de bankroll:**

```
ganancia_arb% = (1 - suma_arb) / suma_arb * 100
```

**Stakes óptimos para arbitraje:**

Para garantizar el mismo retorno en todos los outcomes con bankroll total `B`:

```
stake_i = B / (odd_i * suma_arb)
```

**Ejemplo:**
```
España mejor odd: Polymarket 0.48 → implied odd = 2.083 → contribución = 0.480
Empate mejor odd: Polymarket 0.27 → implied odd = 3.703 → contribución = 0.270
Marruecos mejor odd: Doradobet 5.50 → contribución = 0.182

suma_arb = 0.480 + 0.270 + 0.182 = 0.932
¿suma_arb < 1.0? → SÍ → Arbitraje de 6.8% garantizado ✅
```

> **Nota:** El arbitraje real requiere ejecución simultánea en múltiples plataformas. El riesgo operativo (slippage, latencia, límites de apuesta) puede erosionar la ganancia teórica. Cleo alerta sobre esto.

### 3.6 Comparación de Mercados — Tabla de Valor

Para cada partido, Cleo construye esta matriz:

```
Por cada outcome O en {home, draw, away}:
  Por cada plataforma P en {polymarket, kalshi, doradobet, ...}:
    odd[O][P] = mejor odd disponible para O en P
    p_impl[O][P] = devig(odd[O][P], método=multiplicativo)
    ev[O][P] = p_ryder[O] * odd[O][P] - 1
    kelly[O][P] = kelly_fraction(p_ryder[O], odd[O][P]) / 4
```

---

## 4. FUNCIÓN PRINCIPAL: `cleo_analyze()`

### Pseudocódigo completo

```python
def cleo_analyze(home, away, ryder_probs):
    """
    home: str — nombre del equipo local (ej: "España")
    away: str — nombre del equipo visitante (ej: "Marruecos")
    ryder_probs: dict — {"home": 0.543, "draw": 0.265, "away": 0.192}
    
    Retorna: dict con análisis completo de mercados y oportunidades
    """
    
    result = {
        "match": f"{home} vs {away}",
        "timestamp": now_utc(),
        "ryder_probs": ryder_probs,
        "markets": {},
        "opportunities": [],
        "arbitrage": None,
        "warnings": []
    }
    
    # ── PASO 1: Fetch de precios ──────────────────────────────────────────
    
    polymarket_data = fetch_polymarket(home, away)      # retorna dict o None
    kalshi_data     = fetch_kalshi(home, away)          # retorna dict o None
    doradobet_data  = fetch_doradobet(home, away)       # retorna dict o None
    
    # Casas secundarias (stubs en v1)
    betcris_data    = fetch_betcris(home, away)         # stub: retorna None en v1
    codere_data     = fetch_codere(home, away)          # stub: retorna None en v1
    bodog_data      = fetch_bodog(home, away)           # stub: retorna None en v1
    
    # ── PASO 2: Normalizar formatos ───────────────────────────────────────
    
    # Cada plataforma retorna un dict normalizado:
    # {
    #   "platform": str,
    #   "home_odd": float | None,   # en decimal europeo
    #   "draw_odd": float | None,
    #   "away_odd": float | None,
    #   "margin": float,            # vig estimado (0.0 a 0.15)
    #   "liquidity": float | None,  # en USD (None si no disponible)
    #   "available": bool           # False si fetch falló
    # }
    
    all_markets = [polymarket_data, kalshi_data, doradobet_data,
                   betcris_data, codere_data, bodog_data]
    active_markets = [m for m in all_markets if m and m["available"]]
    
    result["markets"] = {m["platform"]: m for m in active_markets}
    
    if len(active_markets) == 0:
        result["warnings"].append("No se pudieron obtener precios de ninguna plataforma.")
        return result
    
    # ── PASO 3: Calcular EV y Kelly por outcome y plataforma ──────────────
    
    outcomes = ["home", "draw", "away"]
    odd_keys = {"home": "home_odd", "draw": "draw_odd", "away": "away_odd"}
    
    opportunities = []
    
    for outcome in outcomes:
        p_ryder = ryder_probs.get(outcome, 0)
        
        for market in active_markets:
            odd = market.get(odd_keys[outcome])
            
            if odd is None or odd <= 1.0:
                continue
            
            # Probabilidad implícita devigada
            all_odds = [market.get("home_odd"), market.get("draw_odd"), market.get("away_odd")]
            if None in all_odds:
                p_impl = 1 / odd  # fallback: sin devig completo
            else:
                p_impl_devigadas = devig_multiplicativo(all_odds)
                p_impl = p_impl_devigadas[outcomes.index(outcome)]
            
            # EV
            ev = p_ryder * odd - 1
            ev_pct = ev * 100
            
            # Kelly fraccionario (1/4 Kelly)
            kelly_full = kelly(p_ryder, odd)
            kelly_rec = min(kelly_full / 4, 0.15)
            
            # Clasificación de oportunidad
            if ev_pct >= 10:
                tier = "🟢 FUERTE"
            elif ev_pct >= 5:
                tier = "🟡 MODERADA"
            elif ev_pct >= 2:
                tier = "🟠 DÉBIL"
            else:
                tier = None  # No reportar
            
            if tier:
                opportunities.append({
                    "outcome": outcome,
                    "outcome_label": {"home": home, "draw": "Empate", "away": away}[outcome],
                    "platform": market["platform"],
                    "decimal_odd": odd,
                    "p_implied": round(p_impl, 4),
                    "p_ryder": p_ryder,
                    "ev_pct": round(ev_pct, 2),
                    "kelly_recommended": round(kelly_rec, 4),
                    "tier": tier,
                    "liquidity": market.get("liquidity")
                })
    
    # Ordenar por EV descendente
    opportunities.sort(key=lambda x: x["ev_pct"], reverse=True)
    result["opportunities"] = opportunities
    
    # ── PASO 4: Detectar arbitraje cross-platform ─────────────────────────
    
    best_odds = {}
    for outcome, odd_key in odd_keys.items():
        best = None
        best_platform = None
        for market in active_markets:
            odd = market.get(odd_key)
            if odd and (best is None or odd > best):
                best = odd
                best_platform = market["platform"]
        best_odds[outcome] = {"odd": best, "platform": best_platform}
    
    if all(v["odd"] is not None for v in best_odds.values()):
        arb_sum = sum(1 / v["odd"] for v in best_odds.values())
        arb_profit_pct = (1 - arb_sum) / arb_sum * 100 if arb_sum < 1 else 0
        
        result["arbitrage"] = {
            "detected": arb_sum < 1.0,
            "arb_sum": round(arb_sum, 4),
            "profit_pct": round(arb_profit_pct, 2),
            "best_odds": best_odds,
            "warning": "Ejecutar simultáneamente. Slippage y límites pueden erosionar la ganancia."
                        if arb_sum < 1.0 else None
        }
    
    # ── PASO 5: Warnings de plataformas ──────────────────────────────────
    
    if polymarket_data and not polymarket_data["available"]:
        result["warnings"].append("Polymarket no disponible. Verificar conexión o geobloqueo (intentar VPN).")
    if kalshi_data and not kalshi_data["available"]:
        result["warnings"].append("Kalshi requiere cuenta USA para operar. Precios mostrados son referenciales.")
    if doradobet_data and not doradobet_data["available"]:
        result["warnings"].append("Doradobet: sesión expirada o error de scraping. Renovar sesión en config.json.")
    
    return result
```

---

## 5. ESTRUCTURA DE RESPUESTA DE CLEO

### Trigger de activación

```
@Cleo España vs Marruecos
```

o automáticamente tras un análisis de Ryder.

### Formato de respuesta

```
🎯 CLEO — Análisis de Mercados: España vs Marruecos
══════════════════════════════════════════════════════

📊 PROBABILIDADES RYDER (baseline):
   España 54.3% | Empate 26.5% | Marruecos 19.2%
   Fuente: Dixon-Coles + Elo · ProGol CR · 2026-07-05 14:30 UTC

💹 MERCADOS COMPARADOS:
┌──────────────────┬──────────┬──────────┬───────────┬─────────┬───────────┐
│ Plataforma       │ España   │ Empate   │ Marruecos │ Margen  │ Liquidez  │
├──────────────────┼──────────┼──────────┼───────────┼─────────┼───────────┤
│ Polymarket       │ 0.48*    │ 0.27*    │ 0.25*     │ ~0%     │ $45,000   │
│ Kalshi (ref)     │ 0.51*    │ —        │ —         │ ~2%     │ ref only  │
│ Doradobet        │ 1.70dec  │ 3.90dec  │ 5.50dec   │ 8.1%    │ —         │
└──────────────────┴──────────┴──────────┴───────────┴─────────┴───────────┘
* Polymarket/Kalshi: formato probabilidad directa (0–1)
  Odds decimales Doradobet → implícita: España 57.3% | Empate 25.0% | Mar 17.7% (devigado)

⚡ OPORTUNIDADES +EV:
─────────────────────────────────────────────────────────
1. 🟢 FUERTE — España · Polymarket
   Precio: 0.48 (equiv. 2.08 dec) | Implícita: 48.0%
   Ryder: 54.3% | EV = +13.1%
   Kelly recomendado: 9.2% del bankroll (1/4 Kelly, cap 15%)

2. 🟡 MODERADA — Empate · Polymarket
   Precio: 0.27 (equiv. 3.70 dec) | Implícita: 27.0%
   Ryder: 26.5% | EV = -1.9%
   ❌ Sin valor (EV negativo)

3. 🟠 DÉBIL — Marruecos · Doradobet
   Precio: 5.50 dec | Implícita (devigado): 17.7%
   Ryder: 19.2% | EV = +5.6%
   Kelly recomendado: 2.1% del bankroll

─────────────────────────────────────────────────────────

🔄 ARBITRAJE CROSS-PLATFORM:
   Mejor España: Polymarket 0.48 → contribución 0.480
   Mejor Empate: Polymarket 0.27 → contribución 0.270
   Mejor Marruecos: Doradobet 5.50 → contribución 0.182
   
   Suma arb: 0.932 < 1.0 → ✅ ARBITRAJE DETECTADO
   Ganancia garantizada: ~7.3%
   
   ⚠️ Requiere ejecución simultánea en Polymarket + Doradobet.
   Verificar límites de apuesta y slippage antes de ejecutar.
   Ganancia teórica puede erosionarse en la práctica.

💡 RECOMENDACIÓN CLEO:
   España en Polymarket ofrece el mayor valor según Ryder (+13.1% EV).
   Si solo una apuesta: España / Polymarket / 9.2% bankroll.
   
   Doradobet tiene vig alto (8.1%). Evitar salvo líneas específicas
   donde el devig genere valor real (como Marruecos aquí a +5.6% EV).
   
   Kalshi: referencial, no operable desde CR.

⚠️ AVISOS:
   • EV positivo ≠ ganancia garantizada. Basado en modelo Ryder.
   • Polymarket: verificar acceso desde CR (posible VPN necesaria).
   • Kalshi: solo referencia. Requiere cuenta USA para operar.

══════════════════════════════════════════════════════
[cleo] v1.0 · ProGol CR · 2026-06-22 14:32 UTC
EV positivo no garantiza resultado. Juegue con responsabilidad.
```

---

## 6. INTEGRACIÓN CON PROGOL CR

### 6.1 Activación

**Manual:**
```
@Cleo [equipo_local] vs [equipo_visitante]
@Cleo España vs Marruecos
```

**Automática (post-Ryder):**
```python
# En ryder.py, al final de analyze():
if AUTO_CLEO_ENABLED:
    cleo_result = cleo.analyze(home, away, ryder_probs)
    print(cleo.format_response(cleo_result))
```

**Con probabilidades manuales:**
```
@Cleo España vs Marruecos --home 0.543 --draw 0.265 --away 0.192
```

### 6.2 Flujo de datos

```
Usuario / Sistema
      │
      ▼
  ProGol CR Chat
      │
      ├─ "@Cleo" detectado
      │
      ▼
  CleoAgent.analyze(home, away)
      │
      ├─ Llama a model.predict(home, away)  ← Ryder
      │         └─ retorna ryder_probs
      │
      ├─ fetch_polymarket()  ──┐
      ├─ fetch_kalshi()        ├─ paralelo (threading / asyncio)
      ├─ fetch_doradobet()  ───┘
      │
      ├─ calcular EV, Kelly, Arbitraje
      │
      ▼
  format_response()
      │
      ▼
  Chat output + log a picks_history.json
```

### 6.3 Almacenamiento de historial (picks_history.json)

```json
{
  "picks": [
    {
      "id": "cleo_20260705_001",
      "match": "España vs Marruecos",
      "match_date": "2026-07-05",
      "analysis_ts": "2026-07-05T14:32:00Z",
      "top_pick": {
        "outcome": "home",
        "platform": "polymarket",
        "decimal_odd": 2.083,
        "p_ryder": 0.543,
        "ev_pct": 13.1,
        "kelly_recommended": 0.092
      },
      "result": null,          ← se llena post-partido
      "actual_winner": null,   ← "home" / "draw" / "away"
      "pick_correct": null,    ← true / false
      "calibration_note": null
    }
  ]
}
```

### 6.4 Autocalibración (v3+)

Tras cada partido, Cleo actualiza `picks_history.json` con el resultado real y calcula:

```
Brier Score de Cleo:
  BS_cleo = mean((p_ryder_pick - resultado_binario)^2)

Hit Rate de picks +EV:
  HR = picks_correctos_ev_positivo / total_picks_ev_positivo

ROI tracking:
  ROI = (retorno_total - apuestas_totales) / apuestas_totales * 100
```

---

## 7. MÓDULO cleo.py — ARQUITECTURA

Ver archivo `cleo.py` generado junto a este documento.

### Estructura de módulos

```
worldcup-warroom/
├── ryder.py              ← agente existente (no modificar)
├── model.py              ← Dixon-Coles + Elo (no modificar)
├── cleo.py               ← nuevo módulo (este archivo)
├── config.json           ← sesiones y configuración
├── picks_history.json    ← generado por Cleo en primera ejecución
└── CLEO_AGENT.md         ← este documento
```

---

## 8. CONSIDERACIONES DE RIESGO Y COMPLIANCE

### 8.1 Por plataforma

| Plataforma  | Riesgo Operativo                           | Riesgo Legal (CR)      | Cleo puede operar |
|-------------|-------------------------------------------|------------------------|-------------------|
| Polymarket  | Geobloqueo posible, wallet requerida       | Zona gris (cripto)     | ✅ Con precaución  |
| Kalshi      | Solo USA, KYC estricto                    | No aplica desde CR     | ❌ Solo referencia |
| Doradobet   | Scraping frágil, sesión expirable         | Regulado LATAM         | ✅ Usuario activo  |
| Betcris     | Scraping público                          | Regulado LATAM         | ✅ (v2)            |
| Codere      | Scraping público                          | Regulado CR/LATAM      | ✅ (v2)            |
| Bodog       | Sin API pública                           | Zona gris              | ⚠️ (v2)            |

### 8.2 Bankroll Management — Reglas Duras de Cleo

1. **Nunca > 15% del bankroll** en un solo pick (cap absoluto, sin excepciones)
2. **Kelly fraccional 1/4** como default (no Kelly completo)
3. **EV mínimo 2%** para mencionar una oportunidad. EV mínimo 5% para recomendar activamente
4. **Sin apuestas en cadena:** Cleo no recomienda acumuladores (parlays). EV se destruye en combinaciones
5. **Liquidez mínima:** En Polymarket, si liquidez < $5,000, Cleo advierte sobre riesgo de slippage

### 8.3 Disclaimers obligatorios

Cleo **siempre** incluye al final de cada análisis:

```
⚠️ EV positivo no garantiza resultado. El modelo Ryder tiene supuestos
   estadísticos que pueden no reflejar factores no cuantificados
   (lesiones de última hora, condiciones climáticas, arbitraje de árbitros).
   Juegue con responsabilidad. No apueste más de lo que puede perder.
```

### 8.4 Polymarket — Aviso específico

```python
POLYMARKET_WARNING = (
    "Polymarket opera sobre blockchain Polygon (cripto). "
    "El acceso desde Costa Rica puede estar restringido. "
    "Cleo muestra precios para análisis. Verificar términos de servicio "
    "antes de operar. No es asesoría financiera."
)
```

---

## 9. ROADMAP

### v1.0 — Análisis Manual (actual)
- [x] Especificación completa (este documento)
- [x] Módulo `cleo.py` con skeleton implementable
- [x] Fetch real de Polymarket (gamma-api)
- [x] Scraping de Doradobet con sesión guardada
- [x] Kalshi como referencia (read-only)
- [x] Motor EV + Kelly + Arbitraje
- [x] Formato de respuesta para chat
- [x] Activación con `@Cleo`
- [ ] Integración con `model.predict()` de Ryder

### v2.0 — Alertas Automáticas
- [ ] Background worker: escanear todos los partidos del día cada 5 min
- [ ] Alerta automática cuando EV > 10% en cualquier partido
- [ ] Implementar Betcris, Codere scraping
- [ ] Mejorar búsqueda de mercados en Polymarket (fuzzy matching de equipos)
- [ ] Rate limiting y retry logic para todos los fetches

### v3.0 — Tracking y Calibración
- [ ] Actualización automática de `picks_history.json` con resultados reales
- [ ] Cálculo de Brier Score, Hit Rate, ROI de picks de Cleo
- [ ] Dashboard de calibración: ¿las predicciones Ryder + Cleo son rentables?
- [ ] Comparar ROI por plataforma (¿Polymarket más eficiente que Doradobet?)

### v4.0 — Ejecución Semi-Automática
- [ ] Integración con wallet USDC (Polygon) para alertas de ejecución en Polymarket
- [ ] Notificaciones push cuando se detecta arbitraje > 3%
- [ ] Stubs para API de Betcris/Codere si publican endpoints oficiales
- [ ] Módulo de optimización de portfolio (Kelly multi-outcome simultáneo)

---

*Generado para ProGol CR — Mundial 2026*
*Cleo v1.0.0 · 2026-06-22*
*EV positivo no garantiza resultado. Juegue con responsabilidad.*
