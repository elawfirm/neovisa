import telebot
from telebot import types
from flask import Flask, request
import os
import time
import threading
from datetime import datetime

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

# 🧵 اجرای پاکسازی در thread جداگانه
cleanup_thread = threading.Thread(target=cleanup_old_data, daemon=True)
cleanup_thread.start()

# 📝 تابع لاگ برای دیباگ
def log_user_data(cid):
    print(f"📊 User {cid} data: {user_data.get(cid, {})}")

# 🎉 شروع ربات
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {
        "timestamp": time.time(),
        "step": "type_select"
    }
    
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
    user_data[cid] = {
        "type": call.data,
        "step": "phone",
        "timestamp": time.time()
    }
    
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 ارسال شماره", request_contact=True))
    
    bot.edit_message_text(
        chat_id=cid, 
        message_id=call.message.message_id, 
        text="🌟 انتخاب شما ثبت شد!"
    )
    
    bot.send_message(
        cid, 
        "📞 لطفاً شماره تماس خود را ارسال کنید:",
        reply_markup=markup
    )

# 📌 دریافت شماره (از دکمه)
@bot.message_handler(content_types=['contact'], func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone")
def handle_contact(message):
    cid = message.chat.id
    user_data[cid]["phone"] = message.contact.phone_number
    user_data[cid]["step"] = "name"
    user_data[cid]["timestamp"] = time.time()
    
    bot.send_message(
        cid, 
        "✅ شماره تماس ثبت شد!\n📝 لطفاً نام و نام خانوادگی خود را وارد کنید:",
        reply_markup=types.ReplyKeyboardRemove()
    )

# 📌 دریافت شماره (متنی)
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone" and m.content_type == "text")
def handle_phone_text(message):
    cid = message.chat.id
    
    phone = message.text.strip()
    if not phone.replace('+', '').replace(' ', '').isdigit():
        bot.send_message(cid, "❌ شماره تلفن نامعتبر است. لطفاً شماره معتبر وارد کنید:")
        return
    
    user_data[cid]["phone"] = phone
    user_data[cid]["step"] = "name"
    user_data[cid]["timestamp"] = time.time()
    
    bot.send_message(
        cid, 
        "✅ شماره تماس ثبت شد!\n📝 لطفاً نام و نام خانوادگی خود را وارد کنید:",
        reply_markup=types.ReplyKeyboardRemove()
    )

# 📌 دریافت نام
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "name" and m.content_type == "text")
def handle_name(message):
    cid = message.chat.id
    user_data[cid]["name"] = message.text.strip()
    user_data[cid]["step"] = "country_select"
    user_data[cid]["timestamp"] = time.time()
    
    if user_data[cid].get("type") == "spain":
        send_spain_questions(cid)
    else:
        send_other_questions(cid)

# 📌 گزینه‌های اسپانیا
def send_spain_questions(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🎓 تحصیلی", callback_data="spain_edu"),
        types.InlineKeyboardButton("💼 کاری", callback_data="spain_work"),
        types.InlineKeyboardButton("🏡 سرمایه‌گذاری", callback_data="spain_invest"),
        types.InlineKeyboardButton("👨‍👩‍👧‍👦 خانوادگی", callback_data="spain_family"),
    )
    
    bot.send_message(
        cid, 
        "🌍 *گزینه‌های اقامت اسپانیا:*\nلطفاً نوع ویزای مورد نظر را انتخاب کنید:",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data in ["spain_edu", "spain_work", "spain_invest", "spain_family"])
def process_spain_details(call):
    cid = call.message.chat.id
    user_data[cid]["visa_type"] = call.data.replace("spain_", "")
    user_data[cid]["step"] = "spain_details"
    user_data[cid]["timestamp"] = time.time()
    
    bot.answer_callback_query(call.id)

    questions = {
        "edu": """
🎓 *ویزای تحصیلی اسپانیا - اطلاعات مورد نیاز:*

1. *مقطع تحصیلی مورد نظر:*
   - کارشناسی 🎓
   - کارشناسی ارشد 📚  
   - دکترا 🎓
   - زبان اسپانیایی 📖

2. *رشته تحصیلی:*
   - رشته مورد نظر
   - دانشگاه مد نظر

3. *مدارک تحصیلی موجود:*
   - مدرک دیپلم 📄
   - مدرک لیسانس 📄
   - مدرک فوق لیسانس 📄
   - سایر مدارک

4. *مدرک زبان:*
   - اسپانیایی (DELE سطح) 🇪🇸
   - انگلیسی (IELTS/TOEFL) 🇬🇧
   - بدون مدرک زبان ❌

5. *وضعیت مالی:*
   - تمکن مالی مورد نیاز (€10,000+ سالانه) 💶

لطفاً اطلاعات فوق را به صورت کامل وارد کنید.
""",
        "work": """
💼 *ویزای کاری اسپانیا - اطلاعات مورد نیاز:*

1. *نوع ویزای کاری:*
   - Highly Qualified Professional 🎯
   - کارمند عادی 💼
   - انتقال داخل شرکتی 🏢
   - فریلنسر 🎨

2. *سابقه کاری:*
   - مدت سابقه کار (سال) ⏳
   - زمینه تخصصی 🔧
   - صنعت مربوطه 🏭

3. *مدارک تحصیلی:*
   - مدرک دانشگاهی 📄
   - مدارک تخصصی 🏆
   - گواهینامه‌ها 📜

4. *مدرک زبان:*
   - اسپانیایی (سطح A2/B1) 🇪🇸
   - انگلیسی 🇬🇧

5. *پیشنهاد کار:*
   - دارد ✅ / ندارد ❌
   - نام شرکت (اگر دارد) 🏢

6. *حقوق پیشنهادی:*
   - میزان حقوق 💶
""",
        "invest": """
🏡 *ویزای سرمایه‌گذاری اسپانیا - اطلاعات مورد نیاز:*

1. *نوع سرمایه‌گذاری:*
   - خرید ملک 🏠 (حداقل €500,000)
   - سرمایه‌گذاری کسب‌وکار 🏢 (حداقل €1,000,000)
   - خرید اوراق قرضه 📈 (حداقل €2,000,000)
   - سپرده بانکی 🏦 (حداقل €1,000,000)

2. *مبلغ سرمایه:*
   - میزان دقیق سرمایه (یورو) 💶
   - منبع سرمایه 💼

3. *طرح کسب‌وکار:*
   - نوع بیزینس 📊
   - اشتغالزایی 👥
   - سابقه بیزینس 📅

4. *تمکن مالی:*
   - هزینه زندگی سالانه (€30,000+ برای خانواده) 💵

5. *سابقه مدیریتی:*
   - دارد ✅ / ندارد ❌
   - مدت مدیریت ⏳
""",
        "family": """
👨‍👩‍👧‍👦 *ویزای خانوادگی اسپانیا - اطلاعات مورد نیاز:*

1. *نوع رابطه:*
   - همسر 💑
   - فرزند زیر 18 👶
   - فرزند بالغ 👨‍🎓
   - والدین 👵👴

2. *وضعیت اقامت Sponsor:*
   - شهروند اسپانیا 🇪🇸
   - مقیم دائم 🟢
   - ویزای کاری 💼
   - ویزای تحصیلی 🎓

3. *مدارک رابطه:*
   - ازدواج 📄
   - تولد 👶
   - نگهداری 👵

4. *تمکن مالی Sponsor:*
   - درآمد ماهانه (IPREM معیار) 💶
   - مسکن 🏠

5. *بیمه درمانی:*
   - دارد ✅ / ندارد ❌
"""
    }
    
    visa_type = user_data[cid]["visa_type"]
    bot.send_message(cid, questions[visa_type], parse_mode="Markdown")
    user_data[cid]["step"] = "final_details"

# 📌 گزینه‌های سایر کشورها
def send_other_questions(cid):
    markup = types.InlineKeyboardMarkup(row_width=2)
    markup.add(
        types.InlineKeyboardButton("🇨🇦 کانادا", callback_data="other_canada"),
        types.InlineKeyboardButton("🇩🇪 آلمان", callback_data="other_germany"),
        types.InlineKeyboardButton("🇦🇺 استرالیا", callback_data="other_australia"),
        types.InlineKeyboardButton("🇯🇵 ژاپن", callback_data="other_japan"),
        types.InlineKeyboardButton("🇪🇺 شنگن", callback_data="other_schengen"),
        types.InlineKeyboardButton("🇬🇧 انگلستان", callback_data="other_uk"),
        types.InlineKeyboardButton("🇺🇸 آمریکا", callback_data="other_usa"),
        types.InlineKeyboardButton("🇹🇷 ترکیه", callback_data="other_turkey"),
    )
    
    bot.send_message(
        cid, 
        "🌐 *کشور مورد نظر برای مهاجرت:*",
        parse_mode="Markdown",
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith("other_"))
def process_other_details(call):
    cid = call.message.chat.id
    user_data[cid]["country"] = call.data.replace("other_", "")
    user_data[cid]["step"] = "country_details"
    user_data[cid]["timestamp"] = time.time()
    
    bot.answer_callback_query(call.id)

    country_questions = {
        "canada": """
🇨🇦 *کانادا - اطلاعات مورد نیاز:*

1. *برنامه مهاجرتی:*
   - Express Entry 🚀
   - Provincial Nominee 🏛️
   - Quebec Immigration 🍁
   - Startup Visa 🚀
   - Family Sponsorship 👨‍👩‍👧‍👦

2. *امتیاز CRS:*
   - سن (12-110) 🎂
   - تحصیلات (25-150) 🎓
   - سابقه کار (40-80) ⏳
   - زبان (24-136) 🗣️
   - تطابق (10-100) 🔄

3. *مدرک زبان:*
   - IELTS (Listening/Reading/Writing/Speaking) 📊
   - CELPIP (نمره هر بخش) 📝
   - TEF (فرانسه) 🇫🇷

4. *سابقه کاری:*
   - NOC Type (0/A/B/C/D) 🔧
   - سنوات کاری 📅
   - زمینه تخصصی 🏭

5. *تحصیلات:*
   - ECA assessment 📄
   - مدرک معادل کانادا 🎓

6. *پیشنهاد کار:*
   - LMIA approved ✅
   - LMIA exempt ✅
   - بدون پیشنهاد ❌
""",
        "germany": """
🇩🇪 *آلمان - اطلاعات مورد نیاز:*

1. *نوع ویزا:*
   - Blue Card 🔵 (€45,300+)
   - Work Visa 💼
   - Job Seeker 🔍
   - Student 🎓
   - Family 👨‍👩‍👧‍👦

2. *مدرک زبان:*
   - آلمانی (A1/B1/C1) 🇩🇪
   - انگلیسی (IELTS) 🇬🇧
   - Goethe/TestDAF 📜

3. *سابقه کاری:*
   - سنوات مرتبط ⏳
   - زمینه تخصصی 🔧
   - Anerkennung 📄

4. *تحصیلات:*
   - مدرک معادل آلمان 🎓
   - ZAB assessment 📋

5. *پیشنهاد کار:*
   - قرارداد کاری 📝
   - حقوق (براساس Blue Card) 💶
   - صنعت 🏭

6. *تمکن مالی:*
   - Blocked Account (€11,208) 🏦
   - تضمین مالی 💳
""",
        "australia": """
🇦🇺 *استرالیا - اطلاعات مورد نیاز:*

1. *نوع ویزا:*
   - Skilled Independent 189 🎯
   - Skilled Nominated 190 🏛️
   - Employer Sponsored 186/482 💼
   - Student 500 🎓
   - Business Innovation 188 🚀

2. *امتیاز سیستم:*
   - سن (25-32) 🎂
   - زبان (20) 🗣️
   - سابقه کار (5-15) ⏳
   - تحصیلات (10-20) 🎓
   - State Nomination (5-15) 🏛️

3. *مدرک زبان:*
   - IELTS (4x6 minimum) 📊
   - PTE Academic 📝
   - TOEFL iBT 🖥️

4. *Skills Assessment:*
   - Assessing Authority 🔍
   - نتیجه assessment ✅
   - NOC معادل 🔧

5. *سابقه کاری:*
   - سنوات در لیست MLTSSL 📅
   - زمینه تخصصی 🏭

6. *پیشنهاد کار:*
   - Employer Sponsor 🏢
   - Regional Arbeit 🗺️
""",
        "uk": """
🇬🇧 *انگلستان - اطلاعات مورد نیاز:*

1. *نوع ویزا:*
   - Skilled Worker 💼
   - Global Talent 🎯
   - Innovator 🚀
   - Startup 🌱
   - Student 🎓
   - Family 👨‍👩‍👧‍👦

2. *مدرک زبان:*
   - IELTS UKVI 📊
   - CEFR level 🅱️
   - SELT approved ✅

3. *سابقه کاری:*
   - SOC Code 🔧
   - سنوات مرتبط ⏳
   - زمینه تخصصی 🏭

4. *تحصیلات:*
   - UK NARIC 📄
   - مدرک معادل 🎓

5. *پیشنهاد کار:*
   - Sponsor License 🏢
   - Certificate of Sponsorship 📝
   - Salary threshold 💷

6. *امتیاز سیستم:*
   - 70 points required 🎯
   - زبان (10) 🗣️
   - حقوق (20) 💷
   - مهارت (20) 🔧
""",
        "usa": """
🇺🇸 *آمریکا - اطلاعات مورد نیاز:*

1. *نوع ویزا:*
   - H-1B Specialty 💼
   - L-1 Intracompany 🏢
   - O-1 Extraordinary 🎯
   - EB-1/2/3 🟢
   - F-1 Student 🎓
   - DV Lottery 🎫

2. *مدرک زبان:*
   - انگلیسی (TOEFL/IELTS) 🇬🇧
   - سایر زبانها 🗣️

3. *سابقه کاری:*
   - سنوات US equivalent ⏳
   - زمینه تخصصی 🔧
   - PERM Labor Certification 📄

4. *تحصیلات:*
   - US Degree Equivalency 🎓
   - WES Evaluation 📋

5. *پیشنهاد کار:*
   - Employer Petition 🏢
   - Prevailing Wage 💵
   - Labor Condition 📝

6. *تمکن مالی:*
   - I-134 Affidavit 💳
   - Bank Statements 🏦
""",
        "japan": """
🇯🇵 *ژاپن - اطلاعات مورد نیاز:*

1. *نوع ویزا:*
   - Engineer/Specialist 🔧
   - Highly Skilled Professional 🎯
   - Intra-company Transferee 🏢
   - Student 🎓
   - Spouse 💑

2. *مدرک زبان:*
   - ژاپنی (JLPT N1-N5) 🇯🇵
   - انگلیسی (TOEFL/IELTS) 🇬🇧
   - Business Japanese 📊

3. *سابقه کاری:*
   - سنوات مرتبط ⏳
   - زمینه تخصصی 🏭
   - Certificate of Eligibility 📄

4. *تحصیلات:*
   - مدرک دانشگاهی 🎓
   - Technical training 🛠️

5. *پیشنهاد کار:*
   - Contract of Employment 📝
   - Company profile 🏢
   - Salary details 💴

6. *تمکن مالی:*
   - Bank balance 💰
   - Sponsor guarantee 🤝
"""
    }
    
    country_key = user_data[cid]["country"]
    bot.send_message(cid, country_questions.get(country_key, "لطفاً اطلاعات خود را وارد کنید:"), parse_mode="Markdown")
    user_data[cid]["step"] = "final_details"

# 📌 دریافت جزئیات نهایی
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "final_details")
def handle_final_details(message):
    cid = message.chat.id
    
    if cid not in user_data:
        bot.send_message(cid, "❌ خطا در پردازش اطلاعات. لطفاً /start را بزنید.")
        return
    
    if message.content_type != 'text':
        bot.send_message(cid, "❌ لطفاً اطلاعات را به صورت متن وارد کنید.")
        return
    
    details = message.text.strip()
    user_data[cid]["final_details"] = details
    user_data[cid]["timestamp"] = time.time()
    
    # آماده‌سازی اطلاعات برای ارسال
    name = user_data[cid].get("name", "نامشخص")
    phone = user_data[cid].get("phone", "نامشخص")
    
    if user_data[cid].get("type") == "spain":
        visa_type = user_data[cid].get("visa_type", "نامشخص")
        consultation_type = f"اسپانیا - {visa_type}"
    else:
        country_map = {
            "canada": "کانادا", "germany": "آلمان", "australia": "استرالیا",
            "japan": "ژاپن", "schengen": "شنگن", "uk": "انگلستان",
            "usa": "آمریکا", "turkey": "ترکیه"
        }
        country = country_map.get(user_data[cid].get("country", ""), "سایر کشورها")
        consultation_type = f"{country}"
    
    # ✅ پیام برای کاربر
    bot.send_message(cid, "✅ اطلاعات شما با موفقیت ثبت شد!\n⏳ در حال ارسال به ادمین ...")
    
    # ارسال به ادمین
    admin_message = f"""
🔔 *درخواست جدید نئوویزا* ⚖️
━━━━━━━━━━━━━━━━━━
👤 *نام:* {name}
📱 *تلفن:* {phone}
🌐 *نوع درخواست:* {consultation_type}
📝 *جزئیات:*
{details}
━━━━━━━━━━━━━━━━━━
🕒 *زمان ثبت:* {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    """
    
    try:
        bot.send_message(ADMIN_ID, admin_message, parse_mode="Markdown")
        print(f"✅ درخواست کاربر {cid} به ادمین ارسال شد")
    except Exception as e:
        print(f"❌ خطا در ارسال به ادمین: {e}")
        bot.send_message(cid, "⚠️ خطا در ارسال اطلاعات. لطفاً بعداً تلاش کنید.")
        return
    
    # دکمه درخواست جدید
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🔄 درخواست جدید", callback_data="new_request"))
    
    bot.send_message(
        cid, 
        "🎉 *درخواست شما با موفقیت ثبت شد!*\n\nتیم نئووایزا طی ۲۴ ساعت آینده با شما تماس خواهد گرفت.\n\nبرای ثبت درخواست جدید می‌توانید از دکمه زیر استفاده کنید:", 
        parse_mode="Markdown",
        reply_markup=markup
    )
    
    # پاکسازی داده‌های کاربر
    if cid in user_data:
        del user_data[cid]

# 📌 درخواست جدید
@bot.callback_query_handler(func=lambda call: call.data == "new_request")
def process_new_request(call):
    cid = call.message.chat.id
    
    if cid in user_data:
        del user_data[cid]
    
    user_data[cid] = {
        "timestamp": time.time(),
        "step": "type_select"
    }
    
    bot.answer_callback_query(call.id)
    markup = types.InlineKeyboardMarkup()
    markup.add(
        types.InlineKeyboardButton("🌍 اقامت اسپانیا", callback_data="spain"),
        types.InlineKeyboardButton("🌐 سایر کشورها", callback_data="other")
    )
    
    bot.send_message(
        cid, 
        "🔄 *درخواست جدید*\n\n⚖️ نوع خدمت را انتخاب کنید:",
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
    elif current_step == "final_details":
        bot.send_message(cid, "📋 لطفاً اطلاعات خواسته شده را وارد کنید.")
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

@app.route("/health")
def health():
    return {"status": "healthy", "users": len(user_data), "timestamp": datetime.now().isoformat()}

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    print(f"🚀 Starting bot on port {port}")
    app.run(host="0.0.0.0", port=port)
