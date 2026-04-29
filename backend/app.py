import os
import sqlite3
import hashlib
from datetime import datetime
from functools import wraps
import pandas as pd
from flask import Flask, jsonify, request, g
from flask_cors import CORS
from flask import send_from_directory


app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CSV_PATH = os.path.join(BASE_DIR, 'villages.csv')
DB_PATH = os.path.join(BASE_DIR, 'xiangxun.db')

# ========== 数据库初始化 ==========
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    # 用户表
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )''')
    # 用户会话
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
    # 点赞表
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
    parent_id INTEGER DEFAULT NULL,
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
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DB_PATH)
        db.row_factory = sqlite3.Row
    return db

@app.teardown_appcontext
def close_connection(exception):
    db = getattr(g, '_database', None)
    if db is not None:
        db.close()

def hash_password(password):
    return hashlib.sha256(password.encode()).hexdigest()

def verify_password(password, hashed):
    return hash_password(password) == hashed

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        token = request.headers.get('Authorization')
        if not token:
            return jsonify({'error': 'Missing token'}), 401
        token = token.replace('Bearer ', '')
        db = get_db()
        c = db.cursor()
        c.execute('SELECT user_id FROM sessions WHERE token = ?', (token,))
        row = c.fetchone()
        if not row:
            return jsonify({'error': 'Invalid token'}), 401
        request.user_id = row['user_id']
        return f(*args, **kwargs)
    return decorated_function

def get_current_user_id():
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    token = auth_header.split(' ')[1]
    db = get_db()
    c = db.cursor()
    c.execute('SELECT user_id FROM sessions WHERE token = ?', (token,))
    row = c.fetchone()
    return row['user_id'] if row else None

# ========== 标准化映射表（根据最新规则完善） ==========
CATEGORY_MAPPING = {
    # -------------------- 药类 --------------------
    "中草药": ("中草药", "药"),
    "云南参": ("云南参", "药"),
    "白首乌": ("白首乌", "药"),
    "石斛": ("石斛", "药"),
    "铁皮石斛": ("石斛", "药"),
    "马鹿茸": ("鹿茸", "药"),
    "白首乌": ("白首乌", "药"),
    "石斛": ("石斛", "药"),
    "铁皮石斛": ("石斛", "药"),
    "马鹿茸": ("鹿茸", "药"),
    # -------------------- 果类 --------------------
    # 李子类
    "三华李": ("李子", "果"),
    "李": ("李子", "果"),
    "李子": ("李子", "果"),
    "珍珠李": ("李子", "果"),
    "空心李": ("李子", "果"),
    "芙蓉李": ("李子", "果"),
    "蜂糖李": ("李子", "果"),
    "黄蜡李": ("李子", "果"),
    "黑李": ("李子", "果"),
    "柰李": ("李子", "果"),
    "脆红李": ("李子", "果"),
    # 莓类
    "树莓": ("莓类", "果"),
    "草莓": ("莓类", "果"),
    "草莓、西甜瓜": ("莓类", "果"),
    "樱桃、草莓": ("莓类", "果"),
    "莓": ("莓类", "果"),
    "蓝莓": ("莓类", "果"),
    "黑莓": ("莓类", "果"),
    # 葡萄类
    "冰葡萄": ("葡萄", "果"),
    "山葡萄": ("葡萄", "果"),
    "红提葡萄": ("葡萄", "果"),
    "葡萄": ("葡萄", "果"),
    "酿酒葡萄": ("葡萄", "果"),
    "无核白葡萄": ("葡萄", "果"),
    # 梨类
    "刺梨": ("梨", "果"),
    "南果梨": ("梨", "果"),
    "梨": ("梨", "果"),
    "梨文化": ("梨", "果"),
    "洋梨": ("梨", "果"),
    "白酥梨": ("梨", "果"),
    "砂梨": ("梨", "果"),
    "红雪梨": ("梨", "果"),
    "苹果梨": ("梨", "果"),
    "蜜雪梨": ("梨", "果"),
    "金秋梨": ("梨", "果"),
    "长把梨": ("梨", "果"),
    "雪梨": ("梨", "果"),
    "黄花梨": ("梨", "果"),
    "福梨": ("梨", "果"),
    "鸭梨": ("梨", "果"),
    # 坚果类
    "坚果": ("坚果", "果"),
    "山核桃": ("坚果", "果"),
    "榛子": ("坚果", "果"),
    "核桃": ("坚果", "果"),
    # 山楂
    "山楂": ("山楂", "果"),
    "山楂干": ("山楂", "果"),
    # 柚子类
    "思州柚": ("柚子", "果"),
    "文旦": ("柚子", "果"),
    "文旦柚": ("柚子", "果"),
    "早香柚": ("柚子", "果"),
    "柚子": ("柚子", "果"),
    "沙田柚": ("柚子", "果"),
    "甜柚": ("柚子", "果"),
    "蜜柚": ("柚子", "果"),
    "贡水白柚": ("柚子", "果"),
    "金柚": ("柚子", "果"),
    "香柚": ("柚子", "果"),
    "真龙柚": ("柚子", "果"),
    "汶浪蜜柚": ("柚子", "果"),
    "红肉蜜柚": ("柚子", "果"),
    "胡柚": ("柚子", "果"),
    # 橙子类
    "春橙": ("橙子", "果"),
    "晚橙": ("橙子", "果"),
    "橘橙": ("橙子", "果"),
    "橙": ("橙子", "果"),
    "甜橙": ("橙子", "果"),
    "红橙": ("橙子", "果"),
    "脐橙": ("橙子", "果"),
    "血橙": ("橙子", "果"),
    "冰糖橙": ("橙子", "果"),
    "纽荷尔脐橙": ("橙子", "果"),
    "红肉脐橙": ("橙子", "果"),
    "锦橙": ("橙子", "果"),
    # 柿子类
    "月柿": ("柿子", "果"),
    "柿子": ("柿子", "果"),
    "柿饼": ("柿子", "果"),
    "桃、柿子": ("柿子", "果"),
    "水柿": ("柿子", "果"),
    # 杏类
    "李广杏": ("杏", "果"),
    "杏": ("杏", "果"),
    "杏子": ("杏", "果"),
    "树上干杏": ("杏", "果"),
    "银杏": ("银杏", "果"),
    # 枣类
    "板枣": ("枣", "果"),
    "大枣": ("枣", "果"),
    "栆": ("枣", "果"),
    "米枣": ("枣", "果"),
    "红枣": ("枣", "果"),
    "长红枣": ("枣", "果"),
    # 水果大类
    "林果": ("水果", "果"),
    "果品": ("水果", "果"),
    "时令水果": ("水果", "果"),
    "水果": ("水果", "果"),
    # 柑橘类
    "柑桔": ("柑橘", "果"),
    "柑橘": ("柑橘", "果"),
    "椪柑": ("柑橘", "果"),
    "沃柑": ("柑橘", "果"),
    "沙糖桔": ("柑橘", "果"),
    "油柑": ("柑橘", "果"),
    "狮头柑": ("柑橘", "果"),
    "砂糖桔": ("柑橘", "果"),
    "红桔": ("柑橘", "果"),
    "芦柑": ("柑橘", "果"),
    "蕉柑": ("柑橘", "果"),
    "蜜柑": ("柑橘", "果"),
    "贡柑": ("柑橘", "果"),
    "蜜桔": ("柑橘", "果"),
    "金桔": ("柑橘", "果"),
    "金橘": ("柑橘", "果"),
    "香桔": ("柑橘", "果"),
    # 桃子类
    "桃": ("桃子", "果"),
    "桃子": ("桃子", "果"),
    "水蜜桃": ("桃子", "果"),
    "白凤桃": ("桃子", "果"),
    "蜜桃": ("桃子", "果"),
    "蟠桃": ("桃子", "果"),
    "黄桃": ("桃子", "果"),
    "香桃": ("桃子", "果"),
    "油桃": ("桃子", "果"),
    # 桑葚
    "桑椹": ("桑葚", "果"),
    "桑葚": ("桑葚", "果"),
    # 樱桃类
    "樱桃": ("樱桃", "果"),
    "樱桃西红柿": ("樱桃", "果"),
    "甜樱桃": ("樱桃", "果"),
    "苹果、樱桃": ("樱桃", "果"),
    # 瓜类
    "吊瓜": ("瓜类", "果"),
    "打瓜": ("瓜类", "果"),
    "哈密瓜": ("瓜类", "果"),
    "沙漠西瓜": ("瓜类", "果"),
    "甘甜瓜": ("瓜类", "果"),
    "甜瓜": ("瓜类", "果"),
    "硒西瓜": ("瓜类", "果"),
    "蜜瓜": ("瓜类", "果"),
    "西瓜": ("瓜类", "果"),
    "西瓜、葡萄": ("瓜类", "果"),
    "西甜瓜": ("瓜类", "果"),
    "香瓜": ("瓜类", "果"),
    "宣木瓜": ("瓜类", "果"),
    "西香瓜": ("瓜类", "果"),
    # 其他归回果类的
    "板栗": ("板栗", "果"),
    "井冈蜜柚": ("蜜柚", "果"),
    "甘蔗": ("甘蔗", "果"),
    "白玉蔗": ("甘蔗", "果"),
    "圣女果": ("圣女果", "果"),
    # -------------------- 粮类 --------------------
    "优质米": ("谷物", "粮"),
    "有机稻米": ("谷物", "粮"),
    "稻米": ("谷物", "粮"),
    "糯稻": ("谷物", "粮"),
    "丝苗米": ("谷物", "粮"),
    "再生稻": ("谷物", "粮"),
    "大禾谷": ("谷物", "粮"),
    "大米": ("谷物", "粮"),
    "小米": ("谷物", "粮"),
    "早稻": ("谷物", "粮"),
    "杂稻制种": ("谷物", "粮"),
    "水稻": ("谷物", "粮"),
    "稻鸭米": ("谷物", "粮"),
    "米": ("谷物", "粮"),
    "糯米": ("谷物", "粮"),
    "红米": ("谷物", "粮"),
    "红香米": ("谷物", "粮"),
    "贡米": ("谷物", "粮"),
    "香米": ("谷物", "粮"),
    "谷子": ("谷物", "粮"),
    "谷物食品": ("谷物", "粮"),
    "高粱": ("谷物", "粮"),
    "荞麦、糜子、谷子": ("谷物", "粮"),
    "血麦": ("谷物", "粮"),
    "青稞": ("谷物", "粮"),
    "巴平米": ("谷物", "粮"),
    "地瓜": ("薯类", "粮"),
    "番薯": ("薯类", "粮"),
    "红薯三粉": ("薯类", "粮"),
    "红薯制品": ("薯类", "粮"),
    "土豆": ("薯类", "粮"),
    "甘薯": ("薯类", "粮"),
    "紫薯": ("薯类", "粮"),
    "红薯": ("薯类", "粮"),
    "蜜薯": ("薯类", "粮"),
    "玉米": ("玉米", "粮"),
    "糯玉米": ("玉米", "粮"),
    "鲜食玉米": ("玉米", "粮"),
    "府谷黄米": ("黄米", "粮"),
    "杂粮": ("杂粮", "粮"),
    "粮食": ("粮食", "粮"),
    "花生": ("花生", "粮"),
    "豆制品": ("豆制品", "粮"),
    # -------------------- 蔬类 --------------------
    "毛豆": ("毛豆", "蔬"),
    "毛笋": ("笋", "蔬"),
    "笋干": ("笋", "蔬"),
    "瓜菜": ("瓜菜", "蔬"),
    "甜菜": ("甜菜", "蔬"),
    "茭白": ("茭白", "蔬"),
    "胡椒": ("胡椒", "蔬"),
    "葫芦瓜": ("葫芦瓜", "蔬"),
    "蔬": ("蔬菜", "蔬"),
    "韭黄": ("韭黄", "蔬"),
    "食用菌": ("菌类", "蔬"),
    "高原夏菜": ("高原夏菜", "蔬"),
    "无公害蔬菜": ("蔬菜", "蔬"),
    "蔬菜": ("蔬菜", "蔬"),
    # -------------------- 茶类 --------------------
    "有机茶": ("有机茶", "茶"),
    "水仙茶": ("水仙茶", "茶"),
    "油茶": ("油茶", "茶"),
    "莓茶": ("莓茶", "茶"),
    "茶花": ("茶花", "花"),
    # -------------------- 渔类 --------------------
    "水产": ("水产品", "渔"),
    "水产品": ("水产品", "渔"),
    "海产品": ("水产品", "渔"),
    "中华鳖": ("鳖", "渔"),
    "鳖": ("鳖", "渔"),
    "龟鳖": ("鳖", "渔"),
    "江鳟鱼": ("鳟鱼", "渔"),
    "鳟鱼": ("鳟鱼", "渔"),
    "大闸蟹": ("蟹", "渔"),
    "幼蟹": ("蟹", "渔"),
    "河蟹": ("蟹", "渔"),
    "螃蟹": ("蟹", "渔"),
    "蟹苗": ("蟹", "渔"),
    "青虾蟹": ("蟹", "渔"),
    "对虾": ("虾", "渔"),
    "小龙虾": ("虾", "渔"),
    "稻虾": ("虾", "渔"),
    "虾": ("虾", "渔"),
    "青虾": ("虾", "渔"),
    "龙虾": ("虾", "渔"),
    "罗氏沼虾": ("虾", "渔"),
    "捕捞、养殖": ("捕捞", "渔"),
    "海洋捕捞": ("捕捞", "渔"),
    "淡水养殖": ("淡水养殖", "渔"),
    "渔业": ("渔业", "渔"),
    "现代都市渔业园": ("渔业园", "渔"),
    "珍珠": ("珍珠", "渔"),
    # -------------------- 畜类 --------------------
    "乌骨鸡": ("鸡", "畜"),
    "乌鸡": ("鸡", "畜"),
    "土鸡": ("鸡", "畜"),
    "山鸡": ("鸡", "畜"),
    "藏鸡": ("鸡", "畜"),
    "蛋鸡": ("鸡", "畜"),
    "象洞鸡": ("鸡", "畜"),
    "鸡": ("鸡", "畜"),
    "黄羽鸡": ("鸡", "畜"),
    "黑鸡": ("鸡", "畜"),
    "肉鸡": ("鸡", "畜"),
    "麻鸡": ("鸡", "畜"),
    "白羽肉鸡": ("鸡", "畜"),
    "乌猪": ("猪", "畜"),
    "八眉猪": ("猪", "畜"),
    "猪": ("猪", "畜"),
    "生猪": ("猪", "畜"),
    "种猪": ("猪", "畜"),
    "藏香猪": ("猪", "畜"),
    "半细绵羊": ("羊", "畜"),
    "壶天石羊": ("羊", "畜"),
    "奶山羊": ("羊", "畜"),
    "山羊": ("羊", "畜"),
    "有机绒山羊": ("羊", "畜"),
    "牛羊": ("羊", "畜"),
    "细毛羊": ("羊", "畜"),
    "绒山羊": ("羊", "畜"),
    "绵羊": ("羊", "畜"),
    "羊": ("羊", "畜"),
    "羔羊": ("羊", "畜"),
    "黄羊": ("羊", "畜"),
    "肉羊": ("羊", "畜"),
    "奶牛": ("牛", "畜"),
    "牛": ("牛", "畜"),
    "牦牛": ("牛", "畜"),
    "种牦牛": ("牛", "畜"),
    "红牛": ("牛", "畜"),
    "黄牛": ("牛", "畜"),
    "肉牛": ("牛", "畜"),
    "山麻鸭": ("鸭", "畜"),
    "白鸭": ("鸭", "畜"),
    "肉鸭": ("鸭", "畜"),
    "鸭": ("鸭", "畜"),
    "有机羊肉": ("肉制品", "畜"),
    "滩羊肉": ("肉制品", "畜"),
    "牛肉": ("肉制品", "畜"),
    "牛肉干": ("肉制品", "畜"),
    "畜产品": ("肉制品", "畜"),
    "羊肉": ("肉制品", "畜"),
    "羔羊肉": ("肉制品", "畜"),
    "蚕丝": ("蚕", "畜"),
    "蚕桑": ("蚕", "畜"),
    "蚕茧": ("蚕", "畜"),
    "柞蚕": ("蚕", "畜"),
    "桑蚕": ("蚕", "畜"),
    "鸡蛋": ("蛋", "畜"),
    "鸭蛋": ("蛋", "畜"),
    "奶制品": ("乳制品", "畜"),
    "水牛奶": ("乳制品", "畜"),
    "牛乳": ("乳制品", "畜"),
    "白鹅": ("鹅", "畜"),
    "肉鹅": ("鹅", "畜"),
    "肉鸽": ("鸽", "畜"),
    "鸽": ("鸽", "畜"),
    "梅花鹿": ("鹿", "畜"),
    "鹿": ("鹿", "畜"),
    # -------------------- 花类 --------------------
    "花": ("花卉苗木", "花"),
    "花卉": ("花卉苗木", "花"),
    "花卉苗木": ("花卉苗木", "花"),
    "花木": ("花卉苗木", "花"),
    "苗木": ("花卉苗木", "花"),
    "热带树苗": ("花卉苗木", "花"),
    "万寿菊": ("菊花", "花"),
    "菊花": ("菊花", "花"),
    "茶花": ("茶花", "花"),
    # -------------------- 其他类 --------------------
    "葡萄酒": ("葡萄酒", "其他"),
    "旅游": ("旅游", "其他"),
    "花卉、旅游": ("旅游", "其他"),
    "木材": ("木材", "其他"),
    "渔网制作": ("渔网制作", "其他"),
    "肉桂": ("肉桂", "其他"),
    "肉桂八角": ("肉桂", "其他"),
    "芝麻油": ("芝麻油", "其他"),
    "花灯": ("花灯", "其他"),
    "果品加工": ("果品加工", "其他"),
    "畜产品加工": ("畜产品", "畜"),
    "捕捞、养殖": ("捕捞", "渔"),
    "海洋捕捞": ("捕捞", "渔"),
}

# ========== 加载村庄数据（从CSV） ==========
villages_data = []
provinces_data = []
categories_data = []

def load_villages():
    global villages_data, provinces_data, categories_data
    try:
        df = pd.read_csv(CSV_PATH, encoding='utf-8-sig')
        print(f"📄 CSV 文件路径: {CSV_PATH}")
        print(f"📏 CSV 文件总行数（含表头）: {len(df)}")
        villages_data = df.to_dict(orient='records')
        # 清洗 NaN
        import math
        for item in villages_data:
            for k, v in item.items():
                if isinstance(v, float) and math.isnan(v):
                    item[k] = None
        # 统一 baike_urls 分隔符为竖线 |
        import re
        for item in villages_data:
            urls = item.get('baike_urls')
            if urls and isinstance(urls, str):
                # 将所有常见分隔符（中文逗号、英文逗号、分号、顿号、空格等）替换为竖线
                unified = re.sub(r'[，,;；、\s]+', '|', urls)
                parts = [u.strip() for u in unified.split('|') if u.strip()]
                item['baike_urls'] = '|'.join(parts)
            elif urls is None:
                item['baike_urls'] = ''
        # 应用标准化映射
        for item in villages_data:
            original_sub = item.get('sub_category', '')
            if isinstance(original_sub, str):
                original_sub = original_sub.strip()
            if original_sub in CATEGORY_MAPPING:
                new_sub, new_industry = CATEGORY_MAPPING[original_sub]
                item['sub_category'] = new_sub
                item['industry_type'] = new_industry
        # 后续统计
        province_stats = {}
        for v in villages_data:
            p = v.get('province', '未知')
            province_stats[p] = province_stats.get(p, 0) + 1
        provinces_data = [{'name': p, 'count': c} for p, c in province_stats.items()]
        category_stats = {}
        for v in villages_data:
            cat = v.get('industry_type', '其他')
            category_stats[cat] = category_stats.get(cat, 0) + 1
        categories_data = [{'name': c, 'count': cnt} for c, cnt in category_stats.items()]
        print(f"✅ 统计完成: {len(provinces_data)} 个省份, {len(categories_data)} 个分类")
    except Exception as e:
        print(f"❌ 加载失败: {e}")
        villages_data = []
        provinces_data = []
        categories_data = []
load_villages()

# ========== 基础API（无需认证） ==========
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
         keyword_lower = keyword.lower()
         result = [v for v in result if (
             keyword_lower in str(v.get('name', '')).lower() or
             keyword_lower in str(v.get('product_name', '')).lower() or
             keyword_lower in str(v.get('province', '')).lower() or
             keyword_lower in str(v.get('city', '')).lower() or
             keyword_lower in str(v.get('sub_category', '')).lower() or
             keyword_lower in str(v.get('industry_type', '')).lower()
    )]
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

# ========== 用户认证 ==========
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
    import uuid
    token = str(uuid.uuid4())
    c.execute('INSERT INTO sessions (user_id, token) VALUES (?, ?)', (row['id'], token))
    db.commit()
    return jsonify({'token': token, 'user_id': row['id'], 'username': username})

@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_profile():
    db = get_db()
    c = db.cursor()
    c.execute('''
        SELECT id, username, nickname, avatar, signature, gender, birthday,
               province, city, district, created_at, theme_preference
        FROM users WHERE id = ?
    ''', (request.user_id,))
    row = c.fetchone()
    if not row:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(row))

# 获取用户完整资料（含扩展字段）
@app.route('/api/user/profile', methods=['GET'])
@login_required
def get_user_profile():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id, username, nickname, avatar, signature, gender, birthday, province, city, district, created_at, theme_preference FROM users WHERE id = ?', (request.user_id,))
    row = c.fetchone()
    if not row:
        return jsonify({'error': 'User not found'}), 404
    return jsonify(dict(row))

# 更新用户资料
@app.route('/api/user/profile', methods=['PUT'])
@login_required
def update_user_profile():
    data = request.get_json()
    allowed_fields = ['nickname', 'avatar', 'signature', 'gender', 'birthday', 'province', 'city', 'district', 'theme_preference']
    update_fields = {k: v for k, v in data.items() if k in allowed_fields}
    if not update_fields:
        return jsonify({'error': 'No valid fields'}), 400
    set_clause = ', '.join([f"{k} = ?" for k in update_fields.keys()])
    values = list(update_fields.values()) + [request.user_id]
    db = get_db()
    c = db.cursor()
    c.execute(f"UPDATE users SET {set_clause} WHERE id = ?", values)
    db.commit()
    return jsonify({'message': 'Profile updated'}), 200

# 上传头像
@app.route('/api/user/avatar', methods=['POST'])
@login_required
def upload_avatar():
    if 'avatar' not in request.files:
        return jsonify({'error': 'No file'}), 400
    file = request.files['avatar']
    if file.filename == '':
        return jsonify({'error': 'Empty file'}), 400
    import os, time, uuid
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ['jpg', 'jpeg', 'png', 'gif']:
        return jsonify({'error': 'Invalid format'}), 400
    filename = f"{request.user_id}_{uuid.uuid4().hex}.{ext}"
    save_dir = os.path.join(BASE_DIR, 'static', 'avatars')
    os.makedirs(save_dir, exist_ok=True)
    file.save(os.path.join(save_dir, filename))
    avatar_url = f'/static/avatars/{filename}'
    db = get_db()
    c = db.cursor()
    c.execute('UPDATE users SET avatar = ? WHERE id = ?', (avatar_url, request.user_id))
    db.commit()
    return jsonify({'avatar_url': avatar_url}), 200

# 获取用户评论列表
@app.route('/api/user/comments', methods=['GET'])
@login_required
def get_user_comments():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT id, village_id, content, like_count, created_at FROM comments WHERE user_id = ? ORDER BY created_at DESC', (request.user_id,))
    rows = c.fetchall()
    result = []
    for row in rows:
        village = next((v for v in villages_data if v.get('id') == row['village_id']), None)
        result.append({
            'id': row['id'],
            'village_id': row['village_id'],
            'content': row['content'],
            'like_count': row['like_count'],
            'created_at': row['created_at'],
            'village_name': village.get('name') if village else '未知村庄'
        })
    return jsonify(result)

# 获取用户统计数据
@app.route('/api/user/stats', methods=['GET'])
@login_required
def get_user_stats():
    db = get_db()
    c = db.cursor()
    c.execute('SELECT COUNT(*) as favorites FROM favorites WHERE user_id = ?', (request.user_id,))
    fav = c.fetchone()['favorites']
    c.execute('SELECT COUNT(*) as wants FROM wants WHERE user_id = ?', (request.user_id,))
    want = c.fetchone()['wants']
    c.execute('SELECT COUNT(*) as likes FROM village_likes WHERE user_id = ?', (request.user_id,))
    like = c.fetchone()['likes']
    c.execute('SELECT COUNT(*) as comments FROM comments WHERE user_id = ?', (request.user_id,))
    comment = c.fetchone()['comments']
    return jsonify({
        'favorites': fav,
        'wants': want,
        'likes': like,
        'comments': comment,
        'publish_count': 0  # 预留
    })

# ========== 收藏/想去/点赞（村庄） ==========
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

@app.route('/api/villages/<int:id>/comments', methods=['GET'])
def get_village_comments(id):
    """获取某个村庄的所有评论（扁平列表，包含 parent_id）"""
    db = get_db()
    c = db.cursor()
    c.execute('''
        SELECT c.id, c.user_id, c.content, c.like_count, c.created_at,
               c.parent_id, u.username
        FROM comments c
        JOIN users u ON c.user_id = u.id
        WHERE c.village_id = ?
        ORDER BY c.created_at ASC
    ''', (id,))
    comments = [dict(row) for row in c.fetchall()]
    return jsonify(comments)


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
    parent_id = data.get('parent_id')
    if not village_id or not content:
        return jsonify({'error': 'Missing fields'}), 400
    db = get_db()
    c = db.cursor()
    c.execute('INSERT INTO comments (village_id, user_id, content, parent_id) VALUES (?, ?, ?, ?)',
              (village_id, request.user_id, content, parent_id))
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
        'parent_id': parent_id,
        'created_at': datetime.now().isoformat()
    }), 201

@app.route('/api/comments/village/<int:id>', methods=['GET'])
def get_comments_for_village(id):
    db = get_db()
    c = db.cursor()
    current_user_id = get_current_user_id()
    if current_user_id:
        c.execute('''
            SELECT c.id, c.user_id, c.content, c.like_count, c.created_at,
                   c.parent_id, u.username,
                   EXISTS(SELECT 1 FROM comment_likes cl WHERE cl.comment_id = c.id AND cl.user_id = ?) as user_liked
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.village_id = ?
            ORDER BY c.created_at ASC
        ''', (current_user_id, id))
    else:
        c.execute('''
            SELECT c.id, c.user_id, c.content, c.like_count, c.created_at,
                   c.parent_id, u.username,
                   0 as user_liked
            FROM comments c
            JOIN users u ON c.user_id = u.id
            WHERE c.village_id = ?
            ORDER BY c.created_at ASC
        ''', (id,))
    comments = [dict(row) for row in c.fetchall()]
    return jsonify(comments)

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
    current_user_id = get_current_user_id()
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
        if current_user_id is not None:
            c.execute('''
                SELECT c.id, c.user_id, c.content, c.like_count, c.created_at, u.username,
                       EXISTS(SELECT 1 FROM comment_likes cl WHERE cl.comment_id = c.id AND cl.user_id = ?) as user_liked
                FROM comments c
                JOIN users u ON c.user_id = u.id
                WHERE c.village_id = ?
                ORDER BY c.like_count DESC
                LIMIT 5
            ''', (current_user_id, village_id))
        else:
            c.execute('''
                SELECT c.id, c.user_id, c.content, c.like_count, c.created_at, u.username,
                       0 as user_liked
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

@app.route('/static/avatars/<path:filename>')
def serve_avatar(filename):
    return send_from_directory(os.path.join(BASE_DIR, 'static', 'avatars'), filename)

if __name__ == '__main__':
    app.run(debug=True, port=5000)