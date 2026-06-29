from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.services.attendance import build_attendance_template
from app.services.employees import get_employee_list_text
from app.database.repository import get_exchange_rate

from app.services.reports import (
    create_excel_report_file,
    create_pdf_report_file,
    get_report_data,
)
from app.handlers.restart import restartcount_command


def main_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Attendance", callback_data="menu_attendance"),
                InlineKeyboardButton("Employees", callback_data="menu_employees"),
            ],
            [
                InlineKeyboardButton("Borrow", callback_data="employees_borrow"),
                InlineKeyboardButton("Reports", callback_data="menu_reports"),
            ],
            [
                InlineKeyboardButton("Exchange", callback_data="menu_exchange"),
                InlineKeyboardButton("Admin", callback_data="menu_admin"),
            ],
            [
                InlineKeyboardButton("Help", callback_data="menu_help"),
            ],
        ]
    )


def back_to_main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Back", callback_data="menu_main")
            ]
        ]
    )

def back_to_employee_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    "Back",
                    callback_data="menu_employees",
                )
            ]
        ]
    )


def attendance_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Get Template", callback_data="attendance_template"),
            ],
            [
                InlineKeyboardButton("Submit Attendance", callback_data="attendance_submit"),
            ],
            [
                InlineKeyboardButton("Back", callback_data="menu_main"),
            ],
        ]
    )


def employees_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Employee List", callback_data="employees_list"),
            ],
            [
                InlineKeyboardButton("Add Employee", callback_data="employees_add"),
                InlineKeyboardButton("Update Employee", callback_data="employees_update"),
            ],
            [
                InlineKeyboardButton("Delete Employee", callback_data="employees_delete"),
            ],
            [
                InlineKeyboardButton("Back", callback_data="menu_main"),
            ],
        ]
    )


def reports_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("PDF", callback_data="reports_pdf_all"),
                InlineKeyboardButton("Excel", callback_data="reports_excel_all"),
            ],
            [
                InlineKeyboardButton("PDF by Date", callback_data="reports_pdf_date"),
                InlineKeyboardButton("Excel by Date", callback_data="reports_excel_date"),
            ],
            [
                InlineKeyboardButton("Back", callback_data="menu_main"),
            ],
        ]
    )


def admin_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("Restart Count", callback_data="admin_restart"),
            ],
            [
                InlineKeyboardButton("Back", callback_data="menu_main"),
            ],
        ]
    )


async def menu_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_html(
        "Main Menu</b>\n\n"
        "choose option below:",
        reply_markup=main_menu_keyboard(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_main":
        context.user_data.pop("mode", None)

        await query.edit_message_text(
            "🏠 Main Menu\n\n"
            "choose option below:",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "menu_attendance":
        context.user_data.pop("mode", None)

        await query.edit_message_text(
            "Attendance Menu\n\n"
            "choose an action:",
            reply_markup=attendance_menu_keyboard(),
        )
        return

    if data == "menu_employees":
        context.user_data.pop("mode", None)

        await query.edit_message_text(
            "Employee Management\n\n"
            "choose an action:",
            reply_markup=employees_menu_keyboard(),
        )
        return

    if data == "menu_reports":
        context.user_data.pop("mode", None)

        await query.edit_message_text(
            "Reports Menu\n\n"
            "choose report type:",
            reply_markup=reports_menu_keyboard(),
        )
        return

    if data == "menu_exchange":
        current_rate = get_exchange_rate()
        context.user_data["mode"] = "exchange"

        await query.edit_message_text(
            "Exchange Rate\n\n"
            f"Current exchange rate:\n"
            f"1$ = {current_rate:,.0f}៛\n\n"
            "Please input the new exchange rate.\n\n"
            "Example:\n"
            "4100",
            reply_markup=back_to_main_keyboard(),
        )
        return

    if data == "menu_admin":
        context.user_data.pop("mode", None)

        await query.edit_message_text(
            "Admin Menu\n\n"
            "Dangerous actions here.",
            reply_markup=admin_menu_keyboard(),
        )
        return

    if data == "menu_help":
        context.user_data.pop("mode", None)

        await query.edit_message_text(
            "❓ Help\n\n"
            "1. Add employees first\n"
            "2. Click Submit Attendance before sending attendance\n"
            "3. Send daily attendance list\n"
            "4. Export PDF or Excel report\n\n"
            "Use the buttons to operate the bot.",
            reply_markup=back_to_main_keyboard(),
        )
        return

    if data == "attendance_template":
        template_text = build_attendance_template()

        await query.message.reply_html(
            "<b>Attendance Template</b>\n\n"
            f"<code>{template_text}</code>"
        )
        return

    if data == "attendance_submit":
        context.user_data["mode"] = "attendance"

        await query.edit_message_text(
            text=(
                "Please input the attendance list.\n\n"
                "<b>Example:</b>\n"
                "<code>"
                "ថ្ងៃទី: 26.06.26 (7:00am - 5:00pm)\n"
                "1. ប៉ែន ទិត្យ. [ 0 h - Villa ]\n"
                "2. អៀម អេន. [ 2 h - 11Condo ]"
                "</code>\n\n"
            ),
            reply_markup=back_to_main_keyboard(),
            parse_mode="HTML",
        )
        return

    if data == "employees_list":
        text = get_employee_list_text()
        await query.message.reply_html(text)
        return

    if data == "employees_add":
        context.user_data["mode"] = "add_employee"

        await query.edit_message_text(
            "<b>Add Employees</b>\n\n"
            "Format:\n"
            "<code>"
            "ប៉ែន ទិត្យ ប 80000\n"
            "អៀម អេន ស 64000"
            "</code>\n\n",
            reply_markup=back_to_employee_keyboard(),
            parse_mode="HTML",
        )
        return

    if data == "employees_update":
        context.user_data["mode"] = "update_employee"

        await query.edit_message_text(
            "<b>Update Employee</b>\n\n"
            "Format:\n"
            "<code>ឈ្មោះចាស់ -> ឈ្មោះថ្មី</code>",
            reply_markup=back_to_employee_keyboard(),
            parse_mode="HTML",
        )
        return

    if data == "employees_delete":
        context.user_data["mode"] = "delete_employee"

        await query.edit_message_text(
            "<b>Delete Employee</b>\n\n"
            "Format:\n"
            "<code>"
            "ប៉ែន ទិត្យ\n"
            "អៀម អេន"
            "</code>",
            reply_markup=back_to_employee_keyboard(),
            parse_mode="HTML",
        )
        return

    if data == "employees_borrow":
        context.user_data["mode"] = "borrow"

        await query.edit_message_text(
            "Borrow Money \n\n"
            "បញ្ចូលឈ្មោះបុគ្គលិក និងចំនួនលុយដែលខ្ចី។\n"
            "Example:\n"
            "<code>ប៉ែន ទិត្យ 250000</code>",
            reply_markup=back_to_main_keyboard(),
            parse_mode="HTML",
        )
        return

    if data == "reports_pdf_all":
        await query.edit_message_text(
            "កំពុងបង្កើត PDF Report...\n"
        )

        await send_report_from_button(query, context, "pdf")
        return

    if data == "reports_excel_all":
        await query.edit_message_text(
            "កំពុងបង្កើត Excel Report...\n"
        )

        await send_report_from_button(query, context, "excel")
        return

    if data == "reports_pdf_date":
        context.user_data["mode"] = "report_pdf_date"

        await query.edit_message_text(
            "<b>PDF by Date</b>\n\n"
            "One day:\n"
            "<code>26.06.26</code>\n\n"
            "Date range:\n"
            "<code>20.06.26 26.06.26</code>",
            reply_markup=reports_menu_keyboard(),
            parse_mode="HTML",
        )
        return

    if data == "reports_excel_date":
        context.user_data["mode"] = "report_excel_date"

        await query.edit_message_text(
            "<b>Excel by Date</b>\n\n"
            "One day:\n"
            "<code>26.06.26</code>\n\n"
            "Date range:\n"
            "<code>20.06.26 26.06.26</code>",
            reply_markup=reports_menu_keyboard(),
            parse_mode="HTML",
        )
        return

    if data == "admin_restart":
        fake_update = Update(
            update.update_id,
            message=query.message,
        )

        await restartcount_command(fake_update, context)
        return


async def send_report_from_button(query, context, report_type: str):
    reports_data = await get_report_data(None, None)

    if not reports_data:
        await query.message.reply_text(
            "No report data found."
        )
        return

    status_message = await query.message.reply_text(
        "⏳ កំពុងបង្កើតរបាយការណ៍...\n"
        "Generating report..."
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

        await query.message.reply_document(
            document=file_bytes,
            filename=filename,
            caption=caption,
            read_timeout=120,
            write_timeout=120,
        )

        try:
            await status_message.delete()
        except Exception:
            pass

        await query.message.reply_text(
            "Main Menu\n\n"
            "choose the next action:",
            reply_markup=main_menu_keyboard(),
        )

    except Exception as error:
        await query.message.reply_text(
            f"⚠️ Error generating report:\n{error}"
        )

    finally:
        if file_path:
            import os

            if os.path.exists(file_path):
                try:
                    os.remove(file_path)
                except Exception:
                    pass