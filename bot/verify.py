import hashlib
import hmac
from urllib.parse import parse_qsl

from config import BOT_TOKEN


def verify_init_data(init_data: str) -> dict | None:
    """
    Telegram Mini App yuborgan initData imzosini tekshiradi.
    To'g'ri bo'lsa — undagi user ma'lumotlarini dict qilib qaytaradi.
    Noto'g'ri/soxta bo'lsa — None qaytaradi.
    https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app
    """
    if not init_data:
        return None

    try:
        pairs = dict(parse_qsl(init_data, strict_parsing=True))
    except ValueError:
        return None

    received_hash = pairs.pop("hash", None)
    if not received_hash:
        return None

    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(pairs.items()))

    secret_key = hmac.new(b"WebAppData", BOT_TOKEN.encode(), hashlib.sha256).digest()
    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return None

    return pairs
