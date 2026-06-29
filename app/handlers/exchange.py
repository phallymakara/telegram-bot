from telegram import Update
from telegram.ext import ContextTypes

from app.database.repository import get_exchange_rate, set_exchange_rate


async def setexchange_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Set KHR to USD exchange rate.
    Command:
    /setexchange 4100
    """
    args = context.args

    if not args:
        current_rate = get_exchange_rate()

        await update.message.reply_html(
            f"<b>Current Exchange Rate:</b>\n"
            f"1$ = <b>{current_rate:,.0f}៛</b>\n\n"
            "enter new exchange rate:\n\n"
            "<code>/setexchange 4100</code>"
        )
        return

    try:
        rate = float(args[0])

        if rate <= 0:
            raise ValueError()

    except ValueError:
        await update.message.reply_html(
            "⚠️ <b>Error:</b> Exchange rate must positive number.\n\n"
            "Example:\n"
            "<code>/setexchange 4100</code>"
        )
        return

    try:
        set_exchange_rate(rate)

        await update.message.reply_html(
            "✅ Exchange rate updated successfully:</b>\n"
            f"1$ = <b>{rate:,.0f}៛</b>"
        )

    except Exception as error:
        await update.message.reply_html(
            f"⚠️ <b>Database error:</b> {error}"
        )