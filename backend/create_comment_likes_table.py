import sqlite3

DB_PATH = 'xiangxun.db'
conn = sqlite3.connect(DB_PATH)
c = conn.cursor()
c.execute('''
    CREATE TABLE IF NOT EXISTS comment_likes (
        user_id INTEGER NOT NULL,
        comment_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, comment_id)
    )
''')
conn.commit()
conn.close()
print("✅ comment_likes 表已创建（如果不存在）")