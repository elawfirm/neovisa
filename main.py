import telebot
from telebot import types
from flask import Flask, request
import os
import time
import threading
from datetime import datetime
import re

# 🔑 تنظیمات
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
        print("✅ Webhook set successfully")
    except Exception as e:
        print("❌ Webhook error:", e)

set_webhook()

# 🧹 پاکسازی داده‌های قدیمی
def cleanup_old_data():
    while True:
        time.sleep(3600)
        current_time = time.time()
        to_delete = []
        
        for cid, data in user_data.items():
            if current_time - data.get('timestamp', 0) > 7200:
                to_delete.append(cid)
        
        for cid in to_delete:
            del user_data[cid]
            print(f"🧹 Cleaned up data for user {cid}")

cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
cleanup_thread.start()

# 🎯 سوالات ساختاریافته
SPAIN_QUESTIONS = {
    "edu": [
        {
            "question": "🎓 *مقطع تحصیلی مورد نظر:*",
            "type": "options",
            "options": ["کارشناسی", "کارشناسی ارشد", "دکترا", "زبان اسپانیایی"]
        },
        {
            "question": "📚 *رشته تحصیلی مورد نظر:*",
            "type": "text"
        },
        {
            "question": "🏫 *آیا دانشگاه خاصی مد نظر دارید؟*",
            "type": "options",
            "options": ["بله", "خیر"]
        },
        {
            "question": "🗣️ *مدرک زبان اسپانیایی:*",
            "type": "options", 
            "options": ["DELE A1/A2", "DELE B1/B2", "DELE C1/C2", "ندارم"]
        }
    ],
    "work": [
        {
            "question": "💼 *نوع ویزای کاری مورد نظر:*",
            "type": "options",
            "options": ["Highly Qualified Professional", "کارمند عادی", "انتقال داخل شرکتی", "فریلنسر"]
        },
        {
            "question": "⏳ *سابقه کاری (به سال):*",
            "type": "text"
        },
        {
            "question": "🔧 *زمینه تخصصی:*",
            "type": "text"
        },
        {
            "question": "🗣️ *سطح زبان اسپانیایی:*",
            "type": "options",
            "options": ["A1/A2", "B1/B2", "C1/C2", "ندارم"]
        }
    ]
}

COUNTRY_QUESTIONS = {
    "canada": [
        {
            "question": "🇨🇦 *برنامه مهاجرتی مورد نظر:*",
            "type": "options",
            "options": ["Express Entry", "Provincial Nominee", "Quebec Immigration", "Startup Visa"]
        },
        {
            "question": "📊 *مدرک زبان:*",
            "type": "options",
            "options": ["IELTS", "CELPIP", "TEF", "ندارم"]
        },
        {
            "question": "🎯 *امتیاز CRS تقریبی:*",
            "type": "text"
        },
        {
            "question": "🔧 *NOC Code (اگر می‌دانید):*",
            "type": "text"
        }
    ],
    "germany": [
        {
            "question": "🇩🇪 *نوع ویزای مورد نظر:*",
            "type": "options",
            "options": ["Blue Card", "Work Visa", "Job Seeker", "Student Visa"]
        },
        {
            "question": "🗣️ *مدرک زبان آلمانی:*",
            "type": "options",
            "options": ["A1", "A2", "B1", "B2", "C1", "ندارم"]
        },
        {
            "question": "🎓 *مدرک تحصیلی:*",
            "type": "text"
        },
        {
            "question": "⏳ *سابقه کاری (سال):*",
            "type": "text"
        }
    ]
}

# 🎉 شروع ربات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {
        "timestamp": time.time(),
        "step": "type_select",
        "answers": {}
    }
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🌍 اقامت اسپانیا", callback_data="spain")
    btn2 = types.InlineKeyboardButton("🌐 سایر کشورها", callback_data="other")
    markup.add(btn1, btn2)
    
    bot.send_message(
        cid,
        "⚖️ *خوش آمدید به نئوویزا!* 🌍\n\nلطفاً نوع خدمت مورد نظر را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# 📌 انتخاب نوع مشاوره
@bot.callback_query_handler(func=lambda call: call.data in ["spain", "other"])
def process_consultation_type(call):
    cid = call.message.chat.id
    user_data[cid] = {
        "type": call.data,
        "step": "phone",
        "timestamp": time.time(),
        "answers": {},
        "current_question": 0
    }
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        chat_id=cid, 
        message_id=call.message.message_id, 
        text="✅ *انتخاب شما ثبت شد!*",
        parse_mode="Markdown"
    )
    
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 ارسال شماره تماس", request_contact=True))
    
    bot.send_message(
        cid, 
        "📞 لطفاً شماره تماس خود را ارسال کنید:\n\nمی‌توانید از دکمه زیر استفاده کنید یا شماره را به صورت متن وارد نمایید.",
        reply_markup=markup
    )

# 📌 دریافت شماره تماس
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    cid = message.chat.id
    if user_data.get(cid, {}).get("step") != "phone":
        return
        
    user_data[cid]["answers"]["phone"] = message.contact.phone_number
    user_data[cid]["step"] = "name"
    user_data[cid]["timestamp"] = time.time()
    
    bot.send_message(
        cid, 
        "✅ شماره تماس ثبت شد!\n\n📝 لطفاً نام و نام خانوادگی خود را وارد کنید:",
        reply_markup=types.ReplyKeyboardRemove()
    )

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone")
def handle_phone_text(message):
    cid = message.chat.id
    phone = message.text.strip()
    
    # اعتبارسنجی شماره تلفن
    if not re.match(r'^[\d\s\+\-\(\)]{10,15}$', phone):
        bot.send_message(cid, "❌ شماره تلفن نامعتبر است. لطفاً شماره معتبر وارد کنید:")
        return
    
    user_data[cid]["answers"]["phone"] = phone
    user_data[cid]["step"] = "name"
    user_data[cid]["timestamp"] = time.time()
    
    bot.send_message(
        cid, 
        "✅ شماره تماس ثبت شد!\n\n📝 لطفاً نام و نام خانوادگی خود را وارد کنید:",
        reply_markup=types.ReplyKeyboardRemove()
    )

# 📌 دریافت نام
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "name")
def handle_name(message):
    cid = message.chat.id
    name = message.text.strip()
    
    if len(name) < 3:
        bot.send_message(cid, "❌ نام وارد شده بسیار کوتاه است. لطفاً نام کامل وارد کنید:")
        return
    
    user_data[cid]["answers"]["name"] = name
    user_data[cid]["timestamp"] = time.time()
    
    if user_data[cid].get("type") == "spain":
        ask_spain_visa_type(cid)
    else:
        ask_country_selection(cid)

# 📌 انتخاب نوع ویزای اسپانیا
def ask_spain_visa_type(cid):
    user_data[cid]["step"] = "spain_visa_type"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🎓 تحصیلی", callback_data="spain_edu")
    btn2 = types.InlineKeyboardButton("💼 کاری", callback_data="spain_work")
    btn3 = types.InlineKeyboardButton("🏡 سرمایه‌گذاری", callback_data="spain_invest")
    btn4 = types.InlineKeyboardButton("👨‍👩‍👧‍👦 خانوادگی", callback_data="spain_family")
    markup.add(btn1, btn2, btn3, btn4)
    
    bot.send_message(
        cid, 
        "🌍 *نوع ویزای اسپانیا را انتخاب کنید:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# 📌 انتخاب کشور برای سایر کشورها
def ask_country_selection(cid):
    user_data[cid]["step"] = "country_select"
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    countries = [
        ("🇨🇦 کانادا", "country_canada"),
        ("🇩🇪 آلمان", "country_germany"),
        ("🇦🇺 استرالیا", "country_australia"),
        ("🇬🇧 انگلستان", "country_uk"),
        ("🇺🇸 آمریکا", "country_usa"),
        ("🇯🇵 ژاپن", "country_japan")
    ]
    
    for text, data in countries:
        markup.add(types.InlineKeyboardButton(text, callback_data=data))
    
    bot.send_message(
        cid, 
        "🌐 *کشور مورد نظر خود را انتخاب کنید:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

# 📌 پردازش انتخاب کشور
@bot.callback_query_handler(func=lambda call: call.data.startswith(("country_", "spain_")))
def handle_selection(call):
    cid = call.message.chat.id
    
    if call.data.startswith("country_"):
        country = call.data.replace("country_", "")
        user_data[cid]["answers"]["country"] = country
        questions = COUNTRY_QUESTIONS.get(country, [])
    else:
        visa_type = call.data.replace("spain_", "")
        user_data[cid]["answers"]["visa_type"] = visa_type
        questions = SPAIN_QUESTIONS.get(visa_type, [])
    
    user_data[cid]["step"] = "asking_questions"
    user_data[cid]["questions"] = questions
    user_data[cid]["current_question"] = 0
    user_data[cid]["timestamp"] = time.time()
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        chat_id=cid,
        message_id=call.message.message_id,
        text="✅ انتخاب شما ثبت شد!",
        parse_mode="Markdown"
    )
    
    ask_next_question(cid)

# 📌 پرسش سوالات مرحله‌ای
def ask_next_question(cid):
    questions = user_data[cid].get("questions", [])
    current_q = user_data[cid]["current_question"]
    
    if current_q >= len(questions):
        user_data[cid]["step"] = "finalizing"
        finalize_request(cid)
        return
    
    question_data = questions[current_q]
    
    if question_data["type"] == "text":
        bot.send_message(cid, question_data["question"])
    elif question_data["type"] == "options":
        markup = types.InlineKeyboardMarkup()
        for option in question_data["options"]:
            markup.add(types.InlineKeyboardButton(option, callback_data=f"ans_{current_q}_{option}"))
        bot.send_message(cid, question_data["question"], reply_markup=markup)

# 📌 دریافت پاسخ‌های گزینه‌ای
@bot.callback_query_handler(func=lambda call: call.data.startswith("ans_"))
def handle_option_answer(call):
    cid = call.message.chat.id
    parts = call.data.split('_')
    question_index = int(parts[1])
    answer = '_'.join(parts[2:])
    
    user_data[cid]["answers"][f"q{question_index}"] = answer
    user_data[cid]["current_question"] += 1
    user_data[cid]["timestamp"] = time.time()
    
    bot.answer_callback_query(call.id)
    bot.edit_message_text(
        chat_id=cid,
        message_id=call.message.message_id,
        text=f"✅ {answer}",
        parse_mode="Markdown"
    )
    
    ask_next_question(cid)

# 📌 دریافت پاسخ‌های متنی
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "asking_questions")
def handle_text_answer(message):
    cid = message.chat.id
    questions = user_data[cid].get("questions", [])
    current_q = user_data[cid]["current_question"]
    
    if current_q >= len(questions):
        return
    
    question_data = questions[current_q]
    
    if question_data["type"] == "text":
        user_data[cid]["answers"][f"q{current_q}"] = message.text
        user_data[cid]["current_question"] += 1
        user_data[cid]["timestamp"] = time.time()
        
        ask_next_question(cid)

# 📌 نهایی‌سازی درخواست
def finalize_request(cid):
    user_data[cid]["step"] = "completed"
    
    # جمع‌آوری اطلاعات
    name = user_data[cid]["answers"].get("name", "نامشخص")
    phone = user_data[cid]["answers"].get("phone", "نامشخص")
    
    if user_data[cid].get("type") == "spain":
        visa_type = user_data[cid]["answers"].get("visa_type", "نامشخص")
        consultation_type = f"اسپانیا - {visa_type}"
    else:
        country = user_data[cid]["answers"].get("country", "نامشخص")
        consultation_type = f"{country}"
    
    # ایجاد خلاصه اطلاعات
    summary = f"👤 نام: {name}\n📞 تلفن: {phone}\n🌍 نوع: {consultation_type}\n\n"
    
    # اضافه کردن پاسخ‌ها
    for i in range(len(user_data[cid].get("questions", []))):
        answer = user_data[cid]["answers"].get(f"q{i}", "پاسخ داده نشد")
        summary += f"📝 سوال {i+1}: {answer}\n"
    
    # ارسال به ادمین
    try:
        bot.send_message(
            ADMIN_ID,
            f"🔔 *درخواست جدید نئوویزا:*\n\n{summary}",
            parse_mode="Markdown"
        )
    except Exception as e:
        print(f"❌ خطا در ارسال به ادمین: {e}")
    
    # ارسال تأیید به کاربر
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 درخواست جدید", callback_data="new_request"))
    
    bot.send_message(
        cid,
        "🎉 *درخواست شما با موفقیت ثبت شد!*\n\n✅ اطلاعات شما برای تیم نئوویزا ارسال شد.\n📞 همکاران ما طی ۲۴ ساعت آینده با شما تماس خواهند گرفت.\n\nبرای ثبت درخواست جدید می‌توانید از دکمه زیر استفاده کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# 📌 درخواست جدید
@bot.callback_query_handler(func=lambda call: call.data == "new_request")
def handle_new_request(call):
    cid = call.message.chat.id
    user_data[cid] = {
        "timestamp": time.time(),
        "step": "type_select",
        "answers": {}
    }
    
    bot.answer_callback_query(call.id)
    
    markup = types.InlineKeyboardMarkup(row_width=2)
    btn1 = types.InlineKeyboardButton("🌍 اقامت اسپانیا", callback_data="spain")
    btn2 = types.InlineKeyboardButton("🌐 سایر کشورها", callback_data="other")
    markup.add(btn1, btn2)
    
    bot.send_message(
        cid,
        "🔄 *درخواست جدید*\n\nلطفاً نوع خدمت مورد نظر را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

# 📌 مدیریت پیام‌های غیرمنتظره
@bot.message_handler(func=lambda m: True)
def handle_unexpected_messages(message):
    cid = message.chat.id
    current_step = user_data.get(cid, {}).get("step", "")
    
    if not current_step:
        bot.send_message(cid, "🤔 متوجه نشدم! لطفاً /start را بزنید.")
    elif current_step == "phone":
        bot.send_message(cid, "📞 لطفاً شماره تماس خود را ارسال کنید.")
    elif current_step == "name":
        bot.send_message(cid, "📝 لطفاً نام و نام خانوادگی خود را وارد کنید.")
    elif current_step == "asking_questions":
        bot.send_message(cid, "📋 لطفاً به سوال فعلی پاسخ دهید.")
    else:
        bot.send_message(cid, "⚖️ لطفاً از منوی ربات استفاده کنید.")

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
    return "✅ ربات نئوویزا فعال است ⚖️"

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Starting bot on port {port}")
    app.run(host="0.0.0.0", port=port)
