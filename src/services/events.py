import json
import os
from datetime import datetime

BASE_DIR = os.path.dirname(
    os.path.dirname(os.path.abspath(__file__))
)

DATA_DIR = os.path.join(
    BASE_DIR,
    "data",
)

EVENTS_FILE = os.path.join(
    DATA_DIR,
    "events.json",
)

MAX_EVENTS = 100


def ensure_events_file():
    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )

    if not os.path.exists(EVENTS_FILE):
        save_events([])


def load_events():
    ensure_events_file()

    try:
        with open(
            EVENTS_FILE,
            "r",
            encoding="utf-8",
        ) as file:
            events = json.load(file)
    except (json.JSONDecodeError, OSError):
        return []

    if not isinstance(events, list):
        return []

    return events


def save_events(events):
    os.makedirs(
        DATA_DIR,
        exist_ok=True,
    )

    with open(
        EVENTS_FILE,
        "w",
        encoding="utf-8",
    ) as file:
        json.dump(
            events,
            file,
            ensure_ascii=False,
            indent=4,
        )


def add_event(
    event_type,
    message,
):
    events = load_events()

    events.insert(
        0,
        {
            "type": event_type,
            "message": message,
            "time": datetime.now().strftime(
                "%Y-%m-%d %H:%M:%S"
            ),
        },
    )

    events = events[:MAX_EVENTS]

    save_events(events)


def get_events():
    return load_events()


def clear_events():
    save_events([])