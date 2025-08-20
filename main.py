import telebot
from telebot import types
from flask import Flask, request
import os
import time

# 🔑 تنظیمات (از محیط یا مقدار پیش‌فرض)
TOKEN = os.getenv("TOKEN", "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8")
ADMIN_ID = int(os.getenv("ADMIN_ID", 7549512366))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://bot-ltl5.onrender.com/webhook")

# 📌 پیکربندی ربات و Flask
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_data = {}

# 🛠 تنظیم Webhook
def set_webhook():
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
    except Exception as e:
        print("Webhook error:", e)

set_webhook()

# 🎉 شروع ربات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {}
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🌍 اقامت اسپانیا", callback_data="spain"),
        types.InlineKeyboardButton("🌐 سایر کشورها", callback_data="other")
    )
    bot.send_message(
        cid,
        "⚖️ *خوش آمدید به نئوویزا!* 🌍\n📜 نوع خدمت را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# 📌 انتخاب نوع مشاوره
@bot.callback_query_handler(func=lambda call: call.data in ["spain", "other"])
def process_consultation_type(call):
    cid = call.message.chat.id
    user_data[cid] = {"type": call.data, "step": "phone"}
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 ارسال شماره", request_contact=True))
    bot.edit_message_text(chat_id=cid, message_id=call.message.message_id, text="🌟 انتخاب ثبت شد!")
    bot.send_message(cid, "📞 شماره تماس خود را وارد کنید:", reply_markup=markup)

# 📌 دریافت شماره (از دکمه)
@bot.message_handler(content_types=['contact'], func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone")
def handle_contact(message):
    cid = message.chat.id
    user_data[cid]["phone"] = message.contact.phone_number
    user_data[cid]["step"] = "name"
    bot.send_message(cid, "✅ شماره ثبت شد!\n📝 نام و نام خانوادگی را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())

# 📌 دریافت شماره (متنی)
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone" and m.content_type == "text")
def handle_phone_text(message):
    cid = message.chat.id
    user_data[cid]["phone"] = message.text.strip()
    user_data[cid]["step"] = "name"
    bot.send_message(cid, "✅ شماره ثبت شد!\n📝 نام و نام خانوادگی را وارد کنید:", reply_markup=types.ReplyKeyboardRemove())

# 📌 دریافت نام
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "name" and m.content_type == "text")
def handle_name(message):
    cid = message.chat.id
    user_data[cid]["name"] = message.text.strip()
    user_data[cid]["step"] = "details"

    if user_data[cid].get("type") == "spain":
        send_spain_questions(cid)
    else:
        send_other_questions(cid)

# 📌 گزینه‌های اسپانیا
def send_spain_questions(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎓 تحصیل", callback_data="spain_edu"),
        types.InlineKeyboardButton("💼 کار", callback_data="spain_work"),
        types.InlineKeyboardButton("🏡 سرمایه‌گذاری", callback_data="spain_invest"),
    )
    bot.send_message(cid, "🌍 گزینه‌های اقامت اسپانیا:\nلطفاً یکی را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["spain_edu", "spain_work", "spain_invest"])
def process_spain_details(call):
    cid = call.message.chat.id
    user_data[cid]["details"] = call.data.replace("spain_", "")
    bot.answer_callback_query(call.id)

    if call.data == "spain_edu":
        bot.send_message(cid, "📜 دانشگاه، رشته، و سطح تحصیل را وارد کنید:")
    elif call.data == "spain_work":
        bot.send_message(cid, "💼 شغل، تجربه کاری، و مدرک تحصیلی را بنویسید:")
    elif call.data == "spain_invest":
        bot.send_message(cid, "🏡 میزان سرمایه، نوع ملک، و منبع مالی را وارد کنید:")

    user_data[cid]["step"] = "final_details"

# 📌 گزینه‌های سایر کشورها
def send_other_questions(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🇨🇦 کانادا", callback_data="other_canada"),
        types.InlineKeyboardButton("🇩🇪 آلمان", callback_data="other_germany"),
        types.InlineKeyboardButton("🇦🇺 استرالیا", callback_data="other_australia"),
        types.InlineKeyboardButton("🇯🇵 ژاپن", callback_data="other_japan"),
        types.InlineKeyboardButton("🇪🇺 شنگن", callback_data="other_schengen"),
        types.InlineKeyboardButton("🇬🇧 انگلستان", callback_data="other_uk"),
    )
    bot.send_message(cid, "🌐 کشور یا ویزای مورد نظر را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data.startswith("other_"))
def process_other_details(call):
    cid = call.message.chat.id
    user_data[cid]["details"] = call.data.replace("other_", "")
    bot.answer_callback_query(call.id)

    messages = {
        "other_canada": "🇨🇦 برنامه مهاجرتی، امتیاز CRS، و مدرک زبان را وارد کنید:",
        "other_germany": "🇩🇪 نوع ویزا، مدرک زبان، و تجربه کاری را بنویسید:",
        "other_australia": "🇦🇺 نوع ویزا، امتیاز سیستم، و مدرک زبان را وارد کنید:",
        "other_japan": "🇯🇵 نوع ویزا، مدرک زبان ژاپنی، و سابقه کاری را بنویسید:",
        "other_schengen": "🇪🇺 هدف ویزا، مدت اقامت، و مدارک دعوت‌نامه را مشخص کنید:",
        "other_uk": "🇬🇧 نوع ویزا، مدرک زبان، و هدف مهاجرت را وارد کنید:",
    }

    bot.send_message(cid, messages[call.data])
    user_data[cid]["step"] = "final_details"

# 📌 دریافت جزئیات نهایی
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "final_details" and m.content_type == "text")
def handle_final_details(message):
    cid = message.chat.id
    if all(k in user_data[cid] for k in ["name", "phone"]):
        details = message.text.strip()
        if "details" in user_data[cid]:
            user_data[cid]["details"] += f" | {details}"
        else:
            user_data[cid]["details"] = details

        name = user_data[cid]["name"]
        phone = user_data[cid]["phone"]
        consultation_type = "اقامت اسپانیا" if user_data[cid]["type"] == "spain" else f"اقامت {user_data[cid]['details'].split('|')[0]}"

        bot.send_message(
            ADMIN_ID,
            f"🔔 *درخواست جدید نئوویزا:* ⚖️\n👤 {name}\n📱 {phone}\n🌐 {consultation_type}\n📝 {details}",
            parse_mode="Markdown"
        )

        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 درخواست جدید", callback_data="new_request"))
        bot.send_message(cid, "🎉 درخواست شما ثبت شد! تیم نئوویزا به زودی تماس می‌گیرد.\nبرای درخواست جدید، کلیک کنید:", reply_markup=markup)

        del user_data[cid]
    else:
        bot.send_message(cid, "❌ داده‌ها ناقصند! لطفاً دوباره /start را بزنید.")

# 📌 درخواست جدید
@bot.callback_query_handler(func=lambda call: call.data == "new_request")
def process_new_request(call):
    cid = call.message.chat.id
    user_data[cid] = {}
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🌍 اقامت اسپانیا", callback_data="spain"),
        types.InlineKeyboardButton("🌐 سایر کشورها", callback_data="other")
    )
    bot.send_message(cid, "⚖️ *خوش آمدید به نئوویزا!* 🌍\n📜 نوع خدمت را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

# 📌 Webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_str = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_str)
        bot.process_new_updates([update])
        return "", 200
    return "", 403

@app.route("/")
def index():
    return "ربات نئوویزا فعال است ⚖️"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
