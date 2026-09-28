from src.monitoring.monitor import (
    check_internet,
    check_telegram_proxy,
    get_docker_status,
    get_monitored_processes,
    get_processes,
    get_server_status,
    get_services_status,
)
from src.services.services import load_settings
from src.utils.utils import (
    current_time,
    format_bytes,
    format_process,
    progress_bar,
)


def section_header(icon, title):
    return (
        f"{icon} {title}\n"
        "━━━━━━━━━━━━━━━━━━"
    )

def build_main_message():
    server = get_server_status()

    cpu = server["cpu"]
    ram = server["memory"]["percent"]
    temperature = server["temperature"]

    if temperature is None:
        temperature_text = "—"
    else:
        temperature_text = f"{temperature:.0f}°C"

    return (
        "🖥 SERVER MONITOR\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🟢 Сервер работает\n\n"
        f"⚡ CPU: {cpu:.1f}%   "
        f"🌡 CPU: {temperature_text}\n"
        f"🧠 RAM: {ram:.1f}%\n"
        f"⏱ Uptime: {server['uptime']}\n\n"
        "Выберите раздел:"
    )

def build_status_message():
    server = get_server_status()

    memory = server["memory"]
    disk = server["disk"]

    cpu = server["cpu"]
    ram = memory["percent"]
    disk_percent = disk["percent"]

    return (
        f"{section_header('📊', 'СТАТУС СЕРВЕРА')}\n\n"
        f"⚡ CPU: {cpu:.1f}%\n"
        f"{progress_bar(cpu)}\n\n"
        f"🧠 RAM: {ram:.1f}%\n"
        f"{progress_bar(ram)}\n"
        f"{format_bytes(memory['used'])} / "
        f"{format_bytes(memory['total'])}\n\n"
        f"💾 Диск: {disk_percent:.1f}%\n"
        f"{progress_bar(disk_percent)}\n"
        f"{format_bytes(disk['used'])} / "
        f"{format_bytes(disk['total'])}\n\n"
        f"⏱ Uptime: {server['uptime']}\n\n"
        f"🕐 Обновлено: {current_time()}"
    )


def build_docker_message():
    docker = get_docker_status()

    lines = [
        section_header("🐳", "DOCKER"),
        "",
    ]

    if not docker["available"]:
        lines.append(f"🔴 {docker['error']}")
        return "\n".join(lines)

    containers = docker["containers"]

    if not containers:
        lines.append("Контейнеров нет.")
        return "\n".join(lines)

    lines.append(
        f"📦 Контейнеров: {len(containers)}"
    )
    lines.append("")

    for container in containers:
        status = container["status"]

        if status.lower().startswith("up"):
            icon = "🟢"
        else:
            icon = "🔴"

        lines.extend([
            f"{icon} {container['name']}",
            f"   {status}",
            "",
        ])

    return "\n".join(lines).rstrip()


def build_services_message():
    services = get_services_status()

    lines = [
        section_header("⚙️", "СЕРВИСЫ"),
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

        lines.extend([
            f"{icon} {name}",
            f"   Статус: {status}",
            f"   Uptime: {uptime}",
            "",
        ])

    return "\n".join(lines).rstrip()


def build_internet_message():
    internet = check_internet()
    telegram = check_telegram_proxy()

    lines = [
        section_header("🌐", "СЕТЬ"),
        "",
    ]

    if internet["available"]:
        lines.extend([
            "🌐 Интернет",
            "🟢 Доступен",
            f"📡 TCP latency: "
            f"{internet['latency']:.0f} ms",
            "",
        ])
    else:
        lines.extend([
            "🌐 Интернет",
            "🔴 Недоступен",
            "",
        ])

    lines.append("🔐 VLESS → Telegram")
    lines.append("")

    if telegram["available"]:
        latency = telegram["latency"]

        if latency < 500:
            quality = "Хорошее"
        elif latency < 1500:
            quality = "Нормальное"
        else:
            quality = "Медленное"

        lines.extend([
            "🟢 Прокси работает",
            f"📡 Telegram API: {latency:.0f} ms",
            f"📊 Качество: {quality}",
            "",
            "Telegram API успешно отвечает",
            "через SOCKS5 → Xray/VLESS.",
        ])
    else:
        lines.extend([
            "🔴 Прокси не работает",
            f"Причина: {telegram['error']}",
            "",
            "Бот может не отправить сообщения",
            "в Telegram через этот прокси.",
        ])

    return "\n".join(lines)


def build_processes_cpu_message():
    processes = get_processes()["cpu"]

    lines = [
        section_header(
            "⚡",
            "ТОП ПРОЦЕССОВ ПО CPU",
        ),
        "",
        "PID      CPU     RAM    PROCESS",
        "──────────────────────────────",
    ]

    for process in processes:
        lines.append(format_process(process))

    return "\n".join(lines)


def build_processes_ram_message():
    processes = get_processes()["memory"]

    lines = [
        section_header(
            "🧠",
            "ТОП ПРОЦЕССОВ ПО RAM",
        ),
        "",
        "PID      CPU     RAM    PROCESS",
        "──────────────────────────────",
    ]

    for process in processes:
        lines.append(format_process(process))

    return "\n".join(lines)


def build_monitored_processes_message():
    processes = get_monitored_processes()

    lines = [
        section_header(
            "🔎",
            "СЕРВИСЫ И БОТЫ",
        ),
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

        lines.extend([
            f"🟢 {name}",
            f"   PID: {process['pid']}",
            f"   CPU: {process['cpu']:.1f}%",
            f"   RAM: {process['memory']:.1f}%",
            "",
        ])

    return "\n".join(lines).rstrip()


def build_settings_message():
    return (
        f"{section_header('⚙️', 'НАСТРОЙКИ')}\n\n"
        "Выберите раздел:"
    )


def build_network_settings_message():
    settings = load_settings()

    alerts = settings["alerts"]
    vless = settings["vless"]
    monitor = settings["monitor"]

    vless_status = (
        "🟢 ВКЛ"
        if alerts["vless"]
        else "🔴 ВЫКЛ"
    )

    return (
        f"{section_header('🌐', 'НАСТРОЙКИ СЕТИ')}\n\n"
        "🔐 VLESS → Telegram\n\n"
        f"🔔 Уведомления: {vless_status}\n\n"
        f"📡 Порог ping: "
        f"{vless['ping_threshold']} ms\n"
        f"⏱ Интервал проверки: "
        f"{monitor['interval']} сек\n"
        f"🔁 Плохих проверок подряд: "
        f"{vless['required_failures']}"
    )


def build_input_message(setting):
    if setting == "ping":
        return (
            f"{section_header('📡', 'ПОРОГ PING')}\n\n"
            "Введите максимальный допустимый "
            "ping в миллисекундах.\n\n"
            "Примеры:\n"
            "500\n"
            "1000\n"
            "1500"
        )

    if setting == "interval":
        return (
            f"{section_header('⏱', 'ИНТЕРВАЛ ПРОВЕРКИ')}\n\n"
            "Введите интервал проверки "
            "в секундах.\n\n"
            "Примеры:\n"
            "10\n"
            "30\n"
            "60"
        )

    if setting == "failures":
        return (
            f"{section_header('🔁', 'ПЛОХИЕ ПРОВЕРКИ')}\n\n"
            "Введите количество плохих проверок "
            "подряд до отправки уведомления.\n\n"
            "Примеры:\n"
            "1\n"
            "3\n"
            "5"
        )

    return "Введите значение:"