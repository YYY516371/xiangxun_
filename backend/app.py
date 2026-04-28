"""
一村一品 API 服务
从 CSV 文件读取数据，支持用户认证、收藏、点赞、评论、排行榜
"""
import os
import sqlite3
import hashlib
import uuid
import re
import math
from datetime import datetime
from functools import wraps
import pandas as pd
from flask import Flask, jsonify, request, g
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'villages.csv')
DB_PATH = os.path.join(BASE_DIR, 'xiangxun.db')


# ========== 数据库初始化 ==========
def init_db():
    """初始化数据库表结构"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # 会话表（存储 token）
    c.execute('''CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # 收藏表
    c.execute('''CREATE TABLE IF NOT EXISTS favorites (
        user_id INTEGER NOT NULL,
        village_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, village_id)
    )''')
    # 想去表
    c.execute('''CREATE TABLE IF NOT EXISTS wants (
        user_id INTEGER NOT NULL,
        village_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, village_id)
    )''')
    # 村庄点赞表
    c.execute('''CREATE TABLE IF NOT EXISTS village_likes (
        user_id INTEGER NOT NULL,
        village_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, village_id)
    )''')
    # 评论表
    c.execute('''CREATE TABLE IF NOT EXISTS comments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        village_id INTEGER NOT NULL,
        user_id INTEGER NOT NULL,
        content TEXT NOT NULL,
        like_count INTEGER DEFAULT 0,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # 评论点赞表
    c.execute('''CREATE TABLE IF NOT EXISTS comment_likes (
        user_id INTEGER NOT NULL,
        comment_id INTEGER NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        PRIMARY KEY (user_id, comment_id)
    )''')
    conn.commit()
    conn.close()


init_db()


# ========== 辅助函数 ==========
def get_db():
    """获取数据库连接（请求上下文）"""
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db


@app.teardown_appcontext
def close_connection(exception):
    """关闭数据库连接"""
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()


def hash_password(password):
    """SHA256 加密密码"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password, hashed):
    """验证密码"""
    return hash_password(password) == hashed


def login_required(f):
    """认证装饰器：验证请求头中的 token"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        if not auth_header:
            return jsonify({'error': 'Missing token'}), 401
        token = auth_header.replace('Bearer ', '')
        db = get_db()
        c = db.cursor()
        c.execute('SELECT user_id FROM sessions WHERE token = ?', (token,))
        row = c.fetchone()
        if not row:
            return jsonify({'error': 'Invalid token'}), 401
        request.user_id = row['user_id']
        return f(*args, **kwargs)
    return decorated_function


# ========== 加载村庄数据（从 CSV） ==========
villages_data = []
provinces_data = []
categories_data = []


def load_villages():
    global villages_data, provinces_data, categories_data
    try:
        df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
        villages_data = df.to_dict(orient='records')

        # ----------------- 统一 baike_urls 分隔符为 | -----------------
        for v in villages_data:
            urls = v.get('baike_urls')
            if urls and isinstance(urls, str):
                # 将各种可能的分隔符统一替换为 |
                unified = re.sub(r'[，,;；、\s]+', '|', urls)
                parts = [u.strip() for u in unified.split('|') if u.strip()]
                v['baike_urls'] = '|'.join(parts)
            elif urls is None:
                v['baike_urls'] = ''
        # ----------------------------------------------------------

        # 清洗 NaN
        for item in villages_data:
            for k, v in item.items():
                if isinstance(v, float) and math.isnan(v):
                    item[k] = None

        print(f"✅ villages_data 列表长度: {len(villages_data)}")

        # 省份统计
        province_stats = {}
        for v in villages_data:
            p = v.get('province', '未知')
            province_stats[p] = province_stats.get(p, 0) + 1
        provinces_data = [{'name': p, 'count': c} for p, c in province_stats.items()]

        # 分类统计
        category_stats = {}
        for v in villages_data:
            cat = v.get('industry_type', '其他')
            category_stats[cat] = category_stats.get(cat, 0) + 1
        categories_data = [{'name': c, 'count': cnt} for c, cnt in category_stats.items()]

        print(f"✅ 加载 {len(villages_data)} 条村庄数据")
    except Exception as e:
        print(f"❌ 加载失败: {e}")


load_villages()


# ========== 基础 API（无需认证） ==========
@app.route('/')
def hello():
    return '一村一品 API 服务运行中'


@app.route('/api/villages', methods=['GET'])
def get_villages():
    province = request.args.get('province')
    category = request.args.get('category')
    sub_category = request.args.get('sub_category')
    city = request.args.get('city')
    keyword = request.args.get('keyword')
    result = villages_data.copy()
    if province:
        result = [v for v in result if v.get('province') == province]
    if category:
        result = [v for v in result if v.get('industry_type') == category]
    if sub_category:
        result = [v for v in result if v.get('sub_category') == sub_category]
    if city:
        result = [v for v in result if v.get('city') == city]
    if keyword:
        result = [v for v in result if keyword in str(v.get('name', '')) or keyword in str(v.get('product_name', ''))]
    return jsonify(result)


@app.route('/api/villages/<int:id>', methods=['GET'])
def get_village(id):
    for v in villages_data:
        if v.get('id') == id:
            return jsonify(v)
    return jsonify({'error': 'Not found'}), 404


@app.route('/api/village/<int:id>', methods=['GET'])
def get_village_alt(id):
    return get_village(id)


@app.route('/api/provinces', methods=['GET'])
def get_provinces():
    return jsonify(provinces_data)


@app.route('/api/categories', methods=['GET'])
def get_categories():
    return jsonify(categories_data)


@app.route('/api/statistics/province-industry', methods=['GET'])
def province_industry_stats():
    industries = ['茶', '果', '药', '渔', '蔬', '花', '畜', '粮']
    stats = {}
    for v in villages_data:
        prov = v.get('province', '未知')
        ind = v.get('industry_type', '其他')
        if prov not in stats:
            stats[prov] = {ind: 0 for ind in industries}
            stats[prov]['province'] = prov
        if ind in industries:
            stats[prov][ind] += 1
    return jsonify([{'province': prov, **data} for prov, data in stats.items()])


@app.route('/api/statistics/province-count', methods=['GET'])
def province_count_stats():
    return jsonify(provinces_data)


@app.route('/api/statistics/province-top-products', methods=['GET'])
def province_top_products():
    province = request.args.get('province')
    if not province:
        return jsonify({'error': 'Missing province'}), 400
    counts = {}
    for v in villages_data:
        if v.get('province') == province:
            p = v.get('product_name')
            if p:
                counts[p] = counts.get(p, 0) + 1
    top10 = sorted(counts.items(), key=lambda x: x[1], reverse=True)[:10]
    return jsonify([{'product_name': n, 'count': c} for n, c in top10])


@app.route('/api/cities', methods=['GET'])
def get_cities():
    province = request.args.get('province')
    if not province:
        return jsonify({'error': 'Missing province'}), 400
    cities = set(v.get('city') for v in villages_data if v.get('province') == province and v.get('city'))
    return jsonify(sorted(cities))


# ========== 用户认证接口 ==========
@app.route('/api/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    if not username or not password:
        return jsonify({'error': 'Username and password required'}), 400
    db = get_db()
    c = db.cursor()
    try:
        c.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                  (username, hash_password(password)))
        db.commit()
        return jsonify({'message': 'User created'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'error': 'Username exists'}), 409


@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id, password FROM users WHERE username = ?', (username,))
    row = c.fetchone()
    if not row or not verify_password(password, row['password']):
        return jsonify({'error': 'Invalid credentials'}), 401
    token = str(uuid.uuid4())
    c.execute('INSERT INTO sessions (user_id, token) VALUES (?, ?)', (row['id'], token))
    db.commit()
    return jsonify({'token': token, 'user_id': row['id'], 'username': username})


@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_profile():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id, username, created_at FROM users WHERE id = ?', (request.user_id,))
    row = c.fetchone()
    return jsonify(dict(row))


# ========== 收藏 / 想去 / 点赞 ==========
def get_user_village_ids(table):
    db = get_db()
    c = db.cursor()
    c.execute(f'SELECT village_id FROM {table} WHERE user_id = ?', (request.user_id,))
    return [row['village_id'] for row in c.fetchall()]


@app.route('/api/user/favorites', methods=['GET'])
@login_required
def get_favorites():
    ids = get_user_village_ids('favorites')
    result = [v for v in villages_data if v.get('id') in ids]
    return jsonify(result)


@app.route('/api/user/wants', methods=['GET'])
@login_required
def get_wants():
    ids = get_user_village_ids('wants')
    result = [v for v in villages_data if v.get('id') in ids]
    return jsonify(result)


@app.route('/api/user/likes', methods=['GET'])
@login_required
def get_likes():
    ids = get_user_village_ids('village_likes')
    result = [v for v in villages_data if v.get('id') in ids]
    return jsonify(result)


@app.route('/api/villages/<int:id>/favorite', methods=['POST'])
@login_required
def add_favorite(id):
    db = get_db()
    c = db.cursor()
    try:
        c.execute('INSERT INTO favorites (user_id, village_id) VALUES (?, ?)', (request.user_id, id))
        db.commit()
        return jsonify({'message': 'Added'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Already exists'}), 200


@app.route('/api/villages/<int:id>/unfavorite', methods=['POST'])
@login_required
def remove_favorite(id):
    db = get_db()
    c = db.cursor()
    c.execute('DELETE FROM favorites WHERE user_id = ? AND village_id = ?', (request.user_id, id))
    db.commit()
    return jsonify({'message': 'Removed'}), 200


@app.route('/api/villages/<int:id>/want', methods=['POST'])
@login_required
def add_want(id):
    db = get_db()
    c = db.cursor()
    try:
        c.execute('INSERT INTO wants (user_id, village_id) VALUES (?, ?)', (request.user_id, id))
        db.commit()
        return jsonify({'message': 'Added'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Already exists'}), 200


@app.route('/api/villages/<int:id>/unwant', methods=['POST'])
@login_required
def remove_want(id):
    db = get_db()
    c = db.cursor()
    c.execute('DELETE FROM wants WHERE user_id = ? AND village_id = ?', (request.user_id, id))
    db.commit()
    return jsonify({'message': 'Removed'}), 200


@app.route('/api/villages/<int:id>/like', methods=['POST'])
@login_required
def add_village_like(id):
    db = get_db()
    c = db.cursor()
    try:
        c.execute('INSERT INTO village_likes (user_id, village_id) VALUES (?, ?)', (request.user_id, id))
        db.commit()
        return jsonify({'message': 'Liked'}), 201
    except sqlite3.IntegrityError:
        return jsonify({'message': 'Already liked'}), 200


@app.route('/api/villages/<int:id>/unlike', methods=['POST'])
@login_required
def remove_village_like(id):
    db = get_db()
    c = db.cursor()
    c.execute('DELETE FROM village_likes WHERE user_id = ? AND village_id = ?', (request.user_id, id))
    db.commit()
    return jsonify({'message': 'Unliked'}), 200


# ========== 评论 ==========
@app.route('/api/comments', methods=['POST'])
@login_required
def add_comment():
    data = request.get_json()
    village_id = data.get('village_id')
    content = data.get('content')
    if not village_id or not content:
        return jsonify({'error': 'Missing fields'}), 400
    db = get_db()
    c = db.cursor()
    c.execute('INSERT INTO comments (village_id, user_id, content) VALUES (?, ?, ?)',
              (village_id, request.user_id, content))
    db.commit()
    comment_id = c.lastrowid
    c.execute('SELECT username FROM users WHERE id = ?', (request.user_id,))
    user = c.fetchone()
    return jsonify({
        'id': comment_id,
        'village_id': village_id,
        'user_id': request.user_id,
        'username': user['username'],
        'content': content,
        'like_count': 0,
        'created_at': datetime.now().isoformat()
    }), 201


@app.route('/api/comments/<int:id>/like', methods=['POST'])
@login_required
def like_comment(id):
    db = get_db()
    c = db.cursor()
    c.execute('SELECT 1 FROM comment_likes WHERE user_id = ? AND comment_id = ?', (request.user_id, id))
    if c.fetchone():
        return jsonify({'error': 'Already liked'}), 400
    c.execute('INSERT INTO comment_likes (user_id, comment_id) VALUES (?, ?)', (request.user_id, id))
    c.execute('UPDATE comments SET like_count = like_count + 1 WHERE id = ?', (id,))
    db.commit()
    return jsonify({'message': 'Liked'}), 201


@app.route('/api/comments/<int:id>/unlike', methods=['POST'])
@login_required
def unlike_comment(id):
    db = get_db()
    c = db.cursor()
    c.execute('SELECT 1 FROM comment_likes WHERE user_id = ? AND comment_id = ?', (request.user_id, id))
    if not c.fetchone():
        return jsonify({'error': 'Not liked'}), 400
    c.execute('DELETE FROM comment_likes WHERE user_id = ? AND comment_id = ?', (request.user_id, id))
    c.execute('UPDATE comments SET like_count = like_count - 1 WHERE id = ? AND like_count > 0', (id,))
    db.commit()
    return jsonify({'message': 'Unliked'}), 200


# ========== 排行榜 ==========
@app.route('/api/rankings/like', methods=['GET'])
def ranking_like():
    limit = request.args.get('limit', 10, type=int)
    db = get_db()
    c = db.cursor()
    c.execute('''
        SELECT village_id, COUNT(*) as like_count
        FROM village_likes
        GROUP BY village_id
        ORDER BY like_count DESC
        LIMIT ?
    ''', (limit,))
    top_villages = c.fetchall()
    result = []
    for row in top_villages:
        village_id = row['village_id']
        village = next((v for v in villages_data if v.get('id') == village_id), None)
        if not village:
            continue
        c.execute('''
            SELECT c.id, c.user_id, c.content, c.like_count, c.created_at, u.username
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.village_id = ?
            ORDER BY c.like_count DESC
            LIMIT 5
        ''', (village_id,))
        comments = [dict(comment) for comment in c.fetchall()]
        result.append({
            'village_id': village_id,
            'village_name': village.get('name'),
            'product_name': village.get('product_name'),
            'like_count': row['like_count'],
            'top_comments': comments
        })
    return jsonify(result)


@app.route('/api/rankings/want', methods=['GET'])
def ranking_want():
    limit = request.args.get('limit', 10, type=int)
    db = get_db()
    c = db.cursor()
    c.execute('''
        SELECT village_id, COUNT(*) as want_count
        FROM wants
        GROUP BY village_id
        ORDER BY want_count DESC
        LIMIT ?
    ''', (limit,))
    top_villages = c.fetchall()
    result = []
    for row in top_villages:
        village_id = row['village_id']
        village = next((v for v in villages_data if v.get('id') == village_id), None)
        if village:
            result.append({
                'village_id': village_id,
                'village_name': village.get('name'),
                'product_name': village.get('product_name'),
                'want_count': row['want_count']
            })
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True, port=5000)