import logging

from telegram import BotCommand
from telegram.ext import Application, CommandHandler, MessageHandler, filters

from app.config import BOT_TOKEN
from app.database.repository import init_db
from app.handlers.attendance import (
    handle_attendance_message,
    template_command,
)
from app.handlers.employees import (
    addemployees_command,
    deleteemployees_command,
    employees_command,
    updateemployee_command,
)


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def post_init(application: Application) -> None:
    try:
        await application.bot.set_my_commands(
            [
                BotCommand("template", "Get attendance template"),
                BotCommand("input", "Get attendance template"),
                BotCommand("employees", "List all employees"),
                BotCommand("addemployees", "Add employees"),
                BotCommand("updateemployee", "Update employee name"),
                BotCommand("deleteemployees", "Delete employees"),
            ]
        )
        logger.info("Successfully set bot commands.")
    except Exception as error:
        logger.error(f"Failed to set bot commands: {error}")


def main():
    init_db()

    if not BOT_TOKEN:
        logger.error("BOT_TOKEN is missing. Please check your .env file.")
        return

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(120.0)
        .pool_timeout(30.0)
        .build()
    )

    # Attendance commands
    app.add_handler(CommandHandler("template", template_command))
    app.add_handler(CommandHandler("input", template_command))

    # Employee commands
    app.add_handler(CommandHandler("employees", employees_command))
    app.add_handler(CommandHandler("employee", employees_command))

    app.add_handler(CommandHandler("addemployees", addemployees_command))
    app.add_handler(CommandHandler("addemployee", addemployees_command))

    app.add_handler(CommandHandler("updateemployee", updateemployee_command))
    app.add_handler(CommandHandler("updateemployees", updateemployee_command))

    app.add_handler(CommandHandler("deleteemployees", deleteemployees_command))
    app.add_handler(CommandHandler("deleteemployee", deleteemployees_command))

    # Normal text attendance message
    # This should stay near the bottom, after command handlers.
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_attendance_message,
        )
    )

    logger.info("Starting Telegram bot from app/main.py...")
    app.run_polling()


if __name__ == "__main__":
    main()