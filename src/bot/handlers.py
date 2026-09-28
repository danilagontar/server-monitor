from telegram import BotCommand, Update
from telegram.ext import ContextTypes

from src.config import CHAT_ID
from src.bot.keyboards import (
    build_main_keyboard,
    build_settings_keyboard,
    build_network_settings_keyboard,
)
from src.bot.messages import (
    build_status_message,
    build_docker_message,
    build_services_message,
    build_internet_message,
    build_processes_cpu_message,
    build_processes_ram_message,
    build_monitored_processes_message,
    build_settings_message,
    build_network_settings_message,
    build_input_message,
)
from src.monitoring.health import build_health_message
from src.monitoring.network import build_network_message
from src.services.services import update_setting
from src.statistics.stats import build_stats_message

async def setup_commands(application):
    commands = [
        BotCommand(
            "start",
            "Запустить бота",
        ),
        BotCommand(
            "status",
            "Текущее состояние сервера",
        ),
        BotCommand(
            "stats",
            "Статистика сервера",
        ),
        BotCommand(
            "system",
            "Управление сервером",
        ),
    ]

    await application.bot.set_my_commands(commands)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "Привет! Я бот мониторинга сервера.\n\n"
        "Доступные команды:\n"
        "/status — текущее состояние сервера\n"
        "/stats — статистика нагрузки\n"
        "/system — управление сервером"
    )


async def status(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        build_status_message(),
        reply_markup=status_keyboard(),
    )


async def stats(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        build_stats_message(24),
        reply_markup=stats_keyboard(),
    )


async def system(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    await update.message.reply_text(
        "🖥 УПРАВЛЕНИЕ СЕРВЕРОМ\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Выберите раздел:",
        reply_markup=system_keyboard(),
    )


async def handle_setting_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    setting = context.user_data.get(
        "setting_input"
    )

    if not setting:
        return

    text = update.message.text.strip()

    try:
        value = int(text)
    except ValueError:
        await update.message.reply_text(
            "❌ Нужно ввести целое число.\n\n"
            "Попробуйте ещё раз."
        )
        return

    if value <= 0:
        await update.message.reply_text(
            "❌ Значение должно быть больше 0.\n\n"
            "Попробуйте ещё раз."
        )
        return

    if setting == "ping":
        if value > 60000:
            await update.message.reply_text(
                "❌ Слишком большое значение.\n\n"
                "Укажите ping от 1 до 60000 ms."
            )
            return

        update_setting(
            "vless",
            "ping_threshold",
            value,
        )

        message = (
            "✅ Порог ping изменён.\n\n"
            f"Новое значение: {value} ms"
        )

    elif setting == "interval":
        if value > 86400:
            await update.message.reply_text(
                "❌ Слишком большое значение.\n\n"
                "Укажите интервал от 1 до 86400 секунд."
            )
            return

        update_setting(
            "monitor",
            "interval",
            value,
        )

        message = (
            "✅ Интервал проверки изменён.\n\n"
            f"Новое значение: {value} сек"
        )

    elif setting == "failures":
        if value > 100:
            await update.message.reply_text(
                "❌ Слишком большое значение.\n\n"
                "Укажите от 1 до 100 проверок."
            )
            return

        update_setting(
            "vless",
            "required_failures",
            value,
        )

        message = (
            "✅ Количество подтверждений изменено.\n\n"
            f"Новое значение: {value}"
        )

    else:
        return

    context.user_data.pop(
        "setting_input",
        None,
    )

    await update.message.reply_text(
        message,
        reply_markup=network_settings_keyboard(),
    )
async def health(update, context):
    await update.message.reply_text(
        build_health_message(),
        parse_mode="HTML",
    )


async def network(update, context):
    await update.message.reply_text(
        build_network_message(),
        parse_mode="HTML",
    )