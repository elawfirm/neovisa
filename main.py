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

# پیام خوش‌آمدگویی حرفه‌ای و مشتری‌جذب
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌍 اقامت اسپانیا", callback_data="spain"),
               types.InlineKeyboardButton("🌐 سایر کشورها", callback_data="other"))
    bot.send_message(cid, "⚖️ *خوش آمدید به نئوویزا!* 🌍\nما راهنمای شما در مسیر مهاجرت و حل مسائل حقوقی هستیم.\n📜 با انتخاب گزینه زیر، اولین قدم را بردارید:", parse_mode="Markdown", reply_markup=markup)

# پردازش انتخاب نوع مشاوره
@bot.callback_query_handler(func=lambda call: call.data in ["spain", "other"])
def process_consultation_type(call):
    cid = call.message.chat.id
    user_data[cid] = {"type": call.data, "step": "phone"}
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 ارسال شماره"))
    bot.edit_message_text(chat_id=cid, message_id=call.message.message_id, text="🌟 انتخاب شما ثبت شد! ⚖️")
    bot.send_message(cid, "📞 شماره تماس خود را وارد کنید یا دکمه زیر را بزنید:\nما در کنارتان هستیم!", reply_markup=markup)

# دریافت شماره تماس
@bot.message_handler(content_types=['contact'], func=lambda message: user_data.get(message.chat.id, {}).get("step") == "phone")
def handle_contact(message):
    cid = message.chat.id
    phone = message.contact.phone_number
    user_data[cid]["phone"] = phone
    user_data[cid]["step"] = "name"
    markup = types.ReplyKeyboardRemove()
    bot.send_message(cid, "✅ شماره شما ثبت شد! 🌍\n📝 لطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=markup)

# دریافت نام
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "name")
def handle_name(message):
    cid = message.chat.id
    user_data[cid]["name"] = message.text
    user_data[cid]["step"] = "details"
    if user_data[cid]["type"] == "spain":
        send_spain_questions(cid)
    else:
        send_other_questions(cid)

# سوالات تخصصی برای اقامت اسپانیا
def send_spain_questions(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎓 تحصیل", callback_data="spain_edu"),
               types.InlineKeyboardButton("💼 کار", callback_data="spain_work"))
    markup.add(types.InlineKeyboardButton("🏡 سرمایه‌گذاری", callback_data="spain_invest"))
    bot.send_message(cid, "🌍 *گزینه‌های اقامت اسپانیا:* ⚖️\nلطفاً یکی را انتخاب کنید و مسیر مهاجرت خود را روشن کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["spain_edu", "spain_work", "spain_invest"])
def process_spain_details(call):
    cid = call.message.chat.id
    user_data[cid]["details"] = call.data.replace("spain_", "")
    bot.answer_callback_query(call.id)
    if call.data == "spain_edu":
        bot.send_message(cid, "📜 نام دانشگاه، رشته، و سطح تحصیل (لیسانس/فوق/دکتری) را وارد کنید:")
    elif call.data == "spain_work":
        bot.send_message(cid, "💼 شغل، تجربه کاری (سال)، و مدرک تحصیلی را بنویسید:")
    elif call.data == "spain_invest":
        bot.send_message(cid, "🏡 میزان سرمایه (یورو)، نوع ملک، و منبع مالی را وارد کنید:")
    user_data[cid]["step"] = "final_details"

# سوالات تخصصی برای سایر کشورها
def send_other_questions(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇨🇦 کانادا", callback_data="other_canada"),
               types.InlineKeyboardButton("🇩🇪 آلمان", callback_data="other_germany"))
    markup.add(types.InlineKeyboardButton("🇦🇺 استرالیا", callback_data="other_australia"),
               types.InlineKeyboardButton("🇯🇵 ژاپن", callback_data="other_japan"))
    markup.add(types.InlineKeyboardButton("🇪🇺 شنگن", callback_data="other_schengen"),
               types.InlineKeyboardButton("🇬🇧 انگلستان", callback_data="other_uk"))
    bot.send_message(cid, "🌐 *کشور یا ویزای مورد نظر:* ⚖️\nلطفاً انتخاب کنید تا سفری مطمئن بسازیم:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["other_canada", "other_germany", "other_australia", "other_japan", "other_schengen", "other_uk"])
def process_other_details(call):
    cid = call.message.chat.id
    user_data[cid]["details"] = call.data.replace("other_", "")
    bot.answer_callback_query(call.id)
    if call.data == "other_canada":
        bot.send_message(cid, "🇨🇦 برنامه مهاجرتی، امتیاز CRS، و مدرک زبان (آیلتس/تافل) را وارد کنید:")
    elif call.data == "other_germany":
        bot.send_message(cid, "🇩🇪 نوع ویزا، مدرک زبان (آلمانی/انگلیسی)، و تجربه کاری را بنویسید:")
    elif call.data == "other_australia":
        bot.send_message(cid, "🇦🇺 نوع ویزا، امتیاز سیستم، و مدرک زبان (آیلتس/پری) را وارد کنید:")
    elif call.data == "other_japan":
        bot.send_message(cid, "🇯🇵 نوع ویزا، مدرک زبان ژاپنی (JLPT)، و سابقه کاری را بنویسید:")
    elif call.data == "other_schengen":
        bot.send_message(cid, "🇪🇺 هدف ویزا، مدت اقامت (روز)، و مدارک دعوت‌نامه (در صورت وجود) را مشخص کنید:")
    elif call.data == "other_uk":
        bot.send_message(cid, "🇬🇧 نوع ویزا (تحصیل، کار، توریستی)، مدرک زبان (آیلتس/UKVI)، و هدف مهاجرت را وارد کنید:")
    user_data[cid]["step"] = "final_details"

# دریافت جزئیات نهایی
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "final_details")
def handle_final_details(message):
    cid = message.chat.id
    details = message.text
    user_data[cid]["details"] += f" | {details}" if user_data[cid].get("details") else details
    name = user_data[cid]["name"]
    phone = user_data[cid]["phone"]
    consultation_type = "اقامت اسپانیا" if user_data[cid]["type"] == "spain" else f"اقامت {user_data[cid]['details'].split('|')[0]}"
    bot.send_message(ADMIN_ID, f"🔔 *درخواست جدید نئوویزا:* ⚖️\n👤 {name}\n📱 {phone}\n🌐 {consultation_type}\n📝 {details}", parse_mode="Markdown")
    bot.send_message(cid, "🎉 *درخواست شما ثبت شد!* ✅\n📞 تیم نئوویزا به زودی با شما تماس می‌گیرد.\n🌍 با ما به رویاهایتان نزدیک‌تر شوید!", parse_mode="Markdown")
    del user_data[cid]  # پاک کردن داده‌ها بعد از تکمیل

# پیکربندی webhook
@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "", 403

@app.route("/")
def index():
    return "ربات نئوویزا فعال است ⚖️"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))  # پورت پیش‌فرض Render
    app.run(host="0.0.0.0", port=port)
