import json
from datetime import datetime
from pathlib import Path

from config import (
    TIMEZONE,
    ORDER_OPEN_HOUR,
    ORDER_OPEN_MINUTE,
    ORDER_CUTOFF_HOUR,
    ORDER_CUTOFF_MINUTE,
)

PRODUCTS_PATH = Path(__file__).parent / "products.json"


def load_catalog() -> dict:
    with open(PRODUCTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def is_order_time_open() -> bool:
    """Hozirgi vaqt belgilangan ish oralig'i (masalan 09:00-16:00) ichidami?"""
    now = datetime.now(TIMEZONE)
    open_time = now.replace(
        hour=ORDER_OPEN_HOUR, minute=ORDER_OPEN_MINUTE, second=0, microsecond=0
    )
    cutoff = now.replace(
        hour=ORDER_CUTOFF_HOUR, minute=ORDER_CUTOFF_MINUTE, second=0, microsecond=0
    )
    return open_time <= now < cutoff


def open_str() -> str:
    return f"{ORDER_OPEN_HOUR:02d}:{ORDER_OPEN_MINUTE:02d}"


def cutoff_str() -> str:
    return f"{ORDER_CUTOFF_HOUR:02d}:{ORDER_CUTOFF_MINUTE:02d}"
