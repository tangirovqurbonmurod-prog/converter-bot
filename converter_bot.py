import telebot, os, sqlite3, logging, tempfile, shutil, requests
from telebot import types
from datetime import datetime

BOT_TOKEN = os.environ.get("BOT_TOKEN", "8270798642:AAGtdwHVgu0rKCwTU5x9eLLWWYGoWhG-j6I")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "1113404703"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "@abdurakhmon02")
MINI_APP_URL = os.environ.get("MINI_APP_URL", "https://t.me/your_bot/app")  # Mini App URL ni shu yerga kiriting
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")

PRICE_PAGE     = int(os.environ.get("PRICE_PAGE",     "500"))   # Referat
PRICE_KURS     = int(os.environ.get("PRICE_KURS",     "700"))   # Kurs ishi
PRICE_MUSTAQIL = int(os.environ.get("PRICE_MUSTAQIL", "400"))   # Mustaqil ish
PRICE_MAQOLA   = int(os.environ.get("PRICE_MAQOLA",   "600"))   # Maqola
PRICE_SLIDE    = int(os.environ.get("PRICE_SLIDE",    "300"))   # Prezentatsiya
PRICE_TEST     = int(os.environ.get("PRICE_TEST",     "200"))   # Test

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
bot = telebot.TeleBot(BOT_TOKEN)

LN = {"uz": "o'zbek", "ru": "rus", "en": "ingliz"}

# ===== DATABASE =====
def init_db():
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY, username TEXT,
        first_name TEXT, lang TEXT DEFAULT 'uz', joined_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER,
        action TEXT, detail TEXT, income INTEGER DEFAULT 0, created_at TEXT)""")
    conn.commit(); conn.close()

def get_lang(uid):
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("SELECT lang FROM users WHERE telegram_id=?", (uid,))
    row = c.fetchone(); conn.close()
    return row[0] if row else "uz"

def set_lang(uid, lang, uname="", fname=""):
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("""INSERT INTO users (telegram_id,username,first_name,lang,joined_at)
        VALUES (?,?,?,?,?) ON CONFLICT(telegram_id) DO UPDATE SET lang=?""",
        (uid, uname, fname, lang, datetime.now().strftime("%d.%m.%Y %H:%M"), lang))
    conn.commit(); conn.close()

def log_act(uid, action, detail="", income=0):
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("INSERT INTO stats (telegram_id,action,detail,income,created_at) VALUES (?,?,?,?,?)",
        (uid, action, detail, income, datetime.now().strftime("%d.%m.%Y %H:%M")))
    conn.commit(); conn.close()

def all_users():
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users")
    rows = c.fetchall(); conn.close()
    return [r[0] for r in rows]

def get_stats():
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("SELECT COUNT(DISTINCT telegram_id) FROM users"); u = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM stats WHERE action IN ('referat','kurs','mustaqil','maqola','prez','test')"); w = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM stats WHERE action='conv'"); cv = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(income),0) FROM stats"); i = c.fetchone()[0]
    conn.close(); return u, w, cv, i

# ===== CLAUDE AI =====
def claude(prompt, system="", max_tok=4000):
    if not CLAUDE_API_KEY: return "Claude API kaliti sozlanmagan!"
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01", "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": max_tok,
                  "system": system, "messages": [{"role": "user", "content": prompt}]}, timeout=90)
        if r.status_code == 200: return r.json()["content"][0]["text"]
        return f"API xatosi: {r.status_code}"
    except Exception as e: return f"Xatolik: {e}"

def gen_referat(topic, pages, lang):
    ln = LN.get(lang, "o'zbek")
    return claude(
        f"Mavzu: {topic}\nHajm: {pages} bet (~300 so'z/bet)\n\n"
        f"{ln} tilida to'liq akademik referat yozing:\n"
        "**KIRISH**\n(Mavzuning dolzarbligi, tadqiqot maqsadi)\n"
        "**ASOSIY QISM 1: [sarlavha]**\n(Mazmun)\n"
        "**ASOSIY QISM 2: [sarlavha]**\n(Mazmun)\n"
        "**ASOSIY QISM 3: [sarlavha]**\n(Mazmun)\n"
        "**XULOSA**\n(Asosiy xulosalar)\n"
        "**FOYDALANILGAN ADABIYOTLAR**\n(5-7 ta manba)",
        f"Siz professional {ln} tilida ilmiy referat yozuvchi mutaxasssissiz. "
        "Akademik uslub, aniq faktlar, imlo xatosiz, to'liq hajmda yozing.",
        min(pages * 350, 4000))

def gen_kurs(topic, pages, lang):
    ln = LN.get(lang, "o'zbek")
    return claude(
        f"Mavzu: {topic}\nHajm: {pages} bet\n\n"
        f"{ln} tilida professional kurs ishi yozing:\n"
        "**MUNDARIJA**\n"
        "**KIRISH**\n(Dolzarblik, maqsad, vazifalar, ob'ekt, predmet, metodlar)\n"
        "**I BOB: Nazariy asoslar**\n1.1. ...\n1.2. ...\n"
        "**II BOB: Tahlil va natijalar**\n2.1. ...\n2.2. ...\n"
        "**III BOB: Tavsiyalar**\n"
        "**XULOSA**\n"
        "**FOYDALANILGAN ADABIYOTLAR**\n(10-15 ta manba)\n"
        "**ILOVALAR**",
        f"Siz professional {ln} tilida kurs ishi yozuvchi olim mutaxasssissiz. "
        "Ilmiy uslub, jadvallar va tahlillar bilan, to'liq va sifatli yozing.",
        min(pages * 400, 4000))

def gen_mustaqil(topic, pages, lang):
    ln = LN.get(lang, "o'zbek")
    return claude(
        f"Mavzu: {topic}\nHajm: {pages} bet\n\n"
        f"{ln} tilida mustaqil ish yozing:\n"
        "**KIRISH**\n(Maqsad va vazifalar)\n"
        "**MAVZUNING NAZARIY ASOSLARI**\n"
        "**ASOSIY TAHLIL**\n(Misollar, jadvallar, taqqoslash)\n"
        "**XULOSALAR**\n"
        "**ADABIYOTLAR**\n(5-8 ta manba)",
        f"Siz professional {ln} tilida mustaqil ish yozuvchi mutaxasssissiz. "
        "Aniq, qisqa, lekin to'liq va sifatli yozing.",
        min(pages * 320, 4000))

def gen_maqola(topic, pages, lang):
    ln = LN.get(lang, "o'zbek")
    return claude(
        f"Mavzu: {topic}\nHajm: {pages} bet\n\n"
        f"{ln} tilida ilmiy maqola yozing (VAK talablariga mos):\n"
        "**ANNOTATSIYA** (3-5 jumla)\n"
        "**KALIT SO'ZLAR** (5-7 ta)\n"
        "**ABSTRACT** (ingliz tilida, 3-5 jumla)\n"
        "**KEYWORDS** (ingliz tilida)\n"
        "**KIRISH**\n(Muammoning dolzarbligi)\n"
        "**ADABIYOTLAR TAHLILI**\n"
        "**TADQIQOT METODOLOGIYASI**\n"
        "**NATIJALAR VA MUHOKAMA**\n"
        "**XULOSA**\n"
        "**ADABIYOTLAR** (APA 7 formatida, 10-15 ta)",
        f"Siz {ln} tilida VAK ilmiy jurnallari uchun maqola yozuvchi professor. "
        "Ilmiy uslub, annotatsiya va adabiyotlar bilan professional yozing.",
        min(pages * 380, 4000))

def gen_prez(topic, slides, style, lang):
    ln = LN.get(lang, "o'zbek")
    style_tips = {
        "klassik": "professional va rasmiy",
        "zamonaviy": "zamonaviy va dinamik",
        "minimalist": "sodda va toza",
        "biznes": "biznes va korporativ"
    }
    tip = style_tips.get(style, "professional")
    return claude(
        f"Mavzu: {topic}\nSlaydlar soni: {slides}\nUslub: {tip}\n\n"
        f"{ln} tilida {slides} ta slayd mazmunini yozing.\n"
        f"Har bir slayd uchun:\nSLAYD N: [Aniq va qisqa sarlavha]\n"
        "* [Asosiy fikr 1 - 1-2 jumla]\n"
        "* [Asosiy fikr 2 - 1-2 jumla]\n"
        "* [Asosiy fikr 3 - 1-2 jumla]\n\n"
        "1-slayd: Sarlavha slayd (mavzu, muallif, sana)\n"
        f"2-slayd: Mundarija ({slides} ta bo'lim)\n"
        "Oxirgi slayd: Xulosa va savollar\n"
        "Har bir slaydda 3-5 ta asosiy fikr bo'lsin.",
        f"Professional prezentatsiya dizayner va notiq. {ln} tilida aniq, ta'sirli yozing.",
        min(slides * 150, 4000))

def gen_test(topic, count, lang):
    ln = LN.get(lang, "o'zbek")
    return claude(
        f"Mavzu: {topic}\nSavollar soni: {count}\n\n"
        f"{ln} tilida {count} ta professional test savoli:\n"
        "FORMAT:\nN. [Aniq va tushunarli savol]\n"
        "A) [Javob varianti]\n"
        "B) [Javob varianti]\n"
        "C) [Javob varianti]\n"
        "D) [Javob varianti]\n"
        "To'g'ri javob: [harf]\n\n"
        "Savollar 3 darajada bo'lsin:\n"
        f"- {count//3} ta oson (bilim)\n"
        f"- {count//3} ta o'rta (tushunish)\n"
        f"- {count - 2*(count//3)} ta qiyin (tahlil)",
        f"Professional {ln} tili o'qituvchisi va test yaratuvchi.",
        min(count * 85, 4000))

def fix_imlo(text, lang):
    ln = LN.get(lang, "o'zbek")
    return claude(
        f"Quyidagi matnni {ln} tilining rasmiy imlo qoidalariga to'liq muvofiq qilib tuzat.\n"
        "MUHIM: Faqat tuzatilgan matnni qaytар, hech qanday izoh yozma:\n\n"
        f"{text[:2500]}",
        f"Siz {ln} tili grammatika va imlo bo'yicha oliy darajali mutaxassis.", 3500)

# ===== PPTX YARATISH =====
def make_pptx(content, topic, style="klassik"):
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor

        THEMES = {
            "klassik":    {"bg": RGBColor(255,255,255), "title": RGBColor(31,73,125),  "text": RGBColor(30,30,30),   "accent": RGBColor(31,73,125)},
            "zamonaviy":  {"bg": RGBColor(10,10,30),    "title": RGBColor(0,200,200),   "text": RGBColor(220,230,255),"accent": RGBColor(0,200,200)},
            "minimalist": {"bg": RGBColor(248,248,248),  "title": RGBColor(40,40,40),   "text": RGBColor(70,70,70),   "accent": RGBColor(180,180,180)},
            "biznes":     {"bg": RGBColor(0,40,80),      "title": RGBColor(255,200,0),  "text": RGBColor(255,255,255),"accent": RGBColor(255,200,0)},
        }
        th = THEMES.get(style, THEMES["klassik"])

        prs = Presentation()
        prs.slide_width  = Inches(13.33)
        prs.slide_height = Inches(7.5)
        blank = prs.slide_layouts[6]

        slides_data = []
        cur_t, cur_b = topic, []

        for line in content.strip().split("\n"):
            line = line.strip()
            if not line: continue
            ul = line.upper()
            is_slide = any(ul.startswith(x) for x in ("SLAYD","СЛАЙД","SLIDE")) and ":" in line
            if is_slide:
                if cur_t: slides_data.append((cur_t, cur_b[:]))
                cur_t = line.split(":",1)[1].strip(); cur_b = []
            elif line.startswith(("*","•","-","–")):
                cur_b.append(line.lstrip("*•-– ").strip())
            elif cur_t and line and not line.startswith(("A)","B)","C)","D)")):
                cur_b.append(line)

        if cur_t: slides_data.append((cur_t, cur_b))
        if not slides_data: slides_data = [(topic, content.split("\n")[:6])]

        for title, bullets in slides_data:
            sl = prs.slides.add_slide(blank)
            sl.background.fill.solid()
            sl.background.fill.fore_color.rgb = th["bg"]

            # Sarlavha
            tb = sl.shapes.add_textbox(Inches(.4), Inches(.25), Inches(12.5), Inches(1.5))
            tf = tb.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title[:90]; p.font.size = Pt(32); p.font.bold = True
            p.font.color.rgb = th["title"]

            # Chiziq
            ac = sl.shapes.add_shape(1, Inches(.4), Inches(1.78), Inches(12.5), Inches(.07))
            ac.fill.solid(); ac.fill.fore_color.rgb = th["accent"]; ac.line.fill.background()

            # Mazmun
            if bullets:
                cb = sl.shapes.add_textbox(Inches(.4), Inches(1.95), Inches(12.5), Inches(5.3))
                tf2 = cb.text_frame; tf2.word_wrap = True
                for i, b in enumerate(bullets[:9]):
                    p2 = tf2.paragraphs[0] if i == 0 else tf2.add_paragraph()
                    p2.text = f"▸  {b}"
                    p2.font.size = Pt(21); p2.font.color.rgb = th["text"]; p2.space_before = Pt(6)

        td = tempfile.mkdtemp()
        out = os.path.join(td, "prezentatsiya.pptx")
        prs.save(out); return out, td
    except Exception as e:
        logger.error(f"PPTX: {e}"); return None, None

# ===== KONVERTATSIYA =====
def pdf2pptx(pdf, out):
    try:
        import fitz
        from pptx import Presentation
        from pptx.util import Inches
        from io import BytesIO
        prs = Presentation()
        prs.slide_width = Inches(10); prs.slide_height = Inches(7.5)
        doc = fitz.open(pdf)
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
            sl = prs.slides.add_slide(prs.slide_layouts[6])
            sl.shapes.add_picture(BytesIO(pix.tobytes("png")), 0, 0, prs.slide_width, prs.slide_height)
        doc.close(); prs.save(out); return True
    except Exception as e: logger.error(f"pdf2pptx: {e}"); return False

def pptx2pdf(pptx, out):
    try:
        from pptx import Presentation
        from reportlab.pdfgen import canvas
        from PIL import Image
        prs = Presentation(pptx)
        w = float(prs.slide_width)/914400*72; h = float(prs.slide_height)/914400*72
        c = canvas.Canvas(out, pagesize=(w,h))
        for i in range(len(prs.slides)):
            img = Image.new("RGB", (int(w*2),int(h*2)), "white")
            td = tempfile.mkdtemp(); tp = os.path.join(td,f"s{i}.png")
            img.save(tp); c.drawImage(tp,0,0,w,h); c.showPage(); shutil.rmtree(td)
        c.save(); return True
    except Exception as e: logger.error(f"pptx2pdf: {e}"); return False

def imgs2pdf(imgs, out):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from PIL import Image
        c = canvas.Canvas(out, pagesize=A4); aw,ah = A4
        for p in imgs:
            img = Image.open(p); iw,ih = img.size; r = min(aw/iw, ah/ih)
            nw,nh = iw*r, ih*r; c.drawImage(p,(aw-nw)/2,(ah-nh)/2,nw,nh); c.showPage()
        c.save(); return True
    except Exception as e: logger.error(f"imgs2pdf: {e}"); return False

# ===== TRANSLITERATSIYA =====
L2K = {"o'":"ў","O'":"Ў","g'":"ғ","G'":"Ғ","sh":"ш","Sh":"Ш","ch":"ч","Ch":"Ч","ng":"нг",
 "a":"а","A":"А","b":"б","B":"Б","d":"д","D":"Д","e":"е","E":"Е","f":"ф","F":"Ф",
 "g":"г","G":"Г","h":"ҳ","H":"Ҳ","i":"и","I":"И","j":"ж","J":"Ж","k":"к","K":"К",
 "l":"л","L":"Л","m":"м","M":"М","n":"н","N":"Н","o":"о","O":"О","p":"п","P":"П",
 "q":"қ","Q":"Қ","r":"р","R":"Р","s":"с","S":"С","t":"т","T":"Т","u":"у","U":"У",
 "v":"в","V":"В","x":"х","X":"Х","y":"й","Y":"Й","z":"з","Z":"З"}
K2L = {"ў":"o'","Ў":"O'","ғ":"g'","Ғ":"G'","ш":"sh","Ш":"Sh","ч":"ch","Ч":"Ch","нг":"ng",
 "а":"a","А":"A","б":"b","Б":"B","д":"d","Д":"D","е":"e","Е":"E","ф":"f","Ф":"F",
 "г":"g","Г":"G","ҳ":"h","Ҳ":"H","и":"i","И":"I","й":"y","Й":"Y","ж":"j","Ж":"J",
 "к":"k","К":"K","қ":"q","Қ":"Q","л":"l","Л":"L","м":"m","М":"M","н":"n","Н":"N",
 "о":"o","О":"O","п":"p","П":"P","р":"r","Р":"R","с":"s","С":"S","т":"t","Т":"T",
 "у":"u","У":"U","в":"v","В":"V","х":"x","Х":"X","з":"z","З":"Z",
 "я":"ya","Я":"Ya","ю":"yu","Ю":"Yu","ё":"yo","Ё":"Yo","э":"e","Э":"E","ъ":"","ь":"","ц":"ts","щ":"sh"}

def l2k(t):
    r=t
    for k,v in sorted(L2K.items(), key=lambda x: -len(x[0])): r=r.replace(k,v)
    return r

def k2l(t):
    r,i="",0
    while i<len(t):
        two=t[i:i+2]
        if two in K2L: r+=K2L[two]; i+=2
        elif t[i] in K2L: r+=K2L[t[i]]; i+=1
        else: r+=t[i]; i+=1
    return r

# ===== HOLAT BOSHQARUVI =====
ST, UD, UI = {}, {}, {}
def sst(uid, s, **kw): ST[uid]=s; UD.setdefault(uid,{}).update(kw)
def gst(uid): return ST.get(uid)
def cst(uid): ST.pop(uid, None)

# ===== TILLAR =====
def tx(uid, key, **kw):
    lang = get_lang(uid)
    msgs = {
        "uz": {
            "welcome": "Salom! *EduBot*ga xush kelibsiz!\n\nTilni tanlang:",
            "main_menu": "Asosiy menyu. Bo'lim tanlang:",
            "ai_btn": "AI Yordamchi",
            "conv_btn": "Konvertatsiya",
            "tools_btn": "Qo'shimcha",
            "donate_btn": "Donat",
            "help_btn": "Yordam",
            "admin_btn": "Admin",
            "ai_menu": "*AI Yordamchi*\nXizmat tanlang:",
            "btn_referat": "Referat",
            "btn_kurs": "Kurs ishi",
            "btn_mustaqil": "Mustaqil ish",
            "btn_maqola": "Maqola",
            "btn_prez": "Prezentatsiya",
            "btn_test": "Test yaratish",
            "btn_imlo": "Imlo tuzatish",
            "ask_topic": "Mavzuni kiriting:",
            "ask_pages": "Necha bet? (5-50)\n1 bet = {price} so'm",
            "ask_slides": "Necha slayd? (5-30)\n1 slayd = {price} so'm",
            "ask_count": "Nechta savol? (5-50)\n1 savol = {price} so'm",
            "ask_lang": "Qaysi tilda yozilsin?",
            "ask_style": "Prezentatsiya uslubi:",
            "processing": "Tayyorlanmoqda... ({total} so'm)\nSabr qiling!",
            "processing2": "Ishlanmoqda...",
            "done_text": "Tayyor!\nMavzu: {topic}\n{pages} bet | {total} so'm",
            "done_prez": "Tayyor!\n{topic}\n{slides} slayd",
            "done_test": "{count} ta savol tayyor!",
            "imlo_ask": "Matn yoki fayl yuboring (PDF/TXT):",
            "imlo_done": "*Tuzatildi:*\n\n{text}",
            "conv_menu": "*Konvertatsiya*",
            "btn_pdf_pptx": "PDF to PPTX",
            "btn_pptx_pdf": "PPTX to PDF",
            "btn_img_pdf": "Rasmlar to PDF",
            "send_pdf": "PDF fayl yuboring:",
            "send_pptx": "PPTX/PPT fayl yuboring:",
            "send_imgs": "Rasmlar yuboring. Tugagach /done:",
            "imgs_got": "{n} ta rasm qabul qilindi. /done yozing.",
            "res_pdf": "PDF fayl!", "res_pptx": "PPTX fayl!",
            "tools_menu": "*Qo'shimcha*",
            "btn_l2k": "Lotin to Kirill",
            "btn_k2l": "Kirill to Lotin",
            "send_text": "Matn yuboring:",
            "res_text": "Natija:\n\n",
            "donate_text": "*Donat*\n\nKarta: `{card}`\nClick: `{click}`",
            "donate_site": "Donat saytiga o'tish",
            "help_text": "*Narxlar:*\nReferat: {pp} so'm/bet\nKurs ishi: {kp} so'm/bet\nMustaqil ish: {mp2} so'm/bet\nMaqola: {mp} so'm/bet\nPrezentatsiya: {sp} so'm/slayd\nTest: {tp} so'm/savol",
            "admin_text": "*Admin*",
            "contact": "Adminga yozish",
            "bc_ask": "Xabar matnini yozing:",
            "bc_done": "{count} ta foydalanuvchiga yuborildi!",
            "stats": "*Statistika*\n\nFoydalanuvchilar: {u}\nIshlar: {w}\nKonvertatsiyalar: {c}\nDaromad: {i} so'm",
            "lang_set": "Til o'rnatildi!",
            "error": "Xatolik yuz berdi.",
            "wrong_fmt": "Noto'g'ri format.",
            "too_big": "Fayl juda katta (max 20MB)",
            "back": "Orqaga",
            "styles": {"klassik": "Klassik", "zamonaviy": "Zamonaviy", "minimalist": "Minimalist", "biznes": "Biznes"},
        },
        "ru": {
            "welcome": "Добро пожаловать в *EduBot*!\n\nВыберите язык:",
            "main_menu": "Главное меню:",
            "ai_btn": "AI Помощник",
            "conv_btn": "Конвертация",
            "tools_btn": "Инструменты",
            "donate_btn": "Донат",
            "help_btn": "Помощь",
            "admin_btn": "Админ",
            "ai_menu": "*AI Помощник*\nВыберите услугу:",
            "btn_referat": "Реферат",
            "btn_kurs": "Курсовая",
            "btn_mustaqil": "Самост. работа",
            "btn_maqola": "Статья",
            "btn_prez": "Презентация",
            "btn_test": "Создать тест",
            "btn_imlo": "Орфография",
            "ask_topic": "Введите тему:",
            "ask_pages": "Сколько страниц? (5-50)\n1 стр = {price} сум",
            "ask_slides": "Сколько слайдов? (5-30)\n1 слайд = {price} сум",
            "ask_count": "Сколько вопросов? (5-50)\n1 вопрос = {price} сум",
            "ask_lang": "На каком языке?",
            "ask_style": "Стиль презентации:",
            "processing": "Готовлю... ({total} сум)\nПодождите!",
            "processing2": "Обрабатываю...",
            "done_text": "Готово!\nТема: {topic}\n{pages} стр | {total} сум",
            "done_prez": "Готово!\n{topic}\n{slides} слайдов",
            "done_test": "{count} вопросов готово!",
            "imlo_ask": "Отправьте текст или файл (PDF/TXT):",
            "imlo_done": "*Исправлено:*\n\n{text}",
            "conv_menu": "*Конвертация*",
            "btn_pdf_pptx": "PDF в PPTX",
            "btn_pptx_pdf": "PPTX в PDF",
            "btn_img_pdf": "Фото в PDF",
            "send_pdf": "Отправьте PDF:",
            "send_pptx": "Отправьте PPTX/PPT:",
            "send_imgs": "Отправьте фото. Когда закончите — /done:",
            "imgs_got": "{n} фото получено. Напишите /done.",
            "res_pdf": "Вот PDF!", "res_pptx": "Вот PPTX!",
            "tools_menu": "*Инструменты*",
            "btn_l2k": "Латиница в Кириллицу",
            "btn_k2l": "Кириллица в Латиницу",
            "send_text": "Введите текст:",
            "res_text": "Результат:\n\n",
            "donate_text": "*Донат*\n\nКарта: `{card}`\nClick: `{click}`",
            "donate_site": "Сайт доната",
            "help_text": "*Цены:*\nРеферат: {pp} сум/стр\nКурсовая: {kp} сум/стр\nСамост. работа: {mp2} сум/стр\nСтатья: {mp} сум/стр\nПрезентация: {sp} сум/слайд\nТест: {tp} сум/вопрос",
            "admin_text": "*Админ*",
            "contact": "Написать",
            "bc_ask": "Введите текст рассылки:",
            "bc_done": "Отправлено {count} пользователям!",
            "stats": "*Статистика*\n\nПользователи: {u}\nРаботы: {w}\nКонвертации: {c}\nДоход: {i} сум",
            "lang_set": "Язык установлен!",
            "error": "Произошла ошибка.",
            "wrong_fmt": "Неверный формат.",
            "too_big": "Файл слишком большой (макс 20МБ)",
            "back": "Назад",
            "styles": {"klassik": "Классический", "zamonaviy": "Современный", "minimalist": "Минималист", "biznes": "Бизнес"},
        },
        "en": {
            "welcome": "Welcome to *EduBot*!\n\nChoose language:",
            "main_menu": "Main menu:",
            "ai_btn": "AI Assistant",
            "conv_btn": "Conversion",
            "tools_btn": "Tools",
            "donate_btn": "Donate",
            "help_btn": "Help",
            "admin_btn": "Admin",
            "ai_menu": "*AI Assistant*\nChoose service:",
            "btn_referat": "Essay",
            "btn_kurs": "Coursework",
            "btn_mustaqil": "Independent work",
            "btn_maqola": "Article",
            "btn_prez": "Presentation",
            "btn_test": "Create Test",
            "btn_imlo": "Spell Check",
            "ask_topic": "Enter topic:",
            "ask_pages": "How many pages? (5-50)\n1 page = {price} sum",
            "ask_slides": "How many slides? (5-30)\n1 slide = {price} sum",
            "ask_count": "How many questions? (5-50)\n1 question = {price} sum",
            "ask_lang": "Which language?",
            "ask_style": "Presentation style:",
            "processing": "Preparing... ({total} sum)\nPlease wait!",
            "processing2": "Processing...",
            "done_text": "Done!\nTopic: {topic}\n{pages} pages | {total} sum",
            "done_prez": "Done!\n{topic}\n{slides} slides",
            "done_test": "{count} questions ready!",
            "imlo_ask": "Send text or file (PDF/TXT):",
            "imlo_done": "*Fixed:*\n\n{text}",
            "conv_menu": "*Conversion*",
            "btn_pdf_pptx": "PDF to PPTX",
            "btn_pptx_pdf": "PPTX to PDF",
            "btn_img_pdf": "Images to PDF",
            "send_pdf": "Send PDF:",
            "send_pptx": "Send PPTX/PPT:",
            "send_imgs": "Send images. Type /done when done:",
            "imgs_got": "{n} images received. Type /done.",
            "res_pdf": "Here's PDF!", "res_pptx": "Here's PPTX!",
            "tools_menu": "*Tools*",
            "btn_l2k": "Latin to Cyrillic",
            "btn_k2l": "Cyrillic to Latin",
            "send_text": "Enter text:",
            "res_text": "Result:\n\n",
            "donate_text": "*Donate*\n\nCard: `{card}`\nClick: `{click}`",
            "donate_site": "Donate site",
            "help_text": "*Prices:*\nEssay: {pp} sum/page\nCoursework: {kp} sum/page\nIndep. work: {mp2} sum/page\nArticle: {mp} sum/page\nPresentation: {sp} sum/slide\nTest: {tp} sum/q",
            "admin_text": "*Admin*",
            "contact": "Message Admin",
            "bc_ask": "Enter broadcast text:",
            "bc_done": "Sent to {count} users!",
            "stats": "*Statistics*\n\nUsers: {u}\nWorks: {w}\nConversions: {c}\nIncome: {i} sum",
            "lang_set": "Language set!",
            "error": "An error occurred.",
            "wrong_fmt": "Wrong format.",
            "too_big": "File too large (max 20MB)",
            "back": "Back",
            "styles": {"klassik": "Classic", "zamonaviy": "Modern", "minimalist": "Minimalist", "biznes": "Business"},
        },
    }
    text = msgs.get(lang, msgs["uz"]).get(key, key)
    if kw:
        try: text = text.format(**kw)
        except: pass
    return text

# ===== KLAVIATURALAR =====
def lang_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(types.InlineKeyboardButton("O'zbek", callback_data="lang:uz"),
           types.InlineKeyboardButton("Русский", callback_data="lang:ru"),
           types.InlineKeyboardButton("English", callback_data="lang:en"))
    return kb

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=2)
    kb.row("📄 Referat", "📝 Kurs ishi")
    kb.row("📋 Mustaqil ish", "📰 Maqola")
    kb.row("📊 Prezentatsiya", "✅ Test")
    kb.row("✏️ Imlo tuzatish", "🔄 Konvertatsiya")
    kb.row("🛠 Qo\'shimcha", "🌐 Mini App")
    kb.row("❓ Yordam", "👨\u200d💼 Admin")
    return kb

def ai_kb(uid):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_referat"), callback_data="ai:referat"))
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_kurs"), callback_data="ai:kurs"))
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_mustaqil"), callback_data="ai:mustaqil"))
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_maqola"), callback_data="ai:maqola"))
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_prez"), callback_data="ai:prez"))
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_test"), callback_data="ai:test"))
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_imlo"), callback_data="ai:imlo"))
    kb.add(types.InlineKeyboardButton(tx(uid,"back"), callback_data="bk"))
    return kb

def conv_kb(uid):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_pdf_pptx"), callback_data="cv:pdf"))
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_pptx_pdf"), callback_data="cv:pptx"))
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_img_pdf"), callback_data="cv:img"))
    kb.add(types.InlineKeyboardButton(tx(uid,"back"), callback_data="bk"))
    return kb

def tools_kb(uid):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_l2k"), callback_data="tr:l"))
    kb.add(types.InlineKeyboardButton(tx(uid,"btn_k2l"), callback_data="tr:k"))
    kb.add(types.InlineKeyboardButton(tx(uid,"back"), callback_data="bk"))
    return kb

def style_kb(uid):
    kb = types.InlineKeyboardMarkup(row_width=2)
    st = {"klassik":"Klassik","zamonaviy":"Zamonaviy","minimalist":"Minimalist","biznes":"Biznes"}
    lang = get_lang(uid)
    T_styles = {"uz":{"klassik":"Klassik","zamonaviy":"Zamonaviy","minimalist":"Minimalist","biznes":"Biznes"},
                "ru":{"klassik":"Классический","zamonaviy":"Современный","minimalist":"Минималист","biznes":"Бизнес"},
                "en":{"klassik":"Classic","zamonaviy":"Modern","minimalist":"Minimalist","biznes":"Business"}}
    st = T_styles.get(lang, T_styles["uz"])
    kb.add(*[types.InlineKeyboardButton(v, callback_data=f"st:{k}") for k,v in st.items()])
    return kb

def lc_kb(prefix):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(types.InlineKeyboardButton("O'zbek", callback_data=f"{prefix}:uz"),
           types.InlineKeyboardButton("Rus", callback_data=f"{prefix}:ru"),
           types.InlineKeyboardButton("Ingliz", callback_data=f"{prefix}:en"))
    return kb

def bk_kb(uid):
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton(tx(uid,"back"), callback_data="bk"))
    return kb

# ===== BOT HANDLERS =====
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    set_lang(uid, get_lang(uid), msg.from_user.username or "", msg.from_user.first_name or "")
    bot.send_message(uid, tx(uid,"welcome"), parse_mode="Markdown", reply_markup=lang_kb())

@bot.message_handler(commands=["stats"])
def stats(msg):
    if msg.from_user.id != ADMIN_ID: return
    u,w,c,i = get_stats()
    bot.send_message(msg.chat.id, tx(msg.from_user.id,"stats",u=u,w=w,c=c,i=f"{i:,}"), parse_mode="Markdown")

@bot.message_handler(commands=["broadcast"])
def bc_cmd(msg):
    if msg.from_user.id != ADMIN_ID: return
    sst(msg.from_user.id, "bc")
    bot.send_message(msg.chat.id, tx(msg.from_user.id,"bc_ask"))

@bot.message_handler(commands=["done"])
def done_cmd(msg):
    uid = msg.from_user.id
    imgs = UI.get(uid, [])
    if not imgs: return
    pm = bot.send_message(uid, tx(uid,"processing2"))
    td = tempfile.mkdtemp()
    try:
        out = os.path.join(td, "r.pdf")
        if imgs2pdf(imgs, out):
            with open(out,"rb") as f: bot.send_document(uid, f, caption=tx(uid,"res_pdf"))
            log_act(uid, "conv", "img_pdf")
        else: bot.send_message(uid, tx(uid,"error"))
    finally:
        shutil.rmtree(td, ignore_errors=True); UI.pop(uid,None); cst(uid)
    try: bot.delete_message(uid, pm.message_id)
    except: pass
    bot.send_message(uid, tx(uid,"main_menu"), reply_markup=main_kb(uid))

@bot.message_handler(content_types=["photo"])
def photo_h(msg):
    uid = msg.from_user.id
    if gst(uid) != "img": return
    UI.setdefault(uid, [])
    ph = msg.photo[-1]; td = tempfile.mkdtemp()
    try:
        fi = bot.get_file(ph.file_id); data = bot.download_file(fi.file_path)
        p = os.path.join(td, f"i{len(UI[uid])}.jpg")
        with open(p,"wb") as f: f.write(data)
        UI[uid].append(p)
        bot.send_message(uid, tx(uid,"imgs_got",n=len(UI[uid])))
    except Exception as e: logger.error(f"Photo:{e}")

@bot.message_handler(content_types=["document"])
def doc_h(msg):
    uid = msg.from_user.id; state = gst(uid); d = msg.document
    if not d: return
    if d.file_size > 20*1024*1024: bot.send_message(uid, tx(uid,"too_big")); return
    fname = (d.file_name or "").lower()
    td = tempfile.mkdtemp()
    try:
        fi = bot.get_file(d.file_id); data = bot.download_file(fi.file_path)
        inp = os.path.join(td, d.file_name or "f")
        with open(inp,"wb") as f: f.write(data)

        if state in ("imlo_t", "imlo_f"):
            pm = bot.send_message(uid, tx(uid,"processing2"))
            text = ""
            if fname.endswith(".txt"):
                with open(inp,"r",encoding="utf-8",errors="ignore") as f: text = f.read()
            elif fname.endswith(".pdf"):
                try:
                    import fitz; d2 = fitz.open(inp)
                    text = " ".join(pg.get_text() for pg in d2)
                except: pass
            if text:
                fixed = fix_imlo(text, get_lang(uid))
                bot.send_message(uid, tx(uid,"imlo_done",text=fixed[:3500]), parse_mode="Markdown")
                log_act(uid, "imlo")
            else: bot.send_message(uid, tx(uid,"error"))
            try: bot.delete_message(uid, pm.message_id)
            except: pass
            cst(uid); bot.send_message(uid, tx(uid,"main_menu"), reply_markup=main_kb(uid)); return

        pm = bot.send_message(uid, tx(uid,"processing2")); ok = False
        if fname.endswith(".pdf") and state == "pdf_pptx":
            op = os.path.join(td,"r.pptx")
            if pdf2pptx(inp, op):
                with open(op,"rb") as f: bot.send_document(uid, f, caption=tx(uid,"res_pptx"))
                log_act(uid,"conv","pdf_pptx"); ok = True
        elif fname.endswith((".pptx",".ppt")) and state == "pptx_pdf":
            op = os.path.join(td,"r.pdf")
            if pptx2pdf(inp, op):
                with open(op,"rb") as f: bot.send_document(uid, f, caption=tx(uid,"res_pdf"))
                log_act(uid,"conv","pptx_pdf"); ok = True
        if not ok: bot.send_message(uid, tx(uid,"wrong_fmt"))
        cst(uid)
        try: bot.delete_message(uid, pm.message_id)
        except: pass
    except Exception as e: logger.error(f"Doc:{e}"); bot.send_message(uid, tx(uid,"error"))
    finally: shutil.rmtree(td, ignore_errors=True)
    bot.send_message(uid, tx(uid,"main_menu"), reply_markup=main_kb(uid))

@bot.message_handler(func=lambda m: True)
def text_h(msg):
    uid = msg.from_user.id; text = msg.text; state = gst(uid); ud = UD.get(uid,{})

    if state == "bc" and uid == ADMIN_ID:
        cnt = 0
        for u in all_users():
            try: bot.send_message(u, text, parse_mode="Markdown"); cnt += 1
            except: pass
        bot.send_message(uid, tx(uid,"bc_done",count=cnt)); cst(uid); return

    if state == "l2k": bot.send_message(uid, tx(uid,"res_text")+f"`{l2k(text)}`", parse_mode="Markdown", reply_markup=main_kb(uid)); cst(uid); return
    if state == "k2l": bot.send_message(uid, tx(uid,"res_text")+f"`{k2l(text)}`", parse_mode="Markdown", reply_markup=main_kb(uid)); cst(uid); return

    if state == "imlo_t":
        pm = bot.send_message(uid, tx(uid,"processing2"))
        fixed = fix_imlo(text, get_lang(uid))
        try: bot.delete_message(uid, pm.message_id)
        except: pass
        bot.send_message(uid, tx(uid,"imlo_done",text=fixed[:3500]), parse_mode="Markdown")
        log_act(uid,"imlo"); cst(uid); bot.send_message(uid, tx(uid,"main_menu"), reply_markup=main_kb(uid)); return

    TOPIC_MAP = {
        "referat_t":"referat_p","kurs_t":"kurs_p","mustaqil_t":"mustaqil_p",
        "maqola_t":"maqola_p","prez_t":"prez_sl","test_t":"test_cnt"
    }
    if state in TOPIC_MAP:
        UD.setdefault(uid,{})["topic"] = text; ns = TOPIC_MAP[state]; sst(uid, ns)
        if "prez_sl" == ns: bot.send_message(uid, tx(uid,"ask_slides",price=PRICE_SLIDE), parse_mode="Markdown", reply_markup=bk_kb(uid))
        elif "test_cnt" == ns: bot.send_message(uid, tx(uid,"ask_count",price=PRICE_TEST), parse_mode="Markdown", reply_markup=bk_kb(uid))
        else:
            prices = {"referat_p":PRICE_PAGE,"kurs_p":PRICE_KURS,"mustaqil_p":PRICE_MUSTAQIL,"maqola_p":PRICE_MAQOLA}
            bot.send_message(uid, tx(uid,"ask_pages",price=prices.get(ns,PRICE_PAGE)), parse_mode="Markdown", reply_markup=bk_kb(uid))
        return

    PAGE_STATES = {"referat_p":"referat","kurs_p":"kurs","mustaqil_p":"mustaqil","maqola_p":"maqola"}
    if state in PAGE_STATES:
        try: pages = max(5, min(50, int(text.strip())))
        except: bot.send_message(uid, "5-50 orasida raqam kiriting"); return
        prices = {"referat":PRICE_PAGE,"kurs":PRICE_KURS,"mustaqil":PRICE_MUSTAQIL,"maqola":PRICE_MAQOLA}
        svc = PAGE_STATES[state]; pr = prices[svc]
        UD.setdefault(uid,{}).update({"pages":pages,"svc":svc,"total":pages*pr})
        sst(uid, f"{svc}_l")
        bot.send_message(uid, tx(uid,"ask_lang"), reply_markup=lc_kb(f"{svc}_l")); return

    if state == "prez_sl":
        try: slides = max(5, min(30, int(text.strip())))
        except: bot.send_message(uid, "5-30 orasida raqam kiriting"); return
        UD.setdefault(uid,{}).update({"slides":slides,"total":slides*PRICE_SLIDE})
        sst(uid,"prez_st"); bot.send_message(uid, tx(uid,"ask_style"), reply_markup=style_kb(uid)); return

    if state == "test_cnt":
        try: count = max(5, min(50, int(text.strip())))
        except: bot.send_message(uid, "5-50 orasida raqam kiriting"); return
        topic = ud.get("topic","")
        pm = bot.send_message(uid, tx(uid,"processing2"))
        res = gen_test(topic, count, get_lang(uid))
        try: bot.delete_message(uid, pm.message_id)
        except: pass
        for i in range(0,len(res),4000): bot.send_message(uid, res[i:i+4000])
        bot.send_message(uid, tx(uid,"done_test",count=count), parse_mode="Markdown")
        log_act(uid,"test",topic,count*PRICE_TEST); cst(uid)
        bot.send_message(uid, tx(uid,"main_menu"), reply_markup=main_kb(uid)); return

    # Menyu tugmalari
    # Direct menu buttons
    if text == "📄 Referat": sst(uid,"referat_t"); bot.send_message(uid, "📄 Mavzuni kiriting:", reply_markup=bk_kb(uid)); return
    if text == "📝 Kurs ishi": sst(uid,"kurs_t"); bot.send_message(uid, "📝 Mavzuni kiriting:", reply_markup=bk_kb(uid)); return
    if text == "📋 Mustaqil ish": sst(uid,"mustaqil_t"); bot.send_message(uid, "📋 Mavzuni kiriting:", reply_markup=bk_kb(uid)); return
    if text == "📰 Maqola": sst(uid,"maqola_t"); bot.send_message(uid, "📰 Mavzuni kiriting:", reply_markup=bk_kb(uid)); return
    if text == "📊 Prezentatsiya": sst(uid,"prez_t"); bot.send_message(uid, "📊 Mavzuni kiriting:", reply_markup=bk_kb(uid)); return
    if text == "✅ Test": sst(uid,"test_t"); bot.send_message(uid, "✅ Mavzuni kiriting:", reply_markup=bk_kb(uid)); return
    if text == "✏️ Imlo tuzatish": sst(uid,"imlo_t"); bot.send_message(uid, "✏️ Matn yuboring yoki fayl yuklang (PDF/TXT):", reply_markup=bk_kb(uid)); return
    if text == "🔄 Konvertatsiya": bot.send_message(uid, "🔄 Format tanlang:", reply_markup=conv_kb(uid)); return
    if text == "🛠 Qo'shimcha": bot.send_message(uid, "🛠 Vosita tanlang:", reply_markup=tools_kb(uid)); return
    if text == "❓ Yordam":
        bot.send_message(uid, tx(uid,"help_text",pp=PRICE_PAGE,kp=PRICE_KURS,mp2=PRICE_MUSTAQIL,mp=PRICE_MAQOLA,sp=PRICE_SLIDE,tp=PRICE_TEST), parse_mode="Markdown", reply_markup=main_kb(uid)); return
    if text == "🌐 Mini App":
        mk = types.InlineKeyboardMarkup()
        mk.add(types.InlineKeyboardButton("🌐 Mini Ilovani ochish", web_app=types.WebAppInfo(url=MINI_APP_URL)))
        bot.send_message(uid, "📱 *EduBot Mini Ilova*\n\nQuyidagi tugmani bosing va to'liq imkoniyatlardan foydalaning!", parse_mode="Markdown", reply_markup=mk)
        return
    if text in ("👨‍💼 Admin", "👨\u200d💼 Admin"):
        ak = types.InlineKeyboardMarkup()
        ak.add(types.InlineKeyboardButton(tx(uid,"contact"), url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))
        bot.send_message(uid, tx(uid,"admin_text"), parse_mode="Markdown", reply_markup=ak); return

@bot.callback_query_handler(func=lambda c: True)
def cb_h(call):
    uid = call.from_user.id; d = call.data
    bot.answer_callback_query(call.id)
    ud = UD.get(uid,{})

    if d.startswith("lang:"):
        lang = d[5:]
        set_lang(uid, lang, call.from_user.username or "", call.from_user.first_name or "")
        bot.edit_message_text(tx(uid,"lang_set"), uid, call.message.message_id)
        bot.send_message(uid, tx(uid,"main_menu"), reply_markup=main_kb(uid))

    elif d == "ai:referat": sst(uid,"referat_t"); bot.edit_message_text(tx(uid,"ask_topic"), uid, call.message.message_id, reply_markup=bk_kb(uid))
    elif d == "ai:kurs": sst(uid,"kurs_t"); bot.edit_message_text(tx(uid,"ask_topic"), uid, call.message.message_id, reply_markup=bk_kb(uid))
    elif d == "ai:mustaqil": sst(uid,"mustaqil_t"); bot.edit_message_text(tx(uid,"ask_topic"), uid, call.message.message_id, reply_markup=bk_kb(uid))
    elif d == "ai:maqola": sst(uid,"maqola_t"); bot.edit_message_text(tx(uid,"ask_topic"), uid, call.message.message_id, reply_markup=bk_kb(uid))
    elif d == "ai:prez": sst(uid,"prez_t"); bot.edit_message_text(tx(uid,"ask_topic"), uid, call.message.message_id, reply_markup=bk_kb(uid))
    elif d == "ai:test": sst(uid,"test_t"); bot.edit_message_text(tx(uid,"ask_topic"), uid, call.message.message_id, reply_markup=bk_kb(uid))
    elif d == "ai:imlo": sst(uid,"imlo_t"); bot.edit_message_text(tx(uid,"imlo_ask"), uid, call.message.message_id, reply_markup=bk_kb(uid))

    elif ":" in d and d.split(":")[0].endswith("_l"):
        parts = d.split(":"); lang_code = parts[1]; svc = parts[0][:-2]
        topic = ud.get("topic",""); pages = ud.get("pages",5); total = ud.get("total",0)
        pm = bot.send_message(uid, tx(uid,"processing",total=total), parse_mode="Markdown")
        GEN = {"referat":gen_referat,"kurs":gen_kurs,"mustaqil":gen_mustaqil,"maqola":gen_maqola}
        gen_fn = GEN.get(svc, gen_referat)
        res = gen_fn(topic, pages, lang_code)
        try: bot.delete_message(uid, pm.message_id)
        except: pass
        for i in range(0,len(res),4000): bot.send_message(uid, res[i:i+4000])
        bot.send_message(uid, tx(uid,"done_text",topic=topic,pages=pages,total=total), parse_mode="Markdown")
        log_act(uid, svc, topic, total); cst(uid)
        bot.send_message(uid, tx(uid,"main_menu"), reply_markup=main_kb(uid))

    elif d.startswith("st:"):
        style = d[3:]; topic = ud.get("topic",""); slides = ud.get("slides",10); total = ud.get("total",0)
        pm = bot.send_message(uid, tx(uid,"processing",total=total), parse_mode="Markdown")
        content = gen_prez(topic, slides, style, get_lang(uid))
        op, td2 = make_pptx(content, topic, style)
        try: bot.delete_message(uid, pm.message_id)
        except: pass
        if op and os.path.exists(op):
            with open(op,"rb") as f: bot.send_document(uid, f, caption=tx(uid,"done_prez",topic=topic,slides=slides), parse_mode="Markdown")
            if td2: shutil.rmtree(td2, ignore_errors=True)
        else:
            for i in range(0,len(content),4000): bot.send_message(uid, content[i:i+4000])
            bot.send_message(uid, tx(uid,"done_prez",topic=topic,slides=slides), parse_mode="Markdown")
        log_act(uid,"prez",topic,total); cst(uid)
        bot.send_message(uid, tx(uid,"main_menu"), reply_markup=main_kb(uid))

    elif d == "cv:pdf": sst(uid,"pdf_pptx"); bot.edit_message_text(tx(uid,"send_pdf"), uid, call.message.message_id, reply_markup=bk_kb(uid))
    elif d == "cv:pptx": sst(uid,"pptx_pdf"); bot.edit_message_text(tx(uid,"send_pptx"), uid, call.message.message_id, reply_markup=bk_kb(uid))
    elif d == "cv:img": sst(uid,"img"); UI[uid]=[]; bot.edit_message_text(tx(uid,"send_imgs"), uid, call.message.message_id, reply_markup=bk_kb(uid))

    elif d == "tr:l": sst(uid,"l2k"); bot.edit_message_text(tx(uid,"send_text"), uid, call.message.message_id, reply_markup=bk_kb(uid))
    elif d == "tr:k": sst(uid,"k2l"); bot.edit_message_text(tx(uid,"send_text"), uid, call.message.message_id, reply_markup=bk_kb(uid))

    elif d == "bk":
        cst(uid)
        try: bot.edit_message_text(tx(uid,"main_menu"), uid, call.message.message_id)
        except: pass
        bot.send_message(uid, tx(uid,"main_menu"), reply_markup=main_kb(uid))

if __name__ == "__main__":
    init_db()
    print("EduBot ishga tushdi!")
    bot.infinity_polling()
