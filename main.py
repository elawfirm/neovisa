import os
import time
import telebot
from telebot import types
from flask import Flask, request
from datetime import datetime

# تنظیمات اولیه
TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
bot = telebot.TeleBot(TOKEN)
app = Flask(_name_)

# ذخیره داده‌های کاربران
user_data = {}

# صفحه شروع - کاملاً بازطراحی شده
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    
    # ایجاد منوی اصلی زیباتر
    markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True)
    btn1 = types.KeyboardButton('📝 درخواست جدید')
    btn2 = types.KeyboardButton('ℹ اطلاعات حساب')
    btn3 = types.KeyboardButton('📞 پشتیبانی')
    btn4 = types.KeyboardButton('⚙ تنظیمات')
    markup.add(btn1, btn2, btn3, btn4)
    
    # پیام خوشامدگویی بهبود یافته
    welcome_text = """
    🌟 به ربات خدمات مهاجرت خوش آمدید 🌟

    ✅ با استفاده از این ربات می‌توانید:
    • درخواست خدمات مهاجرت ثبت کنید
    • از وضعیت درخواست‌های خود مطلع شوید
    • با پشتیبانی در ارتباط باشید

    لطفاً یکی از گزینه‌های زیر را انتخاب کنید:
    """
    
    bot.send_message(cid, welcome_text, parse_mode="Markdown", reply_markup=markup)

# مدیریت درخواست جدید - بهبود یافته
@bot.message_handler(func=lambda message: message.text == '📝 درخواست جدید')
@bot.callback_query_handler(func=lambda call: call.data == "new_request")
def process_new_request(call_or_message):
    if hasattr(call_or_message, 'message'):
        cid = call_or_message.message.chat.id
        bot.answer_callback_query(call_or_message.id)
    else:
        cid = call_or_message.chat.id
    
    # بازنشانی داده کاربر
    user_data[cid] = {
        "timestamp": time.time(),
        "step": "type_select",
        "data": {}
    }
    
    # ایجاد کیبورد شفاف‌تر
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🇪🇸 اقامت اسپانیا", callback_data="spain")
    btn2 = types.InlineKeyboardButton("🌍 سایر کشورها", callback_data="other")
    btn3 = types.InlineKeyboardButton("❌ انصراف", callback_data="cancel")
    markup.add(btn1, btn2, btn3)
    
    bot.send_message(
        cid, 
        "🔄 درخواست جدید\n\nلطفاً نوع خدمت مورد نظر خود را انتخاب کنید:",
        parse_mode="Markdown", 
        reply_markup=markup
    )

# مدیریت انتخاب کشور
@bot.callback_query_handler(func=lambda call: call.data in ["spain", "other"])
def handle_country_selection(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    if cid not in user_data:
        bot.send_message(cid, "⚠ لطفاً ابتدا از منوی اصلی شروع کنید.")
        return
    
    user_data[cid]["data"]["service_type"] = call.data
    user_data[cid]["step"] = "name"
    
    # حذف کیبورد قبلی
    bot.delete_message(cid, call.message.message_id)
    
    bot.send_message(
        cid,
        "📝 لطفاً نام و نام خانوادگی خود را وارد کنید:",
        parse_mode="Markdown"
    )

# مدیریت انصراف
@bot.callback_query_handler(func=lambda call: call.data == "cancel")
def handle_cancel(call):
    cid = call.message.chat.id
    bot.answer_callback_query(call.id)
    
    if cid in user_data:
        del user_data[cid]
    
    bot.delete_message(cid, call.message.message_id)
    bot.send_message(cid, "❌ درخواست شما لغو شد. برای شروع مجدد /start را بزنید.")

# دریافت نام کاربر
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "name")
def handle_name_input(message):
    cid = message.chat.id
    
    if len(message.text.strip()) < 3:
        bot.send_message(cid, "⚠ نام وارد شده بسیار کوتاه است. لطفاً نام کامل خود را وارد کنید.")
        return
    
    user_data[cid]["data"]["name"] = message.text
    user_data[cid]["step"] = "phone"
    
    # ایجاد کیبورد برای اشتراک شماره تلفن
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    btn = types.KeyboardButton("📞 ارسال شماره تلفن", request_contact=True)
    markup.add(btn)
    
    bot.send_message(
        cid,
        "📞 لطفاً شماره تماس خود را ارسال کنید یا از دکمه زیر استفاده نمایید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# دریافت شماره تلفن
@bot.message_handler(content_types=['contact', 'text'], 
                    func=lambda message: user_data.get(message.chat.id, {}).get("step") == "phone")
def handle_phone_input(message):
    cid = message.chat.id
    phone = None
    
    if message.contact:
        phone = message.contact.phone_number
    else:
        # اعتبارسنجی شماره تلفن
        if not message.text.startswith('+') or not message.text[1:].isdigit() or len(message.text) < 10:
            bot.send_message(cid, "⚠ شماره تلفن معتبر نیست. لطفاً شماره را با فرمت بین‌المللی وارد کنید (مثال: +989123456789)")
            return
        phone = message.text
    
    user_data[cid]["data"]["phone"] = phone
    user_data[cid]["step"] = "final_details"
    
    # حذف کیبورد تلفن
    markup = types.ReplyKeyboardRemove()
    
    bot.send_message(
        cid,
        "📋 لطفاً توضیحات کامل در مورد درخواست خود را وارد کنید:\n(حداقل ۲۰ کاراکتر)",
        parse_mode="Markdown",
        reply_markup=markup
    )

# دریافت جزئیات نهایی
@bot.message_handler(func=lambda message: user_data.get(message.chat.id, {}).get("step") == "final_details")
def handle_final_details(message):
    cid = message.chat.id
    
    if len(message.text) < 20:
        bot.send_message(cid, "⚠ توضیحات بسیار کوتاه است. لطفاً حداقل ۲۰ کاراکتر وارد کنید.")
        return
    
    user_data[cid]["data"]["details"] = message.text
    user_data[cid]["step"] = "completed"
    
    # خلاصه درخواست
    summary = f"""
✅ درخواست شما ثبت شد

📋 خلاصه درخواست:
• 👤 نام: {user_data[cid]['data']['name']}
• 📞 تلفن: {user_data[cid]['data']['phone']}
• 🌍 خدمات: {'اسپانیا' if user_data[cid]['data']['service_type'] == 'spain' else 'سایر کشورها'}
• 📝 توضیحات: {user_data[cid]['data']['details'][:100]}...

📬 به زودی با شما تماس خواهیم گرفت.
    """
    
    bot.send_message(cid, summary, parse_mode="Markdown")
    
    # ارسال به ادمین (در صورت وجود)
    # send_to_admin(cid, user_data[cid]['data'])

# مدیریت پیام‌های غیرمنتظره - بهبود یافته
@bot.message_handler(func=lambda m: True)
def handle_unexpected_messages(message):
    cid = message.chat.id
    
    if message.text == 'ℹ اطلاعات حساب':
        if cid in user_data and 'step' in user_data[cid] and user_data[cid]['step'] == 'completed':
            bot.send_message(cid, "✅ شما یک درخواست فعال دارید. به زودی با شما تماس گرفته خواهد شد.")
        else:
            bot.send_message(cid, "ℹ شما هیچ درخواست فعالی ندارید.")
    elif message.text == '📞 پشتیبانی':
        bot.send_message(cid, "📞 برای ارتباط با پشتیبانی با شماره ۰۲۱-XXXXXXX تماس بگیرید.")
    elif message.text == '⚙ تنظیمات':
        bot.send_message(cid, "⚙ بخش تنظیمات به زودی اضافه خواهد شد.")
    else:
        current_step = user_data.get(cid, {}).get("step", "")
        
        if not current_step:
            bot.send_message(cid, "🤔 متوجه پیام شما نشدم. لطفاً از منوی اصلی استفاده کنید.")
        elif current_step == "phone":
            bot.send_message(cid, "📞 لطفاً شماره تماس خود را ارسال کنید.")
        elif current_step == "name":
            bot.send_message(cid, "📝 لطفاً نام و نام خانوادگی خود را وارد کنید.")
        elif current_step == "final_details":
            bot.send_message(cid, "📋 لطفاً توضیحات کامل درخواست خود را وارد کنید.")

# وب‌هوک و راه‌اندازی سرور
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
    return "✅ ربات خدمات مهاجرت فعال است 🌍"

@app.route("/health")
def health():
    return {
        "status": "healthy", 
        "users": len(user_data), 
        "timestamp": datetime.now().isoformat()
    }

if _name_ == "_main_":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 ربات خدمات مهاجرت روی پورت {port} راه‌اندازی شد")
    app.run(host="0.0.0.0", port=port)
