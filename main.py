import os
import telebot
from telebot import types
from flask import Flask, request
from datetime import datetime

TOKEN = "7902857577:AAGsWarAtHg9A8yXDApkRzCVx7dR3wFc5u0"
bot = telebot.TeleBot(TOKEN)
app = Flask(__name__)

# حتماً تو Render مقدار درست URL سرویس رو بزن
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "https://neovisa-1.onrender.com")
WEBHOOK_SECRET = os.getenv("WEBHOOK_SECRET", "mysecret")

user_data = {}
completed_requests = {}

@app.route(f"/webhook/{WEBHOOK_SECRET}", methods=["POST"])
def webhook():
    if request.headers.get("content-type") == "application/json":
        try:
            update = telebot.types.Update.de_json(request.data.decode("utf-8"))
            bot.process_new_updates([update])
            return "", 200
        except Exception as e:
            print(f"Webhook processing error: {e}")
            return "", 500
    return "", 403

@app.route("/")
def index():
    return "✅ ربات خدمات مهاجرت فعال است 🌍"

@app.route("/health")
def health():
    return {
        "status": "healthy",
        "users": len(user_data),
        "time": datetime.now().isoformat()
    }

# فقط یکبار وقتی سرور روشن شد Webhook ست میشه
with app.app_context():
    try:
        bot.remove_webhook()
    except:
        pass
    bot.set_webhook(url=f"{WEBHOOK_URL}/webhook/{WEBHOOK_SECRET}")

# ---- اینجا همون هندلرهای قبلت رو بذار (start, درخواست جدید, ...)

if __name__ == "__main__":
    port = int(os.getenv("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
