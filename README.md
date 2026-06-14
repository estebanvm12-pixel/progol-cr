# ⚽ World Cup 2026 — War Room

A small **local** web app that shows every World Cup 2026 match for any day
(live scores + status), with an **"Ask the Analyst"** chat panel powered by Claude.

- **Live data:** TheSportsDB (free public key built in — no signup needed).
- **Chat:** Anthropic API (Claude). You paste your own key once; it's stored
  locally in `config.json` and never leaves your machine except to call Anthropic.
- **Zero dependencies:** runs on the Python standard library only.

---

## How to run

**Easiest:** double-click **`Start War Room.bat`**.

**Or from a terminal:**
```powershell
cd C:\Users\esteb\worldcup-warroom
python server.py
```

Your browser opens automatically at <http://127.0.0.1:8765>.
Close the terminal window (or press `Ctrl+C`) to stop it.

---

## First-time setup (to enable chat)

1. Click the **⚙ (Settings)** button, top-right.
2. Paste your **Anthropic API key** (get one at
   <https://console.anthropic.com> → *API Keys*).
3. Pick a model (Sonnet is the recommended balance of smart + cheap).
4. **Save.** The chat panel now says "Claude connected."

> The fixtures dashboard works **without** any key. The key is only needed for
> the chat / analysis panel. Each question costs a few cents on your Anthropic
> account.

---

## What it does

| Feature | Notes |
|---|---|
| Day-by-day fixtures | Use ◀ ▶ or the date picker to browse any day |
| **Competition filter** | 🏆 **World Cup** or 🌍 **All International** (friendlies, qualifiers, Nations League, Gold Cup, etc. — any country-vs-country game) |
| Live scores & status | Auto-refreshes every 45s (toggle "Auto" off to pause) |
| Venues & kickoff times | Kickoff shown in **your** local timezone |
| **🔮 Match Insights** | **Click any match** for a full predictive breakdown (see below) |
| Ask the Analyst | Claude sees the fixtures on screen and answers tactics, previews, corners, predictions |
| **📝 Analyst notes** | Saved in the local database, tied to each date — your running scouting log |
| **Offline cache** | Every fetched match is stored in SQLite; if the feed is down you still see the last-known fixtures (shown with an "offline · cached" badge) |

---

## 🔮 Match Insights (the prediction model)

Click any match card to open a predictive dashboard powered by `model.py` — a
transparent **Poisson scoring model** (the standard approach in football
analytics) built on team strength ratings. From one model you get:

- **Predicted scoreline** + the most-likely scorelines with probabilities
- **Win / Draw / Win** probability bar (1X2)
- **Who scores first** (home / away / no goal)
- **First corner** + expected corners per team
- **Expected goals (xG)** per side
- **Both teams to score**, **Over/Under 2.5**, **expected cards**
- A **1–10 confidence** read

Then hit **🧠 AI deep-dive** to have Claude layer tactical reasoning, players to
watch, and injury/lineup risks on top of the model numbers (needs your API key).

> These are **model estimates, not guarantees** — the panel says so. The model
> does not yet include lineups, injuries, referee or weather; the AI deep-dive
> and the analyst chat are there to add that human/contextual layer.
> Ratings live in `model.py` (`RATINGS`) and are easy to tweak.

### Good things to ask the analyst
- "Preview today's biggest game and the key tactical battle."
- "Corner and card outlook for [team] vs [team]."
- "Give me a prediction with confidence 1–10 and the main risks."
- "Which players should I watch today and why?"

> **Note:** the in-app analyst does **not** browse the internet. It reasons over
> the live fixtures the app feeds it plus its football knowledge, and it flags
> when something (late injuries, confirmed lineups) needs fresh verification.
> For live web research, ask me (Claude Code) directly.

---

## Local database (SQLite — no install needed)

The app uses **SQLite**, which is built into Python — there is **no separate
SQL server to install**. The entire database is a single file, `warroom.db`,
created automatically on first run. It's still real SQL, so you can open it with
any SQLite tool (DB Browser for SQLite, the `sqlite3` CLI, a VS Code extension)
and run queries.

**Tables**

| Table | What's in it |
|---|---|
| `matches` | Every fixture/result the app has fetched (offline cache + history) |
| `notes` | Your analyst notes, tied to a date |
| `competitions` | Catalog of international competitions tracked |

Example query (any SQLite client):
```sql
SELECT date, home, away, home_score, away_score, status
FROM matches WHERE is_intl = 1 ORDER BY date DESC;
```

> If you ever outgrow SQLite, the schema in `db.py` ports cleanly to PostgreSQL.

---

## Files

| File | Purpose |
|---|---|
| `server.py` | Local server: serves the UI, proxies sports data + Claude, exposes notes + predict API |
| `db.py` | SQLite layer: schema, match cache, notes, competitions |
| `model.py` | Prediction engine: Poisson scoring model + team ratings |
| `index.html` / `styles.css` / `app.js` | The dashboard front-end |
| `warroom.db` | Your local database (git-ignored, created on first run) |
| `config.json` | Your saved settings & API key (git-ignored, created on first run) |
| `Start War Room.bat` | One-click launcher |

---

## Troubleshooting

- **"No Anthropic API key set"** → open ⚙ Settings and paste your key.
- **Fixtures won't load** → check your internet; click **⟳ Refresh**. The free
  sports key is rate-limited, so very rapid refreshing can briefly throttle.
- **Port already in use** → edit `PORT = 8765` near the top of `server.py`.
- **Want faster/cheaper chat** → switch the model in Settings
  (Haiku = fastest/cheapest, Opus = smartest).
