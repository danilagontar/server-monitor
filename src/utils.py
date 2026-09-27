from datetime import datetime


def current_time():
    return datetime.now().strftime("%d.%m %H:%M:%S")


def format_bytes(value):
    return f"{value / 1024**3:.1f} GB"


def progress_bar(percent, length=10):
    filled = round(percent / 100 * length)
    return "█" * filled + "░" * (length - filled)


def format_period(hours):
    if hours == 1:
        return "1 час"

    if hours == 6:
        return "6 часов"

    if hours == 24:
        return "24 часа"

    if hours == 168:
        return "7 дней"

    return f"{hours} часов"


def format_process(process):
    name = process["name"]

    if len(name) > 22:
        name = name[:19] + "..."

    return (
        f"{process['pid']:>6}  "
        f"{process['cpu']:>5.1f}%  "
        f"{process['memory']:>5.1f}%  "
        f"{name}"
    )