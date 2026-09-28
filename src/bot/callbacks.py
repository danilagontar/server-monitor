import asyncio
import subprocess

from telegram import Update
from telegram.error import BadRequest
from telegram.ext import ContextTypes

from src.bot.keyboards import (
    main_keyboard,
    back_keyboard,
    status_keyboard,
    stats_keyboard,
    management_keyboard,
    process_keyboard,
    docker_keyboard,
    services_keyboard,
    service_restart_keyboard,
    network_keyboard,
    vless_keyboard,
    notifications_keyboard,
    history_keyboard,
    settings_keyboard,
    network_settings_keyboard,
    cancel_input_keyboard,
    system_settings_keyboard,
    reboot_confirm_keyboard,
    notifications_settings_keyboard,
    monitoring_settings_keyboard,
)
from src.bot.messages import (
    build_input_message,
    build_main_message,
    build_status_message,
    build_docker_message,
    build_services_message,
    build_processes_cpu_message,
    build_processes_ram_message,
    build_settings_message,
    build_network_settings_message,
    build_history_message,
    build_monitoring_settings_message,
)
from src.monitoring.monitor import get_service_status
from src.monitoring.network import build_network_message
from src.monitoring.vless import build_vless_message
from src.services.services import (
    restart_service,
    load_services,
)
from src.services.settings import (
    load_settings,
    update_setting,
)
from src.statistics.stats import build_stats_message
from src.config import ALLOWED_USER_IDS


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


async def show_main_menu(query):
    await safe_edit_message(
        query,
        build_main_message(),
        main_keyboard(),
    )


async def show_management(query):
    text = (
        "🖥 УПРАВЛЕНИЕ\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "Выберите раздел:"
    )

    await safe_edit_message(
        query,
        text,
        management_keyboard(),
    )


async def show_settings(query):
    await safe_edit_message(
        query,
        build_settings_message(),
        settings_keyboard(),
    )


async def callback_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query

    if query.from_user.id not in ALLOWED_USER_IDS:
        await query.answer(
            "Доступ запрещён",
            show_alert=True,
        )
        return

    await query.answer()

    action = query.data

    if action == "main_menu":
        await show_main_menu(query)
        return

    if action == "menu_status":
        await safe_edit_message(
            query,
            build_status_message(),
            status_keyboard(),
        )
        return

    if action == "status_refresh":
        await safe_edit_message(
            query,
            build_status_message(),
            status_keyboard(),
        )
        return

    if action == "menu_stats":
        await safe_edit_message(
            query,
            build_stats_message(1),
            stats_keyboard(1),
        )
        return

    if action.startswith("stats_"):
        hours = int(
            action.split("_")[1]
        )

        await safe_edit_message(
            query,
            build_stats_message(hours),
            stats_keyboard(hours),
        )
        return

    if action == "menu_management":
        await show_management(query)
        return

    if action == "management_menu":
        await show_management(query)
        return

    if action == "management_processes":
        await safe_edit_message(
            query,
            build_processes_cpu_message(),
            process_keyboard("cpu"),
        )
        return

    if action == "processes_cpu":
        await safe_edit_message(
            query,
            build_processes_cpu_message(),
            process_keyboard("cpu"),
        )
        return

    if action == "processes_ram":
        await safe_edit_message(
            query,
            build_processes_ram_message(),
            process_keyboard("ram"),
        )
        return

    if action == "management_docker":
        await safe_edit_message(
            query,
            build_docker_message(),
            docker_keyboard(),
        )
        return

    if action == "management_services":
        await safe_edit_message(
            query,
            build_services_message(),
            services_keyboard(),
        )
        return

    if action == "service_restart_menu":
        services = load_services()

        if not services:
            message = (
                "🔧 ПЕРЕЗАПУСК СЕРВИСА\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Список сервисов пуст."
            )
        else:
            message = (
                "🔧 ПЕРЕЗАПУСК СЕРВИСА\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Выберите сервис:"
            )

        await safe_edit_message(
            query,
            message,
            service_restart_keyboard(),
        )
        return

    if action.startswith("service_restart:"):
        await restart_service_callback(query)
        return

    if action == "menu_network":
        text = await asyncio.to_thread(
            build_network_message
        )

        await safe_edit_message(
            query,
            text,
            network_keyboard(),
        )
        return

    if action == "network_refresh":
        text = await asyncio.to_thread(
            build_network_message
        )

        await safe_edit_message(
            query,
            text,
            network_keyboard(),
        )
        return

    if action == "menu_vless":
        text = await asyncio.to_thread(
            build_vless_message
        )

        await safe_edit_message(
            query,
            text,
            vless_keyboard(),
        )
        return

    if action == "menu_notifications":
        settings = load_settings()

        text = (
            "🔔 УВЕДОМЛЕНИЯ\n"
            "━━━━━━━━━━━━━━━━━━"
        )

        await safe_edit_message(
            query,
            text,
            notifications_settings_keyboard(
                settings
            ),
        )
        return

    if action.startswith("notification_toggle:"):
        notification = action.split(":", 1)[1]

        settings = load_settings()

        if notification not in settings["alerts"]:
            return

        current = settings["alerts"][notification]

        update_setting(
            "alerts",
            notification,
            not current,
        )

        settings = load_settings()

        await safe_edit_message(
            query,
            (
                "🔔 УВЕДОМЛЕНИЯ\n"
                "━━━━━━━━━━━━━━━━━━"
            ),
            notifications_settings_keyboard(
                settings
            ),
        )
        return

    if action == "menu_history":
        await safe_edit_message(
            query,
            build_history_message(),
            history_keyboard(),
        )
        return

    if action == "history_clear":
        from src.services.events import clear_events

        clear_events()

        await safe_edit_message(
            query,
            build_history_message(),
            history_keyboard(),
        )
        return

    if action == "menu_settings":
        await show_settings(query)
        return

    if action == "settings_back":
        previous = context.user_data.get(
            "settings_previous",
            "menu_settings",
        )

        if previous == "menu_vless":
            text = await asyncio.to_thread(
                build_vless_message
            )

            await safe_edit_message(
                query,
                text,
                vless_keyboard(),
            )
            return

        if previous == "menu_notifications":
            await safe_edit_message(
                query,
                (
                    "🔔 УВЕДОМЛЕНИЯ\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"
                    "Настройки уведомлений."
                ),
                notifications_keyboard(),
            )
            return

        await show_settings(query)
        return

    if action == "network_notifications_toggle":
        settings = load_settings()

        current = settings["alerts"]["vless"]

        update_setting(
            "alerts",
            "vless",
            not current,
        )

        settings = load_settings()

        await safe_edit_message(
            query,
            build_network_settings_message(),
            network_settings_keyboard(
                settings["alerts"]["vless"]
            ),
        )
        return

    if action == "settings_network":
        context.user_data["settings_previous"] = (
            "menu_settings"
        )

        await safe_edit_message(
            query,
            build_network_settings_message(),
            network_settings_keyboard(),
        )
        return

    if action == "settings_vless":
        context.user_data["settings_previous"] = (
            "menu_vless"
        )

        await safe_edit_message(
            query,
            build_network_settings_message(),
            network_settings_keyboard(),
        )
        return

    if action == "settings_notifications":
        context.user_data["settings_previous"] = (
            "menu_settings"
        )

        settings = load_settings()

        await safe_edit_message(
            query,
            (
                "🔔 УВЕДОМЛЕНИЯ\n"
                "━━━━━━━━━━━━━━━━━━"
            ),
            notifications_settings_keyboard(
                settings,
                "settings_back",
            ),
        )
        return

    if action == "settings_monitoring":
        context.user_data["settings_previous"] = (
            "menu_settings"
        )

        await safe_edit_message(
            query,
            build_monitoring_settings_message(),
            monitoring_settings_keyboard(),
        )
        return

    if action == "settings_system":
        context.user_data["settings_previous"] = (
            "menu_settings"
        )

        await safe_edit_message(
            query,
            (
                "⚡ СИСТЕМА\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Управление сервером."
            ),
            system_settings_keyboard(),
        )
        return

    if action == "system_reboot_confirm":
        await safe_edit_message(
            query,
            (
                "⚠️ ПЕРЕЗАПУСК СЕРВЕРА\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Вы действительно хотите "
                "перезапустить сервер?"
            ),
            reboot_confirm_keyboard(),
        )
        return

    if action == "system_reboot":
        result = subprocess.run(
            [
                "/usr/bin/sudo",
                "-n",
                "/usr/bin/systemctl",
                "reboot",
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            error = (
                result.stderr.strip()
                or result.stdout.strip()
                or "Неизвестная ошибка"
            )

            await safe_edit_message(
                query,
                (
                    "🔴 ОШИБКА ПЕРЕЗАПУСКА\n"
                    "━━━━━━━━━━━━━━━━━━\n\n"
                    f"{error}"
                ),
                system_settings_keyboard(),
            )
            return

        await safe_edit_message(
            query,
            (
                "🔄 ПЕРЕЗАПУСК СЕРВЕРА\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Сервер перезапускается..."
            ),
        )
        return

    if action == "monitor_interval":
        context.user_data["setting_input"] = (
            "monitor_interval"
        )

        await safe_edit_message(
            query,
            (
                "⏱ ИНТЕРВАЛ ПРОВЕРКИ\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Введите интервал в секундах:"
            ),
            cancel_input_keyboard(),
        )
        return

    if action == "monitor_cpu":
        context.user_data["setting_input"] = (
            "monitor_cpu"
        )

        await safe_edit_message(
            query,
            (
                "⚡ ПОРОГ CPU\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Введите порог в процентах:"
            ),
            cancel_input_keyboard(),
        )
        return

    if action == "monitor_ram":
        context.user_data["setting_input"] = (
            "monitor_ram"
        )

        await safe_edit_message(
            query,
            (
                "🧠 ПОРОГ RAM\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Введите порог в процентах:"
            ),
            cancel_input_keyboard(),
        )
        return

    if action == "monitor_disk":
        context.user_data["setting_input"] = (
            "monitor_disk"
        )

        await safe_edit_message(
            query,
            (
                "💾 ПОРОГ ДИСКА\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Введите порог в процентах:"
            ),
            cancel_input_keyboard(),
        )
        return

    if action == "monitor_failures":
        context.user_data["setting_input"] = (
            "monitor_failures"
        )

        await safe_edit_message(
            query,
            (
                "🔁 ПЛОХИХ ПРОВЕРОК\n"
                "━━━━━━━━━━━━━━━━━━\n\n"
                "Введите количество проверок:"
            ),
            cancel_input_keyboard(),
        )
        return

    if action == "network_ping":
        context.user_data["setting_input"] = "ping"

        await safe_edit_message(
            query,
            build_input_message("ping"),
            cancel_input_keyboard(),
        )
        return

    if action == "network_interval":
        context.user_data["setting_input"] = "interval"

        await safe_edit_message(
            query,
            build_input_message("interval"),
            cancel_input_keyboard(),
        )
        return

    if action == "network_failures":
        context.user_data["setting_input"] = "failures"

        await safe_edit_message(
            query,
            build_input_message("failures"),
            cancel_input_keyboard(),
        )
        return

    if action == "network_cancel":
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


async def restart_service_callback(query):
    data = query.data

    if data == "service_restart_menu":
        return

    service = data.split(
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
            (
                f"🔴 Не удалось перезапустить "
                f"{name}\n\n"
                f"{message}"
            ),
            service_restart_keyboard(),
        )
        return

    for _ in range(5):
        await asyncio.sleep(0.5)

        if get_service_status(service):
            await safe_edit_message(
                query,
                (
                    f"✅ {name} успешно перезапущен\n\n"
                    "Статус: 🟢 active"
                ),
                service_restart_keyboard(),
            )
            return

    await safe_edit_message(
        query,
        (
            f"⚠️ Команда на перезапуск {name} "
            "отправлена.\n\n"
            "Сервис пока не перешёл в состояние "
            "`active`."
        ),
        service_restart_keyboard(),
    )