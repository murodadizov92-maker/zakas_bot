import os
from zoneinfo import ZoneInfo

# --- .env dan o'qish (python-dotenv) ---
from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# Buyurtmalar shu chatga (admin) yuboriladi.
# O'z shaxsiy chat ID'ingizni olish uchun @userinfobot ga /start yozing.
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))

# Mini App qaysi manzilda joylashgan (Render/Railway sizga beradigan public URL)
# Masalan: https://zakas-bot.onrender.com
WEBAPP_URL = os.getenv("WEBAPP_URL", "")

TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tashkent"))

# Buyurtma qabul qilinadigan vaqt oralig'i (shu oraliqdan tashqarida bot buyurtma qabul qilmaydi)
ORDER_OPEN_HOUR = int(os.getenv("ORDER_OPEN_HOUR", "9"))
ORDER_OPEN_MINUTE = int(os.getenv("ORDER_OPEN_MINUTE", "0"))
ORDER_CUTOFF_HOUR = int(os.getenv("ORDER_CUTOFF_HOUR", "16"))
ORDER_CUTOFF_MINUTE = int(os.getenv("ORDER_CUTOFF_MINUTE", "0"))

PORT = int(os.getenv("PORT", "8080"))
