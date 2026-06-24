#!/usr/bin/env python3
"""
ProGol CR — Migración JSON → SQLite
Migra users.json y feedback.json a progol.db con tablas propias.
Idempotente: si ya migrado, no duplica.
"""
import os, json, sqlite3, bcrypt, datetime

BASE    = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE, "data", "progol.db")
USERS_J = os.path.join(BASE, "data", "users.json")
FB_J    = os.path.join(BASE, "data", "feedback.json")

conn = sqlite3.connect(DB_PATH)
cur  = conn.cursor()

# ── Crear tablas ──────────────────────────────────────────────────────────────
cur.executescript("""
CREATE TABLE IF NOT EXISTS users (
    username    TEXT PRIMARY KEY,
    password    TEXT NOT NULL,
    role        TEXT NOT NULL DEFAULT 'free',
    email       TEXT,
    telegram_id TEXT,
    active      INTEGER NOT NULL DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    last_login  TEXT
);

CREATE TABLE IF NOT EXISTS feedback (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    ts         TEXT NOT NULL,
    nombre     TEXT,
    tipo       TEXT,
    opinion    TEXT NOT NULL,
    processed  INTEGER NOT NULL DEFAULT 0
);
""")
conn.commit()

# ── Migrar users.json ─────────────────────────────────────────────────────────
migrated_users = 0
if os.path.exists(USERS_J):
    try:
        with open(USERS_J) as f:
            users = json.load(f)
        for username, data in users.items():
            existing = cur.execute("SELECT username FROM users WHERE username=?", (username,)).fetchone()
            if not existing:
                cur.execute("""INSERT INTO users (username, password, role, email, telegram_id, active)
                               VALUES (?,?,?,?,?,?)""",
                    (username,
                     data.get("password",""),
                     data.get("role","free"),
                     data.get("email",""),
                     data.get("telegram_chat_id",""),
                     int(data.get("active", True))))
                migrated_users += 1
        conn.commit()
        print(f"OK: {migrated_users} usuarios migrados a SQLite")
    except Exception as e:
        print(f"WARN users.json: {e}")

# ── Migrar feedback.json ──────────────────────────────────────────────────────
migrated_fb = 0
if os.path.exists(FB_J):
    try:
        with open(FB_J) as f:
            feedbacks = json.load(f)
        for entry in feedbacks:
            ts = entry.get("ts","")
            existing = cur.execute("SELECT id FROM feedback WHERE ts=? AND opinion=?",
                                   (ts, entry.get("opinion",""))).fetchone()
            if not existing:
                cur.execute("INSERT INTO feedback (ts, nombre, tipo, opinion) VALUES (?,?,?,?)",
                    (ts, entry.get("nombre",""), entry.get("tipo",""), entry.get("opinion","")))
                migrated_fb += 1
        conn.commit()
        print(f"OK: {migrated_fb} feedbacks migrados a SQLite")
    except Exception as e:
        print(f"WARN feedback.json: {e}")

# ── Resumen ───────────────────────────────────────────────────────────────────
total_users = cur.execute("SELECT COUNT(*) FROM users").fetchone()[0]
total_fb    = cur.execute("SELECT COUNT(*) FROM feedback").fetchone()[0]
print(f"DB: {total_users} usuarios, {total_fb} feedbacks en {DB_PATH}")
conn.close()

print("Migración completa. Los archivos JSON originales se mantienen como backup.")
print("Próximo paso: actualizar server.py para leer/escribir en SQLite en lugar de JSON.")
