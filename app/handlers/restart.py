import os

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.database.repository import get_exchange_rate, get_reports_by_dates, restart_attendance_count
from app.reports.generator import get_report_period_string
from app.reports.excel import generate_excel_report
from app.reports.pdf import generate_pdf_report


async def restartcount_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Ask confirmation before restarting attendance count.
    Command:
    /restartcount
    """
    reports_data = get_reports_by_dates(None, None)

    if not reports_data:
        await update.message.reply_html(
            "ℹ️ <b>មិនមានទិន្នន័យវត្តមានសម្រាប់លុបទេ!</b>\n"
            "There is no attendance data to restart."
        )
        return

    keyboard = [
        [
            InlineKeyboardButton(
                "⚠️ បញ្ជាក់លុប / Confirm Reset",
                callback_data="confirm_restart",
            ),
            InlineKeyboardButton(
                "❌ បោះបង់ / Cancel",
                callback_data="cancel_restart",
            ),
        ]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    warning_text = (
        "⚠️ <b>ការព្រមាន / Warning:</b>\n\n"
        "តើអ្នកពិតជាចង់កំណត់ការរាប់ឡើងវិញមែនទេ?\n"
        "រាល់ទិន្នន័យវត្តមាន និងរបាយការណ៍ទាំងអស់នឹងត្រូវបានលុបចេញពីប្រព័ន្ធ។\n\n"
        "មុនពេលលុប ប្រព័ន្ធនឹងបង្កើតឯកសារ Backup ជា PDF និង Excel ជាមុនសិន។\n\n"
        "Are you sure you want to restart the count?\n"
        "All attendance records and reports will be deleted after backup files are generated."
    )

    await update.message.reply_html(warning_text, reply_markup=reply_markup)


async def restartcount_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handle restart confirmation button.
    """
    query = update.callback_query
    await query.answer()

    if query.data == "cancel_restart":
        await query.edit_message_text(
            text=(
                "❌ <b>បានបោះបង់ការកំណត់ការរាប់ឡើងវិញ!</b>\n"
                "The restart count operation has been cancelled."
            ),
            parse_mode="HTML",
        )
        return

    if query.data != "confirm_restart":
        return

    await query.edit_message_text(
        text=(
            "⏳ <b>កំពុងបង្កើតឯកសារបម្រុងទុក...</b>\n"
            "Generating backup reports..."
        ),
        parse_mode="HTML",
    )

    reports_data = get_reports_by_dates(None, None)

    if not reports_data:
        await query.edit_message_text(
            text=(
                "ℹ️ <b>មិនមានទិន្នន័យសម្រាប់លុបទេ!</b>\n"
                "There is no attendance data to restart."
            ),
            parse_mode="HTML",
        )
        return

    os.makedirs("tmp", exist_ok=True)

    period = get_report_period_string(reports_data)
    exchange_rate = get_exchange_rate()

    excel_path = os.path.join("tmp", f"backup_report_{period}.xlsx")
    pdf_path = os.path.join("tmp", f"backup_report_{period}.pdf")

    excel_success = False
    pdf_success = False

    try:
        generate_excel_report(reports_data, excel_path, exchange_rate)
        excel_success = True
    except Exception as error:
        await query.message.reply_html(
            f"⚠️ <b>Error generating Excel backup:</b>\n{error}"
        )

    try:
        await generate_pdf_report(reports_data, period, pdf_path, exchange_rate)
        pdf_success = True
    except Exception as error:
        await query.message.reply_html(
            f"⚠️ <b>Error generating PDF backup:</b>\n{error}"
        )

    if excel_success and os.path.exists(excel_path):
        with open(excel_path, "rb") as file:
            excel_bytes = file.read()

        await query.message.reply_document(
            document=excel_bytes,
            filename=f"backup_report_{period}.xlsx",
            caption="📂 Excel Backup File",
            read_timeout=120,
            write_timeout=120,
        )

    if pdf_success and os.path.exists(pdf_path):
        with open(pdf_path, "rb") as file:
            pdf_bytes = file.read()

        await query.message.reply_document(
            document=pdf_bytes,
            filename=f"backup_report_{period}.pdf",
            caption="📂 PDF Backup File",
            read_timeout=120,
            write_timeout=120,
        )

    if not excel_success and not pdf_success:
        await query.message.reply_html(
            "⚠️ <b>Backup failed.</b>\n"
            "Attendance data was not deleted."
        )
        return

    try:
        restart_attendance_count()

        await query.edit_message_text(
            text=(
                "✅ <b>បានកំណត់ការរាប់ឡើងវិញដោយជោគជ័យ!</b>\n"
                "រាល់ទិន្នន័យវត្តមាន និងរបាយការណ៍ទាំងអស់ត្រូវបានលុបចេញពីប្រព័ន្ធ។\n\n"
                "✅ <b>Successfully restarted attendance count!</b>\n"
                "All attendance records and reports have been deleted."
            ),
            parse_mode="HTML",
        )

    except Exception as error:
        await query.message.reply_html(
            f"⚠️ <b>Error clearing database:</b>\n{error}"
        )

    finally:
        for file_path in [excel_path, pdf_path]:
            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass