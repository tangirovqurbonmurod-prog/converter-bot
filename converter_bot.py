# ============================================================
# EDUBOT v12 — Professional Ta'lim Boti
# 3 tilda (O'zbek, Rus, Ingliz) | Imlo xatosiz | Barcha xizmatlar
# ============================================================
import telebot, os, sqlite3, logging, tempfile, shutil, requests, re, math
from telebot import types
from datetime import datetime
from io import BytesIO

# ============================================================
# SOZLAMALAR
# ============================================================
BOT_TOKEN      = os.environ.get("BOT_TOKEN",      "")
ADMIN_ID       = int(os.environ.get("ADMIN_ID",   "1113404703"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "@abdurakhmon02")
DONATE_URL     = os.environ.get("DONATE_URL",     "https://click.uz")
DONATE_CARD    = os.environ.get("DONATE_CARD",    "9860 0609 2665 0809")
DONATE_CLICK   = os.environ.get("DONATE_CLICK",   "+998 94 975 03 04")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")
UNSPLASH_KEY   = os.environ.get("UNSPLASH_KEY",   "")
SONNET_MODEL   = os.environ.get("SONNET_MODEL", "claude-sonnet-4-5-20251001")
HAIKU_MODEL    = "claude-haiku-4-5-20251001"

def gp(n, d): return int(os.environ.get(n, str(d)))
PRICE_PAGE     = gp("PRICE_PAGE",    300)
PRICE_KURS     = gp("PRICE_KURS",    250)
PRICE_MUSTAQIL = gp("PRICE_MUSTAQIL",280)
PRICE_MAQOLA   = gp("PRICE_MAQOLA",  400)
PRICE_SLIDE    = gp("PRICE_SLIDE",   300)
PRICE_TEST     = gp("PRICE_TEST",    150)
BONUS_FIRST    = gp("BONUS_FIRST",  3000)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

# ============================================================
# KO'P TILLI LUGAT
# ============================================================
TEXTS = {
    "uz": {
        "welcome": "👋 Xush kelibsiz, {name}!\n\n🎓 *EduBot* — Ta'lim yordamchingiz!\n\n📚 Xizmatlar:\n📄 Referat | 📝 Kurs ishi | 📋 Mustaqil ish\n📰 Maqola | 📊 Prezentatsiya | ✅ Test\n✏️ Imlo tuzatish | 🔄 Konvertatsiya",
        "bonus": "\n\n🎁 *{amount:,} so'm bonus berildi!*",
        "choose_lang": "\n\nTilni tanlang:",
        "menu": "📋 Asosiy menyu:",
        "enter_topic": "📝 Mavzuni kiriting:",
        "enter_pages": "📄 Necha bet? (5-100)\n💰 1 bet = {price:,} so'm",
        "enter_slides": "🎯 Necha slayd? (10-50)\n💰 1 slayd = {price:,} so'm",
        "enter_count": "🔢 Nechta savol? (10-1000)\n💰 1 savol = {price:,} so'm",
        "ask_name": "👤 Ism va familiyangizni kiriting:",
        "ask_univ": "🏛 Universitetingiz nomi:",
        "ask_faculty": "📚 Fakultetingiz:",
        "ask_year": "📅 Nechinchi kurs?",
        "ask_teacher": "👩‍🏫 O'qituvchi ismi:",
        "ask_subject": "📖 Fan nomi:",
        "ask_city": "🏙 Shahar:",
        "optional": "(ixtiyoriy — o'tkazib yuborish mumkin)",
        "ask_lang": "🌐 Qaysi tilda?",
        "ask_format": "📁 Format tanlang:",
        "ask_plans": "📋 Nechta bo'lim (reja) bo'lsin?",
        "ask_template": "🎨 Shablon tanlang:",
        "preparing": "⏳ Tayyorlanmoqda... Iltimos kuting.",
        "ready": "✅ Tayyor!\n💰 Balans: {bal:,} so'm",
        "error": "❌ Xatolik yuz berdi. Pul qaytarildi.",
        "no_balance": "❌ Mablag' yetarli emas!\nKerakli: {need:,} so'm\nBalans: {bal:,} so'm\n\nBalansni to'ldiring:",
        "balance_info": "💰 *Balansingiz: {bal:,} so'm*",
        "topup": "💳 Balans to'ldirish",
        "back": "◀️ Orqaga",
        "home": "🏠 Menyu",
        "skip": "⏭ O'tkazib yuborish",
        "lang_set": "✅ Til o'rnatildi: O'zbek 🇺🇿",
        "no_orders": "📦 Hozircha buyurtmalaringiz yo'q.\n\nBirinchi buyurtmangizni bering!",
        "orders_title": "📦 *Oxirgi buyurtmalaringiz:*\n\n",
        "write_topic": "📝 Mavzuni kiriting:",
        "img_accept": "🖼 Rasm qabul qilindi! Qaysi slaydga qo'yish kerak?",
        "img_count": "✅ {n} ta rasm qabul qilindi. /done yozing.",
        "converting": "⏳ Konvertatsiya amalga oshirilmoqda...",
        "wrong_format": "❌ Noto'g'ri format.",
        "imlo_check": "⏳ Imlo tekshirilmoqda...",
        "imlo_done": "✅ *Imlo tuzatildi:*\n\n",
        "imlo_notfound": "❌ Matn topilmadi.",
        "imlo_prompt": "✏️ Matnni yozing yoki fayl (PDF/TXT) yuboring:",
        "ai_img": "🤖 AI avtomatik rasm qo'ysin",
        "user_img": "🖼 O'zim rasm yuklаyman",
        "no_img": "❌ Rasmsiz davom etish",
        "help_text": "❓ *Yordam*\n\n📄 /referat — Referat\n📝 /kursishi — Kurs ishi\n📋 /mustaqilish — Mustaqil ish\n📰 /maqola — Maqola\n📊 /prezentatsiya — Prezentatsiya\n✅ /test — Test\n✏️ /imlo — Imlo tuzatish\n🔄 /konvertatsiya — Konvertatsiya\n💰 /balans — Balans",
        "prices": "💵 *Narxlar:*\n📄 Referat: {p1:,}/bet\n📝 Kurs ishi: {p2:,}/bet\n📋 Mustaqil: {p3:,}/bet\n📰 Maqola: {p4:,}/bet\n📊 Prezentatsiya: {p5:,}/slayd\n✅ Test: {p6:,}/savol",
        "btn_referat": "📄 Referat",
        "btn_kurs": "📝 Kurs ishi",
        "btn_mustaqil": "📋 Mustaqil ish",
        "btn_maqola": "📰 Maqola",
        "btn_prez": "📊 Prezentatsiya",
        "btn_test": "✅ Test",
        "btn_imlo": "✏️ Imlo tuzatish",
        "btn_konv": "🔄 Konvertatsiya",
        "btn_balans": "💰 Balans",
        "btn_orders": "📦 Buyurtmalarim",
        "btn_donat": "💝 Donat",
        "btn_help": "❓ Yordam",
        "btn_admin": "👨‍💼 Admin",
        "slide_pages": "slayd",
        "bet_pages": "bet",
        "savol_pages": "savol",
    },
    "ru": {
        "welcome": "👋 Добро пожаловать, {name}!\n\n🎓 *EduBot* — Ваш учебный помощник!\n\n📚 Услуги:\n📄 Реферат | 📝 Курсовая | 📋 Самостоятельная\n📰 Статья | 📊 Презентация | ✅ Тест\n✏️ Проверка орфографии | 🔄 Конвертация",
        "bonus": "\n\n🎁 *Начислено {amount:,} сум бонус!*",
        "choose_lang": "\n\nВыберите язык:",
        "menu": "📋 Главное меню:",
        "enter_topic": "📝 Введите тему:",
        "enter_pages": "📄 Сколько страниц? (5-100)\n💰 1 стр = {price:,} сум",
        "enter_slides": "🎯 Сколько слайдов? (10-50)\n💰 1 слайд = {price:,} сум",
        "enter_count": "🔢 Сколько вопросов? (10-1000)\n💰 1 вопрос = {price:,} сум",
        "ask_name": "👤 Введите имя и фамилию:",
        "ask_univ": "🏛 Название университета:",
        "ask_faculty": "📚 Факультет:",
        "ask_year": "📅 Курс (1-4)?",
        "ask_teacher": "👩‍🏫 Имя преподавателя:",
        "ask_subject": "📖 Название предмета:",
        "ask_city": "🏙 Город:",
        "optional": "(необязательно — можно пропустить)",
        "ask_lang": "🌐 На каком языке?",
        "ask_format": "📁 Выберите формат:",
        "ask_plans": "📋 Сколько разделов?",
        "ask_template": "🎨 Выберите шаблон:",
        "preparing": "⏳ Подготавливается... Пожалуйста, подождите.",
        "ready": "✅ Готово!\n💰 Баланс: {bal:,} сум",
        "error": "❌ Произошла ошибка. Деньги возвращены.",
        "no_balance": "❌ Недостаточно средств!\nНужно: {need:,} сум\nБаланс: {bal:,} сум\n\nПополните баланс:",
        "balance_info": "💰 *Ваш баланс: {bal:,} сум*",
        "topup": "💳 Пополнить баланс",
        "back": "◀️ Назад",
        "home": "🏠 Меню",
        "skip": "⏭ Пропустить",
        "lang_set": "✅ Язык установлен: Русский 🇷🇺",
        "no_orders": "📦 У вас пока нет заказов.\n\nСделайте первый заказ!",
        "orders_title": "📦 *Ваши последние заказы:*\n\n",
        "write_topic": "📝 Введите тему:",
        "img_accept": "🖼 Фото принято! На какой слайд добавить?",
        "img_count": "✅ Принято {n} фото. Напишите /done.",
        "converting": "⏳ Конвертация выполняется...",
        "wrong_format": "❌ Неверный формат.",
        "imlo_check": "⏳ Проверка орфографии...",
        "imlo_done": "✅ *Орфография исправлена:*\n\n",
        "imlo_notfound": "❌ Текст не найден.",
        "imlo_prompt": "✏️ Напишите текст или отправьте файл (PDF/TXT):",
        "ai_img": "🤖 AI добавит фото автоматически",
        "user_img": "🖼 Загружу сам",
        "no_img": "❌ Без фото",
        "help_text": "❓ *Помощь*\n\n📄 /referat — Реферат\n📝 /kursishi — Курсовая\n📋 /mustaqilish — Самостоятельная\n📰 /maqola — Статья\n📊 /prezentatsiya — Презентация\n✅ /test — Тест\n✏️ /imlo — Орфография\n🔄 /konvertatsiya — Конвертация\n💰 /balans — Баланс",
        "prices": "💵 *Цены:*\n📄 Реферат: {p1:,}/стр\n📝 Курсовая: {p2:,}/стр\n📋 Самост.: {p3:,}/стр\n📰 Статья: {p4:,}/стр\n📊 Презент.: {p5:,}/слайд\n✅ Тест: {p6:,}/вопрос",
        "btn_referat": "📄 Реферат",
        "btn_kurs": "📝 Курсовая",
        "btn_mustaqil": "📋 Самостоятельная",
        "btn_maqola": "📰 Статья",
        "btn_prez": "📊 Презентация",
        "btn_test": "✅ Тест",
        "btn_imlo": "✏️ Орфография",
        "btn_konv": "🔄 Конвертация",
        "btn_balans": "💰 Баланс",
        "btn_orders": "📦 Мои заказы",
        "btn_donat": "💝 Донат",
        "btn_help": "❓ Помощь",
        "btn_admin": "👨‍💼 Админ",
        "slide_pages": "слайдов",
        "bet_pages": "стр",
        "savol_pages": "вопросов",
    },
    "en": {
        "welcome": "👋 Welcome, {name}!\n\n🎓 *EduBot* — Your Educational Assistant!\n\n📚 Services:\n📄 Essay | 📝 Course Work | 📋 Independent Work\n📰 Article | 📊 Presentation | ✅ Test\n✏️ Spell Check | 🔄 Convert",
        "bonus": "\n\n🎁 *{amount:,} sum bonus added!*",
        "choose_lang": "\n\nChoose language:",
        "menu": "📋 Main menu:",
        "enter_topic": "📝 Enter topic:",
        "enter_pages": "📄 How many pages? (5-100)\n💰 1 page = {price:,} sum",
        "enter_slides": "🎯 How many slides? (10-50)\n💰 1 slide = {price:,} sum",
        "enter_count": "🔢 How many questions? (10-1000)\n💰 1 question = {price:,} sum",
        "ask_name": "👤 Enter your name:",
        "ask_univ": "🏛 University name:",
        "ask_faculty": "📚 Faculty:",
        "ask_year": "📅 Year (1-4)?",
        "ask_teacher": "👩‍🏫 Teacher's name:",
        "ask_subject": "📖 Subject name:",
        "ask_city": "🏙 City:",
        "optional": "(optional — you can skip)",
        "ask_lang": "🌐 In which language?",
        "ask_format": "📁 Choose format:",
        "ask_plans": "📋 How many sections?",
        "ask_template": "🎨 Choose template:",
        "preparing": "⏳ Preparing... Please wait.",
        "ready": "✅ Done!\n💰 Balance: {bal:,} sum",
        "error": "❌ An error occurred. Money refunded.",
        "no_balance": "❌ Insufficient balance!\nNeeded: {need:,} sum\nBalance: {bal:,} sum\n\nTop up balance:",
        "balance_info": "💰 *Your balance: {bal:,} sum*",
        "topup": "💳 Top up balance",
        "back": "◀️ Back",
        "home": "🏠 Menu",
        "skip": "⏭ Skip",
        "lang_set": "✅ Language set: English 🇬🇧",
        "no_orders": "📦 No orders yet.\n\nMake your first order!",
        "orders_title": "📦 *Your recent orders:*\n\n",
        "write_topic": "📝 Enter topic:",
        "img_accept": "🖼 Photo accepted! Which slide to add to?",
        "img_count": "✅ {n} photos received. Type /done.",
        "converting": "⏳ Converting...",
        "wrong_format": "❌ Wrong format.",
        "imlo_check": "⏳ Checking spelling...",
        "imlo_done": "✅ *Spelling corrected:*\n\n",
        "imlo_notfound": "❌ Text not found.",
        "imlo_prompt": "✏️ Write text or send file (PDF/TXT):",
        "ai_img": "🤖 AI auto add photos",
        "user_img": "🖼 I'll upload myself",
        "no_img": "❌ Without photos",
        "help_text": "❓ *Help*\n\n📄 /referat — Essay\n📝 /kursishi — Course Work\n📋 /mustaqilish — Independent\n📰 /maqola — Article\n📊 /prezentatsiya — Presentation\n✅ /test — Test\n✏️ /imlo — Spell Check\n🔄 /konvertatsiya — Convert\n💰 /balans — Balance",
        "prices": "💵 *Prices:*\n📄 Essay: {p1:,}/page\n📝 Course: {p2:,}/page\n📋 Independent: {p3:,}/page\n📰 Article: {p4:,}/page\n📊 Presentation: {p5:,}/slide\n✅ Test: {p6:,}/question",
        "btn_referat": "📄 Essay",
        "btn_kurs": "📝 Course Work",
        "btn_mustaqil": "📋 Independent",
        "btn_maqola": "📰 Article",
        "btn_prez": "📊 Presentation",
        "btn_test": "✅ Test",
        "btn_imlo": "✏️ Spell Check",
        "btn_konv": "🔄 Convert",
        "btn_balans": "💰 Balance",
        "btn_orders": "📦 My Orders",
        "btn_donat": "💝 Donate",
        "btn_help": "❓ Help",
        "btn_admin": "👨‍💼 Admin",
        "slide_pages": "slides",
        "bet_pages": "pages",
        "savol_pages": "questions",
    }
}

def t(uid, key, **kwargs):
    """Foydalanuvchi tiliga mos matn"""
    lang = get_lang(uid)
    text = TEXTS.get(lang, TEXTS["uz"]).get(key, TEXTS["uz"].get(key, key))
    if kwargs:
        try: text = text.format(**kwargs)
        except: pass
    return text

LN = {"uz": "o'zbek", "ru": "rus", "en": "ingliz"}

# ============================================================
# DATABASE
# ============================================================
def init_db():
    c = sqlite3.connect("edubot.db")
    cur = c.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(
        telegram_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        lang TEXT DEFAULT 'uz', balance INTEGER DEFAULT 0, joined_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS orders(
        telegram_id INTEGER PRIMARY KEY, state TEXT, data TEXT, updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS stats(
        id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER,
        action TEXT, detail TEXT, income INTEGER DEFAULT 0, created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS buyurtmalar(
        id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER,
        tur TEXT, mavzu TEXT, format TEXT, sahifalar TEXT,
        narx INTEGER, created_at TEXT)""")
    c.commit(); c.close()

import json

def save_order(uid, state, data):
    try:
        c = sqlite3.connect("edubot.db"); cur = c.cursor()
        cur.execute("INSERT OR REPLACE INTO orders VALUES(?,?,?,?)",
            (uid, state, json.dumps(data, ensure_ascii=False),
             datetime.now().strftime("%d.%m.%Y %H:%M")))
        c.commit(); c.close()
    except: pass

def load_order(uid):
    try:
        c = sqlite3.connect("edubot.db"); cur = c.cursor()
        cur.execute("SELECT state,data FROM orders WHERE telegram_id=?", (uid,))
        row = cur.fetchone(); c.close()
        if row: return row[0], json.loads(row[1])
    except: pass
    return None, {}

def clear_order(uid):
    try:
        c = sqlite3.connect("edubot.db"); cur = c.cursor()
        cur.execute("DELETE FROM orders WHERE telegram_id=?", (uid,))
        c.commit(); c.close()
    except: pass

def get_user(uid):
    c = sqlite3.connect("edubot.db"); cur = c.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id=?", (uid,))
    row = cur.fetchone(); c.close()
    return {"id": row[0], "username": row[1], "first_name": row[2],
            "lang": row[3], "balance": row[4]} if row else None

def reg_user(uid, uname, fname, lang="uz"):
    c = sqlite3.connect("edubot.db"); cur = c.cursor()
    cur.execute("SELECT telegram_id FROM users WHERE telegram_id=?", (uid,))
    ex = cur.fetchone()
    if not ex:
        cur.execute("INSERT INTO users VALUES(?,?,?,?,?,?)",
            (uid, uname, fname, lang, BONUS_FIRST,
             datetime.now().strftime("%d.%m.%Y %H:%M")))
        c.commit(); c.close(); return True
    cur.execute("UPDATE users SET username=?,first_name=? WHERE telegram_id=?",
        (uname, fname, uid))
    c.commit(); c.close(); return False

def get_lang(uid):
    u = get_user(uid); return u["lang"] if u else "uz"

def set_lang(uid, lang):
    c = sqlite3.connect("edubot.db"); cur = c.cursor()
    cur.execute("UPDATE users SET lang=? WHERE telegram_id=?", (lang, uid))
    c.commit(); c.close()

def get_balance(uid):
    u = get_user(uid); return u["balance"] if u else 0

def deduct(uid, amt):
    c = sqlite3.connect("edubot.db"); cur = c.cursor()
    cur.execute("UPDATE users SET balance=balance-? WHERE telegram_id=?", (amt, uid))
    c.commit(); c.close()

def add_bal(uid, amt):
    c = sqlite3.connect("edubot.db"); cur = c.cursor()
    cur.execute("UPDATE users SET balance=balance+? WHERE telegram_id=?", (amt, uid))
    c.commit(); c.close()

def log_act(uid, action, detail="", income=0):
    c = sqlite3.connect("edubot.db"); cur = c.cursor()
    cur.execute("INSERT INTO stats(telegram_id,action,detail,income,created_at) VALUES(?,?,?,?,?)",
        (uid, action, detail, income, datetime.now().strftime("%d.%m.%Y %H:%M")))
    c.commit(); c.close()

def save_buyurtma(uid, tur, mavzu, fmt, sah, narx):
    try:
        c = sqlite3.connect("edubot.db"); cur = c.cursor()
        cur.execute("INSERT INTO buyurtmalar(telegram_id,tur,mavzu,format,sahifalar,narx,created_at) VALUES(?,?,?,?,?,?,?)",
            (uid, tur, mavzu, fmt, str(sah), narx, datetime.now().strftime("%d.%m.%Y %H:%M")))
        c.commit(); c.close()
    except: pass

def get_buyurtmalar(uid):
    try:
        c = sqlite3.connect("edubot.db"); cur = c.cursor()
        cur.execute("SELECT tur,mavzu,format,sahifalar,narx,created_at FROM buyurtmalar WHERE telegram_id=? ORDER BY id DESC LIMIT 10", (uid,))
        rows = cur.fetchall(); c.close(); return rows
    except: return []

def all_users():
    c = sqlite3.connect("edubot.db"); cur = c.cursor()
    cur.execute("SELECT telegram_id FROM users")
    rows = cur.fetchall(); c.close()
    return [r[0] for r in rows]

def get_stats():
    c = sqlite3.connect("edubot.db"); cur = c.cursor()
    cur.execute("SELECT COUNT(*) FROM users"); u = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stats WHERE action IN ('referat','kurs','mustaqil','maqola','prez','test')"); w = cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stats WHERE action='conv'"); cv = cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(income),0) FROM stats"); i = cur.fetchone()[0]
    c.close(); return u, w, cv, i

# ============================================================
# HOLAT BOSHQARUVI
# ============================================================
ST, UD, UI = {}, {}, {}
HISTORY = {}

def sst(uid, s, **kw):
    prev = ST.get(uid)
    if prev and prev != s:
        HISTORY.setdefault(uid, []).append(prev)
        if len(HISTORY[uid]) > 20:
            HISTORY[uid] = HISTORY[uid][-20:]
    ST[uid] = s
    UD.setdefault(uid, {}).update(kw)
    save_order(uid, s, UD.get(uid, {}))

def gst(uid): return ST.get(uid)

def cst(uid):
    ST.pop(uid, None)
    HISTORY.pop(uid, None)
    clear_order(uid)

def go_back(uid):
    h = HISTORY.get(uid, [])
    if not h: return None
    prev = h.pop()
    HISTORY[uid] = h
    ST[uid] = prev
    return prev

def restore_state(uid):
    state, data = load_order(uid)
    if state and data:
        ST[uid] = state; UD[uid] = data; return True
    return False

def build_info(ud):
    parts = []
    for k, lbl in [("full_name","Muallif"), ("subject","Fan"), ("university","Universitet"),
                   ("faculty","Fakultet"), ("year","Kurs"), ("teacher","O'qituvchi"), ("city","Shahar")]:
        if ud.get(k): parts.append(f"{lbl}: {ud[k]}")
    return "\n".join(parts)

# ============================================================
# CLAUDE API
# ============================================================
def claude(prompt, system="", max_tok=4000, model=None):
    if not CLAUDE_API_KEY:
        return "Claude API sozlanmagan!"
    if model is None:
        model = HAIKU_MODEL
    try:
        r = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "x-api-key": CLAUDE_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json"
            },
            json={
                "model": model,
                "max_tokens": max_tok,
                "system": system,
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=180
        )
        if r.status_code == 200:
            return r.json()["content"][0]["text"]
        else:
            logger.error(f"Claude API error: {r.status_code} {r.text}")
            return f"API xatosi: {r.status_code}"
    except Exception as e:
        logger.error(f"Claude xato: {e}")
        return f"Xatolik: {e}"

def clean_text(text):
    """AI javobidan keraksiz belgilarni tozalash"""
    import re as _re
    text = _re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=_re.DOTALL)
    text = _re.sub(r'\*(.+?)\*', r'\1', text)
    text = _re.sub(r'#{1,6}\s*', '', text)
    text = _re.sub(r'[`~]', '', text)
    text = _re.sub(r'\n{3,}', '\n\n', text)
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not (line.upper().startswith('SLAYD') or
                line.upper().startswith('SLIDE') or
                line.upper().startswith('INFOGRAFIKA')):
            line = _re.sub(r'^[-•►▸*]+\s*', '', line)
        lines.append(line)
    return '\n'.join(lines).strip()

# ============================================================
# MAZMUN YARATISH
# ============================================================
def gen_prez(topic, slides, lang, ud={}, plans=5):
    """Prezentatsiya mazmuni yaratish"""
    ln = LN.get(lang, "o'zbek")
    info = build_info(ud)
    subject = f"\nFan: {ud['subject']}" if ud.get('subject') else ""
    prompt = (
        f"Mavzu: {topic}\nSlaydlar soni: {slides}\nTil: {ln}\n{info}{subject}\n\n"
        f"QOIDA: Har slayd SLAYD N: bilan boshlansin. Markdown taqiqlangan. Til: {ln}\n\n"
        f"SLAYD 1: {topic}\n"
        f"[kirish matni]\n\n"
        f"SLAYD 2: Reja\n"
        f"1. Birinchi bolim\n"
        f"2. Ikkinchi bolim\n\n"
        f"SLAYD 3: [sarlavha]\n"
        f"[4-5 ta fakt]\n\n"
        f"SLAYD {slides}: Xulosa\n"
        f"[xulosalar. Jami {slides} ta slayd bo'lsin]"
    )
    system = (
        f"Sen prezentatsiya yaratuvchisan. "
        f"SLAYD N: formatini QATIY ushla. "
        f"Markdown belgisi ISHLATMA. Til: {ln}."
    )
    result = claude(prompt, system, 4000, model=SONNET_MODEL)
    logger.info(f'PREZ_RESULT: {result[:800]}')
    result = result.replace('**', '').replace('## ', '').replace('# ', '').replace('##', '').replace('#', '')
    return result
def gen_doc(svc, topic, pages, lang, ud={}):
    """Hujjat yaratish (referat, kurs ishi, maqola, mustaqil)"""
    ln = LN.get(lang, "o'zbek")
    info = build_info(ud)
    wpg = {"referat": 300, "kurs": 350, "mustaqil": 280, "maqola": 320}.get(svc, 300)
    subject = f"\nFan: {ud['subject']}" if ud.get('subject') else ""

    structs = {
        "referat": (
            "KIRISH (200+ so'z)\n"
            "I BOB — Nazariy asoslar (300+ so'z)\n"
            "II BOB — Tahlil va muhokama (300+ so'z)\n"
            "III BOB — Amaliy qo'llanish (300+ so'z)\n"
            "XULOSA (150+ so'z)\n"
            "FOYDALANILGAN ADABIYOTLAR (10 ta manba)"
        ),
        "kurs": (
            "MUNDARIJA\n"
            "KIRISH — maqsad, vazifalar, dolzarblik (300+ so'z)\n"
            "I BOB — Nazariy asos (400+ so'z)\n"
            "II BOB — Tahlil va tadqiqot (400+ so'z)\n"
            "III BOB — Tavsiyalar va xulosalar (300+ so'z)\n"
            "XULOSA (200+ so'z)\n"
            "FOYDALANILGAN ADABIYOTLAR (15 ta APA)\n"
            "ILOVALAR"
        ),
        "mustaqil": (
            "KIRISH (200+ so'z)\n"
            "ASOSIY QISM 1 (300+ so'z)\n"
            "ASOSIY QISM 2 (300+ so'z)\n"
            "XULOSA (150+ so'z)\n"
            "FOYDALANILGAN ADABIYOTLAR (8 ta)"
        ),
        "maqola": (
            "ANNOTATSIYA (150 so'z)\n"
            "KALIT SO'ZLAR (7 ta)\n"
            "ABSTRACT (inglizcha, 150 so'z)\n"
            "KEYWORDS (7 ta)\n"
            "KIRISH (300+ so'z)\n"
            "ADABIYOTLAR TAHLILI (250+ so'z)\n"
            "METODOLOGIYA (200+ so'z)\n"
            "NATIJALAR VA MUHOKAMA (400+ so'z)\n"
            "XULOSA (200+ so'z)\n"
            "FOYDALANILGAN ADABIYOTLAR (15 ta APA)"
        )
    }
    names = {"referat": "referat", "kurs": "kurs ishi", "mustaqil": "mustaqil ish", "maqola": "ilmiy maqola"}
    struct = structs.get(svc, structs["referat"])
    use_model = SONNET_MODEL if svc in ("kurs", "maqola") else HAIKU_MODEL

    prompt = (
        f"Mavzu: {topic}\n"
        f"Hajm: {pages} bet ({pages * wpg}+ so'z)\n"
        f"{info}{subject}\n\n"
        f"{ln} tilida TO'LIQ {names.get(svc, 'hujjat')} yozing:\n\n"
        f"{struct}\n\n"
        f"QATIY TALABLAR:\n"
        f"1. Faqat ilmiy kitoblar va tasdiqlangan manbalardan\n"
        f"2. Har bo'limda aniq faktlar, raqamlar, foizlar\n"
        f"3. Hech qanday **, *, #, ` belgisi ishlatilmasin\n"
        f"4. Imlo va grammatika 100% to'g'ri\n"
        f"5. Har bo'lim to'liq, qisqartirma yo'q\n"
        f"6. Oxirida foydalanilgan adabiyotlar ro'yxati"
    )
    system = (
        f"Sen O'zbekistonning eng professional {ln} akademik yozuvchisisan. "
        f"Faqat ilmiy manbalardan foydalanasan. "
        f"Markdown belgisi ASLO ishlatmaysan. "
        f"Imlo va grammatika xatosiz yozasan."
    )
    result = claude(prompt, system, 4000, model=use_model)
    return clean_text(result)

def gen_test(topic, count, lang):
    """Test savollari yaratish"""
    ln = LN.get(lang, "o'zbek")
    prompt = (
        f"Mavzu: {topic}\nSavollar soni: {count}\nTil: {ln}\n\n"
        f"{count} ta professional test savoli yarating.\n\n"
        f"FORMAT (qat'iy shu formatda):\n"
        f"1. [Savol matni]\n"
        f"A) [javob]\nB) [javob]\nC) [javob]\nD) [javob]\n"
        f"To'g'ri javob: A\n\n"
        f"2. [Savol matni]\n"
        f"...\n\n"
        f"TALABLAR:\n"
        f"1. Hech qanday **, *, # belgisi yo'q\n"
        f"2. Imlo xatosiz\n"
        f"3. Savollar turli murakkablik darajasida\n"
        f"4. To'g'ri javob aniq ko'rsatilsin"
    )
    system = f"Sen professional {ln} test yaratuvchisisan. Markdown ishlatmaysan. Imlo xatosiz."
    result = claude(prompt, system, min(count * 100, 4000))
    return clean_text(result)

def fix_spell(text, lang):
    """Imlo tuzatish"""
    ln = LN.get(lang, "o'zbek")
    result = claude(
        f"{ln} tilida imlo tuzat. Faqat tuzatilgan matnni qaytар:\n\n{text[:3000]}",
        f"Sen {ln} imlo mutaxassisisanm. Faqat tuzatilgan matn.",
        3500
    )
    return clean_text(result)

# ============================================================
# RASM OLISH
# ============================================================
def get_image(query):
    """Internetdan mavzuga mos rasm olish"""
    try:
        import hashlib, time
        search_q = requests.utils.quote(query[:60])
        if UNSPLASH_KEY:
            headers = {"Authorization": f"Client-ID {UNSPLASH_KEY}"}
            r = requests.get(
                f"https://api.unsplash.com/photos/random?query={search_q}&orientation=landscape",
                headers=headers, timeout=15)
            if r.status_code == 200:
                img_url = r.json().get("urls", {}).get("regular", "")
                if img_url:
                    ir = requests.get(img_url, timeout=15)
                    if ir.status_code == 200 and len(ir.content) > 5000:
                        buf = BytesIO(ir.content); buf.seek(0)
                        return buf
        seed = int(hashlib.md5((query + str(time.time())).encode()).hexdigest()[:8], 16) % 9999
        r2 = requests.get(
            f"https://source.unsplash.com/800x500/?{search_q}&sig={seed}",
            timeout=15, allow_redirects=True)
        if r2.status_code == 200 and len(r2.content) > 5000:
            buf2 = BytesIO(r2.content); buf2.seek(0); return buf2
    except Exception as e:
        logger.warning(f"Rasm olishda xato: {e}")
    return None

# ============================================================
# 42 SHABLON
# ============================================================
TEMPLATES = {
    "1": {"name": "🔵 Klassik Ko'k", "bg1": (30,87,179), "bg2": (0,150,255), "title": (255,255,255), "text": (220,235,255), "accent": (255,200,0)},
    "2": {"name": "🌊 Okean", "bg1": (0,119,182), "bg2": (0,180,216), "title": (255,255,255), "text": (200,240,255), "accent": (144,224,239)},
    "3": {"name": "🌿 Yashil", "bg1": (27,94,32), "bg2": (56,142,60), "title": (255,255,255), "text": (200,255,200), "accent": (255,235,59)},
    "4": {"name": "🌅 Quyosh", "bg1": (230,81,0), "bg2": (255,152,0), "title": (255,255,255), "text": (255,240,200), "accent": (255,255,100)},
    "5": {"name": "🌸 Pushti", "bg1": (136,14,79), "bg2": (233,30,99), "title": (255,255,255), "text": (255,210,230), "accent": (255,255,255)},
    "6": {"name": "🌙 Qora", "bg1": (10,10,10), "bg2": (30,30,30), "title": (255,255,255), "text": (200,200,200), "accent": (0,200,255)},
    "7": {"name": "⭐ Oltin", "bg1": (84,62,0), "bg2": (184,138,0), "title": (255,255,255), "text": (255,245,200), "accent": (255,215,0)},
    "8": {"name": "🔴 Qizil", "bg1": (183,28,28), "bg2": (229,57,53), "title": (255,255,255), "text": (255,210,210), "accent": (255,255,255)},
    "9": {"name": "💜 Binafsha", "bg1": (69,39,160), "bg2": (126,87,194), "title": (255,255,255), "text": (230,210,255), "accent": (255,200,100)},
    "10": {"name": "🤍 Oq", "bg1": (245,245,245), "bg2": (255,255,255), "title": (30,30,30), "text": (60,60,60), "accent": (30,87,179)},
    "11": {"name": "🏢 Korporativ", "bg1": (21,38,57), "bg2": (37,57,93), "title": (255,255,255), "text": (180,200,220), "accent": (0,180,255)},
    "12": {"name": "🎨 Kreativ", "bg1": (74,0,114), "bg2": (255,0,100), "title": (255,255,255), "text": (255,200,240), "accent": (255,255,0)},
    "13": {"name": "🌍 Tabiat", "bg1": (27,67,50), "bg2": (40,120,80), "title": (255,255,255), "text": (200,240,210), "accent": (255,235,59)},
    "14": {"name": "❄️ Muzli", "bg1": (1,87,155), "bg2": (3,169,244), "title": (255,255,255), "text": (200,240,255), "accent": (255,255,255)},
    "15": {"name": "🔥 Olov", "bg1": (100,0,0), "bg2": (200,50,0), "title": (255,255,255), "text": (255,220,200), "accent": (255,180,0)},
    "16": {"name": "🌆 Shahar", "bg1": (38,50,56), "bg2": (84,110,122), "title": (255,255,255), "text": (200,215,220), "accent": (0,229,255)},
    "17": {"name": "🎓 Akademik", "bg1": (62,39,35), "bg2": (109,76,65), "title": (255,255,255), "text": (255,235,220), "accent": (255,200,100)},
    "18": {"name": "💼 Biznes", "bg1": (13,71,161), "bg2": (25,118,210), "title": (255,255,255), "text": (210,228,255), "accent": (255,215,0)},
    "19": {"name": "🎭 Teatr", "bg1": (49,27,146), "bg2": (94,53,177), "title": (255,255,255), "text": (225,210,255), "accent": (255,235,59)},
    "20": {"name": "🏔 Tog'", "bg1": (84,110,122), "bg2": (120,144,156), "title": (255,255,255), "text": (220,230,235), "accent": (255,235,59)},
    "21": {"name": "🌺 Gul", "bg1": (136,14,79), "bg2": (216,67,21), "title": (255,255,255), "text": (255,215,220), "accent": (255,255,200)},
    "22": {"name": "🔮 Sehrli", "bg1": (49,27,146), "bg2": (0,131,143), "title": (255,255,255), "text": (210,240,255), "accent": (255,200,255)},
    "23": {"name": "☀️ Issiq", "bg1": (230,100,0), "bg2": (255,180,0), "title": (255,255,255), "text": (255,240,200), "accent": (255,255,255)},
    "24": {"name": "🌊 Dengiz", "bg1": (0,60,100), "bg2": (0,120,180), "title": (255,255,255), "text": (200,235,255), "accent": (0,229,255)},
    "25": {"name": "🦋 Kapalak", "bg1": (74,20,140), "bg2": (170,0,255), "title": (255,255,255), "text": (235,200,255), "accent": (255,255,100)},
    "26": {"name": "🍃 Yashil2", "bg1": (27,94,32), "bg2": (100,180,50), "title": (255,255,255), "text": (210,245,210), "accent": (255,255,100)},
    "27": {"name": "🌙 Kecha", "bg1": (5,5,30), "bg2": (20,20,60), "title": (180,180,255), "text": (150,150,200), "accent": (255,200,0)},
    "28": {"name": "🌈 Kamalak", "bg1": (100,0,150), "bg2": (0,100,200), "title": (255,255,255), "text": (240,240,255), "accent": (255,255,0)},
    "29": {"name": "🏜 Cho'l", "bg1": (100,70,20), "bg2": (180,130,50), "title": (255,255,255), "text": (255,240,200), "accent": (255,200,100)},
    "30": {"name": "🎪 Sirk", "bg1": (183,28,28), "bg2": (255,160,0), "title": (255,255,255), "text": (255,240,200), "accent": (255,255,255)},
    "31": {"name": "💎 Brilliant", "bg1": (0,40,80), "bg2": (0,100,180), "title": (200,230,255), "text": (180,220,255), "accent": (255,215,0)},
    "32": {"name": "🌻 Kungaboqar", "bg1": (200,130,0), "bg2": (255,200,0), "title": (60,40,0), "text": (80,60,10), "accent": (180,100,0)},
    "33": {"name": "🦚 Tovus", "bg1": (0,77,64), "bg2": (0,150,136), "title": (255,255,255), "text": (200,240,235), "accent": (255,235,59)},
    "34": {"name": "🌃 Kecha2", "bg1": (10,10,40), "bg2": (40,40,80), "title": (100,200,255), "text": (150,180,220), "accent": (255,180,0)},
    "35": {"name": "🍒 Gilos", "bg1": (120,0,30), "bg2": (200,30,60), "title": (255,255,255), "text": (255,200,210), "accent": (255,240,200)},
    "36": {"name": "🧊 Muz", "bg1": (200,230,255), "bg2": (240,250,255), "title": (0,60,120), "text": (20,80,140), "accent": (0,120,215)},
    "37": {"name": "🌴 Tropik", "bg1": (0,100,60), "bg2": (0,180,100), "title": (255,255,255), "text": (200,255,220), "accent": (255,220,0)},
    "38": {"name": "🎵 Musiqa", "bg1": (20,0,40), "bg2": (80,0,120), "title": (255,150,255), "text": (200,150,220), "accent": (255,200,255)},
    "39": {"name": "🏛 Antik", "bg1": (245,235,220), "bg2": (255,248,235), "title": (80,50,20), "text": (100,70,40), "accent": (150,100,30)},
    "40": {"name": "⚡ Energiya", "bg1": (0,20,60), "bg2": (0,60,120), "title": (0,200,255), "text": (150,210,255), "accent": (255,230,0)},
    "41": {"name": "🦁 Sher", "bg1": (100,60,0), "bg2": (200,120,0), "title": (255,255,255), "text": (255,235,200), "accent": (255,200,100)},
    "42": {"name": "🌊 To'lqin", "bg1": (0,50,100), "bg2": (0,130,200), "title": (255,255,255), "text": (200,230,255), "accent": (100,255,255)},
}

# ============================================================
# PPTX YARATISH
# ============================================================
def make_pptx(content, topic, tmpl_id, ud={}, user_imgs=None, img_pages=None):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN

    tmpl = TEMPLATES.get(str(tmpl_id), TEMPLATES["1"])
    bg1 = RGBColor(*tmpl["bg1"]); bg2 = RGBColor(*tmpl["bg2"])
    tc = RGBColor(*tmpl["title"]); txc = RGBColor(*tmpl["text"]); acc = RGBColor(*tmpl["accent"])

    prs = Presentation()
    prs.slide_width = Inches(13.33)
    prs.slide_height = Inches(7.5)
    blank = prs.slide_layouts[6]

    # Slaydlarni ajratish
    clean = content.replace("**","").replace("##","").replace("#","")
    slides = []; cur_t = topic; cur_b = []
    for line in clean.strip().split("\n"):
        line = line.strip()
        if not line: continue
        ul = line.upper()
        is_slide = (ul.startswith("SLAYD") or ul.startswith("SLIDE") or ul.startswith("СЛАЙД")) and ":" in line
        if is_slide:
            if cur_t is not None:
                slides.append((cur_t, cur_b[:]))
            cur_t = line.split(":", 1)[1].strip()
            cur_b = []
        else:
            b = re.sub(r'^[-•►▸*\s]+', '', line)
            if b: cur_b.append(b)
    if cur_t: slides.append((cur_t, cur_b))
    # Agar SLAYD formati topilmasa, \n\n boyicha ajratamiz
    if not slides or len(slides) < 2:
        parts = [p.strip() for p in clean.split("\n\n") if p.strip()]
        slides = []
        for p in parts:
            plines = [l.strip() for l in p.split("\n") if l.strip()]
            if plines:
                t = re.sub(r"^(SLAYD|SLIDE)\s*\d+[:\.]?\s*", "", plines[0], flags=re.IGNORECASE).strip() or plines[0]
                b = [re.sub(r"^[-•►▸*\d\.\s]+", "", x) for x in plines[1:] if x]
                slides.append((t[:80], b))
    if not slides:
        slides = [(topic, [clean[:200]])]
    for sn, (title, bullets) in enumerate(slides):
        sl = prs.slides.add_slide(blank)

        # Gradient fon
        bg = sl.background; fill = bg.fill
        fill.gradient(); fill.gradient_angle = 2700000
        fill.gradient_stops[0].position = 0; fill.gradient_stops[0].color.rgb = bg1
        fill.gradient_stops[1].position = 1.0; fill.gradient_stops[1].color.rgb = bg2

        # Dekorativ doiralar
        for cx, cy, sz in [(11.5,-0.8,3.5), (-0.8,5.5,2.5), (12.0,6.0,2.0)]:
            try:
                sh = sl.shapes.add_shape(9, Inches(cx), Inches(cy), Inches(sz), Inches(sz))
                sh.fill.solid(); sh.fill.fore_color.rgb = RGBColor(255,255,255)
                sh.fill.fore_color.transparency = 0.88; sh.line.fill.background()
            except: pass

        # Yuqori chiziq
        try:
            bar = sl.shapes.add_shape(1, Inches(0), Inches(0), Inches(13.33), Inches(0.1))
            bar.fill.solid(); bar.fill.fore_color.rgb = acc; bar.line.fill.background()
        except: pass

        if sn == 0:
            # 1-SLAYD: Mavzu va muallif ma'lumotlari
            tb = sl.shapes.add_textbox(Inches(1), Inches(1.0), Inches(11.33), Inches(2.8))
            tf = tb.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.text = topic
            p.font.size = Pt(36); p.font.bold = True
            p.font.color.rgb = tc; p.alignment = PP_ALIGN.CENTER

            # Ajratuvchi chiziq
            try:
                sep = sl.shapes.add_shape(1, Inches(3), Inches(3.9), Inches(7.33), Inches(0.06))
                sep.fill.solid(); sep.fill.fore_color.rgb = acc; sep.line.fill.background()
            except: pass

            # Muallif ma'lumotlari
            info_lines = []
            if ud.get("full_name"): info_lines.append(f"Muallif: {ud['full_name']}")
            if ud.get("subject"): info_lines.append(f"Fan: {ud['subject']}")
            if ud.get("university"): info_lines.append(f"Universitet: {ud['university']}")
            if ud.get("faculty"): info_lines.append(f"Fakultet: {ud['faculty']}")
            if ud.get("year"): info_lines.append(f"Kurs: {ud['year']}")
            if ud.get("teacher"): info_lines.append(f"O'qituvchi: {ud['teacher']}")
            if ud.get("city"): info_lines.append(f"Shahar: {ud['city']}")
            info_lines.append(datetime.now().strftime("%Y-yil"))

            if info_lines:
                tb2 = sl.shapes.add_textbox(Inches(1), Inches(4.1), Inches(11.33), Inches(2.8))
                tf2 = tb2.text_frame; tf2.word_wrap = True; first2 = True
                for ln_txt in info_lines:
                    p2 = tf2.paragraphs[0] if first2 else tf2.add_paragraph(); first2 = False
                    p2.text = ln_txt; p2.font.size = Pt(17); p2.font.color.rgb = txc
                    p2.alignment = PP_ALIGN.CENTER; p2.space_before = Pt(3)

        elif sn == 1 and any(w in title.upper() for w in ["REJA", "PLAN", "MUNDARIJA", "CONTENT"]):
            # 2-SLAYD: REJALAR
            tb = sl.shapes.add_textbox(Inches(0.5), Inches(0.2), Inches(12.33), Inches(1.1))
            tf = tb.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.text = "📋  REJALAR"
            p.font.size = Pt(34); p.font.bold = True; p.font.color.rgb = tc
            p.alignment = PP_ALIGN.CENTER
            try:
                ln2 = sl.shapes.add_shape(1, Inches(2), Inches(1.4), Inches(9.33), Inches(0.07))
                ln2.fill.solid(); ln2.fill.fore_color.rgb = acc; ln2.line.fill.background()
            except: pass
            if bullets:
                tb2 = sl.shapes.add_textbox(Inches(1.5), Inches(1.6), Inches(10.33), Inches(5.6))
                tf2 = tb2.text_frame; tf2.word_wrap = True; first = True
                for bi, b in enumerate(bullets[:12]):
                    if not b.strip(): continue
                    p2 = tf2.paragraphs[0] if first else tf2.add_paragraph(); first = False
                    p2.text = f"  {bi+1}.  {b.strip()}"
                    p2.font.size = Pt(20); p2.font.color.rgb = txc; p2.space_before = Pt(8)
                    p2.alignment = PP_ALIGN.LEFT

        else:
            # Oddiy slayd
            tb = sl.shapes.add_textbox(Inches(0.4), Inches(0.2), Inches(12.53), Inches(1.2))
            tf = tb.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]; p.text = title[:80]
            p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = tc

            try:
                ln2 = sl.shapes.add_shape(1, Inches(0.4), Inches(1.52), Inches(12.53), Inches(0.07))
                ln2.fill.solid(); ln2.fill.fore_color.rgb = acc; ln2.line.fill.background()
            except: pass

            if bullets:
                has_img = (img_pages and any(img_pages.get(str(i)) == sn+1
                           for i in range(len(user_imgs or [])))) or \
                          (sn+1 in ud.get("ai_img_slides", []))
                txt_w = 7.8 if has_img else 12.5

                # Infografika va oddiy matn ajratish
                normal_b = []; infog = []
                for b in bullets:
                    if b.strip().upper().startswith("INFOGRAFIKA:"):
                        infog.append(b.strip())
                    elif b.strip():
                        normal_b.append(b.strip())

                tb2 = sl.shapes.add_textbox(Inches(0.4), Inches(1.75), Inches(txt_w), Inches(3.8))
                tf2 = tb2.text_frame; tf2.word_wrap = True; first = True
                for b in normal_b[:8]:
                    p2 = tf2.paragraphs[0] if first else tf2.add_paragraph(); first = False
                    p2.text = f"▸  {b}"; p2.font.size = Pt(17); p2.font.color.rgb = txc
                    p2.space_before = Pt(4)

                # Infografika bar chart
                if infog:
                    try:
                        import re as _re2
                        for inf in infog[:1]:
                            parts = inf.split(":", 2)
                            inf_title = parts[1].strip() if len(parts) > 1 else ""
                            data_str = parts[2] if len(parts) > 2 else ""
                            entries = []
                            for item in data_str.split(","):
                                item = item.strip()
                                if ":" in item:
                                    k, v = item.split(":", 1)
                                    num = _re2.sub(r'[^\d.]', '', v.strip())
                                    try: entries.append((k.strip(), float(num), v.strip()))
                                    except: pass
                            if entries:
                                max_val = max(e[1] for e in entries) or 1
                                inf_y = 5.7
                                itb = sl.shapes.add_textbox(Inches(0.4), Inches(inf_y-0.35), Inches(12.0), Inches(0.3))
                                ip = itb.text_frame.paragraphs[0]
                                ip.text = f"📊 {inf_title}"; ip.font.size = Pt(12); ip.font.bold = True
                                ip.font.color.rgb = acc
                                for ei, (lbl, val, orig) in enumerate(entries[:5]):
                                    by = inf_y + ei * 0.35
                                    bw = min(7.5 * (val / max_val), 7.5)
                                    ltb = sl.shapes.add_textbox(Inches(0.4), Inches(by), Inches(2.4), Inches(0.28))
                                    ltb.text_frame.paragraphs[0].text = lbl[:18]
                                    ltb.text_frame.paragraphs[0].font.size = Pt(10)
                                    ltb.text_frame.paragraphs[0].font.color.rgb = txc
                                    bar = sl.shapes.add_shape(1, Inches(3.0), Inches(by+0.03), Inches(max(bw,0.2)), Inches(0.22))
                                    bar.fill.solid(); bar.fill.fore_color.rgb = acc; bar.line.fill.background()
                                    vtb = sl.shapes.add_textbox(Inches(3.0+bw+0.1), Inches(by), Inches(1.5), Inches(0.28))
                                    vtb.text_frame.paragraphs[0].text = orig
                                    vtb.text_frame.paragraphs[0].font.size = Pt(10)
                                    vtb.text_frame.paragraphs[0].font.bold = True
                                    vtb.text_frame.paragraphs[0].font.color.rgb = acc
                    except Exception as ie:
                        logger.error(f"Infografika: {ie}")

            # Sahifa raqami
            try:
                rq = sl.shapes.add_textbox(Inches(12.5), Inches(7.1), Inches(0.8), Inches(0.35))
                rq.text_frame.paragraphs[0].text = str(sn+1)
                rq.text_frame.paragraphs[0].font.size = Pt(11)
                rq.text_frame.paragraphs[0].font.color.rgb = acc
            except: pass

        # Foydalanuvchi rasmlari
        if user_imgs and img_pages:
            for ii, pn in img_pages.items():
                try:
                    ii_int = int(ii) if isinstance(ii, str) else ii
                    if ii_int < len(user_imgs) and pn == sn+1:
                        sl.shapes.add_picture(user_imgs[ii_int], Inches(8.8), Inches(1.6), Inches(4.2), Inches(5.4))
                except Exception as e: logger.error(f"User img: {e}")

    # AI rasmlar
    ai_slides = ud.get("ai_img_slides", [])
    if ai_slides:
        slide_list = list(prs.slides)
        for slide_num in ai_slides:
            try:
                if slide_num-1 < len(slide_list):
                    sl2 = slide_list[slide_num-1]
                    slide_title = topic
                    for sh in sl2.shapes:
                        if sh.has_text_frame and sh.text_frame.paragraphs:
                            txt = sh.text_frame.paragraphs[0].text.strip()
                            if txt and len(txt) > 3 and txt != topic:
                                slide_title = txt; break
                    img_buf = get_image(f"{slide_title} {topic}"[:60])
                    if img_buf:
                        if slide_num % 2 == 0:
                            sl2.shapes.add_picture(img_buf, Inches(0.4), Inches(1.7), Inches(12.5), Inches(3.2))
                        else:
                            sl2.shapes.add_picture(img_buf, Inches(8.6), Inches(1.7), Inches(4.5), Inches(3.5))
            except Exception as ie:
                logger.error(f"AI rasm {slide_num}: {ie}")

    td = tempfile.mkdtemp()
    out = os.path.join(td, "prezentatsiya.pptx")
    prs.save(out); return out, td

# ============================================================
# HTML PREZENTATSIYA
# ============================================================
def make_html(content, topic, tmpl_id, ud={}):
    tmpl = TEMPLATES.get(str(tmpl_id), TEMPLATES["1"])
    bg1 = "#{:02x}{:02x}{:02x}".format(*tmpl["bg1"])
    bg2 = "#{:02x}{:02x}{:02x}".format(*tmpl["bg2"])
    th = "#{:02x}{:02x}{:02x}".format(*tmpl["title"])
    tx = "#{:02x}{:02x}{:02x}".format(*tmpl["text"])
    ac = "#{:02x}{:02x}{:02x}".format(*tmpl["accent"])

    clean = content.replace("**","").replace("##","").replace("#","")
    slides = []; cur_t = topic; cur_b = []
    for line in clean.strip().split("\n"):
        line = line.strip()
        if not line: continue
        ul = line.upper()
        is_slide = (ul.startswith("SLAYD") or ul.startswith("SLIDE")) and ":" in line
        if is_slide:
            if cur_t is not None: slides.append((cur_t, cur_b[:]))
            cur_t = line.split(":", 1)[1].strip(); cur_b = []
        else:
            b = re.sub(r'^[-•►▸*\s]+', '', line)
            if b: cur_b.append(b)
    if cur_t: slides.append((cur_t, cur_b))
    total = len(slides)
    info = build_info(ud)

    slides_html = ""
    for i, (ti, b) in enumerate(slides):
        bl = "".join(f"<li>{x}</li>" for x in b[:10] if x.strip())
        disp = "block" if i == 0 else "none"
        if i == 0:
            slides_html += f"""<div class="slide" id="s{i}" style="display:{disp}">
<div class="snum">{i+1}/{total}</div>
<div class="title-slide"><h1>{ti}</h1>
<div class="info">{info.replace(chr(10),"<br>")}</div>
<p class="yr">{datetime.now().strftime("%Y-yil")}</p></div></div>"""
        else:
            slides_html += f"""<div class="slide" id="s{i}" style="display:{disp}">
<div class="snum">{i+1}/{total}</div>
<h2>{ti}</h2><div class="aline"></div>
<ul>{bl}</ul></div>"""

    html = f"""<!DOCTYPE html><html lang="uz"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{topic}</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}
body{{font-family:'Segoe UI',Arial,sans-serif;background:#0a0a0a;display:flex;justify-content:center;align-items:center;min-height:100vh;flex-direction:column;gap:20px;padding:20px}}
.slide{{background:linear-gradient(135deg,{bg1},{bg2});width:900px;max-width:98vw;aspect-ratio:16/9;border-radius:14px;padding:45px 55px;position:relative;overflow:hidden;box-shadow:0 25px 70px rgba(0,0,0,.6)}}
.slide::before{{content:'';position:absolute;right:-70px;top:-70px;width:280px;height:280px;border-radius:50%;background:rgba(255,255,255,.06)}}
.slide::after{{content:'';position:absolute;left:-50px;bottom:-50px;width:200px;height:200px;border-radius:50%;background:rgba(255,255,255,.04)}}
.snum{{position:absolute;bottom:18px;right:25px;color:{ac};font-size:14px;font-weight:600}}
.title-slide{{display:flex;flex-direction:column;justify-content:center;align-items:center;height:100%;text-align:center}}
.title-slide h1{{color:{th};font-size:40px;font-weight:800;line-height:1.25;margin-bottom:20px;text-shadow:0 2px 10px rgba(0,0,0,.3)}}
.info{{color:{tx};font-size:17px;line-height:2;opacity:.92;margin-bottom:12px}}
.yr{{color:{ac};font-size:16px;font-weight:700}}
h2{{color:{th};font-size:26px;font-weight:700;margin-bottom:6px}}
.aline{{width:60px;height:4px;background:{ac};border-radius:2px;margin:10px 0 20px}}
ul{{list-style:none;color:{tx}}}
li{{font-size:18px;line-height:1.7;margin-bottom:10px;padding-left:24px;position:relative}}
li::before{{content:'▸';position:absolute;left:0;color:{ac};font-weight:bold}}
.ctrl{{display:flex;gap:12px;align-items:center;margin-top:5px}}
.btn{{background:rgba(255,255,255,.12);color:white;border:2px solid {ac};padding:10px 30px;border-radius:30px;cursor:pointer;font-size:15px;font-weight:600;transition:all .3s;backdrop-filter:blur(10px)}}
.btn:hover{{background:{ac};color:#000;transform:scale(1.05)}}
.prog{{color:rgba(255,255,255,.6);font-size:14px;min-width:60px;text-align:center}}
</style></head><body>
{slides_html}
<div class="ctrl">
<button class="btn" onclick="nav(-1)">◀ Oldingi</button>
<span class="prog" id="pg">1/{total}</span>
<button class="btn" onclick="nav(1)">Keyingi ▶</button>
</div>
<script>
var cur=0,tot={total};
function nav(d){{
var ns=cur+d;
if(ns<0||ns>=tot)return;
document.getElementById('s'+cur).style.display='none';
cur=ns;
document.getElementById('s'+cur).style.display='block';
document.getElementById('pg').textContent=(cur+1)+'/'+tot;
}}
document.addEventListener('keydown',function(e){{
if(e.key==='ArrowRight'||e.key===' ')nav(1);
if(e.key==='ArrowLeft')nav(-1);
}});
</script></body></html>"""

    td = tempfile.mkdtemp()
    out = os.path.join(td, "prezentatsiya.html")
    with open(out, "w", encoding="utf-8") as f: f.write(html)
    return out, td

# ============================================================
# DOCX YARATISH
# ============================================================
def make_docx(content, topic, ud={}):
    try:
        from docx import Document
        from docx.shared import Pt as DPt, Inches as DInches, RGBColor as DRGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = DPt(14)

        # Sarlavha sahifasi
        if ud.get("university"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            run = p.add_run(ud["university"].upper())
            run.bold = True; run.font.size = DPt(14)

        doc.add_paragraph()
        title_p = doc.add_heading(topic, 0)
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()
        if ud.get("full_name"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p.add_run(f"Tayyorladi: {ud['full_name']}")
        if ud.get("teacher"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
            p.add_run(f"O'qituvchi: {ud['teacher']}")
        if ud.get("city"):
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.add_run(f"{ud.get('city','')} — {datetime.now().year}")

        doc.add_page_break()

        # Kontent
        for line in content.split("\n"):
            line = line.strip()
            if not line: continue
            if any(line.startswith(h) for h in ["KIRISH","XULOSA","I BOB","II BOB","III BOB",
                   "MUNDARIJA","ANNOTATSIYA","ABSTRACT","METODOLOGIYA","NATIJALAR",
                   "ADABIYOTLAR","FOYDALANILGAN"]):
                h = doc.add_heading(line, 1)
                h.alignment = WD_ALIGN_PARAGRAPH.CENTER
            else:
                p = doc.add_paragraph(line)
                p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
                for run in p.runs:
                    run.font.size = DPt(14)

        td = tempfile.mkdtemp()
        out = os.path.join(td, "dokument.docx")
        doc.save(out); return out, td
    except Exception as e:
        logger.error(f"DOCX xato: {e}"); return None, None

# ============================================================
# PDF YARATISH
# ============================================================
def make_pdf(content, topic, ud={}):
    try:
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        import os as _os

        font_paths = [
            "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
            "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        ]
        font_name = "Helvetica"
        for fp in font_paths:
            if _os.path.exists(fp):
                try:
                    pdfmetrics.registerFont(TTFont("CustomFont", fp))
                    font_name = "CustomFont"; break
                except: pass

        td = tempfile.mkdtemp()
        out = os.path.join(td, "dokument.pdf")
        doc = SimpleDocTemplate(out, pagesize=A4,
                                rightMargin=2*cm, leftMargin=2*cm,
                                topMargin=2*cm, bottomMargin=2*cm)
        styles = getSampleStyleSheet()
        story = []

        # Sarlavha
        title_style = ParagraphStyle("title", fontName=font_name, fontSize=16,
                                     spaceAfter=20, alignment=1, leading=20)
        story.append(Paragraph(topic, title_style))
        story.append(Spacer(1, 20))

        # Muallif
        info_style = ParagraphStyle("info", fontName=font_name, fontSize=12,
                                    spaceAfter=6, alignment=1)
        info = build_info(ud)
        for line in info.split("\n"):
            if line.strip():
                story.append(Paragraph(line, info_style))
        story.append(Spacer(1, 30))

        # Kontent
        head_style = ParagraphStyle("head", fontName=font_name, fontSize=14,
                                    spaceAfter=10, spaceBefore=15, fontWeight=700, leading=18)
        body_style = ParagraphStyle("body", fontName=font_name, fontSize=12,
                                    spaceAfter=8, leading=18, alignment=4)

        for line in content.split("\n"):
            line = line.strip()
            if not line: story.append(Spacer(1, 6)); continue
            if any(line.startswith(h) for h in ["KIRISH","XULOSA","I BOB","II BOB","III BOB",
                   "MUNDARIJA","ANNOTATSIYA","METODOLOGIYA","NATIJALAR","ADABIYOTLAR","FOYDALANILGAN"]):
                story.append(Paragraph(line, head_style))
            else:
                story.append(Paragraph(line.replace("<","&lt;").replace(">","&gt;"), body_style))

        doc.build(story)
        return out, td
    except Exception as e:
        logger.error(f"PDF xato: {e}"); return None, None

# ============================================================
# KONVERTATSIYA
# ============================================================
def pdf_to_text(pdf_path):
    try:
        import fitz
        d = fitz.open(pdf_path)
        return " ".join(pg.get_text() for pg in d)
    except: return ""

def imgs_to_pdf(imgs, out_path):
    try:
        from PIL import Image
        images = []
        for p in imgs:
            img = Image.open(p).convert("RGB")
            images.append(img)
        if images:
            images[0].save(out_path, save_all=True, append_images=images[1:])
            return True
    except Exception as e:
        logger.error(f"imgs_to_pdf: {e}")
    return False

# ============================================================
# TUGMALAR
# ============================================================
def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(t(uid,"btn_referat"), t(uid,"btn_kurs"))
    kb.row(t(uid,"btn_mustaqil"), t(uid,"btn_maqola"))
    kb.row(t(uid,"btn_prez"), t(uid,"btn_test"))
    kb.row(t(uid,"btn_imlo"), t(uid,"btn_konv"))
    kb.row(t(uid,"btn_balans"), t(uid,"btn_orders"))
    kb.row(t(uid,"btn_donat"), t(uid,"btn_help"))
    kb.add(t(uid,"btn_admin"))
    return kb

def lang_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang:uz"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")
    )
    return kb

def bk_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("◀️ Orqaga", callback_data="back_step"),
        types.InlineKeyboardButton("🏠 Menyu", callback_data="bk")
    )
    return kb

def skip_kb(ns):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("⏭ O'tkazib yuborish", callback_data=f"skip:{ns}"),
        types.InlineKeyboardButton("🏠 Menyu", callback_data="bk")
    )
    return kb

def fmt_kb(prefix):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("📝 DOCX", callback_data=f"{prefix}:docx"),
        types.InlineKeyboardButton("📄 PDF", callback_data=f"{prefix}:pdf"),
        types.InlineKeyboardButton("📱 TXT", callback_data=f"{prefix}:txt")
    )
    return kb

def prez_fmt_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("📊 PPTX (PowerPoint)", callback_data="pfmt:pptx"),
        types.InlineKeyboardButton("🌐 HTML (Interaktiv)", callback_data="pfmt:html"),
        types.InlineKeyboardButton("📦 Ikkalasi ham", callback_data="pfmt:both")
    )
    return kb

def slides_kb():
    kb = types.InlineKeyboardMarkup(row_width=4)
    for n in [10,15,20,25,30,35,40,50]:
        kb.add(types.InlineKeyboardButton(f"{n} slayd — {n*PRICE_SLIDE:,} so'm", callback_data=f"slides:{n}"))
    kb.add(types.InlineKeyboardButton("✏️ O'zim yozaman", callback_data="slides:custom"))
    kb.add(types.InlineKeyboardButton("🏠 Menyu", callback_data="bk"))
    return kb

def test_kb():
    kb = types.InlineKeyboardMarkup(row_width=4)
    for n in [10,20,30,50,100,200,500,1000]:
        kb.add(types.InlineKeyboardButton(f"{n} ta — {n*PRICE_TEST:,} so'm", callback_data=f"tcount:{n}"))
    kb.add(types.InlineKeyboardButton("✏️ O'zim yozaman", callback_data="tcount:custom"))
    kb.add(types.InlineKeyboardButton("🏠 Menyu", callback_data="bk"))
    return kb

def plans_kb():
    kb = types.InlineKeyboardMarkup(row_width=4)
    for n in [3,4,5,6,7,8,10,12]:
        kb.add(types.InlineKeyboardButton(f"{n} ta bo'lim", callback_data=f"plans:{n}"))
    kb.add(types.InlineKeyboardButton("✏️ O'zim yozaman", callback_data="plans:custom"))
    kb.add(types.InlineKeyboardButton("🏠 Menyu", callback_data="bk"))
    return kb

def lc_kb(prefix):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("🇺🇿 O'zbek", callback_data=f"{prefix}:uz"),
        types.InlineKeyboardButton("🇷🇺 Rus", callback_data=f"{prefix}:ru"),
        types.InlineKeyboardButton("🇬🇧 Ingliz", callback_data=f"{prefix}:en")
    )
    return kb

def tmpl_kb(page=0):
    kb = types.InlineKeyboardMarkup(row_width=2)
    keys = list(TEMPLATES.keys())
    per = 10; start = page * per; end = min(start + per, len(keys))
    for k in keys[start:end]:
        kb.add(types.InlineKeyboardButton(TEMPLATES[k]["name"], callback_data=f"tmpl:{k}"))
    nav_btns = []
    if page > 0: nav_btns.append(types.InlineKeyboardButton("◀️", callback_data=f"tmpl_p:{page-1}"))
    if end < len(keys): nav_btns.append(types.InlineKeyboardButton("▶️", callback_data=f"tmpl_p:{page+1}"))
    if nav_btns: kb.row(*nav_btns)
    return kb

def img_choice_kb():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🤖 AI avtomatik rasm qo'ysin", callback_data="img:ai"),
        types.InlineKeyboardButton("🖼 O'zim rasm yuklаyman", callback_data="img:user"),
        types.InlineKeyboardButton("❌ Rasmsiz davom etish", callback_data="img:none")
    )
    return kb

def conv_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📄➡️📊 PDF → PPTX", callback_data="cv:pdf"))
    kb.add(types.InlineKeyboardButton("📊➡️📄 PPTX → PDF", callback_data="cv:pptx"))
    kb.add(types.InlineKeyboardButton("🖼➡️📄 Rasmlar → PDF", callback_data="cv:img"))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="bk"))
    return kb

# ============================================================
# INFO STEPS
# ============================================================
INFO_STEPS = [
    ("ask_name",    "full_name",   True),
    ("ask_univ",    "university",  True),
    ("ask_faculty", "faculty",     False),
    ("ask_year",    "year",        False),
    ("ask_teacher", "teacher",     False),
    ("ask_subject", "subject",     False),
    ("ask_city",    "city",        False),
]
INFO_STATES = [s[0] for s in INFO_STEPS]

def finish_info(uid, ud):
    svc = ud.get("svc", "referat")
    if svc == "prez":
        sst(uid, "prez_tmpl")
        bot.send_message(uid, t(uid, "ask_template"), reply_markup=tmpl_kb())
    else:
        sst(uid, f"{svc}_lang")
        bot.send_message(uid, t(uid, "ask_lang"), reply_markup=lc_kb(f"{svc}_lang"))

# ============================================================
# BUYRUQLAR
# ============================================================
@bot.message_handler(commands=["start"])
def cmd_start(msg):
    uid = msg.from_user.id
    uname = msg.from_user.username or ""
    fname = msg.from_user.first_name or ""
    is_new = reg_user(uid, uname, fname)

    txt = t(uid, "welcome", name=fname)
    if is_new:
        txt += t(uid, "bonus", amount=BONUS_FIRST)
    txt += t(uid, "choose_lang")
    bot.send_message(uid, txt, parse_mode="Markdown", reply_markup=lang_kb())
    if is_new:
        try: bot.send_message(ADMIN_ID, f"🆕 Yangi foydalanuvchi: {fname} (@{uname}) | ID: {uid}")
        except: pass

@bot.message_handler(commands=["referat"])
def cmd_referat(msg):
    uid = msg.from_user.id
    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    sst(uid, "referat_t", svc="referat")
    bot.send_message(uid, t(uid, "enter_topic"), reply_markup=bk_kb())

@bot.message_handler(commands=["kursishi"])
def cmd_kurs(msg):
    uid = msg.from_user.id
    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    sst(uid, "kurs_t", svc="kurs")
    bot.send_message(uid, t(uid, "enter_topic"), reply_markup=bk_kb())

@bot.message_handler(commands=["mustaqilish"])
def cmd_mustaqil(msg):
    uid = msg.from_user.id
    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    sst(uid, "mustaqil_t", svc="mustaqil")
    bot.send_message(uid, t(uid, "enter_topic"), reply_markup=bk_kb())

@bot.message_handler(commands=["maqola"])
def cmd_maqola(msg):
    uid = msg.from_user.id
    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    sst(uid, "maqola_t", svc="maqola")
    bot.send_message(uid, t(uid, "enter_topic"), reply_markup=bk_kb())

@bot.message_handler(commands=["prezentatsiya"])
def cmd_prez(msg):
    uid = msg.from_user.id
    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    sst(uid, "prez_t", svc="prez")
    bot.send_message(uid, t(uid, "enter_topic"), reply_markup=bk_kb())

@bot.message_handler(commands=["test"])
def cmd_test(msg):
    uid = msg.from_user.id
    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    sst(uid, "test_t", svc="test")
    bot.send_message(uid, t(uid, "enter_topic"), reply_markup=bk_kb())

@bot.message_handler(commands=["imlo"])
def cmd_imlo(msg):
    uid = msg.from_user.id
    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    sst(uid, "imlo_t")
    kb2 = types.InlineKeyboardMarkup()
    kb2.add(types.InlineKeyboardButton("📁 Fayl yuborish (PDF/TXT)", callback_data="imlo_file"))
    bot.send_message(uid, t(uid, "imlo_prompt"), reply_markup=kb2)

@bot.message_handler(commands=["konvertatsiya"])
def cmd_konv(msg):
    uid = msg.from_user.id
    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    bot.send_message(uid, "🔄 Format tanlang:", reply_markup=conv_kb())

@bot.message_handler(commands=["balans"])
def cmd_balans(msg):
    uid = msg.from_user.id
    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    bal = get_balance(uid)
    kb2 = types.InlineKeyboardMarkup()
    kb2.add(types.InlineKeyboardButton(t(uid,"topup"), callback_data="topup"))
    bot.send_message(uid, t(uid, "balance_info", bal=bal), parse_mode="Markdown", reply_markup=kb2)

@bot.message_handler(commands=["menu"])
def cmd_menu(msg):
    uid = msg.from_user.id
    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")
    bot.send_message(uid, t(uid, "menu"), reply_markup=main_kb(uid))

@bot.message_handler(commands=["yordam", "help"])
def cmd_help(msg):
    uid = msg.from_user.id
    help_txt = t(uid, "help_text") + "\n\n" + t(uid, "prices",
        p1=PRICE_PAGE, p2=PRICE_KURS, p3=PRICE_MUSTAQIL,
        p4=PRICE_MAQOLA, p5=PRICE_SLIDE, p6=PRICE_TEST)
    bot.send_message(uid, help_txt, parse_mode="Markdown", reply_markup=main_kb(uid))

@bot.message_handler(commands=["stats"])
def cmd_stats(msg):
    if msg.from_user.id != ADMIN_ID: return
    u, w, c, i = get_stats()
    bot.send_message(msg.chat.id,
        f"📊 *Statistika*\n\n👥 Foydalanuvchilar: {u}\n"
        f"📝 Ishlar: {w}\n🔄 Konvertatsiyalar: {c}\n💰 Daromad: {i:,} so'm",
        parse_mode="Markdown")

@bot.message_handler(commands=["broadcast"])
def cmd_bc(msg):
    if msg.from_user.id != ADMIN_ID: return
    sst(msg.from_user.id, "bc")
    bot.send_message(msg.chat.id, "📢 Xabar matnini yozing:")

@bot.message_handler(commands=["addbalance"])
def cmd_addbal(msg):
    if msg.from_user.id != ADMIN_ID: return
    try:
        p = msg.text.split(); tid = int(p[1]); amt = int(p[2])
        add_bal(tid, amt)
        bot.send_message(msg.chat.id, f"✅ {tid} ga {amt:,} so'm qo'shildi!")
        bot.send_message(tid, f"💰 Hisobingizga {amt:,} so'm qo'shildi!\nBalans: {get_balance(tid):,} so'm")
    except: bot.send_message(msg.chat.id, "❌ /addbalance [id] [summa]")

@bot.message_handler(commands=["done"])
def cmd_done(msg):
    uid = msg.from_user.id
    imgs = UI.get(uid, [])
    if not imgs: return
    pm = bot.send_message(uid, "⏳ PDF yaratilmoqda...")
    td = tempfile.mkdtemp()
    try:
        out = os.path.join(td, "r.pdf")
        if imgs_to_pdf(imgs, out):
            with open(out, "rb") as f:
                bot.send_document(uid, f, caption="📄 PDF fayl!")
            log_act(uid, "conv", "img_pdf")
        else: bot.send_message(uid, "❌ Xatolik.")
    finally:
        shutil.rmtree(td, ignore_errors=True)
        UI.pop(uid, None); cst(uid)
    try: bot.delete_message(uid, pm.message_id)
    except: pass
    bot.send_message(uid, "✅", reply_markup=main_kb(uid))

# ============================================================
# RASM HANDLER
# ============================================================
@bot.message_handler(content_types=["photo"])
def photo_h(msg):
    uid = msg.from_user.id
    state = gst(uid)
    ph = msg.photo[-1]
    td = tempfile.mkdtemp()
    try:
        fi = bot.get_file(ph.file_id)
        data = bot.download_file(fi.file_path)
        p = os.path.join(td, f"img_{uid}_{len(UI.get(uid,[]))}.jpg")
        with open(p, "wb") as f: f.write(data)
        if state == "img":
            UI.setdefault(uid, []).append(p)
            bot.send_message(uid, t(uid, "img_count", n=len(UI[uid])))
        elif state and "wait_img" in state:
            UI.setdefault(uid, []).append(p)
            n = len(UI[uid]) - 1
            pkb = types.InlineKeyboardMarkup(row_width=5)
            btns = [types.InlineKeyboardButton(str(i), callback_data=f"ipage:{n}:{i}") for i in range(1,16)]
            pkb.add(*btns)
            pkb.add(types.InlineKeyboardButton("✅ Davom etish", callback_data="img_done"))
            bot.send_message(uid, t(uid, "img_accept"), reply_markup=pkb)
        else:
            bot.send_message(uid, "❌ Hozir rasm kutilmayapti.")
    except Exception as e:
        logger.error(f"Photo: {e}")

# ============================================================
# FAYL HANDLER
# ============================================================
@bot.message_handler(content_types=["document"])
def doc_h(msg):
    uid = msg.from_user.id
    state = gst(uid)
    d = msg.document
    if not d: return
    if d.file_size > 20*1024*1024:
        bot.send_message(uid, "❌ Fayl juda katta (max 20MB)"); return
    fname = (d.file_name or "").lower()
    td = tempfile.mkdtemp()
    try:
        fi = bot.get_file(d.file_id)
        data = bot.download_file(fi.file_path)
        inp = os.path.join(td, d.file_name or "f")
        with open(inp, "wb") as f: f.write(data)

        if state == "imlo_f":
            pm = bot.send_message(uid, t(uid, "imlo_check"))
            txt = ""
            if fname.endswith(".txt"):
                with open(inp, "r", encoding="utf-8", errors="ignore") as f: txt = f.read()
            elif fname.endswith(".pdf"):
                txt = pdf_to_text(inp)
            if txt:
                fixed = fix_spell(txt, get_lang(uid))
                try: bot.delete_message(uid, pm.message_id)
                except: pass
                bot.send_message(uid, t(uid, "imlo_done") + fixed[:3500], parse_mode="Markdown")
            else:
                try: bot.delete_message(uid, pm.message_id)
                except: pass
                bot.send_message(uid, t(uid, "imlo_notfound"))
            cst(uid)
            bot.send_message(uid, t(uid, "menu"), reply_markup=main_kb(uid))

        elif state == "cv_pptx":
            pm = bot.send_message(uid, t(uid, "converting"))
            if fname.endswith(".pptx"):
                try:
                    from pptx import Presentation as _P
                    prs = _P(inp)
                    content_txt = "\n".join(
                        shape.text for slide in prs.slides
                        for shape in slide.shapes if shape.has_text_frame
                    )
                    out, td2 = make_pdf(content_txt, fname, {})
                    if out:
                        with open(out, "rb") as f:
                            bot.send_document(uid, f, caption="📄 PDF tayyor!")
                        shutil.rmtree(td2, ignore_errors=True)
                    else: bot.send_message(uid, "❌ Xatolik.")
                except Exception as e:
                    bot.send_message(uid, f"❌ {e}")
            else: bot.send_message(uid, t(uid, "wrong_format"))
            try: bot.delete_message(uid, pm.message_id)
            except: pass
            cst(uid); bot.send_message(uid, t(uid, "menu"), reply_markup=main_kb(uid))
    except Exception as e:
        logger.error(f"Doc: {e}")
    finally:
        shutil.rmtree(td, ignore_errors=True)

# ============================================================
# MATN HANDLER
# ============================================================
@bot.message_handler(content_types=["text"])
def text_h(msg):
    uid = msg.from_user.id
    text = msg.text.strip()
    state = gst(uid)
    ud = UD.get(uid, {})

    reg_user(uid, msg.from_user.username or "", msg.from_user.first_name or "")

    # Barcha tillardagi menyu tugmalari
    menu_map = {}
    for lang in ["uz","ru","en"]:
        tx = TEXTS[lang]
        menu_map[tx["btn_referat"]] = ("referat_t", "referat")
        menu_map[tx["btn_kurs"]] = ("kurs_t", "kurs")
        menu_map[tx["btn_mustaqil"]] = ("mustaqil_t", "mustaqil")
        menu_map[tx["btn_maqola"]] = ("maqola_t", "maqola")
        menu_map[tx["btn_prez"]] = ("prez_t", "prez")
        menu_map[tx["btn_test"]] = ("test_t", "test")

    # Menyu tugmalari
    if text in menu_map:
        st2, svc = menu_map[text]
        sst(uid, st2, svc=svc)
        bot.send_message(uid, t(uid, "enter_topic"), reply_markup=bk_kb()); return

    # Imlo
    imlo_btns = [TEXTS[l]["btn_imlo"] for l in ["uz","ru","en"]]
    if text in imlo_btns:
        sst(uid, "imlo_t")
        kb2 = types.InlineKeyboardMarkup()
        kb2.add(types.InlineKeyboardButton("📁 Fayl yuborish (PDF/TXT)", callback_data="imlo_file"))
        bot.send_message(uid, t(uid, "imlo_prompt"), reply_markup=kb2); return

    # Konvertatsiya
    konv_btns = [TEXTS[l]["btn_konv"] for l in ["uz","ru","en"]]
    if text in konv_btns:
        bot.send_message(uid, "🔄 Format tanlang:", reply_markup=conv_kb()); return

    # Balans
    bal_btns = [TEXTS[l]["btn_balans"] for l in ["uz","ru","en"]]
    if text in bal_btns:
        bal = get_balance(uid)
        kb2 = types.InlineKeyboardMarkup()
        kb2.add(types.InlineKeyboardButton(t(uid,"topup"), callback_data="topup"))
        bot.send_message(uid, t(uid, "balance_info", bal=bal), parse_mode="Markdown", reply_markup=kb2); return

    # Buyurtmalarim
    orders_btns = [TEXTS[l]["btn_orders"] for l in ["uz","ru","en"]]
    if text in orders_btns:
        rows = get_buyurtmalar(uid)
        if not rows:
            bot.send_message(uid, t(uid, "no_orders"), reply_markup=main_kb(uid)); return
        tur_n = {"referat":"📄 Referat","kurs":"📝 Kurs ishi","mustaqil":"📋 Mustaqil ish",
                 "maqola":"📰 Maqola","prez":"📊 Prezentatsiya","test":"✅ Test"}
        txt2 = t(uid, "orders_title")
        for i, (tur, mavzu, fmt, sah, narx, sana) in enumerate(rows, 1):
            tur_lbl = tur_n.get(tur, tur)
            sl = t(uid,"slide_pages") if tur=="prez" else (t(uid,"savol_pages") if tur=="test" else t(uid,"bet_pages"))
            txt2 += f"{i}. {tur_lbl}\n📌 {mavzu}\n📁 {fmt.upper()} | {sah} {sl} | 💰 {int(narx):,} so'm\n🕐 {sana}\n\n"
        bot.send_message(uid, txt2, parse_mode="Markdown", reply_markup=main_kb(uid)); return

    # Donat
    donat_btns = [TEXTS[l]["btn_donat"] for l in ["uz","ru","en"]]
    if text in donat_btns:
        kb2 = types.InlineKeyboardMarkup()
        kb2.add(types.InlineKeyboardButton("🌐 Donat", url=DONATE_URL))
        bot.send_message(uid,
            f"💝 *Donat*\n\n💳 Karta: `{DONATE_CARD}`\n🟢 Click: `{DONATE_CLICK}`",
            parse_mode="Markdown", reply_markup=kb2); return

    # Yordam
    help_btns = [TEXTS[l]["btn_help"] for l in ["uz","ru","en"]]
    if text in help_btns:
        help_txt = t(uid, "help_text") + "\n\n" + t(uid, "prices",
            p1=PRICE_PAGE, p2=PRICE_KURS, p3=PRICE_MUSTAQIL,
            p4=PRICE_MAQOLA, p5=PRICE_SLIDE, p6=PRICE_TEST)
        bot.send_message(uid, help_txt, parse_mode="Markdown", reply_markup=main_kb(uid)); return

    # Admin
    admin_btns = [TEXTS[l]["btn_admin"] for l in ["uz","ru","en"]]
    if text in admin_btns:
        kb2 = types.InlineKeyboardMarkup()
        kb2.add(types.InlineKeyboardButton("💬 Adminga yozish",
            url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))
        bot.send_message(uid, "👨‍💼 Admin", reply_markup=kb2); return

    # Broadcast
    if state == "bc":
        users = all_users()
        ok = 0
        for u2 in users:
            try: bot.send_message(u2, text); ok += 1
            except: pass
        cst(uid)
        bot.send_message(uid, f"✅ {ok}/{len(users)} ta yuborildi!"); return

    # INFO STATES
    if state in INFO_STATES:
        idx = INFO_STATES.index(state)
        _, field, required = INFO_STEPS[idx]
        val = text.strip()
        if val: UD.setdefault(uid, {})[field] = val
        if idx < len(INFO_STEPS) - 1:
            ns, nfield, nreq = INFO_STEPS[idx + 1]
            sst(uid, ns)
            msg_txt = t(uid, ns)
            if not nreq:
                msg_txt += f"\n{t(uid,'optional')}"
                bot.send_message(uid, msg_txt, reply_markup=skip_kb(ns))
            else:
                bot.send_message(uid, msg_txt, reply_markup=bk_kb())
        else:
            finish_info(uid, UD.get(uid, {}))
        return

    # MAVZU KIRITISH STATES
    svc_topic_states = ["referat_t","kurs_t","mustaqil_t","maqola_t","prez_t","test_t"]
    if state in svc_topic_states:
        svc = ud.get("svc", state.replace("_t",""))
        UD.setdefault(uid, {})["topic"] = text
        # Ma'lumotlarni so'rash
        sst(uid, "ask_name", svc=svc, topic=text)
        bot.send_message(uid, t(uid, "ask_name"), reply_markup=bk_kb()); return

    # Sahifa soni
    if state in ["referat_p","kurs_p","mustaqil_p","maqola_p"]:
        try:
            pages = int(text)
            if pages < 1 or pages > 100:
                bot.send_message(uid, "❌ 1-100 oralig'ida kiriting!"); return
            svc = ud.get("svc","referat")
            price_map = {"referat":PRICE_PAGE,"kurs":PRICE_KURS,"mustaqil":PRICE_MUSTAQIL,"maqola":PRICE_MAQOLA}
            price = price_map.get(svc, PRICE_PAGE)
            total = pages * price
            UD.setdefault(uid, {})["pages"] = pages
            UD[uid]["total"] = total
            bal = get_balance(uid)
            if bal < total:
                kb2 = types.InlineKeyboardMarkup()
                kb2.add(types.InlineKeyboardButton(t(uid,"topup"), callback_data="topup"))
                bot.send_message(uid, t(uid,"no_balance",need=total,bal=bal), reply_markup=kb2); return
            sst(uid, f"{svc}_lang")
            bot.send_message(uid,
                f"✅ {pages} bet × {price:,} = *{total:,} so'm*\n\n{t(uid,'ask_lang')}",
                parse_mode="Markdown", reply_markup=lc_kb(f"{svc}_lang"))
        except:
            bot.send_message(uid, "❌ Raqam kiriting!")
        return

    # Test savol soni
    if state == "test_p":
        try:
            count = int(text)
            if count < 1 or count > 1000:
                bot.send_message(uid, "❌ 1-1000 oralig'ida kiriting!"); return
            total = count * PRICE_TEST
            UD.setdefault(uid, {})["count"] = count
            UD[uid]["total"] = total
            bal = get_balance(uid)
            if bal < total:
                kb2 = types.InlineKeyboardMarkup()
                kb2.add(types.InlineKeyboardButton(t(uid,"topup"), callback_data="topup"))
                bot.send_message(uid, t(uid,"no_balance",need=total,bal=bal), reply_markup=kb2); return
            sst(uid, "test_lang")
            bot.send_message(uid,
                f"✅ {count} savol × {PRICE_TEST:,} = *{total:,} so'm*\n\n{t(uid,'ask_lang')}",
                parse_mode="Markdown", reply_markup=lc_kb("test_lang"))
        except:
            bot.send_message(uid, "❌ Raqam kiriting!")
        return

    # Slayd soni (custom)
    if state == "prez_slides_custom":
        try:
            slides = int(text)
            if slides < 5 or slides > 100:
                bot.send_message(uid, "❌ 5-100 oralig'ida kiriting!"); return
            total = slides * PRICE_SLIDE
            UD.setdefault(uid, {})["slides"] = slides
            UD[uid]["total"] = total
            bal = get_balance(uid)
            if bal < total:
                kb2 = types.InlineKeyboardMarkup()
                kb2.add(types.InlineKeyboardButton(t(uid,"topup"), callback_data="topup"))
                bot.send_message(uid, t(uid,"no_balance",need=total,bal=bal), reply_markup=kb2); return
            sst(uid, "prez_plans")
            bot.send_message(uid,
                f"✅ {slides} slayd × {PRICE_SLIDE:,} = *{total:,} so'm*\n\n{t(uid,'ask_plans')}",
                parse_mode="Markdown", reply_markup=plans_kb())
        except:
            bot.send_message(uid, "❌ Raqam kiriting!")
        return

    # Reja soni (custom)
    if state == "prez_plans_custom":
        try:
            plans = int(text)
            if plans < 2 or plans > 20:
                bot.send_message(uid, "❌ 2-20 oralig'ida kiriting!"); return
            UD.setdefault(uid, {})["plans_count"] = plans
            sst(uid, "prez_lang")
            bot.send_message(uid, t(uid, "ask_lang"), reply_markup=lc_kb("prez_lang"))
        except:
            bot.send_message(uid, "❌ Raqam kiriting!")
        return

    # Imlo matn
    if state == "imlo_t":
        pm = bot.send_message(uid, t(uid, "imlo_check"))
        fixed = fix_spell(text, get_lang(uid))
        try: bot.delete_message(uid, pm.message_id)
        except: pass
        bot.send_message(uid, t(uid, "imlo_done") + fixed[:3500], parse_mode="Markdown")
        cst(uid)
        bot.send_message(uid, t(uid, "menu"), reply_markup=main_kb(uid)); return

# ============================================================
# CALLBACK HANDLER
# ============================================================
@bot.callback_query_handler(func=lambda c: True)
def cb(call):
    uid = call.from_user.id
    d = call.data
    ud = UD.get(uid, {})

    # Til tanlash
    if d.startswith("lang:"):
        lang = d[5:]
        set_lang(uid, lang)
        try: bot.edit_message_text(TEXTS[lang]["lang_set"], uid, call.message.message_id)
        except: pass
        bot.send_message(uid, t(uid, "menu"), reply_markup=main_kb(uid))
        return

    # Menyu
    if d == "bk":
        cst(uid)
        try: bot.edit_message_text(t(uid,"menu"), uid, call.message.message_id)
        except: pass
        bot.send_message(uid, t(uid,"menu"), reply_markup=main_kb(uid)); return

    # Orqaga
    if d == "back_step":
        prev = go_back(uid)
        if prev:
            bot.send_message(uid, f"◀️ {prev}", reply_markup=bk_kb())
        else:
            cst(uid)
            bot.send_message(uid, t(uid,"menu"), reply_markup=main_kb(uid)); return

    # Skip
    if d.startswith("skip:"):
        ns = d[5:]
        idx = INFO_STATES.index(ns) if ns in INFO_STATES else -1
        if idx >= 0 and idx < len(INFO_STEPS) - 1:
            next_ns, _, nreq = INFO_STEPS[idx + 1]
            sst(uid, next_ns)
            msg_txt = t(uid, next_ns)
            if not nreq:
                msg_txt += f"\n{t(uid,'optional')}"
                bot.send_message(uid, msg_txt, reply_markup=skip_kb(next_ns))
            else:
                bot.send_message(uid, msg_txt, reply_markup=bk_kb())
        else:
            finish_info(uid, UD.get(uid, {}))
        return

    # Shablon tanlash
    if d.startswith("tmpl:"):
        tmpl_id = d[5:]
        UD.setdefault(uid, {})["template_id"] = tmpl_id
        sst(uid, "prez_slides")
        bot.send_message(uid,
            t(uid,"enter_slides", price=PRICE_SLIDE),
            reply_markup=slides_kb())
        return

    if d.startswith("tmpl_p:"):
        page = int(d[7:])
        try: bot.edit_message_reply_markup(uid, call.message.message_id, reply_markup=tmpl_kb(page))
        except: pass; return

    # Slayd soni
    if d.startswith("slides:"):
        val = d[7:]
        if val == "custom":
            sst(uid, "prez_slides_custom")
            bot.send_message(uid, "✏️ Slayd sonini kiriting (5-100):"); return
        slides = int(val)
        total = slides * PRICE_SLIDE
        UD.setdefault(uid, {})["slides"] = slides
        UD[uid]["total"] = total
        bal = get_balance(uid)
        if bal < total:
            kb2 = types.InlineKeyboardMarkup()
            kb2.add(types.InlineKeyboardButton(t(uid,"topup"), callback_data="topup"))
            bot.send_message(uid, t(uid,"no_balance",need=total,bal=bal), reply_markup=kb2); return
        sst(uid, "prez_plans")
        bot.send_message(uid,
            f"✅ {slides} slayd × {PRICE_SLIDE:,} = *{total:,} so'm*\n\n{t(uid,'ask_plans')}",
            parse_mode="Markdown", reply_markup=plans_kb())
        return

    # Reja soni
    if d.startswith("plans:"):
        val = d[6:]
        if val == "custom":
            sst(uid, "prez_plans_custom")
            bot.send_message(uid, "✏️ Bo'lim sonini kiriting (2-20):"); return
        UD.setdefault(uid, {})["plans_count"] = int(val)
        sst(uid, "prez_lang")
        bot.send_message(uid, t(uid,"ask_lang"), reply_markup=lc_kb("prez_lang"))
        return

    # Til (til_lang format: referat_lang:uz)
    for svc in ["referat","kurs","mustaqil","maqola","prez","test"]:
        if d.startswith(f"{svc}_lang:"):
            lang = d.split(":")[1]
            UD.setdefault(uid, {})["lang"] = lang
            if svc == "prez":
                sst(uid, "prez_img")
                bot.send_message(uid, "🖼 Prezentatsiyaga rasm qo'shmoqchimisiz?", reply_markup=img_choice_kb())
            elif svc == "test":
                sst(uid, "test_confirm")
                count = ud.get("count", 10)
                total = ud.get("total", count * PRICE_TEST)
                bot.send_message(uid,
                    f"📊 *Test:* {ud.get('topic','')}\n"
                    f"📝 {count} ta savol | 💰 {total:,} so'm\n\n"
                    f"Tasdiqlaysizmi?",
                    parse_mode="Markdown",
                    reply_markup=types.InlineKeyboardMarkup().add(
                        types.InlineKeyboardButton("✅ Ha, yaratish", callback_data="test_go"),
                        types.InlineKeyboardButton("❌ Bekor", callback_data="bk")
                    ))
            else:
                sst(uid, f"{svc}_pages")
                price_map = {"referat":PRICE_PAGE,"kurs":PRICE_KURS,"mustaqil":PRICE_MUSTAQIL,"maqola":PRICE_MAQOLA}
                price = price_map.get(svc, PRICE_PAGE)
                bot.send_message(uid, t(uid,"enter_pages",price=price), reply_markup=bk_kb())
            return

    # Test savol soni
    if d.startswith("tcount:"):
        val = d[7:]
        if val == "custom":
            sst(uid, "test_p")
            bot.send_message(uid, t(uid,"enter_count",price=PRICE_TEST)); return
        count = int(val)
        total = count * PRICE_TEST
        UD.setdefault(uid, {})["count"] = count
        UD[uid]["total"] = total
        bal = get_balance(uid)
        if bal < total:
            kb2 = types.InlineKeyboardMarkup()
            kb2.add(types.InlineKeyboardButton(t(uid,"topup"), callback_data="topup"))
            bot.send_message(uid, t(uid,"no_balance",need=total,bal=bal), reply_markup=kb2); return
        sst(uid, "test_lang")
        bot.send_message(uid,
            f"✅ {count} savol × {PRICE_TEST:,} = *{total:,} so'm*\n\n{t(uid,'ask_lang')}",
            parse_mode="Markdown", reply_markup=lc_kb("test_lang"))
        return

    # Rasm tanlash
    if d.startswith("img:"):
        choice = d[4:]
        slides = ud.get("slides", 15)
        if choice == "ai":
            ai_slides = list(range(3, slides+1, 3))
            UD.setdefault(uid, {})["ai_img_slides"] = ai_slides
            sst(uid, "prez_fmt")
            bot.send_message(uid, t(uid,"ask_format"), reply_markup=prez_fmt_kb())
        elif choice == "user":
            sst(uid, "wait_img")
            bot.send_message(uid,
                f"🖼 Rasmlarni yuboring (har rasm uchun qaysi slayd belgilanadi)\n"
                f"Tugatgach /done yozing.")
        elif choice == "none":
            UD.setdefault(uid, {})["ai_img_slides"] = []
            sst(uid, "prez_fmt")
            bot.send_message(uid, t(uid,"ask_format"), reply_markup=prez_fmt_kb())
        return

    if d == "img_done":
        sst(uid, "prez_fmt")
        bot.send_message(uid, t(uid,"ask_format"), reply_markup=prez_fmt_kb()); return

    if d.startswith("ipage:"):
        parts = d.split(":"); img_idx = int(parts[1]); page_num = int(parts[2])
        UD.setdefault(uid, {}).setdefault("img_pages", {})[str(img_idx)] = page_num
        bot.answer_callback_query(call.id, f"✅ {page_num}-slaydga qo'shildi!")
        return

    # Format tanlash (hujjat)
    for svc in ["referat","kurs","mustaqil","maqola"]:
        if d.startswith(f"{svc}_fmt:"):
            fmt = d.split(":")[1]
            UD.setdefault(uid, {})["fmt"] = fmt
            topic = ud.get("topic","")
            pages = ud.get("pages", 5)
            lang = ud.get("lang", get_lang(uid))
            total = ud.get("total", pages * PRICE_PAGE)
            bal = get_balance(uid)
            if bal < total:
                kb2 = types.InlineKeyboardMarkup()
                kb2.add(types.InlineKeyboardButton(t(uid,"topup"), callback_data="topup"))
                bot.send_message(uid, t(uid,"no_balance",need=total,bal=bal), reply_markup=kb2); return
            deduct(uid, total)
            pm = bot.send_message(uid, t(uid,"preparing"))
            import threading
            def gen_doc_task():
                td2 = None
                try:
                    content = gen_doc(svc, topic, pages, lang, ud)
                    if fmt == "docx":
                        out, td2 = make_docx(content, topic, ud)
                        cap = "📝 DOCX fayl tayyor!"
                        fname2 = "dokument.docx"
                    elif fmt == "pdf":
                        out, td2 = make_pdf(content, topic, ud)
                        cap = "📄 PDF fayl tayyor!"
                        fname2 = "dokument.pdf"
                    else:
                        out = None
                        bot.send_message(uid, f"📱 *{topic}*\n\n{content[:4000]}", parse_mode="Markdown")
                        cap = None
                    if out and cap:
                        with open(out, "rb") as f:
                            bot.send_document(uid, f, caption=cap, visible_file_name=fname2)
                    log_act(uid, svc, topic, total)
                    save_buyurtma(uid, svc, topic, fmt, pages, total)
                except Exception as e:
                    logger.error(f"Doc gen: {e}")
                    add_bal(uid, total)
                    bot.send_message(uid, t(uid,"error"))
                finally:
                    if td2: shutil.rmtree(td2, ignore_errors=True)
                    try: bot.delete_message(uid, pm.message_id)
                    except: pass
                    cst(uid)
                    bot.send_message(uid, t(uid,"ready",bal=get_balance(uid)), reply_markup=main_kb(uid))
            threading.Thread(target=gen_doc_task).start()
            return

    # Prezentatsiya format
    if d.startswith("pfmt:"):
        fmt = d[5:]
        UD.setdefault(uid, {})["fmt"] = fmt
        topic = ud.get("topic","")
        slides = ud.get("slides", 15)
        lang = ud.get("lang", get_lang(uid))
        plans = ud.get("plans_count", 5)
        total = ud.get("total", slides * PRICE_SLIDE)
        tmpl_id = ud.get("template_id", "1")
        tmpl_name = TEMPLATES.get(str(tmpl_id), TEMPLATES["1"])["name"]
        bal = get_balance(uid)
        if bal < total:
            kb2 = types.InlineKeyboardMarkup()
            kb2.add(types.InlineKeyboardButton(t(uid,"topup"), callback_data="topup"))
            bot.send_message(uid, t(uid,"no_balance",need=total,bal=bal), reply_markup=kb2); return
        deduct(uid, total)
        pm = bot.send_message(uid, t(uid,"preparing"))
        user_imgs = UI.get(uid, [])
        img_pages = ud.get("img_pages", {})
        import threading
        def gen_prez_task():
            td2 = None
            try:
                content = gen_prez(topic, slides, lang, ud, plans)
                if fmt in ["pptx","both"]:
                    out, td2 = make_pptx(content, topic, tmpl_id, ud, user_imgs, img_pages)
                    with open(out, "rb") as f:
                        bot.send_document(uid, f, caption="📊 PPTX tayyor!", visible_file_name="prezentatsiya.pptx")
                    shutil.rmtree(td2, ignore_errors=True)
                if fmt in ["html","both"]:
                    out2, td3 = make_html(content, topic, tmpl_id, ud)
                    with open(out2, "rb") as f:
                        bot.send_document(uid, f, caption="🌐 HTML tayyor!", visible_file_name="prezentatsiya.html")
                    shutil.rmtree(td3, ignore_errors=True)
                log_act(uid, "prez", topic, total)
                save_buyurtma(uid, "prez", topic, fmt, slides, total)
            except Exception as e:
                logger.error(f"Prez gen: {e}")
                add_bal(uid, total)
                bot.send_message(uid, t(uid,"error"))
            finally:
                try: bot.delete_message(uid, pm.message_id)
                except: pass
                UI.pop(uid, None); cst(uid)
                bot.send_message(uid, t(uid,"ready",bal=get_balance(uid)), reply_markup=main_kb(uid))
        threading.Thread(target=gen_prez_task).start()
        return

    # Test yaratish
    if d == "test_go":
        topic = ud.get("topic","")
        count = ud.get("count", 10)
        lang = ud.get("lang", get_lang(uid))
        total = ud.get("total", count * PRICE_TEST)
        bal = get_balance(uid)
        if bal < total:
            kb2 = types.InlineKeyboardMarkup()
            kb2.add(types.InlineKeyboardButton(t(uid,"topup"), callback_data="topup"))
            bot.send_message(uid, t(uid,"no_balance",need=total,bal=bal), reply_markup=kb2); return
        deduct(uid, total)
        pm = bot.send_message(uid, t(uid,"preparing"))
        import threading
        def gen_test_task():
            try:
                content = gen_test(topic, count, lang)
                bot.send_message(uid, f"✅ *{topic}*\n\n{content[:4000]}", parse_mode="Markdown")
                log_act(uid, "test", topic, total)
                save_buyurtma(uid, "test", topic, "txt", count, total)
            except Exception as e:
                logger.error(f"Test gen: {e}")
                add_bal(uid, total)
                bot.send_message(uid, t(uid,"error"))
            finally:
                try: bot.delete_message(uid, pm.message_id)
                except: pass
                cst(uid)
                bot.send_message(uid, t(uid,"ready",bal=get_balance(uid)), reply_markup=main_kb(uid))
        threading.Thread(target=gen_test_task).start()
        return

    # Konvertatsiya
    if d.startswith("cv:"):
        cv_type = d[3:]
        if cv_type == "img":
            sst(uid, "img")
            bot.send_message(uid, "📷 Rasmlarni yuboring, so'ng /done yozing.")
        elif cv_type == "pptx":
            sst(uid, "cv_pptx")
            bot.send_message(uid, "📊 PPTX faylni yuboring:")
        elif cv_type == "pdf":
            bot.send_message(uid, "🔄 Hozircha PDF → PPTX qo'llab-quvvatlanmaydi.")
        return

    # Imlo fayl
    if d == "imlo_file":
        sst(uid, "imlo_f")
        bot.send_message(uid, "📁 PDF yoki TXT faylni yuboring:"); return

    # Topup
    if d == "topup":
        bot.send_message(uid,
            f"💳 *Balans to'ldirish*\n\n"
            f"💳 Karta: `{DONATE_CARD}`\n"
            f"🟢 Click: `{DONATE_CLICK}`\n\n"
            f"To'lovdan keyin admin: {ADMIN_USERNAME}",
            parse_mode="Markdown"); return

    try: bot.answer_callback_query(call.id)
    except: pass

# ============================================================
# ASOSIY
# ============================================================
if __name__ == "__main__":
    init_db()
    try:
        bot.set_my_commands([
            types.BotCommand("start", "Botni ishga tushirish"),
            types.BotCommand("referat", "Referat yozish"),
            types.BotCommand("kursishi", "Kurs ishi yozish"),
            types.BotCommand("mustaqilish", "Mustaqil ish yozish"),
            types.BotCommand("maqola", "Ilmiy maqola yozish"),
            types.BotCommand("prezentatsiya", "Prezentatsiya yaratish"),
            types.BotCommand("test", "Test savollari yaratish"),
            types.BotCommand("imlo", "Imlo tuzatish"),
            types.BotCommand("konvertatsiya", "Fayl konvertatsiya"),
            types.BotCommand("balans", "Balansni ko'rish"),
            types.BotCommand("yordam", "Yordam va narxlar"),
            types.BotCommand("menu", "Asosiy menyuni ochish"),
        ])
        logger.info("Buyruqlar ro'yxatlandi!")
    except Exception as e:
        logger.error(f"Commands: {e}")
    logger.info("EduBot v12 ishga tushdi!")
    bot.infinity_polling(timeout=60, long_polling_timeout=60)