from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from services import load_services


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
                "🔧 Перезапустить сервис",
                callback_data="service_restart_menu",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_menu",
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
            callback_data="system_services",
        ),
    ])

    return InlineKeyboardMarkup(buttons)


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


def settings_keyboard():
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                "🌐 Настройки сети",
                callback_data="settings_network",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_menu",
            ),
        ],
    ])


def network_settings_keyboard():
    return InlineKeyboardMarkup([
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
                "🔐 Вкл/выкл VLESS",
                callback_data="network_toggle",
            ),
        ],
        [
            InlineKeyboardButton(
                "⬅️ Назад",
                callback_data="system_settings",
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