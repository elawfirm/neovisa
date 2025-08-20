import os
import time
import telebot
from telebot import types
from flask import Flask, request
from datetime import datetime

TOKEN = "7902857577:AAGsWarAtHg9A8yXDApkRzCVx7dR3wFc5u0"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://neovisa-1.onrender.com")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mysecret")

user_data = {}
completed_requests = {}

def setup_webhook():
    try:
        bot.remove_webhook()
        time.sleep(1)
        webhook_url = f"{WEBHOOK_URL}/webhook/{WEBHOOK_SECRET}"
        bot.set_webhook(url=webhook_url)
        info = bot.get_webhook_info()
        print(f"Webhook info: {info.url}, pending: {info.pending_update_count}")
    except Exception as e:
        print(f"Webhook error: {e}")

setup_webhook()

@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {"step": "menu"}
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    markup.add(
        types.KeyboardButton('📝 درخواست جدید'),
        types.KeyboardButton('ℹ اطلاعات حساب'),
        types.KeyboardButton('📞 پشتیبانی'),
        types.KeyboardButton('⚙ تنظیمات')
    )
    welcome_text = """
🌟 به ربات خدمات مهاجرت خوش آمدید 🌟

✅ با استفاده از این ربات می‌توانید:
• درخواست خدمات مهاجرت ثبت کنید
• از وضعیت درخواست‌های خود مطلع شوید
• با پشتیبانی در ارتباط باشید

لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
"""
    bot.send_message(cid, welcome_text, parse_mode="Markdown", reply_markup=markup)

@bot.message_handler(func=lambda m: m.text == '📝 درخواست جدید')
def handle_new_request_message(message):
    process_new_request(message)

@bot.callback_query_handler(func=lambda call: call.data == "new_request")
def handle_new_request_callback(call):
    process_new_request(call)

def process_new_request(call_or_message):
    if isinstance(call_or_message, types.CallbackQuery):
        cid = call_or_message.message.chat.id
        bot.answer_callback_query(call_or_message.id)
    else:
        cid = call_or_message.chat.id

    user_data[cid] = {"timestamp": time.time(), "step": "type_select", "data": {}}
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇪🇸 اقامت اسپانیا", callback_data="spain"),
        types.InlineKeyboardButton("🌍 سایر کشورها", callback_data="other"),
        types.InlineKeyboardButton("❌ انصراف", callback_data="cancel")
    )
    bot.send_message(cid, "🔄 درخواست جدید\n\nلطفاً نوع خدمت مورد نظر خود را انتخاب کنید:", reply_markup=markup)

@bot.callback_query_handler(func=lambda call: call.data in ["spain", "other"])
def handle_country_selection(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    if cid not in user_data or user_data[cid].get("step") != "type_select":
        bot.send_message(cid, "⚠ لطفاً ابتدا از منوی اصلی شروع کنید.")
        return
    user_data[cid]["data"]["service_type"] = call.data
    user_data[cid]["step"] = "name"
    try: bot.delete_message(cid, call.message.message_id)
    except: pass
    bot.send_message(cid, "📝 لطفاً نام و نام خانوادگی خود را وارد کنید:")

@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def handle_cancel(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    user_data.pop(cid, None)
    try: bot.delete_message(cid, call.message.message_id)
    except: pass
    bot.send_message(cid, "❌ درخواست شما لغو شد. برای شروع مجدد /start را بزنید.")

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "name")
def handle_name_input(message):
    cid = message.chat.id
    if len(message.text.strip()) < 3:
        bot.send_message(cid, "⚠ نام وارد شده بسیار کوتاه است.")
        return
    user_data[cid]["data"]["name"] = message.text
    user_data[cid]["step"] = "phone"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 ارسال شماره تلفن", request_contact=True))
    bot.send_message(cid, "📞 لطفاً شماره تماس خود را ارسال کنید:", reply_markup=markup)

@bot.message_handler(content_types=['contact', 'text'], func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone")
def handle_phone_input(message):
    cid = message.chat.id
    phone = None
    if message.contact: phone = message.contact.phone_number
    else:
        if not message.text or not message.text.strip().replace(" ", "").replace("-", "").replace("+", "").isdigit():
            bot.send_message(cid, "⚠ شماره معتبر نیست. دوباره وارد کنید.")
            return
        phone = message.text.strip()
    user_data[cid]["data"]["phone"] = phone
    user_data[cid]["step"] = "final_details"
    bot.send_message(cid, "📋 لطفاً توضیحات کامل درخواست خود را وارد کنید (حداقل ۲۰ کاراکتر):", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "final_details")
def handle_final_details(message):
    cid = message.chat.id
    if len(message.text) < 20:
        bot.send_message(cid, "⚠ توضیحات خیلی کوتاه است (حداقل ۲۰ کاراکتر).")
        return
    user_data[cid]["data"]["details"] = message.text
    user_data[cid]["step"] = "completed"
    completed_requests[cid] = user_data[cid]
    service_type = "اسپانیا" if user_data[cid]['data']['service_type'] == 'spain' else 'سایر کشورها'
    summary = f"""
✅ درخواست شما ثبت شد

• 👤 نام: {user_data[cid]['data']['name']}
• 📞 تلفن: {user_data[cid]['data']['phone']}
• 🌍 خدمات: {service_type}
• 📝 توضیحات: {user_data[cid]['data']['details'][:100]}...

📬 به زودی با شما تماس خواهیم گرفت.
"""
    bot.send_message(cid, summary, parse_mode="Markdown")
    del user_data[cid]
    send_welcome(message)

@bot.message_handler(func=lambda m: True)
def handle_unexpected_messages(message):
    cid = message.chat.id
    txt = message.text
    if txt == 'ℹ اطلاعات حساب':
        if cid in completed_requests:
            data = completed_requests[cid]["data"]
            service_type = "اسپانیا" if data['service_type']=='spain' else 'سایر کشورها'
            ts = datetime.fromtimestamp(completed_requests[cid]["timestamp"]).strftime('%Y-%m-%d %H:%M')
            status = f"""
📊 وضعیت درخواست شما

• 📝 خدمت: {service_type}
• 🕒 زمان ثبت: {ts}
• 📞 شماره تماس: {data['phone']}
• 📋 وضعیت: در حال بررسی
"""
            bot.send_message(cid, status, parse_mode="Markdown")
        else:
            bot.send_message(cid, "ℹ شما هیچ درخواست فعالی ندارید.")
    elif txt == '📞 پشتیبانی':
        bot.send_message(cid, "📞 برای ارتباط با پشتیبانی با شماره ۰۲۱-XXXXXXX تماس بگیرید.")
    elif txt == '⚙ تنظیمات':
        bot.send_message(cid, "⚙ بخش تنظیمات به زودی اضافه خواهد شد.")
    else:
        bot.send_message(cid, "🤔 لطفاً از منوی اصلی استفاده کنید.")

@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        try:
            json_string = request.get_data().decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            bot.process_new_updates([update])
            return "", 200
        except Exception as e:
            print(f"Webhook processing error: {e}")
            return "", 500
    else:
        return "", 403

@app.route("/")
def index(): return "✅ ربات خدمات مهاجرت فعال است 🌍"
@app.route("/health")
def health(): return {"status":"healthy","users":len(user_data),"time":datetime.now().isoformat()}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
