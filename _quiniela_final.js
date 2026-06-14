
/* ══════════════════════ MOBILE TAB SWITCHING ══════════════════════ */

function switchMobileTab(tab) {
  document.querySelectorAll('.mobile-tab').forEach(function(btn) {
    btn.classList.toggle('active', btn.dataset.tab === tab);
  });
  var paneMatches  = document.getElementById('paneMatches');
  var paneChat     = document.getElementById('paneChat');
  var paneQuiniela = document.getElementById('paneQuiniela');
  paneMatches.classList.toggle('mobile-active',  tab === 'matches');
  paneChat.classList.toggle('mobile-active',     tab === 'chat');
  paneQuiniela.classList.toggle('mobile-active', tab === 'quiniela');
  if (tab === 'quiniela' && !_qState.loaded) loadQuiniela(false);
}

/* ══════════════════════ QUINIELA STATE ══════════════════════ */

var _qState = {
  loaded: false,
  groups: [],       // from /api/standings (includes fixtures)
  analysis: {},     // groupName -> { pick1, pick2, conf1, conf2, odd1, odd2, dark_horse, bet_tip }
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

/* ══════════════════════ MATH PICKS ══════════════════════ */

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
    _qState.analysis[g.name] = {
      pick1: sorted[0] ? sorted[0].name : '?',
      pick2: sorted[1] ? sorted[1].name : '?',
      conf1: c1,
      conf2: c2,
      odd1: (1 / (c1 / 100)).toFixed(2),
      odd2: (1 / (c2 / 100)).toFixed(2),
      dark_horse: sorted[2] ? sorted[2].name : null,
      bet_tip: null,
    };
  });
}

/* ══════════════════════ AI ENRICHMENT ══════════════════════ */

async function enrichQWithAI(groups) {
  try {
    var summary = groups.map(function(g) {
      var a = _qState.analysis[g.name];
      var fixtures = (g.fixtures || []).filter(function(f) { return f.status === 'Finished'; });
      var results = fixtures.map(function(f) {
        return f.home + ' ' + (f.scoreHome || '?') + '-' + (f.scoreAway || '?') + ' ' + f.away;
      }).join(', ');
      return g.name + ': lider=' + (a ? a.pick1 : '?') + ' 2do=' + (a ? a.pick2 : '?')
        + (results ? ' Resultados:[' + results + ']' : '');
    }).join(' | ');

    var prompt = 'Mundial 2026 grupos. Para cada grupo dame dark_horse y bet_tip de Doradobet en JSON. '
      + 'Estado: ' + summary + '. '
      + 'JSON SOLO: {"groups":[{"group":"Group A","dark_horse":"pais","bet_tip":"apuesta"},...]}'
      + ' Sin texto extra.';

    var r = await fetch('/api/chat', {
      method: 'POST',
      headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({message: prompt, history: [], matches: [], date: state.date, lang: 'es'})
    });
    var d = await r.json();
    var reply = d.reply || '';
    if (reply.indexOf('API') >= 0 || reply.indexOf('clave') >= 0) return;
    var m = reply.match(/\{[\s\S]*"groups"[\s\S]*\}/);
    if (m) {
      var parsed = JSON.parse(m[0]);
      (parsed.groups || []).forEach(function(g) {
        if (_qState.analysis[g.group]) {
          if (g.dark_horse) _qState.analysis[g.group].dark_horse = g.dark_horse;
          if (g.bet_tip) _qState.analysis[g.group].bet_tip = g.bet_tip;
        }
      });
    }
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
  // 3rd-place tracker strip
  var thirdStrip = build3rdPlaceTracker();
  container.appendChild(thirdStrip);
  // Group cards
  _qState.groups.forEach(function(grp) {
    container.appendChild(buildQGroupCard(grp));
  });
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
    + (analysis.dark_horse ? '<div class="q-dark-horse">&#x1F525; Dark horse: <strong>' + analysis.dark_horse + '</strong></div>' : '')
    + (analysis.bet_tip    ? '<div class="q-bet-tip">&#x1F3AF; ' + analysis.bet_tip + '</div>' : '');
  card.appendChild(picksDiv);

  // ── Results (played matches)
  if (played.length) {
    var resultsDiv = document.createElement('div');
    resultsDiv.className = 'q-fixtures q-results';
    resultsDiv.innerHTML = '<div class="q-fix-title">Resultados</div>';
    played.forEach(function(f) {
      resultsDiv.appendChild(buildFixtureRow(f, true));
    });
    card.appendChild(resultsDiv);
  }

  // ── Upcoming fixtures
  if (upcoming.length) {
    var upcomingDiv = document.createElement('div');
    upcomingDiv.className = 'q-fixtures q-upcoming';
    upcomingDiv.innerHTML = '<div class="q-fix-title">Proximos partidos</div>';
    upcoming.forEach(function(f) {
      upcomingDiv.appendChild(buildFixtureRow(f, false));
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

function buildFixtureRow(f, isResult) {
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
    row.innerHTML = fh + '<span class="q-fix-team">' + f.home + '</span>'
      + '<span class="q-fix-vs">vs</span>'
      + '<span class="q-fix-team q-fix-team-r">' + f.away + '</span>' + fa
      + '<span class="q-fix-date">' + dateStr + '</span>';
  }
  return row;
}

/* ══════════════════════ LIVE ANALYST TRACKER ══════════════════════ */

var liveTracker = { prev: {}, timer: null };

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
        if (isFT) { saveLiveResult(m); loadQuiniela(true); } // refresh quiniela on FT
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
    + '\n2. Apuestas EN VIVO con valor en Doradobet'
    + '\n3. Cuotas justas estimadas ahora'
    + '\n4. Expectativa tactica proximos minutos'
    + '\nMaximo 4 puntos concisos.';

  if (window.innerWidth <= 700) switchMobileTab('chat');
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
