import sqlite3

conn = sqlite3.connect('finance_tracker.db')
users = conn.execute("SELECT id, email FROM users;").fetchall()
for u in users:
    print(u)
conn.close()