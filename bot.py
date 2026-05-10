import telebot
import sqlite3
import logging
from datetime import datetime
from telebot import types

BOT_TOKEN = "8772507029:AAF84YFp8YmBKnrJOvCBI2jc_7oVbjPN2jk"
ADMIN_ID = 1113404703
ADMIN_USERNAME = "@abdurakhmon02"

logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
bot = telebot.TeleBot(BOT_TOKEN)

PRODUCTS = {
    "👗 Ayollar kiyimi": {
        "Ko'ylak": 120000, "Yubka": 95000, "Bluzka": 85000,
        "Platye": 180000, "Shim": 110000, "Kofta": 130000
    },
    "👔 Erkaklar kiyimi": {
        "Ko'ylak (klassik)": 130000, "Shim": 120000, "Futbolka": 65000,
        "Jaket": 350000, "Sviter": 180000
    },
    "👶 Bolalar kiyimi": {
        "Bolalar ko'ylagi": 75000, "Bolalar shimi": 70000,
        "Bolalar kostyumi": 150000, "Bolalar kurtka": 220000
    },
    "👟 Poyabzal": {
        "Krossovka": 280000, "Tufliya (ayollar)": 220000,
        "Tufliya (erkaklar)": 250000, "Sandal": 130000, "Botinka": 320000
    },
    "💍 Aksessuarlar": {
        "Sumka": 180000, "Kamar": 65000, "Shlyapa": 55000,
        "Ro'mol": 45000, "Ko'zoynak": 85000, "Soat": 250000
    },
    "🏃 Sport kiyimlari": {
        "Sport kostyumi": 220000, "Sport futbolkasi": 75000,
        "Legging": 95000, "Sport shimi": 110000
    }
}

SIZES = ["XS", "S", "M", "L", "XL", "XXL"]
SHOE_SIZES = ["36", "37", "38", "39", "40", "41", "42", "43", "44", "45"]

# ==================== DATABASE ====================
def init_db():
    conn = sqlite3.connect('anjirshop.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY, name TEXT, phone TEXT,
        address TEXT, registered_at TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS orders (
        id INTEGER PRIMARY KEY AUTOINCREMENT, telegram_id INTEGER,
        category TEXT, product TEXT, size TEXT, quantity INTEGER,
        price REAL, total REAL, status TEXT DEFAULT "pending", created_at TEXT)''')
    conn.commit()
    conn.close()

def get_user(telegram_id):
    conn = sqlite3.connect('anjirshop.db')
    c = conn.cursor()
    c.execute('SELECT * FROM users WHERE telegram_id=?', (telegram_id,))
    row = c.fetchone()
    conn.close()
    if row:
        return {'telegram_id': row[0], 'name': row[1], 'phone': row[2],
                'address': row[3], 'registered_at': row[4]}
    return None

def save_user(telegram_id, name, phone, address):
    conn = sqlite3.connect('anjirshop.db')
    c = conn.cursor()
    c.execute('INSERT OR REPLACE INTO users VALUES (?,?,?,?,?)',
              (telegram_id, name, phone, address, datetime.now().strftime("%d.%m.%Y %H:%M")))
    conn.commit()
    conn.close()

def save_order(telegram_id, category, product, size, quantity, price):
    total = quantity * price
    conn = sqlite3.connect('anjirshop.db')
    c = conn.cursor()
    c.execute('INSERT INTO orders (telegram_id,category,product,size,quantity,price,total,created_at) VALUES (?,?,?,?,?,?,?,?)',
              (telegram_id, category, product, size, quantity, price, total,
               datetime.now().strftime("%d.%m.%Y %H:%M")))
    order_id = c.lastrowid
    conn.commit()
    conn.close()
    return order_id, total

def get_orders(telegram_id):
    conn = sqlite3.connect('anjirshop.db')
    c = conn.cursor()
    c.execute('SELECT * FROM orders WHERE telegram_id=? ORDER BY id DESC LIMIT 10', (telegram_id,))
    rows = c.fetchall()
    conn.close()
    return rows

# ==================== KLAVIATURALAR ====================
def main_kb(registered=True):
    kb = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if registered:
        kb.row("🛍 Buyurtma berish", "📦 Buyurtmalarim")
        kb.row("👤 Profilim", "📞 Admin")
        kb.row("ℹ️ Do'kon haqida")
    else:
        kb.row("📝 Ro'yxatdan o'tish")
        kb.row("ℹ️ Do'kon haqida")
    return kb

def categories_kb():
    kb = types.InlineKeyboardMarkup()
    for cat in PRODUCTS:
        kb.add(types.InlineKeyboardButton(cat, callback_data=f"cat|{cat}"))
    return kb

def products_kb(category):
    kb = types.InlineKeyboardMarkup()
    for prod, price in PRODUCTS[category].items():
        kb.add(types.InlineKeyboardButton(f"{prod} — {price:,} so'm", callback_data=f"prod|{prod}"))
    kb.add(types.InlineKeyboardButton("🔙 Orqaga", callback_data="back|cats"))
    return kb

def sizes_kb(is_shoe=False):
    kb = types.InlineKeyboardMarkup(row_width=4)
    sizes = SHOE_SIZES if is_shoe else SIZES
    buttons = [types.InlineKeyboardButton(s, callback_data=f"size|{s}") for s in sizes]
    kb.add(*buttons)
    return kb

def qty_kb():
    kb = types.InlineKeyboardMarkup(row_width=5)
    buttons = [types.InlineKeyboardButton(str(i), callback_data=f"qty|{i}") for i in range(1, 6)]
    kb.add(*buttons)
    return kb

def confirm_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("✅ Tasdiqlash", callback_data="order|confirm"))
    kb.add(types.InlineKeyboardButton("❌ Bekor qilish", callback_data="order|cancel"))
    return kb

def payment_kb():
    kb = types.InlineKeyboardMarkup()
    kb.add(types.InlineKeyboardButton("📲 Click", callback_data="pay|click"))
    kb.add(types.InlineKeyboardButton("💳 Payme", callback_data="pay|payme"))
    kb.add(types.InlineKeyboardButton("🤝 Admin bilan kelishuv", callback_data="pay|admin"))
    return kb

# ==================== RO'YXAT HOLATI ====================
user_states = {}
user_data = {}

# ==================== HANDLERLAR ====================
@bot.message_handler(commands=['start'])
def start(msg):
    user = get_user(msg.from_user.id)
    name = msg.from_user.first_name or "Mehmon"
    if user:
        bot.send_message(msg.chat.id,
            f"👗 Xush kelibsiz, *{user['name']}*!\n\n"
            f"🏪 *AnjirShop* — Kiyim-kechak va aksessuarlar do'koni",
            parse_mode='Markdown', reply_markup=main_kb(True))
    else:
        bot.send_message(msg.chat.id,
            f"👋 Assalomu alaykum, *{name}*!\n\n"
            f"🏪 *AnjirShop*ga xush kelibsiz!\n\n"
            f"👗 Kiyim-kechak va aksessuarlarning eng sara kolleksiyalari\n"
            f"🚚 Tez va ishonchli yetkazib berish\n\n"
            f"➡️ Boshlash uchun ro'yxatdan o'ting:",
            parse_mode='Markdown', reply_markup=main_kb(False))

@bot.message_handler(func=lambda m: True)
def handle_text(msg):
    text = msg.text
    uid = msg.from_user.id
    user = get_user(uid)

    # Ro'yxatdan o'tish holatlari
    if user_states.get(uid) == 'wait_name':
        user_data[uid] = {'name': text.strip()}
        user_states[uid] = 'wait_phone'
        kb = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
        kb.add(types.KeyboardButton("📱 Raqamni yuborish", request_contact=True))
        bot.send_message(msg.chat.id,
            f"✅ *{text.strip()}*\n\n📱 Telefon raqamingizni yuboring:",
            parse_mode='Markdown', reply_markup=kb)
        return

    if user_states.get(uid) == 'wait_address':
        user_data[uid]['address'] = text.strip()
        name = user_data[uid]['name']
        phone = user_data[uid]['phone']
        address = user_data[uid]['address']
        save_user(uid, name, phone, address)
        user_states.pop(uid, None)
        try:
            bot.send_message(ADMIN_ID,
                f"🆕 *Yangi mijoz!*\n👤 {name}\n📱 {phone}\n📍 {address}",
                parse_mode='Markdown')
        except: pass
        bot.send_message(msg.chat.id,
            f"🎉 *Tabriklaymiz, {name}!*\n\n✅ Ro'yxatdan o'tdingiz!",
            parse_mode='Markdown', reply_markup=main_kb(True))
        return

    if text == "📝 Ro'yxatdan o'tish":
        user_states[uid] = 'wait_name'
        bot.send_message(msg.chat.id,
            "📝 *Ro'yxatdan o'tish*\n\nIsm va familiyangizni kiriting:",
            parse_mode='Markdown',
            reply_markup=types.ReplyKeyboardRemove())
        return

    if text == "🛍 Buyurtma berish":
        if not user:
            bot.send_message(msg.chat.id, "❗ Avval ro'yxatdan o'ting!", reply_markup=main_kb(False))
            return
        bot.send_message(msg.chat.id, "🛍 *Kategoriyani tanlang:*",
                         parse_mode='Markdown', reply_markup=categories_kb())

    elif text == "📦 Buyurtmalarim":
        if not user:
            bot.send_message(msg.chat.id, "❗ Avval ro'yxatdan o'ting!", reply_markup=main_kb(False))
            return
        orders = get_orders(uid)
        if not orders:
            bot.send_message(msg.chat.id, "📭 Hali buyurtma yo'q.", reply_markup=main_kb(True))
            return
        txt = "📦 *Buyurtmalaringiz:*\n\n"
        for o in orders[:7]:
            size_info = f" | {o[4]}" if o[4] and o[4] != "-" else ""
            txt += f"#{o[0]} — {o[3]}{size_info}\n{o[5]} dona × {o[6]:,.0f} = *{o[7]:,.0f} so'm*\n📅 {o[9]}\n\n"
        bot.send_message(msg.chat.id, txt, parse_mode='Markdown', reply_markup=main_kb(True))

    elif text == "👤 Profilim":
        if not user:
            bot.send_message(msg.chat.id, "❗ Ro'yxatdan o'tmagansiz!", reply_markup=main_kb(False))
            return
        orders = get_orders(uid)
        total = sum(o[7] for o in orders)
        bot.send_message(msg.chat.id,
            f"👤 *Profilim*\n\n📛 {user['name']}\n📱 {user['phone']}\n"
            f"📍 {user['address']}\n📅 {user['registered_at']}\n\n"
            f"📦 Buyurtmalar: *{len(orders)} ta*\n💰 Jami xarid: *{total:,.0f} so'm*",
            parse_mode='Markdown', reply_markup=main_kb(True))

    elif text == "📞 Admin":
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💬 Adminga yozish", url="https://t.me/anjirshop_admin"))
        bot.send_message(msg.chat.id,
            f"📞 *Admin bilan bog'lanish*\n\n👨‍💼 {ADMIN_USERNAME}\n\n"
            f"💳 *To'lov:*\n🟢 Click: +998 94 975 03 04\n"
            f"🔵 Payme: +998 94 975 03 04\n\n⏰ 09:00 — 21:00",
            parse_mode='Markdown', reply_markup=kb)

    elif text == "ℹ️ Do'kon haqida":
        bot.send_message(msg.chat.id,
            "🏪 *AnjirShop*\n\n👗 Ayollar, erkaklar, bolalar kiyimlari\n"
            "👟 Poyabzal va aksessuarlar\n🚚 Toshkent bo'ylab yetkazib berish\n"
            "💯 Sifat kafolati\n↩️ 3 kunlik qaytarish\n\n📍 Toshkent, O'zbekiston",
            parse_mode='Markdown', reply_markup=main_kb(bool(user)))

@bot.message_handler(content_types=['contact'])
def handle_contact(msg):
    uid = msg.from_user.id
    if user_states.get(uid) == 'wait_phone':
        phone = msg.contact.phone_number
        if not phone.startswith('+'): phone = '+' + phone
        user_data[uid]['phone'] = phone
        user_states[uid] = 'wait_address'
        bot.send_message(msg.chat.id,
            f"✅ Tel: *{phone}*\n\n📍 Yetkazib berish manzilingizni kiriting:",
            parse_mode='Markdown', reply_markup=types.ReplyKeyboardRemove())

@bot.callback_query_handler(func=lambda call: True)
def handle_callback(call):
    uid = call.from_user.id
    user = get_user(uid)
    parts = call.data.split("|")
    action = parts[0]
    value = parts[1] if len(parts) > 1 else ""

    if action == "back" and value == "cats":
        bot.edit_message_text("🛍 *Kategoriyani tanlang:*", call.message.chat.id,
                               call.message.message_id, parse_mode='Markdown',
                               reply_markup=categories_kb())

    elif action == "cat":
        if uid not in user_data: user_data[uid] = {}
        user_data[uid]['category'] = value
        bot.edit_message_text(f"📂 *{value}*\n\nMahsulot tanlang:",
                               call.message.chat.id, call.message.message_id,
                               parse_mode='Markdown', reply_markup=products_kb(value))

    elif action == "prod":
        if uid not in user_data: user_data[uid] = {}
        category = user_data[uid].get('category', '')
        price = PRODUCTS.get(category, {}).get(value, 0)
        user_data[uid]['product'] = value
        user_data[uid]['price'] = price
        is_shoe = "Poyabzal" in category
        user_data[uid]['is_shoe'] = is_shoe
        bot.edit_message_text(
            f"👗 *{value}*\n💰 {price:,} so'm\n\n📏 O'lchamni tanlang:",
            call.message.chat.id, call.message.message_id,
            parse_mode='Markdown', reply_markup=sizes_kb(is_shoe))

    elif action == "size":
        user_data[uid]['size'] = value
        product = user_data[uid].get('product', '')
        price = user_data[uid].get('price', 0)
        bot.edit_message_text(
            f"👗 *{product}*\n💰 {price:,} so'm\n📏 O'lcham: *{value}*\n\n📊 Necha dona?",
            call.message.chat.id, call.message.message_id,
            parse_mode='Markdown', reply_markup=qty_kb())

    elif action == "qty":
        qty = int(value)
        user_data[uid]['quantity'] = qty
        product = user_data[uid].get('product', '')
        price = user_data[uid].get('price', 0)
        size = user_data[uid].get('size', '-')
        category = user_data[uid].get('category', '')
        total = qty * price
        bot.edit_message_text(
            f"🧾 *Buyurtma:*\n\n📂 {category}\n👗 {product}\n"
            f"📏 O'lcham: *{size}*\n📊 {qty} dona\n"
            f"💰 {price:,} so'm/dona\n💵 Jami: *{total:,} so'm*\n\n"
            f"📍 {user['address']}\n📱 {user['phone']}\n\n✅ Tasdiqlaysizmi?",
            call.message.chat.id, call.message.message_id,
            parse_mode='Markdown', reply_markup=confirm_kb())

    elif action == "order" and value == "confirm":
        product = user_data[uid].get('product')
        category = user_data[uid].get('category')
        size = user_data[uid].get('size', '-')
        qty = user_data[uid].get('quantity', 1)
        price = user_data[uid].get('price', 0)
        order_id, total = save_order(uid, category, product, size, qty, price)
        try:
            bot.send_message(ADMIN_ID,
                f"🛍 *YANGI BUYURTMA #{order_id}!*\n\n"
                f"👤 {user['name']}\n📱 {user['phone']}\n📍 {user['address']}\n\n"
                f"📂 {category}\n👗 {product}\n📏 {size}\n"
                f"📊 {qty} dona\n💵 *{total:,} so'm*\n📅 {datetime.now().strftime('%d.%m.%Y %H:%M')}",
                parse_mode='Markdown')
        except: pass
        bot.edit_message_text(
            f"🎉 *Buyurtma #{order_id} qabul qilindi!*\n\n"
            f"👗 {product} | {size}\n💵 *{total:,} so'm*\n\n💳 To'lov usulini tanlang:",
            call.message.chat.id, call.message.message_id,
            parse_mode='Markdown', reply_markup=payment_kb())

    elif action == "order" and value == "cancel":
        bot.edit_message_text("❌ Buyurtma bekor qilindi.",
                               call.message.chat.id, call.message.message_id)
        bot.send_message(uid, "🏠 Asosiy menü:", reply_markup=main_kb(bool(user)))

    elif action == "pay":
        if value == "click":
            txt = "📲 *Click orqali to'lov*\n\nRaqam: *+998 94 975 03 04*\nChekni adminga yuboring ✅"
        elif value == "payme":
            txt = "💳 *Payme orqali to'lov*\n\nKarta: *9860060926650809*\nChekni adminga yuboring ✅"
        else:
            txt = f"🤝 *Admin bilan kelishuv*\n\n{ADMIN_USERNAME} siz bilan bog'lanadi."
        kb = types.InlineKeyboardMarkup()
        kb.add(types.InlineKeyboardButton("💬 Adminga yozish", url="https://t.me/anjirshop_admin"))
        bot.edit_message_text(txt, call.message.chat.id, call.message.message_id,
                               parse_mode='Markdown', reply_markup=kb)
        bot.send_message(uid, "🏠 Asosiy menü:", reply_markup=main_kb(bool(user)))

    bot.answer_callback_query(call.id)

@bot.message_handler(commands=['stats'])
def stats(msg):
    if msg.from_user.id != ADMIN_ID:
        bot.send_message(msg.chat.id, "❌ Ruxsat yo'q!")
        return
    conn = sqlite3.connect('anjirshop.db')
    c = conn.cursor()
    c.execute('SELECT COUNT(*) FROM users')
    users = c.fetchone()[0]
    c.execute('SELECT COUNT(*), COALESCE(SUM(total),0) FROM orders')
    row = c.fetchone()
    conn.close()
    bot.send_message(msg.chat.id,
        f"📊 *Statistika*\n\n👥 Mijozlar: *{users}*\n📦 Buyurtmalar: *{row[0]}*\n💰 Jami: *{row[1]:,.0f} so'm*",
        parse_mode='Markdown')

# ==================== MAIN ====================
if __name__ == "__main__":
    init_db()
    print("✅ AnjirShop bot ishga tushdi!")
    bot.infinity_polling()