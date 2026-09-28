import os

import requests

from src.config import (
    BOT_TOKEN,
    CHAT_ID,
    PROXY_URL,
)

BASE_DIR = os.path.dirname(
    os.path.dirname(
        os.path.dirname(
            os.path.abspath(__file__)
        )
    )
)

BOOT_ID_FILE = os.path.join(
    BASE_DIR,
    "data",
    ".last_boot_id",
)


def get_boot_id():
    try:
        with open(
            "/proc/sys/kernel/random/boot_id",
            "r",
            encoding="utf-8",
        ) as file:
            return file.read().strip()
    except OSError:
        return None


def should_send_startup_message():
    boot_id = get_boot_id()

    if not boot_id:
        return False

    os.makedirs(
        os.path.dirname(BOOT_ID_FILE),
        exist_ok=True,
    )

    try:
        with open(
            BOOT_ID_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            previous_boot_id = file.read().strip()
    except OSError:
        previous_boot_id = ""

    if previous_boot_id == boot_id:
        return False

    with open(
        BOOT_ID_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        file.write(boot_id)

    return True


def send_startup_message():
    if not should_send_startup_message():
        return

    url = (
        f"https://api.telegram.org/bot{BOT_TOKEN}"
        "/sendMessage"
    )

    proxies = None

    if PROXY_URL:
        proxies = {
            "http": PROXY_URL,
            "https": PROXY_URL,
        }

    response = requests.post(
        url,
        data={
            "chat_id": CHAT_ID,
            "text": (
                "🟢 СЕРВЕР ПЕРЕЗАПУЩЕН\n\n"
                "Сервер успешно загрузился "
                "и готов к работе."
            ),
        },
        proxies=proxies,
        timeout=15,
    )

    response.raise_for_status()


if __name__ == "__main__":
    try:
        send_startup_message()
        print(
            "Startup notification checked",
            flush=True,
        )
    except Exception as error:
        print(
            f"Startup notification error: {error}",
            flush=True,
        )