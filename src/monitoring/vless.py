import time
from datetime import datetime

import requests

from src.config import PROXY_URL
from src.services.settings import load_settings


def check_telegram_proxy():
    if not PROXY_URL:
        return {
            "working": False,
            "ping": None,
            "error": "PROXY_URL is not set",
        }

    url = "https://api.telegram.org"

    start = time.monotonic()

    try:
        response = requests.get(
            url,
            proxies={
                "http": PROXY_URL,
                "https": PROXY_URL,
            },
            timeout=10,
        )

        elapsed = (
            time.monotonic() - start
        ) * 1000

        if response.status_code < 500:
            return {
                "working": True,
                "ping": round(elapsed),
                "error": None,
            }

        return {
            "working": False,
            "ping": round(elapsed),
            "error": f"HTTP {response.status_code}",
        }

    except requests.RequestException as error:
        return {
            "working": False,
            "ping": None,
            "error": str(error),
        }


def get_vless_state():
    result = check_telegram_proxy()
    settings = load_settings()

    threshold = settings["vless"]["ping_threshold"]

    if not result["working"]:
        return {
            "working": False,
            "ping": result["ping"],
            "quality": "недоступен",
            "high_ping": True,
            "error": result["error"],
            "checked_at": datetime.now(),
        }

    ping = result["ping"]

    if ping <= 300:
        quality = "отличное"
    elif ping <= 700:
        quality = "хорошее"
    elif ping <= threshold:
        quality = "нормальное"
    else:
        quality = "плохое"

    return {
        "working": True,
        "ping": ping,
        "quality": quality,
        "high_ping": ping > threshold,
        "error": None,
        "checked_at": datetime.now(),
    }


def build_vless_message():
    from src.services.services import (
        get_vless_monitor_state,
    )

    settings = load_settings()
    state = get_vless_state()
    monitor_state = get_vless_monitor_state()

    threshold = settings["vless"]["ping_threshold"]
    required_failures = settings["vless"]["required_failures"]

    if state["working"]:
        status = "🟢 Работает"
    else:
        status = "🔴 Недоступен"

    if state["ping"] is None:
        ping_text = "Нет ответа"
    else:
        ping_text = f"{state['ping']} ms"

    checked_at = state.get("checked_at")

    if checked_at:
        checked_text = checked_at.strftime(
            "%H:%M:%S"
        )
    else:
        checked_text = "—"

    bad_count = monitor_state["bad_count"]

    return (
        "🔐 VLESS\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"Статус: {status}\n\n"
        f"Текущая: {ping_text}\n"
        f"Качество: {state['quality']}\n"
        f"Порог: {threshold} ms\n\n"
        f"Плохих проверок: "
        f"{bad_count} / {required_failures}\n\n"
        f"🕐 Проверено: {checked_text}"
    )