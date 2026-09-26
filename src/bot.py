from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN, PROXY_URL
from monitor import get_server_status


def format_bytes(value):
    return f"{value / 1024**3:.1f} GB"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот мониторинга сервера.\n\n"
        "Доступные команды:\n"
        "/status — состояние сервера"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server = get_server_status()

    memory = server["memory"]
    disk = server["disk"]

    message = (
        f"Сервер: {server['hostname']}\n\n"
        f"CPU: {server['cpu']:.1f}%\n"
        f"RAM: {format_bytes(memory['used'])} / "
        f"{format_bytes(memory['total'])} ({memory['percent']:.1f}%)\n"
        f"Диск: {format_bytes(disk['used'])} / "
        f"{format_bytes(disk['total'])} ({disk['percent']:.1f}%)\n"
        f"Uptime: {server['uptime']}"
    )

    await update.message.reply_text(message)


def main():
    builder = Application.builder().token(BOT_TOKEN)

    if PROXY_URL:
        builder = builder.proxy(PROXY_URL).get_updates_proxy(PROXY_URL)

    application = builder.build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    application.run_polling()


if __name__ == "__main__":
    main()