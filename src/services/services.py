import json
import os
import subprocess
import time
from datetime import datetime

import requests

from src.config import PROXY_URL


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)
DATA_DIR = os.path.join(BASE_DIR, "data")
SETTINGS_FILE = os.path.join(
    DATA_DIR,
    "settings.json",
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


DEFAULT_SETTINGS = {
    "alerts": {
        "services": True,
        "docker": True,
        "vless": True,
        "cpu": True,
        "ram": True,
        "disk": True,
        "internet": True,
    },
    "vless": {
        "ping_threshold": 1000,
        "required_failures": 3,
    },
    "system": {
        "cpu_threshold": 90,
        "ram_threshold": 90,
        "disk_threshold": 90,
        "required_failures": 3,
    },
    "monitor": {
        "interval": 30,
    },
}


def ensure_settings():
    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )

    if not os.path.exists(SETTINGS_FILE):
        save_settings(DEFAULT_SETTINGS)


def load_settings():
    ensure_settings()

    try:
        with open(
            SETTINGS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            settings = json.load(file)
    except (json.JSONDecodeError, OSError):
        settings = {}

    merged = {
        "alerts": DEFAULT_SETTINGS["alerts"].copy(),
        "vless": DEFAULT_SETTINGS["vless"].copy(),
        "system": DEFAULT_SETTINGS["system"].copy(),
        "monitor": DEFAULT_SETTINGS["monitor"].copy(),
    }

    merged["alerts"].update(
        settings.get("alerts", {})
    )
    merged["vless"].update(
        settings.get("vless", {})
    )
    merged["system"].update(
        settings.get("system", {})
    )
    merged["monitor"].update(
        settings.get("monitor", {})
    )

    return merged


def save_settings(settings):
    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )

    with open(
        SETTINGS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            settings,
            file,
            ensure_ascii=False,
            indent=4,
        )


def update_setting(section, key, value):
    settings = load_settings()
    settings[section][key] = value
    save_settings(settings)


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

    services = data.get("services", [])

    if not isinstance(services, list):
        return []

    return [
        service
        for service in services
        if isinstance(service, str)
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
    if service not in load_services():
        return False, "Сервис не разрешён"

    result = subprocess.run(
        [
            "sudo",
            "-n",
            "/usr/bin/systemctl",
            "restart",
            service,
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        error = (
            result.stderr.strip()
            or "Неизвестная ошибка"
        )
        return False, error

    return True, "Сервис успешно перезапущен"


def get_docker_state():
    result = subprocess.run(
        [
            "docker",
            "ps",
            "-a",
            "--format",
            "{{.Names}}|{{.State}}",
        ],
        capture_output=True,
        text=True,
    )

    containers = {}

    if result.returncode != 0:
        return containers

    for line in result.stdout.splitlines():
        if "|" not in line:
            continue

        name, state = line.split("|", 1)

        containers[name] = (
            state.strip().lower() == "running"
        )

    return containers


def check_telegram_proxy():
    if not PROXY_URL:
        return {
            "working": False,
            "ping": None,
            "error": "PROXY_URL is not set",
        }

    url = "https://api.telegram.org"

    start = time.monotonic()

    try:
        response = requests.get(
            url,
            proxies={
                "http": PROXY_URL,
                "https": PROXY_URL,
            },
            timeout=10,
        )

        elapsed = (
            time.monotonic() - start
        ) * 1000

        if response.status_code < 500:
            return {
                "working": True,
                "ping": round(elapsed),
                "error": None,
            }

        return {
            "working": False,
            "ping": round(elapsed),
            "error": f"HTTP {response.status_code}",
        }

    except requests.RequestException as error:
        return {
            "working": False,
            "ping": None,
            "error": str(error),
        }


def get_vless_state():
    result = check_telegram_proxy()
    settings = load_settings()

    threshold = settings["vless"]["ping_threshold"]

    if not result["working"]:
        return {
            "working": False,
            "ping": result["ping"],
            "quality": "недоступен",
            "high_ping": True,
            "error": result["error"],
        }

    ping = result["ping"]

    if ping <= 300:
        quality = "отличное"
    elif ping <= 700:
        quality = "хорошее"
    elif ping <= threshold:
        quality = "нормальное"
    else:
        quality = "плохое"

    return {
        "working": True,
        "ping": ping,
        "quality": quality,
        "high_ping": ping > threshold,
        "error": None,
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

    def check_services(self):
        settings = load_settings()

        current = get_services_state()
        events = []

        if self.previous_services is None:
            self.previous_services = current
            return events

        if settings["alerts"]["services"]:
            for service, is_running in current.items():
                previous = self.previous_services.get(service)

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
                previous = self.previous_docker.get(name)

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