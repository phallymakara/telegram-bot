from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.services.attendance import build_attendance_template
from app.services.employees import get_employee_list_text
from app.database.repository import get_exchange_rate


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
        "🏠 <b>ម៉ឺនុយមេ / Main Menu</b>\n\n"
        "សូមជ្រើសរើសមុខងារខាងក្រោម៖\n"
        "Please choose an option below:",
        reply_markup=main_menu_keyboard(),
    )


async def menu_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data

    if data == "menu_main":
        context.user_data.pop("mode", None)

        await query.edit_message_text(
            "🏠 <b>ម៉ឺនុយមេ / Main Menu</b>\n\n"
            "សូមជ្រើសរើសមុខងារខាងក្រោម៖\n"
            "Please choose an option below:",
            parse_mode="HTML",
            reply_markup=main_menu_keyboard(),
        )
        return

    if data == "menu_attendance":
        await query.edit_message_text(
            "📝 <b>វត្តមាន / Attendance Menu</b>\n\n"
            "សូមជ្រើសរើសមុខងារ៖\n"
            "Please choose an action:",
            parse_mode="HTML",
            reply_markup=attendance_menu_keyboard(),
        )
        return

    if data == "menu_employees":
        await query.edit_message_text(
            "👥 <b>គ្រប់គ្រងបុគ្គលិក / Employee Management</b>\n\n"
            "សូមជ្រើសរើសមុខងារ៖\n"
            "Please choose an action:",
            parse_mode="HTML",
            reply_markup=employees_menu_keyboard(),
        )
        return

    if data == "menu_reports":
        await query.edit_message_text(
            "📊 <b>របាយការណ៍ / Reports Menu</b>\n\n"
            "សូមជ្រើសរើសប្រភេទរបាយការណ៍៖\n"
            "Please choose report type:",
            parse_mode="HTML",
            reply_markup=reports_menu_keyboard(),
        )
        return

    if data == "menu_exchange":
        current_rate = get_exchange_rate()
        context.user_data["mode"] = "exchange"

        await query.edit_message_text(
            "💵 <b>អត្រាប្តូរប្រាក់ / Exchange Rate</b>\n\n"
            f"Current exchange rate:\n"
            f"1$ = <b>{current_rate:,.0f}៛</b>\n\n"
            "សូមផ្ញើអត្រាថ្មីដោយមិនចាំបាច់វាយ command។\n"
            "Please send the new exchange rate without command.\n\n"
            "Example:\n"
            "<code>4100</code>",
            parse_mode="HTML",
            reply_markup=back_to_main_keyboard(),
        )
        return

    if data == "menu_admin":
        await query.edit_message_text(
            "⚙️ <b>Admin Menu</b>\n\n"
            "Dangerous actions are placed here.",
            parse_mode="HTML",
            reply_markup=admin_menu_keyboard(),
        )
        return

    if data == "menu_help":
        await query.edit_message_text(
            "❓ <b>ជំនួយ / Help</b>\n\n"
            "Main usage:\n\n"
            "1. Add employees first\n"
            "2. Get attendance template\n"
            "3. Send daily attendance list\n"
            "4. Export PDF or Excel report\n\n"
            "You can use buttons or slash commands.",
            parse_mode="HTML",
            reply_markup=back_to_main_keyboard(),
        )
        return

    if data == "attendance_template":
        template_text = build_attendance_template()

        await query.message.reply_html(
            "📋 <b>គំរូវត្តមាន / Attendance Template</b>\n\n"
            f"<code>{template_text}</code>"
        )
        return

    if data == "attendance_submit":
        context.user_data["mode"] = "attendance"

        await query.edit_message_text(
            text=(
                "✅ <b>Submit Attendance</b>\n\n"
                "សូមផ្ញើបញ្ជីវត្តមាន។\n"
                "Please input the attendance list.\n\n"
                "<b>Example:</b>\n"
                "<code>"
                "ថ្ងៃទី: 26.06.26 (7:00am - 5:00pm)\n"
                "1. ប៉ែន ទិត្យ. [ 0 h ]\n"
                "2. អៀម អេន. [ 2 h ]"
                "</code>\n\n"
                "[ 0 h ] = normal 8 hours\n"
                "[ 2 h ] = 8 hours + 2 overtime hours"
            ),
            parse_mode="HTML",
            reply_markup=back_to_main_keyboard(),
        )
        return

    if data == "employees_list":
        text = get_employee_list_text()
        await query.message.reply_html(text)
        return

    if data == "employees_add":
        context.user_data["mode"] = "add_employee"

        await query.edit_message_text(
            "➕ <b>បន្ថែមបុគ្គលិក / Add Employees</b>\n\n"
            "សូមផ្ញើព័ត៌មានបុគ្គលិកដោយមិនចាំបាច់វាយ command។\n"
            "Please send employee information without command.\n\n"
            "Format:\n"
            "<code>"
            "ប៉ែន ទិត្យ ប 80000\n"
            "អៀម អេន ស 64000"
            "</code>\n\n"
            "ប = Male\n"
            "ស = Female",
            parse_mode="HTML",
            reply_markup=back_to_employee_keyboard(),
        )
        return

    if data == "employees_update":
        context.user_data["mode"] = "update_employee"

        await query.edit_message_text(
            "✏️ <b>កែឈ្មោះបុគ្គលិក / Update Employee</b>\n\n"
            "សូមផ្ញើឈ្មោះចាស់ និងឈ្មោះថ្មីដោយមិនចាំបាច់វាយ command។\n"
            "Please send old name and new name without command.\n\n"
            "Format:\n"
            "<code>ឈ្មោះចាស់ -> ឈ្មោះថ្មី</code>",
            parse_mode="HTML",
            reply_markup=back_to_employee_keyboard(),
        )
        return

    if data == "employees_delete":
        context.user_data["mode"] = "delete_employee"

        await query.edit_message_text(
            "🗑️ <b>លុបបុគ្គលិក / Delete Employee</b>\n\n"
            "សូមផ្ញើឈ្មោះបុគ្គលិកដែលចង់លុប ដោយមិនចាំបាច់វាយ command។\n"
            "Please send employee names without command.\n\n"
            "Format:\n"
            "<code>"
            "ប៉ែន ទិត្យ\n"
            "អៀម អេន"
            "</code>",
            parse_mode="HTML",
            reply_markup=back_to_employee_keyboard(),
        )
        return

    if data == "employees_borrow":
        context.user_data["mode"] = "borrow"

        await query.edit_message_text(
            "💸 Borrow Money \n\n"
            "បញ្ចូលឈ្មោះបុគ្គលិក និងចំនួនលុយដែលខ្ចី។\n"
            "Example:\n"
            "<code>ប៉ែន ទិត្យ 250000</code>",
            parse_mode="HTML",
            reply_markup=back_to_main_keyboard(),
        )
        return

    if data == "reports_pdf_all":
        await query.message.reply_html(
            "📄 To export all PDF reports, send:\n\n"
            "<code>/report_pdf</code>"
        )
        return

    if data == "reports_excel_all":
        await query.message.reply_html(
            "📊 To export all Excel reports, send:\n\n"
            "<code>/report_excel</code>"
        )
        return

    if data == "reports_pdf_date":
        context.user_data["mode"] = "report_pdf_date"

        await query.edit_message_text(
            "📅 <b>PDF by Date</b>\n\n"
            "សូមផ្ញើកាលបរិច្ឆេទដោយមិនចាំបាច់វាយ command។\n"
            "Please send date without command.\n\n"
            "One day:\n"
            "<code>26.06.26</code>\n\n"
            "Date range:\n"
            "<code>20.06.26 26.06.26</code>",
            parse_mode="HTML",
            reply_markup=reports_menu_keyboard(),
        )
        return

    if data == "reports_excel_date":
        context.user_data["mode"] = "report_excel_date"

        await query.edit_message_text(
            "📅 <b>Excel by Date</b>\n\n"
            "សូមផ្ញើកាលបរិច្ឆេទដោយមិនចាំបាច់វាយ command។\n"
            "Please send date without command.\n\n"
            "One day:\n"
            "<code>26.06.26</code>\n\n"
            "Date range:\n"
            "<code>20.06.26 26.06.26</code>",
            parse_mode="HTML",
            reply_markup=reports_menu_keyboard(),
        )
        return

    if data == "admin_restart":
        await query.message.reply_html(
            "🔄 To restart count safely, send:\n\n"
            "<code>/restartcount</code>"
        )
        return