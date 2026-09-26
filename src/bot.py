import threading

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN, PROXY_URL
from monitor import get_server_status
from collector import collect_loop


def format_bytes(value):
    return f"{value / 1024**3:.1f} GB"


def progress_bar(percent, length=10):
    filled = round(percent / 100 * length)
    return "█" * filled + "░" * (length - filled)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот мониторинга сервера.\n\n"
        "Доступные команды:\n"
        "/status — текущее состояние сервера"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    server = get_server_status()

    memory = server["memory"]
    disk = server["disk"]

    cpu = server["cpu"]
    ram = memory["percent"]
    disk_percent = disk["percent"]

    message = (
        "🖥 СЕРВЕР\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"🟢 {server['hostname']}\n\n"

        "⚡ CPU\n"
        f"{progress_bar(cpu)} {cpu:.1f}%\n\n"

        "🧠 RAM\n"
        f"{progress_bar(ram)} {ram:.1f}%\n"
        f"{format_bytes(memory['used'])} / "
        f"{format_bytes(memory['total'])}\n\n"

        "💾 DISK\n"
        f"{progress_bar(disk_percent)} {disk_percent:.1f}%\n"
        f"{format_bytes(disk['used'])} / "
        f"{format_bytes(disk['total'])}\n\n"

        f"⏱ Uptime\n"
        f"{server['uptime']}"
    )

    await update.message.reply_text(message)


def main():
    collector_thread = threading.Thread(
        target=collect_loop,
        daemon=True,
    )

    collector_thread.start()

    builder = Application.builder().token(BOT_TOKEN)

    if PROXY_URL:
        builder = builder.proxy(PROXY_URL)
        builder = builder.get_updates_proxy(PROXY_URL)

    application = builder.build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("status", status))

    application.run_polling()


if __name__ == "__main__":
    main()