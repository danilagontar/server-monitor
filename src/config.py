import os

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN", "")
CHAT_ID = os.getenv("CHAT_ID", "")
PROXY_URL = os.getenv("PROXY_URL", "")

ALLOWED_USER_IDS = [
    int(user_id.strip())
    for user_id in os.getenv(
        "ALLOWED_USER_IDS",
        CHAT_ID,
    ).split(",")
    if user_id.strip()
]