import telebot, os, sqlite3, logging, tempfile, shutil, requests, re
from telebot import types
from datetime import datetime
from io import BytesIO

BOT_TOKEN      = os.environ.get("BOT_TOKEN",      "8270798642:AAGtdwHVgu0rKCwTU5x9eLLWWYGoWhG-j6I")
ADMIN_ID       = int(os.environ.get("ADMIN_ID",   "1113404703"))
ADMIN_USERNAME = os.environ.get("ADMIN_USERNAME", "@abdurakhmon02")
DONATE_URL     = os.environ.get("DONATE_URL",     "https://click.uz")
DONATE_CARD    = os.environ.get("DONATE_CARD",    "9860 0609 2665 0809")
DONATE_CLICK   = os.environ.get("DONATE_CLICK",   "+998 94 975 03 04")
CLAUDE_API_KEY = os.environ.get("CLAUDE_API_KEY", "")

def get_price(name, default):
    return int(os.environ.get(name, str(default)))

PRICE_PAGE     = get_price("PRICE_PAGE",     500)
PRICE_KURS     = get_price("PRICE_KURS",     700)
PRICE_MUSTAQIL = get_price("PRICE_MUSTAQIL", 400)
PRICE_MAQOLA   = get_price("PRICE_MAQOLA",   600)
PRICE_SLIDE    = get_price("PRICE_SLIDE",    300)
PRICE_TEST     = get_price("PRICE_TEST",     200)
BONUS_FIRST    = get_price("BONUS_FIRST",   3000)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s", level=logging.INFO)
logger = logging.getLogger(__name__)
bot = telebot.TeleBot(BOT_TOKEN)
LN = {"uz": "o'zbek", "ru": "rus", "en": "ingliz"}

# ===== DATABASE =====
def init_db():
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY, username TEXT, first_name TEXT,
        lang TEXT DEFAULT 'uz', balance INTEGER DEFAULT 0,
        bonus_given INTEGER DEFAULT 0, joined_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS stats (
        id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER,
        action TEXT, detail TEXT, income INTEGER DEFAULT 0, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS payments (
        id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER,
        amount INTEGER, status TEXT DEFAULT 'pending', created_at TEXT)""")
    conn.commit(); conn.close()

def get_user(uid):
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE telegram_id=?", (uid,))
    row = c.fetchone(); conn.close()
    if row:
        return {"id":row[0],"username":row[1],"first_name":row[2],
                "lang":row[3],"balance":row[4],"bonus_given":row[5]}
    return None

def reg_user(uid, uname, fname, lang="uz"):
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("SELECT telegram_id FROM users WHERE telegram_id=?", (uid,))
    exists = c.fetchone()
    if not exists:
        c.execute("""INSERT INTO users (telegram_id,username,first_name,lang,balance,bonus_given,joined_at)
            VALUES (?,?,?,?,?,?,?)""",
            (uid, uname, fname, lang, BONUS_FIRST, 1,
             datetime.now().strftime("%d.%m.%Y %H:%M")))
        conn.commit(); conn.close()
        return True  # yangi foydalanuvchi
    else:
        c.execute("UPDATE users SET username=?,first_name=?,lang=? WHERE telegram_id=?",
            (uname, fname, lang, uid))
        conn.commit(); conn.close()
        return False

def set_lang(uid, lang):
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET lang=? WHERE telegram_id=?", (lang, uid))
    conn.commit(); conn.close()

def get_lang(uid):
    u = get_user(uid)
    return u["lang"] if u else "uz"

def get_balance(uid):
    u = get_user(uid)
    return u["balance"] if u else 0

def deduct_balance(uid, amount):
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance=balance-? WHERE telegram_id=?", (amount, uid))
    conn.commit(); conn.close()

def add_balance(uid, amount):
    conn = sqlite3.connect("edubot.db")
    c = conn.cursor()
    c.execute("UPDATE users SET balance=balance+? WHERE telegram_id=?", (amount, uid))
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
    c.execute("SELECT COUNT(*) FROM users"); u = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM stats WHERE action IN ('referat','kurs','mustaqil','maqola','prez','test')"); w = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM stats WHERE action='conv'"); cv = c.fetchone()[0]
    c.execute("SELECT COALESCE(SUM(income),0) FROM stats"); i = c.fetchone()[0]
    conn.close(); return u, w, cv, i

# ===== CLAUDE AI =====
def claude(prompt, system="", max_tok=4000):
    if not CLAUDE_API_KEY: return "Claude API kaliti sozlanmagan!"
    try:
        r = requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key": CLAUDE_API_KEY, "anthropic-version": "2023-06-01",
                     "content-type": "application/json"},
            json={"model": "claude-haiku-4-5-20251001", "max_tokens": max_tok,
                  "system": system, "messages": [{"role": "user", "content": prompt}]},
            timeout=120)
        if r.status_code == 200: return r.json()["content"][0]["text"]
        return f"API xatosi: {r.status_code}"
    except Exception as e: return f"Xatolik: {e}"

def build_user_info(ud):
    info = []
    if ud.get("full_name"): info.append(f"Muallif: {ud['full_name']}")
    if ud.get("university"): info.append(f"Universitet: {ud['university']}")
    if ud.get("faculty"): info.append(f"Fakultet: {ud['faculty']}")
    if ud.get("year"): info.append(f"Kurs: {ud['year']}")
    if ud.get("teacher"): info.append(f"O'qituvchi: {ud['teacher']}")
    if ud.get("city"): info.append(f"Shahar: {ud['city']}")
    return "\n".join(info)

def gen_referat(topic, pages, lang, ud={}):
    ln = LN.get(lang, "o'zbek")
    uinfo = build_user_info(ud)
    words_per_page = 300
    total_words = pages * words_per_page
    return claude(
        f"Mavzu: {topic}\nTil: {ln}\nMuallif ma'lumotlari:\n{uinfo}\n\n"
        f"Umumiy so'z soni: kamida {total_words} so'z ({pages} bet)\n\n"
        f"{ln} tilida TO'LIQ akademik referat yozing. Har bir bo'limda kamida {words_per_page} so'z bo'lsin.\n\n"
        "**REFERAT**\n"
        f"**Mavzu:** {topic}\n"
        f"{uinfo}\n\n"
        "**KIRISH**\n"
        "(Mavzuning dolzarbligi, maqsad va vazifalar - kamida 200 so'z)\n\n"
        "**I BOB. NAZARIY ASOSLAR**\n"
        "1.1. (sarlavha - kamida 250 so'z)\n"
        "1.2. (sarlavha - kamida 250 so'z)\n\n"
        "**II BOB. ASOSIY TAHLIL**\n"
        "2.1. (sarlavha - kamida 250 so'z)\n"
        "2.2. (sarlavha - kamida 250 so'z)\n\n"
        "**III BOB. XULOSALAR VA TAVSIYALAR**\n"
        "(kamida 200 so'z)\n\n"
        "**XULOSA**\n"
        "(kamida 150 so'z)\n\n"
        "**FOYDALANILGAN ADABIYOTLAR**\n"
        "(kamida 10 ta manba - kitob, maqola, internet)\n",
        f"Siz professional {ln} tilida referat yozuvchi akademik mutaxasssissiz. "
        "Har bir bo'limni to'liq, batafsil, real ilmiy faktlar va ma'lumotlar bilan yozing. "
        "Kitoblardan, ilmiy maqolalardan olingan aniq faktlar keltiring. "
        "Hech qachon qisqartirmang — to'liq hajmda yozing.",
        4000)

def gen_kurs(topic, pages, lang, ud={}):
    ln = LN.get(lang, "o'zbek")
    uinfo = build_user_info(ud)
    total_words = pages * 350
    return claude(
        f"Mavzu: {topic}\nTil: {ln}\n{uinfo}\n\n"
        f"Kamida {total_words} so'z ({pages} bet) bo'lsin.\n\n"
        f"{ln} tilida TO'LIQ kurs ishi yozing:\n\n"
        "**KURS ISHI**\n"
        f"**Mavzu:** {topic}\n"
        f"{uinfo}\n\n"
        "**MUNDARIJA**\n\n"
        "**KIRISH** (maqsad, vazifalar, dolzarblik, ob'ekt, predmet, gipoteza - 300 so'z)\n\n"
        "**I BOB. NAZARIY ASOSLAR** (har bo'limcha kamida 400 so'z)\n"
        "1.1. Mavzuning nazariy asoslari\n"
        "1.2. Xorijiy va mahalliy tadqiqotlar tahlili\n"
        "1.3. Asosiy tushuncha va kategoriyalar\n\n"
        "**II BOB. EMPIRIK TADQIQOT** (har bo'limcha kamida 400 so'z)\n"
        "2.1. Tadqiqot metodologiyasi\n"
        "2.2. Natijalar va tahlil\n"
        "2.3. Jadvallar va diagrammalar tavsifi\n\n"
        "**III BOB. TAVSIYALAR** (kamida 300 so'z)\n"
        "3.1. Amaliy tavsiyalar\n"
        "3.2. Kelajakdagi tadqiqot yo'nalishlari\n\n"
        "**XULOSA** (200 so'z)\n\n"
        "**FOYDALANILGAN ADABIYOTLAR** (kamida 15 ta - APA formatida)\n\n"
        "**ILOVALAR**\n",
        f"Siz {ln} tilida kurs ishi yozuvchi professor. To'liq, ilmiy, faktlar bilan boy yozing.",
        4000)

def gen_mustaqil(topic, pages, lang, ud={}):
    ln = LN.get(lang, "o'zbek")
    uinfo = build_user_info(ud)
    total_words = pages * 280
    return claude(
        f"Mavzu: {topic}\nTil: {ln}\n{uinfo}\n\nKamida {total_words} so'z.\n\n"
        f"{ln} tilida TO'LIQ mustaqil ish yozing:\n\n"
        "**MUSTAQIL ISH**\n"
        f"**Mavzu:** {topic}\n"
        f"{uinfo}\n\n"
        "**KIRISH** (maqsad, vazifalar - 200 so'z)\n\n"
        "**ASOSIY QISM 1** (kamida 300 so'z - nazariy asos)\n\n"
        "**ASOSIY QISM 2** (kamida 300 so'z - tahlil va misollar)\n\n"
        "**ASOSIY QISM 3** (kamida 250 so'z - amaliy jihat)\n\n"
        "**XULOSA** (150 so'z)\n\n"
        "**ADABIYOTLAR** (8-10 ta manba)\n",
        f"Siz {ln} tilida mustaqil ish yozuvchi o'qituvchisiz. To'liq va sifatli yozing.",
        4000)

def gen_maqola(topic, pages, lang, ud={}):
    ln = LN.get(lang, "o'zbek")
    uinfo = build_user_info(ud)
    total_words = pages * 320
    return claude(
        f"Mavzu: {topic}\nTil: {ln}\n{uinfo}\n\nKamida {total_words} so'z.\n\n"
        f"{ln} tilida VAK talablariga mos ilmiy maqola yozing:\n\n"
        f"**{topic.upper()}**\n"
        f"{uinfo}\n\n"
        "**ANNOTATSIYA** (150-200 so'z)\n\n"
        "**KALIT SO'ZLAR:** (7-10 ta)\n\n"
        "**ABSTRACT** (ingliz tilida, 150 so'z)\n\n"
        "**KEYWORDS:** (ingliz tilida)\n\n"
        "**KIRISH** (dolzarblik, muammo - 300 so'z)\n\n"
        "**ADABIYOTLAR SHARHI** (300 so'z - boshqa tadqiqotlar tahlili)\n\n"
        "**METODOLOGIYA** (200 so'z)\n\n"
        "**NATIJALAR VA MUHOKAMA** (400 so'z - asosiy topilmalar)\n\n"
        "**XULOSA** (200 so'z)\n\n"
        "**ADABIYOTLAR** (APA 7 formatida, 12-15 ta manba)\n",
        f"Siz {ln} tilida VAK jurnallari uchun ilmiy maqola yozuvchi professor. "
        "Ilmiy uslub, aniq faktlar, to'liq hajmda yozing.",
        4000)

def gen_prez(topic, slides, style, lang, ud={}):
    ln = LN.get(lang, "o'zbek")
    uinfo = build_user_info(ud)
    words_per_slide = 280
    return claude(
        f"Mavzu: {topic}\nSlaydlar: {slides}\nUslub: {style}\nTil: {ln}\n{uinfo}\n\n"
        f"Har bir slaydda kamida {words_per_slide} so'z bo'lsin.\n\n"
        f"{ln} tilida {slides} ta BATAFSIL slayd yozing:\n\n"
        "FORMAT:\n"
        "SLAYD N: [Sarlavha]\n"
        "[Kamida 280 so'z - to'liq matn, aniq faktlar, misollar, statistika]\n\n"
        f"1-SLAYD: Sarlavha ({topic}) - muallif, universitet, sana\n"
        f"2-SLAYD: Mundarija - {slides} ta bo'lim ro'yxati\n"
        f"3-{slides-1}-SLAYD: Asosiy mazmun - har birida 280+ so'z\n"
        f"{slides}-SLAYD: Xulosa va takliflar\n\n"
        "MUHIM: Har slaydda aniq ilmiy faktlar, raqamlar, misollar keltiring!",
        f"Siz professional {ln} prezentatsiya mutaxassisi. "
        "Har slaydni batafsil, faktlar va misollar bilan to'ldiring.",
        4000)

def gen_test(topic, count, lang):
    ln = LN.get(lang, "o'zbek")
    return claude(
        f"Mavzu: {topic}\nSavollar: {count}\nTil: {ln}\n\n"
        f"{ln} tilida {count} ta professional test:\n"
        "N. [Aniq savol]\nA) ...\nB) ...\nC) ...\nD) ...\nTo'g'ri javob: [harf]\n\n"
        f"Darajalar: {count//3} ta oson, {count//3} ta o'rta, {count-2*(count//3)} ta qiyin",
        f"Professional {ln} test yaratuvchi.", min(count*85,4000))

def fix_imlo(text, lang):
    ln = LN.get(lang, "o'zbek")
    return claude(
        f"{ln} imlo qoidalariga muvofiq tuzat. Faqat tuzatilgan matn:\n\n{text[:2500]}",
        f"{ln} tili imlo mutaxassisi.", 3500)

# ===== DOCX YARATISH =====
def make_docx(content, title, ud={}):
    try:
        from docx import Document
        from docx.shared import Pt, Cm, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH

        doc = Document()
        style = doc.styles['Normal']
        style.font.name = 'Times New Roman'
        style.font.size = Pt(14)

        # Sahifa sozlamalari
        section = doc.sections[0]
        section.page_height = Cm(29.7)
        section.page_width = Cm(21)
        section.left_margin = Cm(3)
        section.right_margin = Cm(1.5)
        section.top_margin = Cm(2)
        section.bottom_margin = Cm(2)

        # Sarlavha sahifasi
        if ud.get("university"):
            p = doc.add_paragraph(ud["university"])
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.runs[0].font.size = Pt(14)

        if ud.get("faculty"):
            p = doc.add_paragraph(ud["faculty"])
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_paragraph()
        title_p = doc.add_paragraph(title)
        title_p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        title_p.runs[0].font.size = Pt(16)
        title_p.runs[0].font.bold = True
        doc.add_paragraph()

        if ud.get("full_name"):
            p = doc.add_paragraph(f"Muallif: {ud['full_name']}")
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if ud.get("teacher"):
            p = doc.add_paragraph(f"O'qituvchi: {ud['teacher']}")
            p.alignment = WD_ALIGN_PARAGRAPH.RIGHT
        if ud.get("city"):
            p = doc.add_paragraph(ud.get("city","") + f" — {datetime.now().year}")
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER

        doc.add_page_break()

        # Mazmun
        for line in content.split('\n'):
            line = line.strip()
            if not line: doc.add_paragraph(); continue
            if line.startswith('**') and line.endswith('**'):
                heading = line.strip('*')
                p = doc.add_paragraph(heading)
                p.runs[0].font.bold = True
                p.runs[0].font.size = Pt(14)
            elif re.match(r'^\d+\.', line) or re.match(r'^[IVX]+\.', line):
                p = doc.add_paragraph(line)
                p.runs[0].font.bold = True
            else:
                p = doc.add_paragraph(line)
                p.paragraph_format.first_line_indent = Cm(1.25)

        td = tempfile.mkdtemp()
        out = os.path.join(td, 'dokument.docx')
        doc.save(out)
        return out, td
    except Exception as e:
        logger.error(f"DOCX error: {e}"); return None, None

def make_pdf(content, title, ud={}):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.units import cm
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont

        td = tempfile.mkdtemp()
        out = os.path.join(td, 'dokument.pdf')
        c = canvas.Canvas(out, pagesize=A4)
        w, h = A4
        margin = 2*cm
        y = h - margin
        font_size = 12

        def new_page():
            nonlocal y
            c.showPage()
            y = h - margin

        def write_line(text, bold=False, size=12, indent=0):
            nonlocal y
            if y < margin + cm:
                new_page()
            c.setFont("Helvetica-Bold" if bold else "Helvetica", size)
            # Handle long lines
            max_width = w - 2*margin - indent
            words = text.split()
            line = ""
            for word in words:
                test = line + " " + word if line else word
                if c.stringWidth(test, "Helvetica", size) < max_width:
                    line = test
                else:
                    c.drawString(margin + indent, y, line)
                    y -= size + 4
                    if y < margin: new_page()
                    line = word
            if line:
                c.drawString(margin + indent, y, line)
                y -= size + 6

        # Sarlavha
        if ud.get("university"):
            write_line(ud["university"], bold=True, size=13)
        write_line(title, bold=True, size=14)
        if ud.get("full_name"):
            write_line(f"Muallif: {ud['full_name']}")
        y -= cm

        for line in content.split('\n'):
            line = line.strip()
            if not line: y -= 8; continue
            is_heading = line.startswith('**') and line.endswith('**')
            if is_heading:
                write_line(line.strip('*'), bold=True, size=13)
            else:
                write_line(line, indent=20)

        c.save()
        return out, td
    except Exception as e:
        logger.error(f"PDF error: {e}"); return None, None

# ===== PPTX YARATISH =====
def make_pptx(content, topic, style="klassik", ud={}):
    try:
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor

        THEMES = {
            "klassik":    (RGBColor(255,255,255), RGBColor(31,73,125),  RGBColor(30,30,30)),
            "zamonaviy":  (RGBColor(10,10,30),    RGBColor(0,200,200),   RGBColor(220,230,255)),
            "minimalist": (RGBColor(248,248,248),  RGBColor(40,40,40),   RGBColor(70,70,70)),
            "biznes":     (RGBColor(0,40,80),      RGBColor(255,200,0),  RGBColor(255,255,255)),
        }
        bg, tc, tx = THEMES.get(style, THEMES["klassik"])

        prs = Presentation()
        prs.slide_width = Inches(13.33); prs.slide_height = Inches(7.5)
        blank = prs.slide_layouts[6]

        slides_data = []
        cur_t, cur_b = topic, []

        for line in content.strip().split("\n"):
            line = line.strip()
            if not line: continue
            ul = line.upper()
            is_slide = any(ul.startswith(x) for x in ("SLAYD","СЛАЙД","SLIDE")) and ":" in line
            if is_slide:
                if cur_t: slides_data.append((cur_t, "\n".join(cur_b)))
                cur_t = line.split(":",1)[1].strip(); cur_b = []
            else:
                cur_b.append(line)

        if cur_t: slides_data.append((cur_t, "\n".join(cur_b)))
        if not slides_data: slides_data = [(topic, content[:500])]

        for title, body in slides_data:
            sl = prs.slides.add_slide(blank)
            sl.background.fill.solid(); sl.background.fill.fore_color.rgb = bg

            # Sarlavha
            tb = sl.shapes.add_textbox(Inches(.4), Inches(.2), Inches(12.5), Inches(1.3))
            tf = tb.text_frame; tf.word_wrap = True
            p = tf.paragraphs[0]
            p.text = title[:90]; p.font.size = Pt(28); p.font.bold = True; p.font.color.rgb = tc

            # Chiziq
            ac = sl.shapes.add_shape(1, Inches(.4), Inches(1.55), Inches(12.5), Inches(.06))
            ac.fill.solid(); ac.fill.fore_color.rgb = tc; ac.line.fill.background()

            # Mazmun - to'liq matn
            if body:
                cb = sl.shapes.add_textbox(Inches(.4), Inches(1.7), Inches(12.5), Inches(5.6))
                tf2 = cb.text_frame; tf2.word_wrap = True
                lines = [l.strip() for l in body.split("\n") if l.strip()]
                first = True
                for line in lines[:20]:
                    p2 = tf2.paragraphs[0] if first else tf2.add_paragraph()
                    first = False
                    if line.startswith(("*","•","-","–")):
                        p2.text = f"▸ {line.lstrip('*•-– ')}"
                        p2.font.size = Pt(16)
                    else:
                        p2.text = line
                        p2.font.size = Pt(15)
                    p2.font.color.rgb = tx
                    p2.space_before = Pt(4)

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
        prs = Presentation()
        prs.slide_width = Inches(10); prs.slide_height = Inches(7.5)
        doc = fitz.open(pdf)
        for page in doc:
            pix = page.get_pixmap(matrix=fitz.Matrix(2,2))
            sl = prs.slides.add_slide(prs.slide_layouts[6])
            sl.shapes.add_picture(BytesIO(pix.tobytes("png")), 0, 0, prs.slide_width, prs.slide_height)
        doc.close(); prs.save(out); return True
    except Exception as e: logger.error(f"pdf2pptx:{e}"); return False

def pptx2pdf(pptx, out):
    try:
        from pptx import Presentation
        from reportlab.pdfgen import canvas
        from PIL import Image
        prs = Presentation(pptx)
        w = float(prs.slide_width)/914400*72; h = float(prs.slide_height)/914400*72
        c = canvas.Canvas(out, pagesize=(w,h))
        for i in range(len(prs.slides)):
            img = Image.new("RGB",(int(w*2),int(h*2)),"white")
            td2 = tempfile.mkdtemp(); tp = os.path.join(td2,f"s{i}.png")
            img.save(tp); c.drawImage(tp,0,0,w,h); c.showPage(); shutil.rmtree(td2)
        c.save(); return True
    except Exception as e: logger.error(f"pptx2pdf:{e}"); return False

def imgs2pdf(imgs, out):
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import A4
        from PIL import Image
        c = canvas.Canvas(out, pagesize=A4); aw,ah = A4
        for p in imgs:
            img = Image.open(p); iw,ih = img.size; r = min(aw/iw,ah/ih)
            nw,nh = iw*r,ih*r; c.drawImage(p,(aw-nw)/2,(ah-nh)/2,nw,nh); c.showPage()
        c.save(); return True
    except Exception as e: logger.error(f"imgs2pdf:{e}"); return False

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
 "я":"ya","Я":"Ya","ю":"yu","Ю":"Yu","ё":"yo","Ё":"Yo","ъ":"","ь":"","ц":"ts","щ":"sh"}

def l2k(t):
    r=t
    for k,v in sorted(L2K.items(),key=lambda x:-len(x[0])): r=r.replace(k,v)
    return r

def k2l(t):
    r,i="",0
    while i<len(t):
        two=t[i:i+2]
        if two in K2L: r+=K2L[two]; i+=2
        elif t[i] in K2L: r+=K2L[t[i]]; i+=1
        else: r+=t[i]; i+=1
    return r

# ===== HOLAT =====
ST,UD,UI={},{},{}
def sst(uid,s,**kw): ST[uid]=s; UD.setdefault(uid,{}).update(kw)
def gst(uid): return ST.get(uid)
def cst(uid): ST.pop(uid,None)

def send_result(uid, content, title, fmt, ud={}):
    """Natijani foydalanuvchi tanlagan formatda yuborish"""
    if fmt == "docx":
        op, td = make_docx(content, title, ud)
        if op:
            with open(op,"rb") as f: bot.send_document(uid, f, caption=f"📝 {title}")
            shutil.rmtree(td, ignore_errors=True); return True
    elif fmt == "pdf":
        op, td = make_pdf(content, title, ud)
        if op:
            with open(op,"rb") as f: bot.send_document(uid, f, caption=f"📄 {title}")
            shutil.rmtree(td, ignore_errors=True); return True
    elif fmt == "txt":
        bot.send_message(uid, content[:4000])
        if len(content) > 4000:
            for i in range(4000, len(content), 4000):
                bot.send_message(uid, content[i:i+4000])
        return True
    return False

# ===== KLAVIATURALAR =====
def lang_kb():
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(types.InlineKeyboardButton("🇺🇿 O'zbek", callback_data="lang:uz"),
           types.InlineKeyboardButton("🇷🇺 Русский", callback_data="lang:ru"),
           types.InlineKeyboardButton("🇬🇧 English", callback_data="lang:en"))
    return kb

def main_kb(uid):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📄 Referat", "📝 Kurs ishi")
    kb.row("📋 Mustaqil ish", "📰 Maqola")
    kb.row("📊 Prezentatsiya", "✅ Test")
    kb.row("✏️ Imlo tuzatish", "🔄 Konvertatsiya")
    kb.row("💰 Balans", "💝 Donat")
    kb.row("❓ Yordam", "👨‍💼 Admin")
    return kb

def fmt_kb(uid, prefix):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("📝 DOCX", callback_data=f"{prefix}:docx"),
        types.InlineKeyboardButton("📄 PDF",  callback_data=f"{prefix}:pdf"),
        types.InlineKeyboardButton("📱 Matn", callback_data=f"{prefix}:txt"))
    return kb

def conv_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📄➡️📊 PDF → PPTX", callback_data="cv:pdf"))
    kb.add(types.InlineKeyboardButton("📊➡️📄 PPTX → PDF", callback_data="cv:pptx"))
    kb.add(types.InlineKeyboardButton("🖼➡️📄 Rasmlar → PDF", callback_data="cv:img"))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="bk"))
    return kb

def tools_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔡 Lotin → Kirill", callback_data="tr:l"))
    kb.add(types.InlineKeyboardButton("🔠 Kirill → Lotin", callback_data="tr:k"))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="bk"))
    return kb

def style_kb():
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("🎨 Klassik", callback_data="st:klassik"),
        types.InlineKeyboardButton("💎 Zamonaviy", callback_data="st:zamonaviy"),
        types.InlineKeyboardButton("⬜ Minimalist", callback_data="st:minimalist"),
        types.InlineKeyboardButton("💼 Biznes", callback_data="st:biznes"))
    return kb

def lc_kb(prefix):
    kb = types.InlineKeyboardMarkup(row_width=3)
    kb.add(
        types.InlineKeyboardButton("🇺🇿 O'zbek", callback_data=f"{prefix}:uz"),
        types.InlineKeyboardButton("🇷🇺 Rus", callback_data=f"{prefix}:ru"),
        types.InlineKeyboardButton("🇬🇧 Ingliz", callback_data=f"{prefix}:en"))
    return kb

def bk_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="bk"))
    return kb

def yes_no_kb(prefix):
    kb = types.InlineKeyboardMarkup(row_width=2)
    kb.add(
        types.InlineKeyboardButton("✅ Ha", callback_data=f"{prefix}:yes"),
        types.InlineKeyboardButton("❌ Yo'q", callback_data=f"{prefix}:no"))
    return kb

# ===== HANDLERS =====
@bot.message_handler(commands=["start"])
def start(msg):
    uid = msg.from_user.id
    uname = msg.from_user.username or ""
    fname = msg.from_user.first_name or ""
    is_new = reg_user(uid, uname, fname)

    welcome = (
        f"👋 Xush kelibsiz, {fname}!\n\n"
        "🎓 *EduBot* — Ta'lim yordamchingiz!\n\n"
        "📚 Xizmatlar:\n"
        "• 📄 Referat, 📝 Kurs ishi\n"
        "• 📋 Mustaqil ish, 📰 Maqola\n"
        "• 📊 Prezentatsiya, ✅ Test\n"
        "• ✏️ Imlo tuzatish, 🔄 Konvertatsiya\n\n"
    )
    if is_new:
        welcome += f"🎁 *Tabriklaymiz! {BONUS_FIRST:,} so'm bonus berildi!*\n\n"
    welcome += "Tilni tanlang:"

    bot.send_message(uid, welcome, parse_mode="Markdown", reply_markup=lang_kb())

    if is_new:
        try:
            bot.send_message(ADMIN_ID,
                f"🆕 Yangi foydalanuvchi!\n"
                f"👤 {fname} (@{uname})\n"
                f"🎁 {BONUS_FIRST:,} so'm bonus\n"
                f"🆔 {uid}")
        except: pass

@bot.message_handler(commands=["stats"])
def stats_cmd(msg):
    if msg.from_user.id != ADMIN_ID: return
    u,w,c,i = get_stats()
    conn = sqlite3.connect("edubot.db")
    cur = conn.cursor()
    cur.execute("SELECT COALESCE(SUM(balance),0) FROM users")
    total_balance = cur.fetchone()[0]
    conn.close()
    bot.send_message(msg.chat.id,
        f"📊 *Statistika*\n\n"
        f"👥 Foydalanuvchilar: {u}\n"
        f"📝 Ishlar: {w}\n"
        f"🔄 Konvertatsiyalar: {c}\n"
        f"💰 Jami daromad: {i:,} so'm\n"
        f"💳 Jami balans: {total_balance:,} so'm",
        parse_mode="Markdown")

@bot.message_handler(commands=["broadcast"])
def bc_cmd(msg):
    if msg.from_user.id != ADMIN_ID: return
    sst(msg.from_user.id, "bc")
    bot.send_message(msg.chat.id, "📢 Xabar matnini yozing (barcha foydalanuvchilarga yuboriladi):")

@bot.message_handler(commands=["setprice"])
def setprice_cmd(msg):
    if msg.from_user.id != ADMIN_ID: return
    bot.send_message(msg.chat.id,
        "💰 *Narxlarni o'zgartirish*\n\n"
        "Railway Variables da o'zgartiring:\n"
        f"• PRICE_PAGE = {PRICE_PAGE} (Referat)\n"
        f"• PRICE_KURS = {PRICE_KURS} (Kurs ishi)\n"
        f"• PRICE_MUSTAQIL = {PRICE_MUSTAQIL} (Mustaqil)\n"
        f"• PRICE_MAQOLA = {PRICE_MAQOLA} (Maqola)\n"
        f"• PRICE_SLIDE = {PRICE_SLIDE} (Prezentatsiya)\n"
        f"• PRICE_TEST = {PRICE_TEST} (Test)\n"
        f"• BONUS_FIRST = {BONUS_FIRST} (Yangi foydalanuvchi bonus)\n\n"
        "Yoki foydalanuvchiga balans qo'shish:\n"
        "/addbalance [user_id] [summa]",
        parse_mode="Markdown")

@bot.message_handler(commands=["addbalance"])
def add_balance_cmd(msg):
    if msg.from_user.id != ADMIN_ID: return
    try:
        parts = msg.text.split()
        target_uid = int(parts[1])
        amount = int(parts[2])
        add_balance(target_uid, amount)
        bot.send_message(msg.chat.id, f"✅ {target_uid} ga {amount:,} so'm qo'shildi!")
        bot.send_message(target_uid,
            f"💰 Hisobingizga {amount:,} so'm qo'shildi!\n"
            f"Joriy balans: {get_balance(target_uid):,} so'm")
    except Exception as e:
        bot.send_message(msg.chat.id, f"❌ Xato: /addbalance [user_id] [summa]")

@bot.message_handler(commands=["done"])
def done_cmd(msg):
    uid = msg.from_user.id
    imgs = UI.get(uid, [])
    if not imgs: return
    pm = bot.send_message(uid, "⏳ PDF yaratilmoqda...")
    td = tempfile.mkdtemp()
    try:
        out = os.path.join(td, "r.pdf")
        if imgs2pdf(imgs, out):
            with open(out,"rb") as f: bot.send_document(uid, f, caption="📄 PDF fayl!")
            log_act(uid, "conv", "img_pdf")
        else: bot.send_message(uid, "❌ Xatolik yuz berdi.")
    finally:
        shutil.rmtree(td, ignore_errors=True); UI.pop(uid,None); cst(uid)
    try: bot.delete_message(uid, pm.message_id)
    except: pass
    bot.send_message(uid, "✅ Asosiy menyu:", reply_markup=main_kb(uid))

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
        bot.send_message(uid, f"✅ {len(UI[uid])} ta rasm. /done yozing.")
    except Exception as e: logger.error(f"Photo:{e}")

@bot.message_handler(content_types=["document"])
def doc_h(msg):
    uid = msg.from_user.id; state = gst(uid); d = msg.document
    if not d: return
    if d.file_size > 20*1024*1024:
        bot.send_message(uid, "❌ Fayl juda katta (max 20MB)"); return
    fname = (d.file_name or "").lower()
    td = tempfile.mkdtemp()
    try:
        fi = bot.get_file(d.file_id); data = bot.download_file(fi.file_path)
        inp = os.path.join(td, d.file_name or "f")
        with open(inp,"wb") as f: f.write(data)

        if state == "imlo_f":
            pm = bot.send_message(uid, "⏳ Imlo tekshirilmoqda...")
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
                bot.send_message(uid, f"✅ *Tuzatildi:*\n\n{fixed[:3500]}", parse_mode="Markdown")
                log_act(uid, "imlo")
            else: bot.send_message(uid, "❌ Matn topilmadi.")
            try: bot.delete_message(uid, pm.message_id)
            except: pass
            cst(uid); bot.send_message(uid, "✅ Tayyor!", reply_markup=main_kb(uid)); return

        pm = bot.send_message(uid, "⏳ Konvertatsiya..."); ok = False
        if fname.endswith(".pdf") and state == "pdf_pptx":
            op = os.path.join(td,"r.pptx")
            if pdf2pptx(inp, op):
                with open(op,"rb") as f: bot.send_document(uid, f, caption="📊 PPTX fayl!")
                log_act(uid,"conv","pdf_pptx"); ok = True
        elif fname.endswith((".pptx",".ppt")) and state == "pptx_pdf":
            op = os.path.join(td,"r.pdf")
            if pptx2pdf(inp, op):
                with open(op,"rb") as f: bot.send_document(uid, f, caption="📄 PDF fayl!")
                log_act(uid,"conv","pptx_pdf"); ok = True
        if not ok and state not in ("imlo_f",):
            bot.send_message(uid, "❌ Noto'g'ri format.")
        cst(uid)
        try: bot.delete_message(uid, pm.message_id)
        except: pass
    except Exception as e:
        logger.error(f"Doc:{e}"); bot.send_message(uid, "❌ Xatolik yuz berdi.")
    finally: shutil.rmtree(td, ignore_errors=True)
    bot.send_message(uid, "✅ Tayyor!", reply_markup=main_kb(uid))

@bot.message_handler(func=lambda m: True)
def text_h(msg):
    uid = msg.from_user.id; text = msg.text; state = gst(uid); ud = UD.get(uid,{})

    # Broadcast
    if state == "bc" and uid == ADMIN_ID:
        cnt = 0
        for u in all_users():
            try: bot.send_message(u, text, parse_mode="Markdown"); cnt += 1
            except: pass
        bot.send_message(uid, f"✅ {cnt} ta foydalanuvchiga yuborildi!"); cst(uid); return

    # Transliteratsiya
    if state == "l2k":
        bot.send_message(uid, f"✅ Natija:\n\n`{l2k(text)}`", parse_mode="Markdown", reply_markup=main_kb(uid))
        cst(uid); return
    if state == "k2l":
        bot.send_message(uid, f"✅ Natija:\n\n`{k2l(text)}`", parse_mode="Markdown", reply_markup=main_kb(uid))
        cst(uid); return

    # Imlo tuzatish
    if state == "imlo_t":
        pm = bot.send_message(uid, "⏳ Imlo tekshirilmoqda...")
        fixed = fix_imlo(text, get_lang(uid))
        try: bot.delete_message(uid, pm.message_id)
        except: pass
        bot.send_message(uid, f"✅ *Tuzatildi:*\n\n{fixed[:3500]}", parse_mode="Markdown")
        log_act(uid,"imlo"); cst(uid); bot.send_message(uid, "✅", reply_markup=main_kb(uid)); return

    # Shaxsiy ma'lumotlar
    INFO_FIELDS = {
        "ask_name":     ("full_name",   "🏛 Universitetingiz nomini kiriting:"),
        "ask_univ":     ("university",  "📚 Fakultetingiz:"),
        "ask_faculty":  ("faculty",     "📅 Kurs (masalan: 2-kurs):"),
        "ask_year":     ("year",        "👩‍🏫 O'qituvchi ismi (ixtiyoriy, skip uchun '-'):"),
        "ask_teacher":  ("teacher",     "🏙 Shahar (ixtiyoriy, skip uchun '-'):"),
        "ask_city":     ("city",        None),
    }
    if state in INFO_FIELDS:
        field, next_question = INFO_FIELDS[state]
        val = text.strip()
        if val != "-": UD.setdefault(uid, {})[field] = val
        next_states = list(INFO_FIELDS.keys())
        idx = next_states.index(state)
        if idx < len(next_states) - 1:
            next_state = next_states[idx + 1]
            sst(uid, next_state)
            bot.send_message(uid, next_question, reply_markup=bk_kb())
        else:
            # Barcha ma'lumotlar to'landi — til tanlash
            svc = ud.get("svc","referat")
            sst(uid, f"{svc}_lang")
            bot.send_message(uid, "🌐 Qaysi tilda?", reply_markup=lc_kb(f"{svc}_lang"))
        return

    # Mavzu kiritish
    TOPIC_MAP = {
        "referat_t":"referat_p","kurs_t":"kurs_p","mustaqil_t":"mustaqil_p",
        "maqola_t":"maqola_p","prez_t":"prez_sl","test_t":"test_cnt"
    }
    if state in TOPIC_MAP:
        UD.setdefault(uid,{})["topic"] = text
        ns = TOPIC_MAP[state]; sst(uid, ns)
        if ns == "prez_sl":
            bot.send_message(uid, f"🎯 Necha slayd? (5-30)\n💰 1 slayd = {PRICE_SLIDE:,} so'm", reply_markup=bk_kb())
        elif ns == "test_cnt":
            bot.send_message(uid, f"🔢 Nechta savol? (5-50)\n💰 1 savol = {PRICE_TEST:,} so'm", reply_markup=bk_kb())
        else:
            prices = {"referat_p":PRICE_PAGE,"kurs_p":PRICE_KURS,"mustaqil_p":PRICE_MUSTAQIL,"maqola_p":PRICE_MAQOLA}
            pr = prices.get(ns, PRICE_PAGE)
            bot.send_message(uid, f"📄 Necha bet? (5-50)\n💰 1 bet = {pr:,} so'm", reply_markup=bk_kb())
        return

    # Bet soni
    PAGE_STATES = {"referat_p":"referat","kurs_p":"kurs","mustaqil_p":"mustaqil","maqola_p":"maqola"}
    if state in PAGE_STATES:
        try: pages = max(5, min(50, int(text.strip())))
        except: bot.send_message(uid, "❌ 5-50 orasida raqam kiriting"); return
        svc = PAGE_STATES[state]
        prices = {"referat":PRICE_PAGE,"kurs":PRICE_KURS,"mustaqil":PRICE_MUSTAQIL,"maqola":PRICE_MAQOLA}
        pr = prices[svc]; total = pages * pr
        UD.setdefault(uid,{}).update({"pages":pages,"svc":svc,"total":total})
        sst(uid, "ask_name")
        bot.send_message(uid,
            f"✅ {pages} bet × {pr:,} = *{total:,} so'm*\n\n"
            "👤 Ism va familiyangizni kiriting\n"
            "(Hujjat sarlavhasiga yoziladi):",
            parse_mode="Markdown", reply_markup=bk_kb()); return

    # Slayd soni
    if state == "prez_sl":
        try: slides = max(5, min(30, int(text.strip())))
        except: bot.send_message(uid, "❌ 5-30 orasida raqam kiriting"); return
        total = slides * PRICE_SLIDE
        UD.setdefault(uid,{}).update({"slides":slides,"svc":"prez","total":total})
        sst(uid, "ask_name")
        bot.send_message(uid,
            f"✅ {slides} slayd × {PRICE_SLIDE:,} = *{total:,} so'm*\n\n"
            "👤 Ism va familiyangizni kiriting:",
            parse_mode="Markdown", reply_markup=bk_kb()); return

    # Test soni
    if state == "test_cnt":
        try: count = max(5, min(50, int(text.strip())))
        except: bot.send_message(uid, "❌ 5-50 orasida raqam kiriting"); return
        total = count * PRICE_TEST
        bal = get_balance(uid)
        if bal < total:
            bot.send_message(uid,
                f"❌ *Hisobingizda mablag' yetarli emas!*\n\n"
                f"💰 Kerakli: {total:,} so'm\n"
                f"💳 Balans: {bal:,} so'm\n\n"
                f"Hisobni to'ldiring: /pay", parse_mode="Markdown"); return
        UD.setdefault(uid,{}).update({"count":count,"total":total})
        topic = ud.get("topic","")
        deduct_balance(uid, total)
        pm = bot.send_message(uid, f"⏳ {count} ta savol yaratilmoqda... ({total:,} so'm)")
        res = gen_test(topic, count, get_lang(uid))
        try: bot.delete_message(uid, pm.message_id)
        except: pass
        for i in range(0, len(res), 4000): bot.send_message(uid, res[i:i+4000])
        log_act(uid,"test",topic,total); cst(uid)
        bot.send_message(uid, f"✅ Tayyor! Balans: {get_balance(uid):,} so'm", reply_markup=main_kb(uid)); return

    # Menyu tugmalari
    MENU = {
        "📄 Referat": ("referat_t", "referat"),
        "📝 Kurs ishi": ("kurs_t", "kurs"),
        "📋 Mustaqil ish": ("mustaqil_t", "mustaqil"),
        "📰 Maqola": ("maqola_t", "maqola"),
        "📊 Prezentatsiya": ("prez_t", "prez"),
        "✅ Test": ("test_t", "test"),
    }
    if text in MENU:
        state_key, svc = MENU[text]
        sst(uid, state_key, svc=svc)
        bot.send_message(uid, f"📝 Mavzuni kiriting:", reply_markup=bk_kb()); return

    if text == "✏️ Imlo tuzatish":
        sst(uid, "imlo_t")
        bot.send_message(uid, "✏️ Matn yoki fayl yuboring (PDF/TXT):", reply_markup=bk_kb()); return

    if text == "🔄 Konvertatsiya":
        bot.send_message(uid, "🔄 Format tanlang:", reply_markup=conv_kb()); return

    if text == "💰 Balans":
        bal = get_balance(uid)
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💳 Balansni to'ldirish", callback_data="topup"))
        bot.send_message(uid,
            f"💰 *Hisobingiz*\n\n"
            f"💳 Balans: *{bal:,} so'm*\n\n"
            f"To'ldirish uchun admin bilan bog'laning:\n"
            f"{ADMIN_USERNAME}",
            parse_mode="Markdown", reply_markup=kb); return

    if text == "💝 Donat":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("🌐 Donat saytiga o'tish", url=DONATE_URL))
        bot.send_message(uid,
            f"💝 *Donat*\n\n"
            f"💳 Karta: `{DONATE_CARD}`\n"
            f"🟢 Click: `{DONATE_CLICK}`",
            parse_mode="Markdown", reply_markup=kb); return

    if text == "❓ Yordam":
        bot.send_message(uid,
            f"❓ *Narxlar:*\n"
            f"📄 Referat: {PRICE_PAGE:,} so'm/bet\n"
            f"📝 Kurs ishi: {PRICE_KURS:,} so'm/bet\n"
            f"📋 Mustaqil ish: {PRICE_MUSTAQIL:,} so'm/bet\n"
            f"📰 Maqola: {PRICE_MAQOLA:,} so'm/bet\n"
            f"📊 Prezentatsiya: {PRICE_SLIDE:,} so'm/slayd\n"
            f"✅ Test: {PRICE_TEST:,} so'm/savol\n\n"
            f"💰 Balansni to'ldirish: /pay\n"
            f"📞 Admin: {ADMIN_USERNAME}",
            parse_mode="Markdown", reply_markup=main_kb(uid)); return

    if text in ("👨‍💼 Admin", "👨\u200d💼 Admin"):
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💬 Adminga yozish",
               url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))
        bot.send_message(uid, "👨‍💼 *Admin*", parse_mode="Markdown", reply_markup=kb); return

@bot.callback_query_handler(func=lambda c: True)
def cb_h(call):
    uid = call.from_user.id; d = call.data
    bot.answer_callback_query(call.id)
    ud = UD.get(uid,{})

    if d.startswith("lang:"):
        lang = d[5:]; set_lang(uid, lang)
        bot.edit_message_text(f"✅ Til o'rnatildi!", uid, call.message.message_id)
        bot.send_message(uid, "📋 Asosiy menyu:", reply_markup=main_kb(uid))

    elif d == "bk":
        cst(uid)
        try: bot.edit_message_text("📋 Asosiy menyu:", uid, call.message.message_id)
        except: pass
        bot.send_message(uid, "📋 Asosiy menyu:", reply_markup=main_kb(uid))

    elif d == "topup":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💬 Adminga yozish",
               url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))
        bot.send_message(uid,
            f"💳 *Balansni to'ldirish*\n\n"
            f"Admin bilan bog'laning:\n{ADMIN_USERNAME}\n\n"
            f"To'lov rekvizitlari:\n"
            f"💳 Karta: `{DONATE_CARD}`\n"
            f"🟢 Click: `{DONATE_CLICK}`",
            parse_mode="Markdown", reply_markup=kb)

    # Til tanlash (hujjat uchun)
    elif "_lang:" in d:
        parts = d.split(":"); lang_code = parts[1]
        svc = parts[0].replace("_lang","")
        UD.setdefault(uid,{})["content_lang"] = lang_code
        svc2 = ud.get("svc", svc)

        if svc2 == "prez":
            sst(uid, "prez_style_wait")
            bot.edit_message_text("🎨 Prezentatsiya uslubini tanlang:",
                uid, call.message.message_id, reply_markup=style_kb())
        else:
            # Format tanlash
            sst(uid, "fmt_wait")
            bot.edit_message_text("📁 Qaysi formatda olmoqchisiz?",
                uid, call.message.message_id, reply_markup=fmt_kb(uid, "fmt"))

    elif d == "prez_style_wait" or d.startswith("st:"):
        if d.startswith("st:"):
            style = d[3:]
            UD.setdefault(uid,{})["style"] = style
            sst(uid, "prez_fmt_wait")
            bot.edit_message_text("📁 Qaysi formatda olmoqchisiz?",
                uid, call.message.message_id,
                reply_markup=fmt_kb(uid, "prez_fmt"))

    elif d.startswith("fmt:") or d.startswith("prez_fmt:"):
        fmt = d.split(":")[1]
        topic = ud.get("topic","")
        total = ud.get("total",0)
        lang_code = ud.get("content_lang", get_lang(uid))
        svc = ud.get("svc","referat")

        # Balans tekshirish
        bal = get_balance(uid)
        if bal < total:
            bot.send_message(uid,
                f"❌ *Mablag' yetarli emas!*\n\n"
                f"💰 Kerakli: {total:,} so'm\n"
                f"💳 Balans: {bal:,} so'm\n\n"
                f"Balansni to'ldirish uchun: /pay",
                parse_mode="Markdown"); return

        deduct_balance(uid, total)
        pm = bot.send_message(uid, f"⏳ Tayyorlanmoqda...\n💰 {total:,} so'm hisobingizdan ayrildi")

        try:
            if svc == "referat":
                pages = ud.get("pages",5)
                content = gen_referat(topic, pages, lang_code, ud)
                title = f"Referat: {topic}"
                log_act(uid,"referat",topic,total)
            elif svc == "kurs":
                pages = ud.get("pages",10)
                content = gen_kurs(topic, pages, lang_code, ud)
                title = f"Kurs ishi: {topic}"
                log_act(uid,"kurs",topic,total)
            elif svc == "mustaqil":
                pages = ud.get("pages",5)
                content = gen_mustaqil(topic, pages, lang_code, ud)
                title = f"Mustaqil ish: {topic}"
                log_act(uid,"mustaqil",topic,total)
            elif svc == "maqola":
                pages = ud.get("pages",5)
                content = gen_maqola(topic, pages, lang_code, ud)
                title = f"Maqola: {topic}"
                log_act(uid,"maqola",topic,total)
            elif svc == "prez":
                slides = ud.get("slides",10)
                style = ud.get("style","klassik")
                content = gen_prez(topic, slides, style, lang_code, ud)
                title = f"Prezentatsiya: {topic}"
                log_act(uid,"prez",topic,total)
                if fmt in ("docx","pdf","txt"):
                    # PPTX formatda yuborish
                    op, td2 = make_pptx(content, topic, style, ud)
                    if op and os.path.exists(op):
                        with open(op,"rb") as f:
                            bot.send_document(uid, f, caption=f"📊 {title}")
                        shutil.rmtree(td2, ignore_errors=True)
                    else:
                        send_result(uid, content, title, "txt", ud)
                    try: bot.delete_message(uid, pm.message_id)
                    except: pass
                    bal_new = get_balance(uid)
                    bot.send_message(uid, f"✅ Tayyor!\n💳 Balans: {bal_new:,} so'm", reply_markup=main_kb(uid))
                    cst(uid); return
            else:
                content = ""
                title = topic

            try: bot.delete_message(uid, pm.message_id)
            except: pass

            if not send_result(uid, content, title, fmt, ud):
                bot.send_message(uid, content[:4000])

            bal_new = get_balance(uid)
            bot.send_message(uid, f"✅ Tayyor!\n💳 Balans: {bal_new:,} so'm", reply_markup=main_kb(uid))

        except Exception as e:
            logger.error(f"Generate error: {e}")
            add_balance(uid, total)  # Xato bo'lsa pulni qaytarish
            bot.send_message(uid, "❌ Xatolik yuz berdi. Pul qaytarildi.")

        cst(uid)

    elif d.startswith("cv:"):
        t = d[3:]
        if t == "pdf": sst(uid,"pdf_pptx"); bot.edit_message_text("📎 PDF fayl yuboring:", uid, call.message.message_id, reply_markup=bk_kb())
        elif t == "pptx": sst(uid,"pptx_pdf"); bot.edit_message_text("📎 PPTX/PPT fayl yuboring:", uid, call.message.message_id, reply_markup=bk_kb())
        elif t == "img": sst(uid,"img"); UI[uid]=[]; bot.edit_message_text("🖼 Rasmlar yuboring. Tugagach /done:", uid, call.message.message_id, reply_markup=bk_kb())

    elif d == "tr:l": sst(uid,"l2k"); bot.edit_message_text("✏️ Matn yuboring:", uid, call.message.message_id, reply_markup=bk_kb())
    elif d == "tr:k": sst(uid,"k2l"); bot.edit_message_text("✏️ Matn yuboring:", uid, call.message.message_id, reply_markup=bk_kb())

if __name__ == "__main__":
    init_db()
    print("✅ EduBot v4 ishga tushdi!")
    bot.infinity_polling()
