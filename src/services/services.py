import json
import os
import subprocess


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