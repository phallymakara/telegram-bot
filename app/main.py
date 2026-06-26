import logging

from telegram import BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from app.config import BOT_TOKEN
from app.database.repository import init_db

from app.handlers.attendance import handle_attendance_message, template_command
from app.handlers.borrow import borrow_command
from app.handlers.employees import (
    addemployees_command,
    deleteemployees_command,
    employees_command,
    updateemployee_command,
)
from app.handlers.exchange import setexchange_command
from app.handlers.menu import menu_callback, menu_command, main_menu_keyboard
from app.handlers.reports import report_excel_command, report_pdf_command
from app.handlers.restart import restartcount_callback, restartcount_command


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)

logger = logging.getLogger(__name__)


async def start_command(update, context):
    """
    Show main button menu when user starts the bot.
    """
    await update.message.reply_html(
        "👋 <b>សូមស្វាគមន៍មកកាន់ Attendance & Salary Bot</b>\n"
        "<b>Welcome to Attendance & Salary Bot</b>\n\n"
        "សូមជ្រើសរើសមុខងារខាងក្រោម៖\n"
        "Please choose an option below:",
        reply_markup=main_menu_keyboard(),
    )


async def post_init(application: Application) -> None:
    """
    Show only /start in Telegram command menu.
    Other commands still work, but they are hidden from the command list.
    """
    try:
        await application.bot.set_my_commands(
            [
                BotCommand("start", "Start bot"),
            ]
        )
        logger.info("Successfully set bot commands.")
    except Exception as error:
        logger.error(f"Failed to set bot commands: {error}")


def main():
    if not BOT_TOKEN:
        raise ValueError("BOT_TOKEN is missing. Please check your .env file.")

    init_db()

    app = (
        Application.builder()
        .token(BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # =========================
    # Public command
    # =========================
    app.add_handler(CommandHandler("start", start_command))

    # Optional hidden command to reopen menu
    app.add_handler(CommandHandler("menu", menu_command))

    # =========================
    # Hidden backup commands
    # Users mainly use buttons, but these commands still work.
    # =========================

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

    # Exchange command
    app.add_handler(CommandHandler("setexchange", setexchange_command))

    # Borrow command
    app.add_handler(CommandHandler("borrow", borrow_command))

    # Report commands
    app.add_handler(CommandHandler("report_pdf", report_pdf_command))
    app.add_handler(CommandHandler("report_excel", report_excel_command))

    # Restart count command
    app.add_handler(CommandHandler("restartcount", restartcount_command))

    # =========================
    # Button callbacks
    # =========================

    # Main menu buttons
    app.add_handler(
        CallbackQueryHandler(
            menu_callback,
            pattern="^(menu_|attendance_|employees_|reports_|admin_)",
        )
    )

    # Restart confirmation buttons
    app.add_handler(
        CallbackQueryHandler(
            restartcount_callback,
            pattern="^(confirm_restart|cancel_restart)$",
        )
    )

    # =========================
    # Normal text attendance input
    # Must stay at the bottom.
    # =========================
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            handle_attendance_message,
        )
    )

    logger.info("Starting Attendance & Salary Bot...")
    app.run_polling()


if __name__ == "__main__":
    main()