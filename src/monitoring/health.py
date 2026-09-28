import psutil

from src.bot.messages import section_header
from src.monitoring.monitor import check_internet
from src.services.services import load_settings
from src.utils.utils import (
    current_time,
    format_bytes,
    progress_bar,
)


def get_health_status():
    memory = psutil.virtual_memory()
    disk = psutil.disk_usage("/")
    cpu = psutil.cpu_percent(interval=0.5)

    internet = check_internet()

    return {
        "cpu": cpu,
        "ram": memory.percent,
        "ram_used": memory.used,
        "ram_total": memory.total,
        "disk": disk.percent,
        "disk_used": disk.used,
        "disk_total": disk.total,
        "internet": internet,
        "load": psutil.getloadavg(),
        "uptime": (
            psutil.boot_time()
        ),
    }


def build_health_message():
    health = get_health_status()

    cpu = health["cpu"]
    ram = health["ram"]
    disk = health["disk"]

    internet = health["internet"]

    if internet["available"]:
        internet_status = (
            "🟢 Доступен\n"
            f"📡 Latency: "
            f"{internet['latency']:.0f} ms"
        )
    else:
        internet_status = "🔴 Недоступен"

    return (
        f"{section_header('❤️', 'СОСТОЯНИЕ СЕРВЕРА')}\n\n"
        f"⚡ CPU: {cpu:.1f}%\n"
        f"{progress_bar(cpu)}\n\n"
        f"🧠 RAM: {ram:.1f}%\n"
        f"{progress_bar(ram)}\n"
        f"{format_bytes(health['ram_used'])} / "
        f"{format_bytes(health['ram_total'])}\n\n"
        f"💾 Диск: {disk:.1f}%\n"
        f"{progress_bar(disk)}\n"
        f"{format_bytes(health['disk_used'])} / "
        f"{format_bytes(health['disk_total'])}\n\n"
        f"🌐 Интернет\n"
        f"{internet_status}\n\n"
        f"📈 Load average: "
        f"{health['load'][0]:.2f} "
        f"{health['load'][1]:.2f} "
        f"{health['load'][2]:.2f}\n\n"
        f"🕐 Обновлено: {current_time()}"
    )


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

    def check_threshold(
        self,
        name,
        value,
        threshold,
        enabled,
        required_failures,
    ):
        if not enabled:
            self.bad_counts[name] = 0
            self.alert_active[name] = False
            return None

        if value >= threshold:
            self.bad_counts[name] += 1
        else:
            self.bad_counts[name] = 0

            if self.alert_active[name]:
                self.alert_active[name] = False

                return {
                    "type": f"{name}_recovered",
                    "value": value,
                    "threshold": threshold,
                }

        if (
            self.bad_counts[name] >= required_failures
            and not self.alert_active[name]
        ):
            self.alert_active[name] = True

            return {
                "type": f"{name}_high",
                "value": value,
                "threshold": threshold,
            }

        return None

    def check_internet(
        self,
        enabled,
        required_failures,
    ):
        if not enabled:
            self.bad_counts["internet"] = 0
            self.alert_active["internet"] = False
            return None

        internet = check_internet()

        if internet["available"]:
            self.bad_counts["internet"] = 0

            if self.alert_active["internet"]:
                self.alert_active["internet"] = False

                return {
                    "type": "internet_recovered",
                }

            return None

        self.bad_counts["internet"] += 1

        if (
            self.bad_counts["internet"]
            >= required_failures
            and not self.alert_active["internet"]
        ):
            self.alert_active["internet"] = True

            return {
                "type": "internet_down",
            }

        return None

    def check_all(self):
        settings = load_settings()

        alerts = settings["alerts"]
        system = settings["system"]

        memory = psutil.virtual_memory()
        disk = psutil.disk_usage("/")
        cpu = psutil.cpu_percent(interval=0.5)

        required_failures = system[
            "required_failures"
        ]

        events = []

        checks = [
            (
                "cpu",
                cpu,
                system["cpu_threshold"],
                alerts["cpu"],
            ),
            (
                "ram",
                memory.percent,
                system["ram_threshold"],
                alerts["ram"],
            ),
            (
                "disk",
                disk.percent,
                system["disk_threshold"],
                alerts["disk"],
            ),
        ]

        for (
            name,
            value,
            threshold,
            enabled,
        ) in checks:
            event = self.check_threshold(
                name,
                value,
                threshold,
                enabled,
                required_failures,
            )

            if event:
                events.append(event)

        internet_event = self.check_internet(
            alerts["internet"],
            required_failures,
        )

        if internet_event:
            events.append(internet_event)

        return events


def format_health_event(event):
    event_type = event["type"]

    if event_type == "cpu_high":
        return (
            f"{section_header('🔴', 'ВЫСОКАЯ НАГРУЗКА CPU')}\n\n"
            f"⚡ CPU: {event['value']:.1f}%\n"
            f"📊 Порог: {event['threshold']}%\n\n"
            f"🕐 {current_time()}"
        )

    if event_type == "cpu_recovered":
        return (
            f"{section_header('🟢', 'CPU В НОРМЕ')}\n\n"
            f"⚡ CPU: {event['value']:.1f}%\n"
            f"📊 Порог: {event['threshold']}%\n\n"
            f"🕐 {current_time()}"
        )

    if event_type == "ram_high":
        return (
            f"{section_header('🔴', 'ВЫСОКАЯ НАГРУЗКА RAM')}\n\n"
            f"🧠 RAM: {event['value']:.1f}%\n"
            f"📊 Порог: {event['threshold']}%\n\n"
            f"🕐 {current_time()}"
        )

    if event_type == "ram_recovered":
        return (
            f"{section_header('🟢', 'RAM В НОРМЕ')}\n\n"
            f"🧠 RAM: {event['value']:.1f}%\n"
            f"📊 Порог: {event['threshold']}%\n\n"
            f"🕐 {current_time()}"
        )

    if event_type == "disk_high":
        return (
            f"{section_header('🔴', 'ДИСК ЗАПОЛНЕН')}\n\n"
            f"💾 Использование: "
            f"{event['value']:.1f}%\n"
            f"📊 Порог: {event['threshold']}%\n\n"
            f"🕐 {current_time()}"
        )

    if event_type == "disk_recovered":
        return (
            f"{section_header('🟢', 'ДИСК В НОРМЕ')}\n\n"
            f"💾 Использование: "
            f"{event['value']:.1f}%\n"
            f"📊 Порог: {event['threshold']}%\n\n"
            f"🕐 {current_time()}"
        )

    if event_type == "internet_down":
        return (
            f"{section_header('🔴', 'ИНТЕРНЕТ НЕДОСТУПЕН')}\n\n"
            "🌐 Сервер не может подключиться "
            "к интернету.\n\n"
            f"🕐 {current_time()}"
        )

    if event_type == "internet_recovered":
        return (
            f"{section_header('🟢', 'ИНТЕРНЕТ ВОССТАНОВЛЕН')}\n\n"
            "🌐 Подключение к интернету "
            "восстановлено.\n\n"
            f"🕐 {current_time()}"
        )

    return None