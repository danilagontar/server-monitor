import time
from datetime import datetime

import requests


SOCKS_PROXY = "socks5h://127.0.0.1:1080"
TEST_URL = "https://www.google.com"
DEFAULT_TIMEOUT = 10
DEFAULT_LATENCY_THRESHOLD = 1000
MAX_BAD_CHECKS = 3


_state = {
    "bad_checks": 0,
    "last_check": None,
    "status": "unknown",
    "latency": None,
}


def check_vless(
    timeout=DEFAULT_TIMEOUT,
    latency_threshold=DEFAULT_LATENCY_THRESHOLD,
):
    proxies = {
        "http": SOCKS_PROXY,
        "https": SOCKS_PROXY,
    }

    started = time.monotonic()

    try:
        response = requests.get(
            TEST_URL,
            proxies=proxies,
            timeout=timeout,
            allow_redirects=True,
        )

        latency = round(
            (time.monotonic() - started) * 1000
        )

        if response.status_code >= 400:
            raise requests.RequestException(
                f"HTTP {response.status_code}"
            )

        if latency > latency_threshold:
            status = "warning"
        else:
            status = "working"

        _state["bad_checks"] = 0
        _state["status"] = status
        _state["latency"] = latency
        _state["last_check"] = datetime.now()

        return {
            "status": status,
            "latency": latency,
            "bad_checks": 0,
            "last_check": _state["last_check"],
        }

    except (
        requests.RequestException,
        OSError,
    ):
        _state["bad_checks"] = min(
            _state["bad_checks"] + 1,
            MAX_BAD_CHECKS,
        )
        _state["status"] = "down"
        _state["latency"] = None
        _state["last_check"] = datetime.now()

        return {
            "status": "down",
            "latency": None,
            "bad_checks": _state["bad_checks"],
            "last_check": _state["last_check"],
        }


def get_vless_status(
    timeout=DEFAULT_TIMEOUT,
    latency_threshold=DEFAULT_LATENCY_THRESHOLD,
):
    return check_vless(
        timeout=timeout,
        latency_threshold=latency_threshold,
    )


def build_vless_message(
    timeout=DEFAULT_TIMEOUT,
    latency_threshold=DEFAULT_LATENCY_THRESHOLD,
):
    result = get_vless_status(
        timeout=timeout,
        latency_threshold=latency_threshold,
    )

    if result["status"] == "working":
        status_text = "🟢 Работает"
    elif result["status"] == "warning":
        status_text = "🟡 Проблемы"
    else:
        status_text = "🔴 Недоступен"

    if result["latency"] is None:
        latency_text = "—"
    else:
        latency_text = f"{result['latency']} ms"

    if result["last_check"] is None:
        checked_text = "—"
    else:
        checked_text = result["last_check"].strftime(
            "%H:%M:%S"
        )

    return (
        "🔐 VLESS\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        f"Статус: {status_text}\n\n"
        f"Latency: {latency_text}\n"
        f"Порог: {latency_threshold} ms\n\n"
        f"Плохих проверок: "
        f"{result['bad_checks']} / {MAX_BAD_CHECKS}\n\n"
        f"🕐 Проверено: {checked_text}"
    )