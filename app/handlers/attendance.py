from telegram import Update
from telegram.ext import ContextTypes

from app.services.attendance import (
    build_attendance_template,
    build_single_day_report,
    parse_attendance_message,
)


async def template_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Show attendance template.
    Commands:
    /template
    /input
    """
    template_text = build_attendance_template()

    await update.message.reply_html(
        "📋 <b>សូមចម្លងបញ្ជីខាងក្រោម រួចកែសម្រួលវត្តមានបុគ្គលិក៖</b>\n"
        "<b>Copy and edit the attendance list below:</b>\n\n"
        f"<code>{template_text}</code>"
    )


async def handle_attendance_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle normal text messages as attendance reports.
    """
    text = update.message.text

    if not text:
        return

    day_blocks = parse_attendance_message(text)

    if not day_blocks:
        if update.message.chat.type == "private":
            await update.message.reply_html(
                "<b>សុំទោស ខ្ញុំមិនយល់ពីទម្រង់ទិន្នន័យនេះទេ។</b>\n"
                "Sorry, I couldn't parse the format of your message.\n\n"
                "សូមផ្ញើជាបញ្ជីវត្តមាន ឬវាយ /template ដើម្បីយកគំរូ។\n"
                "Please send the attendance list or type /template to get the template."
            )
        return

    if len(day_blocks) == 1:
        try:
            report_text = build_single_day_report(day_blocks[0])
            await update.message.reply_html(report_text)
        except Exception as error:
            await update.message.reply_html(
                f"⚠️ <b>Error while creating attendance report:</b>\n{error}"
            )
        return

    await update.message.reply_html(
        "⚠️ Multi-day attendance is parsed successfully, but multi-day report output "
        "has not been moved to the new structure yet.\n\n"
        "Please submit one day at a time for now."
    )