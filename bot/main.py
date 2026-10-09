import asyncio
import json
import logging
from datetime import datetime

from aiohttp import web
from aiogram import Bot, Dispatcher, F
from aiogram.filters import CommandStart
from aiogram.types import (
    Message,
    WebAppInfo,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

from config import BOT_TOKEN, ADMIN_CHAT_ID, WEBAPP_URL, PORT
from catalog import load_catalog, is_order_time_open, open_str, cutoff_str
from verify import verify_init_data
from config import DATABASE_URL, SECRET_KEY
import db
import api_v2

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("zakas-bot")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()
api_v2.BOT = bot

CATALOG = load_catalog()  # {category: [{id, name, price}, ...]}
PRODUCTS_BY_ID = {p["id"]: p for cat in CATALOG.values() for p in cat}


# ---------------------------------------------------------------- Telegram bot

def main_keyboard(user_id: int = 0) -> ReplyKeyboardMarkup:
    # Baza ulangan bo'lsa yangi ilova (/app/), aks holda eski Mini App
    url = WEBAPP_URL.rstrip("/") + "/app/" if (DATABASE_URL and SECRET_KEY) else WEBAPP_URL
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="🛒 Buyurtma berish", web_app=WebAppInfo(url=url))]],
        resize_keyboard=True,
    )


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        f"Buyurtma berish uchun pastdagi tugmani bosing.\n"
        f"⏰ Buyurtmalar har kuni soat {open_str()} dan {cutoff_str()} gacha qabul qilinadi.",
        reply_markup=main_keyboard(message.from_user.id),
    )


@dp.message(F.text == "🛒 Buyurtma berish")
async def reopen(message: Message):
    await message.answer("Buyurtma oynasi:", reply_markup=main_keyboard(message.from_user.id))


# ---------------------------------------------------------------- HTTP API

async def get_catalog():
    """(katalog, buyurtma_ochiqmi, boshlanish, tugash). Baza ulangan bo'lsa — bazadan."""
    if db.pool is None:
        return CATALOG, is_order_time_open(), open_str(), cutoff_str()
    async with db.pool.acquire() as c:
        rows = await c.fetch(
            "select id,name,price,category from products where active order by sort,id")
    cat: dict = {}
    for r in rows:
        cat.setdefault(r["category"], []).append(
            {"id": r["id"], "name": r["name"], "price": r["price"]})
    st = await api_v2.order_status()
    return cat, st["order_open"], st["open_time"], st["cutoff_time"]


async def handle_products(request: web.Request) -> web.Response:
    cat, is_open, o, c = await get_catalog()
    return web.json_response(
        {"catalog": cat, "order_open": is_open, "open_from": o, "cutoff": c}
    )


async def handle_order(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"ok": False, "error": "bad_json"}, status=400)

    init_data = payload.get("initData", "")
    items = payload.get("items", [])  # [{id, qty}]

    is_web_fallback = not init_data

    if is_web_fallback:
        # Telegram tashqarisida (oddiy brauzerda) ochilgan — initData yo'q,
        # shuning uchun foydalanuvchi qo'lda kiritgan ism/telefon bilan ishlaymiz.
        # DIQQAT: bu yo'lda foydalanuvchi tasdiqlanmaydi (istalgan ism yozilishi mumkin).
        web_name = (payload.get("webName") or "").strip()
        web_phone = (payload.get("webPhone") or "").strip()
        if not web_name or not web_phone:
            return web.json_response({"ok": False, "error": "missing_info"}, status=400)
        full_name = web_name
        username = web_phone
        user_id = "—"
    else:
        user_data = verify_init_data(init_data)
        if user_data is None:
            return web.json_response({"ok": False, "error": "auth_failed"}, status=401)

        user = json.loads(user_data.get("user", "{}"))
        full_name = " ".join(
            filter(None, [user.get("first_name"), user.get("last_name")])
        ) or "Noma'lum"
        username = f"@{user['username']}" if user.get("username") else "—"
        user_id = user.get("id")

    cat, is_open, _o, _c = await get_catalog()
    products_by_id = {p["id"]: p for plist in cat.values() for p in plist}
    if not is_open:
        return web.json_response({"ok": False, "error": "closed"}, status=403)

    if not items:
        return web.json_response({"ok": False, "error": "empty_order"}, status=400)

    lines = []
    total_kg = 0.0
    total_dona = 0.0
    for item in items:
        product = products_by_id.get(item.get("id"))
        if not product:
            continue
        qty = float(item.get("qty", 0))
        if qty <= 0:
            continue
        unit = item.get("unit", "kg")
        unit_label = "kg" if unit == "kg" else "dona"
        if unit == "kg":
            total_kg += qty
        else:
            total_dona += qty
        lines.append(f"• {product['name']} — {qty:g} {unit_label} ({product['price']:,} so'm/{unit_label})".replace(",", " "))

    if not lines:
        return web.json_response({"ok": False, "error": "empty_order"}, status=400)

    today = datetime.now().strftime("%d.%m.%Y")
    source_note = "🌐 Veb-sayt orqali (tasdiqlanmagan!)\n" if is_web_fallback else ""
    text = (
        f"🆕 <b>Yangi buyurtma</b>\n"
        f"{source_note}"
        f"📅 Sana: {today}\n"
        f"👤 Foydalanuvchi: {full_name} ({username})\n"
        f"🆔 ID: {user_id}\n\n"
        f"<b>Mahsulotlar:</b>\n" + "\n".join(lines) + "\n\n"
        f"<b>Jami:</b> {total_kg:g} kg, {total_dona:g} dona"
    )

    if ADMIN_CHAT_ID:
        await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")

    return web.json_response({"ok": True})


async def handle_index(request: web.Request) -> web.FileResponse:
    return web.FileResponse("../webapp/index.html")


def build_app() -> web.Application:
    app = web.Application(
        client_max_size=12 * 1024 * 1024,
        middlewares=[api_v2.cors_mw, api_v2.auth_mw] if DATABASE_URL and SECRET_KEY else [],
    )
    if DATABASE_URL and SECRET_KEY:
        api_v2.add_routes(app)  # yangi Android ilova API'si
    else:
        async def _health(request):
            return web.json_response({"ok": True})
        app.router.add_get("/health", _health)
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/products", handle_products)
    app.router.add_post("/api/order", handle_order)
    app.router.add_static("/", path="../webapp", name="webapp", show_index=False)
    return app

async def main():
    if DATABASE_URL and SECRET_KEY:
        await db.init_db()
    else:
        log.warning("DATABASE_URL/SECRET_KEY yo'q — yangi API o'chiq, faqat eski bot ishlaydi")
    app = build_app()
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "0.0.0.0", PORT)
    await site.start()
    log.info(f"HTTP server ishga tushdi: 0.0.0.0:{PORT}")

    await bot.delete_webhook(drop_pending_updates=True)
    log.info("Bot polling boshlandi")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
