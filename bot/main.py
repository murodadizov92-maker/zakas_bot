import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

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

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("zakas-bot")

WEBAPP_DIR = Path(__file__).resolve().parent.parent / "webapp"

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

CATALOG = load_catalog()  # {category: [{id, name, price}, ...]}
PRODUCTS_BY_ID = {p["id"]: p for cat in CATALOG.values() for p in cat}


# ---------------------------------------------------------------- Telegram bot

def main_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="🛒 Buyurtma berish", web_app=WebAppInfo(url=WEBAPP_URL))]
        ],
        resize_keyboard=True,
    )


@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        f"Assalomu alaykum, {message.from_user.full_name}!\n\n"
        f"Buyurtma berish uchun pastdagi tugmani bosing.\n"
        f"⏰ Buyurtmalar har kuni soat {open_str()} dan {cutoff_str()} gacha qabul qilinadi.",
        reply_markup=main_keyboard(),
    )


@dp.message(F.text == "🛒 Buyurtma berish")
async def reopen(message: Message):
    await message.answer("Buyurtma oynasi:", reply_markup=main_keyboard())


# ---------------------------------------------------------------- HTTP API

async def handle_products(request: web.Request) -> web.Response:
    return web.json_response(
        {
            "catalog": CATALOG,
            "order_open": is_order_time_open(),
            "open_from": open_str(),
            "cutoff": cutoff_str(),
        }
    )


async def handle_order(request: web.Request) -> web.Response:
    try:
        payload = await request.json()
    except json.JSONDecodeError:
        return web.json_response({"ok": False, "error": "bad_json"}, status=400)

    init_data = payload.get("initData", "")
    items = payload.get("items", [])  # [{id, qty}]

    user_data = verify_init_data(init_data)
    if user_data is None:
        return web.json_response({"ok": False, "error": "auth_failed"}, status=401)

    if not is_order_time_open():
        return web.json_response({"ok": False, "error": "closed"}, status=403)

    if not items:
        return web.json_response({"ok": False, "error": "empty_order"}, status=400)

    user = json.loads(user_data.get("user", "{}"))
    full_name = " ".join(
        filter(None, [user.get("first_name"), user.get("last_name")])
    ) or "Noma'lum"
    username = f"@{user['username']}" if user.get("username") else "—"

    lines = []
    total_kg = 0.0
    total_dona = 0.0
    for item in items:
        product = PRODUCTS_BY_ID.get(item.get("id"))
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
    text = (
        f"🆕 <b>Yangi buyurtma</b>\n"
        f"📅 Sana: {today}\n"
        f"👤 Foydalanuvchi: {full_name} ({username})\n"
        f"🆔 ID: {user.get('id')}\n\n"
        f"<b>Mahsulotlar:</b>\n" + "\n".join(lines) + "\n\n"
        f"<b>Jami:</b> {total_kg:g} kg, {total_dona:g} dona"
    )

    if ADMIN_CHAT_ID:
        await bot.send_message(ADMIN_CHAT_ID, text, parse_mode="HTML")

    return web.json_response({"ok": True})


async def handle_index(request: web.Request) -> web.FileResponse:
    return web.FileResponse(WEBAPP_DIR / "index.html")


def build_app() -> web.Application:
    app = web.Application()
    app.router.add_get("/", handle_index)
    app.router.add_get("/api/products", handle_products)
    app.router.add_post("/api/order", handle_order)
    app.router.add_static("/", path=WEBAPP_DIR, name="webapp", show_index=False)
    return app


async def main():
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
