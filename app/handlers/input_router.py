import os

from telegram import Update
from telegram.ext import ContextTypes

from app.handlers.menu import main_menu_keyboard

from app.database.repository import (
    get_exchange_rate,
    record_borrow,
    set_exchange_rate,
)
from app.handlers.attendance import handle_attendance_message
from app.services.employees import (
    add_employees_from_text,
    delete_employees_from_text,
    get_employee_list_text,
    rename_employee,
)
from app.services.reports import (
    create_excel_report_file,
    create_pdf_report_file,
    get_report_data,
    validate_report_dates,
)
from app.services.salary import calculate_borrow_deduction, calculate_debt


def clear_mode(context: ContextTypes.DEFAULT_TYPE):
    context.user_data.pop("mode", None)


async def show_main_menu(update: Update):
    await update.message.reply_text(
        "Main Menu\n\n"
        "Please choose the next action:",
        reply_markup=main_menu_keyboard(),
    )


async def handle_add_employee_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    result = add_employees_from_text(text)

    clear_mode(context)

    success_items = result.get("success", [])
    error_items = result.get("errors", [])

    added_count = len(success_items)
    skipped_count = len(error_items)

    success_text = "\n".join(success_items) if success_items else "None"
    error_text = "\n".join(error_items) if error_items else "None"

    await update.message.reply_html(
        "✅ <b>Employee Add Result</b>\n\n"
        f"Added: <b>{added_count}</b>\n"
        f"Skipped: <b>{skipped_count}</b>\n\n"
        "<b>Added Employees:</b>\n"
        f"{success_text}\n\n"
        "<b>Skipped / Errors:</b>\n"
        f"{error_text}"
    )
    await show_main_menu(update)


async def handle_update_employee_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    if "->" not in text:
        await update.message.reply_html(
            "⚠️ <b>Invalid format.</b>\n\n"
            "Please use this format:\n"
            "<code>old name -> new name</code>"
        )
        return

    old_name, new_name = text.split("->", 1)
    old_name = old_name.strip()
    new_name = new_name.strip()

    success, message = rename_employee(old_name, new_name)

    clear_mode(context)

    if success:
        await update.message.reply_html(f"✅ {message}")
    else:
        await update.message.reply_html(f"⚠️ {message}")
    await show_main_menu(update)


async def handle_delete_employee_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()

    result = delete_employees_from_text(text)

    clear_mode(context)

    await update.message.reply_html(
        "🗑️ <b>Employee Delete Result</b>\n\n"
        f"Deleted: <b>{result['deleted']}</b>\n"
        f"Not found: <b>{result['not_found']}</b>\n\n"
        f"{result['message']}"
    )
    await show_main_menu(update)


async def handle_exchange_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip().replace(",", "")

    try:
        rate = float(text)

        if rate <= 0:
            raise ValueError()

    except ValueError:
        await update.message.reply_html(
            "⚠️ <b>Invalid exchange rate.</b>\n\n"
            "Please send only the number.\n"
            "Example:\n"
            "<code>4100</code>"
        )
        return

    set_exchange_rate(rate)

    clear_mode(context)

    await update.message.reply_html(
        "✅ <b>Exchange rate updated successfully.</b>\n\n"
        f"1$ = <b>{rate:,.0f}៛</b>"
    )
    await show_main_menu(update)


async def handle_borrow_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    parts = text.split()

    if len(parts) < 2:
        await update.message.reply_html(
            "⚠️ <b>Invalid format.</b>\n\n"
            "Please send:\n"
            "<code>employee name amount</code>\n\n"
            "Example:\n"
            "<code>ប៉ែន ទិត្យ 250000</code>"
        )
        return

    amount_text = parts[-1].replace(",", "")

    try:
        amount = float(amount_text)

        if amount < 0:
            raise ValueError()

    except ValueError:
        await update.message.reply_html(
            "⚠️ <b>Invalid amount.</b>\n\n"
            "Please send:\n"
            "<code>ប៉ែន ទិត្យ 250000</code>"
        )
        return

    employee_name = " ".join(parts[:-1]).strip()
    deduction = calculate_borrow_deduction(amount)

    success, result_or_error, report_day = record_borrow(
        employee_name,
        amount,
        deduction,
    )

    if not success:
        await update.message.reply_html(result_or_error)
        return

    clear_mode(context)

    registered_name = result_or_error

    if amount == 0:
        await update.message.reply_html(
            "✅ <b>Borrow cleared successfully.</b>\n\n"
            f"👤 Employee: <b>{registered_name}</b>\n"
            f"📅 Date: <b>{report_day}</b>"
        )
        return

    debt = calculate_debt(amount, deduction)

    await update.message.reply_html(
        "✅ <b>Borrow recorded successfully.</b>\n\n"
        f"👤 Employee: <b>{registered_name}</b>\n"
        f"📅 Date: <b>{report_day}</b>\n"
        f"💵 Borrow Amount: <b>{int(amount):,}៛</b>\n"
        f"✂️ Deduction: <b>{int(deduction):,}៛</b>\n"
        f"🔴 Debt: <b>{int(debt):,}៛</b>"
    )
    await show_main_menu(update)


async def send_report_file(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    report_type: str,
    args: list[str],
):
    is_valid, start_date, end_date, error_message = validate_report_dates(args)

    if not is_valid:
        await update.message.reply_html(
            "⚠️ <b>Invalid date format.</b>\n\n"
            f"{error_message}\n\n"
            "Please use:\n"
            "<code>26.06.26</code>\n"
            "or\n"
            "<code>20.06.26 26.06.26</code>"
        )
        return

    reports_data = await get_report_data(start_date, end_date)

    if not reports_data:
        clear_mode(context)

        await update.message.reply_html(
            "⚠️ <b>No report data found for this period.</b>"
        )

        await show_main_menu(update)
        return

    status_message = await update.message.reply_html(
        "⏳ <b>Generating report...</b>"
    )

    file_path = None

    try:
        if report_type == "excel":
            file_path, period = await create_excel_report_file(reports_data)
            filename = f"report_{period}.xlsx"
            caption = f"📊 Excel Report: {period.replace('_to_', ' to ')}"
        else:
            file_path, period = await create_pdf_report_file(reports_data)
            filename = f"report_{period}.pdf"
            caption = f"📄 PDF Report: {period.replace('_to_', ' to ')}"

        with open(file_path, "rb") as file:
            file_bytes = file.read()

        await update.message.reply_document(
            document=file_bytes,
            filename=filename,
            caption=caption,
            read_timeout=120,
            write_timeout=120,
        )

        clear_mode(context)

        try:
            await status_message.delete()
        except Exception:
            pass

        await show_main_menu(update)

    except Exception as error:
        await update.message.reply_html(
            f"⚠️ <b>Error generating report:</b>\n{error}"
        )

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


async def handle_text_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main text router.

    Text input only works after user clicks a button.
    Attendance will only be recorded after clicking Submit Attendance.
    """
    mode = context.user_data.get("mode")

    if mode == "add_employee":
        await handle_add_employee_input(update, context)
        return

    if mode == "update_employee":
        await handle_update_employee_input(update, context)
        return

    if mode == "delete_employee":
        await handle_delete_employee_input(update, context)
        return

    if mode == "exchange":
        await handle_exchange_input(update, context)
        return

    if mode == "borrow":
        await handle_borrow_input(update, context)
        return

    if mode in ["report_pdf_date", "report_excel_date"]:
        await handle_report_date_input(update, context)
        return

    if mode == "attendance":
        await handle_attendance_message(update, context)

        # Important:
        # after one attendance input, stop waiting.
        # User must click Submit Attendance again for next report.
        clear_mode(context)

        await show_main_menu(update)
        return

    # No mode selected:
    # Do not record attendance automatically.
    await update.message.reply_text(
        "សូមចុចប៊ូតុង Submit Attendance មុនពេលផ្ញើវត្តមាន។\n"
        "Please click Submit Attendance before sending attendance."
    )

    await show_main_menu(update)