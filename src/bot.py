import csv
import os
import threading
from datetime import datetime, timedelta
import asyncio

from services import (
    ServiceMonitor,
    format_event,
    load_settings,
    save_settings,
)
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
from monitor import (
    check_internet,
    check_telegram_proxy,
    get_docker_status,
    get_monitored_processes,
    get_processes,
    get_server_status,
    get_services_status,
)
from collector import collect_loop


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CSV_FILE = os.path.join(BASE_DIR, "data", "metrics.csv")

service_monitor = ServiceMonitor()

def current_time():
    return datetime.now().strftime("%d.%m %H:%M:%S")


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
            f"За последние {format_period(hours)} "
            "данных пока нет."
        )

    stats = calculate_stats(metrics)

    start_time = metrics[0]["timestamp"].strftime(
        "%d.%m %H:%M"
    )
    end_time = metrics[-1]["timestamp"].strftime(
        "%d.%m %H:%M"
    )

    change = stats["disk_change"]

    if change > 0:
        disk_change = f"+{change:.1f}%"
    else:
        disk_change = f"{change:.1f}%"

    return (
        "📊 СТАТИСТИКА СЕРВЕРА\n"
        "━━━━━━━━━━━━━━━━━━\n"
        f"Данные на: {current_time()}\n\n"

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


def system_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🐳 Docker",
                callback_data="system_docker",
            ),
            InlineKeyboardButton(
                "⚙️ Службы",
                callback_data="system_services",
            ),
        ],
        [
            InlineKeyboardButton(
                "🌐 Интернет",
                callback_data="system_internet",
            ),
            InlineKeyboardButton(
                "📊 Процессы",
                callback_data="system_processes",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ Настройки",
                callback_data="system_settings",
            ),
        ],
    ])


def status_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="status_refresh",
            ),
        ],
    ])


def process_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⚡ Топ CPU",
                callback_data="processes_cpu",
            ),
            InlineKeyboardButton(
                "🧠 Топ RAM",
                callback_data="processes_ram",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔎 Сервисы и боты",
                callback_data="processes_monitored",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_menu",
            ),
        ],
    ])


def docker_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="system_docker",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_menu",
            ),
        ],
    ])


def services_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="system_services",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_menu",
            ),
        ],
    ])


def internet_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="system_internet",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_menu",
            ),
        ],
    ])


def process_cpu_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="processes_cpu",
            ),
        ],
        [
            InlineKeyboardButton(
                "🧠 Топ RAM",
                callback_data="processes_ram",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_processes",
            ),
        ],
    ])


def process_ram_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="processes_ram",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚡ Топ CPU",
                callback_data="processes_cpu",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_processes",
            ),
        ],
    ])


def monitored_processes_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="processes_monitored",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_processes",
            ),
        ],
    ])


def back_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_menu",
            ),
        ],
    ])


def build_status_message():
    server = get_server_status()

    memory = server["memory"]
    disk = server["disk"]

    cpu = server["cpu"]
    ram = memory["percent"]
    disk_percent = disk["percent"]

    return (
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
        f"{progress_bar(disk_percent)} "
        f"{disk_percent:.1f}%\n"
        f"{format_bytes(disk['used'])} / "
        f"{format_bytes(disk['total'])}\n\n"

        "⏱ Uptime\n"
        f"{server['uptime']}\n\n"

        f"🕐 Обновлено: {current_time()}"
    )


def build_docker_message():
    docker = get_docker_status()

    lines = [
        "🐳 DOCKER",
        "━━━━━━━━━━━━━━━━━━",
        current_time(),
        "",
    ]

    if not docker["available"]:
        lines.append(f"❌ {docker['error']}")
        return "\n".join(lines)

    containers = docker["containers"]

    if not containers:
        lines.append("Контейнеров нет.")
        return "\n".join(lines)

    lines.append(
        f"Найдено контейнеров: {len(containers)}"
    )
    lines.append("")

    for container in containers:
        status = container["status"]

        if status.lower().startswith("up"):
            icon = "🟢"
        else:
            icon = "🔴"

        lines.append(
            f"{icon} {container['name']}\n"
            f"   {status}"
        )

    return "\n".join(lines)


def build_services_message():
    services = get_services_status()

    lines = [
        "⚙️ СЛУЖБЫ",
        "━━━━━━━━━━━━━━━━━━",
        current_time(),
        "",
    ]

    for service in services:
        status = service["status"]
        uptime = service["uptime"] or "—"

        if status == "active":
            icon = "🟢"
        elif status == "inactive":
            icon = "🔴"
        else:
            icon = "🟡"

        name = service["name"].replace(
            ".service",
            "",
        )

        lines.append(
            f"{icon} {name} - {status}    {uptime}"
        )

    return "\n".join(lines)


def build_internet_message():
    internet = check_internet()
    telegram = check_telegram_proxy()

    lines = [
        "🌐 СЕТЬ",
        "━━━━━━━━━━━━━━━━━━",
        current_time(),
        "",
    ]

    if internet["available"]:
        lines.append(
            "🟢 Интернет: работает\n"
            f"   TCP latency: "
            f"{internet['latency']:.0f} ms"
        )
    else:
        lines.append(
            "🔴 Интернет: недоступен"
        )

    lines.extend([
        "",
        "🔐 VLESS → Telegram",
    ])

    if telegram["available"]:
        latency = telegram["latency"]

        if latency < 500:
            quality = "хорошее"
        elif latency < 1500:
            quality = "нормальное"
        else:
            quality = "медленное"

        lines.extend([
            "🟢 Прокси работает",
            f"   Telegram API: {latency:.0f} ms",
            f"   Качество: {quality}",
            "",
            "Telegram API успешно отвечает",
            "через SOCKS5 → Xray/VLESS.",
        ])
    else:
        lines.extend([
            "🔴 Прокси не работает",
            f"   Причина: {telegram['error']}",
            "",
            "Бот может не отправить сообщения",
            "в Telegram через этот прокси.",
        ])

    return "\n".join(lines)


def format_process(process):
    name = process["name"]

    if len(name) > 22:
        name = name[:19] + "..."

    return (
        f"{process['pid']:>6}  "
        f"{process['cpu']:>5.1f}%  "
        f"{process['memory']:>5.1f}%  "
        f"{name}"
    )


def build_processes_cpu_message():
    processes = get_processes()["cpu"]

    lines = [
        "⚡ ТОП ПРОЦЕССОВ ПО CPU",
        "━━━━━━━━━━━━━━━━━━",
        current_time(),
        "",
        "   PID    CPU    RAM   PROCESS",
        "",
    ]

    for process in processes:
        lines.append(format_process(process))

    return "\n".join(lines)


def build_processes_ram_message():
    processes = get_processes()["memory"]

    lines = [
        "🧠 ТОП ПРОЦЕССОВ ПО RAM",
        "━━━━━━━━━━━━━━━━━━",
        current_time(),
        "",
        "   PID    CPU    RAM   PROCESS",
        "",
    ]

    for process in processes:
        lines.append(format_process(process))

    return "\n".join(lines)


def build_monitored_processes_message():
    processes = get_monitored_processes()

    lines = [
        "🔎 СЕРВИСЫ И БОТЫ",
        "━━━━━━━━━━━━━━━━━━",
        current_time(),
        "",
    ]

    if not processes:
        lines.append(
            "Подходящих процессов сейчас не найдено."
        )
        return "\n".join(lines)

    for process in processes:
        name = process["name"]

        if len(name) > 25:
            name = name[:22] + "..."

        lines.append(
            f"🟢 {name}\n"
            f"   PID: {process['pid']}\n"
            f"   CPU: {process['cpu']:.1f}%\n"
            f"   RAM: {process['memory']:.1f}%"
        )

    return "\n".join(lines)


def build_settings_message():
    proxy = PROXY_URL if PROXY_URL else "не используется"

    return (
        "⚙️ НАСТРОЙКИ\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🤖 Бот: server-monitor\n"
        f"🌐 Proxy: {proxy}\n"
        "📁 Хранилище: CSV\n"
        "⏱ Сбор данных: каждые 60 секунд"
    )


async def setup_commands(application):
    commands = [
        BotCommand("start", "Запустить бота"),
        BotCommand("status", "Текущее состояние сервера"),
        BotCommand("stats", "Статистика сервера"),
        BotCommand("system", "Управление сервером"),
    ]

    await application.bot.set_my_commands(commands)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "Привет! Я бот мониторинга сервера.\n\n"
        "Доступные команды:\n"
        "/status — текущее состояние сервера\n"
        "/stats — статистика нагрузки\n"
        "/system — управление сервером"
    )


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        build_status_message(),
        reply_markup=status_keyboard(),
    )


async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        build_stats_message(24),
        reply_markup=stats_keyboard(),
    )


async def system(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🖥 УПРАВЛЕНИЕ СЕРВЕРОМ\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Выберите раздел:",
        reply_markup=system_keyboard(),
    )


async def stats_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    hours = int(query.data.split("_")[1])

    await query.edit_message_text(
        build_stats_message(hours),
        reply_markup=stats_keyboard(),
    )


async def system_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    action = query.data

    if action == "status_refresh":
        await query.edit_message_text(
            build_status_message(),
            reply_markup=status_keyboard(),
        )
        return

    if action == "system_menu":
        await query.edit_message_text(
            "🖥 УПРАВЛЕНИЕ СЕРВЕРОМ\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Выберите раздел:",
            reply_markup=system_keyboard(),
        )
        return

    if action == "system_docker":
        message = build_docker_message()
        keyboard = docker_keyboard()

    elif action == "system_services":
        message = build_services_message()
        keyboard = services_keyboard()

    elif action == "system_internet":
        message = build_internet_message()
        keyboard = internet_keyboard()

    elif action == "system_processes":
        message = (
            "📊 ПРОЦЕССЫ\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Выберите сортировку:"
        )
        keyboard = process_keyboard()

    elif action == "processes_cpu":
        message = build_processes_cpu_message()
        keyboard = process_cpu_keyboard()

    elif action == "processes_ram":
        message = build_processes_ram_message()
        keyboard = process_ram_keyboard()

    elif action == "processes_monitored":
        message = build_monitored_processes_message()
        keyboard = monitored_processes_keyboard()

    elif action == "system_settings":
        message = build_settings_message()
        keyboard = back_keyboard()

    else:
        return

    await query.edit_message_text(
        message,
        reply_markup=keyboard,
    )

async def service_monitor_loop(application):
    service_monitor.initialize()

    while True:
        try:
            events = service_monitor.check_all()

            for event in events:
                message = format_event(event)

                if message:
                    await application.bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                    )

        except Exception as error:
            print(f"Service monitor error: {error}")

        settings = load_settings()
        interval = settings["monitor"]["interval"]

        await asyncio.sleep(interval)

async def post_init(application):
    await setup_commands(application)

    asyncio.create_task(
        service_monitor_loop(application)
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

    builder = builder.post_init(post_init)

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
        CommandHandler("system", system)
    )

    application.add_handler(
        CallbackQueryHandler(
            stats_callback,
            pattern=r"^stats_",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            system_callback,
            pattern=r"^(system_|processes_|status_)",
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()