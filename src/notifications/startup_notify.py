import requests

from src.config import BOT_TOKEN, CHAT_ID, PROXY_URL


def send_startup_message():
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
                "🟢 СЕРВЕР ЗАПУЩЕН\n\n"
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
            "Startup notification sent",
            flush=True,
        )
    except Exception as error:
        print(
            f"Startup notification error: {error}",
            flush=True,
        )