from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from src.services.services import load_services


def main_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📊 Состояние",
                callback_data="menu_status",
            ),
            InlineKeyboardButton(
                "📈 Статистика",
                callback_data="menu_stats",
            ),
        ],
        [
            InlineKeyboardButton(
                "🖥 Управление",
                callback_data="menu_management",
            ),
        ],
        [
            InlineKeyboardButton(
                "🌐 Сеть",
                callback_data="menu_network",
            ),
            InlineKeyboardButton(
                "🔐 VLESS",
                callback_data="menu_vless",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔔 Уведомления",
                callback_data="menu_notifications",
            ),
            InlineKeyboardButton(
                "📜 История",
                callback_data="menu_history",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ Настройки",
                callback_data="menu_settings",
            ),
        ],
    ])


def back_keyboard(callback_data="main_menu"):
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data=callback_data,
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
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu",
            ),
        ],
    ])


def stats_keyboard(active_hours=1):
    periods = [
        (1, "1ч"),
        (6, "6ч"),
        (24, "24ч"),
        (168, "7д"),
    ]

    buttons = []
    row = []

    for hours, title in periods:
        if hours == active_hours:
            title = f"✅ {title}"

        row.append(
            InlineKeyboardButton(
                title,
                callback_data=f"stats_{hours}",
            )
        )

        if len(row) == 2:
            buttons.append(row)
            row = []

    if row:
        buttons.append(row)

    buttons.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data="main_menu",
        ),
    ])

    return InlineKeyboardMarkup(buttons)


def management_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "📊 Процессы",
                callback_data="management_processes",
            ),
            InlineKeyboardButton(
                "⚙️ Сервисы",
                callback_data="management_services",
            ),
        ],
        [
            InlineKeyboardButton(
                "🐳 Docker",
                callback_data="management_docker",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu",
            ),
        ],
    ])


def process_keyboard(sort_by="cpu"):
    cpu_title = "✅ CPU" if sort_by == "cpu" else "⚡ CPU"
    ram_title = "✅ RAM" if sort_by == "ram" else "🧠 RAM"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                cpu_title,
                callback_data="processes_cpu",
            ),
            InlineKeyboardButton(
                ram_title,
                callback_data="processes_ram",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data=f"processes_{sort_by}",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="management_menu",
            ),
        ],
    ])


def docker_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="management_docker",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="management_menu",
            ),
        ],
    ])


def services_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="management_services",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔧 Перезапустить сервис",
                callback_data="service_restart_menu",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="management_menu",
            ),
        ],
    ])


def service_restart_keyboard():
    buttons = []

    for service in load_services():
        name = service.removesuffix(".service")

        buttons.append([
            InlineKeyboardButton(
                f"🔄 {name}",
                callback_data=f"service_restart:{service}",
            )
        ])

    buttons.append([
        InlineKeyboardButton(
            "⬅️ Назад",
            callback_data="management_services",
        ),
    ])

    return InlineKeyboardMarkup(buttons)


def network_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="network_refresh",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu",
            ),
        ],
    ])


def vless_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="menu_vless",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚙️ Настройки",
                callback_data="settings_vless",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu",
            ),
        ],
    ])


def notifications_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⚙️ Настройки уведомлений",
                callback_data="settings_notifications",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu",
            ),
        ],
    ])


def history_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Обновить",
                callback_data="menu_history",
            ),
        ],
        [
            InlineKeyboardButton(
                "🗑 Очистить",
                callback_data="history_clear",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu",
            ),
        ],
    ])


def settings_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🌐 Сеть",
                callback_data="settings_network",
            ),
            InlineKeyboardButton(
                "🔔 Уведомления",
                callback_data="settings_notifications",
            ),
        ],
        [
            InlineKeyboardButton(
                "📊 Мониторинг",
                callback_data="settings_monitoring",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚡ Система",
                callback_data="settings_system",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu",
            ),
        ],
    ])


def network_settings_keyboard(
    notifications_enabled=True,
):
    if notifications_enabled:
        notification_title = "🔔 Уведомления: 🟢 ВКЛ"
    else:
        notification_title = "🔔 Уведомления: 🔴 ВЫКЛ"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                notification_title,
                callback_data="network_notifications_toggle",
            ),
        ],
        [
            InlineKeyboardButton(
                "📡 Порог ping",
                callback_data="network_ping",
            ),
        ],
        [
            InlineKeyboardButton(
                "⏱ Интервал проверки",
                callback_data="network_interval",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔁 Плохих проверок",
                callback_data="network_failures",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="settings_back",
            ),
        ],
    ])


def cancel_input_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data="network_cancel",
            ),
        ],
    ])


def system_settings_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🔄 Перезапустить сервер",
                callback_data="system_reboot_confirm",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="settings_back",
            ),
        ],
    ])


def reboot_confirm_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "✅ Да, перезапустить",
                callback_data="system_reboot",
            ),
            InlineKeyboardButton(
                "❌ Отмена",
                callback_data="settings_system",
            ),
        ],
    ])

def notifications_settings_keyboard(settings):
    alerts = settings["alerts"]

    def status(key):
        return "🟢 ВКЛ" if alerts[key] else "🔴 ВЫКЛ"

    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"⚙️ Сервисы: {status('services')}",
                callback_data="notification_toggle:services",
            ),
        ],
        [
            InlineKeyboardButton(
                f"🐳 Docker: {status('docker')}",
                callback_data="notification_toggle:docker",
            ),
        ],
        [
            InlineKeyboardButton(
                f"🔐 VLESS: {status('vless')}",
                callback_data="notification_toggle:vless",
            ),
        ],
        [
            InlineKeyboardButton(
                f"⚡ CPU: {status('cpu')}",
                callback_data="notification_toggle:cpu",
            ),
        ],
        [
            InlineKeyboardButton(
                f"🧠 RAM: {status('ram')}",
                callback_data="notification_toggle:ram",
            ),
        ],
        [
            InlineKeyboardButton(
                f"💾 Диск: {status('disk')}",
                callback_data="notification_toggle:disk",
            ),
        ],
        [
            InlineKeyboardButton(
                f"🌐 Интернет: {status('internet')}",
                callback_data="notification_toggle:internet",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="main_menu",
            ),
        ],
    ])
def monitoring_settings_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "⏱ Интервал проверки",
                callback_data="monitor_interval",
            ),
        ],
        [
            InlineKeyboardButton(
                "⚡ Порог CPU",
                callback_data="monitor_cpu",
            ),
            InlineKeyboardButton(
                "🧠 Порог RAM",
                callback_data="monitor_ram",
            ),
        ],
        [
            InlineKeyboardButton(
                "💾 Порог диска",
                callback_data="monitor_disk",
            ),
        ],
        [
            InlineKeyboardButton(
                "🔁 Плохих проверок",
                callback_data="monitor_failures",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="settings_back",
            ),
        ],
    ])