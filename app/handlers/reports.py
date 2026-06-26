import os

from telegram import Update
from telegram.ext import ContextTypes

from app.services.reports import (
    create_excel_report_file,
    create_pdf_report_file,
    get_report_data,
    validate_report_dates,
)


async def report_excel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Export attendance report as Excel.

    Commands:
    /report_excel
    /report_excel 26.06.26
    /report_excel 20.06.26 26.06.26
    """
    args = context.args

    is_valid, start_date, end_date, error_message = validate_report_dates(args)

    if not is_valid:
        await update.message.reply_html(
            "⚠️ <b>ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ!</b>\n"
            f"{error_message}\n\n"
            "Example:\n"
            "<code>/report_excel 26.06.26</code>\n"
            "<code>/report_excel 20.06.26 26.06.26</code>"
        )
        return

    reports_data = await get_report_data(start_date, end_date)

    if not reports_data:
        await update.message.reply_html(
            "⚠️ <b>មិនមានទិន្នន័យសម្រាប់កាលបរិច្ឆេទនេះទេ។</b>\n"
            "No data found for the specified period."
        )
        return

    status_message = await update.message.reply_html(
        "⏳ <b>កំពុងបង្កើតរបាយការណ៍ Excel...</b>\n"
        "Generating Excel report..."
    )

    file_path = None

    try:
        file_path, period = await create_excel_report_file(reports_data)

        with open(file_path, "rb") as file:
            excel_bytes = file.read()

        await update.message.reply_document(
            document=excel_bytes,
            filename=f"report_{period}.xlsx",
            caption=f"📊 Excel Report: {period.replace('_to_', ' to ')}",
            read_timeout=120,
            write_timeout=120,
        )

        try:
            await status_message.delete()
        except Exception:
            pass

    except Exception as error:
        try:
            await status_message.delete()
        except Exception:
            pass

        await update.message.reply_html(
            f"⚠️ <b>Error generating Excel report:</b>\n{error}"
        )

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


async def report_pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Export attendance report as PDF.

    Commands:
    /report_pdf
    /report_pdf 26.06.26
    /report_pdf 20.06.26 26.06.26
    """
    args = context.args

    is_valid, start_date, end_date, error_message = validate_report_dates(args)

    if not is_valid:
        await update.message.reply_html(
            "⚠️ <b>ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ!</b>\n"
            f"{error_message}\n\n"
            "Example:\n"
            "<code>/report_pdf 26.06.26</code>\n"
            "<code>/report_pdf 20.06.26 26.06.26</code>"
        )
        return

    reports_data = await get_report_data(start_date, end_date)

    if not reports_data:
        await update.message.reply_html(
            "⚠️ <b>មិនមានទិន្នន័យសម្រាប់កាលបរិច្ឆេទនេះទេ។</b>\n"
            "No data found for the specified period."
        )
        return

    status_message = await update.message.reply_html(
        "⏳ <b>កំពុងបង្កើតរបាយការណ៍ PDF...</b>\n"
        "Generating PDF report..."
    )

    file_path = None

    try:
        file_path, period = await create_pdf_report_file(reports_data)

        with open(file_path, "rb") as file:
            pdf_bytes = file.read()

        await update.message.reply_document(
            document=pdf_bytes,
            filename=f"report_{period}.pdf",
            caption=f"📄 PDF Report: {period.replace('_to_', ' to ')}",
            read_timeout=120,
            write_timeout=120,
        )

        try:
            await status_message.delete()
        except Exception:
            pass

    except Exception as error:
        try:
            await status_message.delete()
        except Exception:
            pass

        await update.message.reply_html(
            f"⚠️ <b>Error generating PDF report:</b>\n{error}"
        )

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass