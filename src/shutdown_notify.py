import requests

from config import BOT_TOKEN, CHAT_ID, PROXY_URL


def send_shutdown_message():
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
                "⚠️ СЕРВЕР ОТКЛЮЧАЕТСЯ\n\n"
                "Сервер сейчас уходит "
                "на перезагрузку или выключение."
            ),
        },
        proxies=proxies,
        timeout=10,
    )

    response.raise_for_status()


if __name__ == "__main__":
    try:
        send_shutdown_message()
        print(
            "Shutdown notification sent",
            flush=True,
        )
    except Exception as error:
        print(
            f"Shutdown notification error: {error}",
            flush=True,
        )