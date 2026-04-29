import sqlite3
conn = sqlite3.connect('xiangxun.db')
c = conn.cursor()
c.execute("PRAGMA table_info(users)")
columns = [row[1] for row in c.fetchall()]
print("现有列:", columns)
conn.close()