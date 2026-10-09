import json
import logging

import asyncpg

from config import (
    DATABASE_URL, ADMIN_PHONE, ADMIN_CODE,
    ORDER_OPEN_HOUR, ORDER_OPEN_MINUTE, ORDER_CUTOFF_HOUR, ORDER_CUTOFF_MINUTE,
)
from catalog import load_catalog

log = logging.getLogger("zakas-db")
pool: asyncpg.Pool | None = None


def norm_phone(s) -> str:
    """Telefonni solishtirish uchun: faqat raqamlar, oxirgi 9 ta (+998 90 123 45 67 -> 901234567)."""
    digits = "".join(ch for ch in str(s or "") if ch.isdigit())
    return digits[-9:] if len(digits) >= 9 else digits


SCHEMA = """
create table if not exists users(
  id serial primary key,
  phone text unique not null,
  name text not null default '',
  code text,
  is_admin boolean not null default false,
  active boolean not null default true,
  created_at timestamptz not null default now()
);
create table if not exists products(
  id integer primary key,
  name text not null,
  price integer not null default 0,
  category text not null default 'Прочие',
  image_url text,
  active boolean not null default true,
  sort integer not null default 0
);
create table if not exists orders(
  id serial primary key,
  user_id integer references users(id),
  order_date date not null,
  created_at timestamptz not null default now(),
  items jsonb not null,
  total_kg numeric not null default 0,
  total_dona numeric not null default 0
);
create table if not exists settings(
  key text primary key,
  value text not null
);
"""


async def init_db():
    global pool
    pool = await asyncpg.create_pool(
        DATABASE_URL, min_size=1, max_size=5, statement_cache_size=0
    )
    async with pool.acquire() as c:
        await c.execute(SCHEMA)

        # Mahsulotlarni products.json dan bir marta to'ldirish
        if await c.fetchval("select count(*) from products") == 0:
            i = 0
            for cat, items in load_catalog().items():
                for p in items:
                    i += 1
                    await c.execute(
                        "insert into products(id,name,price,category,sort) values($1,$2,$3,$4,$5) "
                        "on conflict (id) do nothing",
                        p["id"], p["name"], int(p["price"]), cat, i,
                    )
            log.info("products.json dan %d ta mahsulot yuklandi", i)

        # Sozlamalar (boshlang'ich qiymatlar)
        defaults = {
            "open_time": f"{ORDER_OPEN_HOUR:02d}:{ORDER_OPEN_MINUTE:02d}",
            "cutoff_time": f"{ORDER_CUTOFF_HOUR:02d}:{ORDER_CUTOFF_MINUTE:02d}",
        }
        for k, v in defaults.items():
            await c.execute(
                "insert into settings(key,value) values($1,$2) on conflict do nothing", k, v
            )

        # Admin foydalanuvchi
        phone = norm_phone(ADMIN_PHONE)
        if phone:
            await c.execute(
                "insert into users(phone,name,code,is_admin) values($1,'Admin',$2,true) "
                "on conflict (phone) do update set is_admin=true, active=true, "
                "code=coalesce(excluded.code, users.code)",
                phone, ADMIN_CODE or None,
            )
    log.info("Baza tayyor")


async def get_settings() -> dict:
    async with pool.acquire() as c:
        rows = await c.fetch("select key,value from settings")
    return {r["key"]: r["value"] for r in rows}


async def ping() -> bool:
    async with pool.acquire() as c:
        return await c.fetchval("select 1") == 1
