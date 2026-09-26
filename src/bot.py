import csv
import os
import threading
from datetime import datetime, timedelta

from telegram import (
    BotCommand,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
)

from config import BOT_TOKEN, PROXY_URL
from monitor import get_server_status
from collector import collect_loop


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = os.path.join(BASE_DIR, "data", "metrics.csv")


def format_bytes(value):
    return f"{value / 1024**3:.1f} GB"


def progress_bar(percent, length=10):
    filled = round(percent / 100 * length)
    return "█" * filled + "░" * (length - filled)


def format_period(hours):
    if hours == 1:
        return "1 час"
    if hours == 6:
        return "6 часов"
    if hours == 24:
        return "24 часа"
    if hours == 168:
        return "7 дней"

    return f"{hours} часов"


def read_metrics(hours):
    if not os.path.exists(CSV_FILE):
        return []

    since = datetime.now() - timedelta(hours=hours)
    metrics = []

    with open(CSV_FILE, "r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            timestamp = datetime.strptime(
                row["timestamp"],
                "%Y-%m-%d %H:%M:%S",
            )

            if timestamp >= since:
                metrics.append({
                    "timestamp": timestamp,
                    "cpu": float(row["cpu"]),
                    "ram_percent": float(row["ram_percent"]),
                    "disk_percent": float(row["disk_percent"]),
                })

    return metrics


def calculate_stats(metrics):
    cpu_values = [item["cpu"] for item in metrics]
    ram_values = [item["ram_percent"] for item in metrics]
    disk_values = [item["disk_percent"] for item in metrics]

    return {
        "cpu_avg": sum(cpu_values) / len(cpu_values),
        "cpu_min": min(cpu_values),
        "cpu_max": max(cpu_values),
        "ram_avg": sum(ram_values) / len(ram_values),
        "ram_min": min(ram_values),
        "ram_max": max(ram_values),
        "disk_start": disk_values[0],
        "disk_end": disk_values[-1],
        "disk_change": disk_values[-1] - disk_values[0],
    }


def build_stats_message(hours):
    metrics = read_metrics(hours)

    if not metrics:
        return (
            "📊 СТАТИСТИКА СЕРВЕРА\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            f"За последние {format_period(hours)} данных пока нет."
        )

    stats = calculate_stats(metrics)

    start_time = metrics[0]["timestamp"].strftime("%d.%m %H:%M")
    end_time = metrics[-1]["timestamp"].strftime("%d.%m %H:%M")

    change = stats["disk_change"]

    if change > 0:
        disk_change = f"+{change:.1f}%"
    else:
        disk_change = f"{change:.1f}%"

    return (
        "📊 СТАТИСТИКА СЕРВЕРА\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"Период: {format_period(hours)}\n"
        f"Измерений: {len(metrics)}\n\n"

        "⚡ CPU\n"
        f"Средняя: {stats['cpu_avg']:.1f}%\n"
        f"Минимум: {stats['cpu_min']:.1f}%\n"
        f"Максимум: {stats['cpu_max']:.1f}%\n\n"

        "🧠 RAM\n"
        f"Средняя: {stats['ram_avg']:.1f}%\n"
        f"Минимум: {stats['ram_min']:.1f}%\n"
        f"Максимум: {stats['ram_max']:.1f}%\n\n"

        "💾 DISK\n"
        f"В начале: {stats['disk_start']:.1f}%\n"
        f"Сейчас: {stats['disk_end']:.1f}%\n"
        f"Изменение: {disk_change}\n\n"

        "⏱ Период измерений\n"
        f"{start_time} — {end_time}"
    )


def stats_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "1 час",
                callback_data="stats_1",
            ),
            InlineKeyboardButton(
                "6 часов",
                callback_data="stats_6",
            ),
        ],
        [
            InlineKeyboardButton(
                "24 часа",
                callback_data="stats_24",
            ),
            InlineKeyboardButton(
                "7 дней",
                callback_data="stats_168",
            ),
        ],
    ])


async def setup_commands(application):
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("status", "Текущее состояние сервера"),
        BotCommand("stats", "Статистика сервера"),
    ]

    await application.bot.set_my_commands(commands)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот мониторинга сервера.\n\n"
        "Доступные команды:\n"
        "/status — текущее состояние сервера\n"
        "/stats — статистика нагрузки"
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

        "⏱ Uptime\n"
        f"{server['uptime']}"
    )

    await update.message.reply_text(message)


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = build_stats_message(24)

    await update.message.reply_text(
        message,
        reply_markup=stats_keyboard(),
    )


async def stats_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    hours = int(query.data.split("_")[1])
    message = build_stats_message(hours)

    await query.edit_message_text(
        message,
        reply_markup=stats_keyboard(),
    )


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

    builder = builder.post_init(setup_commands)

    application = builder.build()

    application.add_handler(
        CommandHandler("start", start)
    )

    application.add_handler(
        CommandHandler("status", status)
    )

    application.add_handler(
        CommandHandler("stats", stats)
    )

    application.add_handler(
        CallbackQueryHandler(
            stats_callback,
            pattern=r"^stats_",
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()