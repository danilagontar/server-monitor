import asyncio

from config import CHAT_ID
from src.monitoring.health import (
    HealthMonitor,
    format_health_event,
)
from src.services.services import (
    ServiceMonitor,
    format_event,
    load_settings,
)


service_monitor = ServiceMonitor()
health_monitor = HealthMonitor()


async def service_monitor_loop(application):
    service_monitor.initialize()

    while True:
        try:
            events = service_monitor.check_all()

            for event in events:
                message = format_event(event)

                if message:
                    await application.bot.send_message(
                        chat_id=CHAT_ID,
                        text=message,
                    )

            health_events = (
                health_monitor.check_all()
            )

            for event in health_events:
                message = format_health_event(
                    event
                )

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

        settings = load_settings()
        interval = settings["monitor"]["interval"]

        await asyncio.sleep(interval)


async def post_init(application):
    from src.bot.handlers import setup_commands

    await setup_commands(application)

    asyncio.create_task(
        service_monitor_loop(application)
    )