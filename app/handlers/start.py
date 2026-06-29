from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.menu import main_menu_keyboard


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Start bot and show button menu.
    """
    await update.message.reply_html(
        "👋 <b>សូមស្វាគមន៍មកកាន់ Attendance & Salary Bot</b>\n"
        "<b>Welcome to Attendance & Salary Bot</b>\n\n"
        "សូមជ្រើសរើសមុខងារខាងក្រោម៖\n"
        "Please choose an option below:",
        reply_markup=main_menu_keyboard(),
    )