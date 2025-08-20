import telebot
from telebot import types
from flask import Flask, request
import os
import time

# دریافت متغیرهای محیطی
TOKEN = os.getenv("TOKEN", "7902857577:AAGsWarAtHg9A8yXDApkRzCVx7dR3wFc5u0")
ADMIN_ID = os.getenv("ADMIN_ID", 7549512366)
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://neovisa-1.onrender.com/webhook")

# تنظیم ربات
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_data = {}

# تنظیم خودکار Webhook
def set_webhook():
    try:
        bot.remove_webhook()
        time.sleep(1)
        bot.set_webhook(url=WEBHOOK_URL)
        print(f"🔧 Webhook تنظیم شد: {WEBHOOK_URL}")
    except Exception as e:
        print(f"❌ خطا در تنظیم Webhook: {e}")

set_webhook()

# پیام خوش‌آمدگویی
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {"step": "type_select"}
    print(f"🔍 دیباگ - /start برای {cid}")
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌍 اقامت اسپانیا", callback_data="spain"),
               types.InlineKeyboardButton("🌐 سایر کشورها", callback_data="other"))
    bot.send_message(cid, "⚖️ *خوش آمدید به نئوویزا!* 🌍\n📜 نوع خدمت را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

# پردازش انتخاب نوع مشاوره
@bot.callback_query_handler(func=lambda call: call.data in ["spain", "other"])
def process_consultation_type(call):
    cid = call.message.chat.id
    user_data[cid] = {"type": call.data, "step": "phone"}
    print(f"🔍 دیباگ - نوع مشاوره برای {cid}: {call.data}")
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 ارسال شماره", request_contact=True))
    bot.edit_message_text(chat_id=cid, message_id=call.message.message_id, text="🌟 انتخاب ثبت شد!")
    bot.send_message(cid, "📞 شماره تماس خود را وارد کنید:", reply_markup=markup)

# دریافت شماره تماس (از دکمه)
@bot.message_handler(content_types=['contact'], func=lambda message: user_data.get(message.chat.id, {}).get("step") == "phone")
def handle_contact(message):
    cid = message.chat.id
    user_data[cid] = user_data.get(cid, {})
    user_data[cid]["phone"] = message.contact.phone_number
    user_data[cid]["step"] = "name"
    print(f"🔍 دیباگ - شماره برای {cid}: {user_data[cid]['phone']}")
    markup = types.ReplyKeyboardRemove()
    bot.send_message(cid, "✅ شماره ثبت شد!\n📝 نام و نام خانوادگی را وارد کنید:", reply_markup=markup)

# دریافت شماره تماس (ورودی متنی)
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "phone" and message.content_type == "text")
def handle_phone_text(message):
    cid = message.chat.id
    user_data[cid] = user_data.get(cid, {})
    user_data[cid]["phone"] = message.text.strip()
    user_data[cid]["step"] = "name"
    print(f"🔍 دیباگ - شماره متنی برای {cid}: {user_data[cid]['phone']}")
    markup = types.ReplyKeyboardRemove()
    bot.send_message(cid, "✅ شماره ثبت شد!\n📝 نام و نام خانوادگی را وارد کنید:", reply_markup=markup)

# دریافت نام
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "name" and message.content_type == "text")
def handle_name(message):
    cid = message.chat.id
    user_data[cid] = user_data.get(cid, {})
    if "name" not in user_data[cid]:
        user_data[cid]["name"] = message.text.strip()
        user_data[cid]["step"] = "details"
        print(f"🔍 دیباگ - نام برای {cid}: {user_data[cid]['name']}")
        bot.send_message(cid, "📝 جزئیات درخواست خود را وارد کنید (مثلاً تحصیل، کار، یا مهاجرت):")
    else:
        bot.send_message(cid, "❌ خطا! لطفاً دوباره /start را بزنید.")

# دریافت جزئیات نهایی
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "details" and message.content_type == "text")
def handle_final_details(message):
    cid = message.chat.id
    user_data[cid] = user_data.get(cid, {})
    print(f"🔍 دیباگ - جزئیات نهایی برای {cid}: {message.text}")
    if all(key in user_data[cid] for key in ["name", "phone", "type"]):
        details = message.text
        user_data[cid]["details"] = details
        name = user_data[cid]["name"]
        phone = user_data[cid]["phone"]
        consultation_type = "اقامت اسپانیا" if user_data[cid]["type"] == "spain" else "اقامت سایر کشورها"
        bot.send_message(ADMIN_ID, f"🔔 *درخواست جدید نئوویزا:* ⚖️\n👤 {name}\n📱 {phone}\n🌐 {consultation_type}\n📝 {details}", parse_mode="Markdown")
        markup = types.InlineKeyboardMarkup()
        markup.add(types.InlineKeyboardButton("🔄 درخواست جدید", callback_data="new_request"))
        bot.send_message(cid, "🎉 درخواست شما ثبت شد! تیم نئوویزا به زودی تماس می‌گیرد.\nبرای درخواست جدید، کلیک کنید:", reply_markup=markup)
        del user_data[cid]
    else:
        bot.send_message(cid, f"❌ داده‌ها ناقصند! موجود: {user_data[cid]}. لطفاً دوباره /start را بزنید.")

# پردازش درخواست جدید
@bot.callback_query_handler(func=lambda call: call.data == "new_request")
def process_new_request(call):
    cid = call.message.chat.id
    user_data[cid] = {"step": "type_select"}
    print(f"🔍 دیباگ - درخواست جدید برای {cid}")
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌍 اقامت اسپانیا", callback_data="spain"),
               types.InlineKeyboardButton("🌐 سایر کشورها", callback_data="other"))
    bot.send_message(cid, "⚖️ *خوش آمدید به نئوویزا!* 🌍\n📜 نوع خدمت را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

# مدیریت پیام‌های ناموفق
@bot.message_handler(func=lambda message: True)
def handle_unknown(message):
    cid = message.chat.id
    if cid not in user_data or user_data[cid].get("step") is None:
        print(f"🔍 دیباگ - پیام ناموفق برای {cid}")
        bot.send_message(cid, "❌ دستور نامعتبر! لطفاً با /start شروع کنید.")

# پیکربندی webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        print(f"🔍 دیباگ - دریافت آپدیت برای {update.update_id}: {json_string[:100]}...")  # 100 کاراکتر اول
        bot.process_new_updates([update])
        return "", 200
    return "", 403

@app.route("/")
def index():
    return "ربات نئوویزا فعال است ⚖️"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))  # پورت پیش‌فرض برای VPS
    app.run(host="0.0.0.0", port=port)
