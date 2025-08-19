import telebot
from flask import Flask, request
import os
import time

# دریافت متغیرهای محیطی
TOKEN = os.getenv("TOKEN", "7902857577:AAGsWarAtHg9A8yXDApkRzCVx7dR3wFc5u0")
WEBHOOK_URL = "https://neovisa-1.onrender.com/webhook"  # آدرس ثابت
ADMIN_ID = 7549512366

# تنظیم ربات
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_data = {}

# تنظیم خودکار Webhook
def set_webhook():
    try:
        bot.remove_webhook()  # حذف Webhook قبلی
        time.sleep(1)  # صبر برای اطمینان
        status = bot.set_webhook(url=WEBHOOK_URL)
        if status:
            print(f"Webhook successfully set to {WEBHOOK_URL}")
        else:
            print(f"Failed to set webhook to {WEBHOOK_URL}")
    except Exception as e:
        print(f"Error setting webhook: {e}")

# فراخوانی تنظیم Webhook موقع شروع
set_webhook()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {}
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🌍 ویزای توریستی", callback_data="visa_tour"))
    markup.add(telebot.types.InlineKeyboardButton("💼 ویزای کاری", callback_data="visa_work"))
    markup.add(telebot.types.InlineKeyboardButton("🎓 ویزای تحصیلی", callback_data="visa_study"))
    bot.send_message(cid, "🌐 *خوش آمدید به neovisa!* ✈️\nلطفاً نوع ویزای موردنظر را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["visa_tour", "visa_work", "visa_study"])
def process_visa_type(call):
    cid = call.message.chat.id
    user_data[cid] = {"type": call.data, "step": "phone"}
    bot.answer_callback_query(call.id)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(telebot.types.KeyboardButton("📱 ارسال شماره"))
    bot.send_message(cid, "📞 لطفاً شماره تماس خود را وارد کنید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'], func=lambda message: user_data.get(message.chat.id, {}).get("step") == "phone")
def handle_contact(message):
    cid = message.chat.id
    phone = message.contact.phone_number
    user_data[cid]["phone"] = phone
    user_data[cid]["step"] = "name"
    bot.send_message(cid, "✅ شماره شما ثبت شد. 📝 لطفاً نام خود را وارد کنید:", reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "name")
def handle_name(message):
    cid = message.chat.id
    user_data[cid]["name"] = message.text.strip()
    name = user_data[cid].get("name", "نام ناشناخته")
    phone = user_data[cid].get("phone", "شماره ناشناخته")
    visa_type = {"visa_tour": "توریستی", "visa_work": "کاری", "visa_study": "تحصیلی"}[user_data[cid]["type"]]
    bot.send_message(ADMIN_ID, f"🔔 درخواست جدید neovisa: 👤 {name} 📱 {phone} 🌐 {visa_type}", parse_mode="Markdown")
    bot.send_message(cid, "🎉 درخواست شما ثبت شد! 📞 تیم neovisa تماس می‌گیرد.", parse_mode="Markdown")
    del user_data[cid]

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "Unsupported", 403

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # پورت Render
    app.run(host="0.0.0.0", port=port)
