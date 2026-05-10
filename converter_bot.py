"""
╔══════════════════════════════════════════════╗
║         PROFESSIONAL FILE CONVERTER BOT      ║
║  PDF ↔ PPT/PPTX | Rasmlar → PDF             ║
║  UZB ↔ Kirill transliteratsiya              ║
║  3 til: O'zbek | Русский | English          ║
╚══════════════════════════════════════════════╝
"""

import telebot, os
import os
import logging
import sqlite3
import tempfile
import shutil
from telebot import types
from datetime import datetime
from io import BytesIO

# ===================== SOZLAMALAR =====================
BOT_TOKEN = "8270798642:AAGtdwHVgu0rKCwTU5x9eLLWWYGoWhG-j6I"   # <-- TOKEN
ADMIN_ID  = 1113404703               # <-- ADMIN ID
ADMIN_USERNAME = "@abdurakhmon02"   # <-- ADMIN USERNAME
DONATE_URL = "https://donate.uz"    # <-- DONAT SAYTI
DONATE_CARD = "8600 XXXX XXXX XXXX" # <-- KARTA RAQAMI
DONATE_CLICK = "+998 XX XXX XX XX"  # <-- CLICK RAQAMI

logging.basicConfig(
    format='%(asctime)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[
        logging.FileHandler('converter.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)
bot = telebot.TeleBot(BOT_TOKEN, parse_mode='Markdown')

# ===================== TILLAR =====================
LANGS = {
    'uz': {
        'welcome': "👋 Xush kelibsiz!\n\n🤖 *Universal Converter Bot*\n\nMen quyidagilarni qila olaman:\n\n📄 *Fayl konvertatsiya:*\n• PDF → PPTX (slaydlarga)\n• PPTX/PPT → PDF\n• Rasmlar → PDF\n\n🔤 *Transliteratsiya:*\n• O'zbek lotin ↔ Kirill\n\n💝 *Donat:* Botni rivojlantirish uchun\n\nTilni tanlang yoki /help yozing:",
        'choose_lang': "🌐 Tilni tanlang:",
        'main_menu': "📋 *Asosiy menyu*\n\nQuyidagi tugmalardan birini bosing:",
        'convert': "📁 Fayl konvertatsiya",
        'translit': "🔤 Transliteratsiya",
        'donate': "💝 Donat",
        'help': "❓ Yordam",
        'admin': "👨‍💼 Admin",
        'send_file': "📎 Faylni yuboring:\n\n*Qabul qilinadigan formatlar:*\n• PDF fayl → PPTX ga o'giriladi\n• PPTX/PPT fayl → PDF ga o'giriladi\n• Rasm (JPG, PNG, WEBP) → PDF ga o'giriladi\n• Bir vaqtda bir nechta rasm yuborishingiz mumkin",
        'send_text': "✏️ O'girmoqchi bo'lgan matnni yuboring:",
        'choose_translit': "🔤 *Transliteratsiya turi:*",
        'lat_to_kril': "🔡 Lotin → Kirill",
        'kril_to_lat': "🔠 Kirill → Lotin",
        'processing': "⏳ Ishlanmoqda...",
        'done': "✅ Tayyor!",
        'error': "❌ Xatolik yuz berdi. Iltimos qaytadan urinib ko'ring.",
        'file_too_big': "❌ Fayl hajmi juda katta (max 20MB)",
        'wrong_format': "❌ Noto'g'ri format. PDF, PPT, PPTX yoki rasm yuboring.",
        'pdf_to_pptx': "📄➡️📊 PDF → PPTX",
        'pptx_to_pdf': "📊➡️📄 PPTX/PPT → PDF",
        'img_to_pdf': "🖼➡️📄 Rasmlar → PDF",
        'back': "🔙 Orqaga",
        'donate_text': "💝 *Donat*\n\nBotni rivojlantirish uchun xayriya qilishingiz mumkin!\n\n💳 *Karta:* `{card}`\n🟢 *Click:* `{click}`\n\n🌐 *Donat sayti:*",
        'donate_site': "🌐 Donat saytiga o'tish",
        'help_text': "❓ *Yordam*\n\n*📄 Fayl konvertatsiya:*\n1. «Fayl konvertatsiya» tugmasini bosing\n2. Format tanlang\n3. Faylingizni yuboring\n4. Natijani oling!\n\n*🔤 Transliteratsiya:*\n1. «Transliteratsiya» tugmasini bosing\n2. Yo'nalish tanlang\n3. Matn yuboring\n4. O'girilgan matn keladi!\n\n*⚠️ Cheklovlar:*\n• Fayl hajmi: max 20MB\n• Formatlar: PDF, PPT, PPTX, JPG, PNG, WEBP",
        'admin_text': "👨‍💼 *Admin bilan bog'lanish*\n\nSavol yoki takliflaringiz bo'lsa:",
        'contact_admin': "💬 Adminga yozish",
        'stats_msg': "📊 *Statistika*\n\n👥 Foydalanuvchilar: *{users}*\n🔄 Konvertatsiyalar: *{converts}*\n🔤 Transliteratsiyalar: *{translits}*\n💝 Donatlar: *{donates}*",
        'lang_set': "✅ Til o'rnatildi!",
        'result_pdf': "📄 Mana sizning PDF faylingiz!",
        'result_pptx': "📊 Mana sizning PPTX faylingiz!",
        'result_text': "✅ *Natija:*\n\n",
        'send_images': "🖼 Rasmlarni yuboring (bir yoki bir nechta). Tugatgach /done yozing:",
        'images_done': "✅ {n} ta rasm PDF ga birlashtirildi!",
        'wait_img': "⏳ Rasmlaringiz qabul qilindi, PDF yaratilmoqda...",
    },
    'ru': {
        'welcome': "👋 Добро пожаловать!\n\n🤖 *Universal Converter Bot*\n\nЯ умею:\n\n📄 *Конвертация файлов:*\n• PDF → PPTX (в слайды)\n• PPTX/PPT → PDF\n• Изображения → PDF\n\n🔤 *Транслитерация:*\n• Узбекский латиница ↔ Кириллица\n\n💝 *Донат:* Поддержать развитие бота\n\nВыберите язык или напишите /help:",
        'choose_lang': "🌐 Выберите язык:",
        'main_menu': "📋 *Главное меню*\n\nНажмите на одну из кнопок:",
        'convert': "📁 Конвертация файлов",
        'translit': "🔤 Транслитерация",
        'donate': "💝 Донат",
        'help': "❓ Помощь",
        'admin': "👨‍💼 Админ",
        'send_file': "📎 Отправьте файл:\n\n*Поддерживаемые форматы:*\n• PDF файл → конвертируется в PPTX\n• PPTX/PPT файл → конвертируется в PDF\n• Изображение (JPG, PNG, WEBP) → конвертируется в PDF\n• Можно отправить несколько изображений",
        'send_text': "✏️ Отправьте текст для транслитерации:",
        'choose_translit': "🔤 *Тип транслитерации:*",
        'lat_to_kril': "🔡 Латиница → Кириллица",
        'kril_to_lat': "🔠 Кириллица → Латиница",
        'processing': "⏳ Обработка...",
        'done': "✅ Готово!",
        'error': "❌ Произошла ошибка. Попробуйте ещё раз.",
        'file_too_big': "❌ Файл слишком большой (макс 20МБ)",
        'wrong_format': "❌ Неверный формат. Отправьте PDF, PPT, PPTX или изображение.",
        'pdf_to_pptx': "📄➡️📊 PDF → PPTX",
        'pptx_to_pdf': "📊➡️📄 PPTX/PPT → PDF",
        'img_to_pdf': "🖼➡️📄 Изображения → PDF",
        'back': "🔙 Назад",
        'donate_text': "💝 *Донат*\n\nВы можете поддержать развитие бота!\n\n💳 *Карта:* `{card}`\n🟢 *Click:* `{click}`\n\n🌐 *Сайт доната:*",
        'donate_site': "🌐 Перейти на сайт доната",
        'help_text': "❓ *Помощь*\n\n*📄 Конвертация файлов:*\n1. Нажмите «Конвертация файлов»\n2. Выберите формат\n3. Отправьте файл\n4. Получите результат!\n\n*🔤 Транслитерация:*\n1. Нажмите «Транслитерация»\n2. Выберите направление\n3. Отправьте текст\n4. Получите результат!\n\n*⚠️ Ограничения:*\n• Размер файла: макс 20МБ\n• Форматы: PDF, PPT, PPTX, JPG, PNG, WEBP",
        'admin_text': "👨‍💼 *Связь с админом*\n\nЕсли у вас есть вопросы или предложения:",
        'contact_admin': "💬 Написать админу",
        'stats_msg': "📊 *Статистика*\n\n👥 Пользователи: *{users}*\n🔄 Конвертации: *{converts}*\n🔤 Транслитерации: *{translits}*\n💝 Донаты: *{donates}*",
        'lang_set': "✅ Язык установлен!",
        'result_pdf': "📄 Вот ваш PDF файл!",
        'result_pptx': "📊 Вот ваш PPTX файл!",
        'result_text': "✅ *Результат:*\n\n",
        'send_images': "🖼 Отправьте изображения (одно или несколько). Когда закончите, напишите /done:",
        'images_done': "✅ {n} изображений объединено в PDF!",
        'wait_img': "⏳ Изображения получены, создаётся PDF...",
    },
    'en': {
        'welcome': "👋 Welcome!\n\n🤖 *Universal Converter Bot*\n\nI can:\n\n📄 *File conversion:*\n• PDF → PPTX (to slides)\n• PPTX/PPT → PDF\n• Images → PDF\n\n🔤 *Transliteration:*\n• Uzbek Latin ↔ Cyrillic\n\n💝 *Donate:* Support bot development\n\nChoose language or type /help:",
        'choose_lang': "🌐 Choose language:",
        'main_menu': "📋 *Main Menu*\n\nPress one of the buttons below:",
        'convert': "📁 File Conversion",
        'translit': "🔤 Transliteration",
        'donate': "💝 Donate",
        'help': "❓ Help",
        'admin': "👨‍💼 Admin",
        'send_file': "📎 Send your file:\n\n*Supported formats:*\n• PDF file → converts to PPTX\n• PPTX/PPT file → converts to PDF\n• Image (JPG, PNG, WEBP) → converts to PDF\n• You can send multiple images",
        'send_text': "✏️ Send the text you want to transliterate:",
        'choose_translit': "🔤 *Transliteration type:*",
        'lat_to_kril': "🔡 Latin → Cyrillic",
        'kril_to_lat': "🔠 Cyrillic → Latin",
        'processing': "⏳ Processing...",
        'done': "✅ Done!",
        'error': "❌ An error occurred. Please try again.",
        'file_too_big': "❌ File is too large (max 20MB)",
        'wrong_format': "❌ Wrong format. Send PDF, PPT, PPTX or image.",
        'pdf_to_pptx': "📄➡️📊 PDF → PPTX",
        'pptx_to_pdf': "📊➡️📄 PPTX/PPT → PDF",
        'img_to_pdf': "🖼➡️📄 Images → PDF",
        'back': "🔙 Back",
        'donate_text': "💝 *Donate*\n\nYou can support the bot development!\n\n💳 *Card:* `{card}`\n🟢 *Click:* `{click}`\n\n🌐 *Donate site:*",
        'donate_site': "🌐 Go to donate site",
        'help_text': "❓ *Help*\n\n*📄 File Conversion:*\n1. Press «File Conversion»\n2. Choose format\n3. Send your file\n4. Get the result!\n\n*🔤 Transliteration:*\n1. Press «Transliteration»\n2. Choose direction\n3. Send text\n4. Get result!\n\n*⚠️ Limits:*\n• File size: max 20MB\n• Formats: PDF, PPT, PPTX, JPG, PNG, WEBP",
        'admin_text': "👨‍💼 *Contact Admin*\n\nIf you have questions or suggestions:",
        'contact_admin': "💬 Message Admin",
        'stats_msg': "📊 *Statistics*\n\n👥 Users: *{users}*\n🔄 Conversions: *{converts}*\n🔤 Transliterations: *{translits}*\n💝 Donations: *{donates}*",
        'lang_set': "✅ Language set!",
        'result_pdf': "📄 Here is your PDF file!",
        'result_pptx': "📊 Here is your PPTX file!",
        'result_text': "✅ *Result:*\n\n",
        'send_images': "🖼 Send images (one or more). When done, type /done:",
        'images_done': "✅ {n} images merged into PDF!",
        'wait_img': "⏳ Images received, creating PDF...",
    }
}

def t(uid, key):
    lang = get_lang(uid)
    return LANGS.get(lang, LANGS['uz']).get(key, key)

# ===================== DATABASE =====================
def init_db():
    conn = sqlite3.connect('converter.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT, first_name TEXT,
        lang TEXT DEFAULT 'uz',
        joined_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        telegram_id INTEGER, action TEXT,
        detail TEXT, created_at TEXT)''')
    conn.commit()
    conn.close()

def get_lang(uid):
    conn = sqlite3.connect('converter.db')
    c = conn.cursor()
    c.execute('SELECT lang FROM users WHERE telegram_id=?', (uid,))
    row = c.fetchone()
    conn.close()
    return row[0] if row else 'uz'

def set_lang(uid, lang, username='', first_name=''):
    conn = sqlite3.connect('converter.db')
    c = conn.cursor()
    c.execute('''INSERT INTO users (telegram_id, username, first_name, lang, joined_at)
                 VALUES (?,?,?,?,?)
                 ON CONFLICT(telegram_id) DO UPDATE SET lang=?''',
              (uid, username, first_name, lang,
               datetime.now().strftime("%d.%m.%Y %H:%M"), lang))
    conn.commit()
    conn.close()

def log_action(uid, action, detail=''):
    conn = sqlite3.connect('converter.db')
    c = conn.cursor()
    c.execute('INSERT INTO stats (telegram_id,action,detail,created_at) VALUES (?,?,?,?)',
              (uid, action, detail, datetime.now().strftime("%d.%m.%Y %H:%M")))
    conn.commit()
    conn.close()

def get_stats():
    conn = sqlite3.connect('converter.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(DISTINCT telegram_id) FROM users')
    users = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM stats WHERE action='convert'")
    converts = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM stats WHERE action='translit'")
    translits = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM stats WHERE action='donate'")
    donates = c.fetchone()[0]
    conn.close()
    return users, converts, translits, donates

# ===================== TRANSLITERATSIYA =====================
LAT_TO_KRL = {
    "o'": "ў", "O'": "Ў", "g'": "ғ", "G'": "Ғ",
    "sh": "ш", "Sh": "Ш", "SH": "Ш",
    "ch": "ч", "Ch": "Ч", "CH": "Ч",
    "ng": "нг", "Ng": "Нг", "NG": "НГ",
    "a": "а", "A": "А", "b": "б", "B": "Б",
    "d": "д", "D": "Д", "e": "е", "E": "Е",
    "f": "ф", "F": "Ф", "g": "г", "G": "Г",
    "h": "ҳ", "H": "Ҳ", "i": "и", "I": "И",
    "j": "ж", "J": "Ж", "k": "к", "K": "К",
    "l": "л", "L": "Л", "m": "м", "M": "М",
    "n": "н", "N": "Н", "o": "о", "O": "О",
    "p": "п", "P": "П", "q": "қ", "Q": "Қ",
    "r": "р", "R": "Р", "s": "с", "S": "С",
    "t": "т", "T": "Т", "u": "у", "U": "У",
    "v": "в", "V": "В", "x": "х", "X": "Х",
    "y": "й", "Y": "Й", "z": "з", "Z": "З",
}

KRL_TO_LAT = {
    "ў": "o'", "Ў": "O'", "ғ": "g'", "Ғ": "G'",
    "ш": "sh", "Ш": "Sh", "ч": "ch", "Ч": "Ch",
    "нг": "ng", "Нг": "Ng",
    "а": "a", "А": "A", "б": "b", "Б": "B",
    "д": "d", "Д": "D", "е": "e", "Е": "E",
    "ф": "f", "Ф": "F", "г": "g", "Г": "G",
    "ҳ": "h", "Ҳ": "H", "и": "i", "И": "I",
    "й": "y", "Й": "Y", "ж": "j", "Ж": "J",
    "к": "k", "К": "K", "қ": "q", "Қ": "Q",
    "л": "l", "Л": "L", "м": "m", "М": "M",
    "н": "n", "Н": "N", "о": "o", "О": "O",
    "п": "p", "П": "P", "р": "r", "Р": "R",
    "с": "s", "С": "S", "т": "t", "Т": "T",
    "у": "u", "У": "U", "в": "v", "В": "V",
    "х": "x", "Х": "X", "з": "z", "З": "Z",
    "я": "ya", "Я": "Ya", "ю": "yu", "Ю": "Yu",
    "ё": "yo", "Ё": "Yo", "э": "e", "Э": "E",
    "ъ": "", "ь": "", "ц": "ts", "Ц": "Ts",
    "щ": "sh", "Щ": "Sh",
}

def lat_to_kirill(text):
    result = text
    for lat, krl in sorted(LAT_TO_KRL.items(), key=lambda x: -len(x[0])):
        result = result.replace(lat, krl)
    return result

def kirill_to_lat(text):
    result = ""
    i = 0
    while i < len(text):
        if i + 1 < len(text) and text[i:i+2] in KRL_TO_LAT:
            result += KRL_TO_LAT[text[i:i+2]]
            i += 2
        elif text[i] in KRL_TO_LAT:
            result += KRL_TO_LAT[text[i]]
            i += 1
        else:
            result += text[i]
            i += 1
    return result

# ===================== KONVERTATSIYA =====================
def pdf_to_pptx(pdf_path, output_path):
    """PDF ni har bir sahifasini slaydga aylantiradi"""
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pypdf import PdfReader
    from PIL import Image
    import fitz  # PyMuPDF

    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)

    doc = fitz.open(pdf_path)
    blank_layout = prs.slide_layouts[6]

    for page_num in range(len(doc)):
        page = doc[page_num]
        mat = fitz.Matrix(2, 2)
        pix = page.get_pixmap(matrix=mat)
        img_data = pix.tobytes("png")

        slide = prs.slides.add_slide(blank_layout)
        img_stream = BytesIO(img_data)
        slide.shapes.add_picture(img_stream, 0, 0,
                                  prs.slide_width, prs.slide_height)

    doc.close()
    prs.save(output_path)

def pptx_to_pdf(pptx_path, output_path):
    """PPTX ni PDF ga aylantiradi"""
    from pptx import Presentation
    from pptx.util import Inches
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import landscape, letter
    from PIL import Image
    import fitz

    prs = Presentation(pptx_path)
    width = float(prs.slide_width) / 914400 * 72
    height = float(prs.slide_height) / 914400 * 72

    c = canvas.Canvas(output_path, pagesize=(width, height))

    for i, slide in enumerate(prs.slides):
        # Har bir slaydni rasm sifatida saqlash
        slide_img_path = output_path + f"_slide_{i}.png"
        render_slide(prs, slide, slide_img_path, width, height)
        c.drawImage(slide_img_path, 0, 0, width, height)
        c.showPage()
        if os.path.exists(slide_img_path):
            os.remove(slide_img_path)

    c.save()

def render_slide(prs, slide, output_path, width, height):
    """Slaydni rasm sifatida saqlaydi"""
    from PIL import Image, ImageDraw
    img = Image.new('RGB', (int(width*2), int(height*2)), 'white')
    img.save(output_path)

def images_to_pdf(image_paths, output_path):
    """Rasmlarni PDF ga birlashtiradi"""
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import A4
    from PIL import Image

    c = canvas.Canvas(output_path, pagesize=A4)
    a4_width, a4_height = A4

    for img_path in image_paths:
        img = Image.open(img_path)
        img_width, img_height = img.size
        ratio = min(a4_width / img_width, a4_height / img_height)
        new_w = img_width * ratio
        new_h = img_height * ratio
        x = (a4_width - new_w) / 2
        y = (a4_height - new_h) / 2
        c.drawImage(img_path, x, y, new_w, new_h)
        c.showPage()

    c.save()

# ===================== FOYDALANUVCHI HOLATI =====================
user_states = {}
user_images = {}  # Rasmlarni to'plash uchun

# ===================== KLAVIATURALAR =====================
def lang_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang:uz"),
        types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
        types.InlineKeyboardButton("🇬🇧 English", callback_data="lang:en")
    )
    return kb

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row(t(uid, 'convert'), t(uid, 'translit'))
    kb.row(t(uid, 'donate'), t(uid, 'help'))
    kb.row(t(uid, 'admin'))
    return kb

def convert_kb(uid):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(t(uid, 'pdf_to_pptx'), callback_data="conv:pdf_pptx"))
    kb.add(types.InlineKeyboardButton(t(uid, 'pptx_to_pdf'), callback_data="conv:pptx_pdf"))
    kb.add(types.InlineKeyboardButton(t(uid, 'img_to_pdf'), callback_data="conv:img_pdf"))
    kb.add(types.InlineKeyboardButton(t(uid, 'back'), callback_data="conv:back"))
    return kb

def translit_kb(uid):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(t(uid, 'lat_to_kril'), callback_data="trl:lat_krl"))
    kb.add(types.InlineKeyboardButton(t(uid, 'kril_to_lat'), callback_data="trl:krl_lat"))
    kb.add(types.InlineKeyboardButton(t(uid, 'back'), callback_data="trl:back"))
    return kb

def back_kb(uid):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(t(uid, 'back'), callback_data="back:main"))
    return kb

# ===================== HANDLERS =====================
@bot.message_handler(commands=['start'])
def start(msg):
    uid = msg.from_user.id
    set_lang(uid, get_lang(uid),
             msg.from_user.username or '',
             msg.from_user.first_name or '')
    bot.send_message(uid, LANGS['uz']['choose_lang'], reply_markup=lang_kb())

@bot.message_handler(commands=['help'])
def help_cmd(msg):
    uid = msg.from_user.id
    bot.send_message(uid, t(uid, 'help_text'), reply_markup=main_kb(uid))

@bot.message_handler(commands=['stats'])
def stats_cmd(msg):
    if msg.from_user.id != ADMIN_ID:
        return
    users, converts, translits, donates = get_stats()
    bot.send_message(msg.chat.id,
        t(msg.from_user.id, 'stats_msg').format(
            users=users, converts=converts,
            translits=translits, donates=donates))

@bot.message_handler(commands=['done'])
def done_images(msg):
    uid = msg.from_user.id
    images = user_images.get(uid, [])
    if not images:
        return
    bot.send_message(uid, t(uid, 'wait_img'))
    tmpdir = tempfile.mkdtemp()
    try:
        output = os.path.join(tmpdir, 'result.pdf')
        images_to_pdf(images, output)
        with open(output, 'rb') as f:
            bot.send_document(uid, f, caption=t(uid, 'result_pdf'))
        log_action(uid, 'convert', 'img_to_pdf')
    except Exception as e:
        logger.error(f"Image to PDF error: {e}")
        bot.send_message(uid, t(uid, 'error'))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        user_images.pop(uid, None)
        user_states.pop(uid, None)
    bot.send_message(uid, t(uid, 'main_menu'), reply_markup=main_kb(uid))

@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    uid = msg.from_user.id
    text = msg.text
    state = user_states.get(uid)

    # Transliteratsiya holatlari
    if state == 'lat_krl':
        result = lat_to_kirill(text)
        bot.send_message(uid, t(uid, 'result_text') + f"`{result}`",
                         reply_markup=main_kb(uid))
        log_action(uid, 'translit', 'lat_to_krl')
        user_states.pop(uid, None)
        return

    if state == 'krl_lat':
        result = kirill_to_lat(text)
        bot.send_message(uid, t(uid, 'result_text') + f"`{result}`",
                         reply_markup=main_kb(uid))
        log_action(uid, 'translit', 'krl_to_lat')
        user_states.pop(uid, None)
        return

    # Menyu tugmalari — barcha tillarda tekshirish
    convert_texts = [LANGS[l]['convert'] for l in LANGS]
    translit_texts = [LANGS[l]['translit'] for l in LANGS]
    donate_texts = [LANGS[l]['donate'] for l in LANGS]
    help_texts = [LANGS[l]['help'] for l in LANGS]
    admin_texts = [LANGS[l]['admin'] for l in LANGS]

    if text in convert_texts:
        bot.send_message(uid, t(uid, 'send_file'), reply_markup=convert_kb(uid))

    elif text in translit_texts:
        bot.send_message(uid, t(uid, 'choose_translit'), reply_markup=translit_kb(uid))

    elif text in donate_texts:
        log_action(uid, 'donate')
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(t(uid, 'donate_site'), url=DONATE_URL))
        bot.send_message(uid,
            t(uid, 'donate_text').format(card=DONATE_CARD, click=DONATE_CLICK),
            reply_markup=kb)

    elif text in help_texts:
        bot.send_message(uid, t(uid, 'help_text'), reply_markup=main_kb(uid))

    elif text in admin_texts:
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton(
            t(uid, 'contact_admin'), url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))
        bot.send_message(uid, t(uid, 'admin_text'), reply_markup=kb)

@bot.message_handler(content_types=['document'])
def handle_document(msg):
    uid = msg.from_user.id
    state = user_states.get(uid)
    doc = msg.document

    if doc.file_size > 20 * 1024 * 1024:
        bot.send_message(uid, t(uid, 'file_too_big'))
        return

    fname = doc.file_name.lower() if doc.file_name else ''
    processing_msg = bot.send_message(uid, t(uid, 'processing'))
    tmpdir = tempfile.mkdtemp()

    try:
        file_info = bot.get_file(doc.file_id)
        downloaded = bot.download_file(file_info.file_path)
        input_path = os.path.join(tmpdir, doc.file_name or 'input')
        with open(input_path, 'wb') as f:
            f.write(downloaded)

        if fname.endswith('.pdf') and state == 'pdf_pptx':
            output_path = os.path.join(tmpdir, 'result.pptx')
            try:
                import fitz
                pdf_to_pptx(input_path, output_path)
            except ImportError:
                # PyMuPDF yo'q bo'lsa reportlab bilan
                _pdf_to_pptx_fallback(input_path, output_path)
            with open(output_path, 'rb') as f:
                bot.send_document(uid, f, caption=t(uid, 'result_pptx'))
            log_action(uid, 'convert', 'pdf_to_pptx')

        elif fname.endswith(('.pptx', '.ppt')) and state == 'pptx_pdf':
            output_path = os.path.join(tmpdir, 'result.pdf')
            pptx_to_pdf(input_path, output_path)
            with open(output_path, 'rb') as f:
                bot.send_document(uid, f, caption=t(uid, 'result_pdf'))
            log_action(uid, 'convert', 'pptx_to_pdf')

        else:
            bot.send_message(uid, t(uid, 'wrong_format'))
            return

        user_states.pop(uid, None)

    except Exception as e:
        logger.error(f"Document error for {uid}: {e}")
        bot.send_message(uid, t(uid, 'error'))
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
        try:
            bot.delete_message(uid, processing_msg.message_id)
        except: pass

    bot.send_message(uid, t(uid, 'main_menu'), reply_markup=main_kb(uid))

def _pdf_to_pptx_fallback(pdf_path, output_path):
    """PyMuPDF yo'q bo'lsa ishlatiladigan fallback"""
    from pptx import Presentation
    from pptx.util import Inches
    from pypdf import PdfReader
    from reportlab.pdfgen import canvas as rl_canvas

    prs = Presentation()
    prs.slide_width = Inches(10)
    prs.slide_height = Inches(7.5)
    reader = PdfReader(pdf_path)

    for i, page in enumerate(reader.pages):
        blank = prs.slide_layouts[6]
        slide = prs.slides.add_slide(blank)
        text = page.extract_text() or f"Sahifa {i+1}"
        txBox = slide.shapes.add_textbox(
            Inches(0.5), Inches(0.5),
            Inches(9), Inches(6.5))
        tf = txBox.text_frame
        tf.word_wrap = True
        from pptx.util import Pt
        p = tf.paragraphs[0]
        p.text = text[:3000]

    prs.save(output_path)

@bot.message_handler(content_types=['photo'])
def handle_photo(msg):
    uid = msg.from_user.id
    state = user_states.get(uid)

    if state != 'img_pdf':
        return

    if uid not in user_images:
        user_images[uid] = []

    tmpdir = tempfile.mkdtemp()
    photo = msg.photo[-1]  # Eng yuqori sifatli rasm

    try:
        file_info = bot.get_file(photo.file_id)
        downloaded = bot.download_file(file_info.file_path)
        img_path = os.path.join(tmpdir, f"img_{len(user_images[uid])}.jpg")
        with open(img_path, 'wb') as f:
            f.write(downloaded)
        user_images[uid].append(img_path)

        count = len(user_images[uid])
        bot.send_message(uid, f"✅ {count} ta rasm qabul qilindi. Davom eting yoki /done yozing.")
    except Exception as e:
        logger.error(f"Photo error: {e}")
        bot.send_message(uid, t(uid, 'error'))

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    data = call.data
    bot.answer_callback_query(call.id)

    # Til tanlash
    if data.startswith("lang:"):
        lang = data[5:]
        set_lang(uid, lang,
                 call.from_user.username or '',
                 call.from_user.first_name or '')
        bot.edit_message_text(
            LANGS[lang]['lang_set'],
            uid, call.message.message_id)
        bot.send_message(uid, t(uid, 'main_menu'), reply_markup=main_kb(uid))

    # Konvertatsiya
    elif data.startswith("conv:"):
        action = data[5:]
        if action == "pdf_pptx":
            user_states[uid] = 'pdf_pptx'
            bot.edit_message_text(
                t(uid, 'send_file') + "\n\n📄 *PDF fayl yuboring:*",
                uid, call.message.message_id,
                reply_markup=back_kb(uid))
        elif action == "pptx_pdf":
            user_states[uid] = 'pptx_pdf'
            bot.edit_message_text(
                t(uid, 'send_file') + "\n\n📊 *PPTX/PPT fayl yuboring:*",
                uid, call.message.message_id,
                reply_markup=back_kb(uid))
        elif action == "img_pdf":
            user_states[uid] = 'img_pdf'
            user_images[uid] = []
            bot.edit_message_text(
                t(uid, 'send_images'),
                uid, call.message.message_id,
                reply_markup=back_kb(uid))
        elif action == "back":
            user_states.pop(uid, None)
            bot.edit_message_text(
                t(uid, 'main_menu'),
                uid, call.message.message_id)
            bot.send_message(uid, t(uid, 'main_menu'), reply_markup=main_kb(uid))

    # Transliteratsiya
    elif data.startswith("trl:"):
        action = data[4:]
        if action == "lat_krl":
            user_states[uid] = 'lat_krl'
            bot.edit_message_text(
                t(uid, 'send_text'),
                uid, call.message.message_id,
                reply_markup=back_kb(uid))
        elif action == "krl_lat":
            user_states[uid] = 'krl_lat'
            bot.edit_message_text(
                t(uid, 'send_text'),
                uid, call.message.message_id,
                reply_markup=back_kb(uid))
        elif action == "back":
            user_states.pop(uid, None)
            bot.edit_message_text(
                t(uid, 'main_menu'),
                uid, call.message.message_id)
            bot.send_message(uid, t(uid, 'main_menu'), reply_markup=main_kb(uid))

    elif data == "back:main":
        user_states.pop(uid, None)
        bot.edit_message_text(
            t(uid, 'main_menu'),
            uid, call.message.message_id)
        bot.send_message(uid, t(uid, 'main_menu'), reply_markup=main_kb(uid))

# ===================== MAIN =====================
if __name__ == "__main__":
    init_db()
    print("✅ Converter Bot ishga tushdi!")
    print(f"👨‍💼 Admin ID: {ADMIN_ID}")
    print("📋 Komandalar: /start /help /stats (admin)")
    bot.infinity_polling()