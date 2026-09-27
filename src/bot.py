import threading

from config import BOT_TOKEN, PROXY_URL
from collector import collect_loop
from handlers import (
    handle_setting_input,
    start,
    stats,
    status,
    system,
)
from callbacks import (
    service_restart_callback,
    stats_callback,
    system_callback,
)
from tasks import post_init

from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)


def main():
    collector_thread = threading.Thread(
        target=collect_loop,
        daemon=True,
    )

    collector_thread.start()

    builder = Application.builder().token(
        BOT_TOKEN
    )

    if PROXY_URL:
        builder = builder.proxy(
            PROXY_URL
        )
        builder = builder.get_updates_proxy(
            PROXY_URL
        )

    builder = builder.post_init(
        post_init
    )

    application = builder.build()

    application.add_handler(
        CommandHandler(
            "start",
            start,
        )
    )

    application.add_handler(
        CommandHandler(
            "status",
            status,
        )
    )

    application.add_handler(
        CommandHandler(
            "stats",
            stats,
        )
    )

    application.add_handler(
        CommandHandler(
            "system",
            system,
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            stats_callback,
            pattern=r"^stats_",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            service_restart_callback,
            pattern=r"^service_restart",
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            system_callback,
            pattern=(
                r"^(system_|processes_|status_|"
                r"settings_|network_)"
            ),
        )
    )

    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_setting_input,
        )
    )

    application.run_polling()


if __name__ == "__main__":
    main()