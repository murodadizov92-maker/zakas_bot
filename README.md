# Zakas bot — Telegram Mini App

Mijozlar Telegram bot ichida Mini App ochib, kategoriya bo'yicha mahsulot tanlaydi,
kg/dona miqdorini yozadi va "Tasdiqlash" bossa — buyurtma sizning shaxsiy chatingizga
(sana, foydalanuvchi, mahsulotlar, jami kg/dona bilan) tartibli xabar bo'lib keladi.
Belgilangan soatdan keyin bot yangi buyurtma qabul qilmaydi.

Mahsulotlar ro'yxati (`bot/products.json`) sizning "Шаблон/Прайс лист" faylingizdan
tayyorlangan — narxi bo'lgan **377 ta mahsulot**, 13 ta kategoriya bo'yicha.

## 1-qadam: Bot yaratish

1. Telegramda **@BotFather** ga yozing → `/newbot` → nom va username bering.
2. Sizga **BOT_TOKEN** beradi — uni saqlab qo'ying.
3. O'zingizning shaxsiy **chat ID**ingizni bilish uchun **@userinfobot** ga `/start` yozing — u sizga ID raqamini beradi (**ADMIN_CHAT_ID**).

## 2-qadam: Render.com'da bepul hosting

1. [render.com](https://render.com) da ro'yxatdan o'ting (GitHub akkaunt bilan kirsa qulay).
2. Bu loyihani GitHub'ga yuklang (yangi repo yarating, fayllarni push qiling).
3. Render'da **New → Web Service** → repo'ni tanlang.
4. Sozlamalar:
   - **Root Directory:** bo'sh qoldiring (repo tuzilishi shu papka bilan bir xil bo'lsin)
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `cd bot && python main.py`
   - **Instance type:** Free
5. **Environment** bo'limida quyidagilarni kiriting (`.env.example` dagi kabi):
   - `BOT_TOKEN`
   - `ADMIN_CHAT_ID`
   - `WEBAPP_URL` — bu qadamda hali bilmaysiz, avval bo'sh qoldiring
   - `ORDER_OPEN_HOUR` = `9`
   - `ORDER_OPEN_MINUTE` = `0`
   - `ORDER_CUTOFF_HOUR` = `16`
   - `ORDER_CUTOFF_MINUTE` = `0`
   - `TIMEZONE` = `Asia/Tashkent`
6. **Deploy** tugmasini bosing. Deploy tugagach, Render sizga URL beradi
   (masalan `https://zakas-bot.onrender.com`).
7. Shu URL'ni **WEBAPP_URL** environment o'zgaruvchisiga qo'yib, qayta deploy qiling
   (Render buni "Manual Deploy" orqali qiladi).

> Eslatma: Free tarif biroz "uxlab qolishi" mumkin (foydalanilmasa 15 daqiqadan keyin
> to'xtaydi, keyingi so'rovda ~30 soniyada qayta uyg'onadi). Agar bu muammo bo'lsa,
> keyinroq Railway.app yoki arzon VPS'ga o'tkazish mumkin — kod o'zgarmaydi.

## 3-qadam: Botni sinash

1. Botingizga Telegramda `/start` yozing.
2. "🛒 Buyurtma berish" tugmasi chiqadi — bosing, Mini App ochiladi.
3. Kategoriya tanlang, mahsulot(lar)ga miqdor kiriting, "Buyurtmani ko'rish" → "Tasdiqlash".
4. Buyurtma sizning shaxsiy chatingizga xabar bo'lib kelishi kerak.

## Buyurtma qabul qilish vaqt oralig'ini o'zgartirish

Render dashboard → Environment → `ORDER_OPEN_HOUR`/`ORDER_OPEN_MINUTE` (boshlanish) va
`ORDER_CUTOFF_HOUR`/`ORDER_CUTOFF_MINUTE` (tugash) qiymatlarini o'zgartiring → saqlang
(avtomatik qayta ishga tushadi). Kodga tegish shart emas.

## Mahsulot/narxlar ro'yxatini yangilash

Yangi "Шаблон"/prays-list Excel faylini menga (Claude'ga) yuborsangiz,
`bot/products.json` faylini qayta generatsiya qilib beraman — shuni Render'dagi
repo'ga almashtirib qo'yasiz.

## Loyiha tuzilishi

```
zakas-bot/
├── bot/
│   ├── main.py          # aiohttp server + aiogram bot (bitta process)
│   ├── config.py        # sozlamalar (.env dan o'qiydi)
│   ├── catalog.py        # mahsulotlar va vaqt tekshiruvi
│   ├── verify.py         # Mini App so'rovini xavfsiz tekshirish
│   └── products.json     # mahsulotlar (avtomatik tayyorlangan)
├── webapp/
│   ├── index.html
│   ├── style.css
│   └── app.js             # Mini App logikasi
├── requirements.txt
└── .env.example
```
