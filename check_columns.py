import sqlite3

conn = sqlite3.connect('finance_tracker.db')
columns = conn.execute("PRAGMA table_info(savings_goals);").fetchall()
for col in columns:
    print(col)
conn.close()