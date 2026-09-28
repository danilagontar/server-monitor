import time

import psutil

from monitor import check_internet
from services import check_telegram_proxy, load_settings


def get_network_stats():
    counters = psutil.net_io_counters()

    return {
        "bytes_sent": counters.bytes_sent,
        "bytes_recv": counters.bytes_recv,
        "packets_sent": counters.packets_sent,
        "packets_recv": counters.packets_recv,
    }


def get_network_interfaces():
    counters = psutil.net_io_counters(pernic=True)

    interfaces = []

    for name, counter in counters.items():
        if (
            counter.bytes_sent == 0
            and counter.bytes_recv == 0
        ):
            continue

        interfaces.append(
            {
                "name": name,
                "bytes_sent": counter.bytes_sent,
                "bytes_recv": counter.bytes_recv,
            }
        )

    return interfaces


def calculate_network_speed(
    previous,
    current,
    interval,
):
    if not previous or interval <= 0:
        return {
            "download": 0,
            "upload": 0,
        }

    download = (
        current["bytes_recv"]
        - previous["bytes_recv"]
    ) / interval

    upload = (
        current["bytes_sent"]
        - previous["bytes_sent"]
    ) / interval

    return {
        "download": max(0, download),
        "upload": max(0, upload),
    }


def format_speed(value):
    if value < 1024:
        return f"{value:.0f} B/s"

    if value < 1024**2:
        return f"{value / 1024:.1f} KB/s"

    if value < 1024**3:
        return f"{value / 1024**2:.1f} MB/s"

    return f"{value / 1024**3:.1f} GB/s"


def get_health_status():
    settings = load_settings()

    alerts = settings.get("alerts", {})
    system = settings.get("system", {})

    cpu_threshold = system.get(
        "cpu_threshold",
        90,
    )

    ram_threshold = system.get(
        "ram_threshold",
        90,
    )

    disk_threshold = system.get(
        "disk_threshold",
        90,
    )

    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu = psutil.cpu_percent(interval=0.5)

    internet = check_internet()
    telegram = check_telegram_proxy()

    internet_available = internet.get(
        "available",
        False,
    )

    telegram_working = telegram.get(
        "working",
        False,
    )

    telegram_ping = telegram.get(
        "ping",
        0,
    )

    return {
        "cpu": {
            "value": cpu,
            "threshold": cpu_threshold,
            "enabled": alerts.get("cpu", True),
            "ok": cpu < cpu_threshold,
        },
        "ram": {
            "value": memory.percent,
            "threshold": ram_threshold,
            "enabled": alerts.get("ram", True),
            "ok": memory.percent < ram_threshold,
        },
        "disk": {
            "value": disk.percent,
            "threshold": disk_threshold,
            "enabled": alerts.get("disk", True),
            "ok": disk.percent < disk_threshold,
        },
        "internet": {
            "available": internet_available,
            "latency": internet.get(
                "latency",
                0,
            ),
            "enabled": alerts.get(
                "internet",
                True,
            ),
        },
        "telegram": {
            "working": telegram_working,
            "ping": telegram_ping,
            "error": telegram.get(
                "error",
            ),
        },
    }


def build_health_message():
    health = get_health_status()

    cpu = health["cpu"]
    ram = health["ram"]
    disk = health["disk"]
    internet = health["internet"]
    telegram = health["telegram"]

    problems = []

    cpu_icon = "🟢"

    if cpu["enabled"] and not cpu["ok"]:
        cpu_icon = "🔴"
        problems.append("Высокая загрузка CPU")

    ram_icon = "🟢"

    if ram["enabled"] and not ram["ok"]:
        ram_icon = "🔴"
        problems.append(
            "Высокое использование RAM"
        )

    disk_icon = "🟢"

    if disk["enabled"] and not disk["ok"]:
        disk_icon = "🔴"
        problems.append(
            "Заканчивается место на диске"
        )

    if internet["available"]:
        internet_icon = "🟢"

        internet_text = (
            f'{internet["latency"]:.0f} ms'
        )
    else:
        internet_icon = "🔴"
        internet_text = "недоступен"

        if internet["enabled"]:
            problems.append(
                "Интернет недоступен"
            )

    if telegram["working"]:
        telegram_icon = "🟢"

        telegram_text = (
            f'{telegram["ping"]:.0f} ms'
        )
    else:
        telegram_icon = "🔴"
        telegram_text = "недоступен"

        problems.append(
            "Telegram через proxy недоступен"
        )

    message = (
        "🩺 <b>SERVER HEALTH</b>\n\n"
        f"{cpu_icon} CPU       "
        f"{cpu['value']:.1f}%\n"
        f"{ram_icon} RAM       "
        f"{ram['value']:.1f}%\n"
        f"{disk_icon} Disk      "
        f"{disk['value']:.1f}%\n"
        f"{internet_icon} Internet  "
        f"{internet_text}\n"
        f"{telegram_icon} Telegram  "
        f"{telegram_text}\n"
    )

    message += "\n━━━━━━━━━━━━━━\n\n"

    if problems:
        message += (
            f"⚠️ <b>Проблем: "
            f"{len(problems)}</b>\n"
        )

        for problem in problems:
            message += f"• {problem}\n"
    else:
        message += (
            "🟢 <b>Все основные системы "
            "работают нормально</b>"
        )

    return message


def build_network_message():
    stats = get_network_stats()

    interfaces = get_network_interfaces()

    message = (
        "🌐 <b>СЕТЬ</b>\n\n"
        f"📥 Получено: "
        f"{stats['bytes_recv'] / 1024**3:.2f} GB\n"
        f"📤 Отправлено: "
        f"{stats['bytes_sent'] / 1024**3:.2f} GB\n\n"
        f"📦 RX packets: "
        f"{stats['packets_recv']:,}\n"
        f"📦 TX packets: "
        f"{stats['packets_sent']:,}\n"
    )

    if interfaces:
        message += "\n<b>Интерфейсы:</b>\n"

        for interface in interfaces:
            name = interface["name"]

            received = (
                interface["bytes_recv"]
                / 1024**3
            )

            sent = (
                interface["bytes_sent"]
                / 1024**3
            )

            message += (
                f"\n<b>{name}</b>\n"
                f"  ↓ {received:.2f} GB\n"
                f"  ↑ {sent:.2f} GB\n"
            )

    return message


class HealthMonitor:
    def __init__(self):
        self.bad_counts = {
            "cpu": 0,
            "ram": 0,
            "disk": 0,
            "internet": 0,
        }

        self.alert_active = {
            "cpu": False,
            "ram": False,
            "disk": False,
            "internet": False,
        }

        self.previous_network = None
        self.previous_network_time = None

    def get_network_speed(self):
        current = get_network_stats()
        current_time = time.monotonic()

        if (
            self.previous_network is None
            or self.previous_network_time is None
        ):
            self.previous_network = current
            self.previous_network_time = current_time

            return {
                "download": 0,
                "upload": 0,
            }

        interval = (
            current_time
            - self.previous_network_time
        )

        speed = calculate_network_speed(
            self.previous_network,
            current,
            interval,
        )

        self.previous_network = current
        self.previous_network_time = current_time

        return speed

    def check_threshold(
        self,
        name,
        value,
        threshold,
        required_failures,
    ):
        if value >= threshold:
            self.bad_counts[name] += 1

            if (
                self.bad_counts[name]
                >= required_failures
                and not self.alert_active[name]
            ):
                self.alert_active[name] = True

                return {
                    "type": f"{name}_bad",
                    "value": value,
                    "threshold": threshold,
                }

            return None

        self.bad_counts[name] = 0

        if self.alert_active[name]:
            self.alert_active[name] = False

            return {
                "type": f"{name}_recovered",
                "value": value,
                "threshold": threshold,
            }

        return None

    def check_internet(
        self,
        required_failures,
    ):
        result = check_internet()

        if result.get("available"):
            value = 0
        else:
            value = 1

        return self.check_threshold(
            "internet",
            value,
            1,
            required_failures,
        )

    def check_all(self):
        settings = load_settings()

        alerts = settings.get(
            "alerts",
            {},
        )

        system = settings.get(
            "system",
            {},
        )

        required_failures = system.get(
            "required_failures",
            3,
        )

        events = []

        if alerts.get("cpu", True):
            cpu = psutil.cpu_percent(
                interval=0.5
            )

            event = self.check_threshold(
                "cpu",
                cpu,
                system.get(
                    "cpu_threshold",
                    90,
                ),
                required_failures,
            )

            if event:
                events.append(event)
        else:
            self.bad_counts["cpu"] = 0
            self.alert_active["cpu"] = False

        if alerts.get("ram", True):
            ram = psutil.virtual_memory()

            event = self.check_threshold(
                "ram",
                ram.percent,
                system.get(
                    "ram_threshold",
                    90,
                ),
                required_failures,
            )

            if event:
                events.append(event)
        else:
            self.bad_counts["ram"] = 0
            self.alert_active["ram"] = False

        if alerts.get("disk", True):
            disk = psutil.disk_usage("/")

            event = self.check_threshold(
                "disk",
                disk.percent,
                system.get(
                    "disk_threshold",
                    90,
                ),
                required_failures,
            )

            if event:
                events.append(event)
        else:
            self.bad_counts["disk"] = 0
            self.alert_active["disk"] = False

        if alerts.get("internet", True):
            event = self.check_internet(
                required_failures
            )

            if event:
                events.append(event)
        else:
            self.bad_counts["internet"] = 0
            self.alert_active["internet"] = False

        return events


def format_health_event(event):
    event_type = event["type"]

    if event_type == "cpu_bad":
        return (
            "🔴 <b>ВЫСОКАЯ ЗАГРУЗКА CPU</b>\n\n"
            f"CPU: {event['value']:.1f}%\n"
            f"Порог: {event['threshold']}%"
        )

    if event_type == "cpu_recovered":
        return (
            "🟢 <b>CPU В НОРМЕ</b>\n\n"
            f"CPU: {event['value']:.1f}%"
        )

    if event_type == "ram_bad":
        return (
            "🔴 <b>ВЫСОКОЕ ИСПОЛЬЗОВАНИЕ RAM</b>\n\n"
            f"RAM: {event['value']:.1f}%\n"
            f"Порог: {event['threshold']}%"
        )

    if event_type == "ram_recovered":
        return (
            "🟢 <b>RAM В НОРМЕ</b>\n\n"
            f"RAM: {event['value']:.1f}%"
        )

    if event_type == "disk_bad":
        return (
            "🔴 <b>ЗАКАНЧИВАЕТСЯ МЕСТО</b>\n\n"
            f"Disk: {event['value']:.1f}%\n"
            f"Порог: {event['threshold']}%"
        )

    if event_type == "disk_recovered":
        return (
            "🟢 <b>МЕСТО НА ДИСКЕ В НОРМЕ</b>\n\n"
            f"Disk: {event['value']:.1f}%"
        )

    if event_type == "internet_bad":
        return (
            "🔴 <b>ИНТЕРНЕТ НЕДОСТУПЕН</b>\n\n"
            "Проверка: 1.1.1.1:443"
        )

    if event_type == "internet_recovered":
        return (
            "🟢 <b>ИНТЕРНЕТ ВОССТАНОВЛЕН</b>"
        )

    return None