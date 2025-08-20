import telebot
from telebot import types
from flask import Flask, request
import os
import time

# دریافت متغیرهای محیطی
TOKEN = os.getenv("TOKEN", "8010785406:AAGU3XARPR_GzihDYS8T624bPTEU8ildmQ8")
ADMIN_ID = int(os.getenv("ADMIN_ID", 7549512366))
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://bot-ltl5.onrender.com/webhook")

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
    except Exception as e:
        print("Webhook error:", e)

set_webhook()

# شروع
@bot.message_handler(commands=['start'])
def send_welcome(message):
    cid = message.chat.id
    user_data[cid] = {}
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🌍 اقامت اسپانیا", callback_data="spain"),
               types.InlineKeyboardButton("🌐 سایر کشورها", callback_data="other"))
    bot.send_message(cid, "⚖️ *خوش آمدید به نئوویزا!* 🌍\n\n📜 لطفاً نوع خدمت را انتخاب کنید:", 
                     parse_mode="Markdown", reply_markup=markup)

# انتخاب نوع مشاوره
@bot.callback_query_handler(func=lambda call: call.data in ["spain", "other"])
def process_consultation_type(call):
    cid = call.message.chat.id
    user_data[cid] = {"type": call.data, "step": "phone"}
    bot.answer_callback_query(call.id)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    markup.add(types.KeyboardButton("📱 ارسال شماره", request_contact=True))
    bot.edit_message_text(chat_id=cid, message_id=call.message.message_id, text="🌟 انتخاب ثبت شد!")
    bot.send_message(cid, "📞 لطفاً شماره تماس خود را وارد کنید:", reply_markup=markup)

# شماره تماس
@bot.message_handler(content_types=['contact'], func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone")
def handle_contact(message):
    cid = message.chat.id
    user_data[cid]["phone"] = message.contact.phone_number
    user_data[cid]["step"] = "name"
    bot.send_message(cid, "✅ شماره ثبت شد!\n👤 لطفاً *نام و نام خانوادگی* خود را وارد کنید:", 
                     parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())

@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "phone" and m.content_type == "text")
def handle_phone_text(message):
    cid = message.chat.id
    user_data[cid]["phone"] = message.text.strip()
    user_data[cid]["step"] = "name"
    bot.send_message(cid, "✅ شماره ثبت شد!\n👤 لطفاً *نام و نام خانوادگی* خود را وارد کنید:", 
                     parse_mode="Markdown", reply_markup=types.ReplyKeyboardRemove())

# دریافت نام
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "name")
def handle_name(message):
    cid = message.chat.id
    user_data[cid]["name"] = message.text.strip()
    user_data[cid]["step"] = "marital"
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("👤 مجرد", callback_data="single"),
               types.InlineKeyboardButton("💍 متأهل", callback_data="married"))
    bot.send_message(cid, "💍 وضعیت تأهل خود را انتخاب کنید:", reply_markup=markup)

# وضعیت تأهل
@bot.callback_query_handler(func=lambda call: call.data in ["single", "married"])
def handle_marital(call):
    cid = call.message.chat.id
    user_data[cid]["marital"] = "مجرد" if call.data == "single" else "متأهل"
    user_data[cid]["step"] = "country"
    bot.answer_callback_query(call.id)

    if user_data[cid]["type"] == "spain":
        send_spain_options(cid)
    else:
        send_other_options(cid)

# گزینه‌های اسپانیا
def send_spain_options(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🎓 تحصیلی", callback_data="spain_edu"),
               types.InlineKeyboardButton("💼 کاری", callback_data="spain_work"),
               types.InlineKeyboardButton("🏡 سرمایه‌گذاری", callback_data="spain_invest"))
    bot.send_message(cid, "🇪🇸 لطفاً نوع اقامت در اسپانیا را انتخاب کنید:", reply_markup=markup)

# جزئیات اسپانیا
@bot.callback_query_handler(func=lambda call: call.data.startswith("spain_"))
def process_spain(call):
    cid = call.message.chat.id
    user_data[cid]["program"] = call.data.replace("spain_", "")
    user_data[cid]["step"] = "final"
    bot.answer_callback_query(call.id)

    if user_data[cid]["program"] == "edu":
        bot.send_message(cid, "🎓 لطفاً *رشته و مقطع تحصیلی* خود را بنویسید:")
    elif user_data[cid]["program"] == "work":
        bot.send_message(cid, "💼 لطفاً *شغل، تجربه کاری و مدرک تحصیلی* خود را وارد کنید:")
    elif user_data[cid]["program"] == "invest":
        bot.send_message(cid, "🏡 لطفاً *میزان سرمایه و روش سرمایه‌گذاری* را توضیح دهید:")

# گزینه‌های سایر کشورها
def send_other_options(cid):
    markup = types.InlineKeyboardMarkup()
    markup.add(types.InlineKeyboardButton("🇨🇦 کانادا", callback_data="other_canada"),
               types.InlineKeyboardButton("🇩🇪 آلمان", callback_data="other_germany"),
               types.InlineKeyboardButton("🇦🇺 استرالیا", callback_data="other_australia"))
    markup.add(types.InlineKeyboardButton("🇯🇵 ژاپن", callback_data="other_japan"),
               types.InlineKeyboardButton("🇪🇺 شنگن", callback_data="other_schengen"),
               types.InlineKeyboardButton("🇬🇧 انگلستان", callback_data="other_uk"))
    bot.send_message(cid, "🌐 لطفاً کشور مورد نظر را انتخاب کنید:", reply_markup=markup)

# جزئیات سایر کشورها
@bot.callback_query_handler(func=lambda call: call.data.startswith("other_"))
def process_other(call):
    cid = call.message.chat.id
    country = call.data.replace("other_", "")
    user_data[cid]["program"] = country
    user_data[cid]["step"] = "final"
    bot.answer_callback_query(call.id)

    questions = {
        "canada": "🇨🇦 لطفاً *برنامه مهاجرتی (اکسپرس انتری، تحصیلی، استارت‌آپ...)* و *سطح زبان* خود را وارد کنید:",
        "germany": "🇩🇪 لطفاً *نوع ویزا (جاب سیکر، بلوکارت، تحصیلی...)* و *سطح زبان آلمانی* خود را وارد کنید:",
        "australia": "🇦🇺 لطفاً *نوع ویزا* و *امتیاز سیستم مهاجرتی* خود را وارد کنید:",
        "japan": "🇯🇵 لطفاً *نوع ویزا* و *سطح زبان ژاپنی* خود را وارد کنید:",
        "schengen": "🇪🇺 لطفاً *هدف سفر، مدت اقامت و دعوت‌نامه* خود را توضیح دهید:",
        "uk": "🇬🇧 لطفاً *نوع ویزا* و *هدف مهاجرت* خود را وارد کنید:"
    }
    bot.send_message(cid, questions.get(country, "📝 لطفاً جزئیات خود را وارد کنید:"), parse_mode="Markdown")

# دریافت جزئیات نهایی
@bot.message_handler(func=lambda m: user_data.get(m.chat.id, {}).get("step") == "final")
def handle_final(message):
    cid = message.chat.id
    details = message.text.strip()
    user_data[cid]["details"] = details

    # ارسال به ادمین
    name = user_data[cid]["name"]
    phone = user_dat_
