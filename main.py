import os
import time
import telebot
from telebot import types
from flask import Flask, request
from datetime import datetime

# ===== تنظیمات اولیه =====
TOKEN = "7902857577:AAGsWarAtHg9A8yXDApkRzCVx7dR3wFc5u0"  # توکن مستقیم برای تستimport os
import time
import telebot
from telebot import types
from flask import Flask, request
from datetime import datetime

# ===== تنظیمات اولیه =====
TOKEN = "7902857577:AAGsWarAtHg9A8yXDApkRzCVx7dR3wFc5u0"  # توکن مستقیم برای تست
try:
    import sys
    print(f"🔍 دیباگ - نسخه پایتون: {sys.version}", flush=True)
except Exception as e:
    print(f"❌ خطا در بارگذاری پایتون: {e}", flush=True)
    raise

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# آدرس وبهوک
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://neovisa-1.onrender.com")  # فقط دامنه
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mysecret")

# ذخیره داده کاربران
user_data = {}

# ===== تنظیم خودکار Webhook =====
def setup_webhook():
    try:
        bot.remove_webhook()  # حذف Webhook قبلی
        time.sleep(1)  # زمان برای اطمینان
        webhook_url = f"{WEBHOOK_URL}/webhook/{WEBHOOK_SECRET}"  # فقط یک بار /webhook
        print(f"🚀 تلاش برای تنظیم Webhook به: {webhook_url}", flush=True)
        bot.set_webhook(url=webhook_url)
        info = bot.get_webhook_info()
        if info.url == webhook_url and info.has_custom_certificate is False and info.pending_update_count == 0:
            print(f"✅ Webhook با موفقیت تنظیم شد: {webhook_url}", flush=True)
        else:
            print(f"⚠ Webhook تنظیم نشد - وضعیت: {info.url}, Pending: {info.pending_update_count}", flush=True)
    except Exception as e:
        print(f"❌ خطا در تنظیم Webhook: {e}", flush=True)

setup_webhook()

# ===== منو و شروع =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {"step": "menu"}
    print(f"🔍 دیباگ - /start برای {cid}", flush=True)
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

# ===== درخواست جدید =====
@bot.message_handler(func=lambda message: message.text == '📝 درخواست جدید')
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

    user_data[cid] = {
        "timestamp": time.time(),
        "step": "type_select",
        "data": {}
    }
    print(f"🔍 دیباگ - درخواست جدید برای {cid}", flush=True)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇪🇸 اقامت اسپانیا", callback_data="spain"),
        types.InlineKeyboardButton("🌍 سایر کشورها", callback_data="other"),
        types.InlineKeyboardButton("❌ انصراف", callback_data="cancel")
    )
    bot.send_message(
        cid,
        "🔄 درخواست جدید\n\nلطفاً نوع خدمت مورد نظر خود را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ===== انتخاب کشور =====
@bot.callback_query_handler(func=lambda call: call.data in ["spain", "other"])
def handle_country_selection(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    print(f"🔍 دیباگ - انتخاب کشور برای {cid}: {call.data}", flush=True)
    if cid not in user_data or user_data[cid].get("step") != "type_select":
        bot.send_message(cid, "⚠ لطفاً ابتدا از منوی اصلی شروع کنید.")
        return

    user_data[cid]["data"]["service_type"] = call.data
    user_data[cid]["step"] = "name"
    try:
        bot.delete_message(cid, call.message.message_id)
    except Exception as e:
        print(f"🔍 دیباگ - خطا در حذف پیام: {e}", flush=True)
    bot.send_message(cid, "📝 لطفاً نام و نام خانوادگی خود را وارد کنید:")

# ===== انصراف =====
@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def handle_cancel(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    print(f"🔍 دیباگ - انصراف برای {cid}", flush=True)
    if cid in user_data:
        del user_data[cid]
    try:
        bot.delete_message(cid, call.message.message_id)
    except Exception as e:
        print(f"🔍 دیباگ - خطا در حذف پیام: {e}", flush=True)
    bot.send_message(cid, "❌ درخواست شما لغو شد. برای شروع مجدد /start را بزنید.")

# ===== دریافت نام =====
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "name")
def handle_name_input(message):
    cid = message.chat.id
    print(f"🔍 دیباگ - دریافت نام برای {cid}: {message.text}", flush=True)
    if len(message.text.strip()) < 3:
        bot.send_message(cid, "⚠ نام وارد شده بسیار کوتاه است.")
        return

    user_data[cid]["data"]["name"] = message.text
    user_data[cid]["step"] = "phone"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 ارسال شماره تلفن", request_contact=True))
    bot.send_message(cid, "📞 لطفاً شماره تماس خود را ارسال کنید:", reply_markup=markup)

# ===== دریافت تلفن =====
@bot.message_handler(content_types=['contact', 'text'], func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone")
def handle_phone_input(message):
    cid = message.chat.id
    print(f"🔍 دیباگ - دریافت تلفن برای {cid}: {message.text if message.text else message.contact.phone_number if message.contact else 'بدون شماره'}", flush=True)
    phone = None
    if message.contact:
        phone = message.contact.phone_number
    else:
        if not message.text or not message.text.strip().replace(" ", "").replace("-", "").replace("+", "").isdigit():
            bot.send_message(cid, "⚠ شماره معتبر نیست. دوباره وارد کنید.")
            return
        phone = message.text.strip()

    user_data[cid]["data"]["phone"] = phone
    user_data[cid]["step"] = "final_details"
    bot.send_message(cid, "📋 لطفاً توضیحات کامل درخواست خود را وارد کنید (حداقل ۲۰ کاراکتر):", reply_markup=types.ReplyKeyboardRemove())

# ===== دریافت توضیحات =====
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "final_details")
def handle_final_details(message):
    cid = message.chat.id
    print(f"🔍 دیباگ - دریافت جزئیات برای {cid}: {message.text}", flush=True)
    if len(message.text) < 20:
        bot.send_message(cid, "⚠ توضیحات خیلی کوتاه است (حداقل ۲۰ کاراکتر).")
        return

    user_data[cid]["data"]["details"] = message.text
    user_data[cid]["step"] = "completed"
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
    del user_data[cid]  # پاک کردن داده بعد از تکمیل
    send_welcome(message)  # بازگشت به منوی اصلی

# ===== سایر پیام‌ها =====
@bot.message_handler(func=lambda m: True)
def handle_unexpected_messages(message):
    cid = message.chat.id
    txt = message.text
    print(f"🔍 دیباگ - پیام ناموفق برای {cid}: {txt}", flush=True)
    if txt == 'ℹ اطلاعات حساب':
        if cid in user_data and user_data[cid].get('step') == 'completed':
            service_type = "اسپانیا" if user_data[cid]['data']['service_type'] == 'spain' else 'سایر کشورها'
            status = f"""
📊 وضعیت درخواست شما

• 📝 خدمت: {service_type}
• 🕒 زمان ثبت: {datetime.fromtimestamp(user_data[cid]['timestamp']).strftime('%Y-%m-%d %H:%M')}
• 📞 شماره تماس: {user_data[cid]['data']['phone']}
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

# ===== Flask Webhook =====
@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        try:
            json_string = request.get_data().decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            print(f"🔍 دیباگ - دریافت آپدیت برای {update.update_id}: {json_string[:100]}...", flush=True)
            bot.process_new_updates([update])
            return "", 200
        except Exception as e:
            print(f"❌ خطا در پردازش آپدیت: {e}", flush=True)
            return "", 500
    else:
        print(f"🔍 دیباگ - درخواست نامعتبر: {request.headers.get('content-type')}", flush=True)
        return "", 403

@app.route("/")
def index():
    return "✅ ربات خدمات مهاجرت فعال است 🌍"

@app.route("/health")
def health():
    return {"status": "healthy", "users": len(user_data), "time": datetime.now().isoformat()}

# ===== اجرای ربات =====
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
try:
    import sys
    print(f"🔍 دیباگ - نسخه پایتون: {sys.version}", flush=True)
except Exception as e:
    print(f"❌ خطا در بارگذاری پایتون: {e}", flush=True)
    raise

bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# آدرس وبهوک
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://neovisa-1.onrender.com")  # فقط دامنه
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mysecret")

# ذخیره داده کاربران
user_data = {}

# ===== تنظیم خودکار Webhook =====
def setup_webhook():
    try:
        bot.remove_webhook()  # حذف Webhook قبلی
        time.sleep(1)  # زمان برای اطمینان
        webhook_url = f"{WEBHOOK_URL}/webhook/{WEBHOOK_SECRET}"
        bot.set_webhook(url=webhook_url)
        info = bot.get_webhook_info()
        if info.url == webhook_url and info.has_custom_certificate is False:
            print(f"🚀 Webhook با موفقیت تنظیم شد: {webhook_url}", flush=True)
        else:
            print(f"⚠ Webhook تنظیم نشد: {info.url}", flush=True)
    except Exception as e:
        print(f"❌ خطا در تنظیم Webhook: {e}", flush=True)

setup_webhook()

# ===== منو و شروع =====
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {"step": "menu"}
    print(f"🔍 دیباگ - /start برای {cid}", flush=True)
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

# ===== درخواست جدید =====
@bot.message_handler(func=lambda message: message.text == '📝 درخواست جدید')
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

    user_data[cid] = {
        "timestamp": time.time(),
        "step": "type_select",
        "data": {}
    }
    print(f"🔍 دیباگ - درخواست جدید برای {cid}", flush=True)
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇪🇸 اقامت اسپانیا", callback_data="spain"),
        types.InlineKeyboardButton("🌍 سایر کشورها", callback_data="other"),
        types.InlineKeyboardButton("❌ انصراف", callback_data="cancel")
    )
    bot.send_message(
        cid,
        "🔄 درخواست جدید\n\nلطفاً نوع خدمت مورد نظر خود را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# ===== انتخاب کشور =====
@bot.callback_query_handler(func=lambda call: call.data in ["spain", "other"])
def handle_country_selection(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    print(f"🔍 دیباگ - انتخاب کشور برای {cid}: {call.data}", flush=True)
    if cid not in user_data or user_data[cid].get("step") != "type_select":
        bot.send_message(cid, "⚠ لطفاً ابتدا از منوی اصلی شروع کنید.")
        return

    user_data[cid]["data"]["service_type"] = call.data
    user_data[cid]["step"] = "name"
    try:
        bot.delete_message(cid, call.message.message_id)
    except Exception as e:
        print(f"🔍 دیباگ - خطا در حذف پیام: {e}", flush=True)
    bot.send_message(cid, "📝 لطفاً نام و نام خانوادگی خود را وارد کنید:")

# ===== انصراف =====
@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def handle_cancel(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    print(f"🔍 دیباگ - انصراف برای {cid}", flush=True)
    if cid in user_data:
        del user_data[cid]
    try:
        bot.delete_message(cid, call.message.message_id)
    except Exception as e:
        print(f"🔍 دیباگ - خطا در حذف پیام: {e}", flush=True)
    bot.send_message(cid, "❌ درخواست شما لغو شد. برای شروع مجدد /start را بزنید.")

# ===== دریافت نام =====
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "name")
def handle_name_input(message):
    cid = message.chat.id
    print(f"🔍 دیباگ - دریافت نام برای {cid}: {message.text}", flush=True)
    if len(message.text.strip()) < 3:
        bot.send_message(cid, "⚠ نام وارد شده بسیار کوتاه است.")
        return

    user_data[cid]["data"]["name"] = message.text
    user_data[cid]["step"] = "phone"
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📞 ارسال شماره تلفن", request_contact=True))
    bot.send_message(cid, "📞 لطفاً شماره تماس خود را ارسال کنید:", reply_markup=markup)

# ===== دریافت تلفن =====
@bot.message_handler(content_types=['contact', 'text'], func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone")
def handle_phone_input(message):
    cid = message.chat.id
    print(f"🔍 دیباگ - دریافت تلفن برای {cid}: {message.text if message.text else message.contact.phone_number if message.contact else 'بدون شماره'}", flush=True)
    phone = None
    if message.contact:
        phone = message.contact.phone_number
    else:
        if not message.text or not message.text.strip().replace(" ", "").replace("-", "").replace("+", "").isdigit():
            bot.send_message(cid, "⚠ شماره معتبر نیست. دوباره وارد کنید.")
            return
        phone = message.text.strip()

    user_data[cid]["data"]["phone"] = phone
    user_data[cid]["step"] = "final_details"
    bot.send_message(cid, "📋 لطفاً توضیحات کامل درخواست خود را وارد کنید (حداقل ۲۰ کاراکتر):", reply_markup=types.ReplyKeyboardRemove())

# ===== دریافت توضیحات =====
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "final_details")
def handle_final_details(message):
    cid = message.chat.id
    print(f"🔍 دیباگ - دریافت جزئیات برای {cid}: {message.text}", flush=True)
    if len(message.text) < 20:
        bot.send_message(cid, "⚠ توضیحات خیلی کوتاه است (حداقل ۲۰ کاراکتر).")
        return

    user_data[cid]["data"]["details"] = message.text
    user_data[cid]["step"] = "completed"
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
    del user_data[cid]  # پاک کردن داده بعد از تکمیل
    send_welcome(message)  # بازگشت به منوی اصلی

# ===== سایر پیام‌ها =====
@bot.message_handler(func=lambda m: True)
def handle_unexpected_messages(message):
    cid = message.chat.id
    txt = message.text
    print(f"🔍 دیباگ - پیام ناموفق برای {cid}: {txt}", flush=True)
    if txt == 'ℹ اطلاعات حساب':
        if cid in user_data and user_data[cid].get('step') == 'completed':
            service_type = "اسپانیا" if user_data[cid]['data']['service_type'] == 'spain' else 'سایر کشورها'
            status = f"""
📊 وضعیت درخواست شما

• 📝 خدمت: {service_type}
• 🕒 زمان ثبت: {datetime.fromtimestamp(user_data[cid]['timestamp']).strftime('%Y-%m-%d %H:%M')}
• 📞 شماره تماس: {user_data[cid]['data']['phone']}
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

# ===== Flask Webhook =====
@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        try:
            json_string = request.get_data().decode("utf-8")
            update = telebot.types.Update.de_json(json_string)
            print(f"🔍 دیباگ - دریافت آپدیت برای {update.update_id}: {json_string[:100]}...", flush=True)
            bot.process_new_updates([update])
            return "", 200
        except Exception as e:
            print(f"❌ خطا در پردازش آپدیت: {e}", flush=True)
            return "", 500
    else:
        print(f"🔍 دیباگ - درخواست نامعتبر: {request.headers.get('content-type')}", flush=True)
        return "", 403

@app.route("/")
def index():
    return "✅ ربات خدمات مهاجرت فعال است 🌍"

@app.route("/health")
def health():
    return {"status": "healthy", "users": len(user_data), "time": datetime.now().isoformat()}

# ===== اجرای ربات =====
if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)

