import sqlite3

DB_PATH = 'xiangxun.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
try:
    c.execute('ALTER TABLE comments ADD COLUMN parent_id INTEGER DEFAULT NULL')
    print("✅ 成功添加 parent_id 列")
except sqlite3.OperationalError as e:
    if "duplicate column name" in str(e):
        print("ℹ️ parent_id 列已存在，无需添加")
    else:
        print(f"❌ 错误: {e}")
conn.commit()
conn.close()