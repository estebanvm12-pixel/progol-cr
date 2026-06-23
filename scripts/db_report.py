import sqlite3, json
conn = sqlite3.connect('data/progol.db')
cur = conn.cursor()
cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = [r[0] for r in cur.fetchall()]
print('Tables:', tables)
for t in tables:
    cur.execute(f"SELECT COUNT(*) FROM [{t}]")
    n = cur.fetchone()[0]
    cur.execute(f"PRAGMA table_info([{t}])")
    cols = [c[1] for c in cur.fetchall()]
    print(f"  {t}: {n} rows | cols: {cols}")
    if 0 < n <= 30:
        cur.execute(f"SELECT * FROM [{t}]")
        for row in cur.fetchall():
            print("   ", dict(zip(cols, row)))
conn.close()
