import telebot, os, sqlite3, logging, tempfile, shutil, requests, re, math
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
UNSPLASH_KEY = os.environ.get("UNSPLASH_KEY", "")
SONNET_MODEL = "claude-sonnet-4-20250514"
HAIKU_MODEL = "claude-haiku-4-5-20251001"

def gp(n,d): return int(os.environ.get(n,str(d)))
PRICE_PAGE=gp("PRICE_PAGE",500); PRICE_KURS=gp("PRICE_KURS",700)
PRICE_MUSTAQIL=gp("PRICE_MUSTAQIL",400); PRICE_MAQOLA=gp("PRICE_MAQOLA",600)
PRICE_SLIDE=gp("PRICE_SLIDE",300); PRICE_TEST=gp("PRICE_TEST",200)
BONUS_FIRST=gp("BONUS_FIRST",3000)

logging.basicConfig(format="%(asctime)s - %(levelname)s - %(message)s",level=logging.INFO)
logger=logging.getLogger(__name__)
bot=telebot.TeleBot(BOT_TOKEN)
LN={"uz":"o'zbek","ru":"rus","en":"ingliz"}

def init_db():
    c=sqlite3.connect("edubot.db"); cur=c.cursor()
    cur.execute("""CREATE TABLE IF NOT EXISTS users(telegram_id INTEGER PRIMARY KEY,username TEXT,first_name TEXT,lang TEXT DEFAULT 'uz',balance INTEGER DEFAULT 0,joined_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS orders(telegram_id INTEGER PRIMARY KEY,state TEXT,data TEXT,updated_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS stats(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id INTEGER,action TEXT,detail TEXT,income INTEGER DEFAULT 0,created_at TEXT)""")
    cur.execute("""CREATE TABLE IF NOT EXISTS buyurtmalar(id INTEGER PRIMARY KEY AUTOINCREMENT,telegram_id INTEGER,tur TEXT,mavzu TEXT,format TEXT,sahifalar TEXT,narx INTEGER,created_at TEXT)""")
    c.commit(); c.close()

def save_order(uid, state, data):
    import json
    try:
        c=sqlite3.connect("edubot.db"); cur=c.cursor()
        cur.execute("INSERT OR REPLACE INTO orders VALUES(?,?,?,?)",
            (uid,state,json.dumps(data,ensure_ascii=False),datetime.now().strftime("%d.%m.%Y %H:%M")))
        c.commit(); c.close()
    except: pass

def load_order(uid):
    import json
    try:
        c=sqlite3.connect("edubot.db"); cur=c.cursor()
        cur.execute("SELECT state,data FROM orders WHERE telegram_id=?",(uid,))
        row=cur.fetchone(); c.close()
        if row: return row[0], json.loads(row[1])
    except: pass
    return None, {}

def clear_order(uid):
    try:
        c=sqlite3.connect("edubot.db"); cur=c.cursor()
        cur.execute("DELETE FROM orders WHERE telegram_id=?",(uid,))
        c.commit(); c.close()
    except: pass

def restore_order(uid):
    state,data=load_order(uid)
    if state and data:
        ST[uid]=state; UD[uid]=data; return True
    return False

def get_user(uid):
    c=sqlite3.connect("edubot.db"); cur=c.cursor()
    cur.execute("SELECT * FROM users WHERE telegram_id=?",(uid,))
    row=cur.fetchone(); c.close()
    return {"id":row[0],"username":row[1],"first_name":row[2],"lang":row[3],"balance":row[4]} if row else None

def reg_user(uid,uname,fname,lang="uz"):
    c=sqlite3.connect("edubot.db"); cur=c.cursor()
    cur.execute("SELECT telegram_id FROM users WHERE telegram_id=?",(uid,))
    ex=cur.fetchone()
    if not ex:
        cur.execute("INSERT INTO users VALUES(?,?,?,?,?,?)",(uid,uname,fname,lang,BONUS_FIRST,datetime.now().strftime("%d.%m.%Y %H:%M")))
        c.commit(); c.close(); return True
    cur.execute("UPDATE users SET username=?,first_name=? WHERE telegram_id=?",(uname,fname,uid))
    c.commit(); c.close(); return False

def get_lang(uid):
    u=get_user(uid); return u["lang"] if u else "uz"
def set_lang(uid,lang):
    c=sqlite3.connect("edubot.db"); cur=c.cursor()
    cur.execute("UPDATE users SET lang=? WHERE telegram_id=?",(lang,uid)); c.commit(); c.close()
def get_balance(uid):
    u=get_user(uid); return u["balance"] if u else 0
def deduct(uid,amt):
    c=sqlite3.connect("edubot.db"); cur=c.cursor()
    cur.execute("UPDATE users SET balance=balance-? WHERE telegram_id=?",(amt,uid)); c.commit(); c.close()
def add_bal(uid,amt):
    c=sqlite3.connect("edubot.db"); cur=c.cursor()
    cur.execute("UPDATE users SET balance=balance+? WHERE telegram_id=?",(amt,uid)); c.commit(); c.close()
def log_act(uid,action,detail="",income=0):
    c=sqlite3.connect("edubot.db"); cur=c.cursor()
    cur.execute("INSERT INTO stats(telegram_id,action,detail,income,created_at) VALUES(?,?,?,?,?)",(uid,action,detail,income,datetime.now().strftime("%d.%m.%Y %H:%M")))
    c.commit(); c.close()
def save_buyurtma(uid,tur,mavzu,fmt,sah,narx):
    try:
        c=sqlite3.connect("edubot.db"); cur=c.cursor()
        cur.execute("INSERT INTO buyurtmalar(telegram_id,tur,mavzu,format,sahifalar,narx,created_at) VALUES(?,?,?,?,?,?,?)",
            (uid,tur,mavzu,fmt,str(sah),narx,datetime.now().strftime("%d.%m.%Y %H:%M")))
        c.commit(); c.close()
    except: pass

def get_buyurtmalar(uid):
    try:
        c=sqlite3.connect("edubot.db"); cur=c.cursor()
        cur.execute("SELECT tur,mavzu,format,sahifalar,narx,created_at FROM buyurtmalar WHERE telegram_id=? ORDER BY id DESC LIMIT 10",(uid,))
        rows=cur.fetchall(); c.close(); return rows
    except: return []

def all_users():
    c=sqlite3.connect("edubot.db"); cur=c.cursor()
    cur.execute("SELECT telegram_id FROM users"); rows=cur.fetchall(); c.close()
    return [r[0] for r in rows]
def get_stats():
    c=sqlite3.connect("edubot.db"); cur=c.cursor()
    cur.execute("SELECT COUNT(*) FROM users"); u=cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stats WHERE action IN ('referat','kurs','mustaqil','maqola','prez','test')"); w=cur.fetchone()[0]
    cur.execute("SELECT COUNT(*) FROM stats WHERE action='conv'"); cv=cur.fetchone()[0]
    cur.execute("SELECT COALESCE(SUM(income),0) FROM stats"); i=cur.fetchone()[0]
    c.close(); return u,w,cv,i

def claude(prompt,system="",max_tok=4000,model=None):
    if not CLAUDE_API_KEY: return "Claude API sozlanmagan!"
    if model is None: model=HAIKU_MODEL
    try:
        r=requests.post("https://api.anthropic.com/v1/messages",
            headers={"x-api-key":CLAUDE_API_KEY,"anthropic-version":"2023-06-01","content-type":"application/json"},
            json={"model":model,"max_tokens":max_tok,"system":system,"messages":[{"role":"user","content":prompt}]},
            timeout=180)
        return r.json()["content"][0]["text"] if r.status_code==200 else f"API xatosi:{r.status_code}"
    except Exception as e: return f"Xatolik:{e}"

def build_info(ud):
    parts=[]
    for k,lbl in [("full_name","Muallif"),("university","Universitet"),("faculty","Fakultet"),("year","Kurs"),("teacher","O'qituvchi"),("city","Shahar")]:
        if ud.get(k): parts.append(f"{lbl}: {ud[k]}")
    return "\n".join(parts)

def gen_text(svc,topic,pages,lang,ud={}):
    ln=LN.get(lang,"o'zbek"); info=build_info(ud)
    wpg={"referat":300,"kurs":350,"mustaqil":280,"maqola":320}.get(svc,300)
    structs={
        "referat":"**KIRISH** (200+ so'z)\n**I BOB** (300+ so'z)\n**II BOB** (300+ so'z)\n**III BOB** (300+ so'z)\n**XULOSA** (150+ so'z)\n**ADABIYOTLAR** (10 ta manba)",
        "kurs":"**MUNDARIJA**\n**KIRISH** (maqsad,vazifalar,dolzarblik - 300 so'z)\n**I BOB: Nazariy asos** (400+ so'z)\n**II BOB: Tahlil** (400+ so'z)\n**III BOB: Tavsiyalar** (300+ so'z)\n**XULOSA** (200 so'z)\n**ADABIYOTLAR** (15 ta APA)\n**ILOVALAR**",
        "mustaqil":"**KIRISH** (200+ so'z)\n**ASOSIY QISM 1** (300+ so'z)\n**ASOSIY QISM 2** (300+ so'z)\n**XULOSA** (150+ so'z)\n**ADABIYOTLAR** (8 ta)",
        "maqola":"**ANNOTATSIYA** (150 so'z)\n**KALIT SO'ZLAR** (7 ta)\n**ABSTRACT** (inglizcha)\n**KEYWORDS**\n**KIRISH** (300+ so'z)\n**ADABIYOTLAR TAHLILI** (250+ so'z)\n**METODOLOGIYA** (200+ so'z)\n**NATIJALAR** (400+ so'z)\n**XULOSA** (200 so'z)\n**ADABIYOTLAR** (15 ta APA)"
    }
    struct=structs.get(svc,structs["referat"])
    names={"referat":"referat","kurs":"kurs ishi","mustaqil":"mustaqil ish","maqola":"ilmiy maqola"}
    subject_info=f"\nFan: {ud['subject']}" if ud.get('subject') else ""
    use_model=SONNET_MODEL if svc in ("kurs","maqola") else HAIKU_MODEL
    res=claude(
        f"Mavzu: {topic}\nHajm: {pages} bet ({pages*wpg}+ so'z)\n{info}{subject_info}\n\n"
        f"{ln} tilida TO'LIQ {names.get(svc,'hujjat')} yozing:\n{struct}\n\n"
        "QATIY TALABLAR:\n"
        "1. Faqat ilmiy kitoblar va tasdiqlangan manbalardan ma'lumot\n"
        "2. Har bo'limda aniq faktlar, raqamlar, foizlar bo'lsin\n"
        "3. Hech qanday **, *, #, ` belgilari ISHLATILMASIN\n"
        "4. Imlo va grammatika 100% to'g'ri\n"
        "5. Oxirida FOYDALANILGAN ADABIYOTLAR bo'limi bo'lsin",
        f"Sen {ln} tilida eng professional akademik yozuvchisan. "
        f"Faqat ilmiy manbalar. Markdown belgisi ASLO ishlatma. Imlo xatosiz.",
        4000, model=use_model)
    return clean_ai_text(res)

TEMPLATES={
    "1":{"name":"🔵 Klassik Ko'k","bg1":(30,87,179),"bg2":(0,150,255),"title":(255,255,255),"text":(220,235,255),"accent":(255,200,0)},
    "2":{"name":"🌊 Okean","bg1":(0,119,182),"bg2":(0,180,216),"title":(255,255,255),"text":(200,240,255),"accent":(144,224,239)},
    "3":{"name":"🌿 Yashil","bg1":(27,94,32),"bg2":(56,142,60),"title":(255,255,255),"text":(200,255,200),"accent":(255,235,59)},
    "4":{"name":"🌅 Quyosh","bg1":(230,81,0),"bg2":(255,152,0),"title":(255,255,255),"text":(255,240,200),"accent":(255,255,100)},
    "5":{"name":"🌸 Pushti","bg1":(136,14,79),"bg2":(233,30,99),"title":(255,255,255),"text":(255,210,230),"accent":(255,255,255)},
    "6":{"name":"🌙 Qora","bg1":(10,10,10),"bg2":(30,30,30),"title":(255,255,255),"text":(200,200,200),"accent":(0,200,255)},
    "7":{"name":"⭐ Oltin","bg1":(84,62,0),"bg2":(184,138,0),"title":(255,255,255),"text":(255,245,200),"accent":(255,215,0)},
    "8":{"name":"🔴 Qizil","bg1":(183,28,28),"bg2":(229,57,53),"title":(255,255,255),"text":(255,210,210),"accent":(255,255,255)},
    "9":{"name":"💜 Binafsha","bg1":(69,39,160),"bg2":(126,87,194),"title":(255,255,255),"text":(230,210,255),"accent":(255,200,100)},
    "10":{"name":"🤍 Oq","bg1":(245,245,245),"bg2":(255,255,255),"title":(30,30,30),"text":(60,60,60),"accent":(30,87,179)},
    "11":{"name":"🏢 Korporativ","bg1":(21,38,57),"bg2":(37,57,93),"title":(255,255,255),"text":(180,200,220),"accent":(0,180,255)},
    "12":{"name":"🎨 Kreativ","bg1":(74,0,114),"bg2":(255,0,100),"title":(255,255,255),"text":(255,200,240),"accent":(255,255,0)},
    "13":{"name":"🌍 Tabiat","bg1":(27,67,50),"bg2":(40,120,80),"title":(255,255,255),"text":(200,240,210),"accent":(255,235,59)},
    "14":{"name":"❄️ Muzli","bg1":(1,87,155),"bg2":(3,169,244),"title":(255,255,255),"text":(200,240,255),"accent":(255,255,255)},
    "15":{"name":"🔥 Olov","bg1":(100,0,0),"bg2":(200,50,0),"title":(255,255,255),"text":(255,220,200),"accent":(255,180,0)},
    "16":{"name":"🌆 Shahar","bg1":(38,50,56),"bg2":(84,110,122),"title":(255,255,255),"text":(200,215,220),"accent":(0,229,255)},
    "17":{"name":"🎓 Akademik","bg1":(62,39,35),"bg2":(109,76,65),"title":(255,255,255),"text":(255,235,220),"accent":(255,200,100)},
    "18":{"name":"💼 Biznes","bg1":(13,71,161),"bg2":(25,118,210),"title":(255,255,255),"text":(210,228,255),"accent":(255,215,0)},
    "19":{"name":"🎭 Teatr","bg1":(49,27,146),"bg2":(94,53,177),"title":(255,255,255),"text":(225,210,255),"accent":(255,235,59)},
    "20":{"name":"🏔️ Tog'","bg1":(84,110,122),"bg2":(120,144,156),"title":(255,255,255),"text":(220,230,235),"accent":(255,235,59)},
    "21":{"name":"🌺 Gul","bg1":(136,14,79),"bg2":(216,67,21),"title":(255,255,255),"text":(255,215,220),"accent":(255,255,200)},
    "22":{"name":"🔮 Sehrli","bg1":(49,27,146),"bg2":(0,131,143),"title":(255,255,255),"text":(210,240,255),"accent":(255,200,255)},
    "23":{"name":"☀️ Issiq","bg1":(230,100,0),"bg2":(255,180,0),"title":(255,255,255),"text":(255,240,200),"accent":(255,255,255)},
    "24":{"name":"🌊 Dengiz","bg1":(0,60,100),"bg2":(0,120,180),"title":(255,255,255),"text":(200,235,255),"accent":(0,229,255)},
    "25":{"name":"🦋 Kapalak","bg1":(74,20,140),"bg2":(170,0,255),"title":(255,255,255),"text":(235,200,255),"accent":(255,255,100)},
    "26":{"name":"🍃 O't","bg1":(27,94,32),"bg2":(100,180,50),"title":(255,255,255),"text":(210,245,210),"accent":(255,255,100)},
    "27":{"name":"🌙 Kecha","bg1":(5,5,30),"bg2":(20,20,60),"title":(180,180,255),"text":(150,150,200),"accent":(255,200,0)},
    "28":{"name":"🌈 Kamalak","bg1":(100,0,150),"bg2":(0,100,200),"title":(255,255,255),"text":(240,240,255),"accent":(255,255,0)},
    "29":{"name":"🏜️ Cho'l","bg1":(100,70,20),"bg2":(180,130,50),"title":(255,255,255),"text":(255,240,200),"accent":(255,200,100)},
    "30":{"name":"🎪 Sirk","bg1":(183,28,28),"bg2":(255,160,0),"title":(255,255,255),"text":(255,240,200),"accent":(255,255,255)},
    "31":{"name":"💎 Brilliant","bg1":(0,40,80),"bg2":(0,100,180),"title":(200,230,255),"text":(180,220,255),"accent":(255,215,0)},
    "32":{"name":"🌻 Kungaboqar","bg1":(200,130,0),"bg2":(255,200,0),"title":(60,40,0),"text":(80,60,10),"accent":(180,100,0)},
    "33":{"name":"🦚 Tovus","bg1":(0,77,64),"bg2":(0,150,136),"title":(255,255,255),"text":(200,240,235),"accent":(255,235,59)},
    "34":{"name":"🌃 Osmono'par","bg1":(10,10,40),"bg2":(40,40,80),"title":(100,200,255),"text":(150,180,220),"accent":(255,180,0)},
    "35":{"name":"🍒 Gilos","bg1":(120,0,30),"bg2":(200,30,60),"title":(255,255,255),"text":(255,200,210),"accent":(255,240,200)},
    "36":{"name":"🧊 Muzlik","bg1":(200,230,255),"bg2":(240,250,255),"title":(0,60,120),"text":(20,80,140),"accent":(0,120,215)},
    "37":{"name":"🌴 Tropik","bg1":(0,100,60),"bg2":(0,180,100),"title":(255,255,255),"text":(200,255,220),"accent":(255,220,0)},
    "38":{"name":"🎵 Musiqa","bg1":(20,0,40),"bg2":(80,0,120),"title":(255,150,255),"text":(200,150,220),"accent":(255,200,255)},
    "39":{"name":"🏛️ Antik","bg1":(245,235,220),"bg2":(255,248,235),"title":(80,50,20),"text":(100,70,40),"accent":(150,100,30)},
    "40":{"name":"⚡ Energiya","bg1":(0,20,60),"bg2":(0,60,120),"title":(0,200,255),"text":(150,210,255),"accent":(255,230,0)},
    "41":{"name":"🦁 Sher","bg1":(100,60,0),"bg2":(200,120,0),"title":(255,255,255),"text":(255,235,200),"accent":(255,200,100)},
    "42":{"name":"🌊 To'lqin","bg1":(0,50,100),"bg2":(0,130,200),"title":(255,255,255),"text":(200,230,255),"accent":(100,255,255)},
}

def create_slide_image(topic, slide_title, tmpl_id="1"):
    """PIL bilan mavzuga mos chiroyli rasm yaratish"""
    try:
        from PIL import Image, ImageDraw
        tmpl=TEMPLATES.get(str(tmpl_id),TEMPLATES["1"])
        c1=tmpl["bg1"]; c2=tmpl["bg2"]; acc=tmpl["accent"]
        
        w,h=800,500
        img=Image.new("RGB",(w,h),c1)
        draw=ImageDraw.Draw(img)
        
        # Gradient
        for y in range(h):
            ratio=y/h
            r=int(c1[0]*(1-ratio)+c2[0]*ratio)
            g=int(c1[1]*(1-ratio)+c2[1]*ratio)
            b=int(c1[2]*(1-ratio)+c2[2]*ratio)
            draw.line([(0,y),(w,y)],fill=(r,g,b))
        
        # Dekorativ shakllar
        draw.ellipse([w-180,-80,w+80,180],fill=(*acc,60))
        draw.ellipse([-80,h-180,180,h+80],fill=(*acc,40))
        draw.ellipse([w//2-60,h//2-60,w//2+60,h//2+60],
                     fill=(255,255,255,15))
        
        # Accent chiziq
        draw.rectangle([0,0,w,6],fill=acc)
        draw.rectangle([0,h-6,w,h],fill=acc)
        
        # Matn - slide_title
        title_short=slide_title[:35]
        # Matn markazda
        try:
            # Oddiy shrift ishlatamiz
            from PIL import ImageFont
            # Default PIL shrift
            font_big=ImageFont.load_default()
        except: pass
        
        # Matn yozing
        txt_color=tmpl["title"]
        draw.text((w//2, h//2-40), title_short, 
                  fill=txt_color, anchor="mm")
        topic_short=topic[:40]
        draw.text((w//2, h//2+20), topic_short,
                  fill=tmpl["text"], anchor="mm")
        
        # Gorizontal chiziq
        draw.rectangle([w//4, h//2-5, 3*w//4, h//2-2], fill=acc)
        
        buf=BytesIO()
        img.save(buf,"PNG")
        buf.seek(0)
        return buf
    except Exception as e:
        logger.error(f"create_slide_image: {e}")
        return None

def get_unsplash_image(query):
    """Internetdan mavzuga mos rasm olish"""
    try:
        import hashlib, time
        search_q=requests.utils.quote(query[:60])
        if UNSPLASH_KEY:
            headers={"Authorization":f"Client-ID {UNSPLASH_KEY}"}
            r=requests.get(f"https://api.unsplash.com/photos/random?query={search_q}&orientation=landscape",
                headers=headers,timeout=15)
            if r.status_code==200:
                img_url=r.json().get("urls",{}).get("regular","")
                if img_url:
                    img_r=requests.get(img_url,timeout=15)
                    if img_r.status_code==200 and len(img_r.content)>5000:
                        buf=BytesIO(img_r.content); buf.seek(0); return buf
        seed=int(hashlib.md5((query+str(time.time())).encode()).hexdigest()[:8],16)%9999
        r2=requests.get(f"https://source.unsplash.com/800x500/?{search_q}&sig={seed}",timeout=15,allow_redirects=True)
        if r2.status_code==200 and len(r2.content)>5000:
            buf2=BytesIO(r2.content); buf2.seek(0); return buf2
    except Exception as e: logger.warning(f"Unsplash xato: {e}")
    try:
        import hashlib
        seed2=int(hashlib.md5(query.encode()).hexdigest()[:8],16)%9999
        r3=requests.get(f"https://picsum.photos/seed/{seed2}/800/500",timeout=10,allow_redirects=True)
        if r3.status_code==200 and len(r3.content)>5000:
            buf3=BytesIO(r3.content); buf3.seek(0); return buf3
    except: pass
    return None

def gen_prez_content(topic, slides, tmpl_name, lang, ud={}, plans_count=5):
    ln=LN.get(lang,"o'zbek"); info=build_info(ud)
    content_slides=slides-2
    slides_per_plan=max(1,content_slides//plans_count)
    subject_info=f"\nFan: {ud['subject']}" if ud.get('subject') else ""
    result=claude(
        f"Mavzu: {topic}\nSlaydlar soni: {slides}\nUslub: {tmpl_name}\n{info}{subject_info}\n"
        f"Rejalar soni: {plans_count}\n\n"
        "MUHIM FORMAT - AYNAN SHUNDAY YOZILSIN:\n"
        "SLAYD 1: [mavzu nomi]\n"
        "[1-slayd uchun hech narsa yozma]\n"
        "SLAYD 2: REJALAR\n"
        "[rejalar ro'yxati]\n"
        "SLAYD 3: [birinchi reja sarlavhasi]\n"
        "[mazmun]\n"
        "... va hokazo\n\n"
        "QOIDALAR:\n"
        "1. Har slayd SLAYD N: bilan boshlansin - bu MAJBURIY\n"
        "2. Hech qanday **, ##, *, # belgisi ISHLATILMASIN\n"
        "3. Har slaydda 4-6 ta aniq fakt va raqam bo'lsin\n"
        "4. Faqat ilmiy kitoblardan ma'lumot\n"
        f"5. SLAYD 1: faqat mavzu nomi - boshqa hech narsa yo'q\n"
        f"6. SLAYD 2: sarlavha REJALAR - {plans_count} ta bo'lim raqamlangan\n"
        f"7. SLAYD 3-{slides-1}: har slayd o'z sarlavhasi va mazmuni\n"
        f"8. SLAYD {slides}: Xulosa va Foydalanilgan adabiyotlar\n"
        "9. INFOGRAFIKA qo'shish (1-2 ta slaydda):\n"
        "   INFOGRAFIKA: [sarlavha]: [kalit1]: [qiymat1], [kalit2]: [qiymat2]\n"
        "10. Imlo 100% to'g'ri bo'lsin\n\n"
        f"Barcha {slides} ta slaydni to'liq yoz!",
        f"Sen professional {ln} prezentatsiya mutaxassisisan. "
        f"SLAYD N: formatini qat'iy ushla. Markdown ishlatma. Imlo xatosiz.",
        4000, model=SONNET_MODEL)
    return clean_ai_text(result)

def gen_test_content(topic, count, lang, with_img=False):
    ln=LN.get(lang,"o'zbek")
    img_instruction="" if not with_img else (
        "\n\nHar 5 ta savoldan keyin:\n"
        "[RASM: mavzuga mos rasm tavsifi - 1 jumla]\n"
        "Bu rasm keyingi savollar uchun asos bo'ladi.")
    import re as re2
    res=claude(
        f"Mavzu: {topic}\nSavollar: {count}\nTil: {ln}\n\n"
        f"{count} ta professional test savoli:{img_instruction}\n\n"
        f"FORMAT:\nN. [Aniq, bir ma'noli savol]\n"
        "A) [javob]\nB) [javob]\nC) [javob]\nD) [javob]\n"
        "To'g'ri javob: [harf]\n\n"
        f"Darajalar: {count//3} oson, {count//3} o'rta, {count-2*(count//3)} qiyin\n"
        "Har bir savol oldingi savoldan farq qilsin!",
        f"Professional {ln} test yaratuvchi. Markdown belgisiz.",min(count*90,4000))
    res=re2.sub(r'\*\*(.+?)\*\*',r'\1',res)
    res=re2.sub(r'\*(.+?)\*',r'\1',res)
    return res

def clean_ai_text(text):
    import re as _re
    text = _re.sub(r'\*\*(.+?)\*\*', r'\1', text, flags=_re.DOTALL)
    text = _re.sub(r'\*(.+?)\*', r'\1', text)
    text = _re.sub(r'#{1,6}\s*', '', text)
    text = _re.sub(r'[`~]', '', text)
    text = _re.sub(r'\n{3,}', '\n\n', text)
    lines = []
    for line in text.split('\n'):
        line = line.strip()
        if not line.upper().startswith('SLAYD') and not line.upper().startswith('INFOGRAFIKA'):
            line = _re.sub(r'^[-•►▸*]+\s*', '', line)
        lines.append(line)
    return '\n'.join(lines).strip()

def fix_spell(text, lang):
    ln=LN.get(lang,"o'zbek")
    return claude(f"{ln} imlo qoidalariga muvofiq tuzat. Faqat tuzatilgan matn:\n\n{text[:2500]}",
        f"{ln} imlo mutaxassisi.",3500)

def make_pptx_pro(content, topic, tmpl_id, ud={}, user_imgs=None, img_pages=None):
    from pptx import Presentation
    from pptx.util import Inches, Pt
    from pptx.dml.color import RGBColor
    from pptx.enum.text import PP_ALIGN
    tmpl=TEMPLATES.get(str(tmpl_id),TEMPLATES["1"])
    bg1=RGBColor(*tmpl["bg1"]); bg2=RGBColor(*tmpl["bg2"])
    tc=RGBColor(*tmpl["title"]); txc=RGBColor(*tmpl["text"]); acc=RGBColor(*tmpl["accent"])
    prs=Presentation(); prs.slide_width=Inches(13.33); prs.slide_height=Inches(7.5)
    blank=prs.slide_layouts[6]
    clean=content.replace("**","").replace("## ","").replace("# ","")
    slides=[]; cur_t,cur_b=topic,[]
    for line in clean.strip().split("\n"):
        line=line.strip()
        if not line: continue
        ul=line.upper()
        is_sl=(ul.startswith("SLAYD") or ul.startswith("SLIDE") or ul.startswith("СЛАЙД")) and ":" in line
        if is_sl:
            if cur_t: slides.append((cur_t,cur_b[:]))
            cur_t=line.split(":",1)[1].strip(); cur_b=[]
        else:
            cur_b.append(line.lstrip("*•-– ▸►"))
    if cur_t: slides.append((cur_t,cur_b))
    if not slides: slides=[(topic,[clean[:200]])]
    for sn,(title,bullets) in enumerate(slides):
        sl=prs.slides.add_slide(blank)
        bg=sl.background; fill=bg.fill; fill.gradient(); fill.gradient_angle=2700000
        fill.gradient_stops[0].position=0; fill.gradient_stops[0].color.rgb=bg1
        fill.gradient_stops[1].position=1.0; fill.gradient_stops[1].color.rgb=bg2
        for cx,cy,sz in [(11.5,-0.8,3.5),(-0.8,5.5,2.5),(12.0,6.0,2.0)]:
            try:
                sh=sl.shapes.add_shape(9,Inches(cx),Inches(cy),Inches(sz),Inches(sz))
                sh.fill.solid(); sh.fill.fore_color.rgb=RGBColor(255,255,255)
                sh.fill.fore_color.transparency=0.88; sh.line.fill.background()
            except: pass
        try:
            bar=sl.shapes.add_shape(1,Inches(0),Inches(0),Inches(13.33),Inches(0.1))
            bar.fill.solid(); bar.fill.fore_color.rgb=acc; bar.line.fill.background()
        except: pass
        if sn==0:
            tb=sl.shapes.add_textbox(Inches(1),Inches(1.2),Inches(11.33),Inches(2.5))
            tf=tb.text_frame; tf.word_wrap=True
            p=tf.paragraphs[0]; p.text=topic
            p.font.size=Pt(38); p.font.bold=True; p.font.color.rgb=tc; p.alignment=PP_ALIGN.CENTER
            try:
                sep=sl.shapes.add_shape(1,Inches(3),Inches(4.0),Inches(7.33),Inches(0.06))
                sep.fill.solid(); sep.fill.fore_color.rgb=acc; sep.line.fill.background()
            except: pass
            info_lines=[]
            if ud.get("full_name"): info_lines.append(f"Muallif: {ud['full_name']}")
            if ud.get("subject"): info_lines.append(f"Fan: {ud['subject']}")
            if ud.get("university"): info_lines.append(f"Universitet: {ud['university']}")
            if ud.get("faculty"): info_lines.append(f"Fakultet: {ud['faculty']}")
            if ud.get("year"): info_lines.append(f"Kurs: {ud['year']}")
            if ud.get("teacher"): info_lines.append(f"O'qituvchi: {ud['teacher']}")
            if ud.get("city"): info_lines.append(f"Shahar: {ud['city']}")
            info_lines.append(datetime.now().strftime("%Y-yil"))
            tb2=sl.shapes.add_textbox(Inches(1),Inches(4.2),Inches(11.33),Inches(2.8))
            tf2=tb2.text_frame; tf2.word_wrap=True; first2=True
            for ln_txt in info_lines:
                p2=tf2.paragraphs[0] if first2 else tf2.add_paragraph(); first2=False
                p2.text=ln_txt; p2.font.size=Pt(18); p2.font.color.rgb=txc
                p2.alignment=PP_ALIGN.CENTER; p2.space_before=Pt(3)
        elif sn==1 and ("REJA" in title.upper() or "PLAN" in title.upper() or "MUNDARIJA" in title.upper()):
            # 2-SLAYD: REJALAR - markazda katta, chiroyli
            # Sarlavha "REJALAR"
            tb=sl.shapes.add_textbox(Inches(0.5),Inches(0.2),Inches(12.33),Inches(1.1))
            tf=tb.text_frame; tf.word_wrap=True
            p=tf.paragraphs[0]; p.text="📋  REJALAR"
            p.font.size=Pt(36); p.font.bold=True; p.font.color.rgb=tc
            p.alignment=PP_ALIGN.CENTER
            # Chiziq
            try:
                ln2=sl.shapes.add_shape(1,Inches(2),Inches(1.4),Inches(9.33),Inches(0.07))
                ln2.fill.solid(); ln2.fill.fore_color.rgb=acc; ln2.line.fill.background()
            except: pass
            # Rejalar markazda
            if bullets:
                tb2=sl.shapes.add_textbox(Inches(1.5),Inches(1.6),Inches(10.33),Inches(5.6))
                tf2=tb2.text_frame; tf2.word_wrap=True
                first=True
                for bi,b in enumerate(bullets[:12]):
                    b=b.strip()
                    if not b: continue
                    p2=tf2.paragraphs[0] if first else tf2.add_paragraph()
                    first=False
                    p2.text=f"  {bi+1}.  {b}"
                    p2.font.size=Pt(22); p2.font.bold=False
                    p2.font.color.rgb=txc; p2.space_before=Pt(8)
                    p2.alignment=PP_ALIGN.LEFT
        else:
            tb=sl.shapes.add_textbox(Inches(0.4),Inches(0.2),Inches(12.53),Inches(1.2))
            tf=tb.text_frame; tf.word_wrap=True
            p=tf.paragraphs[0]; p.text=title[:80]
            p.font.size=Pt(30); p.font.bold=True; p.font.color.rgb=tc
            try:
                ln2=sl.shapes.add_shape(1,Inches(0.4),Inches(1.55),Inches(12.53),Inches(0.07))
                ln2.fill.solid(); ln2.fill.fore_color.rgb=acc; ln2.line.fill.background()
            except: pass
            if bullets:
                has_img=img_pages and any(img_pages.get(str(i))==sn+1 for i in range(len(user_imgs or [])))
                txt_w=8.5 if has_img else 12.5
                tb2=sl.shapes.add_textbox(Inches(0.4),Inches(1.75),Inches(txt_w),Inches(5.5))
                tf2=tb2.text_frame; tf2.word_wrap=True
                first=True
                for b in bullets[:12]:
                    if not b.strip(): continue
                    p2=tf2.paragraphs[0] if first else tf2.add_paragraph(); first=False
                    p2.text=f"▸  {b.strip()}"; p2.font.size=Pt(18); p2.font.color.rgb=txc; p2.space_before=Pt(5)
            try:
                rq=sl.shapes.add_textbox(Inches(12.5),Inches(7.1),Inches(0.8),Inches(0.35))
                rq.text_frame.paragraphs[0].text=str(sn+1)
                rq.text_frame.paragraphs[0].font.size=Pt(11); rq.text_frame.paragraphs[0].font.color.rgb=acc
            except: pass
        # Foydalanuvchi rasmini qo'yish
        if user_imgs and img_pages:
            for ii,pn in img_pages.items():
                try:
                    ii_int=int(ii) if isinstance(ii,str) else ii
                    if ii_int<len(user_imgs) and pn==sn+1:
                        img_path=user_imgs[ii_int]
                        sl.shapes.add_picture(
                            img_path,
                            Inches(8.8),Inches(1.6),
                            Inches(4.2),Inches(5.4))
                        logger.info(f"User img added: slide {sn+1}")
                except Exception as e: logger.error(f"User img:{e}")
    # AI rasm: internetdan, aralash joylashuv
    ai_img_slides=ud.get("ai_img_slides",[])
    tmpl_id_for_img=str(ud.get("template_id","1"))
    if ai_img_slides:
        slide_list=list(prs.slides)
        for slide_num in ai_img_slides:
            try:
                if slide_num-1 < len(slide_list):
                    sl2=slide_list[slide_num-1]
                    slide_title=topic
                    for sh in sl2.shapes:
                        if sh.has_text_frame and sh.text_frame.paragraphs:
                            t=sh.text_frame.paragraphs[0].text.strip()
                            if t and len(t)>3 and t!=topic: slide_title=t; break
                    img_query=f"{slide_title} {topic}"[:60]
                    img_buf=get_unsplash_image(img_query)
                    if not img_buf: img_buf=create_slide_image(topic,slide_title,tmpl_id_for_img)
                    if img_buf:
                        if slide_num%2==0:
                            sl2.shapes.add_picture(img_buf,Inches(0.4),Inches(1.7),Inches(12.5),Inches(3.5))
                        else:
                            sl2.shapes.add_picture(img_buf,Inches(8.6),Inches(1.7),Inches(4.5),Inches(3.8))
                        logger.info(f"Rasm slayd {slide_num}: {img_query}")
            except Exception as ie:
                logger.error(f"AI img slide {slide_num}: {ie}")

    td=tempfile.mkdtemp(); out=os.path.join(td,"prezentatsiya.pptx")
    prs.save(out); return out,td

def make_pptx_html(content, topic, tmpl_id, ud={}):
    tmpl=TEMPLATES.get(str(tmpl_id),TEMPLATES["1"])
    bg1="#{:02x}{:02x}{:02x}".format(*tmpl["bg1"])
    bg2="#{:02x}{:02x}{:02x}".format(*tmpl["bg2"])
    th="#{:02x}{:02x}{:02x}".format(*tmpl["title"])
    tx="#{:02x}{:02x}{:02x}".format(*tmpl["text"])
    ac="#{:02x}{:02x}{:02x}".format(*tmpl["accent"])
    clean=content.replace("**","").replace("## ","").replace("# ","")
    slides=[]; cur_t,cur_b=topic,[]
    for line in clean.strip().split("\n"):
        line=line.strip()
        if not line: continue
        ul=line.upper()
        is_sl=(ul.startswith("SLAYD") or ul.startswith("SLIDE")) and ":" in line
        if is_sl:
            if cur_t: slides.append((cur_t,cur_b[:]))
            cur_t=line.split(":",1)[1].strip(); cur_b=[]
        else: cur_b.append(line.lstrip("*•-– ▸►"))
    if cur_t: slides.append((cur_t,cur_b))
    total=len(slides)
    slides_html=""
    info=build_info(ud)
    for i,(t,b) in enumerate(slides):
        bl="".join(f"<li>{x}</li>" for x in b[:10] if x.strip())
        disp="block" if i==0 else "none"
        if i==0:
            slides_html+=f"""<div class="slide" id="s{i}" style="display:{disp}"><div class="snum">{i+1}/{total}</div><div class="title-slide"><h1>{t}</h1><div class="info">{info.replace(chr(10),"<br>")}</div><p class="yr">{datetime.now().strftime("%Y-yil")}</p></div></div>"""
        else:
            slides_html+=f"""<div class="slide" id="s{i}" style="display:{disp}"><div class="snum">{i+1}/{total}</div><h2>{t}</h2><div class="aline"></div><ul>{bl}</ul></div>"""
    html=f"""<!DOCTYPE html><html><head><meta charset="UTF-8"><title>{topic}</title><style>
*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:'Segoe UI',sans-serif;background:#111;display:flex;justify-content:center;align-items:center;min-height:100vh;flex-direction:column;gap:15px}}
.slide{{background:linear-gradient(135deg,{bg1},{bg2});width:900px;max-width:98vw;aspect-ratio:16/9;border-radius:12px;padding:45px 55px;position:relative;overflow:hidden;box-shadow:0 20px 60px rgba(0,0,0,.5)}}
.slide::before{{content:'';position:absolute;right:-70px;top:-70px;width:280px;height:280px;border-radius:50%;background:rgba(255,255,255,.07)}}
.snum{{position:absolute;bottom:18px;right:25px;color:{ac};font-size:13px;opacity:.8}}
.title-slide{{display:flex;flex-direction:column;justify-content:center;align-items:center;height:100%;text-align:center}}
.title-slide h1{{color:{th};font-size:42px;font-weight:800;line-height:1.2;margin-bottom:25px}}
.info{{color:{tx};font-size:18px;line-height:1.9;opacity:.9;margin-bottom:15px}}
.yr{{color:{ac};font-size:17px;font-weight:600}}
h2{{color:{th};font-size:28px;font-weight:700;margin-bottom:8px}}
.aline{{width:70px;height:4px;background:{ac};border-radius:2px;margin:12px 0 22px}}
ul{{list-style:none;color:{tx}}}li{{font-size:19px;line-height:1.65;margin-bottom:11px;padding-left:22px;position:relative}}li::before{{content:'▸';position:absolute;left:0;color:{ac}}}
.ctrl{{display:flex;gap:15px;align-items:center}}.btn{{background:rgba(255,255,255,.15);color:white;border:2px solid {ac};padding:10px 28px;border-radius:25px;cursor:pointer;font-size:15px;font-weight:600;transition:.3s}}.btn:hover{{background:{ac};color:#000}}
.prog-wrap{{width:900px;max-width:98vw;background:rgba(255,255,255,.2);height:4px;border-radius:2px}}.prog{{height:100%;background:{ac};border-radius:2px;transition:.3s}}
</style></head><body>
{slides_html}
<div class="ctrl"><button class="btn" onclick="prev()">◀ Oldingi</button><span style="color:white;font-size:15px" id="cnt">1/{total}</span><button class="btn" onclick="next()">Keyingi ▶</button></div>
<div class="prog-wrap"><div class="prog" id="prog" style="width:{100//total if total else 100}%"></div></div>
<script>let c=0,t={total};function show(n){{document.querySelectorAll(".slide").forEach((s,i)=>s.style.display=i===n?"block":"none");document.getElementById("cnt").textContent=(n+1)+"/"+t;document.getElementById("prog").style.width=((n+1)/t*100)+"%"}}function next(){{if(c<t-1){{c++;show(c)}}}}function prev(){{if(c>0){{c--;show(c)}}}}document.addEventListener("keydown",e=>{{if(e.key==="ArrowRight")next();if(e.key==="ArrowLeft")prev()}});</script>
</body></html>"""
    td=tempfile.mkdtemp(); out=os.path.join(td,"prezentatsiya.html")
    with open(out,"w",encoding="utf-8") as f: f.write(html)
    return out,td

def make_docx(content, title, ud={}):
    try:
        from docx import Document; from docx.shared import Pt,Cm; from docx.enum.text import WD_ALIGN_PARAGRAPH
        doc=Document(); style=doc.styles["Normal"]; style.font.name="Times New Roman"; style.font.size=Pt(14)
        sec=doc.sections[0]; sec.page_height=Cm(29.7); sec.page_width=Cm(21)
        sec.left_margin=Cm(3); sec.right_margin=Cm(1.5); sec.top_margin=Cm(2); sec.bottom_margin=Cm(2)
        if ud.get("university"): p=doc.add_paragraph(ud["university"]); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.runs[0].font.size=Pt(14)
        if ud.get("faculty"): p=doc.add_paragraph(ud["faculty"]); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        doc.add_paragraph()
        p=doc.add_paragraph(title); p.alignment=WD_ALIGN_PARAGRAPH.CENTER; p.runs[0].font.size=Pt(16); p.runs[0].font.bold=True
        doc.add_paragraph()
        if ud.get("full_name"): p=doc.add_paragraph(f"Muallif: {ud['full_name']}"); p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
        if ud.get("teacher"): p=doc.add_paragraph(f"O'qituvchi: {ud['teacher']}"); p.alignment=WD_ALIGN_PARAGRAPH.RIGHT
        if ud.get("city"): p=doc.add_paragraph(f"{ud['city']}, {datetime.now().year}"); p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        doc.add_page_break()
        for line in content.split("\n"):
            line=line.strip()
            if not line: doc.add_paragraph(); continue
            cl=line.strip("*").strip()
            if line.startswith("**") and line.endswith("**"):
                p=doc.add_paragraph(cl); p.runs[0].font.bold=True; p.runs[0].font.size=Pt(14)
            else:
                p=doc.add_paragraph(cl); p.paragraph_format.first_line_indent=Cm(1.25)
        td=tempfile.mkdtemp(); out=os.path.join(td,"dokument.docx"); doc.save(out); return out,td
    except Exception as e: logger.error(f"DOCX:{e}"); return None,None

def make_pdf_simple(content, title, ud={}):
    try:
        from reportlab.pdfgen import canvas; from reportlab.lib.pagesizes import A4; from reportlab.lib.units import cm
        td=tempfile.mkdtemp(); out=os.path.join(td,"dokument.pdf")
        c=canvas.Canvas(out,pagesize=A4); w,h=A4; mg=2*cm; y=h-mg
        def nl(): 
            nonlocal y; c.showPage(); y=h-mg
        def wl(text,bold=False,size=12,indent=0):
            nonlocal y
            if y<mg+cm: nl()
            c.setFont("Helvetica-Bold" if bold else "Helvetica",size)
            words=text.split(); line=""
            mw=w-2*mg-indent
            for word in words:
                test=line+" "+word if line else word
                if c.stringWidth(test,"Helvetica",size)<mw: line=test
                else:
                    c.drawString(mg+indent,y,line); y-=size+4
                    if y<mg: nl()
                    line=word
            if line: c.drawString(mg+indent,y,line); y-=size+6
        if ud.get("university"): wl(ud["university"],bold=True,size=14)
        wl(title,bold=True,size=16); y-=cm
        for line in content.split("\n"):
            line=line.strip()
            if not line: y-=8; continue
            is_h=line.startswith("**") and line.endswith("**")
            wl(line.strip("*"),bold=is_h,size=13 if is_h else 12,indent=0 if is_h else 20)
        c.save(); return out,td
    except Exception as e: logger.error(f"PDF:{e}"); return None,None

def pdf2pptx(pdf,out):
    try:
        import fitz
        from pptx import Presentation
        from pptx.util import Inches
        prs=Presentation(); prs.slide_width=Inches(10); prs.slide_height=Inches(7.5)
        blank=prs.slide_layouts[6]
        doc=fitz.open(pdf)
        for page in doc:
            pix=page.get_pixmap(matrix=fitz.Matrix(1.5,1.5))
            img_b=BytesIO(pix.tobytes("png"))
            sl=prs.slides.add_slide(blank)
            sl.shapes.add_picture(img_b,0,0,prs.slide_width,prs.slide_height)
        doc.close(); prs.save(out)
        logger.info(f"pdf2pptx OK: {out}")
        return True
    except Exception as e:
        logger.error(f"pdf2pptx error: {e}")
        return False

def pptx2pdf(pptx,out):
    """PPTX slaydlarni rasm orqali PDF ga aylantirish"""
    try:
        from pptx import Presentation
        from pptx.util import Inches
        from reportlab.pdfgen import canvas as rl_canvas
        from PIL import Image, ImageDraw
        
        prs=Presentation(pptx)
        w_pt=float(prs.slide_width)/914400*72
        h_pt=float(prs.slide_height)/914400*72
        px_w=int(float(prs.slide_width)/914400*120)
        px_h=int(float(prs.slide_height)/914400*120)
        
        c=rl_canvas.Canvas(out,pagesize=(w_pt,h_pt))
        td3=tempfile.mkdtemp()
        
        for i,slide in enumerate(prs.slides):
            img=Image.new("RGB",(px_w,px_h),(255,255,255))
            draw=ImageDraw.Draw(img)
            
            for shape in slide.shapes:
                try:
                    if shape.has_text_frame:
                        left=max(0,int(shape.left/914400*120)) if shape.left else 10
                        top=max(0,int(shape.top/914400*120)) if shape.top else 10
                        for para in shape.text_frame.paragraphs:
                            txt=" ".join(r.text for r in para.runs).strip()
                            if txt:
                                draw.text((left,top),txt[:80],fill=(0,0,0))
                                top+=20
                except: pass
            
            tp=os.path.join(td3,f"s{i}.png")
            img.save(tp,"PNG")
            c.drawImage(tp,0,0,w_pt,h_pt)
            c.showPage()
        
        c.save()
        shutil.rmtree(td3,ignore_errors=True)
        logger.info(f"pptx2pdf OK: {len(prs.slides)} slides")
        return True
    except Exception as e:
        logger.error(f"pptx2pdf error: {e}")
        return False

def imgs2pdf(imgs,out):
    try:
        from reportlab.pdfgen import canvas; from reportlab.lib.pagesizes import A4; from PIL import Image
        c=canvas.Canvas(out,pagesize=A4); aw,ah=A4
        for p in imgs:
            img=Image.open(p); iw,ih=img.size; r=min(aw/iw,ah/ih)
            nw,nh=iw*r,ih*r; c.drawImage(p,(aw-nw)/2,(ah-nh)/2,nw,nh); c.showPage()
        c.save(); return True
    except Exception as e: logger.error(f"imgs2pdf:{e}"); return False

L2K={"o'":"ў","O'":"Ў","g'":"ғ","G'":"Ғ","sh":"ш","Sh":"Ш","ch":"ч","Ch":"Ч","ng":"нг","a":"а","A":"А","b":"б","B":"Б","d":"д","D":"Д","e":"е","E":"Е","f":"ф","F":"Ф","g":"г","G":"Г","h":"ҳ","H":"Ҳ","i":"и","I":"И","j":"ж","J":"Ж","k":"к","K":"К","l":"л","L":"Л","m":"м","M":"М","n":"н","N":"Н","o":"о","O":"О","p":"п","P":"П","q":"қ","Q":"Қ","r":"р","R":"Р","s":"с","S":"С","t":"т","T":"Т","u":"у","U":"У","v":"в","V":"В","x":"х","X":"Х","y":"й","Y":"Й","z":"з","Z":"З"}
K2L={"ў":"o'","Ў":"O'","ғ":"g'","Ғ":"G'","ш":"sh","Ш":"Sh","ч":"ch","Ч":"Ch","нг":"ng","а":"a","А":"A","б":"b","Б":"B","д":"d","Д":"D","е":"e","Е":"E","ф":"f","Ф":"F","г":"g","Г":"G","ҳ":"h","Ҳ":"H","и":"i","И":"I","й":"y","Й":"Y","ж":"j","Ж":"J","к":"k","К":"K","қ":"q","Қ":"Q","л":"l","Л":"L","м":"m","М":"M","н":"n","Н":"N","о":"o","О":"O","п":"p","П":"P","р":"r","Р":"R","с":"s","С":"S","т":"t","Т":"T","у":"u","У":"U","в":"v","В":"V","х":"x","Х":"X","з":"z","З":"Z","я":"ya","Я":"Ya","ю":"yu","Ю":"Yu","ё":"yo","Ё":"Yo","ъ":"","ь":"","ц":"ts","щ":"sh"}
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

ST,UD,UI,HIST={},{},{},{}
def sst(uid,s,**kw):
    ST[uid]=s; UD.setdefault(uid,{}).update(kw)
    try: save_order(uid,s,UD.get(uid,{}))
    except: pass
def gst(uid): return ST.get(uid)
def cst(uid):
    ST.pop(uid,None); clear_order(uid)

INFO_STEPS=[
    ("ask_name","full_name","👤 Ism va familiyangizni kiriting:",True),
    ("ask_univ","university","🏛 Universitetingiz nomi:",True),
    ("ask_faculty","faculty","📚 Fakultetingiz:",False),
    ("ask_year","year","📅 Nechinchi kurs?:",False),
    ("ask_teacher","teacher","👩‍🏫 O'qituvchi ismi:",False),
    ("ask_subject","subject","📖 Fan nomi (masalan: Iqtisodiyot):",False),
    ("ask_city","city","🏙 Shahar:",False),
]
INFO_STATES=[s[0] for s in INFO_STEPS]

def finish_info(uid,ud):
    svc=ud.get("svc","referat")
    if svc=="prez": show_templates(uid,1)
    else:
        sst(uid,f"{svc}_lang")
        bot.send_message(uid,"🌐 Qaysi tilda?",reply_markup=lc_kb(f"{svc}_lang"))

def show_templates(uid,page):
    per=10; total=len(TEMPLATES); pages=math.ceil(total/per)
    start=(page-1)*per; end=min(start+per,total)
    keys=list(TEMPLATES.keys())[start:end]
    kb=types.InlineKeyboardMarkup(row_width=2)
    for k in keys: kb.add(types.InlineKeyboardButton(TEMPLATES[k]["name"],callback_data=f"tmpl:{k}"))
    nav=[]
    if page>1: nav.append(types.InlineKeyboardButton("◀",callback_data=f"tpg:{page-1}"))
    nav.append(types.InlineKeyboardButton(f"{page}/{pages}",callback_data="noop"))
    if page<pages: nav.append(types.InlineKeyboardButton("▶",callback_data=f"tpg:{page+1}"))
    if nav: kb.row(*nav)
    bot.send_message(uid,f"🎨 *Shablon tanlang* ({total} ta)\nSahifa {page}/{pages}:",parse_mode="Markdown",reply_markup=kb)

def lang_kb():
    kb=types.InlineKeyboardMarkup(row_width=3)
    kb.add(types.InlineKeyboardButton("🇺🇿 O'zbek",callback_data="lang:uz"),
           types.InlineKeyboardButton("🇷🇺 Русский",callback_data="lang:ru"),
           types.InlineKeyboardButton("🇬🇧 English",callback_data="lang:en"))
    return kb
def main_kb(uid):
    kb=types.ReplyKeyboardMarkup(resize_keyboard=True)
    kb.row("📄 Referat","📝 Kurs ishi")
    kb.row("📋 Mustaqil ish","📰 Maqola")
    kb.row("📊 Prezentatsiya","✅ Test")
    kb.row("✏️ Imlo tuzatish","🔄 Konvertatsiya")
    kb.row("💰 Balans","📦 Buyurtmalarim")
    kb.row("💝 Donat","❓ Yordam")
    kb.add("👨‍💼 Admin")
    return kb
def fmt_kb(prefix):
    kb=types.InlineKeyboardMarkup(row_width=3)
    kb.add(types.InlineKeyboardButton("📝 DOCX",callback_data=f"{prefix}:docx"),
           types.InlineKeyboardButton("📄 PDF",callback_data=f"{prefix}:pdf"),
           types.InlineKeyboardButton("📱 Matn",callback_data=f"{prefix}:txt"))
    return kb
def prez_fmt_kb():
    kb=types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton("📊 PPTX (PowerPoint)",callback_data="pfmt:pptx"),
           types.InlineKeyboardButton("🌐 HTML (Interaktiv brauzer)",callback_data="pfmt:html"),
           types.InlineKeyboardButton("📦 Ikkalasi ham",callback_data="pfmt:both"))
    return kb
def conv_kb():
    kb=types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📄➡️📊 PDF → PPTX",callback_data="cv:pdf"))
    kb.add(types.InlineKeyboardButton("📊➡️📄 PPTX → PDF",callback_data="cv:pptx"))
    kb.add(types.InlineKeyboardButton("🖼➡️📄 Rasmlar → PDF",callback_data="cv:img"))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga",callback_data="bk"))
    return kb
def lc_kb(prefix):
    kb=types.InlineKeyboardMarkup(row_width=3)
    kb.add(types.InlineKeyboardButton("🇺🇿 O'zbek",callback_data=f"{prefix}:uz"),
           types.InlineKeyboardButton("🇷🇺 Rus",callback_data=f"{prefix}:ru"),
           types.InlineKeyboardButton("🇬🇧 Ingliz",callback_data=f"{prefix}:en"))
    return kb
def bk_kb():
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("◀️ Orqaga",callback_data="back_step"),
           types.InlineKeyboardButton("🏠 Menyu",callback_data="bk"))
    return kb

def slides_count_kb():
    """Prezentatsiya slayd soni tugmalari"""
    kb=types.InlineKeyboardMarkup(row_width=3)
    counts=[10,15,20,25,30,35,40,50]
    btns=[types.InlineKeyboardButton(
        f"{n} slayd\n{n*PRICE_SLIDE:,} so'm",
        callback_data=f"slides:{n}") for n in counts]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("✏️ O'zim yozaman",callback_data="slides:custom"))
    kb.add(types.InlineKeyboardButton("🏠 Asosiy menyu",callback_data="bk"))
    return kb

def test_count_kb():
    """Test savol soni tugmalari"""
    kb=types.InlineKeyboardMarkup(row_width=3)
    counts=[10,20,30,50,100,200,500,1000]
    btns=[types.InlineKeyboardButton(
        f"{n} ta\n{n*PRICE_TEST:,} so'm",
        callback_data=f"tcount:{n}") for n in counts]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("✏️ O'zim yozaman",callback_data="tcount:custom"))
    kb.add(types.InlineKeyboardButton("🏠 Asosiy menyu",callback_data="bk"))
    return kb

def plans_count_kb():
    """Reja soni tugmalari"""
    kb=types.InlineKeyboardMarkup(row_width=4)
    for n in [3,4,5,6,7,8,10,12]:
        kb.add(types.InlineKeyboardButton(f"{n} ta reja",callback_data=f"plans:{n}"))
    kb.add(types.InlineKeyboardButton("✏️ O'zim yozaman",callback_data="plans:custom"))
    kb.add(types.InlineKeyboardButton("🏠 Asosiy menyu",callback_data="bk"))
    return kb

def prez_img_slide_kb(slide_count):
    """Qaysi slaydga rasm qo'yish"""
    kb=types.InlineKeyboardMarkup(row_width=5)
    btns=[types.InlineKeyboardButton(str(i),callback_data=f"ipage:0:{i}") 
          for i in range(1,min(slide_count+1,16))]
    kb.add(*btns)
    kb.add(types.InlineKeyboardButton("✅ Davom etish",callback_data="img_done"))
    kb.add(types.InlineKeyboardButton("🏠 Asosiy menyu",callback_data="bk"))
    return kb
def skip_kb(ns):
    kb=types.InlineKeyboardMarkup(row_width=2)
    kb.add(types.InlineKeyboardButton("⏭ O'tkazib yuborish",callback_data=f"skip:{ns}"),
           types.InlineKeyboardButton("🔙 Orqaga",callback_data="bk"))
    kb.add(types.InlineKeyboardButton("🏠 Asosiy menyu",callback_data="bk"))
    return kb

@bot.message_handler(commands=["start"])
def start(msg):
    uid=msg.from_user.id; uname=msg.from_user.username or ""; fname=msg.from_user.first_name or ""
    is_new=reg_user(uid,uname,fname)
    txt=(f"👋 Xush kelibsiz, {fname}!\n\n🎓 *EduBot* — Ta'lim yordamchingiz!\n\n"
         "📚 Xizmatlar:\n• 📄 Referat  • 📝 Kurs ishi\n• 📋 Mustaqil ish  • 📰 Maqola\n"
         "• 📊 Prezentatsiya (42 shablon!)\n• ✅ Test (10-1000 ta savol)\n"
         "• ✏️ Imlo tuzatish  • 🔄 Konvertatsiya\n\n")
    if is_new: txt+=f"🎁 *{BONUS_FIRST:,} so'm bonus berildi!*\n\n"
    txt+="Tilni tanlang:"
    bot.send_message(uid,txt,parse_mode="Markdown",reply_markup=lang_kb())
    if is_new:
        try: bot.send_message(ADMIN_ID,f"🆕 Yangi: {fname} (@{uname}) | {uid}")
        except: pass

@bot.message_handler(commands=["stats"])
def stats_cmd(msg):
    if msg.from_user.id!=ADMIN_ID: return
    u,w,c,i=get_stats()
    bot.send_message(msg.chat.id,f"📊 *Statistika*\n\n👥 Foydalanuvchilar: {u}\n📝 Ishlar: {w}\n🔄 Konvertatsiyalar: {c}\n💰 Daromad: {i:,} so'm",parse_mode="Markdown")

@bot.message_handler(commands=["broadcast"])
def bc_cmd(msg):
    if msg.from_user.id!=ADMIN_ID: return
    sst(msg.from_user.id,"bc"); bot.send_message(msg.chat.id,"📢 Xabar matnini yozing:")

@bot.message_handler(commands=["addbalance"])
def abal_cmd(msg):
    if msg.from_user.id!=ADMIN_ID: return
    try:
        p=msg.text.split(); tid=int(p[1]); amt=int(p[2])
        add_bal(tid,amt); bot.send_message(msg.chat.id,f"✅ {tid} ga {amt:,} so'm qo'shildi!")
        bot.send_message(tid,f"💰 Hisobingizga {amt:,} so'm qo'shildi!\nBalans: {get_balance(tid):,} so'm")
    except: bot.send_message(msg.chat.id,"❌ /addbalance [id] [summa]")

@bot.message_handler(commands=["done"])
def done_cmd(msg):
    uid=msg.from_user.id; imgs=UI.get(uid,[])
    if not imgs: return
    pm=bot.send_message(uid,"⏳ PDF yaratilmoqda...")
    td=tempfile.mkdtemp()
    try:
        out=os.path.join(td,"r.pdf")
        if imgs2pdf(imgs,out):
            with open(out,"rb") as f: bot.send_document(uid,f,caption="📄 PDF fayl!")
            log_act(uid,"conv","img_pdf")
        else: bot.send_message(uid,"❌ Xatolik.")
    finally:
        shutil.rmtree(td,ignore_errors=True); UI.pop(uid,None); cst(uid)
    try: bot.delete_message(uid,pm.message_id)
    except: pass
    bot.send_message(uid,"✅",reply_markup=main_kb(uid))


@bot.message_handler(commands=["referat"])
def cmd_referat(msg):
    uid=msg.from_user.id; reg_user(uid,msg.from_user.username or "",msg.from_user.first_name or "")
    sst(uid,"referat_t",svc="referat"); bot.send_message(uid,"📄 Mavzuni kiriting:",reply_markup=bk_kb())

@bot.message_handler(commands=["kursishi"])
def cmd_kurs(msg):
    uid=msg.from_user.id; reg_user(uid,msg.from_user.username or "",msg.from_user.first_name or "")
    sst(uid,"kurs_t",svc="kurs"); bot.send_message(uid,"📝 Mavzuni kiriting:",reply_markup=bk_kb())

@bot.message_handler(commands=["mustaqilish"])
def cmd_mustaqil(msg):
    uid=msg.from_user.id; reg_user(uid,msg.from_user.username or "",msg.from_user.first_name or "")
    sst(uid,"mustaqil_t",svc="mustaqil"); bot.send_message(uid,"📋 Mavzuni kiriting:",reply_markup=bk_kb())

@bot.message_handler(commands=["maqola"])
def cmd_maqola(msg):
    uid=msg.from_user.id; reg_user(uid,msg.from_user.username or "",msg.from_user.first_name or "")
    sst(uid,"maqola_t",svc="maqola"); bot.send_message(uid,"📰 Mavzuni kiriting:",reply_markup=bk_kb())

@bot.message_handler(commands=["prezentatsiya"])
def cmd_prez(msg):
    uid=msg.from_user.id; reg_user(uid,msg.from_user.username or "",msg.from_user.first_name or "")
    sst(uid,"prez_t",svc="prez"); bot.send_message(uid,"📊 Mavzuni kiriting:",reply_markup=bk_kb())

@bot.message_handler(commands=["test"])
def cmd_test(msg):
    uid=msg.from_user.id; reg_user(uid,msg.from_user.username or "",msg.from_user.first_name or "")
    sst(uid,"test_t",svc="test"); bot.send_message(uid,"✅ Mavzuni kiriting:",reply_markup=bk_kb())

@bot.message_handler(commands=["imlo"])
def cmd_imlo(msg):
    uid=msg.from_user.id; reg_user(uid,msg.from_user.username or "",msg.from_user.first_name or "")
    sst(uid,"imlo_t")
    kb2=types.InlineKeyboardMarkup()
    kb2.add(types.InlineKeyboardButton("📁 Fayl yuborish",callback_data="imlo_file"))
    bot.send_message(uid,"✏️ Matnni yozing:",reply_markup=kb2)

@bot.message_handler(commands=["konvertatsiya"])
def cmd_conv(msg):
    uid=msg.from_user.id; reg_user(uid,msg.from_user.username or "",msg.from_user.first_name or "")
    bot.send_message(uid,"🔄 Format tanlang:",reply_markup=conv_kb())

@bot.message_handler(commands=["balans"])
def cmd_balans(msg):
    uid=msg.from_user.id; reg_user(uid,msg.from_user.username or "",msg.from_user.first_name or "")
    bal=get_balance(uid); kb2=types.InlineKeyboardMarkup()
    kb2.add(types.InlineKeyboardButton("💳 Balans to'ldirish",callback_data="topup"))
    bot.send_message(uid,f"💰 *Balansingiz: {bal:,} so'm*",parse_mode="Markdown",reply_markup=kb2)

@bot.message_handler(commands=["yordam","help"])
def cmd_help(msg):
    uid=msg.from_user.id
    bot.send_message(uid,
        f"❓ *Buyruqlar:*\n/referat /kursishi /mustaqilish /maqola\n"
        f"/prezentatsiya /test /imlo /konvertatsiya /balans\n\n"
        f"💵 *Narxlar:*\n📄 {PRICE_PAGE:,}/bet | 📝 {PRICE_KURS:,}/bet\n"
        f"📋 {PRICE_MUSTAQIL:,}/bet | 📰 {PRICE_MAQOLA:,}/bet\n"
        f"📊 {PRICE_SLIDE:,}/slayd | ✅ {PRICE_TEST:,}/savol",
        parse_mode="Markdown",reply_markup=main_kb(uid))

@bot.message_handler(commands=["menu"])
def cmd_menu(msg):
    uid=msg.from_user.id; reg_user(uid,msg.from_user.username or "",msg.from_user.first_name or "")
    bot.send_message(uid,"📋 Asosiy menyu:",reply_markup=main_kb(uid))

@bot.message_handler(content_types=["photo"])
def photo_h(msg):
    uid=msg.from_user.id; state=gst(uid); ph=msg.photo[-1]
    td=tempfile.mkdtemp()
    try:
        fi=bot.get_file(ph.file_id); data=bot.download_file(fi.file_path)
        p=os.path.join(td,f"img_{uid}_{len(UI.get(uid,[]))}.jpg")
        with open(p,"wb") as f: f.write(data)
        if state=="img":
            UI.setdefault(uid,[]).append(p); bot.send_message(uid,f"✅ {len(UI[uid])} ta rasm. /done yozing.")
        elif state and "wait_img" in state:
            UI.setdefault(uid,[]).append(p); n=len(UI[uid])-1
            pkb=types.InlineKeyboardMarkup(row_width=5)
            btns=[types.InlineKeyboardButton(str(i),callback_data=f"ipage:{n}:{i}") for i in range(1,16)]
            pkb.add(*btns); pkb.add(types.InlineKeyboardButton("✅ Davom etish",callback_data="img_done"))
            bot.send_message(uid,"🖼 Rasm qabul qilindi! Qaysi slaydga qo'ymoqchisiz?",reply_markup=pkb)
        else: bot.send_message(uid,"❌ Hozir rasm kutilmayapti.")
    except Exception as e: logger.error(f"Photo:{e}")

@bot.message_handler(content_types=["document"])
def doc_h(msg):
    uid=msg.from_user.id; state=gst(uid); d=msg.document
    if not d: return
    if d.file_size>20*1024*1024: bot.send_message(uid,"❌ Fayl juda katta (max 20MB)"); return
    fname=(d.file_name or "").lower(); td=tempfile.mkdtemp()
    try:
        fi=bot.get_file(d.file_id); data=bot.download_file(fi.file_path)
        inp=os.path.join(td,d.file_name or "f")
        with open(inp,"wb") as f: f.write(data)
        if state=="imlo_f":
            pm=bot.send_message(uid,"⏳ Imlo tekshirilmoqda...")
            txt=""
            if fname.endswith(".txt"):
                with open(inp,"r",encoding="utf-8",errors="ignore") as f: txt=f.read()
            elif fname.endswith(".pdf"):
                try:
                    import fitz; d2=fitz.open(inp); txt=" ".join(pg.get_text() for pg in d2)
                except: pass
            if txt:
                fixed=fix_spell(txt,get_lang(uid)); fc=clean_ai_text(fixed)
                try: bot.delete_message(uid,pm.message_id)
                except: pass
                if fname.endswith(".pdf"):
                    op,td3=make_pdf_simple(fc,"Tuzatilgan matn",{})
                    if op:
                        with open(op,"rb") as f2: bot.send_document(uid,f2,caption="✅ Imlo tuzatildi (PDF)")
                        shutil.rmtree(td3,ignore_errors=True)
                    else: bot.send_message(uid,f"✅ Tuzatildi:\n\n{fc[:3500]}")
                elif fname.endswith(".docx"):
                    op,td3=make_docx(fc,"Tuzatilgan matn",{})
                    if op:
                        with open(op,"rb") as f2: bot.send_document(uid,f2,caption="✅ Imlo tuzatildi (DOCX)")
                        shutil.rmtree(td3,ignore_errors=True)
                    else: bot.send_message(uid,f"✅ Tuzatildi:\n\n{fc[:3500]}")
                else: bot.send_message(uid,f"✅ *Tuzatildi:*\n\n{fc[:3500]}",parse_mode="Markdown")
            else:
                try: bot.delete_message(uid,pm.message_id)
                except: pass
                bot.send_message(uid,"❌ Matn topilmadi.")
            cst(uid); bot.send_message(uid,"✅",reply_markup=main_kb(uid)); return
        pm=bot.send_message(uid,"⏳ Konvertatsiya..."); ok=False
        if fname.endswith(".pdf") and state=="pdf_pptx":
            op=os.path.join(td,"r.pptx")
            if pdf2pptx(inp,op):
                with open(op,"rb") as f: bot.send_document(uid,f,caption="📊 PPTX!")
                log_act(uid,"conv","pdf_pptx"); ok=True
        elif fname.endswith((".pptx",".ppt")) and state=="pptx_pdf":
            op=os.path.join(td,"r.pdf")
            if pptx2pdf(inp,op):
                with open(op,"rb") as f: bot.send_document(uid,f,caption="📄 PDF!")
                log_act(uid,"conv","pptx_pdf"); ok=True
        if not ok: bot.send_message(uid,"❌ Noto'g'ri format.")
        cst(uid)
        try: bot.delete_message(uid,pm.message_id)
        except: pass
    except Exception as e: logger.error(f"Doc:{e}"); bot.send_message(uid,"❌ Xatolik.")
    finally: shutil.rmtree(td,ignore_errors=True)
    bot.send_message(uid,"✅",reply_markup=main_kb(uid))

@bot.message_handler(func=lambda m: True)
def text_h(msg):
    uid=msg.from_user.id; text=msg.text; state=gst(uid); ud=UD.get(uid,{})

    if state=="bc" and uid==ADMIN_ID:
        cnt=0
        for u in all_users():
            try: bot.send_message(u,text,parse_mode="Markdown"); cnt+=1
            except: pass
        bot.send_message(uid,f"✅ {cnt} ta foydalanuvchiga yuborildi!"); cst(uid); return

    if state=="l2k": bot.send_message(uid,f"✅ Natija:\n\n`{l2k(text)}`",parse_mode="Markdown",reply_markup=main_kb(uid)); cst(uid); return
    if state=="k2l": bot.send_message(uid,f"✅ Natija:\n\n`{k2l(text)}`",parse_mode="Markdown",reply_markup=main_kb(uid)); cst(uid); return

    if state=="imlo_t":
        pm=bot.send_message(uid,"⏳ Imlo tekshirilmoqda...")
        fixed=fix_spell(text,get_lang(uid))
        try: bot.delete_message(uid,pm.message_id)
        except: pass
        bot.send_message(uid,f"✅ *Tuzatildi:*\n\n{fixed[:3500]}",parse_mode="Markdown")
        log_act(uid,"imlo"); cst(uid); bot.send_message(uid,"✅",reply_markup=main_kb(uid)); return

    if state in INFO_STATES:
        idx=INFO_STATES.index(state); _,field,_,_=INFO_STEPS[idx]
        val=text.strip()
        if val: UD.setdefault(uid,{})[field]=val
        if idx<len(INFO_STEPS)-1:
            ns,_,nq,nr=INFO_STEPS[idx+1]; sst(uid,ns)
            if nr: bot.send_message(uid,nq,reply_markup=bk_kb())
            else: bot.send_message(uid,f"{nq} (ixtiyoriy)",reply_markup=skip_kb(ns))
        else: finish_info(uid,ud)
        return

    TOPIC_MAP={"referat_t":"referat_p","kurs_t":"kurs_p","mustaqil_t":"mustaqil_p","maqola_t":"maqola_p","prez_t":"prez_sl","test_t":"test_cnt"}
    if state in TOPIC_MAP:
        UD.setdefault(uid,{})["topic"]=text; ns=TOPIC_MAP[state]; sst(uid,ns)
        if ns=="prez_sl":
            bot.send_message(uid,
                f"🎯 *Necha slayd kerak?*\n💰 1 slayd = {PRICE_SLIDE:,} so'm\n\n"
                f"💡 Tanlang yoki raqam yozing:",
                parse_mode="Markdown", reply_markup=slides_count_kb())
        elif ns=="test_cnt":
            bot.send_message(uid,
                f"🔢 *Nechta savol kerak?*\n💰 1 savol = {PRICE_TEST:,} so'm\n\n"
                f"💡 Tanlang yoki raqam yozing:",
                parse_mode="Markdown", reply_markup=test_count_kb())
        else:
            prices={"referat_p":PRICE_PAGE,"kurs_p":PRICE_KURS,"mustaqil_p":PRICE_MUSTAQIL,"maqola_p":PRICE_MAQOLA}
            bot.send_message(uid,f"📄 Necha bet? (5-50)\n💰 1 bet = {prices.get(ns,PRICE_PAGE):,} so'm",reply_markup=bk_kb())
        return

    PAGE_STATES={"referat_p":"referat","kurs_p":"kurs","mustaqil_p":"mustaqil","maqola_p":"maqola"}
    if state in PAGE_STATES:
        try: pages=max(5,min(50,int(text.strip())))
        except: bot.send_message(uid,"❌ 5-50 orasida raqam kiriting"); return
        svc=PAGE_STATES[state]; prices={"referat":PRICE_PAGE,"kurs":PRICE_KURS,"mustaqil":PRICE_MUSTAQIL,"maqola":PRICE_MAQOLA}
        pr=prices[svc]; total=pages*pr
        UD.setdefault(uid,{}).update({"pages":pages,"svc":svc,"total":total})
        sst(uid,"ask_name")
        bot.send_message(uid,f"✅ {pages} bet × {pr:,} = *{total:,} so'm*\n\n👤 Ism va familiyangizni kiriting:",parse_mode="Markdown",reply_markup=bk_kb()); return

    if state=="prez_sl":
        try: slides=max(5,min(50,int(text.strip())))
        except: bot.send_message(uid,"❌ 5-50 orasida raqam kiriting"); return
        total=slides*PRICE_SLIDE
        UD.setdefault(uid,{}).update({"slides":slides,"svc":"prez","total":total})
        sst(uid,"prez_plans")
        bot.send_message(uid,
            f"✅ {slides} slayd × {PRICE_SLIDE:,} = *{total:,} so'm*\n\n"
            "📋 *Nechta reja (bo'lim) bo'lsin?*\n"
            "(Har bir reja alohida bo'lim bo'ladi)",
            parse_mode="Markdown", reply_markup=plans_count_kb()); return

    if state=="prez_plans":
        try: plans=max(2,min(15,int(text.strip())))
        except: bot.send_message(uid,"❌ 2-15 orasida raqam kiriting"); return
        UD.setdefault(uid,{})["plans_count"]=plans
        sst(uid,"ask_name")
        bot.send_message(uid,f"✅ {plans} ta reja.\n\n👤 Ism va familiyangizni kiriting:",reply_markup=bk_kb()); return

    if state=="test_cnt":
        try: count=max(10,min(1000,int(text.strip())))
        except: bot.send_message(uid,"❌ 10-1000 orasida raqam kiriting"); return
        total=count*PRICE_TEST; bal=get_balance(uid)
        if bal<total: bot.send_message(uid,f"❌ Mablag' yetarli emas!\nKerakli: {total:,}\nBalans: {bal:,}\n\nBalans to'ldirish uchun adminga yozing."); return
        UD.setdefault(uid,{}).update({"count":count,"total":total})
        # Rasmli test so'rash
        img_test_kb=types.InlineKeyboardMarkup(row_width=2)
        img_test_kb.add(
            types.InlineKeyboardButton("🖼 Ha, rasmli test",callback_data="test_img:yes"),
            types.InlineKeyboardButton("📝 Yo'q, oddiy test",callback_data="test_img:no"))
        img_test_kb.add(types.InlineKeyboardButton("🏠 Asosiy menyu",callback_data="bk"))
        bot.send_message(uid,
            f"✅ {count} ta savol × {PRICE_TEST:,} = *{total:,} so'm*\n\n"
            "🖼 Testda rasmlar ham bo'lsinmi?\n"
            "(Rasmli test: grafik, jadval va rasmlar bilan)",
            parse_mode="Markdown", reply_markup=img_test_kb); return

    MENU={"📄 Referat":("referat_t","referat"),"📝 Kurs ishi":("kurs_t","kurs"),"📋 Mustaqil ish":("mustaqil_t","mustaqil"),"📰 Maqola":("maqola_t","maqola"),"📊 Prezentatsiya":("prez_t","prez"),"✅ Test":("test_t","test")}
    if text in MENU:
        st2,svc=MENU[text]; sst(uid,st2,svc=svc)
        bot.send_message(uid,"📝 Mavzuni kiriting:",reply_markup=bk_kb()); return

    if text=="✏️ Imlo tuzatish":
        sst(uid,"imlo_t")
        kb2=types.InlineKeyboardMarkup()
        kb2.add(types.InlineKeyboardButton("📁 Fayl yuborish (PDF/TXT)",callback_data="imlo_file"))
        bot.send_message(uid,"✏️ Matnni yozing yoki fayl yuboring:",reply_markup=kb2); return
    if text=="🔄 Konvertatsiya": bot.send_message(uid,"🔄 Format tanlang:",reply_markup=conv_kb()); return
    if text=="💰 Balans":
        bal=get_balance(uid); kb2=types.InlineKeyboardMarkup()
        kb2.add(types.InlineKeyboardButton("💳 Balans to'ldirish",callback_data="topup"))
        bot.send_message(uid,f"💰 *Balansingiz: {bal:,} so'm*",parse_mode="Markdown",reply_markup=kb2); return
    if text=="💝 Donat":
        kb2=types.InlineKeyboardMarkup()
        kb2.add(types.InlineKeyboardButton("🌐 Donat",url=DONATE_URL))
        bot.send_message(uid,f"💝 *Donat*\n\n💳 Karta: `{DONATE_CARD}`\n🟢 Click: `{DONATE_CLICK}`",parse_mode="Markdown",reply_markup=kb2); return
    if text=="❓ Yordam":
        bot.send_message(uid,f"❓ *Narxlar:*\n📄 Referat: {PRICE_PAGE:,}/bet\n📝 Kurs ishi: {PRICE_KURS:,}/bet\n📋 Mustaqil: {PRICE_MUSTAQIL:,}/bet\n📰 Maqola: {PRICE_MAQOLA:,}/bet\n📊 Prezentatsiya: {PRICE_SLIDE:,}/slayd\n✅ Test: {PRICE_TEST:,}/savol",parse_mode="Markdown",reply_markup=main_kb(uid)); return
    if "Admin" in text:
        kb2=types.InlineKeyboardMarkup()
        kb2.add(types.InlineKeyboardButton("💬 Adminga yozish",url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))
        bot.send_message(uid,"👨‍💼 Admin",reply_markup=kb2); return

@bot.callback_query_handler(func=lambda c: True)
def cb_h(call):
    uid=call.from_user.id; d=call.data
    bot.answer_callback_query(call.id)
    ud=UD.get(uid,{})

    if d=="noop": return

    if d=="back_step":
        # Oldingi bosqichga qaytish
        prev=go_back(uid)
        if prev:
            STATE_MESSAGES={
                "referat_t":"📄 Mavzuni kiriting:",
                "kurs_t":"📝 Mavzuni kiriting:",
                "mustaqil_t":"📋 Mavzuni kiriting:",
                "maqola_t":"📰 Mavzuni kiriting:",
                "prez_t":"📊 Mavzuni kiriting:",
                "test_t":"✅ Mavzuni kiriting:",
                "referat_p":f"📄 Necha bet? (5-50) | 1 bet = {PRICE_PAGE:,} so'm",
                "kurs_p":f"📝 Necha bet? (5-50) | 1 bet = {PRICE_KURS:,} so'm",
                "mustaqil_p":f"📋 Necha bet? (5-50) | 1 bet = {PRICE_MUSTAQIL:,} so'm",
                "maqola_p":f"📰 Necha bet? (5-50) | 1 bet = {PRICE_MAQOLA:,} so'm",
                "prez_sl":"📊 Necha slayd?",
                "prez_plans":"📋 Nechta reja?",
                "test_cnt":"🔢 Nechta savol?",
                "ask_name":"👤 Ism va familiyangizni kiriting:",
                "ask_univ":"🏛 Universitetingiz:",
                "ask_faculty":"📚 Fakultetingiz:",
                "ask_year":"📅 Nechinchi kurs?",
                "ask_teacher":"👩‍🏫 O'qituvchi ismi:",
                "ask_city":"🏙 Shahar:",
                "prez_tmpl":"🎨 Shablon tanlang:",
                "prez_lang":"🌐 Qaysi tilda?",
            }
            kb2=types.InlineKeyboardMarkup(row_width=2)
            kb2.add(types.InlineKeyboardButton("◀️ Orqaga",callback_data="back_step"),
                    types.InlineKeyboardButton("🏠 Menyu",callback_data="bk"))
            msg=STATE_MESSAGES.get(prev,"Davom eting:")
            try: bot.edit_message_text(msg,uid,call.message.message_id,reply_markup=kb2)
            except: bot.send_message(uid,msg,reply_markup=kb2)
        else:
            try: bot.edit_message_text("📋 Asosiy menyu:",uid,call.message.message_id)
            except: pass
            bot.send_message(uid,"📋 Asosiy menyu:",reply_markup=main_kb(uid))
        return

    if d.startswith("lang:"):
        lang=d[5:]; set_lang(uid,lang)
        try: bot.edit_message_text("✅ Til o'rnatildi!",uid,call.message.message_id)
        except: pass
        bot.send_message(uid,"📋 Asosiy menyu:",reply_markup=main_kb(uid))

    elif d=="bk":
        cst(uid)
        try: bot.edit_message_text("📋 Asosiy menyu:",uid,call.message.message_id)
        except: pass
        bot.send_message(uid,"📋 Asosiy menyu:",reply_markup=main_kb(uid))

    elif d=="topup":
        kb2=types.InlineKeyboardMarkup()
        kb2.add(types.InlineKeyboardButton("💬 Adminga yozish",url=f"https://t.me/{ADMIN_USERNAME.lstrip('@')}"))
        bot.send_message(uid,f"💳 Balans to'ldirish:\n{ADMIN_USERNAME}\n\n💳 Karta: `{DONATE_CARD}`",parse_mode="Markdown",reply_markup=kb2)

    elif d=="imlo_file":
        sst(uid,"imlo_f")
        try: bot.edit_message_text("📁 Fayl yuboring (PDF yoki TXT):",uid,call.message.message_id,reply_markup=bk_kb())
        except: bot.send_message(uid,"📁 Fayl yuboring:",reply_markup=bk_kb())

    elif d.startswith("skip:"):
        skip_st=d[5:]
        if skip_st not in INFO_STATES: return
        idx=INFO_STATES.index(skip_st)
        if idx<len(INFO_STEPS)-1:
            ns,_,nq,nr=INFO_STEPS[idx+1]; sst(uid,ns)
            try:
                if nr: bot.edit_message_text(nq,uid,call.message.message_id,reply_markup=bk_kb())
                else: bot.edit_message_text(f"{nq} (ixtiyoriy)",uid,call.message.message_id,reply_markup=skip_kb(ns))
            except:
                if nr: bot.send_message(uid,nq,reply_markup=bk_kb())
                else: bot.send_message(uid,f"{nq} (ixtiyoriy)",reply_markup=skip_kb(ns))
        else:
            finish_info(uid,ud)
            try: bot.delete_message(uid,call.message.message_id)
            except: pass

    elif d.startswith("tpg:"):
        page=int(d[4:])
        try: bot.delete_message(uid,call.message.message_id)
        except: pass
        show_templates(uid,page)

    elif d.startswith("tmpl:"):
        tmpl_id=d[5:]; UD.setdefault(uid,{})["template_id"]=tmpl_id
        tname=TEMPLATES.get(tmpl_id,{}).get("name","Shablon")
        img_kb2=types.InlineKeyboardMarkup(row_width=1)
        img_kb2.add(types.InlineKeyboardButton("🤖 AI avtomatik rasm qo'ysin",callback_data="pimg:ai"))
        img_kb2.add(types.InlineKeyboardButton("🖼 O'zim rasm yuklaydi",callback_data="pimg:user"))
        img_kb2.add(types.InlineKeyboardButton("❌ Rasmsiz davom etish",callback_data="pimg:no"))
        img_kb2.add(types.InlineKeyboardButton("🏠 Asosiy menyu",callback_data="bk"))
        try: bot.edit_message_text(f"✅ {tname}\n\n🖼 Prezentatsiyaga rasm qo'shmoqchimisiz?",uid,call.message.message_id,reply_markup=img_kb2)
        except: bot.send_message(uid,f"✅ {tname}\n🖼 Rasm?",reply_markup=img_kb2)

    elif d.startswith("pimg:"):
        choice=d[5:]; slides=ud.get("slides",10)
        if choice=="user":
            sst(uid,"wait_img_prez")
            try: bot.edit_message_text("🖼 Rasmni yuboring:\n(Keyin qaysi slaydga qo'yishni tanlaysiz)",uid,call.message.message_id,reply_markup=bk_kb())
            except: bot.send_message(uid,"🖼 Rasmni yuboring:",reply_markup=bk_kb())
        elif choice=="ai":
            # AI avtomatik rasm qo'yadi - qaysi slaydlarni tanlash
            kb_ai=types.InlineKeyboardMarkup(row_width=5)
            for i in range(1,min(slides+1,16)):
                kb_ai.add(types.InlineKeyboardButton(str(i),callback_data=f"ai_img_slide:{i}"))
            kb_ai.add(types.InlineKeyboardButton("🏠 Asosiy menyu",callback_data="bk"))
            try:
                bot.edit_message_text(
                    "🤖 *AI avtomatik rasm qo'yadi!*\n\nQaysi slaydlarga rasm qo'yilsin?\n(Bir nechta tanlash mumkin)",
                    uid,call.message.message_id,parse_mode="Markdown",reply_markup=kb_ai)
            except: bot.send_message(uid,"Qaysi slaydlarga rasm?",reply_markup=kb_ai)
        else:
            sst(uid,"prez_lang")
            try: bot.edit_message_text("🌐 Qaysi tilda?",uid,call.message.message_id,reply_markup=lc_kb("prez_lang"))
            except: bot.send_message(uid,"🌐 Qaysi tilda?",reply_markup=lc_kb("prez_lang"))

    elif d.startswith("ipage:"):
        parts=d.split(":"); ii=int(parts[1]); pn=int(parts[2])
        UD.setdefault(uid,{}).setdefault("img_pages",{})[ii]=pn
        svc=ud.get("svc","prez"); sst(uid,f"{svc}_lang")
        try: bot.edit_message_text(f"✅ {pn}-slaydga qo'yiladi!\n🌐 Qaysi tilda?",uid,call.message.message_id,reply_markup=lc_kb(f"{svc}_lang"))
        except: bot.send_message(uid,"🌐 Qaysi tilda?",reply_markup=lc_kb(f"{svc}_lang"))

    elif d=="img_done":
        svc=ud.get("svc","prez"); sst(uid,f"{svc}_lang")
        try: bot.edit_message_text("🌐 Qaysi tilda?",uid,call.message.message_id,reply_markup=lc_kb(f"{svc}_lang"))
        except: bot.send_message(uid,"🌐 Qaysi tilda?",reply_markup=lc_kb(f"{svc}_lang"))

    elif "prez_lang:" in d or d.startswith("prez_lang:"):
        lang_code=d.split(":")[-1]
        UD.setdefault(uid,{})["content_lang"]=lang_code
        try: bot.edit_message_text("📁 Format tanlang:",uid,call.message.message_id,reply_markup=prez_fmt_kb())
        except: bot.send_message(uid,"📁 Format tanlang:",reply_markup=prez_fmt_kb())

    elif d.startswith("pfmt:"):
        fmt=d[5:]; topic=ud.get("topic",""); slides=ud.get("slides",10); total=ud.get("total",0)
        lang_code=ud.get("content_lang",get_lang(uid)); tmpl_id=ud.get("template_id","1")
        bal=get_balance(uid)
        if bal<total: bot.send_message(uid,f"❌ Mablag' yetarli emas!\nKerakli: {total:,}\nBalans: {bal:,}"); return
        deduct(uid,total)
        pm=bot.send_message(uid,f"⏳ {slides} ta slayd tayyorlanmoqda... 💰 {total:,} so'm ayirildi")
        try:
            tmpl_name=TEMPLATES.get(str(tmpl_id),TEMPLATES["1"])["name"]
            plans_count=ud.get('plans_count',5)
            content=gen_prez_content(topic,slides,tmpl_name,lang_code,ud,plans_count)
            user_imgs=UI.get(uid); img_pages=ud.get("img_pages")
            try: bot.delete_message(uid,pm.message_id)
            except: pass
            if fmt in ("pptx","both"):
                op,td2=make_pptx_pro(content,topic,tmpl_id,ud,user_imgs,img_pages)
                if op and os.path.exists(op):
                    with open(op,"rb") as f: bot.send_document(uid,f,caption=f"📊 {topic}")
                    shutil.rmtree(td2,ignore_errors=True)
            if fmt in ("html","both"):
                op,td2=make_pptx_html(content,topic,tmpl_id,ud)
                if op and os.path.exists(op):
                    with open(op,"rb") as f: bot.send_document(uid,f,caption=f"🌐 {topic} (HTML - brauzerda oching)")
                    shutil.rmtree(td2,ignore_errors=True)
            log_act(uid,"prez",topic,total)
            save_buyurtma(uid,"prez",topic,fmt,ud.get("slides",0),total)
        except Exception as e:
            logger.error(f"Prez:{e}"); add_bal(uid,total); bot.send_message(uid,"❌ Xatolik. Pul qaytarildi.")
        cst(uid); UI.pop(uid,None)
        bot.send_message(uid,f"✅ Tayyor! Balans: {get_balance(uid):,} so'm",reply_markup=main_kb(uid))

    elif "_lang:" in d and "prez_lang" not in d:
        lang_code=d.split(":")[-1]
        UD.setdefault(uid,{})["content_lang"]=lang_code
        try: bot.edit_message_text("📁 Qaysi formatda?",uid,call.message.message_id,reply_markup=fmt_kb("fmt"))
        except: bot.send_message(uid,"📁 Qaysi formatda?",reply_markup=fmt_kb("fmt"))

    elif d.startswith("fmt:"):
        fmt=d[4:]; topic=ud.get("topic",""); pages=ud.get("pages",5); total=ud.get("total",0)
        lang_code=ud.get("content_lang",get_lang(uid)); svc=ud.get("svc","referat")
        bal=get_balance(uid)
        if bal<total: bot.send_message(uid,f"❌ Mablag' yetarli emas!\nKerakli: {total:,}\nBalans: {bal:,}"); return
        deduct(uid,total)
        pm=bot.send_message(uid,f"⏳ Tayyorlanmoqda... 💰 {total:,} so'm ayirildi")
        try:
            content=gen_text(svc,topic,pages,lang_code,ud)
            names={"referat":"Referat","kurs":"Kurs ishi","mustaqil":"Mustaqil ish","maqola":"Maqola"}
            title=f"{names.get(svc,'Hujjat')}: {topic}"
            try: bot.delete_message(uid,pm.message_id)
            except: pass
            if fmt=="txt":
                for i in range(0,len(content),4000): bot.send_message(uid,content[i:i+4000])
            elif fmt=="docx":
                op,td2=make_docx(content,title,ud)
                if op:
                    with open(op,"rb") as f: bot.send_document(uid,f,caption=f"📝 {title}")
                    shutil.rmtree(td2,ignore_errors=True)
            elif fmt=="pdf":
                op,td2=make_pdf_simple(content,title,ud)
                if op:
                    with open(op,"rb") as f: bot.send_document(uid,f,caption=f"📄 {title}")
                    shutil.rmtree(td2,ignore_errors=True)
            log_act(uid,svc,topic,total)
            save_buyurtma(uid,svc,topic,fmt,ud.get("pages",0),total)
        except Exception as e:
            logger.error(f"Gen:{e}"); add_bal(uid,total); bot.send_message(uid,"❌ Xatolik. Pul qaytarildi.")
        cst(uid); bot.send_message(uid,f"✅ Tayyor! Balans: {get_balance(uid):,} so'm",reply_markup=main_kb(uid))

    elif d.startswith("test_fmt:"):
        fmt=d[9:]; topic=ud.get("topic",""); count=ud.get("count",10); total=ud.get("total",0)
        bal=get_balance(uid)
        if bal<total: bot.send_message(uid,f"❌ Mablag' yetarli emas!\nKerakli: {total:,}\nBalans: {bal:,}"); return
        deduct(uid,total)
        pm=bot.send_message(uid,f"⏳ {count} ta savol yaratilmoqda...")
        try:
            with_img=ud.get('test_with_img',False)
            res=gen_test_content(topic,count,get_lang(uid),with_img)
            try: bot.delete_message(uid,pm.message_id)
            except: pass
            if fmt=="txt":
                for i in range(0,len(res),4000): bot.send_message(uid,res[i:i+4000])
            else:
                fn=make_docx if fmt=="docx" else make_pdf_simple
                op,td2=fn(res,f"Test: {topic}",{})
                if op:
                    cap="📝" if fmt=="docx" else "📄"
                    with open(op,"rb") as f: bot.send_document(uid,f,caption=f"{cap} Test: {topic}")
                    shutil.rmtree(td2,ignore_errors=True)
            log_act(uid,"test",topic,total)
            save_buyurtma(uid,"test",topic,fmt,ud.get("count",0),total)
        except Exception as e:
            logger.error(f"Test:{e}"); add_bal(uid,total); bot.send_message(uid,"❌ Xatolik. Pul qaytarildi.")
        cst(uid); bot.send_message(uid,f"✅ Tayyor! Balans: {get_balance(uid):,} so'm",reply_markup=main_kb(uid))

    elif d.startswith("cv:"):
        t=d[3:]
        if t=="pdf": sst(uid,"pdf_pptx"); bot.edit_message_text("📎 PDF fayl yuboring:",uid,call.message.message_id,reply_markup=bk_kb())
        elif t=="pptx": sst(uid,"pptx_pdf"); bot.edit_message_text("📎 PPTX/PPT fayl yuboring:",uid,call.message.message_id,reply_markup=bk_kb())
        elif t=="img": sst(uid,"img"); UI[uid]=[]; bot.edit_message_text("🖼 Rasmlar yuboring. Tugagach /done:",uid,call.message.message_id,reply_markup=bk_kb())

    elif d=="tr:l": sst(uid,"l2k"); bot.edit_message_text("✏️ Matn yuboring:",uid,call.message.message_id,reply_markup=bk_kb())
    elif d=="tr:k": sst(uid,"k2l"); bot.edit_message_text("✏️ Matn yuboring:",uid,call.message.message_id,reply_markup=bk_kb())

    elif d.startswith("resume:"):
        st2=d[7:]; svc=UD.get(uid,{}).get("svc","")
        if "tmpl" in st2 or st2=="prez_tmpl": show_templates(uid,1)
        elif "lang" in st2: bot.send_message(uid,"🌐 Qaysi tilda?",reply_markup=lc_kb(f"{svc}_lang"))
        else: bot.send_message(uid,"📋 Asosiy menyu:",reply_markup=main_kb(uid))

    # Slayd soni tugmasi
    elif d.startswith("slides:"):
        val=d[7:]
        if val=="custom":
            sst(uid,"prez_sl")
            bot.edit_message_text(f"✏️ Necha slayd? (5-50)\n💰 1 slayd = {PRICE_SLIDE:,} so'm",
                uid,call.message.message_id,reply_markup=bk_kb())
        else:
            slides=int(val); total=slides*PRICE_SLIDE
            UD.setdefault(uid,{}).update({"slides":slides,"svc":"prez","total":total})
            sst(uid,"prez_plans")
            try:
                bot.edit_message_text(
                    f"✅ {slides} slayd × {PRICE_SLIDE:,} = *{total:,} so'm*\n\n"
                    "📋 *Nechta reja (bo'lim) bo'lsin?*",
                    uid,call.message.message_id,
                    parse_mode="Markdown",reply_markup=plans_count_kb())
            except: bot.send_message(uid,f"✅ {slides} slayd\n📋 Nechta reja?",reply_markup=plans_count_kb())

    # Test soni tugmasi
    elif d.startswith("tcount:"):
        val=d[7:]
        if val=="custom":
            sst(uid,"test_cnt")
            bot.edit_message_text(f"✏️ Nechta savol? (10-1000)\n💰 1 savol = {PRICE_TEST:,} so'm",
                uid,call.message.message_id,reply_markup=bk_kb())
        else:
            count=int(val); total=count*PRICE_TEST; bal=get_balance(uid)
            if bal<total:
                bot.edit_message_text(f"❌ Mablag' yetarli emas!\nKerakli: {total:,}\nBalans: {bal:,}",
                    uid,call.message.message_id); return
            UD.setdefault(uid,{}).update({"count":count,"total":total})
            img_kb2=types.InlineKeyboardMarkup(row_width=2)
            img_kb2.add(types.InlineKeyboardButton("🖼 Ha, rasmli",callback_data="test_img:yes"),
                        types.InlineKeyboardButton("📝 Oddiy test",callback_data="test_img:no"))
            img_kb2.add(types.InlineKeyboardButton("🏠 Asosiy menyu",callback_data="bk"))
            try:
                bot.edit_message_text(
                    f"✅ {count} ta savol × {PRICE_TEST:,} = *{total:,} so'm*\n\n"
                    "🖼 Testda rasmlar bo'lsinmi?",
                    uid,call.message.message_id,parse_mode="Markdown",reply_markup=img_kb2)
            except: bot.send_message(uid,f"✅ {count} ta savol\n🖼 Rasmli?",reply_markup=img_kb2)

    # Reja soni tugmasi
    elif d.startswith("plans:"):
        val=d[6:]
        if val=="custom":
            sst(uid,"prez_plans")
            bot.edit_message_text("✏️ Nechta reja? (2-15 ta):",uid,call.message.message_id,reply_markup=bk_kb())
        else:
            plans=int(val)
            UD.setdefault(uid,{})["plans_count"]=plans
            sst(uid,"ask_name")
            try:
                bot.edit_message_text(f"✅ {plans} ta reja.\n\n👤 Ism va familiyangizni kiriting:",
                    uid,call.message.message_id,reply_markup=bk_kb())
            except: bot.send_message(uid,f"✅ {plans} ta reja.\n\n👤 Ism kiriting:",reply_markup=bk_kb())

    # Test uchun rasm
    elif d.startswith("test_img:"):
        with_img=d[9:]=="yes"
        UD.setdefault(uid,{})["test_with_img"]=with_img
        try:
            bot.edit_message_text("📁 Qaysi formatda olmoqchisiz?",
                uid,call.message.message_id,reply_markup=fmt_kb("test_fmt"))
        except: bot.send_message(uid,"📁 Format tanlang:",reply_markup=fmt_kb("test_fmt"))

    # AI rasm qo'yish - qaysi slaydga
    elif d.startswith("ai_img_slide:"):
        slide_num=int(d[13:])
        UD.setdefault(uid,{}).setdefault("ai_img_slides",[]).append(slide_num)
        slides=ud.get("slides",10)
        already=UD[uid].get("ai_img_slides",[])
        kb3=types.InlineKeyboardMarkup(row_width=5)
        for i in range(1,min(slides+1,16)):
            label=f"✅{i}" if i in already else str(i)
            kb3.add(types.InlineKeyboardButton(label,callback_data=f"ai_img_slide:{i}"))
        kb3.add(types.InlineKeyboardButton("✅ Tayyor",callback_data="ai_img_done"))
        kb3.add(types.InlineKeyboardButton("🏠 Asosiy menyu",callback_data="bk"))
        try:
            bot.edit_message_text(
                f"✅ {slide_num}-slaydga AI rasm qo'yiladi!\n"
                f"Tanlangan slaydlar: {already}\n\n"
                "Yana slayd tanlang yoki 'Tayyor' bosing:",
                uid,call.message.message_id,reply_markup=kb3)
        except: pass

    elif d=="ai_img_done":
        sst(uid,"prez_lang")
        try:
            bot.edit_message_text("🌐 Qaysi tilda?",uid,call.message.message_id,reply_markup=lc_kb("prez_lang"))
        except: bot.send_message(uid,"🌐 Qaysi tilda?",reply_markup=lc_kb("prez_lang"))

if __name__=="__main__":
    init_db()
    try:
        bot.set_my_commands([
            types.BotCommand("start","Botni ishga tushirish"),
            types.BotCommand("referat","Referat yozish"),
            types.BotCommand("kursishi","Kurs ishi yozish"),
            types.BotCommand("mustaqilish","Mustaqil ish yozish"),
            types.BotCommand("maqola","Ilmiy maqola yozish"),
            types.BotCommand("prezentatsiya","Prezentatsiya yaratish"),
            types.BotCommand("test","Test savollari yaratish"),
            types.BotCommand("imlo","Imlo tuzatish"),
            types.BotCommand("konvertatsiya","Fayl konvertatsiya"),
            types.BotCommand("balans","Balansni ko'rish"),
            types.BotCommand("yordam","Yordam va narxlar"),
            types.BotCommand("menu","Asosiy menyuni ochish"),
        ])
    except Exception as e: logger.error(f"Commands: {e}")
    print("EduBot v9 ishga tushdi!")
    bot.infinity_polling()