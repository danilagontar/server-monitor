from telegram import BotCommand, Update
from telegram.ext import ContextTypes

from src.bot.keyboards import (
    main_keyboard,
    network_settings_keyboard,
)
from src.bot.messages import (
    build_input_message,
    build_main_message,
)
from src.services.settings import (
    load_settings,
    update_setting,
)


async def setup_commands(application):
    commands = [
        BotCommand(
            "start",
            "Открыть главное меню",
        ),
    ]

    await application.bot.set_my_commands(commands)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    context.user_data.clear()

    await update.message.reply_text(
        build_main_message(),
        reply_markup=main_keyboard(),
    )


async def handle_setting_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
):
    if not update.message:
        return

    setting = context.user_data.get(
        "setting_input"
    )

    if not setting:
        return

    text = update.message.text.strip()

    try:
        value = int(text)
    except ValueError:
        await update.message.reply_text(
            "❌ Нужно ввести целое число.\n\n"
            "Попробуйте ещё раз."
        )
        return

    if value <= 0:
        await update.message.reply_text(
            "❌ Значение должно быть больше 0.\n\n"
            "Попробуйте ещё раз."
        )
        return

    if setting == "ping":
        if value > 60000:
            await update.message.reply_text(
                "❌ Слишком большое значение.\n\n"
                "Укажите ping от 1 до 60000 ms."
            )
            return

        update_setting(
            "vless",
            "ping_threshold",
            value,
        )

        message = (
            "✅ Порог ping изменён.\n\n"
            f"Новое значение: {value} ms"
        )

    elif setting == "interval":
        if value > 86400:
            await update.message.reply_text(
                "❌ Слишком большое значение.\n\n"
                "Укажите интервал от 1 до 86400 секунд."
            )
            return

        update_setting(
            "monitor",
            "interval",
            value,
        )

        message = (
            "✅ Интервал проверки изменён.\n\n"
            f"Новое значение: {value} сек"
        )

    elif setting == "failures":
        if value > 100:
            await update.message.reply_text(
                "❌ Слишком большое значение.\n\n"
                "Укажите от 1 до 100 проверок."
            )
            return

        update_setting(
            "vless",
            "required_failures",
            value,
        )

        message = (
            "✅ Количество подтверждений изменено.\n\n"
            f"Новое значение: {value}"
        )

    else:
        return

    context.user_data.pop(
        "setting_input",
        None,
    )

    settings = load_settings()

    await update.message.reply_text(
        message,
        reply_markup=network_settings_keyboard(
            settings["alerts"]["vless"]
        ),
    )