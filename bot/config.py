import os
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()
ADMIN_CHAT_ID = int(os.getenv("ADMIN_CHAT_ID", "0"))
WEBAPP_URL = os.getenv("WEBAPP_URL", "")
TIMEZONE = ZoneInfo(os.getenv("TIMEZONE", "Asia/Tashkent"))

# Eski (Telegram Mini App) uchun boshlang'ich vaqtlar. Yangi ilovada vaqt bazadan olinadi.
ORDER_OPEN_HOUR = int(os.getenv("ORDER_OPEN_HOUR", "9"))
ORDER_OPEN_MINUTE = int(os.getenv("ORDER_OPEN_MINUTE", "0"))
ORDER_CUTOFF_HOUR = int(os.getenv("ORDER_CUTOFF_HOUR", "16"))
ORDER_CUTOFF_MINUTE = int(os.getenv("ORDER_CUTOFF_MINUTE", "0"))

PORT = int(os.getenv("PORT", "8080"))

# --- Yangi: Android ilova uchun ---
DATABASE_URL = os.getenv("DATABASE_URL", "").strip()
SUPABASE_URL = os.getenv("SUPABASE_URL", "").strip().rstrip("/")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "").strip()
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET", "products").strip()
ADMIN_PHONE = os.getenv("ADMIN_PHONE", "").strip()
ADMIN_CODE = os.getenv("ADMIN_CODE", "").strip()
SECRET_KEY = os.getenv("SECRET_KEY", "").strip()
