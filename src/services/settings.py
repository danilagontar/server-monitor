import json
import os


BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
)

SETTINGS_FILE = os.path.join(
    DATA_DIR,
    "settings.json",
)


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