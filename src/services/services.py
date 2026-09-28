import json
import os
import subprocess
import time
from datetime import datetime

from src.monitoring.vless import get_vless_state
from src.services.docker import get_docker_state
from src.services.settings import load_settings


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
)

SERVICES_FILE = os.path.join(
    DATA_DIR,
    "services.json",
)


DEFAULT_SERVICES = [
    "tickets-bot.service",
    "xray.service",
    "jozycat.service",
]


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


def ensure_services():
    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )

    if not os.path.exists(SERVICES_FILE):
        save_services(DEFAULT_SERVICES)


def load_services():
    ensure_services()

    try:
        with open(
            SERVICES_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            data = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    services = data.get(
        "services",
        [],
    )

    if not isinstance(
        services,
        list,
    ):
        return []

    return [
        service
        for service in services
        if isinstance(
            service,
            str,
        )
        and service.strip()
    ]


def save_services(services):
    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )

    with open(
        SERVICES_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            {
                "services": services,
            },
            file,
            ensure_ascii=False,
            indent=4,
        )


def get_service_status(service):
    result = subprocess.run(
        [
            "systemctl",
            "is-active",
            service,
        ],
        capture_output=True,
        text=True,
    )

    return result.stdout.strip() == "active"


def get_services_state():
    return {
        service: get_service_status(service)
        for service in load_services()
    }


def restart_service(service):
    print(
        f"RESTART REQUEST: {service!r}",
        flush=True,
    )

    allowed_services = {
        "tickets-bot.service",
        "xray.service",
        "jozycat.service",
    }

    if service not in allowed_services:
        print(
            f"RESTART DENIED: {service!r}",
            flush=True,
        )
        return False, "Сервис не разрешён"

    command = [
        "/usr/bin/sudo",
        "-n",
        "/usr/bin/systemctl",
        "restart",
        service,
    ]

    print(
        f"RESTART COMMAND: {command!r}",
        flush=True,
    )

    result = subprocess.run(
        command,
        capture_output=True,
        text=True,
        timeout=30,
    )

    print(
        f"RESTART RESULT: code={result.returncode} "
        f"stdout={result.stdout!r} "
        f"stderr={result.stderr!r}",
        flush=True,
    )

    if result.returncode != 0:
        error = (
            result.stderr.strip()
            or result.stdout.strip()
            or "Неизвестная ошибка"
        )

        return False, error

    return True, "Сервис успешно перезапущен"


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