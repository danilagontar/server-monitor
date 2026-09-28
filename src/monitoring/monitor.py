from datetime import datetime

from src.monitoring.vless import get_vless_state
from src.services.docker import get_docker_state
from src.services.services import get_services_state
from src.services.settings import load_settings


_vless_monitor_state = {
    "bad_count": 0,
    "was_bad": False,
    "state": None,
}


def get_vless_monitor_state():
    return {
        "bad_count": _vless_monitor_state["bad_count"],
        "was_bad": _vless_monitor_state["was_bad"],
        "state": _vless_monitor_state["state"],
    }


class ServiceMonitor:
    def __init__(self):
        self.previous_services = None
        self.previous_docker = None
        self.previous_vless = None

        self.vless_bad_count = 0
        self.vless_was_bad = False

    def initialize(self):
        self.previous_services = get_services_state()
        self.previous_docker = get_docker_state()

        vless = get_vless_state()
        self.previous_vless = vless

        if vless["high_ping"]:
            self.vless_bad_count = 1
        else:
            self.vless_bad_count = 0

        _update_vless_monitor_state(
            self,
            vless,
        )

    def check_services(self):
        settings = load_settings()

        current = get_services_state()
        events = []

        if self.previous_services is None:
            self.previous_services = current
            return events

        if settings["alerts"]["services"]:
            for service, is_running in current.items():
                previous = self.previous_services.get(
                    service
                )

                if previous is True and not is_running:
                    events.append({
                        "type": "service_down",
                        "name": service,
                    })

                elif previous is False and is_running:
                    events.append({
                        "type": "service_up",
                        "name": service,
                    })

        self.previous_services = current

        return events

    def check_docker(self):
        settings = load_settings()

        current = get_docker_state()
        events = []

        if self.previous_docker is None:
            self.previous_docker = current
            return events

        if settings["alerts"]["docker"]:
            for name, is_running in current.items():
                previous = self.previous_docker.get(
                    name
                )

                if previous is True and not is_running:
                    events.append({
                        "type": "docker_down",
                        "name": name,
                    })

                elif previous is False and is_running:
                    events.append({
                        "type": "docker_up",
                        "name": name,
                    })

            for name, previous in self.previous_docker.items():
                if name not in current and previous:
                    events.append({
                        "type": "docker_down",
                        "name": name,
                    })

        self.previous_docker = current

        return events

    def check_vless(self):
        settings = load_settings()
        vless = get_vless_state()

        if not settings["alerts"]["vless"]:
            self.vless_bad_count = 0
            self.vless_was_bad = False
            self.previous_vless = vless

            _update_vless_monitor_state(
                self,
                vless,
            )

            return []

        threshold = settings["vless"]["ping_threshold"]
        required_failures = settings["vless"]["required_failures"]

        events = []

        if vless["high_ping"]:
            self.vless_bad_count += 1
        else:
            self.vless_bad_count = 0

        if self.vless_bad_count >= required_failures:
            if not self.vless_was_bad:
                events.append({
                    "type": "vless_bad",
                    "ping": vless["ping"],
                    "threshold": threshold,
                    "working": vless["working"],
                    "error": vless["error"],
                })

                self.vless_was_bad = True

        elif (
            self.vless_was_bad
            and not vless["high_ping"]
        ):
            events.append({
                "type": "vless_recovered",
                "ping": vless["ping"],
                "threshold": threshold,
            })

            self.vless_was_bad = False

        self.previous_vless = vless

        _update_vless_monitor_state(
            self,
            vless,
        )

        return events

    def check_all(self):
        events = []

        events.extend(
            self.check_services()
        )
        events.extend(
            self.check_docker()
        )
        events.extend(
            self.check_vless()
        )

        return events


def _update_vless_monitor_state(
    monitor,
    state,
):
    _vless_monitor_state["bad_count"] = (
        monitor.vless_bad_count
    )
    _vless_monitor_state["was_bad"] = (
        monitor.vless_was_bad
    )
    _vless_monitor_state["state"] = state


def format_event(event):
    event_type = event["type"]

    if event_type == "service_down":
        return (
            "🚨 СЛУЖБА ОСТАНОВЛЕНА\n\n"
            f"{event['name']}\n\n"
            f"🕐 {datetime.now().strftime('%d.%m %H:%M:%S')}"
        )

    if event_type == "service_up":
        return (
            "🟢 СЛУЖБА ВОССТАНОВЛЕНА\n\n"
            f"{event['name']}\n\n"
            "Сервис снова работает."
        )

    if event_type == "docker_down":
        return (
            "🚨 DOCKER-КОНТЕЙНЕР ОСТАНОВЛЕН\n\n"
            f"{event['name']}\n\n"
            f"🕐 {datetime.now().strftime('%d.%m %H:%M:%S')}"
        )

    if event_type == "docker_up":
        return (
            "🟢 DOCKER-КОНТЕЙНЕР ВОССТАНОВЛЕН\n\n"
            f"{event['name']}\n\n"
            "Контейнер снова работает."
        )

    if event_type == "vless_bad":
        if event["working"]:
            return (
                "⚠️ VLESS → TELEGRAM\n\n"
                "Высокая задержка Telegram API.\n\n"
                f"📡 Ping: {event['ping']} ms\n"
                f"📈 Порог: {event['threshold']} ms"
            )

        return (
            "🔴 VLESS → TELEGRAM\n\n"
            "Telegram API недоступен через прокси.\n\n"
            f"Ошибка: {event['error']}"
        )

    if event_type == "vless_recovered":
        return (
            "🟢 VLESS → TELEGRAM\n\n"
            "Задержка восстановилась.\n\n"
            f"📡 Ping: {event['ping']} ms\n"
            f"📈 Порог: {event['threshold']} ms"
        )

    return None