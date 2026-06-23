// ---------- World Cup 2026 War Room — frontend ----------

const FLAGS = {
  "Mexico":"🇲🇽","South Africa":"🇿🇦","South Korea":"🇰🇷","Korea Republic":"🇰🇷",
  "Czech Republic":"🇨🇿","Czechia":"🇨🇿","Canada":"🇨🇦","Switzerland":"🇨🇭","Qatar":"🇶🇦",
  "Bosnia-Herzegovina":"🇧🇦","Bosnia and Herzegovina":"🇧🇦","Brazil":"🇧🇷","Morocco":"🇲🇦",
  "Haiti":"🇭🇹","Scotland":"🏴󠁧󠁢󠁳󠁣󠁴󠁿","United States":"🇺🇸","USA":"🇺🇸","Paraguay":"🇵🇾",
  "Australia":"🇦🇺","Turkey":"🇹🇷","Türkiye":"🇹🇷","Germany":"🇩🇪","Curacao":"🇨🇼","Curaçao":"🇨🇼",
  "Belgium":"🇧🇪","Egypt":"🇪🇬","Iran":"🇮🇷","New Zealand":"🇳🇿","Spain":"🇪🇸","Cape Verde":"🇨🇻",
  "Saudi Arabia":"🇸🇦","Uruguay":"🇺🇾","France":"🇫🇷","Senegal":"🇸🇳","Iraq":"🇮🇶","Norway":"🇳🇴",
  "Argentina":"🇦🇷","Algeria":"🇩🇿","Austria":"🇦🇹","Jordan":"🇯🇴","Portugal":"🇵🇹",
  "DR Congo":"🇨🇩","Congo DR":"🇨🇩","DR Congo (Congo)":"🇨🇩","Uzbekistan":"🇺🇿","Colombia":"🇨🇴",
  "England":"🏴󠁧󠁢󠁥󠁮󠁧󠁿","Croatia":"🇭🇷","Ghana":"🇬🇭","Panama":"🇵🇦","Netherlands":"🇳🇱","Japan":"🇯🇵",
  "Italy":"🇮🇹","Ecuador":"🇪🇨","Ivory Coast":"🇨🇮","Côte d'Ivoire":"🇨🇮","Tunisia":"🇹🇳",
  "Costa Rica":"🇨🇷","Nigeria":"🇳🇬","Cameroon":"🇨🇲","Wales":"🏴󠁧󠁢󠁷󠁬󠁳󠁿","Denmark":"🇩🇰",
  "Poland":"🇵🇱","Serbia":"🇷🇸","Ukraine":"🇺🇦","Peru":"🇵🇪","Chile":"🇨🇱","Mali":"🇲🇱",
  // Extended coverage (national teams that show up in friendlies/qualifiers)
  "Iceland":"🇮🇸","Finland":"🇫🇮","Estonia":"🇪🇪","Latvia":"🇱🇻","Lithuania":"🇱🇹",
  "Slovakia":"🇸🇰","Slovenia":"🇸🇮","Romania":"🇷🇴","Bulgaria":"🇧🇬","Albania":"🇦🇱",
  "Georgia":"🇬🇪","Armenia":"🇦🇲","Azerbaijan":"🇦🇿","Kazakhstan":"🇰🇿","Israel":"🇮🇱",
  "Cyprus":"🇨🇾","Luxembourg":"🇱🇺","Moldova":"🇲🇩","North Macedonia":"🇲🇰","Montenegro":"🇲🇪",
  "Kosovo":"🇽🇰","Faroe Islands":"🇫🇴","Malta":"🇲🇹","Andorra":"🇦🇩","San Marino":"🇸🇲",
  "Gibraltar":"🇬🇮","Liechtenstein":"🇱🇮","Belarus":"🇧🇾","Republic of Ireland":"🇮🇪","Ireland":"🇮🇪",
  "Bolivia":"🇧🇴","Venezuela":"🇻🇪","Honduras":"🇭🇳","El Salvador":"🇸🇻","Guatemala":"🇬🇹",
  "Nicaragua":"🇳🇮","Trinidad and Tobago":"🇹🇹","Jamaica":"🇯🇲","Grenada":"🇬🇩","Guyana":"🇬🇾",
  "Suriname":"🇸🇷","Dominican Republic":"🇩🇴","Bermuda":"🇧🇲","Zambia":"🇿🇲","Zimbabwe":"🇿🇼",
  "Kenya":"🇰🇪","Uganda":"🇺🇬","Angola":"🇦🇴","Mozambique":"🇲🇿","Burkina Faso":"🇧🇫",
  "Guinea":"🇬🇳","Gabon":"🇬🇦","Benin":"🇧🇯","Togo":"🇹🇬","Madagascar":"🇲🇬","Mauritania":"🇲🇷",
  "Namibia":"🇳🇦","Sudan":"🇸🇩","Libya":"🇱🇾","China":"🇨🇳","China PR":"🇨🇳","North Korea":"🇰🇵",
  "Oman":"🇴🇲","Bahrain":"🇧🇭","Kuwait":"🇰🇼","Syria":"🇸🇾","Lebanon":"🇱🇧",
  "United Arab Emirates":"🇦🇪","India":"🇮🇳","Thailand":"🇹🇭","Vietnam":"🇻🇳","Malaysia":"🇲🇾",
  "Indonesia":"🇮🇩","Philippines":"🇵🇭","Hong Kong":"🇭🇰","Tajikistan":"🇹🇯","Turkmenistan":"🇹🇲",
  "Kyrgyzstan":"🇰🇬","Palestine":"🇵🇸","Yemen":"🇾🇪","Fiji":"🇫🇯","Papua New Guinea":"🇵🇬",
  "Solomon Islands":"🇸🇧","New Caledonia":"🇳🇨","Tahiti":"🇵🇫","Vanuatu":"🇻🇺",
};
const flag = (name) => FLAGS[name?.trim()] || "⚽";

// Windows doesn't render flag emoji as flags, so use real flag images (flagcdn).
const FLAG_SPECIAL = { "England": "gb-eng", "Scotland": "gb-sct", "Wales": "gb-wls", "Northern Ireland": "gb-nir" };
function isoFromEmoji(emoji) {
  const letters = [...(emoji || "")]
    .map((c) => c.codePointAt(0))
    .filter((cp) => cp >= 0x1f1e6 && cp <= 0x1f1ff)
    .map((cp) => String.fromCharCode(cp - 0x1f1e6 + 65));
  return letters.length === 2 ? letters.join("").toLowerCase() : null;
}
function flagImg(name, cls = "flag-img") {
  const key = (name || "").trim();
  let code = FLAG_SPECIAL[key];
  if (!code) { const e = FLAGS[key]; if (e) code = isoFromEmoji(e); }
  if (!code) return `<span class="flag-emoji">${flag(name)}</span>`;
  return `<img class="${cls}" src="https://flagcdn.com/w80/${code}.png" alt="${escapeHtml(key)}" loading="lazy" onerror="this.outerHTML='<span class=\\'flag-emoji\\'>⚽</span>'">`;
}

// Club crest (badge image) for club matches; flag for national teams.
function crest(m, side, lg) {
  const badge = side === "home" ? m.homeBadge : m.awayBadge;
  const name = side === "home" ? m.home : m.away;
  if (badge) {
    return `<img class="${lg ? "crest-lg" : "crest"}" src="${escapeHtml(badge)}" alt="${escapeHtml(name)}" loading="lazy" onerror="this.outerHTML='<span class=\\'flag-emoji\\'>⚽</span>'">`;
  }
  return flagImg(name, lg ? "flag-img-lg" : "flag-img");
}

function localDateStr() {
  const d = new Date();
  return `${d.getFullYear()}-${String(d.getMonth()+1).padStart(2,'0')}-${String(d.getDate()).padStart(2,'0')}`;
}

const state = {
  date: localDateStr(),
  scope: "worldcup",
  matches: [],
  history: [],
  config: { hasAnthropicKey: false, model: "claude-sonnet-4-6", sportsdbKey: "3", hasRemoteToken: false },
  user: { username: "", role: "premium", perms: {} },
  autoTimer: null,
  liveTimer: null,
  currentMatch: null,
  currentPred: null,
  lang: localStorage.getItem("wr_lang") ||
        ((navigator.language || "").toLowerCase().startsWith("es") ? "es" : "en"),
  db: { loggedIn: false, username: "", checked: false },
};

// ---------- i18n ----------
const I18N = {
en: {
  tagline: "Live fixtures · predictive insights · on-demand analysis",
  topPicksBtnTitle: "Top 10 confident predictions today",
  notesBtnTitle: "Analyst notes (local database)",
  settingsBtnTitle: "Settings",
  prevDay: "Previous day", nextDay: "Next day", today: "Today",
  scopeWC: "🏆 World Cup", scopeIntl: "🌍 International", scopeClubs: "⚽ Top Leagues",
  refresh: "⟳ Refresh", offlineBadge: "offline · cached",
  loadingFixtures: "Loading fixtures…",
  matchCount: (n) => n === 1 ? "1 match" : `${n} matches`,
  noClubMatches: `No club matches in the tracked top leagues on this date.<br><span class="muted">Most European leagues are off-season in June — try an in-season date, or switch to World Cup / International.</span>`,
  noMatches: (what) => `No ${what} on this date.<br><span class="muted">Use ◀ ▶ to browse other days, or switch the competition filter above.</span>`,
  intlMatches: "international matches", wcMatches: "World Cup matches",
  loadErr: "Couldn't load live data:", tryRefresh: "Try Refresh, or check your connection.",
  netErr: "Network error reaching the local server.",
  st_Scheduled: "Scheduled", st_Live: "Live", st_Finished: "Finished",
  st_Cancelled: "Cancelled", st_Postponed: "Postponed",
  askAnalyst: "Ask the Analyst",
  chatIntro: `<p>I'm Ryder, your World Cup analyst. I can see the fixtures on the left in real time. <strong>Click any match</strong> for a full predictive breakdown — or ask me anything.</p><p class="muted">I separate fact from opinion and always flag uncertainty.</p>`,
  chip1: "Preview today's games", chip2: "Biggest match today & key tactical battle",
  chip3: "Corner & card outlook", chip4: "Who should I watch?",
  chatPlaceholder: "Ask about lineups, tactics, corners, predictions…", send: "Send",
  analyzing: "Analyzing", cantReach: "Could not reach the analyst:",
  noKeyChat: "⚠️ No Anthropic API key set yet. Click the ⚙ Settings button and paste your key to enable chat.",
  claudeConnected: "Claude connected · ", addKey: "⚙ Add API key to enable",
  pillSet: "set ✓", pillNotSet: "not set",
  recentForm: "Recent form", modelVerdict: "Model verdict",
  favored: (t) => `${t} favored`, confidence: (c) => `Confidence ${c}/10`,
  resultProb: "Match result probability", draw: "Draw",
  keyMarkets: "Key markets", whoFirst: "⚽ Who scores first", firstCorner: "🚩 First corner",
  xg: "Expected goals (xG)", xCorners: "Expected corners (est.)", btts: "Both teams score",
  ou25: "Over / Under 2.5", modelGoals: "model goals per side",
  leanYes: "leaning yes", leanNo: "leaning no", underX: (x) => `under ${x}`,
  advMarkets: "Advanced markets",
  over15: "Over 1.5 goals", over35: "Over 3.5 goals",
  csHome: "🧤 Home clean sheet", csAway: "🧤 Away clean sheet",
  concedesNothing: (t) => `${t} concedes nothing`,
  dc1x: "Double chance 1X", dc12: "Double chance 12",
  orDraw: (t) => `${t} or draw`, eitherWins: "either team wins",
  htLabel: "Half-time result (first-half estimate)",
  scorelines: "Most likely scorelines",
  bestBets: "Best bets — model combos", freeBadge: "free · no API",
  secureCombo: "Secure combo", riskyCombo: "Risky combo",
  legsHit: (n, c, o) => `All ${n} legs hit ≈ <strong>${c}%</strong> · fair odds ≈ <strong>${o}x</strong>`,
  longshotLabel: "Longshot of the match:",
  exactScore: (h, hs, as, a) => `Exact score ${h} ${hs}–${as} ${a}`,
  fairOdds: (o) => `fair odds ≈ ${o}x`,
  betDisclaimer: "⚠️ Model estimates, not betting advice. Legs are correlated, so true combo odds differ from the simple product. Never bet more than you can afford to lose.",
  legToScore: (t) => `${t} to score`, legDC: (t) => `${t} or draw (double chance)`,
  legU35: "Under 3.5 goals", legO15: "Over 1.5 goals", legO25: "Over 2.5 goals",
  legFirstCorner: (t) => `${t} takes the first corner`,
  legBttsYes: "Both teams to score", legBttsNo: "Both teams to score: NO",
  legToWin: (t) => `${t} to win`, legScoresFirst: (t) => `${t} scores first`,
  legHtLead: (t) => `${t} leading at half-time`, legWtn: (t) => `${t} to win to nil`,
  legU25: "Under 2.5 goals",
  quickRead: "Analyst quick read",
  readDisclaimer: "Generated from model numbers — zero API cost. Use the AI deep-dive below for squad intel &amp; tactical depth (requires Anthropic credits).",
  rVerdict: "Verdict", rGoals: "Goals", rFirstHalf: "First half", rFirstGoal: "First goal",
  rSetPieces: "Set pieces", rDiscipline: "Discipline", rRisk: "Risk",
  vHeavy: (f, p) => `<strong>${f}</strong> are heavy favorites at <strong>${p}%</strong>. The model sees a clear quality gap — expect them to control proceedings barring a shock.`,
  vModerate: (f, p, u, up, d) => `<strong>${f}</strong> are moderate favorites at ${p}%, but <strong>${u}</strong> at ${up}% keeps this genuinely competitive. Draw (${d}%) is very much alive.`,
  vNarrow: (f, p, d) => `Narrow edge to <strong>${f}</strong> at ${p}%, with the draw (${d}%) almost equally likely. Treat this as a tight contest — small margins decide it.`,
  vCoinflip: (f, p) => `Near coin-flip — <strong>${f}</strong> shade it at ${p}% but any result is plausible. Do not back a heavy favorite here.`,
  gVeryLow: (h, a, t, o, b) => `Very low scoring expected (xG ${h}–${a}, total ${t}). Over 2.5 at just ${o}% — the under is the clear lean. BTTS ${b}% leans no.`,
  gModest: (h, a, o, b) => `Modest output likely (xG ${h}–${a}). Over 2.5 at ${o}%, BTTS ${b}% — goals will come but won't flow freely. Over 1.5 is the safer over-ball.`,
  gDecent: (h, a, o, b) => `Decent goal output expected (xG ${h}–${a}). Over 2.5 (${o}%) and BTTS (${b}%) are both live. Watch the first 20 min for the tone.`,
  gFeast: (h, a, t, o, b) => `Open, attacking game — model sees a goal feast (xG ${h}–${a}, total ${t}). Over 2.5 (${o}%) and BTTS (${b}%) both strongly expected.`,
  htCagey: (d) => `HT draw (${d}%) is the single most likely interval result — a cagey first half is expected. Teams likely feeling each other out.`,
  htEdge: (t, p, h, hp, d, a, ap) => `<strong>${t}</strong> edge the half-time result at ${p}% — HT: ${h} ${hp}% / Draw ${d}% / ${a} ${ap}%.`,
  fgText: (t, p, n) => `<strong>${t}</strong> most likely to open the scoring (${p}%). Goalless at full time: ${n}%.`,
  spText: (t, tot, h, hc, a, ac, fp) => `<strong>${t}</strong> should dominate corners — ${tot} expected (${h} ${hc} / ${a} ${ac}). First corner ${fp}% to ${t}.`,
  dFeisty: "feisty and physical", dModerate: "moderate card count", dDisciplined: "relatively disciplined",
  dText: (tot, h, hc, a, ac, ctx) => `${tot} total cards expected (${h} ${hc} / ${a} ${ac}) — ${ctx}. Underdog may foul more to break up play.`,
  rkLive: (u, p) => `<strong>Upset genuinely live:</strong> ${u} have a ${p}% chance. One goal from a set piece or counter could flip everything.`,
  rkPossible: (u, p) => `${u} at ${p}% — an upset is possible if they absorb pressure and hit on the break. Don't completely fade them.`,
  rkUnlikely: (u, p) => `${u} at ${p}% — the model doesn't fancy an upset, but in football it's never zero.`,
  deepdiveBtn: "🧠 AI deep-dive on this match",
  ddNoKeyIntro: "Add an Anthropic API key in ⚙ Settings to run the deep-dive here, or paste this prompt into Claude.ai for free:",
  ddFallbackHint: `Copy this prompt → paste into <strong>Claude.ai</strong> or <strong>ChatGPT</strong>:`,
  copyPrompt: "Copy prompt", copied: "✓ Copied!", openClaude: "Open Claude.ai →",
  modelNote1: "Model estimate — not a guarantee.",
  modelNote2: "It does not yet factor lineups, injuries, referee or weather — use the AI deep-dive to layer those in.",
  modelNoteCards: (t, h, hc, a, ac) => `Expected cards (model estimate): ${t} total (${h} ${hc} · ${a} ${ac}).`,
  inclHomeEdge: ", incl. home edge", strength: "strength",
  lowDataWarn: "<strong>⚠ Limited data:</strong> one or both teams aren't in the ratings table, so this is a rough baseline — lean on the AI deep-dive here.",
  liveTitle: "🔴 LIVE in-play read", liveUpdating: "updating live",
  liveMinute: (mn) => `${mn}'`, liveScore: "Live score",
  liveNextGoal: "Next goal", liveNone: "No more goals",
  liveResultNow: "Result from here", liveRecos: "Live bet ideas",
  liveLeaderHolds: (t, p) => `${t} to hold on — ${p}% to win from here`,
  liveNextHome: (t, p) => `Next goal: ${t} (${p}%)`,
  liveOver: (line, p) => `Live over ${line} goals (${p}%)`,
  liveUnder: (line, p) => `Live under ${line} goals (${p}%)`,
  liveBttsYes: (p) => `Both teams to score: still on (${p}%)`,
  liveComeback: (t, p) => `${t} to recover a draw or better (${p}%)`,
  liveDrawNow: (p) => `Draw protected — ${p}% it stays level`,
  liveNextNone: (p) => `No goal before the next break looks likely (${p}% no more goals)`,
  liveDisclaimer: "Re-projected from the live score & clock. Refreshes automatically. Spot a price above the fair odds at your book — that's the value.",
  liveFairOdds: (o) => `fair odds ≈ ${o}x`,
  liveOnlyWhenLive: "This panel activates automatically when the match is in play.",
  topPicksHeader: "🎯 Top 10 Confident Picks",
  topPicksSub: "Today's matches ranked by model confidence — highest predictability first. Click any pick for the full breakdown.",
  crunching: "Crunching predictions…",
  noPicks: (d) => `No predictions available yet for <strong>${d}</strong>.`,
  noPicksHint: "Browse some matches first so they get cached, then re-open Top Picks.",
  couldNotLoadPicks: "Could not load picks:",
  likely: (h, a) => `Likely ${h}–${a}`, upcoming: "Upcoming", liveBadge: "● LIVE",
  pickConfTitle: (c) => `Model confidence ${c}/10`,
  notesHeader: "📝 Analyst Notes",
  notesDesc: `Saved in your local database (<code>warroom.db</code>), tied to the selected date. The start of your running analyst log.`,
  noteTitlePh: "Title (optional) — e.g. 'Mexico press weakness'",
  noteBodyPh: "Observation, tactical note, injury intel, prediction…",
  saveNote: "Save note", loadingNotes: "Loading…",
  noNotes: "No notes for this date yet.", cantLoadNotes: "Couldn't load notes.",
  delNote: "Delete note", defaultNoteTitle: "Note",
  settingsHeader: "Settings",
  settingsDesc: `Stored locally on your PC in <code>config.json</code>. Nothing is uploaded except direct calls to Anthropic when you chat.`,
  apiKeyLabel: "Anthropic API key",
  apiKeyHint: `Get one at <strong>console.anthropic.com</strong> → API Keys. Leave blank to keep the existing key.`,
  modelLabel: "Model", sportsLabel: "Sports data key (TheSportsDB)",
  sportsHint: `Default <code>3</code> is a free public key. Add your own premium key for faster live updates.`,
  tokenLabel: "Remote access token", tokenPh: "Set a password for tunnel access",
  tokenHint: `Required when running <code>python server.py --tunnel</code>. Anyone with the tunnel URL will need this token. Leave blank to clear.`,
  save: "Save",
},
es: {
  tagline: "Partidos en vivo · predicciones · análisis a demanda",
  topPicksBtnTitle: "Top 10 pronósticos confiables de hoy",
  notesBtnTitle: "Notas del analista (base de datos local)",
  settingsBtnTitle: "Configuración",
  prevDay: "Día anterior", nextDay: "Día siguiente", today: "Hoy",
  scopeWC: "🏆 Mundial", scopeIntl: "🌍 Internacional", scopeClubs: "⚽ Ligas Top",
  refresh: "⟳ Actualizar", offlineBadge: "sin conexión · caché",
  loadingFixtures: "Cargando partidos…",
  matchCount: (n) => n === 1 ? "1 partido" : `${n} partidos`,
  noClubMatches: `No hay partidos de clubes en las ligas seguidas en esta fecha.<br><span class="muted">La mayoría de las ligas europeas están de vacaciones en junio — prueba una fecha de temporada o cambia a Mundial / Internacional.</span>`,
  noMatches: (what) => `No hay ${what} en esta fecha.<br><span class="muted">Usa ◀ ▶ para ver otros días o cambia el filtro de competición arriba.</span>`,
  intlMatches: "partidos internacionales", wcMatches: "partidos del Mundial",
  loadErr: "No se pudieron cargar los datos en vivo:", tryRefresh: "Prueba Actualizar o revisa tu conexión.",
  netErr: "Error de red con el servidor local.",
  st_Scheduled: "Programado", st_Live: "En vivo", st_Finished: "Finalizado",
  st_Cancelled: "Cancelado", st_Postponed: "Pospuesto",
  askAnalyst: "Pregunta al Analista",
  chatIntro: `<p>Soy Ryder, tu analista del Mundial. Veo los partidos de la izquierda en tiempo real. <strong>Toca cualquier partido</strong> para un desglose predictivo completo — o pregúntame lo que sea.</p><p class="muted">Separo hechos de opiniones y siempre señalo la incertidumbre.</p>`,
  chip1: "Resumen de los partidos de hoy", chip2: "Partido más importante de hoy y su batalla táctica",
  chip3: "Panorama de córners y tarjetas", chip4: "¿A quién debo seguir?",
  chatPlaceholder: "Pregunta por alineaciones, tácticas, córners, predicciones…", send: "Enviar",
  analyzing: "Analizando", cantReach: "No se pudo contactar al analista:",
  noKeyChat: "⚠️ Aún no hay clave API de Anthropic. Pulsa el botón ⚙ Configuración y pega tu clave para activar el chat.",
  claudeConnected: "Claude conectado · ", addKey: "⚙ Agrega tu clave API para activar",
  pillSet: "configurada ✓", pillNotSet: "sin configurar",
  recentForm: "Forma reciente", modelVerdict: "Veredicto del modelo",
  favored: (t) => `Favorito: ${t}`, confidence: (c) => `Confianza ${c}/10`,
  resultProb: "Probabilidad del resultado", draw: "Empate",
  keyMarkets: "Mercados clave", whoFirst: "⚽ Quién anota primero", firstCorner: "🚩 Primer córner",
  xg: "Goles esperados (xG)", xCorners: "Córners esperados (est.)", btts: "Ambos equipos anotan",
  ou25: "Más / Menos 2.5", modelGoals: "goles del modelo por equipo",
  leanYes: "se inclina al sí", leanNo: "se inclina al no", underX: (x) => `menos ${x}`,
  advMarkets: "Mercados avanzados",
  over15: "Más de 1.5 goles", over35: "Más de 3.5 goles",
  csHome: "🧤 Local sin recibir gol", csAway: "🧤 Visitante sin recibir gol",
  concedesNothing: (t) => `${t} no recibe gol`,
  dc1x: "Doble oportunidad 1X", dc12: "Doble oportunidad 12",
  orDraw: (t) => `${t} o empate`, eitherWins: "cualquiera gana",
  htLabel: "Resultado al descanso (estimación del 1er tiempo)",
  scorelines: "Marcadores más probables",
  bestBets: "Mejores apuestas — combinadas del modelo", freeBadge: "gratis · sin API",
  secureCombo: "Combinada segura", riskyCombo: "Combinada arriesgada",
  legsHit: (n, c, o) => `Las ${n} selecciones aciertan ≈ <strong>${c}%</strong> · cuota justa ≈ <strong>${o}x</strong>`,
  longshotLabel: "Apuesta remota del partido:",
  exactScore: (h, hs, as, a) => `Marcador exacto ${h} ${hs}–${as} ${a}`,
  fairOdds: (o) => `cuota justa ≈ ${o}x`,
  betDisclaimer: "⚠️ Estimaciones del modelo, no consejo de apuestas. Las selecciones están correlacionadas, así que la cuota real difiere del producto simple. Nunca apuestes más de lo que puedas permitirte perder.",
  legToScore: (t) => `${t} anota`, legDC: (t) => `${t} o empate (doble oportunidad)`,
  legU35: "Menos de 3.5 goles", legO15: "Más de 1.5 goles", legO25: "Más de 2.5 goles",
  legFirstCorner: (t) => `${t} saca el primer córner`,
  legBttsYes: "Ambos equipos anotan", legBttsNo: "Ambos anotan: NO",
  legToWin: (t) => `Gana ${t}`, legScoresFirst: (t) => `${t} anota primero`,
  legHtLead: (t) => `${t} gana al descanso`, legWtn: (t) => `${t} gana sin recibir gol`,
  legU25: "Menos de 2.5 goles",
  quickRead: "Lectura rápida del analista",
  readDisclaimer: "Generado con los números del modelo — costo de API cero. Usa el análisis IA de abajo para info de plantillas y profundidad táctica (requiere créditos de Anthropic).",
  rVerdict: "Veredicto", rGoals: "Goles", rFirstHalf: "Primer tiempo", rFirstGoal: "Primer gol",
  rSetPieces: "Balón parado", rDiscipline: "Disciplina", rRisk: "Riesgo",
  vHeavy: (f, p) => `<strong>${f}</strong> es claro favorito con <strong>${p}%</strong>. El modelo ve una brecha de calidad evidente — debería controlar el partido salvo sorpresa.`,
  vModerate: (f, p, u, up, d) => `<strong>${f}</strong> es favorito moderado con ${p}%, pero <strong>${u}</strong> con ${up}% mantiene esto competitivo. El empate (${d}%) sigue muy vivo.`,
  vNarrow: (f, p, d) => `Ventaja mínima para <strong>${f}</strong> con ${p}%, y el empate (${d}%) casi igual de probable. Trátalo como un partido cerrado — los pequeños detalles deciden.`,
  vCoinflip: (f, p) => `Prácticamente un volado — <strong>${f}</strong> apenas arriba con ${p}%, pero cualquier resultado es viable. No respaldes a un favorito fuerte aquí.`,
  gVeryLow: (h, a, t, o, b) => `Se esperan muy pocos goles (xG ${h}–${a}, total ${t}). Más de 2.5 con solo ${o}% — el under es la inclinación clara. Ambos anotan ${b}%, se inclina al no.`,
  gModest: (h, a, o, b) => `Producción modesta probable (xG ${h}–${a}). Más de 2.5 con ${o}%, ambos anotan ${b}% — habrá goles pero no fluirán. Más de 1.5 es la apuesta over más segura.`,
  gDecent: (h, a, o, b) => `Buena producción de goles esperada (xG ${h}–${a}). Más de 2.5 (${o}%) y ambos anotan (${b}%) están vivos. Observa los primeros 20 min para leer el tono.`,
  gFeast: (h, a, t, o, b) => `Partido abierto y ofensivo — el modelo ve fiesta de goles (xG ${h}–${a}, total ${t}). Más de 2.5 (${o}%) y ambos anotan (${b}%) muy probables.`,
  htCagey: (d) => `El empate al descanso (${d}%) es el resultado parcial más probable — se espera un primer tiempo cauteloso, de estudio.`,
  htEdge: (t, p, h, hp, d, a, ap) => `<strong>${t}</strong> lleva ventaja al descanso con ${p}% — HT: ${h} ${hp}% / Empate ${d}% / ${a} ${ap}%.`,
  fgText: (t, p, n) => `<strong>${t}</strong> es el más probable en abrir el marcador (${p}%). Sin goles al final: ${n}%.`,
  spText: (t, tot, h, hc, a, ac, fp) => `<strong>${t}</strong> debería dominar los córners — ${tot} esperados (${h} ${hc} / ${a} ${ac}). Primer córner ${fp}% para ${t}.`,
  dFeisty: "friccionado y físico", dModerate: "conteo moderado de tarjetas", dDisciplined: "relativamente disciplinado",
  dText: (tot, h, hc, a, ac, ctx) => `${tot} tarjetas totales esperadas (${h} ${hc} / ${a} ${ac}) — ${ctx}. El no favorito puede hacer más faltas para cortar el juego.`,
  rkLive: (u, p) => `<strong>Sorpresa muy posible:</strong> ${u} tiene ${p}% de probabilidad. Un gol de balón parado o contragolpe puede voltear todo.`,
  rkPossible: (u, p) => `${u} con ${p}% — la sorpresa es posible si aguanta la presión y golpea al contragolpe. No lo descartes por completo.`,
  rkUnlikely: (u, p) => `${u} con ${p}% — el modelo no ve la sorpresa, pero en el fútbol nunca es cero.`,
  deepdiveBtn: "🧠 Análisis IA a fondo de este partido",
  ddNoKeyIntro: "Agrega una clave API de Anthropic en ⚙ Configuración para correr el análisis aquí, o pega este prompt en Claude.ai gratis:",
  ddFallbackHint: `Copia este prompt → pégalo en <strong>Claude.ai</strong> o <strong>ChatGPT</strong>:`,
  copyPrompt: "Copiar prompt", copied: "✓ ¡Copiado!", openClaude: "Abrir Claude.ai →",
  modelNote1: "Estimación del modelo — no es garantía.",
  modelNote2: "Aún no considera alineaciones, lesiones, árbitro ni clima — usa el análisis IA para sumar eso.",
  modelNoteCards: (t, h, hc, a, ac) => `Tarjetas esperadas (estimación del modelo): ${t} en total (${h} ${hc} · ${a} ${ac}).`,
  inclHomeEdge: ", incl. ventaja de local", strength: "fuerza",
  lowDataWarn: "<strong>⚠ Datos limitados:</strong> uno o ambos equipos no están en la tabla de ratings, así que esto es una base aproximada — apóyate en el análisis IA aquí.",
  liveTitle: "🔴 Lectura EN VIVO", liveUpdating: "actualizando en vivo",
  liveMinute: (mn) => `${mn}'`, liveScore: "Marcador en vivo",
  liveNextGoal: "Próximo gol", liveNone: "Sin más goles",
  liveResultNow: "Resultado desde aquí", liveRecos: "Ideas de apuesta en vivo",
  liveLeaderHolds: (t, p) => `${t} aguanta el resultado — ${p}% de ganar desde aquí`,
  liveNextHome: (t, p) => `Próximo gol: ${t} (${p}%)`,
  liveOver: (line, p) => `Más de ${line} goles en vivo (${p}%)`,
  liveUnder: (line, p) => `Menos de ${line} goles en vivo (${p}%)`,
  liveBttsYes: (p) => `Ambos equipos anotan: sigue vivo (${p}%)`,
  liveComeback: (t, p) => `${t} rescata el empate o mejor (${p}%)`,
  liveDrawNow: (p) => `Empate protegido — ${p}% de que siga igualado`,
  liveNextNone: (p) => `Difícil que caiga gol pronto (${p}% sin más goles)`,
  liveDisclaimer: "Recalculado con el marcador y el reloj en vivo. Se actualiza solo. Si tu casa paga una cuota mayor a la justa — ahí está el valor.",
  liveFairOdds: (o) => `cuota justa ≈ ${o}x`,
  liveOnlyWhenLive: "Este panel se activa solo cuando el partido está en juego.",
  topPicksHeader: "🎯 Top 10 Pronósticos Confiables",
  topPicksSub: "Partidos del día ordenados por confianza del modelo — mayor previsibilidad primero. Toca cualquier pronóstico para el desglose completo.",
  crunching: "Calculando predicciones…",
  noPicks: (d) => `Aún no hay predicciones disponibles para <strong>${d}</strong>.`,
  noPicksHint: "Navega algunos partidos primero para que se guarden en caché y vuelve a abrir los Pronósticos.",
  couldNotLoadPicks: "No se pudieron cargar los pronósticos:",
  likely: (h, a) => `Probable ${h}–${a}`, upcoming: "Próximo", liveBadge: "● EN VIVO",
  pickConfTitle: (c) => `Confianza del modelo ${c}/10`,
  notesHeader: "📝 Notas del Analista",
  notesDesc: `Guardadas en tu base de datos local (<code>warroom.db</code>), ligadas a la fecha seleccionada. El inicio de tu bitácora de analista.`,
  noteTitlePh: "Título (opcional) — ej. 'Debilidad de México en la presión'",
  noteBodyPh: "Observación, nota táctica, info de lesiones, predicción…",
  saveNote: "Guardar nota", loadingNotes: "Cargando…",
  noNotes: "Aún no hay notas para esta fecha.", cantLoadNotes: "No se pudieron cargar las notas.",
  delNote: "Eliminar nota", defaultNoteTitle: "Nota",
  settingsHeader: "Configuración",
  settingsDesc: `Guardado localmente en tu PC en <code>config.json</code>. No se sube nada excepto las llamadas directas a Anthropic cuando chateas.`,
  apiKeyLabel: "Clave API de Anthropic",
  apiKeyHint: `Consigue una en <strong>console.anthropic.com</strong> → API Keys. Déjalo en blanco para conservar la clave actual.`,
  modelLabel: "Modelo", sportsLabel: "Clave de datos deportivos (TheSportsDB)",
  sportsHint: `La clave <code>3</code> es pública y gratuita. Usa tu propia clave premium para actualizaciones en vivo más rápidas.`,
  tokenLabel: "Token de acceso remoto", tokenPh: "Define una contraseña para el acceso por túnel",
  tokenHint: `Necesario al correr <code>python server.py --tunnel</code>. Cualquiera con la URL del túnel necesitará este token. Déjalo en blanco para borrarlo.`,
  save: "Guardar",
},
};

function t(key, ...args) {
  const dict = I18N[state.lang] || I18N.en;
  let v = dict[key];
  if (v === undefined) v = I18N.en[key];
  if (v === undefined) return key;
  return typeof v === "function" ? v(...args) : v;
}

function dateLocale() { return state.lang === "es" ? "es-MX" : "en-GB"; }

// Swap all static chrome text (elements tagged with data-i18n attributes)
function applyI18n() {
  document.documentElement.lang = state.lang;
  document.querySelectorAll("[data-i18n]").forEach(el => { el.innerHTML = t(el.dataset.i18n); });
  document.querySelectorAll("[data-i18n-html]").forEach(el => { el.innerHTML = t(el.dataset.i18nHtml); });
  document.querySelectorAll("[data-i18n-ph]").forEach(el => { el.placeholder = t(el.dataset.i18nPh); });
  document.querySelectorAll("[data-i18n-title]").forEach(el => { el.title = t(el.dataset.i18nTitle); });
  const lb = $("langBtn");
  if (lb) lb.textContent = state.lang === "es" ? "ES" : "EN";
}

function setLang(lang) {
  state.lang = lang;
  localStorage.setItem("wr_lang", lang);
  applyI18n();
  $("dateHeading").textContent = prettyDate(state.date);
  renderMatches();
  updateChatStatus();
  // Re-render any open modals in the new language
  if (!$("insightsModal").classList.contains("hidden") && state.currentPred && state.currentMatch) {
    $("insightsHeader").innerHTML = insightsHeader(state.currentMatch);
    $("insightsBody").innerHTML = renderInsights(state.currentPred, state.currentMatch);
    const btn = $("deepdiveBtn");
    if (btn) btn.onclick = () => runDeepDive(state.currentMatch, state.currentPred);
  }
  if (!$("topPicksModal").classList.contains("hidden")) loadTopPicks();
  if (!$("notesModal").classList.contains("hidden")) { $("notesDateLabel").textContent = "· " + prettyDate(state.date); loadNotes(); }
}

// ---------- helpers ----------
const $ = (id) => document.getElementById(id);

function fmtKickoff(utc) {
  if (!utc) return "";
  let iso = utc.includes("T") ? utc : utc.replace(" ", "T");
  if (!/[zZ]|[+\-]\d\d:?\d\d$/.test(iso)) iso += "Z"; // TheSportsDB is UTC
  const d = new Date(iso);
  if (isNaN(d)) return "";
  return d.toLocaleString(dateLocale(), {
    weekday: "short", hour: "2-digit", minute: "2-digit",
  });
}

function prettyDate(yyyymmdd) {
  const d = new Date(yyyymmdd + "T12:00:00");
  return d.toLocaleDateString(dateLocale(), { weekday: "long", month: "long", day: "numeric", year: "numeric" });
}

// ---------- matches ----------
async function loadMatches() {
  const list = $("matchList");
  $("dateHeading").textContent = prettyDate(state.date);
  list.innerHTML = `<div class="empty">${t("loadingFixtures")}</div>`;
  try {
    const matchRes = await fetch(`/api/matches?date=${encodeURIComponent(state.date)}&scope=${state.scope}&tz=${-new Date().getTimezoneOffset()}`);
    const data = await matchRes.json();
    state.matches = (data.matches || []).map(m => ({
      ...m,
      homeScore: m.homeScore ?? m.scoreHome ?? null,
      awayScore: m.awayScore ?? m.scoreAway ?? null,
      progress:  m.progress  ?? (m.minute != null ? m.minute + "'" : null),
    }));
    const badge = $("offlineBadge");
    if (data.cached) badge.classList.remove("hidden"); else badge.classList.add("hidden");
    if (data.error && state.matches.length === 0) {
      list.innerHTML = `<div class="error-box">${t("loadErr")}<br>${escapeHtml(data.error)}<br><br>${t("tryRefresh")}</div>`;
      $("matchCount").textContent = "";
      return;
    }
    renderMatches();
    if ($("topPicksModal") && !$("topPicksModal").classList.contains("hidden")) {
      loadTopPicks();
    }
  } catch (e) {
    list.innerHTML = `<div class="error-box">${t("netErr")}<br>${escapeHtml(String(e))}</div>`;
  }
}


function renderMatches() {
  const list = $("matchList");
  const ms = state.matches;
  $("matchCount").textContent = ms.length ? t("matchCount", ms.length) : "";
  if (!ms.length) {
    const msg = state.scope === "clubs"
      ? t("noClubMatches")
      : t("noMatches", state.scope === "international" ? t("intlMatches") : t("wcMatches"));
    list.innerHTML = `<div class="empty">${msg}</div>`;
    return;
  }
  list.innerHTML = ms.map(matchCard).join("");
  list.querySelectorAll(".match-card").forEach((el) =>
    el.addEventListener("click", () => openInsights(state.matches[+el.dataset.idx])));
}

function matchCard(m, i) {
  const live = m.status === "Live";
  const hasScore = m.homeScore !== null && m.awayScore !== null;
  const scoreHtml = hasScore
    ? `${m.homeScore}<span class="vs"> – </span>${m.awayScore}`
    : `<span class="vs">vs</span>`;
  const ko = fmtKickoff(m.kickoffUtc);
  const progress = live && m.progress ? ` · ${escapeHtml(m.progress)}` : "";

  return `
  <div class="match-card ${live ? "live" : ""}" data-idx="${i}">
    <div class="mc-top">
      <span class="status-badge status-${m.status}">${t("st_" + m.status) !== "st_" + m.status ? t("st_" + m.status) : m.status}${progress}</span>
      <span class="mc-meta">${escapeHtml(m.league || "")}${m.round ? " · MD " + escapeHtml(String(m.round)) : ""}</span>
    </div>
    <div class="mc-teams">
      <div class="team home"><span class="flag">${crest(m, "home")}</span><span class="team-name">${escapeHtml(m.home)}</span></div>
      <div class="score">${scoreHtml}</div>
      <div class="team away"><span class="team-name">${escapeHtml(m.away)}</span><span class="flag">${crest(m, "away")}</span></div>
    </div>
    <div class="mc-bottom">
      ${ko ? `<span class="ko">🕒 ${escapeHtml(ko)}</span>` : ""}
      ${m.canal ? `<span class="mc-canal">📺 ${escapeHtml(m.canal)}</span>` : ""}
      ${m.venue ? `<span class="mc-venue">📍 ${escapeHtml(m.venue)}</span>` : ""}
    </div>
  </div>`;
}

// ---------- date controls ----------
function setDate(yyyymmdd) {
  state.date = yyyymmdd;
  $("datePicker").value = yyyymmdd;
  loadMatches();
}
function shiftDay(delta) {
  const d = new Date(state.date + "T12:00:00");
  d.setDate(d.getDate() + delta);
  setDate(d.toISOString().slice(0, 10));
}

// ---------- chat ----------
function addMsg(role, html, cls = "") {
  const log = $("chatLog");
  const div = document.createElement("div");
  div.className = `msg ${role} ${cls}`.trim();
  div.innerHTML = html;
  log.appendChild(div);
  log.scrollTop = log.scrollHeight;
  if (role === "assistant") _notifyChatBubble();
  return div;
}

function sendBetRecommendations() {
  const matches = state.matches || [];
  if (!matches.length) {
    sendChat("Dame las mejores apuestas recomendadas para los partidos de hoy, incluyendo 1X2, goles, y apuestas de valor.");
    return;
  }
  const matchList = matches.map(m =>
    `${m.home} vs ${m.away} (${m.status}, ${m.kickoffUtc ? "kickoff " + m.kickoffUtc : "hora desconocida"})`
  ).join("; ");
  sendChat(
    `Analiza todos los partidos del día y dame las recomendaciones de apuestas más sólidas:\n\n${matchList}\n\n` +
    `Para CADA partido incluye:\n` +
    `• 1X2 — tu pronóstico con % de confianza y cuota estimada justa (ej: México gana ~65% → cuota justa ~1.54)\n` +
    `• Goles: Más/Menos 2.5, BTTS sí/no\n` +
    `• Apuesta de valor (si existe) — dónde el mercado puede estar equivocado\n` +
    `• Apuesta de córners (más/menos total estimado)\n\n` +
    `Al final: sugiere 1 parlay/acumulador combinando las mejores picks del día.\n` +
    `Usa tus conocimientos del Mundial 2026 y el contexto de cada equipo. ` +
    `Recuerda separar hechos de opinión y señala incertidumbres. ` +
    `⚠️ El usuario verifica y coloca sus apuestas directamente en la casa de apuestas.`
  );
}

// ---------- MAESTRO protocol ----------
async function activateMaestro() {
  // Show banner
  const banner = $("maestroBanner");
  if (banner) banner.style.display = "flex";
  // Open chat if closed
  const popup = $("chatPopup");
  if (popup && popup.classList.contains("hidden")) toggleChatPopup();
  // Show classified notice in chat
  addMsg("assistant",
    `<div style="color:#fbbf24;font-weight:700;font-size:13px;margin-bottom:8px">🔐 PROTOCOLO MAESTRO — ACTIVADO</div>
     <div style="font-size:12px;color:#94a3b8;margin-bottom:10px">Modo ultra-profundo desbloqueado. Generando combinadas del día desde el modelo…</div>`,
    "maestro-msg"
  );
  // Build local combos immediately from today's picks
  try {
    const res = await fetch(`/api/top-picks?date=${encodeURIComponent(state.date)}&tz=${-new Date().getTimezoneOffset()}`);
    const data = await res.json();
    const picks = data.picks || [];
    if (picks.length) {
      const combos = buildDayCombos(picks);
      let comboHtml = "";
      function renderMaestroCombo(title, icon, c) {
        if (!c) return `<div style="color:#475569;font-size:12px">${title}: No hay suficientes picks hoy.</div>`;
        const odds = c.combined > 0 ? (100/c.combined*0.92).toFixed(2) : "—";
        return `
          <div class="maestro-combo-block">
            <div class="maestro-combo-title" style="color:${icon==='🛡️'?'#22c55e':'#f97316'}">${icon} ${title}</div>
            ${c.legs.map(l => `
              <div class="maestro-combo-leg">
                <span style="color:#94a3b8;font-size:11.5px">${escapeHtml(l.match)}</span>
                <span style="color:#e2e8f0;font-weight:600;font-size:11.5px">${escapeHtml(l.label)}</span>
                <span style="color:#22c55e;font-weight:700;font-size:11.5px">${l.prob.toFixed(0)}%</span>
              </div>`).join("")}
            <div class="maestro-combo-foot">Prob. combinada ≈ <strong style="color:#f1f5f9">${c.combined}%</strong> · cuota justa ≈ <strong style="color:#a5b4fc">~${odds}x</strong></div>
          </div>`;
      }
      comboHtml = renderMaestroCombo("Combinada Segura (3 patas)", "🛡️", combos.safe) +
                  renderMaestroCombo("Combinada Arriesgada (5 patas)", "🔥", combos.risky);
      addMsg("assistant", comboHtml, "maestro-msg");
    }
  } catch(_) {}
  // Now ask Claude for ultra-deep analysis
  await sendChat("MAESTRO");
}

// ── Image attachment state ──────────────────────────────────────────────
let _pendingImageB64 = null;

function clearChatImage() {
  _pendingImageB64 = null;
  $("chatImageInput").value = "";
  $("imgPreviewBar").style.display = "none";
}

function initImageUpload() {
  const input = $("chatImageInput");
  if (!input) return;
  input.addEventListener("change", () => {
    const file = input.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = (ev) => {
      const dataUrl = ev.target.result;
      // Strip "data:image/...;base64," prefix
      _pendingImageB64 = dataUrl.split(",")[1];
      $("imgPreviewThumb").src = dataUrl;
      $("imgPreviewBar").style.display = "flex";
    };
    reader.readAsDataURL(file);
  });
  // Paste from clipboard (Ctrl+V in chat textarea)
  $("chatInput").addEventListener("paste", (ev) => {
    const items = ev.clipboardData && ev.clipboardData.items;
    if (!items) return;
    for (const item of items) {
      if (item.type.startsWith("image/")) {
        ev.preventDefault();
        const file = item.getAsFile();
        const reader = new FileReader();
        reader.onload = (e) => {
          _pendingImageB64 = e.target.result.split(",")[1];
          $("imgPreviewThumb").src = e.target.result;
          $("imgPreviewBar").style.display = "flex";
        };
        reader.readAsDataURL(file);
        break;
      }
    }
  });
}

async function sendChat(text) {
  text = (text || "").trim();
  const hasImage = !!_pendingImageB64;
  if (!text && !hasImage) return;
  const isMaestro = text === "MAESTRO";
  if (!isMaestro) {
    let userHtml = text ? `<p>${escapeHtml(text).replace(/\n/g, "<br>")}</p>` : "";
    if (hasImage) userHtml += `<img src="${$("imgPreviewThumb").src}" style="max-width:180px;border-radius:8px;margin-top:6px;display:block;">`;
    addMsg("user", userHtml);
  }
  state.history.push({ role: "user", content: text || "[imagen adjunta]" });
  $("chatInput").value = "";
  autoGrow($("chatInput"));
  $("sendBtn").disabled = true;
  const thinking = addMsg("assistant", `${t("analyzing")}<span class='dot-flash'></span>`, "thinking");

  const imageToSend = _pendingImageB64;
  clearChatImage();

  try {
    const body = {
      message: text,
      history: state.history.slice(0, -1),
      matches: state.matches,
      date: state.date,
      lang: state.lang,
    };
    if (imageToSend) body.image = imageToSend;
    const res = await fetch("/api/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json();
    thinking.remove();
    if (data.error) {
      addMsg("assistant", `<p>⚠️ ${escapeHtml(data.error)}</p>`);
    } else {
      addMsg("assistant", renderMarkdown(data.reply || ""));
      state.history.push({ role: "assistant", content: data.reply || "" });
      // If the agent fetched live standings/fixtures, sync the Quiniela
      if (data.refreshQuiniela && _qState.loaded) {
        loadQuiniela(true);
      }
    }
  } catch (e) {
    thinking.remove();
    addMsg("assistant", `<p>⚠️ ${t("cantReach")} ${escapeHtml(String(e))}</p>`);
  } finally {
    $("sendBtn").disabled = false;
    $("chatInput").focus();
  }
}

// ---------- minimal markdown ----------
function escapeHtml(s) {
  return String(s ?? "").replace(/[&<>"']/g, (c) => (
    { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]
  ));
}

function renderInline(s) {
  s = escapeHtml(s);
  s = s.replace(/`([^`]+)`/g, "<code>$1</code>");
  s = s.replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>");
  s = s.replace(/(^|[^*])\*([^*\n]+)\*/g, "$1<em>$2</em>");
  return s;
}

function renderMarkdown(md) {
  const lines = md.replace(/\r/g, "").split("\n");
  let html = "", i = 0;
  const closeList = (tag) => { if (tag) html += `</${tag}>`; };
  let listTag = null;

  while (i < lines.length) {
    let line = lines[i];

    // table block
    if (/^\s*\|.*\|\s*$/.test(line) && i + 1 < lines.length && /^\s*\|[\s:|-]+\|\s*$/.test(lines[i + 1])) {
      closeList(listTag); listTag = null;
      const header = line.trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim());
      i += 2;
      const rows = [];
      while (i < lines.length && /^\s*\|.*\|\s*$/.test(lines[i])) {
        rows.push(lines[i].trim().replace(/^\||\|$/g, "").split("|").map(c => c.trim()));
        i++;
      }
      html += "<table><thead><tr>" + header.map(h => `<th>${renderInline(h)}</th>`).join("") + "</tr></thead><tbody>";
      html += rows.map(r => "<tr>" + r.map(c => `<td>${renderInline(c)}</td>`).join("") + "</tr>").join("");
      html += "</tbody></table>";
      continue;
    }

    // headings
    let mh = line.match(/^(#{1,6})\s+(.*)$/);
    if (mh) { closeList(listTag); listTag = null; html += `<p><strong>${renderInline(mh[2])}</strong></p>`; i++; continue; }

    // bullet list
    if (/^\s*[-*]\s+/.test(line)) {
      if (listTag !== "ul") { closeList(listTag); html += "<ul>"; listTag = "ul"; }
      html += `<li>${renderInline(line.replace(/^\s*[-*]\s+/, ""))}</li>`; i++; continue;
    }
    // numbered list
    if (/^\s*\d+\.\s+/.test(line)) {
      if (listTag !== "ol") { closeList(listTag); html += "<ol>"; listTag = "ol"; }
      html += `<li>${renderInline(line.replace(/^\s*\d+\.\s+/, ""))}</li>`; i++; continue;
    }

    // blank
    if (line.trim() === "") { closeList(listTag); listTag = null; i++; continue; }

    // paragraph (gather consecutive plain lines)
    closeList(listTag); listTag = null;
    let para = [line];
    i++;
    while (i < lines.length && lines[i].trim() !== "" &&
           !/^\s*[-*]\s+/.test(lines[i]) && !/^\s*\d+\.\s+/.test(lines[i]) &&
           !/^\s*\|.*\|\s*$/.test(lines[i]) && !/^#{1,6}\s/.test(lines[i])) {
      para.push(lines[i]); i++;
    }
    html += `<p>${para.map(renderInline).join("<br>")}</p>`;
  }
  closeList(listTag);
  return html;
}

// ---------- settings ----------
function openSettings() {
  $("settingsModal").classList.remove("hidden");
  refreshKeyPill();
  // Load LAN IP for mobile access display
  fetch("/api/network-info").then(r => r.json()).then(d => {
    const el = $("lanUrlDisplay");
    if (el) {
      if (d.lanUrl) {
        el.innerHTML = `<a href="${escapeHtml(d.lanUrl)}" target="_blank" style="color:#22c55e;font-weight:700">${escapeHtml(d.lanUrl)}</a>`;
      } else {
        el.textContent = "No se detectó IP local. ¿Estás conectado a WiFi?";
      }
      if (d.eloOverrides > 0) {
        el.innerHTML += `<div style="margin-top:4px;color:#64748b">Modelo calibrado: ${d.eloOverrides} equipos con Elo actualizado</div>`;
      }
    }
    if (d.publicUrl) {
      const row = $("publicUrlRow");
      const pdel = $("publicUrlDisplay");
      if (row) row.style.display = "block";
      if (pdel) pdel.innerHTML = `<a href="${escapeHtml(d.publicUrl)}" target="_blank" style="color:#f59e0b;font-weight:700;word-break:break-all">${escapeHtml(d.publicUrl)}</a>`;
    }
  }).catch(() => {});
}
function closeSettings() { $("settingsModal").classList.add("hidden"); }
function refreshKeyPill() {
  const pill = $("keyState");
  if (state.config.hasAnthropicKey) { pill.textContent = t("pillSet"); pill.className = "pill ok"; }
  else { pill.textContent = t("pillNotSet"); pill.className = "pill no"; }
  $("modelInput").value = state.config.model || "claude-sonnet-4-6";
  $("sportsdbInput").value = state.config.sportsdbKey || "3";
  $("remoteTokenInput").value = "";
  const rtp = $("remoteTokenState");
  if (rtp) {
    if (state.config.hasRemoteToken) { rtp.textContent = t("pillSet"); rtp.className = "pill ok"; }
    else { rtp.textContent = t("pillNotSet"); rtp.className = "pill no"; }
  }
  // API-Football
  const afp = $("apifootballState");
  if (afp) {
    if (state.config.hasApiFootball) { afp.textContent = "✓ Activo"; afp.className = "pill ok"; }
    else { afp.textContent = "Sin clave"; afp.className = "pill no"; }
  }
  // Email fields
  if ($("emailSenderInput")) $("emailSenderInput").value = state.config.emailAddress || "";
  if ($("emailPassInput")) $("emailPassInput").value = "";
  if ($("emailRecipientInput")) $("emailRecipientInput").value = state.config.emailRecipient || "Esteban_vm12@hotmail.com";
  const esp = $("emailSenderState");
  if (esp) {
    if (state.config.emailAddress && state.config.hasEmailPassword) { esp.textContent = "✓ Listo"; esp.className = "pill ok"; }
    else { esp.textContent = "Sin config"; esp.className = "pill no"; }
  }
  const epp = $("emailPassState");
  if (epp) {
    if (state.config.hasEmailPassword) { epp.textContent = "✓ Set"; epp.className = "pill ok"; }
    else { epp.textContent = "Sin contraseña"; epp.className = "pill no"; }
  }
  // Telegram fields
  if ($("tgChatInput")) $("tgChatInput").value = state.config.telegramChatId || "";
  if ($("tgTokenInput")) $("tgTokenInput").value = "";
  const tgt = $("tgTokenState");
  if (tgt) {
    if (state.config.hasTelegramToken && state.config.telegramChatId) { tgt.textContent = "✓ Listo"; tgt.className = "pill ok"; }
    else { tgt.textContent = "Sin config"; tgt.className = "pill no"; }
  }
  const tgc = $("tgChatState");
  if (tgc) {
    if (state.config.telegramChatId) { tgc.textContent = "✓ Set"; tgc.className = "pill ok"; }
    else { tgc.textContent = "Sin ID"; tgc.className = "pill no"; }
  }
}
function updateChatStatus() {
  // chatStatus is now the animated dot in the popup header — leave it alone
}

async function loadConfig() {
  try {
    const res = await fetch("/api/config");
    state.config = await res.json();
  } catch (e) { /* ignore */ }
  updateChatStatus();
}

async function loadMe() {
  try {
    const res = await fetch("/api/me");
    if (res.status === 401) { window.location.href = "/login"; return; }
    state.user = await res.json();
  } catch (e) { return; }
  applyRole();
}

function applyRole() {
  const { role, username, perms } = state.user;
  // Show user chip
  const chip = $("userBadge");
  if (chip) {
    chip.classList.remove("hidden");
    const rolEl = $("userBadgeRole");
    const nameEl = $("userBadgeName");
    if (rolEl) { rolEl.textContent = role === "mega_premium" ? "MEGA" : role.toUpperCase(); rolEl.className = `user-chip-role ${role}`; }
    if (nameEl) nameEl.textContent = username;
  }
  // Settings gear — only maestro
  document.querySelectorAll(".settings-only").forEach(el => {
    el.style.display = perms.settings ? "inline-flex" : "none";
  });
  // MAESTRO button
  const mb = document.querySelector(".chat-maestro-btn");
  if (mb) mb.style.display = perms.maestro_btn ? "" : "none";
  // Scout Report button
  const srb = $("scoutReportBtn");
  if (srb) srb.style.display = perms.scout_report ? "" : "none";
  // Picks button (always visible but limited for premium)
  // Day combos in PICKS modal shown by data attr
  document.querySelectorAll(".maestro-only").forEach(el => {
    el.style.display = perms.maestro_btn ? "" : "none";
  });
}

async function doLogout() {
  await fetch("/api/logout", { method: "POST" }).catch(() => {});
  window.location.href = "/login";
}

async function saveSettings() {
  const payload = {
    anthropic_model: $("modelInput").value,
    sportsdb_key: $("sportsdbInput").value.trim() || "3",
  };
  const key = $("apiKeyInput").value.trim();
  if (key) payload.anthropic_api_key = key;
  const rt = $("remoteTokenInput").value;
  if (rt !== undefined) payload.remote_token = rt.trim();
  const afKey = $("apifootballInput") ? $("apifootballInput").value.trim() : "";
  if (afKey) payload.apifootball_key = afKey;
  const emailSender = $("emailSenderInput") ? $("emailSenderInput").value.trim() : "";
  if (emailSender !== undefined) payload.email_address = emailSender;
  const emailPass = $("emailPassInput") ? $("emailPassInput").value.trim() : "";
  if (emailPass) payload.email_password = emailPass;
  const emailRecipient = $("emailRecipientInput") ? $("emailRecipientInput").value.trim() : "";
  if (emailRecipient) payload.email_recipient = emailRecipient;
  const tgToken = $("tgTokenInput") ? $("tgTokenInput").value.trim() : "";
  if (tgToken) payload.telegram_bot_token = tgToken;
  const tgChat = $("tgChatInput") ? $("tgChatInput").value.trim() : "";
  if (tgChat) payload.telegram_chat_id = tgChat;
  const res = await fetch("/api/config", {
    method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload),
  });
  state.config = await res.json();
  $("apiKeyInput").value = "";
  if ($("apifootballInput")) $("apifootballInput").value = "";
  if ($("emailPassInput")) $("emailPassInput").value = "";
  if ($("tgTokenInput")) $("tgTokenInput").value = "";
  updateChatStatus();
  refreshKeyPill();
  closeSettings();
  loadMatches();
}

// ─── Gurú Bankroll Advisor ─────────────────────────────────────────────────
function openGuruModal() {
  $("guruModal").classList.remove("hidden");
  $("guruInput").focus();
}
function closeGuruModal() { $("guruModal").classList.add("hidden"); }

function renderGuruText(text) {
  var sections = [];
  var lines = text.split('\n');
  var current = null;
  lines.forEach(function(line) {
    var trimmed = line.trim();
    var isHeader = /^(🧿|📦|⚡|🎲|🏹|📊|🔮|🗓|⚠️|🔌|👇|📋|📅|💡)/.test(trimmed) && trimmed.length > 2;
    if (isHeader) {
      if (current) sections.push(current);
      current = { header: trimmed, lines: [] };
    } else if (current) {
      current.lines.push(line);
    } else {
      if (!current) current = { header: null, lines: [] };
      current.lines.push(line);
    }
  });
  if (current) sections.push(current);

  var html = '';
  sections.forEach(function(sec) {
    if (!sec.header && !sec.lines.some(function(l){ return l.trim(); })) return;

    var h = sec.header || '';
    var isTitle    = /^🧿/.test(h);
    var isCombo    = /^📦/.test(h);
    var isRisky    = /^(⚡|🎲|🏹)/.test(h);
    var isSummary  = /^📊/.test(h);
    var isWarn     = /^⚠️/.test(h);
    var isTomorrow = /^(🗓|📋)/.test(h);
    var isFooter   = /^(🔌|👇)/.test(h);

    // Strip amount from header: "📦 COMBO SEGURO — ₡10,000 apostados"
    var amtM    = h.match(/(—\s*₡[\d,\s]+\w+.*)/);
    var hdrTitle = amtM ? h.slice(0, h.indexOf(amtM[0])).trim() : h;
    var hdrAmt   = amtM ? amtM[0].replace(/^—\s*/, '') : '';

    // Accent color
    var accent = isCombo ? '#22c55e' : isRisky ? '#f59e0b' : isTomorrow ? '#60a5fa'
               : isWarn  ? '#f87171' : isSummary ? '#a78bfa' : '#475569';
    var accentCls = isCombo ? 'gb-combo' : isRisky ? 'gb-risky' : isTomorrow ? 'gb-tomorrow'
                  : isWarn ? 'gb-warn-block' : isSummary ? 'gb-summary' : '';

    // Footer / plain text (no header card)
    if (isFooter || (!sec.header && !isTitle)) {
      sec.lines.forEach(function(l) {
        if (l.trim()) html += '<div class="gb-plain-line">' + fmtGuruLine(l.trim()) + '</div>';
      });
      return;
    }

    // Parse body lines into picks, stats, etc.
    var bodyLines = sec.lines;
    var picks = [], statLines = [], otherLines = [], trailerLines = [], cuotaLine = null;
    var j = 0;
    while (j < bodyLines.length) {
      var bl = bodyLines[j].trim();
      if (!bl || /^━+$/.test(bl)) { j++; continue; }
      if (/^[•·\-]\s/.test(bl)) {
        var matchName = bl.replace(/^[•·\-]\s*/, '');
        var nextBl = (j + 1 < bodyLines.length) ? bodyLines[j + 1].trim() : '';
        if (nextBl && /@ [\d.]/.test(nextBl)) {
          picks.push({ matchName: matchName, detail: nextBl }); j += 2;
        } else {
          picks.push({ matchName: matchName, detail: null }); j++;
        }
      } else if (/^(Invertís|Si solo|Si entran|Peor caso|Retorno|Total|Podés)/.test(bl)) {
        statLines.push(bl); j++;
      } else if (/^Cuota combinada/.test(bl)) {
        cuotaLine = bl; j++;
      } else if (/^✅/.test(bl)) {
        trailerLines.push(bl); j++;
      } else {
        otherLines.push(bl); j++;
      }
    }

    // ── Card wrapper ──
    html += '<div class="gb-card ' + accentCls + '">';

    // ── Header bar with colored left strip ──
    html += '<div class="gb-hdr" style="border-left:4px solid ' + accent + '">'
          + '<span class="gb-hdr-title">' + escapeHtml(hdrTitle) + '</span>'
          + (hdrAmt ? '<span class="gb-hdr-amt">' + escapeHtml(hdrAmt) + '</span>' : '')
          + '</div>';

    // ── Intro / other lines ──
    otherLines.forEach(function(ol) {
      html += '<p class="gb-intro">' + fmtGuruLine(ol) + '</p>';
    });

    // ── Pick chips (one per pick) ──
    picks.forEach(function(pk) {
      var oddM  = pk.detail ? pk.detail.match(/@ ([\d.]+)/) : null;
      var probM = pk.detail ? pk.detail.match(/\(([\d.]+)%/) : null;
      var evM   = pk.detail ? pk.detail.match(/EV ([+\-][\d.]+%)/) : null;
      var betDesc = pk.detail ? pk.detail.replace(/\s*\(.*$/, '').replace(/\s*@ [\d.]+.*$/, '').trim() : '';
      var evVal = evM ? parseFloat(evM[1]) : -99;
      var evCls = evVal >= 0 ? 'gb-ev-pos' : 'gb-ev-neg';

      html += '<div class="gb-pick-chip">'
            +   '<div class="gb-pick-chip-top">'
            +     '<span class="gb-pick-match-name">' + escapeHtml(pk.matchName) + '</span>'
            +     (oddM ? '<span class="gb-pick-odd">' + oddM[1] + '</span>' : '')
            +   '</div>'
            +   (betDesc ? '<div class="gb-pick-bet">' + escapeHtml(betDesc) + '</div>' : '')
            +   '<div class="gb-pick-chip-bot">'
            +     (probM ? '<span class="gb-pick-prob">' + probM[1] + '% prob</span>' : '')
            +     (evM   ? '<span class="' + evCls + '">' + escapeHtml(evM[1]) + ' EV</span>' : '')
            +   '</div>'
            + '</div>';
    });

    // ── Cuota combinada ──
    if (cuotaLine) {
      var cuotaVal = cuotaLine.match(/([\d.]+)\s*$/);
      html += '<div class="gb-cuota">'
            + '<span class="gb-cuota-lbl">CUOTA COMBINADA</span>'
            + '<span class="gb-cuota-num">' + (cuotaVal ? cuotaVal[1] : cuotaLine.replace(/.*:/, '').trim()) + '</span>'
            + '</div>';
    }

    // ── Trailer / retorno lines ──
    trailerLines.forEach(function(tl) {
      html += '<div class="gb-retorno">' + fmtGuruLine(tl) + '</div>';
    });

    // ── Stats table (RESUMEN) ──
    if (statLines.length > 0) {
      html += '<div class="gb-stats">';
      statLines.forEach(function(sl) {
        var ci = sl.indexOf(':');
        if (ci > -1) {
          html += '<div class="gb-stat-row">'
                + '<span class="gb-sk">' + escapeHtml(sl.slice(0, ci).trim()) + '</span>'
                + '<span class="gb-sv">' + fmtGuruLine(sl.slice(ci + 1).trim()) + '</span>'
                + '</div>';
        } else {
          html += '<div class="gb-stat-row"><span class="gb-sk">' + fmtGuruLine(sl) + '</span></div>';
        }
      });
      html += '</div>';
    }

    html += '</div>'; // .gb-card
  });
  return html || '<p class="gb-plain-line">' + escapeHtml(text) + '</p>';
}

function fmtGuruLine(text) {
  return escapeHtml(text)
    .replace(/(₡[\d,]+)/g, '<span class="g-money">$1</span>')
    .replace(/\(EV ([+\-][\d.]+%)\)/g, '(<span class="g-ev-neg">EV $1</span>)')
    .replace(/\(EV (\+[\d.]+%)\)/g, '(<span class="g-ev-pos">EV $1</span>)')
    .replace(/(@\s*[\d.]+)/g, '<span class="g-odd">$1</span>')
    .replace(/\((\d+\.\d+%)\)/g, '(<span class="g-pct">$1</span>)')
    .replace(/(✅[^\n]*)/g, '<span class="g-return">$1</span>');
}

async function sendGuruMsg(preset) {
  const input = $("guruInput");
  const msg = preset || input.value.trim();
  if (!msg) return;
  input.value = "";

  const chat = $("guruChat");
  const welcome = chat.querySelector(".guru-welcome");
  if (welcome) welcome.remove();

  const userEl = document.createElement("div");
  userEl.className = "guru-msg user";
  userEl.textContent = msg;
  chat.appendChild(userEl);

  const loadEl = document.createElement("div");
  loadEl.className = "guru-msg loading";
  loadEl.textContent = "🧿 Gurú calculando el plan óptimo…";
  chat.appendChild(loadEl);
  chat.scrollTop = chat.scrollHeight;

  const btn = $("guruSendBtn");
  btn.disabled = true;

  try {
    const res = await fetch("/api/guru", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, matches: state.matches, date: state.date, lang: "es" }),
    });
    const data = await res.json();
    loadEl.remove();
    const replyEl = document.createElement("div");
    replyEl.className = "guru-msg guru";
    replyEl.innerHTML = data.error ? `<span class="g-warn">⚠️ ${escapeHtml(data.error)}</span>` : renderGuruText(data.reply || "");
    chat.appendChild(replyEl);
  } catch (e) {
    loadEl.textContent = `⚠️ ${e}`;
  } finally {
    btn.disabled = false;
    chat.scrollTop = chat.scrollHeight;
  }
}

// ─── Scout Report ──────────────────────────────────────────────────────────

async function loadScoutReport(force = false) {
  const modal = $("scoutReportModal");
  const body  = $("scoutReportBody");
  if (!modal || !body) return;
  modal.classList.remove("hidden");
  body.innerHTML = '<p class="muted small">Generando reporte…</p>';

  try {
    const url = `/api/scout-report?date=${state.date}${force ? "&force=1" : ""}`;
    const res  = await fetch(url);
    const data = await res.json();
    if (!data.ok) { body.innerHTML = `<p class="error">Error: ${data.error}</p>`; return; }
    body.innerHTML = renderScoutReport(data.report);
  } catch (e) {
    body.innerHTML = `<p class="error">Error de red: ${e.message}</p>`;
  }
}

function renderScoutReport(r) {
  const s = r.sample || {};
  const bm = r.by_market || {};
  const bc = r.by_confidence || {};
  const vb = r.vs_benchmark || {};
  const ds = r.data_sources || {};
  const ins = r.auto_insights || [];

  // Summary row
  const hitColor = s.hit_rate_30d >= 60 ? "#22c55e" : s.hit_rate_30d >= 50 ? "#f59e0b" : "#ef4444";
  let html = `
  <div class="sr-summary">
    <div class="sr-stat"><span class="sr-big" style="color:${hitColor}">${s.hit_rate_30d ?? "—"}%</span><span class="sr-label">Acierto 30d</span></div>
    <div class="sr-stat"><span class="sr-big">${s.total_30d ?? 0}</span><span class="sr-label">Picks resueltos</span></div>
    <div class="sr-stat"><span class="sr-big">${s.wins_30d ?? 0}</span><span class="sr-label">Aciertos</span></div>
    <div class="sr-stat"><span class="sr-big" style="color:#f59e0b">${r.brier_score ?? "—"}</span><span class="sr-label">Brier score</span></div>
  </div>
  <p class="sr-brier-note muted small">${r.brier_note || ""}</p>`;

  // Benchmark comparison table
  html += `<h3 class="sr-section">⚡ ProGol CR vs Competidores</h3>
  <div class="sr-table-wrap"><table class="sr-table">
    <thead><tr><th>Herramienta</th><th>Overall</th><th>DC</th><th>Más/Menos</th><th>BTTS</th><th>1X2</th></tr></thead>
    <tbody>`;

  const order = ["ProGol CR (Dixon-Coles)", "Forebet AI", "BetBurger Tips", "Tipster avg", "Random baseline"];
  for (const name of order) {
    const d = vb[name] || {};
    const isUs = name.startsWith("ProGol");
    const style = isUs ? 'style="font-weight:800;background:rgba(34,197,94,0.08)"' : '';
    const fmt = (v) => v != null ? `<span style="color:${v>=60?"#22c55e":v>=50?"#f59e0b":"#ef4444"}">${v}%</span>` : "—";
    html += `<tr ${style}><td>${isUs ? "🏆 " : ""}${name}</td>
      <td>${fmt(d.overall)}</td><td>${fmt(d.dc)}</td>
      <td>${fmt(d["over_2.5"] ?? d["under_2.5"])}</td>
      <td>${fmt(d.btts)}</td><td>${fmt(d["1x2"])}</td></tr>`;
  }
  html += `</tbody></table></div>
  <p class="muted small">${r.benchmark_note || ""}</p>`;

  // By confidence tier
  html += `<h3 class="sr-section">🎯 Precisión por confianza</h3>
  <div class="sr-conf-row">`;
  const confLabels = { alta: "🟢 Alta (≥68%)", media: "🟡 Media (50-67%)", especulativa: "🔴 Especulativa (<50%)" };
  for (const [tier, label] of Object.entries(confLabels)) {
    const d = bc[tier] || {};
    const pct = d.hit_rate ?? 0;
    const col = pct >= 68 ? "#22c55e" : pct >= 52 ? "#f59e0b" : "#ef4444";
    html += `<div class="sr-conf-card">
      <div class="sr-big" style="color:${col}">${pct}%</div>
      <div class="sr-label">${label}</div>
      <div class="muted small">${d.wins ?? 0}/${d.total ?? 0} picks</div>
    </div>`;
  }
  html += `</div>`;

  // Auto insights
  if (ins.length) {
    html += `<h3 class="sr-section">🔍 Insights automáticos</h3><ul class="sr-insights">`;
    ins.forEach(i => { html += `<li>${i}</li>`; });
    html += `</ul>`;
  }

  // Data sources
  if (ds.active || ds.would_improve) {
    html += `<h3 class="sr-section">📡 Datos activos vs mejoras pendientes</h3>
    <div class="sr-sources">
      <div class="sr-source-col">
        <div class="sr-source-title" style="color:#22c55e">✅ Activos</div>
        <ul>`;
    (ds.active || []).forEach(d => { html += `<li>${d}</li>`; });
    html += `</ul></div><div class="sr-source-col">
        <div class="sr-source-title" style="color:#f59e0b">⬆️ Mejoraría con</div>
        <ul>`;
    (ds.would_improve || []).forEach(d => { html += `<li>${d}</li>`; });
    html += `</ul></div></div>`;
  }

  html += `<p class="muted small" style="margin-top:16px">Generado: ${r.generated_at || "—"}</p>`;
  return html;
}

async function sendPicksEmail() {
  const btn = $("sendPicksEmailBtn");
  if (btn) { btn.disabled = true; btn.textContent = "📧 Enviando…"; }
  try {
    const res = await fetch("/api/send-picks-email", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ date: state.date, tz: -new Date().getTimezoneOffset() }),
    });
    const data = await res.json();
    if (data.ok) {
      alert("✅ " + (data.message || "Email enviado correctamente."));
    } else {
      alert("❌ Error al enviar: " + (data.error || "Error desconocido"));
    }
  } catch (e) {
    alert("❌ Error de red: " + e.message);
  } finally {
    if (btn) { btn.disabled = false; btn.textContent = "📧 Enviar picks por email"; }
  }
}

// ---------- match insights (prediction model) ----------
function pct(x) { return (Math.round(x * 10) / 10) + "%"; }

async function openInsights(m) {
  if (!m) return;
  stopLivePolling();
  state.currentMatch = m;
  $("insightsHeader").innerHTML = insightsHeader(m);
  $("insightsBody").innerHTML = `<p class="muted" style="text-align:center;padding:34px">${t("crunching")}</p>`;
  $("insightsModal").classList.remove("hidden");
  try {
    const res = await fetch(`/api/predict?home=${encodeURIComponent(m.home)}&away=${encodeURIComponent(m.away)}`);
    const pred = await res.json();
    if (pred.error) { $("insightsBody").innerHTML = `<div class="error-box">${escapeHtml(pred.error)}</div>`; return; }
    state.currentPred = pred;
    $("insightsBody").innerHTML = renderInsights(pred, m);
    // Live in-play panel + auto-refresh when the match is in progress
    if (m.status === "Live") {
      refreshLivePanel(m);
      state.liveTimer = setInterval(() => refreshLivePanel(m), 25000);
    }
    // Auto-trigger Scout agent analysis
    setTimeout(() => runDeepDive(m, pred), 700);
    fetchCouncilPanel(m);
    // Trigger live score sync (script tags in innerHTML don't execute)
    setTimeout(() => syncLiveScore(m.home, m.away), 500);
  } catch (e) {
    $("insightsBody").innerHTML = `<div class="error-box">${escapeHtml(String(e))}</div>`;
  }
}

function stopLivePolling() {
  if (state.liveTimer) { clearInterval(state.liveTimer); state.liveTimer = null; }
}

async function refreshLivePanel(m) {
  const mount = $("livePanelMount");
  if (!mount) { stopLivePolling(); return; }   // modal re-rendered/closed
  // Pull the freshest score+minute for this match from the live list if present
  const fresh = state.matches.find(x => x.home === m.home && x.away === m.away) || m;
  if (fresh.status && fresh.status !== "Live") { mount.innerHTML = ""; stopLivePolling(); return; }
  // Use numeric minute first, then progress string, then fallback to 0
  const minuteNum = fresh.minute ?? (fresh.progress ? parseInt(fresh.progress) : null);
  const minute = minuteNum != null ? String(minuteNum) : (fresh.progress || "0").toString();
  const hs = fresh.homeScore ?? fresh.scoreHome ?? 0;
  const as = fresh.awayScore ?? fresh.scoreAway ?? 0;
  try {
    const url = `/api/live?home=${encodeURIComponent(m.home)}&away=${encodeURIComponent(m.away)}`
              + `&minute=${encodeURIComponent(minute)}&hs=${hs}&as=${as}`;
    const live = await fetch(url).then(r => r.json());
    const mount2 = $("livePanelMount");
    if (mount2 && !live.error) {
      mount2.innerHTML = renderLivePanel(live, m);
      // Update main probability bar with live recalculation
      const lp = live.prob;
      if (lp) {
        const lph = lp.home, lpd = lp.draw, lpa = lp.away;
        const segH = document.getElementById('mainProbSegH');
        const segD = document.getElementById('mainProbSegD');
        const segA = document.getElementById('mainProbSegA');
        const leg  = document.getElementById('mainProbLegend');
        const lbl  = document.getElementById('mainProbLabel');
        if (segH) { segH.style.width = lph + '%'; segH.textContent = lph >= 12 ? Math.round(lph) + '%' : ''; }
        if (segD) { segD.style.width = lpd + '%'; segD.textContent = lpd >= 12 ? Math.round(lpd) + '%' : ''; }
        if (segA) { segA.style.width = lpa + '%'; segA.textContent = lpa >= 12 ? Math.round(lpa) + '%' : ''; }
        if (leg)  leg.innerHTML = `<span>🟢 ${escapeHtml(m.home)} ${pct(lph)}</span><span>${t('draw')} ${pct(lpd)}</span><span>${escapeHtml(m.away)} ${pct(lpa)} 🔵</span>`;
        if (lbl)  lbl.innerHTML = t('resultProb') + ' <span style="color:#ef4444;font-size:10px;font-weight:700;letter-spacing:.5px">● LIVE</span>';
      }
    }
  } catch (e) { /* keep last render on transient errors */ }
}

function closeInsights() { stopLivePolling(); $("insightsModal").classList.add("hidden"); }

// ── Model Health Dashboard (owner only) ──────────────────────────────────────
function closeModelHealth() {
  const m = $("modelHealthModal");
  if (m) m.classList.add("hidden");
}

async function openModelHealth() {
  const modal = $("modelHealthModal");
  const body  = $("modelHealthBody");
  if (!modal || !body) return;
  modal.classList.remove("hidden");
  body.innerHTML = '<p class="muted small">Cargando datos del modelo…</p>';

  try {
    const [health, cal, bias, sources] = await Promise.all([
      fetch("/api/ryder/model-health").then(r => r.json()),
      fetch("/api/ryder/calibration?n=100").then(r => r.json()),
      fetch("/api/ryder/bias?n=200").then(r => r.json()),
      fetch("/api/ryder/source-health").then(r => r.json()),
    ]);
    body.innerHTML = renderModelHealth(health, cal, bias, sources);
  } catch (e) {
    body.innerHTML = `<p class="error">Error: ${e.message}</p>`;
  }
}

function renderModelHealth(health, cal, bias, sources) {
  const statusColor = {
    excelente: "#22c55e", bueno: "#84cc16", aceptable: "#f59e0b",
    necesita_revision: "#ef4444", sin_datos: "#94a3b8",
  };
  const sc = statusColor[health.status] || "#94a3b8";

  // Header stats
  let html = `<div class="sr-summary">
    <div class="sr-stat"><span class="sr-big" style="color:${sc}">${health.accuracy_pct ?? "—"}</span><span class="sr-label">Accuracy</span></div>
    <div class="sr-stat"><span class="sr-big">${health.brier_score ?? "—"}</span><span class="sr-label">Brier Score</span></div>
    <div class="sr-stat"><span class="sr-big">${health.total_predictions ?? 0}</span><span class="sr-label">Predicciones</span></div>
    <div class="sr-stat"><span class="sr-big">${health.sample_size ?? 0}</span><span class="sr-label">Reviews</span></div>
  </div>
  <p class="muted small" style="margin:6px 0 16px">
    Estado: <strong style="color:${sc}">${health.status ?? "—"}</strong> ·
    vs random: <strong>${health.vs_random ?? "—"}</strong> ·
    Sin revisar: <strong>${health.unreviewed_count ?? 0}</strong>
  </p>`;

  // Calibration
  if (cal.status === "ok") {
    const calColor = { excelente: "#22c55e", buena: "#84cc16", aceptable: "#f59e0b", necesita_ajuste: "#ef4444" }[cal.calibration] || "#94a3b8";
    html += `<h3 class="sr-section">📐 Calibración (ECE: <span style="color:${calColor}">${cal.ece}</span> — ${cal.calibration})</h3>
    <p class="muted small">${cal.narrative}</p>`;

    if (cal.curve && cal.curve.length) {
      html += `<div class="mh-curve-wrap">`;
      for (const b of cal.curve) {
        const gap = b.gap;
        const barColor = Math.abs(gap) < 0.05 ? "#22c55e" : Math.abs(gap) < 0.10 ? "#f59e0b" : "#ef4444";
        const gapStr = gap > 0 ? `+${(gap*100).toFixed(0)}%` : `${(gap*100).toFixed(0)}%`;
        html += `<div class="mh-bucket" title="${b.bucket_low}-${b.bucket_high}%: predicho ${(b.predicted_avg*100).toFixed(0)}% real ${(b.actual_rate*100).toFixed(0)}%">
          <span class="mh-bucket-range">${b.bucket_low}–${b.bucket_high}%</span>
          <div class="mh-bucket-bar">
            <div class="mh-bucket-fill" style="width:${b.actual_rate*100}%;background:${barColor}"></div>
          </div>
          <span class="mh-bucket-gap" style="color:${barColor}">${gapStr}</span>
          <span class="mh-bucket-n muted">(${b.n})</span>
        </div>`;
      }
      html += `</div>`;
    }
  } else {
    html += `<h3 class="sr-section">📐 Calibración</h3><p class="muted small">${cal.message || "Sin datos"}</p>`;
  }

  // Bias
  html += `<h3 class="sr-section">🔍 Detección de Sesgos</h3>`;
  if (bias.status === "ok") {
    html += `<p class="muted small">${bias.narrative}</p>`;
    if (bias.biases && bias.biases.length) {
      for (const b of bias.biases) {
        const color = b.severity === "warning" ? "#f59e0b" : "#94a3b8";
        html += `<div class="mh-bias-item" style="border-left:3px solid ${color}">
          <strong style="color:${color}">${b.type}</strong>: ${b.message}
          ${b.fix ? `<div class="muted small">💡 ${b.fix}</div>` : ""}
        </div>`;
      }
    } else {
      html += `<p class="muted small" style="color:#22c55e">✅ Sin sesgos sistemáticos detectados.</p>`;
    }
    if (bias.insights && bias.insights.length) {
      for (const ins of bias.insights) {
        html += `<div class="mh-bias-item" style="border-left:3px solid #22c55e"><span class="muted small">ℹ️ ${ins.message}</span></div>`;
      }
    }
  } else {
    html += `<p class="muted small">${bias.message || "Sin datos suficientes."}</p>`;
  }

  // Source health
  html += `<h3 class="sr-section">🌐 Salud de Fuentes</h3>`;
  if (sources && Object.keys(sources).length) {
    for (const [src, info] of Object.entries(sources)) {
      const ok = info.last_status === "ok";
      const dot = ok ? "🟢" : "🔴";
      html += `<div class="mh-source-row">
        <span>${dot} <strong>${src}</strong></span>
        <span class="muted small">${info.uptime_24h}% uptime · ${info.avg_latency_ms|0}ms · ${info.checks_24h} checks</span>
      </div>`;
    }
  } else {
    html += `<p class="muted small">Sin datos de fuentes aún (se registran cada 15 min).</p>`;
  }

  html += `<p class="muted small" style="margin-top:14px;text-align:right">Calculado: ${(health.computed_at||"").slice(0,19).replace("T"," ")} UTC</p>`;
  return html;
}

function insightsHeader(m) {
  const ko = fmtKickoff(m.kickoffUtc);
  const meta = [
    m.league ? escapeHtml(m.league) : "",
    ko ? "🕒 " + escapeHtml(ko) : "",
    m.venue ? "📍 " + escapeHtml(m.venue) : "",
  ].filter(Boolean).join("  ·  ");
  const score = (m.homeScore != null && m.awayScore != null) ? `${m.homeScore} – ${m.awayScore}` : "vs";
  return `
    <div class="ins-teams">
      <div class="ins-team"><span class="ins-flag">${crest(m, "home", true)}</span><span class="nm">${escapeHtml(m.home)}</span></div>
      <div class="ins-vs">${score}</div>
      <div class="ins-team"><span class="ins-flag">${crest(m, "away", true)}</span><span class="nm">${escapeHtml(m.away)}</span></div>
    </div>
    <div class="ins-meta">${meta}</div>`;
}

function tile(label, big, sub) {
  return `<div class="tile"><div class="tile-label">${label}</div><div class="tile-big">${big}</div><div class="tile-sub">${sub || ""}</div></div>`;
}
function splitTile(label, m, h, a, none) {
  const hasNone = none != null;
  return `<div class="tile">
    <div class="tile-label">${label}</div>
    <div class="split">
      <div class="split-bar">
        <span class="h" style="width:${h}%"></span>
        ${hasNone ? `<span class="n" style="width:${none}%"></span>` : ""}
        <span class="a" style="width:${a}%"></span>
      </div>
      <div class="split-row">
        <span class="lh">${escapeHtml(m.home)} ${h}%</span>
        ${hasNone ? `<span class="muted">None ${none}%</span>` : ""}
        <span class="la">${escapeHtml(m.away)} ${a}%</span>
      </div>
    </div>
  </div>`;
}

function renderPostMatchReport(p, m) {
  const hs = m.homeScore ?? m.scoreHome ?? null;
  const as = m.awayScore ?? m.scoreAway ?? null;
  if (m.status !== 'Finished' || hs === null || as === null) return '';

  const hn = Number(hs), an = Number(as);
  const totalGoals = hn + an;

  // Determine actual result outcome
  const actualResult = hn > an ? 'home' : an > hn ? 'away' : 'draw';
  const predictedFav = p.favorite === m.home ? 'home' : p.favorite === m.away ? 'away' : 'draw';
  const favWon = actualResult === predictedFav;

  // Evaluate markets
  const btts = hn > 0 && an > 0;
  const over15 = totalGoals > 1;
  const over25 = totalGoals > 2;
  const over35 = totalGoals > 3;

  const bttsPred = p.btts >= 50;
  const over15Pred = (p.over15 || 0) >= 50;
  const over25Pred = (p.over25 || 0) >= 50;

  // Score accuracy
  const ps = p.predictedScore || {home: 0, away: 0};
  const exactScore = ps.home === hn && ps.away === an;

  // Build market rows
  const mkRow = (label, pred, actual, won) => {
    const icon = won ? '✓' : '✗';
    const cls  = won ? 'pmr-win' : 'pmr-loss';
    return `<div class="pmr-row ${cls}"><span class="pmr-icon">${icon}</span><span class="pmr-label">${label}</span><span class="pmr-actual">${actual}</span></div>`;
  };

  const probFav = predictedFav === 'home' ? p.prob.home : predictedFav === 'away' ? p.prob.away : p.prob.draw;
  const rows = [
    mkRow(
      `Favorito: <strong>${escapeHtml(p.favorite)}</strong> (${Math.round(probFav)}%)`,
      p.favorite,
      actualResult === 'home' ? escapeHtml(m.home) : actualResult === 'away' ? escapeHtml(m.away) : 'Empate',
      favWon
    ),
    mkRow(
      `Marcador exacto: <strong>${ps.home}-${ps.away}</strong>`,
      `${ps.home}-${ps.away}`,
      `${hn}-${an}`,
      exactScore
    ),
    mkRow(
      `Ambos anotan (${Math.round(p.btts)}% sí)`,
      bttsPred ? 'Sí' : 'No',
      btts ? 'Sí' : 'No',
      bttsPred === btts
    ),
    mkRow(
      `Más de 1.5 goles (${Math.round(p.over15 || 0)}%)`,
      over15Pred ? 'Sí' : 'No',
      over15 ? 'Sí' : 'No',
      over15Pred === over15
    ),
    mkRow(
      `Más de 2.5 goles (${Math.round(p.over25 || 0)}%)`,
      over25Pred ? 'Sí' : 'No',
      over25 ? 'Sí' : 'No',
      over25Pred === over25
    ),
  ];

  const wins = rows.filter(r => r.includes('pmr-win')).length;
  const total = rows.length;
  const pct = Math.round((wins / total) * 100);
  const scoreColor = pct >= 80 ? '#4ade80' : pct >= 60 ? '#facc15' : '#f87171';
  const scoreLabel = pct >= 80 ? 'Modelo muy acertado' : pct >= 60 ? 'Modelo bastante acertado' : pct >= 40 ? 'Modelo regular' : 'Modelo falló';

  return `
  <div class="pmr-block">
    <div class="pmr-header">
      <span class="pmr-title">Reporte Final del Modelo</span>
      <span class="pmr-score" style="color:${scoreColor}">${wins}/${total} — ${scoreLabel}</span>
    </div>
    <div class="pmr-result-line">
      <span class="pmr-ft-badge">FT</span>
      <span class="pmr-ft-score">${escapeHtml(m.home)} <strong>${hn} – ${an}</strong> ${escapeHtml(m.away)}</span>
    </div>
    <div class="pmr-rows">${rows.join('')}</div>
    <div class="pmr-accuracy-bar">
      <div class="pmr-accuracy-fill" style="width:${pct}%;background:${scoreColor}"></div>
    </div>
    <div class="pmr-accuracy-label" style="color:${scoreColor}">${pct}% acertividad del modelo</div>
  </div>`;
}

function renderInsights(p, m) {
  const ph = p.prob.home, pd = p.prob.draw, pa = p.prob.away;
  const sf = p.scoreFirst, fc = p.firstCorner, ec = p.expectedCorners, ecd = p.expectedCards, eg = p.expectedGoals;
  const ht = p.halfTime || {home: 0, draw: 0, away: 0};
  const cs = p.cleanSheet || {home: 0, away: 0};
  const dc = p.doubleChance || {home_draw: 0, draw_away: 0, home_away: 0};
  const topMax = p.topScores.length ? p.topScores[0].p : 1;

  // Recent form badges (shown when the DB has stored results for these teams)
  const fr = p.formRecord || {home: [], away: []};
  const hasFR = fr.home.length || fr.away.length;
  const formDot = (r) => `<span class="form-dot form-${r.toLowerCase()}">${r}</span>`;
  const formSection = hasFR ? `
    <div class="section-label">${t("recentForm")}</div>
    <div class="form-grid">
      <div class="form-side">${fr.home.map(formDot).join("")}<span class="form-name">${escapeHtml(m.home)}</span></div>
      <div class="form-side">${fr.away.map(formDot).join("")}<span class="form-name">${escapeHtml(m.away)}</span></div>
    </div>` : "";

  const postMatch = renderPostMatchReport(p, m);

  return `
  <div id="livePanelMount"></div>
  ${postMatch}
  ${formSection}
  <div class="verdict">
    <div class="verdict-score">${p.predictedScore.home} – ${p.predictedScore.away}</div>
    <div class="verdict-meta">
      <div class="verdict-label">${t("modelVerdict")}</div>
      <div class="verdict-fav">${t("favored", escapeHtml(p.favorite))}</div>
      <span class="conf-badge">${t("confidence", p.confidence)}</span>
    </div>
  </div>

  <div class="section-label" id="mainProbLabel">${t("resultProb")}</div>
  <div class="probbar">
    <div class="probseg home" id="mainProbSegH" style="width:${ph}%">${ph >= 12 ? Math.round(ph) + "%" : ""}</div>
    <div class="probseg draw" id="mainProbSegD" style="width:${pd}%">${pd >= 12 ? Math.round(pd) + "%" : ""}</div>
    <div class="probseg away" id="mainProbSegA" style="width:${pa}%">${pa >= 12 ? Math.round(pa) + "%" : ""}</div>
  </div>
  <div class="prob-legend" id="mainProbLegend">
    <span>🟢 ${escapeHtml(m.home)} ${pct(ph)}</span>
    <span>${t("draw")} ${pct(pd)}</span>
    <span>${escapeHtml(m.away)} ${pct(pa)} 🔵</span>
  </div>

  ${(()=>{
    const lo = p.liveOdds;
    if (!lo || lo.mkt_home == null) return "";
    const cn = lo.consensus || "low";
    const icon = cn === "high" ? "🟢" : cn === "medium" ? "🟡" : "🔴";
    const label = cn === "high"
      ? "Consenso alto — modelo y mercado coinciden"
      : cn === "medium"
      ? "Divergencia moderada — evalúa con cuidado"
      : "El mercado discrepa — Ryder puede estar equivocado";
    const fav = p.favorite;
    const isFavHome = fav === m.home;
    const modelFav = isFavHome ? ph : pa;
    const mktFav   = isFavHome ? lo.mkt_home : lo.mkt_away;
    const bkCount  = lo.bookmakers_count || 1;
    return `
    <div class="consensus-block consensus-${cn}">
      <div class="consensus-header">
        <span class="consensus-badge">${icon} ${label}</span>
        <span class="consensus-delta">Δ ${lo.delta}%</span>
      </div>
      <div class="consensus-row">
        <div class="consensus-col">
          <div class="consensus-col-label">🤖 Ryder (modelo)</div>
          <div class="consensus-col-val">${escapeHtml(fav)} ${pct(modelFav)}</div>
        </div>
        <div class="consensus-col">
          <div class="consensus-col-label">📊 Casas de apuestas (${bkCount})</div>
          <div class="consensus-col-val">${escapeHtml(fav)} ${pct(mktFav)}</div>
        </div>
      </div>
      ${lo.best_home ? `<div class="consensus-odds">Cuotas: 1 ${lo.best_home}  ·  X ${lo.best_draw}  ·  2 ${lo.best_away}</div>` : ""}
    </div>`;
  })()}

  <div class="section-label">${t("keyMarkets")}</div>
  <div class="tiles">
    ${splitTile(t("whoFirst"), m, sf.home, sf.away, sf.none)}
    ${splitTile(t("firstCorner"), m, fc.home, fc.away)}
    ${tile(t("xg"), `${eg.home} – ${eg.away}`, t("modelGoals"))}
    ${tile(t("xCorners"), `${ec.total}`, `${escapeHtml(m.home)} ${ec.home} · ${escapeHtml(m.away)} ${ec.away} <span class="est-badge">est.</span>`)}
    ${tile(t("btts"), pct(p.btts), p.btts >= 50 ? t("leanYes") : t("leanNo"))}
    ${tile(t("ou25"), pct(p.over25), t("underX", pct(p.under25)))}
  </div>

  <div class="section-label">${t("advMarkets")}</div>
  <div class="tiles">
    ${tile(t("over15"), pct(p.over15), t("underX", pct(+(100 - p.over15).toFixed(1))))}
    ${tile(t("over35"), pct(p.over35), t("underX", pct(+(100 - p.over35).toFixed(1))))}
    ${tile(t("csHome"), pct(cs.home), t("concedesNothing", escapeHtml(m.home)))}
    ${tile(t("csAway"), pct(cs.away), t("concedesNothing", escapeHtml(m.away)))}
    ${tile(t("dc1x"), pct(dc.home_draw), t("orDraw", escapeHtml(m.home)))}
    ${tile(t("dc12"), pct(dc.home_away), t("eitherWins"))}
  </div>

  <div class="section-label">${t("htLabel")}</div>
  <div class="probbar">
    <div class="probseg home" style="width:${ht.home}%">${ht.home >= 12 ? Math.round(ht.home) + "%" : ""}</div>
    <div class="probseg draw" style="width:${ht.draw}%">${ht.draw >= 12 ? Math.round(ht.draw) + "%" : ""}</div>
    <div class="probseg away" style="width:${ht.away}%">${ht.away >= 12 ? Math.round(ht.away) + "%" : ""}</div>
  </div>
  <div class="prob-legend">
    <span>🟢 ${escapeHtml(m.home)} ${pct(ht.home)}</span>
    <span>${t("draw")} ${pct(ht.draw)}</span>
    <span>${escapeHtml(m.away)} ${pct(ht.away)} 🔵</span>
  </div>

  ${(() => {
    const bh = p.byHalves;
    if (!bh) return '';
    const fh = bh.firstHalf, sh = bh.secondHalf;
    const labels = bh.goals15Labels || ["0-15","15-30","30-45","45-60","60-75","75-90"];
    const all15  = bh.goals15All || [];
    const maxG   = all15.length ? Math.max(...all15) : 1;
    const barW   = v => Math.max(4, Math.round(v / maxG * 100));
    const homeN  = escapeHtml(m.home), awayN = escapeHtml(m.away);

    const halfBlock = (half, label, isFirst) => {
      const g15 = half.goals15 || [];
      const c15 = half.corners15 || [];
      const k15 = half.cards15 || [];
      const g15lbl = isFirst ? labels.slice(0,3) : labels.slice(3);
      const ec = half.expCorners || {};
      const ek = half.expCards || {};

      const barsHtml = g15.map((g, i) => {
        const isBreak = (i === 2);
        return `<div class="bh-bar-row${isBreak ? ' bh-break-bar' : ''}">
          <span class="bh-bar-lbl">${g15lbl[i]}'</span>
          <div class="bh-bar-wrap">
            <div class="bh-bar-track"><div class="bh-bar-fill bh-fill-goal" style="width:${barW(g)}%"></div></div>
            <span class="bh-bar-val">${g.toFixed(2)}</span>
          </div>
          <div class="bh-bar-wrap">
            <div class="bh-bar-track"><div class="bh-bar-fill bh-fill-corner" style="width:${barW(c15[i]||0)}%"></div></div>
            <span class="bh-bar-val">${(c15[i]||0).toFixed(1)}</span>
          </div>
          <div class="bh-bar-wrap">
            <div class="bh-bar-track"><div class="bh-bar-fill bh-fill-card" style="width:${barW((k15[i]||0)*5)}%"></div></div>
            <span class="bh-bar-val">${(k15[i]||0).toFixed(2)}</span>
          </div>
          ${isBreak ? `<span class="bh-break-tag">pausa ~${half.hydBreakMin}'</span>` : ''}
        </div>`;
      }).join('');

      const htRow = isFirst && half.htResult ? `
        <div class="bh-ht-row">
          <span class="bh-ht-label">Al descanso</span>
          <span class="bh-ht-seg bh-seg-h">${homeN} ${half.htResult.home}%</span>
          <span class="bh-ht-sep">·</span>
          <span class="bh-ht-seg bh-seg-d">X ${half.htResult.draw}%</span>
          <span class="bh-ht-sep">·</span>
          <span class="bh-ht-seg bh-seg-a">${awayN} ${half.htResult.away}%</span>
        </div>` : '';

      return `<div class="bh-half">
        <div class="bh-half-title">${label}</div>
        <div class="bh-stats-grid">
          <div class="bh-stat"><span class="bh-stat-lbl">xG total</span><span class="bh-stat-val">${half.expGoals}</span></div>
          <div class="bh-stat"><span class="bh-stat-lbl">${homeN}</span><span class="bh-stat-val">${half.expHome}</span></div>
          <div class="bh-stat"><span class="bh-stat-lbl">${awayN}</span><span class="bh-stat-val">${half.expAway}</span></div>
          <div class="bh-stat"><span class="bh-stat-lbl">P(gol)</span><span class="bh-stat-val bh-pct-g">${half.over05}%</span></div>
          <div class="bh-stat"><span class="bh-stat-lbl">+1.5G</span><span class="bh-stat-val">${half.over15||'—'}%</span></div>
          <div class="bh-stat"><span class="bh-stat-lbl">BTTS</span><span class="bh-stat-val">${half.btts||'—'}%</span></div>
        </div>
        <div class="bh-market-row">
          <div class="bh-market">
            <span class="bh-mkt-icon">⛳</span>
            <div class="bh-mkt-body">
              <span class="bh-mkt-label">Córners esperados</span>
              <span class="bh-mkt-total">${ec.total||'—'}</span>
              <span class="bh-mkt-sub">${homeN} ${ec.home||'—'} · ${awayN} ${ec.away||'—'}</span>
            </div>
          </div>
          <div class="bh-market">
            <span class="bh-mkt-icon">🟨</span>
            <div class="bh-mkt-body">
              <span class="bh-mkt-label">Tarjetas esperadas</span>
              <span class="bh-mkt-total">${ek.total||'—'}</span>
              <span class="bh-mkt-sub">${homeN} ${ek.home||'—'} · ${awayN} ${ek.away||'—'}</span>
            </div>
          </div>
        </div>
        <div class="bh-score1st">
          Marca primero: <strong>${homeN} ${half.scoreFirst ? half.scoreFirst.home : '—'}%</strong> · <strong>${awayN} ${half.scoreFirst ? half.scoreFirst.away : '—'}%</strong>
        </div>
        ${htRow}
        <div class="bh-bars-header">
          <span class="bh-bh-tramo">Tramo</span>
          <span class="bh-bh-col">xGoles</span>
          <span class="bh-bh-col">Córners</span>
          <span class="bh-bh-col">Tarjetas</span>
        </div>
        <div class="bh-bars">${barsHtml}</div>
        <div class="bh-break-info">
          Pausa hidratación ~${half.hydBreakMin}' · P(gol en 10 min post-pausa): <strong>${half.pGoalPostBreak}%</strong>
        </div>
      </div>`;
    };

    return `<div class="section-label">Análisis por tiempos — WC 2026</div>
  <div class="bh-container">
    ${halfBlock(fh, "1er Tiempo  (0'–45')", true)}
    <div class="bh-divider"></div>
    ${halfBlock(sh, "2do Tiempo  (45'–90')", false)}
  </div>`;
  })()}

  <div class="section-label">${t("scorelines")}</div>
  <div class="scorelines">
    ${p.topScores.map((s) => `
      <div class="sl-row">
        <span class="sl-label">${s.h}–${s.a}</span>
        <span class="sl-bar"><span class="sl-fill" style="width:${Math.round(s.p / topMax * 100)}%"></span></span>
        <span class="sl-pct">${s.p}%</span>
      </div>`).join("")}
  </div>

  <div class="section-label">${t("bestBets")} <span class="read-free-badge">${t("freeBadge")}</span></div>
  ${(() => {
    const c = buildCombos(p, m);
    return `
  <div class="doradobet-warn">⚠️ <strong>DoradoBet:</strong> ${state.lang==='es'
    ? 'No puedes combinar varias apuestas del mismo partido. Usa estas picks <strong>individualmente</strong> o combínalas con picks de <strong>otros partidos</strong> en el cupón múltiple.'
    : 'You cannot combine multiple bets from the same match. Use these picks <strong>individually</strong> or combine with picks from <strong>other matches</strong>.'}</div>
  <div class="combo-grid">
    ${comboCard(t("secureCombo"), "🛡️", "secure", c.secure)}
    ${comboCard(t("riskyCombo"), "🔥", "risky", c.risky)}
  </div>
  <div class="combo-longshot">
    🎲 <strong>${t("longshotLabel")}</strong> ${escapeHtml(c.longshot.label)} — ${c.longshot.prob}% (${t("fairOdds", (100 / c.longshot.prob).toFixed(1))})
  </div>
  <div class="bet-disclaimer">${t("betDisclaimer")}</div>`;
  })()}

  <div class="section-label">${t("quickRead")} <span class="read-free-badge">${t("freeBadge")}</span></div>
  <div class="local-read">
    ${localRead(p, m).map(r => `
      <div class="read-row">
        <span class="read-icon">${r.icon}</span>
        <div><span class="read-title">${r.title}:</span> ${r.text}</div>
      </div>`).join("")}
  </div>

  ${(() => {
    const c = buildCombos(p, m);
    if (!c.top3 || !c.top3.legs.length) return '';
    const t3Odds = c.top3.combined  > 0 ? (100 / c.top3.combined).toFixed(2)  : '—';
    const r5Odds = c.risky5.combined > 0 ? (100 / c.risky5.combined).toFixed(2) : '—';
    return `
  <div class="section-label">🎯 Picks combinables mismo partido <span class="est-badge">mercados estimados</span> <span class="read-free-badge">${t('freeBadge')}</span></div>
  <div class="alt-combos-wrap">
    <div class="alt-combo-card alt-secure">
      <div class="alt-combo-head">🛡️ <strong>3 más seguras</strong> <span class="alt-combo-pct">~${c.top3.combined}%</span> <span class="alt-combo-odds">~${t3Odds}x</span></div>
      <div class="alt-combo-note">Mismo partido · DoradoBet → <strong>Crear Apuesta</strong></div>
      ${c.top3.legs.map(l => `
        <div class="alt-combo-leg">
          <span class="alt-leg-label">${escapeHtml(l.label)}</span>
          <span class="alt-leg-prob">${l.prob}%</span>
        </div>`).join('')}
    </div>
    <div class="alt-combo-card alt-parlay">
      <div class="alt-combo-head">⚡ <strong>Risky — 5 picks seguros distintos</strong> <span class="alt-combo-pct">~${c.risky5.combined}%</span> <span class="alt-combo-odds">~${r5Odds}x</span></div>
      <div class="alt-combo-note">Distintos a los 3 anteriores · <strong>Crear Apuesta</strong> en DoradoBet</div>
      ${c.risky5.legs.map(l => `
        <div class="alt-combo-leg">
          <span class="alt-leg-label">${escapeHtml(l.label)}</span>
          <span class="alt-leg-prob">${l.prob}%</span>
        </div>`).join('')}
    </div>
  </div>`;
  })()}

  <div id="councilPanelMount" class="council-panel-wrap"></div>

  <div class="scout-agent-out" id="deepdiveOut">
    <div class="scout-agent-loading">
      <span class="scout-spinner">⚽</span>
      <span class="muted small">Scout analizando con modelo Dixon-Coles + IA…</span>
    </div>
  </div>

  <div class="model-note">
    <strong>${t("modelNote1")}</strong> ${escapeHtml(p.model)} (Elo ${p.homeElo} vs ${p.awayElo}${p.homeAdvantage ? t("inclHomeEdge") : ""} · ρ=-0.13).
    ${t("modelNoteCards", ecd.total, escapeHtml(m.home), ecd.home, escapeHtml(m.away), ecd.away)}
  </div>

  <div class="live-auto-panel" id="liveWidgetWrap">
    <div class="lap-header">
      <span class="live-dot-pulse"></span>
      <span class="lap-title">Seguimiento EN VIVO</span>
      <span id="lw_status_badge" class="lw-status-badge">⏰ Cargando…</span>
    </div>
    <div class="lap-body" id="lapBody">
      <div class="lap-loading">Obteniendo datos en vivo…</div>
    </div>
  </div>
`;
}

// ---------- auto-sync score from API ----------
let _liveScoreInterval = null;
async function syncLiveScore(home, away) {
  const badge  = document.getElementById('lw_status_badge');
  const body   = document.getElementById('lapBody');
  if (!body) return;
  try {
    const r = await fetch(`/api/livematch-score?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`);
    const d = await r.json();
    if (!d.found) {
      body.innerHTML = '<div class="lap-not-found">Sin datos en vivo disponibles aún</div>';
      return;
    }
    const isLive = ['live','halftime','extra_time','1H','2H','in'].includes(d.status);
    const isFin  = ['finished','post','FT','completed'].includes(d.status);
    const hs = d.scoreHome ?? 0;
    const as_ = d.scoreAway ?? 0;
    const minVal = d.minuteNum ?? (isLive ? 45 : (isFin ? 90 : 0));

    if (badge) {
      badge.textContent = isFin ? '✓ FINALIZADO' : isLive ? '🔴 EN VIVO' : '⏰ PROGRAMADO';
      badge.className = 'lw-status-badge ' + (isFin ? 'badge-fin' : isLive ? 'badge-live' : 'badge-sched');
    }

    // auto-fetch model recalculation
    if (isLive || isFin) {
      try {
        const neutral = 1;
        const lr = await fetch(`/api/live?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}&minute=${minVal}&hs=${hs}&as=${as_}&neutral=${neutral}`);
        const ld = await lr.json();
        if (!ld.error) {
          const pb = ld.prob || {}, ng = ld.nextGoal || {}, rem = ld.remGoals || {};
          const ph = pb.home||0, pd = pb.draw||0, pa = pb.away||0;
          body.innerHTML = `
            <div class="lap-score">
              <span class="lap-team">${escapeHtml(home)}</span>
              <span class="lap-goals">${hs}</span>
              <span class="lap-sep">${isLive?'<span class="lap-live-dot"></span>':''} – </span>
              <span class="lap-goals">${as_}</span>
              <span class="lap-team">${escapeHtml(away)}</span>
            </div>
            <div class="lap-prob-bar-wrap">
              <div class="lap-prob-bar">
                <div style="width:${ph}%;background:#22c55e;height:100%;border-radius:3px 0 0 3px"></div>
                <div style="width:${pd}%;background:#475569;height:100%"></div>
                <div style="width:${pa}%;background:#3b82f6;height:100%;border-radius:0 3px 3px 0"></div>
              </div>
              <div class="lap-prob-labels">
                <span style="color:#22c55e">${escapeHtml(home)} ${ph}%</span>
                <span style="color:#94a3b8">Empate ${pd}%</span>
                <span style="color:#60a5fa">${escapeHtml(away)} ${pa}%</span>
              </div>
            </div>
            <div class="lap-ng-row">
              <div class="lap-ng-cell ng-h"><div class="lap-ng-lbl">${escapeHtml(home)}</div><div class="lap-ng-pct">${ng.home}%</div></div>
              <div class="lap-ng-cell ng-n"><div class="lap-ng-lbl">Sin gol</div><div class="lap-ng-pct">${ng.none}%</div></div>
              <div class="lap-ng-cell ng-a"><div class="lap-ng-lbl">${escapeHtml(away)}</div><div class="lap-ng-pct">${ng.away}%</div></div>
            </div>
            <div class="lap-rows">
              <div class="lap-row"><span>xG restante</span><span>${escapeHtml(home)} ${rem.home} · ${escapeHtml(away)} ${rem.away}</span></div>
              <div class="lap-row"><span>+2.5 goles (resto)</span><span>${ld.liveOver25}%</span></div>
              <div class="lap-row"><span>Ambos anotan</span><span>${ld.liveBtts}%</span></div>
              <div class="lap-row"><span>Marcadores probables</span><span>${(ld.topScores||[]).slice(0,3).map(s=>`${s.h}-${s.a}(${s.p}%)`).join(' · ')}</span></div>
              ${ld.expectedCorners ? `
              <div class="lap-row lap-row-sep lap-row-compare" id="lapRowCorners">
                <span>🚩 Córneres</span>
                <div class="lap-compare-wrap">
                  <span class="lap-compare-exp">Esp. ${ld.expectedCorners.total} <span class="est-badge">est.</span></span>
                  <span class="lap-live-stat" id="lc_corners_live"></span>
                  <span class="lap-compare-status" id="lcs_corners"></span>
                </div>
              </div>` : ''}
              ${ld.expectedCards ? `
              <div class="lap-row lap-row-compare" id="lapRowCards">
                <span>🟨 Tarjetas</span>
                <div class="lap-compare-wrap">
                  <span class="lap-compare-exp">Esp. ${ld.expectedCards.total} <span class="est-badge">est.</span></span>
                  <span class="lap-live-stat" id="lc_cards_live"></span>
                  <span class="lap-compare-status" id="lcs_cards"></span>
                </div>
              </div>` : ''}
              ${ld.expectedCorners || ld.expectedCards ? `
              <div class="lap-row" id="lapRowPoss" style="display:none">
                <span>⚽ Posesión</span><span id="lc_poss_live" style="color:#f8fafc;font-weight:600"></span>
              </div>
              <div class="lap-row" id="lapRowShots" style="display:none">
                <span>🎯 Tiros al arco</span><span id="lc_shots_live" style="color:#f8fafc;font-weight:600"></span>
              </div>` : ''}
            </div>`;
        }
          // fetch ESPN live stats (corners, cards, possession, shots)
          try {
            const er = await fetch(`/api/espn-stats?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}`);
            const es = await er.json();
            if (es.found) {
              // corners
              const cornEl = document.getElementById('lc_corners_live');
              const cornSt = document.getElementById('lcs_corners');
              if (cornEl && es.totalCorners != null) {
                const expC = ld.expectedCorners?.total || 0;
                cornEl.textContent = `Real: ${es.homeCorners ?? 0} – ${es.awayCorners ?? 0} (Total ${es.totalCorners})`;
                if (cornSt) updateLapCompareAuto(cornSt, expC, es.totalCorners);
              }
              // cards
              const cardEl = document.getElementById('lc_cards_live');
              const cardSt = document.getElementById('lcs_cards');
              if (cardEl && es.totalYellow != null) {
                const expK = ld.expectedCards?.total || 0;
                const totalCards = (es.totalYellow || 0) + (es.totalRed || 0);
                cardEl.textContent = `🟨 ${es.homeYellow ?? 0}+${es.awayYellow ?? 0}${(es.homeRed||0)+(es.awayRed||0)>0 ? ` 🟥 ${es.homeRed??0}+${es.awayRed??0}` : ''}`;
                if (cardSt) updateLapCompareAuto(cardSt, expK, totalCards);
              }
              // possession
              const possEl = document.getElementById('lc_poss_live');
              const possRow = document.getElementById('lapRowPoss');
              if (possEl && es.homePossession != null) {
                possEl.textContent = `${escapeHtml(home)} ${es.homePossession}% · ${escapeHtml(away)} ${es.awayPossession}%`;
                if (possRow) possRow.style.display = '';
              }
              // shots on target
              const shotsEl = document.getElementById('lc_shots_live');
              const shotsRow = document.getElementById('lapRowShots');
              if (shotsEl && es.homeShotsOn != null) {
                shotsEl.textContent = `${escapeHtml(home)} ${es.homeShotsOn} · ${escapeHtml(away)} ${es.awayShotsOn}`;
                if (shotsRow) shotsRow.style.display = '';
              }
            }
          } catch(_) { /* ESPN non-blocking */ }
      } catch(e2) { /* model error silent */ }
    } else {
      body.innerHTML = `<div class="lap-not-found">El partido aún no comenzó. El modelo recalculará automáticamente al iniciar.</div>`;
    }

    if (_liveScoreInterval) clearInterval(_liveScoreInterval);
    if (isLive) _liveScoreInterval = setInterval(() => syncLiveScore(home, away), 60000);
  } catch(e) { body.innerHTML = '<div class="lap-not-found">Sin datos disponibles</div>'; }
}

function updateLapCompare(type, expected, rawVal) {
  const actual = parseFloat(rawVal);
  const el = document.getElementById('lcs_' + type);
  if (!el) return;
  if (rawVal === '' || isNaN(actual)) { el.textContent = ''; el.className = 'lap-compare-status'; return; }
  const diff = actual - expected;
  const pct = expected > 0 ? Math.round(Math.abs(diff) / expected * 100) : 0;
  if (Math.abs(diff) < 0.5) {
    el.textContent = '≈ En línea';
    el.className = 'lap-compare-status lcs-ok';
  } else if (diff > 0) {
    el.textContent = `▲ +${diff.toFixed(1)} sobre lo esperado (${pct}%)`;
    el.className = 'lap-compare-status lcs-over';
  } else {
    el.textContent = `▼ ${diff.toFixed(1)} bajo lo esperado (${pct}%)`;
    el.className = 'lap-compare-status lcs-under';
  }
}

function updateLapCompareAuto(el, expected, actual) {
  if (el == null) return;
  if (actual == null || isNaN(actual)) { el.textContent = ''; el.className = 'lap-compare-status'; return; }
  const diff = actual - expected;
  const pct = expected > 0 ? Math.round(Math.abs(diff) / expected * 100) : 0;
  if (Math.abs(diff) < 0.5) {
    el.textContent = '≈ En línea';
    el.className = 'lap-compare-status lcs-ok';
  } else if (diff > 0) {
    el.textContent = `▲ +${diff.toFixed(1)} sobre lo esperado (${pct}%)`;
    el.className = 'lap-compare-status lcs-over';
  } else {
    el.textContent = `▼ ${diff.toFixed(1)} bajo lo esperado (${pct}%)`;
    el.className = 'lap-compare-status lcs-under';
  }
}

// ---------- live stats widget ----------
async function runLiveWidget(home, away, homeAdvantage) {
  const out = $('lw_out');
  if (!out) return;
  const min  = parseInt($('lw_min')?.value  || '0', 10);
  const hs   = parseInt($('lw_hs')?.value   || '0', 10);
  const as_  = parseInt($('lw_as')?.value   || '0', 10);
  const poss = parseFloat($('lw_poss')?.value || '');
  const neutral = !homeAdvantage;
  out.innerHTML = '<span class="muted small">⚡ Calculando…</span>';
  try {
    const url = `/api/live?home=${encodeURIComponent(home)}&away=${encodeURIComponent(away)}&minute=${min}&hs=${hs}&as=${as_}&neutral=${neutral ? 1 : 0}`;
    const r = await fetch(url);
    const d = await r.json();
    if (d.error) { out.innerHTML = `<span class="warn">${escapeHtml(d.error)}</span>`; return; }
    const pb = d.prob || {};
    const ng = d.nextGoal || {};
    const rem = d.remGoals || {};
    const possLine = (!isNaN(poss) && poss > 0)
      ? `<div class="lw-stat"><span class="lw-label">Posesión</span><span class="lw-val">${poss}% ${home} / ${100 - poss}% ${away}</span></div>`
      : '';
    const ph = pb.home || 0, pd2 = pb.draw || 0, pa = pb.away || 0;
    out.innerHTML = `
      <div class="lw-result">
        <div class="lw-header">🔴 MIN ${min}′ &nbsp;·&nbsp; ${escapeHtml(home)} ${hs} – ${as_} ${escapeHtml(away)}</div>

        <div class="lw-prob-bar-wrap">
          <div class="lw-prob-bar-track">
            <div class="lw-prob-bar-h" style="width:${ph}%"></div>
            <div class="lw-prob-bar-d" style="width:${pd2}%"></div>
            <div class="lw-prob-bar-a" style="width:${pa}%"></div>
          </div>
          <div class="lw-prob-bar-labels">
            <span class="lh">${escapeHtml(home)} ${ph}%</span>
            <span class="ld">Empate ${pd2}%</span>
            <span class="la">${escapeHtml(away)} ${pa}%</span>
          </div>
        </div>

        <div style="font-size:10px;color:var(--muted);margin-bottom:6px;font-weight:700;">PRÓXIMO GOL</div>
        <div class="lw-next-goal">
          <div class="lw-ng-item ng-h"><span class="lw-prob-label">${escapeHtml(home)}</span><span class="lw-ng-pct">${ng.home}%</span></div>
          <div class="lw-ng-item ng-n"><span class="lw-prob-label">Sin gol</span><span class="lw-ng-pct">${ng.none}%</span></div>
          <div class="lw-ng-item ng-a"><span class="lw-prob-label">${escapeHtml(away)}</span><span class="lw-ng-pct">${ng.away}%</span></div>
        </div>

        <div class="lw-stats">
          <div class="lw-stat"><span class="lw-label">xG restante</span><span class="lw-val">${escapeHtml(home)} ${rem.home} · ${escapeHtml(away)} ${rem.away}</span></div>
          <div class="lw-stat"><span class="lw-label">+2.5 goles (resto)</span><span class="lw-val">${d.liveOver25}%</span></div>
          <div class="lw-stat"><span class="lw-label">Ambos anotan</span><span class="lw-val">${d.liveBtts}%</span></div>
          ${possLine}
          <div class="lw-stat"><span class="lw-label">Marcadores finales probables</span><span class="lw-val">${(d.topScores || []).slice(0,3).map(s => `${s.h}-${s.a} (${s.p}%)`).join(' · ')}</span></div>
        </div>
      </div>`;
  } catch(e) {
    out.innerHTML = `<span class="warn">⚠️ ${escapeHtml(String(e))}</span>`;
  }
}

// ---------- deep-dive prompt builder ----------
function buildDeepDivePrompt(m, p) {
  const fr = p.formRecord || {home: [], away: []};
  const formLine = (fr.home.length || fr.away.length)
    ? `\n- Recent form — ${m.home}: ${fr.home.join(" ") || "no data"}, ${m.away}: ${fr.away.join(" ") || "no data"}`
    : "";
  return `Análisis completo de ${m.home} vs ${m.away}${m.league ? " (" + m.league + ")" : ""}.

Mi modelo estadístico estima:
- Resultado: ${m.home} ${p.prob.home}% / Empate ${p.prob.draw}% / ${m.away} ${p.prob.away}%
- xG: ${m.home} ${p.expectedGoals.home}, ${m.away} ${p.expectedGoals.away}; marcador más probable ${p.predictedScore.home}-${p.predictedScore.away}
- Marca primero: ${m.home} ${p.scoreFirst.home}%, ${m.away} ${p.scoreFirst.away}%
- Primer córner: ${m.home} ${p.firstCorner.home}%, ${m.away} ${p.firstCorner.away}%; total esperado ${p.expectedCorners.total}
- Ambos marcan ${p.btts}% | +1.5 goles ${p.over15}% | +2.5 goles ${p.over25}% | +3.5 goles ${p.over35}%
- Portería en cero: ${m.home} ${(p.cleanSheet||{}).home||0}%, ${m.away} ${(p.cleanSheet||{}).away||0}%
- Doble oportunidad 1X ${(p.doubleChance||{}).home_draw||0}% | 12 ${(p.doubleChance||{}).home_away||0}%
- Medio tiempo: ${m.home} ${(p.halfTime||{}).home||0}% / Empate ${(p.halfTime||{}).draw||0}% / ${m.away} ${(p.halfTime||{}).away||0}%
- Tarjetas esperadas: ${p.expectedCards.total}${formLine}

Por favor incluye:
1. **Análisis táctico**: batalla táctica clave, 2-3 jugadores a seguir, dónde puede fallar el modelo.
2. **📋 Apuestas recomendadas**: 1X2 con confianza %, Más/Menos goles, Ambos marcan, apuesta de valor si existe, y si hay múltiples partidos hoy una sugerencia de parlay/acumulador.
3. Tu confianza general 1-10.
Separa hechos de opiniones. ⚠️ Recuerda: el usuario realiza sus propias apuestas.${getRecentResultsContext()}`;
}

// ---------- Claude.ai paste fallback ----------
// Store the latest prompt so the copy button can reach it without inline JS quoting issues
let _fallbackPrompt = "";
function claudeAiFallback(prompt, errMsg) {
  _fallbackPrompt = prompt;
  const errBlock = errMsg
    ? `<p style="color:var(--warn);font-size:13px;margin:0 0 10px">⚠️ ${escapeHtml(errMsg)}</p>`
    : `<p style="font-size:13px;color:var(--muted);margin:0 0 10px">${t("ddNoKeyIntro")}</p>`;
  return `<div class="claude-fallback">
    ${errBlock}
    <p class="fallback-hint">${t("ddFallbackHint")}</p>
    <textarea class="prompt-area" readonly onclick="this.select()">${escapeHtml(prompt)}</textarea>
    <div class="fallback-actions">
      <button class="copy-prompt-btn" id="copyPromptBtn">${t("copyPrompt")}</button>
      <a href="https://claude.ai/new" target="_blank" rel="noopener" class="open-claude-btn">${t("openClaude")}</a>
    </div>
  </div>`;
}
// Wire up the copy button after HTML is injected (called from runDeepDive / openInsights)
function _wireCopyBtn() {
  const btn = document.getElementById("copyPromptBtn");
  if (!btn) return;
  btn.onclick = () => {
    if (navigator.clipboard) {
      navigator.clipboard.writeText(_fallbackPrompt).then(() => {
        btn.textContent = t("copied");
        setTimeout(() => { btn.textContent = t("copyPrompt"); }, 2000);
      });
    } else {
      // Fallback: select the textarea
      const ta = btn.closest(".claude-fallback")?.querySelector(".prompt-area");
      if (ta) { ta.select(); document.execCommand("copy"); }
    }
  };
}

// ---------- deep-dive runner ----------
async function _localScoutFallback(m, out) {
  try {
    const lr = await fetch(`/api/local-scout?home=${encodeURIComponent(m.home)}&away=${encodeURIComponent(m.away)}`);
    const ld = await lr.json();
    if (ld.reply) {
      out.innerHTML = `<div class="scout-local-badge">🔌 Scout Local · sin API</div>` + renderMarkdown(ld.reply);
      return true;
    }
  } catch (_) {}
  return false;
}


// ── Panel del Consejo Ryder × Cleo × Lucas ────────────────────────────────
async function fetchCouncilPanel(m) {
  const mount = $("councilPanelMount");
  if (!mount) return;
  mount.innerHTML = `<div class="council-loading"><span class="council-spinner">🎲</span><span class="muted small">Ryder × Cleo × Lucas analizando…</span></div>`;
  try {
    const url = `/api/council?home=${encodeURIComponent(m.home)}&away=${encodeURIComponent(m.away)}&n=1000`;
    const res  = await fetch(url);
    const data = await res.json();
    if (data.error) { mount.innerHTML = ""; return; }
    mount.innerHTML = renderCouncilPanel(data, m);
  } catch(e) {
    mount.innerHTML = "";
  }
}

function renderCouncilPanel(d, m) {
  const r = d.ryder, l = d.lucas, c = d.consensus;
  const ops = (d.cleo && d.cleo.opportunities) || [];

  const bar = (ph, pd, pa, label) => `
    <div class="council-agent-label">${label}</div>
    <div class="council-bar">
      <div class="council-seg council-h" style="width:${ph}%">${ph >= 10 ? Math.round(ph)+"%" : ""}</div>
      <div class="council-seg council-d" style="width:${pd}%">${pd >= 10 ? Math.round(pd)+"%" : ""}</div>
      <div class="council-seg council-a" style="width:${pa}%">${pa >= 10 ? Math.round(pa)+"%" : ""}</div>
    </div>`;

  const topScores = (l.top_scorelines || []).slice(0,3).map(([sc, pct]) =>
    `<span class="council-score-tag">${escapeHtml(sc)} <em>${pct}%</em></span>`
  ).join("");

  const bestPick = c.ph >= c.pa && c.ph >= c.pd ? `[1] ${escapeHtml(m.home)}`
                 : c.pa > c.ph && c.pa >= c.pd ? `[2] ${escapeHtml(m.away)}`
                 : `[X] Empate`;
  const bestConf = Math.max(c.ph, c.pd, c.pa);
  const confClass = bestConf >= 65 ? "council-conf-high" : bestConf >= 52 ? "council-conf-mid" : "council-conf-low";

  const cleoHtml = ops.length ? `
    <div class="council-cleo-ops">
      <span class="council-cleo-label">📊 Cleo detectó:</span>
      ${ops.map(op => `<span class="council-op-tag">${escapeHtml(op.platform||"")}: EV ${op.ev_pct > 0 ? "+" : ""}${(op.ev_pct||0).toFixed(1)}%</span>`).join("")}
    </div>` : "";

  return `
  <div class="council-panel">
    <div class="council-header">
      <span class="council-title">⚖️ Consejo — Ryder × Cleo × Lucas</span>
      <span class="council-badge ${confClass}">${bestPick} · ${Math.round(bestConf)}%</span>
    </div>
    <div class="council-legend">
      <span>🟢 ${escapeHtml(m.home)}</span><span>⬜ X</span><span>🔵 ${escapeHtml(m.away)}</span>
    </div>
    ${bar(r.ph, r.pd, r.pa, "📐 Ryder (Dixon-Coles + Elo)")}
    ${bar(l.ph, l.pd, l.pa, `🎲 Lucas (${(l.n||1000).toLocaleString()} simulaciones MC)`)}
    ${bar(c.ph, c.pd, c.pa, "🤝 Consenso (40% Ryder + 60% Lucas)")}
    ${topScores ? `<div class="council-scores-row"><span class="council-scores-label">Marcadores:</span>${topScores}</div>` : ""}
    ${cleoHtml}
  </div>`;
}

async function runDeepDive(m, p) {
  const out = $("deepdiveOut");
  if (!out) return;
  const prompt = buildDeepDivePrompt(m, p);
  out.innerHTML = `<div class="scout-agent-loading"><span class="scout-spinner">⚽</span><span class="muted small">${t("analyzing")}</span></div>`;
  const ctrl = new AbortController();
  const timer = setTimeout(() => ctrl.abort(), 18000);
  try {
    const res = await fetch("/api/chat", {
      method: "POST", headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: prompt, history: [], matches: state.matches, date: state.date, lang: state.lang }),
      signal: ctrl.signal,
    });
    clearTimeout(timer);
    const data = await res.json();
    if (data.error) {
      const ok = await _localScoutFallback(m, out);
      if (!ok) out.innerHTML = `<p class="muted">⚠️ ${escapeHtml(data.error)}</p>`;
    } else {
      out.innerHTML = renderMarkdown(data.reply || "");
    }
  } catch (e) {
    clearTimeout(timer);
    // Timeout or network error — use local scout
    const ok = await _localScoutFallback(m, out);
    if (!ok) out.innerHTML = `<p class="muted">⚠️ ${escapeHtml(String(e))}</p>`;
  }
}

// ---------- best bets (model combos) ----------
// Markets DoradoBet (and most bookmakers) CANNOT combine with other same-match bets:
// first_corner, first_scorer, first_card, anytime_scorer (as same-match combos).
// We ONLY use fully combinable markets below.
function buildCombos(p, m) {
  const isHomeFav = p.favorite === m.home;
  const fav = p.favorite;
  const dog = isHomeFav ? m.away : m.home;
  const dc = p.doubleChance || {};
  const cs = p.cleanSheet || {};
  const wtn = p.winToNil || {};
  const ht = p.halfTime || {};

  const favWin   = +(isHomeFav ? p.prob.home : p.prob.away).toFixed(1);
  const dogWin   = +(isHomeFav ? p.prob.away : p.prob.home).toFixed(1);
  const favDC    = +(isHomeFav ? dc.home_draw : dc.draw_away).toFixed(1);
  const favHT    = +(isHomeFav ? ht.home : ht.away).toFixed(1);
  const drawHT   = +ht.draw.toFixed(1);
  const favWTN   = +(isHomeFav ? wtn.home : wtn.away).toFixed(1);
  const favScores= +(100 - (isHomeFav ? cs.away : cs.home)).toFixed(1);
  const dogScores= +(100 - (isHomeFav ? cs.home : cs.away)).toFixed(1);
  const noBtts   = +(100 - p.btts).toFixed(1);
  const under25  = +(100 - p.over25).toFixed(1);
  const under35  = +(100 - p.over35).toFixed(1);

  const pickLegs = (pool, n) => {
    const out = [], used = new Set();
    for (const leg of pool.slice().sort((a, b) => b.prob - a.prob)) {
      if (used.has(leg.market)) continue;
      used.add(leg.market);
      out.push(leg);
      if (out.length === n) break;
    }
    return out;
  };
  const combined = (legs) => +(legs.reduce((acc, l) => acc * l.prob / 100, 100)).toFixed(1);

  // ── SECURE (3 patas) — mercados principales primero, córners solo si no alcanza ──
  // Prioridad: DC, victoria directa, goles, BTTS, clean sheet → corners/tarjetas como fallback
  const ecS = p.expectedCorners || { home: 5, away: 3, total: 8 };
  const ecdS = p.expectedCards   || { home: 1.5, away: 1.5, total: 3 };
  const ecTotalS = ecS.total || 8;
  const ecdTotalS = ecdS.total || 3;
  const cLineLowS = ecTotalS >= 10 ? 7.5 : ecTotalS >= 8 ? 6.5 : 5.5;
  const cLineFavS = Math.max(ecS.home||5, ecS.away||3) >= 5 ? 4.5 : 3.5;
  const probCLowS  = Math.min(88, Math.max(55, 58 + (ecTotalS - cLineLowS) * 8));
  const probCFavS  = Math.min(88, Math.max(58, 62 + (Math.max(ecS.home||5,ecS.away||3) - cLineFavS) * 10));
  const probCards1S= Math.min(88, Math.max(52, 55 + (ecdTotalS - 1.5) * 12));
  const securePool = [
    // Mercados principales — alta prioridad
    { market: "dc",          label: `${fav} o empate`,                    prob: favDC },
    { market: "o15",         label: t("legO15"),                           prob: p.over15 },
    { market: "u35",         label: t("legU35"),                           prob: under35 },
    { market: "btts_no",     label: t("legBttsNo"),                        prob: noBtts },
    { market: "u25",         label: "Menos de 2.5 goles",                  prob: under25 },
    { market: "wtn",         label: `${fav} gana sin recibir gol`,         prob: favWTN },
    // Fallback: córners/tarjetas solo si nada más llega a prob ≥ 60
    { market: "corner_fav",  label: `${fav} córners Over ${cLineFavS}`,   prob: +probCFavS.toFixed(1) },
    { market: "corner_tot",  label: `Total córners Over ${cLineLowS}`,    prob: +probCLowS.toFixed(1) },
    { market: "cards_15",    label: `Tarjetas amarillas Over 1.5`,        prob: +probCards1S.toFixed(1) },
  ];

  // ── RISKY (5 patas) — mercados combinables de menor probabilidad pero mayor cuota ──
  const riskyPool = [
    { market: "result",  label: t("legToWin", fav),   prob: favWin },
    { market: "o25",     label: t("legO25"),           prob: p.over25 },
  ];
  if (favHT >= 28)   riskyPool.push({ market: "ht",     label: t("legHtLead", fav),  prob: favHT });
  if (drawHT >= 25)  riskyPool.push({ market: "htdraw", label: state.lang==='es'?`Empate al descanso`:`Draw at HT`, prob: drawHT });
  if (favWTN >= 18)  riskyPool.push({ market: "wtn",    label: t("legWtn", fav),     prob: favWTN });
  if (p.btts >= 45)  riskyPool.push({ market: "btts",   label: t("legBttsYes"),      prob: p.btts });
  if (dogScores >= 40) riskyPool.push({ market: "dscore",label: t("legToScore", dog), prob: dogScores });
  if (dogWin >= 20)  riskyPool.push({ market: "dogwin", label: t("legToWin", dog),   prob: dogWin });
  if (p.over35 >= 25) riskyPool.push({ market: "o35",   label: "Más de 3.5 goles",   prob: p.over35 });

  const secure = pickLegs(securePool, 5);
  const risky  = pickLegs(riskyPool, 5);
  const ps = p.predictedScore;

  // ── MERCADOS ALTERNATIVOS (córners, amarillas, faltas) ───────────────────
  const ec = p.expectedCorners || { home: 5, away: 3, total: 8 };
  const ecd = p.expectedCards   || { home: 1.5, away: 1.5, total: 3 };
  const homeIsStr = p.prob.home >= p.prob.away;
  const strongTeam = homeIsStr ? m.home : m.away;
  const weakTeam   = homeIsStr ? m.away : m.home;
  const ecHome = ec.home || 5, ecAway = ec.away || 3, ecTotal = ec.total || 8;
  const ecdHome = ecd.home || 1.5, ecdAway = ecd.away || 1.5, ecdTotal = ecd.total || 3;

  // Córner lines basadas en expectedCorners del modelo
  const cornersTotal = ecTotal;
  const cLineHigh = cornersTotal >= 10 ? 8.5 : cornersTotal >= 8 ? 7.5 : 6.5;
  const cLineLow  = cornersTotal >= 10 ? 6.5 : cornersTotal >= 8 ? 5.5 : 4.5;
  const cLineFav  = Math.max(ecHome, ecAway) >= 5 ? 4.5 : 3.5;
  const probCornerHigh = Math.min(92, Math.max(45, 50 + (cornersTotal - cLineHigh) * 10));
  const probCornerLow  = Math.min(92, Math.max(55, 60 + (cornersTotal - cLineLow)  * 8));
  const probCornerFav  = Math.min(90, Math.max(60, 65 + (Math.max(ecHome,ecAway) - cLineFav) * 10));

  // Amarillas basadas en expectedCards
  const cardLine = ecdTotal >= 4 ? 2.5 : ecdTotal >= 3 ? 1.5 : 1.5;
  const probCards15 = Math.min(90, Math.max(50, 55 + (ecdTotal - 1.5) * 12));
  const probCards25 = Math.min(82, Math.max(35, 40 + (ecdTotal - 2.5) * 12));
  const probWeakCard = Math.min(85, Math.max(50, 55 + ecdTotal * 5));

  // Faltas (estimadas desde xG y estilos — no tenemos dato directo pero lo derivamos)
  const probFaultsHigh = Math.min(80, Math.max(55, 58 + (favWin >= 70 ? 8 : favWin >= 55 ? 4 : 0)));

  const altPool = [
    { key: "corner_low",   label: `${strongTeam} córners Over ${cLineFav}`,       prob: +probCornerFav.toFixed(1),  group: "corner" },
    { key: "corner_total", label: `Total córners Over ${cLineLow}`,                prob: +probCornerLow.toFixed(1),  group: "corner" },
    { key: "cards_15",     label: `Tarjetas amarillas Over 1.5`,                   prob: +probCards15.toFixed(1),   group: "cards" },
    { key: "weak_card",    label: `${weakTeam} recibe tarjeta amarilla`,           prob: +probWeakCard.toFixed(1),  group: "cards" },
    { key: "fouls_high",   label: `Total faltas Over 20.5`,                        prob: +probFaultsHigh.toFixed(1),group: "fouls" },
    { key: "corner_high",  label: `Total córners Over ${cLineHigh}`,               prob: +probCornerHigh.toFixed(1),group: "corner" },
    { key: "cards_25",     label: `Tarjetas amarillas Over 2.5`,                   prob: +probCards25.toFixed(1),   group: "cards" },
  ].filter(x => x.prob >= 45).sort((a, b) => b.prob - a.prob);

  // Combinada segura ×3 de mercados alternativos (distinto grupo, sin repetir)
  const altSecure = [];
  const usedGroups = new Set();
  for (const leg of altPool) {
    if (!usedGroups.has(leg.group) && leg.prob >= 60) {
      usedGroups.add(leg.group);
      altSecure.push(leg);
      if (altSecure.length === 3) break;
    }
  }
  // Si no llega a 3, rellena con los siguientes sin importar grupo
  for (const leg of altPool) {
    if (altSecure.length >= 3) break;
    if (!altSecure.find(x => x.key === leg.key)) altSecure.push(leg);
  }

  // 5 picks más seguros combinables — más seguras primero, córners como fallback
  // Córners Over 2.5 y Más de 0.5 goles son las dos apuestas más seguras del fútbol
  const probO05  = Math.min(97, Math.max(88, 90 + (p.over15 - 75) * 0.4)); // derivado de O1.5
  const probC25  = Math.min(99, Math.max(92, 94 + (ecTotal - 8) * 0.5));   // derivado de córners esperados
  const parlay5Pool = [
    // Las dos más seguras del fútbol — casi certeza matemática
    { key: "c25",      label: `Córners Over 2.5`,                          prob: +probC25.toFixed(1),  group: "corners_safe" },
    { key: "o05",      label: `Más de 0.5 goles`,                          prob: +probO05.toFixed(1),  group: "goals_safe" },
    // Mercados principales de alta probabilidad
    { key: "dc",       label: `${fav} o empate`,                           prob: favDC,    group: "dc" },
    { key: "o15",      label: `Más de 1.5 goles`,                          prob: p.over15, group: "goals" },
    { key: "u35",      label: `Menos de 3.5 goles`,                        prob: under35,  group: "goals" },
    { key: "u25",      label: `Menos de 2.5 goles`,                        prob: under25,  group: "goals" },
    { key: "o25",      label: `Más de 2.5 goles`,                          prob: p.over25, group: "goals" },
    { key: "btts_no",  label: `Ambos equipos NO anotan`,                   prob: noBtts,   group: "btts" },
    { key: "result",   label: `${fav} gana`,                               prob: favWin,   group: "result" },
    { key: "wtn",      label: `${fav} gana sin recibir gol`,               prob: favWTN,   group: "wtn" },
    { key: "ht",       label: `${fav} gana el primer tiempo`,              prob: favHT,    group: "ht" },
    { key: "htdraw",   label: `Empate al descanso`,                        prob: drawHT,   group: "ht" },
    { key: "tscore",   label: `${fav} anota`,                              prob: favScores, group: "score" },
    // Resto de córners/tarjetas como último recurso
    ...altPool.slice(0, 3).map(x => ({ ...x, key: `alt_${x.key}`, group: `alt_${x.group}` })),
  ].filter(x => x.prob >= 50).sort((a, b) => b.prob - a.prob);

  // ── TOP 3 más seguras ────────────────────────────────────────
  const top3 = [];
  const usedKeysT3 = new Set();
  const usedGroupsT3 = new Set();
  for (const leg of parlay5Pool) {
    if (usedKeysT3.has(leg.key)) continue;
    if (leg.group === 'goals' && usedGroupsT3.has('goals')) continue;
    usedKeysT3.add(leg.key);
    usedGroupsT3.add(leg.group);
    top3.push(leg);
    if (top3.length === 3) break;
  }

  // ── RISKY 5 — siguientes 5 picks seguros, distintos a los top3 ──
  const risky5 = [];
  const usedKeysR5 = new Set([...usedKeysT3]);
  const usedGroupsR5 = new Set([...usedGroupsT3]);
  for (const leg of parlay5Pool) {
    if (usedKeysR5.has(leg.key)) continue;
    if (leg.group === 'goals' && usedGroupsR5.has('goals')) continue;
    usedKeysR5.add(leg.key);
    usedGroupsR5.add(leg.group);
    risky5.push(leg);
    if (risky5.length === 5) break;
  }

  return {
    secure: { legs: secure, combined: combined(secure) },
    risky:  { legs: risky,  combined: combined(risky) },
    longshot: { label: t("exactScore", m.home, ps.home, ps.away, m.away), prob: ps.p },
    altSecure: { legs: altSecure, combined: combined(altSecure) },
    top3:   { legs: top3,   combined: combined(top3)   },
    risky5: { legs: risky5, combined: combined(risky5) },
  };
}

function comboCard(title, icon, cls, combo) {
  const odds = combo.combined > 0 ? (100 / combo.combined).toFixed(2) : "—";
  return `<div class="combo-card ${cls}">
    <div class="combo-head">
      <span class="combo-title">${icon} ${title}</span>
      <span class="combo-combined">~${combo.combined}%</span>
    </div>
    ${combo.legs.map(l => `
      <div class="combo-leg">
        <span class="leg-label">${escapeHtml(l.label)}</span>
        <span class="leg-prob">${l.prob}%</span>
      </div>`).join("")}
    <div class="combo-foot">${t("legsHit", combo.legs.length, combo.combined, odds)}</div>
  </div>`;
}

// ---------- live in-play recommendations ----------
function buildLiveRecos(live, m) {
  const recos = [];
  const add = (label, prob) => { if (prob >= 1) recos.push({ label, prob: +prob.toFixed(1) }); };
  const ng = live.nextGoal, pr = live.prob;
  const homeLeads = live.homeScore > live.awayScore;
  const awayLeads = live.awayScore > live.homeScore;
  const level = live.homeScore === live.awayScore;
  const favWin = Math.max(pr.home, pr.away);
  const favTeam = pr.home >= pr.away ? m.home : m.away;
  const undTeam = pr.home >= pr.away ? m.away : m.home;

  // 1. Leader protecting a lead, or strong live favourite to win
  if (live.leader && favWin >= 60 && favTeam === live.leader)
    add(t("liveLeaderHolds", live.leader, favWin), favWin);
  else if (favWin >= 58)
    add(t("liveLeaderHolds", favTeam, favWin), favWin);

  // 2. Next goal — only when it's a clear lean
  const nextTeam = ng.home >= ng.away ? m.home : m.away;
  const nextPct = Math.max(ng.home, ng.away);
  if (nextPct >= 42 && (nextPct - Math.min(ng.home, ng.away)) >= 12)
    add(t("liveNextHome", nextTeam, nextPct), nextPct);
  if (ng.none >= 55)
    add(t("liveNextNone", ng.none), ng.none);

  // 3. Goals market for the rest of the match (skip already-settled lines)
  const tot = live.curTotal ?? 0;
  if (tot < 3 && live.liveOver25 >= 55 && live.liveOver25 < 99.5) add(t("liveOver", "2.5", live.liveOver25), live.liveOver25);
  else if (live.liveUnder25 >= 60 && live.liveUnder25 < 99.5) add(t("liveUnder", "2.5", live.liveUnder25), live.liveUnder25);
  if (tot < 2 && live.liveOver15 >= 78 && live.liveOver15 < 99.5) add(t("liveOver", "1.5", live.liveOver15), live.liveOver15);

  // 4. BTTS still live (only meaningful if not already both scored)
  if (!live.bttsResolved && live.liveBtts >= 55) add(t("liveBttsYes", live.liveBtts), live.liveBtts);

  // 5. Comeback / draw protection for trailing favourite
  if ((homeLeads || awayLeads)) {
    const trailing = homeLeads ? m.away : m.home;
    const trailDC = homeLeads ? +(pr.away + pr.draw).toFixed(1) : +(pr.home + pr.draw).toFixed(1);
    if (trailDC >= 40) add(t("liveComeback", trailing, trailDC), trailDC);
  } else if (level && pr.draw >= 45) {
    add(t("liveDrawNow", pr.draw), pr.draw);
  }

  // dedupe by label, keep top 4 by probability
  const seen = new Set();
  return recos.filter(r => !seen.has(r.label) && seen.add(r.label))
              .sort((a, b) => b.prob - a.prob).slice(0, 4);
}

function renderLivePanel(live, m) {
  if (live.error) return "";
  const ng = live.nextGoal, pr = live.prob;
  const recos = buildLiveRecos(live, m);
  const recoHtml = recos.map(r => {
    const odds = r.prob > 0 ? (100 / r.prob).toFixed(2) : "—";
    return `<div class="live-reco">
      <span class="live-reco-label">${escapeHtml(r.label)}</span>
      <span class="live-reco-odds">${t("liveFairOdds", odds)}</span>
    </div>`;
  }).join("");
  const minDisplay = live.minute >= 90 ? "90+'" : live.minute > 0 ? live.minute + "'" : "—'";
  const scoreDisplay = `${live.homeScore} – ${live.awayScore}`;
  return `
  <div class="live-panel">
    <div class="live-panel-head">
      <span class="live-panel-title">${t("liveTitle")}</span>
      <span class="live-clock-badge"><span class="live-dot"></span>${minDisplay}</span>
    </div>
    <div class="live-scoreline">
      <span class="live-team-name">${escapeHtml(m.home)}</span>
      <span class="live-score-big">${scoreDisplay}</span>
      <span class="live-team-name live-team-away">${escapeHtml(m.away)}</span>
    </div>

    <div class="live-row">
      <div class="live-sub">${t("liveNextGoal")}</div>
      <div class="split-bar live-bar">
        <span class="h" style="width:${ng.home}%"></span>
        <span class="n" style="width:${ng.none}%"></span>
        <span class="a" style="width:${ng.away}%"></span>
      </div>
      <div class="split-row">
        <span class="lh">${escapeHtml(m.home)} ${ng.home}%</span>
        <span class="muted">${t("liveNone")} ${ng.none}%</span>
        <span class="la">${escapeHtml(m.away)} ${ng.away}%</span>
      </div>
    </div>

    <div class="live-row">
      <div class="live-sub">${t("liveResultNow")}</div>
      <div class="probbar">
        <div class="probseg home" style="width:${pr.home}%">${pr.home >= 12 ? Math.round(pr.home) + "%" : ""}</div>
        <div class="probseg draw" style="width:${pr.draw}%">${pr.draw >= 12 ? Math.round(pr.draw) + "%" : ""}</div>
        <div class="probseg away" style="width:${pr.away}%">${pr.away >= 12 ? Math.round(pr.away) + "%" : ""}</div>
      </div>
      <div class="prob-legend">
        <span>🟢 ${escapeHtml(m.home)} ${pct(pr.home)}</span>
        <span>${t("draw")} ${pct(pr.draw)}</span>
        <span>${escapeHtml(m.away)} ${pct(pr.away)} 🔵</span>
      </div>
    </div>

    ${recoHtml ? `<div class="live-sub live-recos-label">⚡ ${t("liveRecos")}</div><div class="live-recos">${recoHtml}</div>` : ""}
    <div class="live-disclaimer">${t("liveDisclaimer")}</div>
  </div>`;
}

// ---------- local analyst read (free, no API) ----------
function localRead(p, m) {
  const ph = p.prob.home, pd = p.prob.draw, pa = p.prob.away;
  const eg = p.expectedGoals;
  const sf = p.scoreFirst;
  const ec = p.expectedCorners;
  const ht = p.halfTime || {home: 0, draw: 0, away: 0};
  const cs = p.cleanSheet || {home: 0, away: 0};
  const ecd = p.expectedCards;
  const fc = p.firstCorner || {home: 0, away: 0};
  const home = m.home, away = m.away;
  const fav = p.favorite;
  const und = fav === home ? away : home;
  const favWin = Math.max(ph, pa);
  const undWin = Math.min(ph, pa);
  const totalXg = +(eg.home + eg.away).toFixed(2);
  const rows = [];

  // 1. Verdict
  let verdict;
  if (favWin > 72)      verdict = t("vHeavy", escapeHtml(fav), favWin);
  else if (favWin > 58) verdict = t("vModerate", escapeHtml(fav), favWin, escapeHtml(und), undWin, pd);
  else if (favWin > 48) verdict = t("vNarrow", escapeHtml(fav), favWin, pd);
  else                  verdict = t("vCoinflip", escapeHtml(fav), favWin);
  rows.push({icon:"🎯", title: t("rVerdict"), text: verdict});

  // 2. Goals outlook
  let goalsTxt;
  if (totalXg < 1.6)      goalsTxt = t("gVeryLow", eg.home, eg.away, totalXg, p.over25, p.btts);
  else if (totalXg < 2.3) goalsTxt = t("gModest", eg.home, eg.away, p.over25, p.btts);
  else if (totalXg < 3.0) goalsTxt = t("gDecent", eg.home, eg.away, p.over25, p.btts);
  else                    goalsTxt = t("gFeast", eg.home, eg.away, totalXg, p.over25, p.btts);
  rows.push({icon:"⚽", title: t("rGoals"), text: goalsTxt});

  // 3. First half read
  const htH = ht.home || 0, htD = ht.draw || 0, htA = ht.away || 0;
  let htTxt;
  if (htD > 40)
    htTxt = t("htCagey", htD);
  else if (htH > htA)
    htTxt = t("htEdge", escapeHtml(home), htH, escapeHtml(home), htH, htD, escapeHtml(away), htA);
  else
    htTxt = t("htEdge", escapeHtml(away), htA, escapeHtml(home), htH, htD, escapeHtml(away), htA);
  rows.push({icon:"⏱", title: t("rFirstHalf"), text: htTxt});

  // 4. First goal
  const sfTeam = sf.home > sf.away ? home : away;
  const sfPct = Math.max(sf.home, sf.away);
  const sfNone = Math.max(0, +(100 - sf.home - sf.away).toFixed(1));
  rows.push({icon:"🔫", title: t("rFirstGoal"), text: t("fgText", escapeHtml(sfTeam), sfPct, sfNone)});

  // 5. Set pieces
  const cornTeam = ec.home > ec.away ? home : away;
  const fcPct = Math.max(fc.home, fc.away);
  rows.push({icon:"🚩", title: t("rSetPieces"), text: t("spText", escapeHtml(cornTeam), ec.total, escapeHtml(home), ec.home, escapeHtml(away), ec.away, fcPct)});

  // 6. Discipline
  const cardCtx = ecd.total > 4.2 ? t("dFeisty") : ecd.total > 3.4 ? t("dModerate") : t("dDisciplined");
  rows.push({icon:"🟨", title: t("rDiscipline"), text: t("dText", ecd.total, escapeHtml(home), ecd.home, escapeHtml(away), ecd.away, cardCtx)});

  // 7. Upset risk
  let riskTxt;
  if (undWin > 28)      riskTxt = t("rkLive", escapeHtml(und), undWin);
  else if (undWin > 15) riskTxt = t("rkPossible", escapeHtml(und), undWin);
  else                  riskTxt = t("rkUnlikely", escapeHtml(und), undWin);
  rows.push({icon:"⚠️", title: t("rRisk"), text: riskTxt});

  return rows;
}

// ---------- day combos (multi-match parlays) ----------
function _bestBetForPick(p, mode) {
  const favIsHome = p.prob.home >= p.prob.away;
  const favName = favIsHome ? p.home : p.away;
  const favProb = Math.max(p.prob.home, p.prob.away);
  const drawProb = p.prob.draw || 0;
  const dcProb = favProb + drawProb;
  const under25 = 100 - (p.over25 || 50);
  const o15 = p.over15 || 0;
  const matchLabel = `${p.home} vs ${p.away}`;

  if (mode === 'safe') {
    // Pick highest-probability selection (usually DC or O1.5)
    const opts = [
      { label: `${favName} o empate`, prob: dcProb, type: 'dc' },
      { label: 'Más de 1.5 goles', prob: o15, type: 'o15' },
      { label: 'Menos de 2.5 goles', prob: under25, type: 'u25' },
    ].sort((a, b) => b.prob - a.prob);
    const best = opts[0];
    return best.prob >= 62 ? { ...best, match: matchLabel, league: p.league } : null;
  } else {
    // Risky: prefer direct result; fall back to O1.5
    if (favProb >= 55) {
      return { label: `${favName} gana`, prob: +favProb.toFixed(1), type: '1x2', match: matchLabel, league: p.league };
    }
    if (o15 >= 60) {
      return { label: 'Más de 1.5 goles', prob: +o15.toFixed(1), type: 'o15', match: matchLabel, league: p.league };
    }
    if (dcProb >= 60) {
      return { label: `${favName} o empate`, prob: +dcProb.toFixed(1), type: 'dc', match: matchLabel, league: p.league };
    }
    return null;
  }
}

function buildDayCombos(picks) {
  const seen = new Set();
  const unique = picks.filter(p => {
    const key = `${p.home}|${p.away}`;
    if (seen.has(key)) return false;
    seen.add(key); return true;
  });

  const safeLegs = unique.map(p => _bestBetForPick(p, 'safe')).filter(Boolean)
    .sort((a, b) => b.prob - a.prob);
  const riskyLegs = unique.map(p => _bestBetForPick(p, 'risky')).filter(Boolean)
    .sort((a, b) => b.prob - a.prob);

  function makeCombo(legs, n) {
    const selected = legs.slice(0, n);
    if (selected.length < n) return null;
    const combined = +(selected.reduce((acc, l) => acc * l.prob / 100, 1) * 100).toFixed(1);
    const fairOdds = combined > 0 ? +(100 / combined * 0.92).toFixed(2) : '—';
    return { legs: selected, combined, fairOdds };
  }
  return { safe: makeCombo(safeLegs, 3), risky: makeCombo(riskyLegs, 5) };
}

function renderDayCombos(combos) {
  function comboBlock(label, icon, c) {
    if (!c) return '';
    return `
    <div class="daycombo-card">
      <div class="daycombo-title">${icon} ${label} <span class="daycombo-odds">~${c.fairOdds}x</span></div>
      ${c.legs.map(l => `
        <div class="daycombo-leg">
          <span class="dcl-match">${escapeHtml(l.match)}</span>
          <span class="dcl-pick">${escapeHtml(l.label)}</span>
          <span class="dcl-prob">${l.prob.toFixed(0)}%</span>
        </div>`).join('')}
      <div class="daycombo-foot">Prob. combinada ≈ <strong>${c.combined}%</strong> · cuota justa ≈ <strong>${c.fairOdds}x</strong></div>
    </div>`;
  }
  return `
  <div class="daycombo-section">
    <div class="daycombo-header">🎰 Combinadas del día</div>
    <div class="daycombo-grid">
      ${comboBlock('Combinada Segura', '🛡️', combos.safe)}
      ${comboBlock('Combinada Arriesgada', '🔥', combos.risky)}
    </div>
    <p class="daycombo-disclaimer">⚠️ Estimaciones del modelo estadístico, no asesoría financiera. Las probabilidades son independientes — las cuotas reales varían según la casa.</p>
  </div>`;
}

// ---------- top picks ----------
function openTopPicks() {
  $("topPicksModal").classList.remove("hidden");
  loadTopPicks();
}
function closeTopPicksModal() { $("topPicksModal").classList.add("hidden"); }

async function loadTopPicks() {
  const list = $("picksList");
  list.innerHTML = `<p class="muted small" style="text-align:center;padding:20px">${t("crunching")}</p>`;
  try {
    const res = await fetch(`/api/top-picks?date=${encodeURIComponent(state.date)}&tz=${-new Date().getTimezoneOffset()}`);
    const data = await res.json();
    const picks = data.picks || [];
    if (!picks.length) {
      list.innerHTML = `<div class="picks-empty">
        <p>${t("noPicks", prettyDate(state.date))}</p>
        <p class="muted small">${t("noPicksHint")}</p>
      </div>`;
      return;
    }
    const combos = buildDayCombos(picks);
    const combosHtml = (combos.safe || combos.risky) ? renderDayCombos(combos) : '';
    list.innerHTML = combosHtml + picks.map((p, i) => renderPickCard(p, i)).join("");
    // Wire click handlers — clicking a pick card opens the insights modal
    list.querySelectorAll("[data-pick-idx]").forEach(card => {
      card.onclick = () => {
        const pick = picks[+card.dataset.pickIdx];
        closeTopPicksModal();
        // Build a minimal match object that openInsights can use
        const m = {
          home: pick.home, away: pick.away, league: pick.league,
          homeBadge: pick.homeBadge, awayBadge: pick.awayBadge,
          kickoffUtc: pick.kickoffUtc, status: pick.status,
        };
        openInsights(m);
      };
    });
  } catch (e) {
    list.innerHTML = `<p class="muted small">⚠️ ${t("couldNotLoadPicks")} ${escapeHtml(String(e))}</p>`;
  }
}

function pickStatusBadge(p) {
  const s = (p.status || "").toLowerCase();
  if (s === "live") return `<span class="pick-status live">${t("liveBadge")}</span>`;
  if (s === "finished") return `<span class="pick-status ft">FT</span>`;
  // Scheduled / upcoming — show LOCAL kickoff time (SportsDB timestamps are UTC)
  if (p.kickoffUtc) {
    let iso = p.kickoffUtc.includes("T") ? p.kickoffUtc : p.kickoffUtc.replace(" ", "T");
    if (!/[zZ]|[+\-]\d\d:?\d\d$/.test(iso)) iso += "Z";
    const t = new Date(iso);
    if (!isNaN(t)) {
      const hh = String(t.getHours()).padStart(2, "0");
      const mm = String(t.getMinutes()).padStart(2, "0");
      return `<span class="pick-status soon">⏱ ${hh}:${mm}</span>`;
    }
  }
  return `<span class="pick-status soon">${t("upcoming")}</span>`;
}

function renderPickCard(p, idx) {
  const rank = idx + 1;
  const medal = rank === 1 ? "🥇" : rank === 2 ? "🥈" : rank === 3 ? "🥉" : `<span class="pick-rank-num">${rank}</span>`;
  const conf = +p.conf.toFixed(1);
  const confClass = conf >= 7 ? "conf-high" : conf >= 5.5 ? "conf-mid" : "conf-low";
  const confPct = Math.round(Math.min(conf / 10, 1) * 100);
  const favProb = Math.max(p.prob.home, p.prob.away);
  const undProb = Math.min(p.prob.home, p.prob.away);
  const isHomeF = p.prob.home >= p.prob.away;
  const ps = p.predictedScore;
  const totalXg = +(p.expectedGoals.home + p.expectedGoals.away).toFixed(1);
  const overSignal = p.over25 >= 55 ? `O2.5 ${p.over25}% ✓` : p.over25 <= 38 ? `U2.5 ${100 - p.over25}% ✓` : `O2.5 ${p.over25}%`;
  const homeBadgeHtml = p.homeBadge
    ? `<img class="pick-badge" src="${escapeHtml(p.homeBadge)}" alt="" loading="lazy" onerror="this.style.display='none'">`
    : `<span class="pick-badge-placeholder"></span>`;
  const awayBadgeHtml = p.awayBadge
    ? `<img class="pick-badge" src="${escapeHtml(p.awayBadge)}" alt="" loading="lazy" onerror="this.style.display='none'">`
    : `<span class="pick-badge-placeholder"></span>`;
  const statusBadge = pickStatusBadge(p);

  return `<div class="pick-card" data-pick-idx="${idx}" role="button" tabindex="0">
    <div class="pick-medal">${medal}</div>
    <div class="pick-body">
      <div class="pick-teams">
        ${homeBadgeHtml}<span class="pick-team ${isHomeF ? "pick-fav-team" : ""}">${escapeHtml(p.home)}</span>
        <span class="pick-vs">vs</span>
        ${awayBadgeHtml}<span class="pick-team ${!isHomeF ? "pick-fav-team" : ""}">${escapeHtml(p.away)}</span>
      </div>
      <div class="pick-meta">
        <span class="pick-league-tag">${escapeHtml(p.league || "Match")}</span>
        ${statusBadge}
        <span class="pick-score-hint">${t("likely", ps.home, ps.away)}</span>
        <span class="pick-over-hint">${overSignal}</span>
      </div>
    </div>
    <div class="pick-right">
      <div class="pick-prob-wrap">
        <span class="pick-fav-label">${escapeHtml(p.favorite)}</span>
        <span class="pick-fav-prob">${favProb}%</span>
      </div>
      <div class="pick-conf-wrap ${confClass}" title="${t("pickConfTitle", conf)}">
        <div class="pick-conf-bar"><div class="pick-conf-fill" style="width:${confPct}%"></div></div>
        <span class="pick-conf-val">${conf}</span>
      </div>
      ${p.lucas ? `<div class="pick-lucas-badge">🎲 L: ${p.lucas.ph}/${p.lucas.pd}/${p.lucas.pa}%</div>` : ""}
    </div>
  </div>`;
}

// ---------- notes (local DB) ----------
function openNotes() {
  $("notesDateLabel").textContent = "· " + prettyDate(state.date);
  $("notesModal").classList.remove("hidden");
  loadNotes();
}
function closeNotes() { $("notesModal").classList.add("hidden"); }

async function loadNotes() {
  const list = $("notesList");
  list.innerHTML = `<p class="muted small">${t("loadingNotes")}</p>`;
  try {
    const res = await fetch(`/api/notes?date=${encodeURIComponent(state.date)}`);
    const data = await res.json();
    const notes = data.notes || [];
    if (!notes.length) { list.innerHTML = `<p class="muted small">${t("noNotes")}</p>`; return; }
    list.innerHTML = notes.map(noteCard).join("");
    list.querySelectorAll("[data-del]").forEach(b => b.onclick = () => deleteNote(b.dataset.del));
  } catch (e) {
    list.innerHTML = `<p class="muted small">${t("cantLoadNotes")}</p>`;
  }
}
function noteCard(n) {
  const when = (n.created_at || "").replace("T", " ").replace("Z", " UTC");
  return `<div class="note-item">
    <div class="note-head">
      <strong>${escapeHtml(n.title || t("defaultNoteTitle"))}</strong>
      <button class="note-del" data-del="${n.id}" title="${t("delNote")}">✕</button>
    </div>
    <div class="note-body">${escapeHtml(n.body).replace(/\n/g, "<br>")}</div>
    <div class="note-meta muted small">${escapeHtml(when)}</div>
  </div>`;
}
async function submitNote(e) {
  e.preventDefault();
  const body = $("noteBody").value.trim();
  if (!body) return;
  await fetch("/api/notes", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      match_date: state.date, competition: state.scope,
      title: $("noteTitle").value.trim(), body,
    }),
  });
  $("noteTitle").value = ""; $("noteBody").value = "";
  loadNotes();
}
async function deleteNote(id) {
  await fetch("/api/notes/delete", {
    method: "POST", headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ id: Number(id) }),
  });
  loadNotes();
}

// ---------- auto refresh ----------
function setupAutoRefresh() {
  if (state.autoTimer) clearInterval(state.autoTimer);
  if ($("autoRefresh").checked) {
    state.autoTimer = setInterval(() => {
      // Advance date if the calendar day changed (app left open overnight)
      const today = localDateStr();
      if (state.date === today || state.date > today) {
        state.date = today;
      }
      loadMatches();
    }, 45000);
  }
}

function autoGrow(ta) { ta.style.height = "auto"; ta.style.height = Math.min(ta.scrollHeight, 140) + "px"; }

// ---------- wire up ----------

function init() {
  $("datePicker").value = state.date;
  $("prevDay").onclick = () => shiftDay(-1);
  $("nextDay").onclick = () => shiftDay(1);
  $("todayBtn").onclick = () => setDate(localDateStr());
  $("datePicker").onchange = (e) => setDate(e.target.value);
  document.querySelectorAll(".seg-opt").forEach((b) => b.onclick = () => {
    document.querySelectorAll(".seg-opt").forEach((x) => x.classList.remove("active"));
    b.classList.add("active");
    state.scope = b.dataset.scope;
    loadMatches();
  });
  $("refreshBtn").onclick = loadMatches;
  $("autoRefresh").onchange = setupAutoRefresh;

  $("closeInsights").onclick = closeInsights;
  $("insightsModal").onclick = (e) => { if (e.target.id === "insightsModal") closeInsights(); };

  $("quinielaBtn").onclick = openQuiniela;
  $("closeQuiniela").onclick = closeQuiniela;
  $("quinielaModal").onclick = (e) => { if (e.target.id === "quinielaModal") closeQuiniela(); };

  $("topPicksBtn").onclick = openTopPicks;
  $("closeTopPicks").onclick = closeTopPicksModal;
  $("topPicksModal").onclick = (e) => { if (e.target.id === "topPicksModal") closeTopPicksModal(); };

  $("scoutReportBtn").onclick = () => loadScoutReport(false);
  $("guruBtn").onclick = () => openGuruModal();
  $("guruInput").addEventListener("keydown", e => { if (e.key === "Enter") sendGuruMsg(); });
  $("closeScoutReport").onclick = () => $("scoutReportModal").classList.add("hidden");
  $("scoutReportModal").onclick = (e) => { if (e.target.id === "scoutReportModal") $("scoutReportModal").classList.add("hidden"); };

  $("notesBtn").onclick = openNotes;
  $("closeNotes").onclick = closeNotes;
  $("noteForm").onsubmit = submitNote;
  $("notesModal").onclick = (e) => { if (e.target.id === "notesModal") closeNotes(); };

  $("settingsBtn").onclick = openSettings;
  $("cancelSettings").onclick = closeSettings;
  $("saveSettings").onclick = saveSettings;
  if ($("sendPicksEmailBtn")) $("sendPicksEmailBtn").onclick = sendPicksEmail;
  $("langBtn").onclick = () => setLang(state.lang === "es" ? "en" : "es");
  $("settingsModal").onclick = (e) => { if (e.target.id === "settingsModal") closeSettings(); };

  initImageUpload();
  $("chatForm").onsubmit = (e) => { e.preventDefault(); sendChat($("chatInput").value); };
  $("chatInput").oninput = (e) => autoGrow(e.target);
  $("chatInput").onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); sendChat($("chatInput").value); }
  };
  document.querySelectorAll(".chip:not(.chip-bets)").forEach(c => c.onclick = () => sendChat(c.textContent));

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") { closeInsights(); closeNotes(); closeSettings(); closeTopPicksModal(); closeInvest(); closeModelHealth(); }
  });

$("investBtn").onclick = openInvest;
  $("closeInvest").onclick = closeInvest;
  $("investModal").onclick = (e) => { if (e.target.id === "investModal") closeInvest(); };
  $("investChatForm").onsubmit = (e) => { e.preventDefault(); investSend($("investChatInput").value); };
  $("investChatInput").oninput = (e) => autoGrow(e.target);
  $("investChatInput").onkeydown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) { e.preventDefault(); investSend($("investChatInput").value); }
  };
  document.querySelectorAll(".invest-tab").forEach(b => b.onclick = () => investTabSwitch(b.dataset.itab));

  applyI18n();
  loadMe();
  loadConfig();
  loadMatches();
  setupAutoRefresh();
}

document.addEventListener("DOMContentLoaded", init);

// iOS keyboard fix — scroll input into view when keyboard opens in popups
(function() {
  const isIOS = /iPad|iPhone|iPod/.test(navigator.userAgent);
  if (!isIOS) return;
  const inputs = ["chatInput", "guruInput"];
  inputs.forEach(id => {
    const el = document.getElementById(id);
    if (!el) return;
    el.addEventListener("focus", () => {
      setTimeout(() => el.scrollIntoView({ block: "nearest", behavior: "smooth" }), 350);
    });
  });
  // When visual viewport resizes (keyboard), shrink chat popup height
  if (window.visualViewport) {
    window.visualViewport.addEventListener("resize", () => {
      const popup = document.querySelector(".chat-popup:not(.hidden)");
      if (popup) {
        const avail = window.visualViewport.height;
        popup.style.maxHeight = Math.min(avail * 0.85, 540) + "px";
      }
      const guru = document.getElementById("guruModal");
      if (guru && !guru.classList.contains("hidden")) {
        const card = guru.querySelector(".guru-card");
        if (card) card.style.maxHeight = Math.min(window.visualViewport.height * 0.95, 680) + "px";
      }
    });
  }
})();

// ========== INVESTMENT ANALYST ==========

const _investState = { history: [], sending: false };

function openInvest() {
  $("investModal").classList.remove("hidden");
  renderInvestDashboard();
  renderInvestApps();
}

function closeInvest() {
  $("investModal").classList.add("hidden");
}

function investTabSwitch(tab) {
  document.querySelectorAll(".invest-tab").forEach(b => b.classList.toggle("active", b.dataset.itab === tab));
  ["dashboard","chat","apps"].forEach(p => {
    const el = $("investPane" + p.charAt(0).toUpperCase() + p.slice(1));
    if (el) el.classList.toggle("hidden", p !== tab);
  });
}

function investChip(msg) {
  investTabSwitch("chat");
  investSend(msg);
}

async function investSend(msg) {
  msg = (msg || "").trim();
  if (!msg || _investState.sending) return;
  $("investChatInput").value = "";
  autoGrow($("investChatInput"));

  const log = $("investChatLog");
  log.insertAdjacentHTML("beforeend", `<div class="invest-msg user"><p>${escapeHtml(msg)}</p></div>`);
  _investState.history.push({ role: "user", content: msg });

  _investState.sending = true;
  $("investSendBtn").disabled = true;
  const thinking = document.createElement("div");
  thinking.className = "invest-msg assistant invest-thinking";
  thinking.innerHTML = `<span class="invest-dots"><span></span><span></span><span></span></span>`;
  log.appendChild(thinking);
  log.scrollTop = log.scrollHeight;

  try {
    const res = await fetch("/api/invest/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ message: msg, history: _investState.history.slice(-12), lang: state.lang }),
    });
    const data = await res.json();
    thinking.remove();
    if (data.error) {
      log.insertAdjacentHTML("beforeend", `<div class="invest-msg assistant error"><p>⚠️ ${escapeHtml(data.error)}</p></div>`);
    } else {
      const reply = data.reply || "";
      _investState.history.push({ role: "assistant", content: reply });
      log.insertAdjacentHTML("beforeend", `<div class="invest-msg assistant">${renderMarkdown(reply)}</div>`);
    }
  } catch (e) {
    thinking.remove();
    log.insertAdjacentHTML("beforeend", `<div class="invest-msg assistant error"><p>⚠️ Network error: ${escapeHtml(String(e))}</p></div>`);
  } finally {
    _investState.sending = false;
    $("investSendBtn").disabled = false;
    log.scrollTop = log.scrollHeight;
  }
}

function renderInvestDashboard() {
  const el = $("investDashboard");
  if (!el || el.dataset.rendered) return;
  el.dataset.rendered = "1";
  el.innerHTML = `
    ${investSection("📅 Daily Market Briefing Template", `
      <p class="muted small">Ask the analyst "Give me a daily briefing" or use the chip in the Chat tab.</p>
      <table class="invest-table">
        <tr><th>Asset</th><th>What to Track</th><th>Why It Matters</th></tr>
        <tr><td>S&P 500 (SPY)</td><td>Price, % change, volume vs avg</td><td>US large-cap benchmark</td></tr>
        <tr><td>Nasdaq (QQQ)</td><td>Price, % change, tech weighting</td><td>Tech/growth risk sentiment</td></tr>
        <tr><td>Dow Jones (DIA)</td><td>Price, % change</td><td>Blue-chip industrials</td></tr>
        <tr><td>Russell 2000 (IWM)</td><td>Price, vs S&P spread</td><td>Small-cap / risk appetite</td></tr>
        <tr><td>Bitcoin (BTC)</td><td>Price, dominance %, volume</td><td>Crypto risk-on indicator</td></tr>
        <tr><td>Ethereum (ETH)</td><td>Price, ETH/BTC ratio</td><td>Alt-coin and DeFi health</td></tr>
        <tr><td>Gold (GLD)</td><td>Price, USD correlation</td><td>Safe haven / inflation hedge</td></tr>
        <tr><td>Oil (USO/WTI)</td><td>Price, OPEC news</td><td>Inflation, geopolitical risk</td></tr>
        <tr><td>US Dollar (DXY)</td><td>Index level, trend</td><td>Inverse to risk assets</td></tr>
        <tr><td>10Y Treasury</td><td>Yield level, change</td><td>Rate risk, stock valuation</td></tr>
        <tr><td>VIX</td><td>Level (&lt;20 calm / &gt;30 fear)</td><td>Market fear gauge</td></tr>
      </table>
    `)}
    ${investSection("🔔 Real-Time Alert Template", `
      <div class="invest-alert-template">
        <div class="invest-alert-row"><span class="invest-label">Subject:</span> Market Alert: [Asset/Ticker] – [Reason]</div>
        <div class="invest-alert-row"><span class="invest-label">What happened:</span> [Price move / event description]</div>
        <div class="invest-alert-row"><span class="invest-label">Why it matters:</span> [Market context]</div>
        <div class="invest-alert-row"><span class="invest-label">Current price:</span> $X.XX (±X% today)</div>
        <div class="invest-alert-row"><span class="invest-label">Key levels:</span> Support $X / Resistance $X</div>
        <div class="invest-alert-row"><span class="invest-label">Risk level:</span> <span class="invest-risk medium">Medium</span></div>
        <div class="invest-alert-row"><span class="invest-label">Possible opportunity:</span> [Long/Short/Watch/Avoid]</div>
        <div class="invest-alert-row"><span class="invest-label">What to verify:</span> [Before acting checklist]</div>
        <div class="invest-alert-row"><span class="invest-label">Confidence:</span> X/10</div>
      </div>
    `)}
    ${investSection("📈 Stock Analysis Template", `
      <table class="invest-table">
        <tr><th>Metric</th><th>What to Check</th></tr>
        <tr><td>Revenue Growth</td><td>YoY %, trend (accelerating or slowing?)</td></tr>
        <tr><td>Earnings Growth</td><td>EPS trend, beat/miss history</td></tr>
        <tr><td>Profit Margins</td><td>Gross / Operating / Net margin vs. sector</td></tr>
        <tr><td>Debt / Equity</td><td>D/E ratio, interest coverage</td></tr>
        <tr><td>Free Cash Flow</td><td>FCF yield, FCF per share trend</td></tr>
        <tr><td>P/E Ratio</td><td>vs. historical avg, vs. sector peers</td></tr>
        <tr><td>Forward P/E</td><td>Analyst consensus next 12M</td></tr>
        <tr><td>PEG Ratio</td><td>&lt;1 = potentially undervalued vs. growth</td></tr>
        <tr><td>Competitive Moat</td><td>Brand, network effect, switching cost, patents</td></tr>
        <tr><td>Insider Activity</td><td>Buying = bullish signal; mass selling = caution</td></tr>
        <tr><td>Institutional Ownership</td><td>% held, recent changes</td></tr>
        <tr><td>Earnings Calendar</td><td>Next report date — avoid holding into surprise</td></tr>
      </table>
    `)}
    ${investSection("₿ Crypto Analysis Template", `
      <table class="invest-table">
        <tr><th>Factor</th><th>What to Check</th><th>Red Flag</th></tr>
        <tr><td>Market Cap</td><td>Rank, size vs. total crypto market</td><td>Tiny cap = high manipulation risk</td></tr>
        <tr><td>24H Volume</td><td>Volume / Market Cap ratio</td><td>&lt;5% = low liquidity</td></tr>
        <tr><td>Token Utility</td><td>Real use case or pure speculation?</td><td>No utility = meme / extreme risk</td></tr>
        <tr><td>Dev Activity</td><td>GitHub commits, team transparency</td><td>Dead repo = abandoned project</td></tr>
        <tr><td>Exchange Access</td><td>Listed on Binance/Coinbase/Kraken?</td><td>Only DEX = defi risk</td></tr>
        <tr><td>Token Unlocks</td><td>Vesting schedule, upcoming unlocks</td><td>Large unlock = sell pressure</td></tr>
        <tr><td>Whale Concentration</td><td>Top 10 wallets % of supply</td><td>&gt;50% = manipulation risk</td></tr>
        <tr><td>BTC Correlation</td><td>Does it follow BTC or diverge?</td><td>High corr = no hedge value</td></tr>
        <tr><td>Regulatory Risk</td><td>SEC status, country bans</td><td>Security classification = exit risk</td></tr>
      </table>
      <p class="muted small">⚠️ Label meme coins EXTREME RISK. Never size them &gt;1-3% of portfolio.</p>
    `)}
    ${investSection("📦 ETF Analysis Template", `
      <table class="invest-table">
        <tr><th>Factor</th><th>What to Look For</th></tr>
        <tr><td>Expense Ratio</td><td>Index ETFs: &lt;0.10% ideal. Actively managed: 0.5–1%</td></tr>
        <tr><td>Top Holdings</td><td>Concentration risk — is it too heavy in 1-2 names?</td></tr>
        <tr><td>Sector Exposure</td><td>Matches your thesis? Over/underweight vs. benchmark?</td></tr>
        <tr><td>AUM / Liquidity</td><td>&gt;$1B AUM = liquid. Low AUM = closure risk</td></tr>
        <tr><td>Dividend Yield</td><td>Relevant for income strategies</td></tr>
        <tr><td>5Y / 10Y Return</td><td>vs. benchmark index performance</td></tr>
        <tr><td>vs. Stock-Picking</td><td>80% of active managers underperform index ETFs long-term</td></tr>
      </table>
    `)}
    ${investSection("🛡️ Risk Management Template", `
      <div class="invest-risk-grid">
        <div class="invest-risk-card"><div class="invest-risk-label low">Low Risk</div><p>Broad index ETFs, treasury bonds, money market. Core portfolio (60-80%). Sleep-well positions.</p></div>
        <div class="invest-risk-card"><div class="invest-risk-label medium">Medium Risk</div><p>Individual blue-chip stocks, sector ETFs, dividend stocks. Satellite positions (15-25%). Research required.</p></div>
        <div class="invest-risk-card"><div class="invest-risk-card-label high">High Risk</div><p>Small caps, growth stocks, BTC/ETH, thematic ETFs. Speculative sleeve (5-15%). Size carefully.</p></div>
        <div class="invest-risk-card"><div class="invest-risk-card-label extreme">Extreme Risk</div><p>Meme coins, micro-caps, new tokens, leverage. Maximum 1-5% of total portfolio. Money you can afford to lose 100% of.</p></div>
      </div>
      <div class="invest-position-rules">
        <h4>Position Sizing Rules</h4>
        <ul>
          <li>Never put &gt;10% of portfolio in any single stock</li>
          <li>Never put &gt;5% in any single crypto</li>
          <li>Never put &gt;30% in any single sector</li>
          <li>Always keep 5-10% in cash for opportunities</li>
          <li>Rebalance quarterly or when position drifts &gt;5% from target</li>
        </ul>
      </div>
    `)}
    ${investSection("📋 Investment Decision Checklist", `
      <div class="invest-checklist">
        <label class="invest-check"><input type="checkbox"> Do I understand what this asset does and how it makes money?</label>
        <label class="invest-check"><input type="checkbox"> Is this based on data and fundamentals — not hype or social media?</label>
        <label class="invest-check"><input type="checkbox"> Is the price trend positive (higher highs/lows) or negative?</label>
        <label class="invest-check"><input type="checkbox"> Is the valuation reasonable vs. peers and history?</label>
        <label class="invest-check"><input type="checkbox"> Can I clearly state the #1 risk to this investment?</label>
        <label class="invest-check"><input type="checkbox"> Do I have a specific exit plan (target price + stop loss)?</label>
        <label class="invest-check"><input type="checkbox"> Is this short-term speculation or long-term investing?</label>
        <label class="invest-check"><input type="checkbox"> Is the potential reward worth the risk?</label>
        <label class="invest-check"><input type="checkbox"> Is there a safer ETF alternative that gives similar exposure?</label>
        <label class="invest-check"><input type="checkbox"> Would I still like this investment if it dropped 20% next month?</label>
      </div>
      <p class="muted small">If you can't check at least 7/10 — research more before investing.</p>
    `)}
    ${investSection("📊 Watchlist Template", `
      <table class="invest-table">
        <tr><th>Asset</th><th>Ticker</th><th>Category</th><th>Why Watching</th><th>Entry Trigger</th><th>Risk</th><th>Conf.</th></tr>
        <tr class="invest-row-placeholder"><td colspan="7">Add assets via the Analyst Chat — ask "Add [ticker] to my watchlist analysis"</td></tr>
      </table>
    `)}
    ${investSection("📧 Daily Email Report Template", `
      <div class="invest-email-template">
        <div class="invest-email-line"><strong>Subject:</strong> Daily Investment Briefing – [Date]</div>
        <hr class="invest-hr">
        <div class="invest-email-section"><strong>Executive Summary</strong> — 2-3 sentence market overview</div>
        <div class="invest-email-section"><strong>Market Mood</strong> — Risk-On / Risk-Off / Neutral + VIX level</div>
        <div class="invest-email-section"><strong>Best Opportunities Today</strong> — Top 3 ideas to research</div>
        <div class="invest-email-section"><strong>Assets to Avoid / Monitor</strong> — Caution list</div>
        <div class="invest-email-section"><strong>Crypto Update</strong> — BTC, ETH, top movers</div>
        <div class="invest-email-section"><strong>Stock Market Update</strong> — S&P, Nasdaq, key movers</div>
        <div class="invest-email-section"><strong>ETF Ideas</strong> — Sector rotation opportunities</div>
        <div class="invest-email-section"><strong>Macro Risks</strong> — Fed, inflation, geopolitics</div>
        <div class="invest-email-section"><strong>Alerts Triggered</strong> — Price breaks, news catalysts</div>
        <div class="invest-email-section"><strong>Final Analyst Conclusion</strong> — Action bias for the day</div>
      </div>
      <p class="muted small">Generate this report instantly: go to Chat → click "📰 Daily Briefing"</p>
    `)}
  `;
}

function renderInvestApps() {
  const el = $("investAppsContent");
  if (!el || el.dataset.rendered) return;
  el.dataset.rendered = "1";
  el.innerHTML = `
    <div class="invest-disclaimer">
      ⚠️ App availability, fees, and regulations may vary by country. Always verify current terms. These are educational recommendations, not endorsements.
    </div>
    <h3 class="invest-apps-title">Recommended iPhone Investment App Setup</h3>
    <div class="invest-app-cards">

      <div class="invest-app-card">
        <div class="invest-app-header">
          <span class="invest-app-icon">📊</span>
          <div>
            <div class="invest-app-name">TradingView</div>
            <div class="invest-app-role">Charts &amp; Real-Time Alerts</div>
          </div>
          <span class="invest-risk low">Free / Pro</span>
        </div>
        <table class="invest-table">
          <tr><td>Stocks, ETFs, Crypto, Forex, Commodities</td></tr>
          <tr><td>Real-time charts with 100+ indicators</td></tr>
          <tr><td>Custom price alerts (free: 1, Pro: unlimited)</td></tr>
          <tr><td>Community ideas &amp; analyst scripts</td></tr>
          <tr><td>Available globally</td></tr>
        </table>
        <p class="invest-verdict">✅ <strong>Best for:</strong> Chart analysis, technical alerts, market overview. Use this as your daily screen.</p>
      </div>

      <div class="invest-app-card">
        <div class="invest-app-header">
          <span class="invest-app-icon">💼</span>
          <div>
            <div class="invest-app-name">Interactive Brokers (IBKR)</div>
            <div class="invest-app-role">Stocks, ETFs &amp; Global Markets</div>
          </div>
          <span class="invest-risk low">Low fees</span>
        </div>
        <table class="invest-table">
          <tr><td>Stocks, ETFs, Options, Forex, Futures</td></tr>
          <tr><td>Global access: US, EU, LATAM, Asia</td></tr>
          <tr><td>$0 commissions on US stocks/ETFs</td></tr>
          <tr><td>Regulated in multiple jurisdictions</td></tr>
          <tr><td>Advanced order types, fractional shares</td></tr>
        </table>
        <p class="invest-verdict">✅ <strong>Best for:</strong> Serious long-term investors. Best global access from Costa Rica / Latin America.</p>
      </div>

      <div class="invest-app-card">
        <div class="invest-app-header">
          <span class="invest-app-icon">₿</span>
          <div>
            <div class="invest-app-name">Binance / Coinbase</div>
            <div class="invest-app-role">Crypto Investing</div>
          </div>
          <span class="invest-risk high">High Risk</span>
        </div>
        <table class="invest-table">
          <tr><td>Binance: 350+ coins, lowest fees (0.1%), largest liquidity</td></tr>
          <tr><td>Coinbase: US-regulated, 250+ coins, beginner friendly</td></tr>
          <tr><td>Both support BTC, ETH, and major altcoins</td></tr>
          <tr><td>Built-in alerts and price notifications</td></tr>
          <tr><td>⚠️ Always use hardware wallet for large holdings</td></tr>
        </table>
        <p class="invest-verdict">✅ <strong>Best for:</strong> Crypto. Use Binance for range &amp; fees; Coinbase for simplicity &amp; regulation.</p>
      </div>

      <div class="invest-app-card">
        <div class="invest-app-header">
          <span class="invest-app-icon">🗂</span>
          <div>
            <div class="invest-app-name">Delta / Stock Events</div>
            <div class="invest-app-role">Portfolio Tracker</div>
          </div>
          <span class="invest-risk low">Free / Premium</span>
        </div>
        <table class="invest-table">
          <tr><td>Track stocks, ETFs, crypto in one portfolio</td></tr>
          <tr><td>Real-time P&amp;L, allocation charts</td></tr>
          <tr><td>Stock Events: earnings calendar, dividends</td></tr>
          <tr><td>Sync with brokers via read-only API</td></tr>
          <tr><td>No trading — pure tracking</td></tr>
        </table>
        <p class="invest-verdict">✅ <strong>Best for:</strong> Monitoring your full portfolio in one view across multiple brokers.</p>
      </div>

      <div class="invest-app-card">
        <div class="invest-app-header">
          <span class="invest-app-icon">📰</span>
          <div>
            <div class="invest-app-name">Bloomberg / Seeking Alpha</div>
            <div class="invest-app-role">Financial News &amp; Research</div>
          </div>
          <span class="invest-risk low">Free / Paid</span>
        </div>
        <table class="invest-table">
          <tr><td>Bloomberg: best real-time macro + breaking news (free tier)</td></tr>
          <tr><td>Seeking Alpha: deep stock analysis, earnings previews</td></tr>
          <tr><td>Both available globally</td></tr>
          <tr><td>Premium tiers unlock analyst ratings &amp; quant scores</td></tr>
        </table>
        <p class="invest-verdict">✅ <strong>Best for:</strong> Daily news feed. Bloomberg for macro; Seeking Alpha for stock deep-dives.</p>
      </div>

    </div>

    <h3 class="invest-apps-title" style="margin-top:24px">Automation Workflow</h3>
    <div class="invest-workflow">
      <div class="invest-workflow-step">
        <span class="invest-step-num">1</span>
        <div><strong>Market Data</strong><br><span class="muted small">TradingView price alerts → Telegram/email</span></div>
      </div>
      <div class="invest-workflow-arrow">→</div>
      <div class="invest-workflow-step">
        <span class="invest-step-num">2</span>
        <div><strong>Analysis</strong><br><span class="muted small">Ask this analyst "Daily Briefing"</span></div>
      </div>
      <div class="invest-workflow-arrow">→</div>
      <div class="invest-workflow-step">
        <span class="invest-step-num">3</span>
        <div><strong>Risk Check</strong><br><span class="muted small">Run Investment Decision Checklist</span></div>
      </div>
      <div class="invest-workflow-arrow">→</div>
      <div class="invest-workflow-step">
        <span class="invest-step-num">4</span>
        <div><strong>Execute</strong><br><span class="muted small">IBKR or Binance — manual only</span></div>
      </div>
      <div class="invest-workflow-arrow">→</div>
      <div class="invest-workflow-step">
        <span class="invest-step-num">5</span>
        <div><strong>Track</strong><br><span class="muted small">Delta portfolio tracker</span></div>
      </div>
    </div>
  `;
}

function investSection(title, content) {
  return `
    <div class="invest-section">
      <div class="invest-section-head" onclick="this.parentElement.classList.toggle('open')">
        <span>${title}</span>
        <span class="invest-chevron">▼</span>
      </div>
      <div class="invest-section-body">${content}</div>
    </div>
  `;
}


/* ═══════════════════ MOBILE TAB SWITCHING ═══════════════════ */

/* ══════════════════════ MOBILE TAB SWITCHING ══════════════════════ */

/* ── Floating chat popup ── */
function toggleChatPopup() {
  var popup  = document.getElementById('chatPopup');
  var bubble = document.getElementById('chatBubble');
  var badge  = document.getElementById('chatBubbleBadge');
  var isOpen = !popup.classList.contains('hidden');
  popup.classList.toggle('hidden', isOpen);
  bubble.classList.toggle('open', !isOpen);
  // Clear unread badge on open
  if (!isOpen) {
    badge.classList.add('hidden');
    badge.textContent = '';
    // Scroll log to bottom
    var log = document.getElementById('chatLog');
    if (log) log.scrollTop = log.scrollHeight;
  }
}

function openChatPopup() {
  var popup = document.getElementById('chatPopup');
  if (popup.classList.contains('hidden')) toggleChatPopup();
}

// Show unread badge on bubble when analyst sends a message while popup is closed
function _notifyChatBubble() {
  var popup = document.getElementById('chatPopup');
  if (!popup || !popup.classList.contains('hidden')) return;
  var badge = document.getElementById('chatBubbleBadge');
  badge.classList.remove('hidden');
  var n = parseInt(badge.textContent || '0') + 1;
  badge.textContent = n > 9 ? '9+' : String(n);
}

function switchMobileTab(tab) {
  document.querySelectorAll('.mobile-tab').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });
  var paneMatches  = document.getElementById('paneMatches');
  var paneQuiniela = document.getElementById('paneQuiniela');
  paneMatches.classList.toggle('mobile-active',  tab === 'matches');
  paneQuiniela.classList.toggle('mobile-active', tab === 'quiniela');
  if (tab === 'quiniela' && !_qState.loaded) loadQuiniela(false);
}

/* ══════════════════════ QUINIELA STATE ══════════════════════ */

var _qState = {
  loaded: false,
  groups: [],       // from /api/standings (includes fixtures)
  analysis: {},     // groupName -> { pick1, pick2, conf1, conf2, odd1, odd2, dark_horse, bet_tip }
  champion: null,   // champion prediction result
  champLoading: false,
};

/* ══════════════════════ OPEN / CLOSE ══════════════════════ */

function openQuiniela() {
  if (window.innerWidth <= 700) {
    switchMobileTab('quiniela');
  } else {
    document.getElementById('quinielaModal').classList.remove('hidden');
    document.body.style.overflow = 'hidden';
    if (!_qState.loaded) loadQuiniela(false);
    else renderAllContainers();
  }
}
function closeQuiniela() {
  document.getElementById('quinielaModal').classList.add('hidden');
  document.body.style.overflow = '';
}

/* ══════════════════════ LOAD ══════════════════════ */

async function loadQuiniela(forceRefresh) {
  if (forceRefresh) { _qState.loaded = false; _qState.analysis = {}; }
  setQLoading(true);

  try {
    var res = await fetch('/api/standings');
    var data = await res.json();
    if (data.error) throw new Error(data.error);
    _qState.groups = data.groups || [];
  } catch(e) {
    setQError('Error cargando datos: ' + e.message);
    return;
  }

  // Phase 1: instant math-based predictions
  computeQPicks(_qState.groups);
  _qState.loaded = true;
  renderAllContainers();

  // Phase 2: AI enrichment (dark_horse, bet_tip) — re-render when done
  enrichQWithAI(_qState.groups).then(function() { renderAllContainers(); });
}

function setQLoading(on) {
  var c1 = document.getElementById('quinielaGroups');
  var c2 = document.getElementById('quinielaGroupsModal');
  var msg = '<div class="q-loading-msg">Cargando grupos y partidos del Mundial 2026...</div>';
  if (on) {
    if (c1) c1.innerHTML = msg;
    if (c2) c2.innerHTML = msg;
  }
}
function setQError(msg) {
  var html = '<p class="muted small" style="padding:16px">' + msg + ' <button class="ghost-btn" onclick="loadQuiniela(true)">Reintentar</button></p>';
  var c1 = document.getElementById('quinielaGroups');
  var c2 = document.getElementById('quinielaGroupsModal');
  if (c1) c1.innerHTML = html;
  if (c2) c2.innerHTML = html;
}

/* ══════════════════════ MATH PICKS + MATCH PREDICTIONS ══════════════════════ */

// Team strength score: weights pts, GD, GF, win rate
function _teamStrength(t) {
  var pts = parseInt(t.pts) || 0;
  var gd  = parseFloat(t.gd) || 0;
  var gf  = parseFloat(t.gf) || 0;
  var gp  = parseInt(t.gp) || 1;
  var w   = parseInt(t.w) || 0;
  var winRate = w / gp;
  return pts * 4 + gd * 2 + gf * 0.5 + winRate * 6;
}

// Win probability from strength ratio (logistic-style)
function _winProb(sHome, sAway) {
  var diff = sHome - sAway;
  return Math.round(Math.min(Math.max(50 + diff * 3.5, 22), 78));
}

function _genWhyQualify(pick1, pick2, dark_horse, sorted) {
  var t1 = sorted.find(function(t){return t.name===pick1;}) || sorted[0] || {};
  var t2 = sorted.find(function(t){return t.name===pick2;}) || sorted[1] || {};
  var pts1 = parseInt(t1.pts)||0, gd1 = parseFloat(t1.gd)||0;
  var pts2 = parseInt(t2.pts)||0, gd2 = parseFloat(t2.gd)||0;
  var gp  = parseInt(t1.gp)||0;
  if (gp === 0) {
    return pick1 + ' y ' + pick2 + ' son favoritos historicos del grupo — el torneo aun no ha comenzado para este grupo.';
  }
  var parts = [];
  if (pts1 > 0) parts.push(pick1 + ' lidera con ' + pts1 + ' pts' + (gd1 > 0 ? ' y DG ' + (gd1>0?'+':'') + gd1:''));
  if (pts2 > 0 && pts2 >= pts1-3) parts.push(pick2 + ' sigue firme con ' + pts2 + ' pts' + (gd2!==0?' (DG '+(gd2>0?'+':'')+gd2+')':''));
  if (dark_horse && sorted[2]) {
    var t3 = sorted[2]; var g3 = parseInt(t3.gp)||0; var p3 = parseInt(t3.pts)||0;
    if (g3>0 && p3<pts2) parts.push(dark_horse + ' queda con ' + (3-g3) + ' partidos para remontar');
  }
  return parts.length ? parts.join('. ') + '.' : pick1 + ' y ' + pick2 + ' clasifican segun estadisticas actuales.';
}

function _genMatchPredictions(fixtures, teamMap) {
  return (fixtures || []).filter(function(f){return f.status !== 'Finished';}).map(function(f) {
    var th = teamMap[f.home] || {pts:0,gd:0,gf:0,gp:0,w:0,d:0,l:0};
    var ta = teamMap[f.away] || {pts:0,gd:0,gf:0,gp:0,w:0,d:0,l:0};
    var sh = _teamStrength(th);
    var sa = _teamStrength(ta);
    var adjHome = sh + 1.5; // slight WC neutral-venue home boost
    var pHome = _winProb(adjHome, sa);
    var pAway = _winProb(sa, adjHome);
    var pDraw = 100 - pHome - pAway;
    if (pDraw < 10) { var excess = 10-pDraw; pDraw=10; if(pHome>pAway){pHome-=excess;}else{pAway-=excess;} }

    var stronger = pHome >= pAway ? f.home : f.away;
    var weaker   = pHome >= pAway ? f.away : f.home;
    var pWin = Math.max(pHome, pAway);
    var strDiff = Math.abs(sh - sa);
    // Expected goals from strength
    var expGH = Math.max(0.5, Math.round((1.3 + strDiff * 0.10) * 10) / 10);
    var expGA = Math.max(0.3, Math.round((0.9 - strDiff * 0.07) * 10) / 10);
    var expTotal = expGH + expGA;
    var hGoals = Math.round(pHome >= 50 ? expGH : expGA);
    var aGoals = Math.round(pHome >= 50 ? expGA : expGH);
    var predicted_score = hGoals + '-' + aGoals;
    var prediction, confidence, reasoning;
    if (pHome >= 50) {
      prediction = 'Victoria ' + f.home; confidence = pHome;
      reasoning = f.home + ' domina con mejor forma (str ' + sh.toFixed(1) + ' vs ' + sa.toFixed(1) + '). Favorito claro.';
    } else if (pAway >= 50) {
      prediction = 'Victoria ' + f.away; confidence = pAway;
      reasoning = f.away + ' llega superior (str ' + sa.toFixed(1) + ' vs ' + sh.toFixed(1) + '). Ventaja estadistica.';
    } else {
      prediction = 'Empate probable'; confidence = pDraw; predicted_score = '1-1';
      reasoning = 'Equipos muy parejos (str ' + sh.toFixed(1) + ' vs ' + sa.toFixed(1) + '). Partido abierto.';
    }

    // ── 3 SECURE BETS (low risk, ~55-75% confidence) ──────────────────
    var secure = [];
    // 1. Doble oportunidad for the stronger side
    var dcOdd = (1 / (Math.min(pWin + pDraw, 85) / 100)).toFixed(2);
    secure.push({ label: stronger + ' o empate (DC)', odd: dcOdd, why: 'Doble oportunidad — elimina el riesgo de derrota del favorito' });
    // 2. Over 1.5 goals — almost always hits in WC groups
    var p15 = Math.min(Math.round(60 + strDiff * 3), 82);
    secure.push({ label: 'Mas de 1.5 goles', odd: (1/(p15/100)).toFixed(2), why: 'Grupos del Mundial tienen alta tasa de goles' });
    // 3. Stronger team anota (team to score)
    var pScore = Math.min(Math.round(68 + strDiff * 2.5), 88);
    secure.push({ label: stronger + ' anota', odd: (1/(pScore/100)).toFixed(2), why: 'Equipo superior casi siempre marca en la fase de grupos' });

    // ── 3 RISKY BETS (high reward, ~25-45% probability) ───────────────
    var risky = [];
    // 1. Correct score
    var csOdd = (6.5 + Math.random() * 3).toFixed(2);
    risky.push({ label: 'Marcador exacto ' + predicted_score, odd: csOdd, why: 'Alto pago si el marcador predicho se cumple' });
    // 2. Corners over 6.5 — high-press teams generate corners
    var cornersOdd = (1.75 + Math.random() * 0.35).toFixed(2);
    risky.push({ label: 'Mas de 6.5 corners', odd: cornersOdd, why: 'Partidos de grupos con equipos presionantes generan 8-11 corners' });
    // 3. Both teams to score OR weaker team wins (based on strDiff)
    if (strDiff < 4) {
      var bttsP = Math.round(45 + strDiff); var bttsOdd = (1/(bttsP/100)).toFixed(2);
      risky.push({ label: 'Ambos equipos anotan', odd: bttsOdd, why: 'Equipos parejos — probable que ambos lleguen al gol' });
    } else {
      var upsetP = Math.round(28 - strDiff * 0.5); var upsetOdd = (1/(Math.max(upsetP,18)/100)).toFixed(2);
      risky.push({ label: 'Victoria ' + weaker + ' (sorpresa)', odd: upsetOdd, why: 'Cuota alta si el menor da la sorpresa' });
    }

    // ── COMBO (parlay 3 picks, multiply odds ~0.85 juice) ─────────────
    var comboLegs = [
      stronger + ' o empate',
      'Mas de 1.5 goles',
      'Mas de 6.5 corners'
    ];
    var comboOdd = (parseFloat(dcOdd) * parseFloat((1/(p15/100)).toFixed(2)) * parseFloat(cornersOdd) * 0.85).toFixed(2);
    var combo = { legs: comboLegs, odd: comboOdd, why: 'Combinada de 3 — seguridad + corneres altos + resultado probable' };

    return { home: f.home, away: f.away, prediction: prediction, predicted_score: predicted_score,
             confidence: confidence, reasoning: reasoning,
             secure: secure, risky: risky, combo: combo };
  });
}

function computeQPicks(groups) {
  groups.forEach(function(g) {
    var sorted = g.teams.slice().sort(function(a, b) {
      var dp = parseInt(b.pts) - parseInt(a.pts);
      if (dp !== 0) return dp;
      var dd = parseFloat(b.gd) - parseFloat(a.gd);
      if (dd !== 0) return dd;
      return parseFloat(b.gf) - parseFloat(a.gf);
    });
    var gp0 = parseInt(sorted[0] ? sorted[0].gp : 0) || 0;
    var progress = Math.min(gp0 / 3, 1);
    var gap01 = parseInt(sorted[0] ? sorted[0].pts : 0) - parseInt(sorted[1] ? sorted[1].pts : 0);
    var gap12 = parseInt(sorted[1] ? sorted[1].pts : 0) - parseInt(sorted[2] ? sorted[2].pts : 0);
    var c1 = Math.min(Math.max(Math.round(55 + progress * Math.min(gap01 * 10, 38)), 40), 96);
    var c2 = Math.min(Math.max(Math.round(48 + progress * Math.min(gap12 * 8, 28)), 28), 85);
    var pick1 = sorted[0] ? sorted[0].name : '?';
    var pick2 = sorted[1] ? sorted[1].name : '?';
    var dark_horse = sorted[2] ? sorted[2].name : null;

    // Build team lookup map for match predictions
    var teamMap = {};
    g.teams.forEach(function(t) { teamMap[t.name] = t; });

    _qState.analysis[g.name] = {
      pick1: pick1,
      pick2: pick2,
      conf1: c1,
      conf2: c2,
      odd1: (1 / (c1 / 100)).toFixed(2),
      odd2: (1 / (c2 / 100)).toFixed(2),
      dark_horse: dark_horse,
      dark_horse_why: dark_horse ? _genDarkHorseWhy(sorted[2], sorted) : null,
      why_qualify: _genWhyQualify(pick1, pick2, dark_horse, sorted),
      matchPredictions: _genMatchPredictions(g.fixtures, teamMap),
    };
  });
}

function _genDarkHorseWhy(t, sorted) {
  if (!t) return null;
  var pts = parseInt(t.pts)||0; var gp = parseInt(t.gp)||0; var gf = parseFloat(t.gf)||0;
  if (gp === 0) return 'Aun sin jugar — potencial de sorpresa en el debut.';
  var remaining = 3 - gp;
  if (pts > 0) return 'Con ' + pts + 'pts y ' + remaining + ' partidos restantes, puede remontar si los lideres tropiezan.';
  if (gf > 0) return 'Ha anotado ' + gf + ' goles — capacidad ofensiva para dar la sorpresa.';
  return 'Equipo peligroso con ' + remaining + ' partidos restantes.';
}

/* ══════════════════════ AI ENRICHMENT ══════════════════════ */

async function enrichQWithAI(groups) {
  // Enrich in batches of 4 groups to keep prompt size manageable
  var batchSize = 4;
  for (var bi = 0; bi < groups.length; bi += batchSize) {
    var batch = groups.slice(bi, bi + batchSize);
    await _enrichBatch(batch);
    renderAllContainers(); // show partial results as they arrive
  }
}

async function _enrichBatch(batch) {
  try {
    var groupData = batch.map(function(g) {
      var a = _qState.analysis[g.name] || {};
      var standings = g.teams.map(function(t) {
        return t.name + '(' + t.pts + 'pts ' + t.w + 'W' + t.d + 'D' + t.l + 'L gd:' + t.gd + ')';
      }).join(', ');
      var played = (g.fixtures || []).filter(function(f) { return f.status === 'Finished'; });
      var upcoming = (g.fixtures || []).filter(function(f) { return f.status === 'Scheduled' || f.status === 'Live'; });
      var results = played.map(function(f) {
        return f.home + ' ' + (f.scoreHome || '?') + '-' + (f.scoreAway || '?') + ' ' + f.away;
      }).join('; ');
      var next = upcoming.map(function(f) { return f.home + ' vs ' + f.away; }).join('; ');
      return g.name + ' | Standings: ' + standings
        + (results ? ' | Results: ' + results : '')
        + (next ? ' | Upcoming: ' + next : '');
    }).join('\n');

    var prompt = 'Eres analista elite del Mundial 2026. Datos reales de los grupos:\n' + groupData
      + '\n\nPara CADA grupo devuelve analisis completo en JSON EXACTO (sin texto extra):\n'
      + '{"groups":[{'
      + '"group":"Group X",'
      + '"why_qualify":"razon concisa 1-2 frases por que los 2 lideres clasificaran (menciona forma actual, estadisticas, rivales pendientes)",'
      + '"dark_horse":"equipo con posibilidad de sorpresa",'
      + '"dark_horse_why":"por que podria sorprender en 1 frase",'
      + '"matches":[{'
      + '"home":"equipo","away":"equipo",'
      + '"prediction":"quien gana o empate",'
      + '"predicted_score":"ej 2-1",'
      + '"confidence":75,'
      + '"best_bet":"apuesta de mayor valor con cuota estimada ej: Mexico -0.5 AH @1.85",'
      + '"risk_bet":"apuesta de mayor riesgo/pago ej: Ambos marcan @2.10",'
      + '"reasoning":"1 frase explicando por que esta prediccion"'
      + '}]'
      + '}]}';

    var r = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: prompt, history: [], matches: [], date: state.date, lang: 'es'})
    });
    var d = await r.json();
    var reply = d.reply || '';
    if (reply.indexOf('API') >= 0 || reply.indexOf('clave') >= 0 || reply.indexOf('Anthropic') >= 0) return;
    var m = reply.match(/\{[\s\S]*"groups"[\s\S]*\}/);
    if (!m) return;
    var parsed = JSON.parse(m[0]);
    (parsed.groups || []).forEach(function(g) {
      if (!_qState.analysis[g.group]) return;
      var a = _qState.analysis[g.group];
      if (g.dark_horse) a.dark_horse = g.dark_horse;
      if (g.dark_horse_why) a.dark_horse_why = g.dark_horse_why;
      if (g.why_qualify) a.why_qualify = g.why_qualify;
      if (g.matches) a.matchPredictions = g.matches;
    });
  } catch(e) {}
}

/* ══════════════════════ RENDER ══════════════════════ */

function renderAllContainers() {
  var c1 = document.getElementById('quinielaGroups');
  var c2 = document.getElementById('quinielaGroupsModal');
  if (c1) { c1.innerHTML = ''; buildQContent(c1, false); }
  if (c2) { c2.innerHTML = ''; buildQContent(c2, true); }
}

function buildQContent(container, isModal) {
  // Champion prediction banner
  var champDiv = document.createElement('div');
  champDiv.id = isModal ? 'champBannerModal' : 'champBanner';
  champDiv.className = 'q-champ-banner';
  if (_qState.champion) {
    champDiv.innerHTML = _buildChampHtml(_qState.champion);
  } else {
    champDiv.innerHTML = '<div class="q-champ-loading">🔮 Calculando predicción de campeón…</div>';
    if (!_qState.champLoading) {
      _qState.champLoading = true;
      fetch('/api/champion-prediction').then(function(r){ return r.json(); }).then(function(d) {
        _qState.champion = d;
        _qState.champLoading = false;
        document.querySelectorAll('.q-champ-banner').forEach(function(el) {
          el.innerHTML = _buildChampHtml(d);
        });
      }).catch(function() { _qState.champLoading = false; });
    }
  }
  container.appendChild(champDiv);

  // 3rd-place tracker strip
  var thirdStrip = build3rdPlaceTracker();
  container.appendChild(thirdStrip);
  // Group cards — all expanded by default
  _qState.groups.forEach(function(grp) {
    container.appendChild(buildQGroupCard(grp));
  });
}

function _buildChampHtml(d) {
  if (d.error) return '<div class="q-champ-err">⚠️ ' + escapeHtml(d.error) + '</div>';
  var html = '<div class="q-champ-inner">';
  html += '<div class="q-champ-trophy">🏆</div>';
  html += '<div class="q-champ-content">';
  html += '<div class="q-champ-label">Predicción del modelo · Campeón Mundial 2026</div>';
  html += '<div class="q-champ-name">' + escapeHtml(d.champion || '?') + '</div>';
  if (d.finalist) {
    html += '<div class="q-champ-sub">Final vs <strong>' + escapeHtml(d.finalist) + '</strong></div>';
  }
  if (d.semi1 || d.semi2) {
    var sf = [d.semi1, d.semi2].filter(Boolean).map(function(t){ return escapeHtml(t); }).join(' · ');
    html += '<div class="q-champ-semis">Semifinalistas: ' + sf + '</div>';
  }
  html += '</div></div>';
  return html;
}

/* ── 3rd-place tracker ── */
function build3rdPlaceTracker() {
  var thirds = _qState.groups.map(function(g) {
    var sorted = g.teams.slice().sort(function(a, b) {
      var dp = parseInt(b.pts) - parseInt(a.pts);
      if (dp !== 0) return dp;
      return parseFloat(b.gd) - parseFloat(a.gd);
    });
    var third = sorted[2];
    return third ? { name: third.name, pts: parseInt(third.pts), gd: parseFloat(third.gd), gf: parseFloat(third.gf), logo: third.logo, group: g.name } : null;
  }).filter(Boolean);

  thirds.sort(function(a, b) {
    if (b.pts !== a.pts) return b.pts - a.pts;
    if (b.gd !== a.gd) return b.gd - a.gd;
    return b.gf - a.gf;
  });

  var strip = document.createElement('div');
  strip.className = 'q-third-strip';
  strip.innerHTML = '<div class="q-third-title">Carrera por los mejores 3ros — 8 clasifican</div>';
  var list = document.createElement('div');
  list.className = 'q-third-list';
  thirds.forEach(function(t, i) {
    var isIn = i < 8;
    var flag = t.logo ? '<img class="qs-flag" src="' + t.logo + '" alt="" loading="lazy">' : '';
    var item = document.createElement('div');
    item.className = 'q-third-item' + (isIn ? ' q-third-in' : ' q-third-out');
    item.innerHTML = (isIn ? '<span class="q-third-rank">' + (i+1) + '</span>' : '<span class="q-third-rank q-third-rank-out">' + (i+1) + '</span>')
      + flag
      + '<span class="q-third-name">' + t.name + '</span>'
      + '<span class="q-third-pts">' + t.pts + 'pts</span>'
      + '<span class="q-third-grp muted small">' + t.group + '</span>';
    list.appendChild(item);
  });
  strip.appendChild(list);
  return strip;
}

/* ── Group card ── */
function buildQGroupCard(grp) {
  var analysis = _qState.analysis[grp.name] || {};
  var fixtures = grp.fixtures || [];
  var played   = fixtures.filter(function(f) { return f.status === 'Finished'; });
  var upcoming = fixtures.filter(function(f) { return f.status === 'Scheduled'; });
  var live     = fixtures.filter(function(f) { return f.status === 'Live'; });

  var card = document.createElement('div');
  card.className = 'qgroup-card';

  // ── Header
  var header = document.createElement('div');
  header.className = 'qgroup-header';
  var liveIndicator = live.length ? '<span class="q-live-dot">LIVE</span>' : '';
  header.innerHTML = '<span class="qgroup-label">' + grp.name + '</span>'
    + liveIndicator
    + '<span class="qgroup-progress">' + played.length + '/6 partidos</span>';
  card.appendChild(header);

  // ── Live match banner (if any)
  live.forEach(function(f) {
    var banner = document.createElement('div');
    banner.className = 'q-live-banner';
    var fh = f.homeLogo ? '<img class="qs-flag" src="' + f.homeLogo + '" alt="">' : '';
    var fa = f.awayLogo ? '<img class="qs-flag" src="' + f.awayLogo + '" alt="">' : '';
    banner.innerHTML = '<span class="q-live-label">EN VIVO</span>'
      + fh + ' <strong>' + f.home + '</strong>'
      + ' <span class="q-score">' + (f.scoreHome || '0') + ' - ' + (f.scoreAway || '0') + '</span>'
      + ' <strong>' + f.away + '</strong> ' + fa;
    card.appendChild(banner);
  });

  // ── Analyst picks
  var picksDiv = document.createElement('div');
  picksDiv.className = 'qanalyst-picks';
  var p1Team = grp.teams.find(function(t) { return t.name === analysis.pick1; }) || {};
  var p2Team = grp.teams.find(function(t) { return t.name === analysis.pick2; }) || {};
  var f1 = p1Team.logo ? '<img class="qpick-flag" src="' + p1Team.logo + '" alt="">' : '';
  var f2 = p2Team.logo ? '<img class="qpick-flag" src="' + p2Team.logo + '" alt="">' : '';

  picksDiv.innerHTML = '<div class="qanalyst-title">Analista recomienda clasificar</div>'
    + '<div class="qpick-row"><span class="qpick-pos qpick-pos-1">1&#xB0;</span>' + f1
    + '<span class="qpick-name">' + (analysis.pick1 || '...') + '</span>'
    + '<span class="qpick-conf">' + (analysis.conf1 || '?') + '%</span>'
    + '<span class="qpick-odd">~' + (analysis.odd1 || '?') + '</span></div>'
    + '<div class="qpick-row"><span class="qpick-pos qpick-pos-2">2&#xB0;</span>' + f2
    + '<span class="qpick-name">' + (analysis.pick2 || '...') + '</span>'
    + '<span class="qpick-conf">' + (analysis.conf2 || '?') + '%</span>'
    + '<span class="qpick-odd">~' + (analysis.odd2 || '?') + '</span></div>'
    + (analysis.why_qualify ? '<div class="q-why-qualify">&#x1F4AC; ' + analysis.why_qualify + '</div>' : '')
    + (analysis.dark_horse ? '<div class="q-dark-horse">&#x1F525; Dark horse: <strong>' + analysis.dark_horse + '</strong>'
        + (analysis.dark_horse_why ? ' — <span class="q-dh-why">' + analysis.dark_horse_why + '</span>' : '') + '</div>' : '');
  card.appendChild(picksDiv);

  // ── Results (played matches)
  if (played.length) {
    var resultsDiv = document.createElement('div');
    resultsDiv.className = 'q-fixtures q-results';
    resultsDiv.innerHTML = '<div class="q-fix-title">Resultados</div>';
    played.forEach(function(f) {
      resultsDiv.appendChild(buildFixtureRow(f, true, null));
    });
    card.appendChild(resultsDiv);
  }

  // ── Upcoming fixtures with predictions
  if (upcoming.length) {
    var upcomingDiv = document.createElement('div');
    upcomingDiv.className = 'q-fixtures q-upcoming';
    upcomingDiv.innerHTML = '<div class="q-fix-title">Prox. partidos &amp; pronstico</div>';
    var preds = analysis.matchPredictions || [];
    upcoming.forEach(function(f) {
      var pred = preds.find(function(p) {
        return p.home === f.home && p.away === f.away;
      }) || null;
      upcomingDiv.appendChild(buildFixtureRow(f, false, pred));
    });
    card.appendChild(upcomingDiv);
  }

  // ── Standings table
  var tableWrap = document.createElement('div');
  tableWrap.className = 'qstandings-wrap';
  var table = document.createElement('table');
  table.className = 'qstandings-table';
  table.innerHTML = '<thead><tr>'
    + '<th style="text-align:left;padding-left:12px">Equipo</th>'
    + '<th>PJ</th><th>G</th><th>E</th><th>P</th><th>DG</th><th>Pts</th>'
    + '</tr></thead>';
  var tbody = document.createElement('tbody');
  grp.teams.forEach(function(team, rank) {
    var isP1 = team.name === analysis.pick1;
    var isP2 = team.name === analysis.pick2;
    var rowClass = isP1 ? 'qs-qualify-1' : isP2 ? 'qs-qualify-2' : '';
    var gdNum = parseFloat(team.gd);
    var gdClass = gdNum > 0 ? 'qs-gd-pos' : gdNum < 0 ? 'qs-gd-neg' : '';
    var flag = team.logo ? '<img class="qs-flag" src="' + team.logo + '" alt="" loading="lazy">' : '';
    // Qualification status badge
    var qualBadge = isP1 ? '<span class="q-qual-badge q-qual-1">1&#xB0;</span>'
      : isP2 ? '<span class="q-qual-badge q-qual-2">2&#xB0;</span>' : '';
    var tr = document.createElement('tr');
    if (rowClass) tr.className = rowClass;
    tr.innerHTML = '<td><div class="qs-team-cell">' + flag
      + '<span class="qs-name">' + team.name + qualBadge + '</span></div></td>'
      + '<td>' + team.gp + '</td>'
      + '<td>' + team.w + '</td>'
      + '<td>' + team.d + '</td>'
      + '<td>' + team.l + '</td>'
      + '<td class="' + gdClass + '">' + team.gd + '</td>'
      + '<td class="qs-pts">' + team.pts + '</td>';
    tbody.appendChild(tr);
  });
  table.appendChild(tbody);
  tableWrap.appendChild(table);
  card.appendChild(tableWrap);
  return card;
}

function buildFixtureRow(f, isResult, pred) {
  var wrap = document.createElement('div');
  wrap.className = 'q-fix-wrap';

  var row = document.createElement('div');
  row.className = 'q-fix-row';
  var fh = f.homeLogo ? '<img class="qs-flag" src="' + f.homeLogo + '" alt="" loading="lazy">' : '';
  var fa = f.awayLogo ? '<img class="qs-flag" src="' + f.awayLogo + '" alt="" loading="lazy">' : '';
  var dateStr = '';
  if (f.kickoff) {
    var dt = new Date(f.kickoff);
    dateStr = dt.toLocaleDateString('es', {month:'short', day:'numeric'})
      + ' ' + dt.toLocaleTimeString('es', {hour:'2-digit', minute:'2-digit'});
  }
  if (isResult) {
    row.innerHTML = fh + '<span class="q-fix-team">' + f.home + '</span>'
      + '<span class="q-fix-score">' + (f.scoreHome || '0') + ' - ' + (f.scoreAway || '0') + '</span>'
      + '<span class="q-fix-team q-fix-team-r">' + f.away + '</span>' + fa;
  } else {
    var confBadge = pred && pred.confidence ? '<span class="q-pred-conf">' + pred.confidence + '%</span>' : '';
    var predScore = pred && pred.predicted_score ? '<span class="q-pred-score">' + pred.predicted_score + '</span>' : '';
    row.innerHTML = fh + '<span class="q-fix-team">' + f.home + '</span>'
      + '<span class="q-fix-vs">vs</span>'
      + '<span class="q-fix-team q-fix-team-r">' + f.away + '</span>' + fa
      + '<span class="q-fix-date">' + dateStr + '</span>'
      + confBadge + predScore;
  }
  wrap.appendChild(row);

  // Prediction + bet slip for upcoming matches
  if (!isResult && pred) {
    var details = document.createElement('div');
    details.className = 'q-pred-details';
    var html = '';
    if (pred.prediction) {
      html += '<div class="q-pred-winner">&#x1F3AF; <strong>' + pred.prediction + '</strong>'
        + (pred.predicted_score ? ' &nbsp;<span class="q-pred-score">' + pred.predicted_score + '</span>' : '')
        + (pred.confidence ? ' &nbsp;<span class="q-pred-conf">' + pred.confidence + '%</span>' : '')
        + '</div>';
    }
    if (pred.reasoning) html += '<div class="q-pred-reason">' + pred.reasoning + '</div>';
    details.innerHTML = html;
    wrap.appendChild(details);
  }
  return wrap;
}

/* ══════════════════════ LIVE ANALYST TRACKER ══════════════════════ */

var liveTracker = { prev: {}, timer: null, fired: {} };

function _matchKey(m) { return m.home + '|' + m.away + '|' + (m.kickoffUtc || ''); }

function startLiveTracker() {
  if (liveTracker.timer) clearInterval(liveTracker.timer);
  liveTracker.timer = setInterval(checkLiveChanges, 55000);
}

async function checkLiveChanges() {
  var matches = state.matches || [];
  if (!matches.some(function(m) { return m.status === 'Live' || m.status === 'Scheduled'; })) return;
  try {
    var tz = Intl.DateTimeFormat().resolvedOptions().timeZone;
    var res = await fetch('/api/matches?date=' + state.date + '&scope=' + state.scope + '&tz=' + encodeURIComponent(tz));
    var data = await res.json();
    var fresh = data.matches || [];
    var changed = [];
    fresh.forEach(function(m) {
      var key = _matchKey(m);
      var scoreStr = (m.scoreHome != null ? m.scoreHome : '') + ':' + (m.scoreAway != null ? m.scoreAway : '');
      var prev = liveTracker.prev[key];
      if (!prev) { liveTracker.prev[key] = {score: scoreStr, status: m.status}; return; }
      if (prev.status !== m.status || prev.score !== scoreStr) {
        changed.push({match: m, prevStatus: prev.status, prevScore: prev.score});
        liveTracker.prev[key] = {score: scoreStr, status: m.status};
      }
    });
    state.matches = fresh;
    renderMatches(fresh);
    for (var i = 0; i < changed.length; i++) {
      var ch = changed[i]; var m = ch.match;
      var scoreStr = (m.scoreHome != null ? m.scoreHome : '?') + ':' + (m.scoreAway != null ? m.scoreAway : '?');
      var isGoal = ch.prevScore !== scoreStr && m.status === 'Live';
      var isKickoff = ch.prevStatus === 'Scheduled' && m.status === 'Live';
      var isFT = m.status === 'Finished' && ch.prevStatus === 'Live';
      if (isGoal || isKickoff || isFT) {
        // Dedup: only fire each event type once per match per session
        var eventKey = key + '|' + (isKickoff ? 'ko' : isFT ? 'ft' : 'g' + scoreStr);
        if (liveTracker.fired[eventKey]) continue;
        liveTracker.fired[eventKey] = true;
        if (isFT) saveLiveResult(m);
        if (isGoal || isFT) loadQuiniela(true);
        await triggerLiveAnalystUpdate(m, {isGoal: isGoal, isKickoff: isKickoff, isFT: isFT});
      }
    }
  } catch(e) {}
}

async function triggerLiveAnalystUpdate(m, flags) {
  var scoreStr = (m.scoreHome != null ? m.scoreHome : '?') + ':' + (m.scoreAway != null ? m.scoreAway : '?');
  var event = flags.isKickoff ? 'Inicio: ' + m.home + ' vs ' + m.away
    : flags.isFT ? 'Final: ' + m.home + ' ' + scoreStr + ' ' + m.away
    : 'Gol: ' + m.home + ' ' + scoreStr + ' ' + m.away + ' (min. ' + (m.minute || '?') + ')';

  var prompt = '[ALERTA EN VIVO] ' + event
    + '\nMarcador: ' + m.home + ' ' + scoreStr + ' ' + m.away + ', min. ' + (m.minute || '-')
    + '\n1. Probabilidades actualizadas del resultado final'
    + '\n2. Apuestas EN VIVO con valor'
    + '\n3. Cuotas justas estimadas ahora'
    + '\n4. Expectativa tactica proximos minutos'
    + '\nMaximo 4 puntos concisos.';

  openChatPopup();
  var log = $('chatLog');
  var divider = document.createElement('div');
  divider.className = 'msg assistant live-update-msg';
  divider.innerHTML = '<div class="live-update-label">Alerta en vivo - ' + event + ' - analizando...</div>';
  log.appendChild(divider);
  var bubble = document.createElement('div');
  bubble.className = 'msg assistant';
  log.appendChild(bubble);
  log.scrollTop = log.scrollHeight;
  try {
    var r = await fetch('/api/chat', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: prompt, history: [], matches: state.matches || [], date: state.date, lang: state.lang || 'en'})
    });
    var d = await r.json();
    bubble.innerHTML = renderMarkdown(d.reply || d.error || 'Sin respuesta.');
  } catch(e) { bubble.textContent = 'No se pudo contactar al analista.'; }
  log.scrollTop = log.scrollHeight;
}

function saveLiveResult(m) {
  try {
    var results = JSON.parse(localStorage.getItem('matchResults') || '[]');
    results.push({date: state.date, home: m.home, away: m.away, scoreHome: m.scoreHome, scoreAway: m.scoreAway, ts: Date.now()});
    if (results.length > 200) results.splice(0, results.length - 200);
    localStorage.setItem('matchResults', JSON.stringify(results));
  } catch(e) {}
}

function getRecentResultsContext() {
  try {
    var results = JSON.parse(localStorage.getItem('matchResults') || '[]');
    if (!results.length) return '';
    return '\n\nRESULTADOS RECIENTES: ' + results.slice(-20).map(function(r) {
      return r.home + ' ' + r.scoreHome + '-' + r.scoreAway + ' ' + r.away;
    }).join(', ');
  } catch(e) { return ''; }
}

startLiveTracker();

// ── Live Match Tracker ─────────────────────────────────────────────────────
let _liveInterval = null;

function openLiveModal() {
  document.getElementById('liveModal').classList.remove('hidden');
  loadLiveMatches();
  _liveInterval = setInterval(loadLiveMatches, 60000);
}
function closeLiveModal() {
  document.getElementById('liveModal').classList.add('hidden');
  if (_liveInterval) { clearInterval(_liveInterval); _liveInterval = null; }
}

async function loadLiveMatches() {
  const loading = document.getElementById('liveLoading');
  const list    = document.getElementById('liveMatchList');
  const empty   = document.getElementById('liveEmpty');
  const setup   = document.getElementById('liveSetupBanner');
  const meta    = document.getElementById('liveLastUpdate');

  loading.classList.remove('hidden');
  list.innerHTML = '';
  empty.classList.add('hidden');
  setup.classList.add('hidden');

  try {
    const res  = await fetch('/api/live-scores');
    const data = await res.json();
    loading.classList.add('hidden');

    if (data.error === 'no_key') {
      setup.classList.remove('hidden');
      return;
    }

    const matches = data.matches || [];
    meta.textContent = 'Actualizado: ' + new Date().toLocaleTimeString('es-CR');

    if (matches.length === 0) {
      empty.classList.remove('hidden');
      return;
    }

    matches.forEach(m => {
      list.insertAdjacentHTML('beforeend', renderLiveMatch(m));
    });
  } catch (e) {
    loading.innerHTML = '<span style="color:#f87171">Error al cargar datos en vivo</span>';
  }
}

function renderLiveMatch(m) {
  const hg = m.home_goals ?? '–';
  const ag = m.away_goals ?? '–';
  const min = m.minute ? m.minute + "'" : m.status || '–';
  const st  = m.stats || {};
  const hs  = st.home || {};
  const as_ = st.away || {};

  const poss_h = parseInt(hs['Ball Possession']) || 50;
  const poss_a = 100 - poss_h;
  const shots_h = hs['Total Shots'] ?? '–';
  const shots_a = as_['Total Shots'] ?? '–';
  const att_h   = hs['Total attacks'] ?? hs['Attacks'] ?? '–';
  const att_a   = as_['Total attacks'] ?? as_['Attacks'] ?? '–';
  const danger_h= hs['Dangerous Attacks'] ?? '–';
  const danger_a= as_['Dangerous Attacks'] ?? '–';

  const eventsHtml = (m.events || []).slice(-5).reverse().map(ev => {
    const isHome = ev.team_id === m.home_id;
    const icon = ev.type === 'Goal' ? '⚽' : ev.type === 'Card' ? (ev.detail === 'Red Card' ? '🟥' : '🟨') : ev.type === 'subst' ? '🔄' : '•';
    return `<div class="live-event ${isHome ? 'live-event-home' : 'live-event-away'}">
      <span class="live-ev-min">${ev.minute || ''}′</span>
      <span class="live-ev-icon">${icon}</span>
      <span class="live-ev-player">${escapeHtml(ev.player || ev.detail || '')}</span>
    </div>`;
  }).join('');

  return `<div class="live-match-card">
    <div class="live-match-header">
      <span class="live-league">${escapeHtml(m.league || m.country || '')}</span>
      <span class="live-minute-badge">${escapeHtml(String(min))}</span>
    </div>
    <div class="live-scoreline">
      <div class="live-team live-team-home">
        ${m.home_logo ? `<img src="${m.home_logo}" class="live-team-logo" alt="">` : ''}
        <span class="live-team-name">${escapeHtml(m.home || '')}</span>
      </div>
      <div class="live-score">${hg} <span class="live-score-sep">–</span> ${ag}</div>
      <div class="live-team live-team-away">
        <span class="live-team-name">${escapeHtml(m.away || '')}</span>
        ${m.away_logo ? `<img src="${m.away_logo}" class="live-team-logo" alt="">` : ''}
      </div>
    </div>
    <div class="live-stats-grid">
      <div class="live-stat-row live-possession">
        <span class="live-stat-val-left">${poss_h}%</span>
        <div class="live-poss-bar">
          <div class="live-poss-fill" style="width:${poss_h}%"></div>
        </div>
        <span class="live-stat-val-right">${poss_a}%</span>
        <span class="live-stat-label">Posesión</span>
      </div>
      <div class="live-stat-row">
        <span class="live-stat-val-left">${shots_h}</span>
        <span class="live-stat-label">Remates</span>
        <span class="live-stat-val-right">${shots_a}</span>
      </div>
      <div class="live-stat-row">
        <span class="live-stat-val-left">${att_h}</span>
        <span class="live-stat-label">Ataques</span>
        <span class="live-stat-val-right">${att_a}</span>
      </div>
      <div class="live-stat-row live-danger">
        <span class="live-stat-val-left live-danger-val">${danger_h}</span>
        <span class="live-stat-label">⚡ Peligrosos</span>
        <span class="live-stat-val-right live-danger-val">${danger_a}</span>
      </div>
    </div>
    ${eventsHtml ? `<div class="live-events-feed">${eventsHtml}</div>` : ''}
  </div>`;
}

// ── Apoyo / Support ────────────────────────────────────────────────────────
function openApoyoModal() {
  document.getElementById('apoyoModal').classList.remove('hidden');
  apoyoLoadWall();
}
function closeApoyoModal() {
  document.getElementById('apoyoModal').classList.add('hidden');
}
function apoyoCopy() {
  var num = '85610677';
  var btn = document.getElementById('modalCopyBtn');
  if (navigator.clipboard) {
    navigator.clipboard.writeText(num).then(function() {
      btn.textContent = '✅ Copiado'; btn.classList.add('copied');
      setTimeout(function(){ btn.textContent = '📋 Copiar número'; btn.classList.remove('copied'); }, 2000);
    });
  } else {
    var ta = document.createElement('textarea'); ta.value = num;
    document.body.appendChild(ta); ta.select(); document.execCommand('copy'); document.body.removeChild(ta);
    btn.textContent = '✅ Copiado'; btn.classList.add('copied');
    setTimeout(function(){ btn.textContent = '📋 Copiar número'; btn.classList.remove('copied'); }, 2000);
  }
}
function apoyoSetAmt(v) {
  document.getElementById('apoyoAmount').value = '₡' + parseInt(v).toLocaleString('es-CR');
}
function apoyoSubmit() {
  var name = document.getElementById('apoyoName').value.trim();
  var amount = document.getElementById('apoyoAmount').value.trim();
  var msg = document.getElementById('apoyoMsg').value.trim();
  if (!amount) { alert('Por favor ingresa el monto que enviaste por SINPE.'); return; }
  var btn = document.getElementById('apoyoSubmitBtn');
  btn.disabled = true; btn.textContent = 'Registrando…';
  fetch('/api/supporters', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({name: name, amount: amount, message: msg})
  }).then(function(r){ return r.json(); }).then(function(d) {
    if (d.ok) {
      var suc = document.getElementById('apoyoSuccess');
      suc.classList.remove('hidden');
      document.getElementById('apoyoName').value = '';
      document.getElementById('apoyoAmount').value = '';
      document.getElementById('apoyoMsg').value = '';
      setTimeout(function(){ suc.classList.add('hidden'); }, 4000);
      apoyoLoadWall();
    } else {
      alert('Error: ' + (d.error || 'intenta de nuevo'));
    }
    btn.disabled = false; btn.textContent = 'Registrar mi apoyo →';
  }).catch(function() {
    alert('Error de conexión.'); btn.disabled = false; btn.textContent = 'Registrar mi apoyo →';
  });
}
function apoyoLoadWall() {
  var list = document.getElementById('apoyoWallList');
  if (!list) return;
  list.innerHTML = '<div class="apoyo-wall-empty">Cargando…</div>';
  fetch('/api/supporters').then(function(r){ return r.json(); }).then(function(d) {
    var supporters = (d.supporters || []).slice().reverse();
    if (!supporters.length) {
      list.innerHTML = '<div class="apoyo-wall-empty">Sé el primero en apoyar 💚</div>';
      return;
    }
    list.innerHTML = supporters.map(function(s) {
      var initials = (s.name || 'A').trim().split(' ').map(function(w){ return w[0]; }).join('').toUpperCase().slice(0,2);
      return '<div class="apoyo-wall-item">'
        + '<div class="apoyo-wall-avatar">' + initials + '</div>'
        + '<div style="flex:1;min-width:0">'
        + '<div class="apoyo-wall-name">' + escapeHtml(s.name || 'Anónimo') + '</div>'
        + (s.message ? '<div class="apoyo-wall-msg">"' + escapeHtml(s.message) + '"</div>' : '')
        + '</div>'
        + '<div class="apoyo-wall-amount">' + escapeHtml(s.amount || '') + '</div>'
        + '</div>';
    }).join('');
  }).catch(function() {
    list.innerHTML = '<div class="apoyo-wall-empty">No se pudo cargar.</div>';
  });
}

// ---- Auth ----

function openLoginModal() {
  document.getElementById('loginModal').classList.remove('hidden');
  document.getElementById('loginError').classList.add('hidden');
  document.getElementById('loginError').textContent = '';
}

function closeLoginModal() {
  document.getElementById('loginModal').classList.add('hidden');
}

function switchAuthTab(tab) {
  var isLogin = tab === 'login';
  document.getElementById('authPaneLogin').classList.toggle('hidden', !isLogin);
  document.getElementById('authPaneRegister').classList.toggle('hidden', isLogin);
  document.getElementById('tabLogin').classList.toggle('active', isLogin);
  document.getElementById('tabRegister').classList.toggle('active', !isLogin);
  document.getElementById('loginError').classList.add('hidden');
}

function _showAuthError(msg) {
  var el = document.getElementById('loginError');
  el.textContent = msg;
  el.classList.remove('hidden');
}

async function loginUser() {
  var email = (document.getElementById('loginEmail').value || '').trim();
  var password = (document.getElementById('loginPassword').value || '').trim();
  if (!email || !password) { _showAuthError('Ingresa email y contraseña.'); return; }
  try {
    var r = await fetch('/api/auth/login', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, password})
    });
    var d = await r.json();
    if (d.ok) {
      localStorage.setItem('progol_auth', JSON.stringify({api_key: d.api_key, tier: d.tier, email: d.email}));
      closeLoginModal();
      refreshAuthUI();
    } else {
      _showAuthError(d.error || 'Error al iniciar sesión.');
    }
  } catch(e) { _showAuthError('Error de red.'); }
}

async function registerUser() {
  var email = (document.getElementById('regEmail').value || '').trim();
  var password = (document.getElementById('regPassword').value || '').trim();
  if (!email || !password) { _showAuthError('Ingresa email y contraseña.'); return; }
  try {
    var r = await fetch('/api/auth/register', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({email, password})
    });
    var d = await r.json();
    if (d.ok) {
      // Auto-login after register
      localStorage.setItem('progol_auth', JSON.stringify({api_key: d.api_key, tier: d.tier, email: email}));
      closeLoginModal();
      refreshAuthUI();
    } else {
      _showAuthError(d.error || 'Error al registrarse.');
    }
  } catch(e) { _showAuthError('Error de red.'); }
}

async function checkAuthState() {
  var raw = localStorage.getItem('progol_auth');
  if (!raw) { refreshAuthUI(); return; }
  try {
    var auth = JSON.parse(raw);
    var r = await fetch('/api/auth/me', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({api_key: auth.api_key})
    });
    var d = await r.json();
    if (d.ok) {
      auth.tier = d.tier;
      auth.email = d.email;
      localStorage.setItem('progol_auth', JSON.stringify(auth));
      refreshAuthUI(auth);
    } else {
      localStorage.removeItem('progol_auth');
      refreshAuthUI();
    }
  } catch(e) { refreshAuthUI(); }
}

function refreshAuthUI(auth) {
  if (!auth) {
    try { auth = JSON.parse(localStorage.getItem('progol_auth') || 'null'); } catch(e) {}
  }
  var loginBtn = document.getElementById('loginBtn');
  var userBadge = document.getElementById('userBadge');
  if (!loginBtn || !userBadge) return;
  if (auth && auth.email) {
    loginBtn.classList.add('hidden');
    var short = auth.email.length > 16 ? auth.email.slice(0, 14) + '…' : auth.email;
    var tierClass = 'tier-badge ' + (auth.tier || 'scout');
    userBadge.innerHTML = '<span class="user-badge-email">' + short + '</span><span class="' + tierClass + '">' + (auth.tier || 'scout') + '</span><button class="user-badge-logout" onclick="logoutUser()" title="Cerrar sesión">✕</button>';
    userBadge.classList.remove('hidden');
  } else {
    loginBtn.classList.remove('hidden');
    userBadge.classList.add('hidden');
  }
}

function logoutUser() {
  localStorage.removeItem('progol_auth');
  refreshAuthUI(null);
}

// Wire Enter key on login/register inputs
document.addEventListener('DOMContentLoaded', function() {
  ['loginEmail','loginPassword'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('keydown', function(e) { if (e.key === 'Enter') loginUser(); });
  });
  ['regEmail','regPassword'].forEach(function(id) {
    var el = document.getElementById(id);
    if (el) el.addEventListener('keydown', function(e) { if (e.key === 'Enter') registerUser(); });
  });
  checkAuthState();
});

