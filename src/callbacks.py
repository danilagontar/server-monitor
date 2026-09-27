import asyncio

from telegram import Update
from telegram.ext import ContextTypes

from config import CHAT_ID
from keyboards import (
    cancel_input_keyboard,
    docker_keyboard,
    internet_keyboard,
    monitored_processes_keyboard,
    network_settings_keyboard,
    process_cpu_keyboard,
    process_keyboard,
    process_ram_keyboard,
    service_restart_keyboard,
    services_keyboard,
    settings_keyboard,
    stats_keyboard,
    status_keyboard,
    system_keyboard,
)
from messages import (
    build_docker_message,
    build_internet_message,
    build_monitored_processes_message,
    build_network_settings_message,
    build_processes_cpu_message,
    build_processes_ram_message,
    build_services_message,
    build_settings_message,
    build_status_message,
    build_input_message,
)
from monitor import get_service_status
from services import (
    load_services,
    load_settings,
    restart_service,
    update_setting,
)
from stats import build_stats_message


async def stats_callback(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    query = update.callback_query

    await query.answer()

    hours = int(
        query.data.split("_")[1]
    )

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
        message = (
            build_monitored_processes_message()
        )
        keyboard = monitored_processes_keyboard()

    elif action == "system_settings":
        message = build_settings_message()
        keyboard = settings_keyboard()

    elif action == "settings_network":
        message = build_network_settings_message()
        keyboard = network_settings_keyboard()

    elif action == "network_ping":
        context.user_data[
            "setting_input"
        ] = "ping"

        await query.edit_message_text(
            build_input_message("ping"),
            reply_markup=cancel_input_keyboard(),
        )
        return

    elif action == "network_interval":
        context.user_data[
            "setting_input"
        ] = "interval"

        await query.edit_message_text(
            build_input_message("interval"),
            reply_markup=cancel_input_keyboard(),
        )
        return

    elif action == "network_failures":
        context.user_data[
            "setting_input"
        ] = "failures"

        await query.edit_message_text(
            build_input_message("failures"),
            reply_markup=cancel_input_keyboard(),
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

        await query.edit_message_text(
            build_network_settings_message(),
            reply_markup=network_settings_keyboard(),
        )
        return

    elif action == "network_cancel":
        context.user_data.pop(
            "setting_input",
            None,
        )

        await query.edit_message_text(
            build_network_settings_message(),
            reply_markup=network_settings_keyboard(),
        )
        return

    else:
        return

    await query.edit_message_text(
        message,
        reply_markup=keyboard,
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
        await query.edit_message_text(
            "🔧 ПЕРЕЗАПУСК СЕРВИСА\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Выберите сервис:",
            reply_markup=service_restart_keyboard(),
        )
        return

    if query.data == "service_restart_back":
        await query.edit_message_text(
            build_services_message(),
            reply_markup=services_keyboard(),
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
        await query.edit_message_text(
            "❌ Сервис не разрешён."
        )
        return

    name = service.removesuffix(
        ".service"
    )

    await query.edit_message_text(
        f"🔄 Перезапускаю {name}..."
    )

    success, message = restart_service(
        service
    )

    if not success:
        await query.edit_message_text(
            f"🔴 Не удалось перезапустить "
            f"{name}\n\n"
            f"{message}",
            reply_markup=service_restart_keyboard(),
        )
        return

    await asyncio.sleep(1)

    is_running = get_service_status(service)

    status = (
        "🟢 active"
        if is_running
        else "🔴 inactive"
    )

    await query.edit_message_text(
        f"✅ {name} перезапущен\n\n"
        f"Статус: {status}",
        reply_markup=service_restart_keyboard(),
    )