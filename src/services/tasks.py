import asyncio
import traceback

from src.config import CHAT_ID

from src.monitoring.health import (
    HealthMonitor,
    format_health_event,
)
from src.services.events import add_event
from src.services.services import (
    ServiceMonitor,
    format_event,
)
from src.services.settings import load_settings

service_monitor = ServiceMonitor()
health_monitor = HealthMonitor()


async def service_monitor_loop(application):
    service_monitor.initialize()

    while True:
        try:
            events = service_monitor.check_all()

            for event in events:
                add_event(
                    event["type"],
                    _history_message(event),
                )

                message = format_event(event)

                if message:
                    await application.bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                    )

            health_events = health_monitor.check_all()

            for event in health_events:
                add_event(
                    event["type"],
                    _history_message(event),
                )

                message = format_health_event(event)

                if message:
                    await application.bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                        parse_mode="HTML",
                    )

        except Exception as error:
            print(
                f"Service monitor error: {error}",
                flush=True,
            )
            traceback.print_exc()

        settings = load_settings()
        interval = settings["monitor"]["interval"]

        await asyncio.sleep(interval)


def _history_message(event):
    event_type = event["type"]

    if event_type == "service_down":
        name = event["name"].removesuffix(".service")
        return f"🔴 {name} остановлен"

    if event_type == "service_up":
        name = event["name"].removesuffix(".service")
        return f"🟢 {name} запущен"

    if event_type == "docker_down":
        return (
            f"🔴 Docker: {event['name']} "
            "остановлен"
        )

    if event_type == "docker_up":
        return (
            f"🟢 Docker: {event['name']} "
            "запущен"
        )

    if event_type == "vless_bad":
        if event["working"]:
            return (
                f"🔴 VLESS: высокий ping "
                f"{event['ping']} ms"
            )

        return "🔴 VLESS: Telegram недоступен"

    if event_type == "vless_recovered":
        return (
            f"🟢 VLESS: ping восстановлен "
            f"{event['ping']} ms"
        )

    if event_type == "cpu_high":
        return (
            f"🔴 CPU выше {event['threshold']}%: "
            f"{event['value']:.1f}%"
        )

    if event_type == "cpu_recovered":
        return (
            f"🟢 CPU в норме: "
            f"{event['value']:.1f}%"
        )

    if event_type == "ram_high":
        return (
            f"🔴 RAM выше {event['threshold']}%: "
            f"{event['value']:.1f}%"
        )

    if event_type == "ram_recovered":
        return (
            f"🟢 RAM в норме: "
            f"{event['value']:.1f}%"
        )

    if event_type == "disk_high":
        return (
            f"🔴 Диск выше {event['threshold']}%: "
            f"{event['value']:.1f}%"
        )

    if event_type == "disk_recovered":
        return (
            f"🟢 Диск в норме: "
            f"{event['value']:.1f}%"
        )

    if event_type == "internet_down":
        return "🔴 Интернет недоступен"

    if event_type == "internet_recovered":
        return "🟢 Интернет восстановлен"

    return event_type


async def post_init(application):
    from src.bot.handlers import setup_commands
    from src.notifications.startup_notify import (
        send_startup_message,
    )

    await setup_commands(application)

    try:
        send_startup_message()

    except Exception as error:
        print(
            f"Startup notification error: {error}",
            flush=True,
        )

    asyncio.create_task(
        service_monitor_loop(application)
    )