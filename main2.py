import telebot
from flask import Flask, request
import os

TOKEN = os.getenv("TOKEN", "7902857577:AAGsWarAtHg9A8yXDApkRzCVx7dR3wFc5u0")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://neovisa.onrender.com/webhook")
ADMIN_ID = 7549512366

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)
user_data = {}

@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {}
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🌍 ویزای توریستی", callback_data="visa_tour"),
               telebot.types.InlineKeyboardButton("💼 ویزای کاری", callback_data="visa_work"))
    markup.add(telebot.types.InlineKeyboardButton("🎓 ویزای تحصیلی", callback_data="visa_study"))
    bot.send_message(cid, "🌐 *خوش آمدید به neovisa!* ✈️\nما شما را در مسیر مهاجرت همراهی می‌کنیم.\nلطفاً نوع ویزای موردنظر را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["visa_tour", "visa_work", "visa_study"])
def process_visa_type(call):
    cid = call.message.chat.id
    print(f"Debug: Received visa callback data: {call.data} for chat {cid}")
    user_data[cid] = {"type": call.data, "step": "phone"}
    bot.answer_callback_query(call.id)
    markup = telebot.types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(telebot.types.KeyboardButton("📱 ارسال شماره"))
    bot.send_message(cid, "📞 لطفاً شماره تماس خود را وارد کنید یا دکمه زیر را بزنید:", reply_markup=markup)

@bot.message_handler(content_types=['contact'], func=lambda message: user_data.get(message.chat.id, {}).get("step") == "phone")
def handle_contact(message):
    cid = message.chat.id
    print(f"Debug: Received contact for chat {cid}, step: {user_data.get(cid, {}).get('step')}, phone: {message.contact.phone_number}")
    phone = message.contact.phone_number
    user_data[cid]["phone"] = phone
    user_data[cid]["step"] = "name"
    bot.send_message(cid, "✅ شماره شما ثبت شد. 📝 لطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "phone" and message.content_type == "text")
def handle_phone_text(message):
    cid = message.chat.id
    print(f"Debug: Received phone text for chat {cid}, phone: {message.text}")
    user_data[cid]["phone"] = message.text.strip()
    user_data[cid]["step"] = "name"
    bot.send_message(cid, "✅ شماره شما ثبت شد. 📝 لطفاً نام و نام خانوادگی خود را وارد کنید:", reply_markup=telebot.types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "name")
def handle_name(message):
    cid = message.chat.id
    user_data[cid]["name"] = message.text.strip()
    user_data[cid]["step"] = "details"
    send_visa_questions(cid)

def send_visa_questions(cid):
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(telebot.types.InlineKeyboardButton("🌴 مقصد سفر", callback_data="visa_destination"),
               telebot.types.InlineKeyboardButton("📅 مدت اقامت", callback_data="visa_duration"))
    markup.add(telebot.types.InlineKeyboardButton("💼 تجربه کاری", callback_data="visa_work_exp"),
               telebot.types.InlineKeyboardButton("🎓 مدارک تحصیلی", callback_data="visa_education"))
    print(f"Debug: Sending visa questions to chat {cid}")
    bot.send_message(cid, "🌐 *جزئیات ویزا:* ✈️\nلطفاً اطلاعات موردنیاز را انتخاب کنید:", parse_mode="Markdown", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["visa_destination", "visa_duration", "visa_work_exp", "visa_education"])
def process_visa_details(call):
    cid = call.message.chat.id
    print(f"Debug: Received visa detail callback: {call.data} for chat {cid}")
    user_data[cid]["subarea"] = call.data.replace("visa_", "")
    bot.answer_callback_query(call.id)
    if call.data == "visa_destination":
        bot.send_message(cid, "🌴 *مقصد سفر:* ✈️\nلطفاً نام کشور و هدف سفر (گردشگری، دیدار) را وارد کنید:")
    elif call.data == "visa_duration":
        bot.send_message(cid, "📅 *مدت اقامت:* ✈️\nلطفاً مدت زمان اقامت (به روز) و تاریخ سفر را وارد کنید:")
    elif call.data == "visa_work_exp":
        bot.send_message(cid, "💼 *تجربه کاری:* ✈️\nلطفاً سابقه کاری (شغل، مدت زمان، شرکت) را وارد کنید:")
    elif call.data == "visa_education":
        bot.send_message(cid, "🎓 *مدارک تحصیلی:* ✈️\nلطفاً مدرک تحصیلی، دانشگاه، و سال فارغ‌التحصیلی را وارد کنید:")

@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "details")
def handle_details(message):
    cid = message.chat.id
    user_data[cid]["details"] = message.text
    name = user_data[cid].get("name", "نام ناشناخته")
    phone = user_data[cid].get("phone", "شماره ناشناخته")
    visa_type = {
        "visa_tour": "ویزای توریستی",
        "visa_work": "ویزای کاری",
        "visa_study": "ویزای تحصیلی"
    }[user_data[cid]["type"]]
    bot.send_message(ADMIN_ID, f"🔔 *درخواست جدید neovisa:* ✈️\n👤 {name}\n📱 {phone}\n🌐 {visa_type}\n📝 {user_data[cid]['details']}", parse_mode="Markdown")
    bot.send_message(cid, "🎉 *درخواست شما با موفقیت ثبت شد!* ✅\n📞 تیم neovisa در اسرع وقت تماس می‌گیرد.", parse_mode="Markdown")
    del user_data[cid]

@app.route("/webhook", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        json_string = request.get_data().decode("utf-8")
        update = telebot.types.Update.de_json(json_string)
        bot.process_new_updates([update])
        return "", 200
    return "", 403

import telebot.apihelper
bot.remove_webhook()
bot.set_webhook(url=WEBHOOK_URL)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5002))
    app.run(host="0.0.0.0", port=port)
