from monitor import (
    check_internet,
    check_telegram_proxy,
    get_docker_status,
    get_monitored_processes,
    get_processes,
    get_server_status,
    get_services_status,
)
from services import load_settings
from utils import (
    current_time,
    format_bytes,
    format_process,
    progress_bar,
)


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
    return (
        "⚙️ НАСТРОЙКИ\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
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
        "🌐 НАСТРОЙКИ СЕТИ\n"
        "━━━━━━━━━━━━━━━━━━\n\n"
        "🔐 VLESS → Telegram\n\n"
        f"Статус уведомлений: {vless_status}\n\n"
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
            "📡 ПОРОГ PING\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Введите максимальный допустимый "
            "ping в миллисекундах.\n\n"
            "Например:\n"
            "500\n"
            "1000\n"
            "1500"
        )

    if setting == "interval":
        return (
            "⏱ ИНТЕРВАЛ ПРОВЕРКИ\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Введите интервал проверки "
            "в секундах.\n\n"
            "Например:\n"
            "10\n"
            "30\n"
            "60"
        )

    if setting == "failures":
        return (
            "🔁 КОЛИЧЕСТВО ПЛОХИХ ПРОВЕРОК\n"
            "━━━━━━━━━━━━━━━━━━\n\n"
            "Введите количество плохих проверок "
            "подряд до отправки уведомления.\n\n"
            "Например:\n"
            "1\n"
            "3\n"
            "5"
        )

    return "Введите значение:"