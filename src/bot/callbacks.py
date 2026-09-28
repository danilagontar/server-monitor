import asyncio

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from src.config import CHAT_ID
from src.bot.keyboards import (
    stats_keyboard,
    system_keyboard,
    status_keyboard,
    process_keyboard,
    docker_keyboard,
    services_keyboard,
    service_restart_keyboard,
    internet_keyboard,
    process_cpu_keyboard,
    process_ram_keyboard,
    monitored_processes_keyboard,
    settings_keyboard,
    network_settings_keyboard,
    cancel_input_keyboard,
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
)
from src.monitoring.monitor import get_service_status
from src.services.services import (
    restart_service,
    load_services,
    update_setting,
)
from src.statistics.stats import build_stats_message


async def safe_edit_message(
    query,
    text,
    reply_markup=None,
):
    try:
        await query.edit_message_text(
            text,
            reply_markup=reply_markup,
        )
    except BadRequest as error:
        if "Message is not modified" not in str(error):
            raise


async def stats_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    hours = int(
        query.data.split("_")[1]
    )

    await safe_edit_message(
        query,
        build_stats_message(hours),
        stats_keyboard(),
    )


async def system_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    action = query.data

    if action == "status_refresh":
        await safe_edit_message(
            query,
            build_status_message(),
            status_keyboard(),
        )
        return

    if action == "system_menu":
        await safe_edit_message(
            query,
            "🖥 УПРАВЛЕНИЕ СЕРВЕРОМ\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Выберите раздел:",
            system_keyboard(),
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
        keyboard = settings_keyboard()

    elif action == "settings_network":
        message = build_network_settings_message()
        keyboard = network_settings_keyboard()

    elif action == "network_ping":
        context.user_data["setting_input"] = "ping"

        await safe_edit_message(
            query,
            build_input_message("ping"),
            cancel_input_keyboard(),
        )
        return

    elif action == "network_interval":
        context.user_data["setting_input"] = "interval"

        await safe_edit_message(
            query,
            build_input_message("interval"),
            cancel_input_keyboard(),
        )
        return

    elif action == "network_failures":
        context.user_data["setting_input"] = "failures"

        await safe_edit_message(
            query,
            build_input_message("failures"),
            cancel_input_keyboard(),
        )
        return

    elif action == "network_toggle":
        settings = load_settings()

        current = settings["alerts"]["vless"]

        update_setting(
            "alerts",
            "vless",
            not current,
        )

        await safe_edit_message(
            query,
            build_network_settings_message(),
            network_settings_keyboard(),
        )
        return

    elif action == "network_cancel":
        context.user_data.pop(
            "setting_input",
            None,
        )

        await safe_edit_message(
            query,
            build_network_settings_message(),
            network_settings_keyboard(),
        )
        return

    else:
        return

    await safe_edit_message(
        query,
        message,
        keyboard,
    )


async def service_restart_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    if str(query.message.chat_id) != str(CHAT_ID):
        await query.answer(
            "Доступ запрещён",
            show_alert=True,
        )
        return

    await query.answer()

    if query.data == "service_restart_menu":
        services = load_services()

        if not services:
            await safe_edit_message(
                query,
                "🔧 ПЕРЕЗАПУСК СЕРВИСА\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Список сервисов пуст.",
                service_restart_keyboard(),
            )
            return

        await safe_edit_message(
            query,
            "🔧 ПЕРЕЗАПУСК СЕРВИСА\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Выберите сервис:",
            service_restart_keyboard(),
        )
        return

    if query.data == "service_restart_back":
        await safe_edit_message(
            query,
            build_services_message(),
            services_keyboard(),
        )
        return

    if not query.data.startswith(
        "service_restart:"
    ):
        return

    service = query.data.split(
        ":",
        1,
    )[1]

    if service not in load_services():
        await safe_edit_message(
            query,
            "❌ Сервис не разрешён.",
            service_restart_keyboard(),
        )
        return

    name = service.removesuffix(
        ".service"
    )

    await safe_edit_message(
        query,
        f"🔄 Перезапускаю {name}...",
    )

    success, message = restart_service(
        service
    )

    if not success:
        await safe_edit_message(
            query,
            f"🔴 Не удалось перезапустить "
            f"{name}\n\n"
            f"{message}",
            service_restart_keyboard(),
        )
        return

    for _ in range(5):
        await asyncio.sleep(0.5)

        if get_service_status(service):
            await safe_edit_message(
                query,
                f"✅ {name} успешно перезапущен\n\n"
                "Статус: 🟢 active",
                service_restart_keyboard(),
            )
            return

    await safe_edit_message(
        query,
        f"⚠️ Команда на перезапуск {name} "
        "отправлена.\n\n"
        "Сервис пока не перешёл в состояние "
        "`active`.",
        service_restart_keyboard(),
    )