from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from app.services.attendance import build_attendance_template
from app.services.employees import get_employee_list_text
from app.database.repository import get_exchange_rate


def main_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📝 វត្តមាន / Attendance", callback_data="menu_attendance"),
                InlineKeyboardButton("👥 បុគ្គលិក / Employees", callback_data="menu_employees"),
            ],
            [
                InlineKeyboardButton("📊 របាយការណ៍ / Reports", callback_data="menu_reports"),
                InlineKeyboardButton("💵 អត្រាប្តូរប្រាក់ / Exchange", callback_data="menu_exchange"),
            ],
            [
                InlineKeyboardButton("⚙️ Admin", callback_data="menu_admin"),
                InlineKeyboardButton("❓ ជំនួយ / Help", callback_data="menu_help"),
            ],
        ]
    )


def back_to_main_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔙 ត្រឡប់ទៅម៉ឺនុយមេ / Back to Main Menu", callback_data="menu_main")
            ]
        ]
    )


def attendance_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📋 ទាញយកគំរូ / Get Template", callback_data="attendance_template"),
            ],
            [
                InlineKeyboardButton("✍️ របៀបបញ្ចូលវត្តមាន / Submit Guide", callback_data="attendance_guide"),
            ],
            [
                InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ / Back", callback_data="menu_main"),
            ],
        ]
    )


def employees_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📋 បញ្ជីបុគ្គលិក / Employee List", callback_data="employees_list"),
            ],
            [
                InlineKeyboardButton("➕ បន្ថែម / Add", callback_data="employees_add"),
                InlineKeyboardButton("✏️ កែឈ្មោះ / Update", callback_data="employees_update"),
            ],
            [
                InlineKeyboardButton("🗑️ លុប / Delete", callback_data="employees_delete"),
                InlineKeyboardButton("💸 ខ្ចីលុយ / Borrow", callback_data="employees_borrow"),
            ],
            [
                InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ / Back", callback_data="menu_main"),
            ],
        ]
    )


def reports_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("📄 PDF ទាំងអស់ / All PDF", callback_data="reports_pdf_all"),
                InlineKeyboardButton("📊 Excel ទាំងអស់ / All Excel", callback_data="reports_excel_all"),
            ],
            [
                InlineKeyboardButton("📅 PDF តាមថ្ងៃ / PDF by Date", callback_data="reports_pdf_date"),
                InlineKeyboardButton("📅 Excel តាមថ្ងៃ / Excel by Date", callback_data="reports_excel_date"),
            ],
            [
                InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ / Back", callback_data="menu_main"),
            ],
        ]
    )


def admin_menu_keyboard():
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton("🔄 Restart Count", callback_data="admin_restart"),
            ],
            [
                InlineKeyboardButton("🔙 ត្រឡប់ក្រោយ / Back", callback_data="menu_main"),
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

        await query.edit_message_text(
            "💵 <b>អត្រាប្តូរប្រាក់ / Exchange Rate</b>\n\n"
            f"Current exchange rate:\n"
            f"1$ = <b>{current_rate:,.0f}៛</b>\n\n"
            "To update, send:\n"
            "<code>/setexchange 4100</code>",
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

    if data == "attendance_guide":
        await query.edit_message_text(
            "✍️ <b>របៀបបញ្ចូលវត្តមាន / Submit Attendance Guide</b>\n\n"
            "Copy the template, edit the hours, then send it back to the bot.\n\n"
            "<code>"
            "ថ្ងៃទី: 26.06.26 (7:00am - 5:00pm)\n"
            "1. ប៉ែន ទិត្យ. [ 0 h ]\n"
            "2. អៀម អេន. [ 2 h ]\n"
            "</code>\n\n"
            "[ 0 h ] = normal 8 hours\n"
            "[ 2 h ] = 8 hours + 2 overtime hours",
            parse_mode="HTML",
            reply_markup=attendance_menu_keyboard(),
        )
        return

    if data == "employees_list":
        text = get_employee_list_text()
        await query.message.reply_html(text)
        return

    if data == "employees_add":
        await query.edit_message_text(
            "➕ <b>បន្ថែមបុគ្គលិក / Add Employees</b>\n\n"
            "Please send this format:\n\n"
            "<code>/addemployees\n"
            "ប៉ែន ទិត្យ ប 80000\n"
            "អៀម អេន ស 64000</code>\n\n"
            "ប = Male\n"
            "ស = Female",
            parse_mode="HTML",
            reply_markup=employees_menu_keyboard(),
        )
        return

    if data == "employees_update":
        await query.edit_message_text(
            "✏️ <b>កែឈ្មោះបុគ្គលិក / Update Employee</b>\n\n"
            "Please send this format:\n\n"
            "<code>/updateemployee ឈ្មោះចាស់ -> ឈ្មោះថ្មី</code>",
            parse_mode="HTML",
            reply_markup=employees_menu_keyboard(),
        )
        return

    if data == "employees_delete":
        await query.edit_message_text(
            "🗑️ <b>លុបបុគ្គលិក / Delete Employee</b>\n\n"
            "Please send this format:\n\n"
            "<code>/deleteemployees\n"
            "ប៉ែន ទិត្យ\n"
            "អៀម អេន</code>",
            parse_mode="HTML",
            reply_markup=employees_menu_keyboard(),
        )
        return

    if data == "employees_borrow":
        await query.edit_message_text(
            "💸 <b>ខ្ចីលុយ / Borrow Money</b>\n\n"
            "Please send this format:\n\n"
            "<code>/borrow ប៉ែន ទិត្យ 250000</code>",
            parse_mode="HTML",
            reply_markup=employees_menu_keyboard(),
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
        await query.edit_message_text(
            "📅 <b>PDF by Date</b>\n\n"
            "Please send one of these formats:\n\n"
            "<code>/report_pdf 26.06.26</code>\n"
            "<code>/report_pdf 20.06.26 26.06.26</code>",
            parse_mode="HTML",
            reply_markup=reports_menu_keyboard(),
        )
        return

    if data == "reports_excel_date":
        await query.edit_message_text(
            "📅 <b>Excel by Date</b>\n\n"
            "Please send one of these formats:\n\n"
            "<code>/report_excel 26.06.26</code>\n"
            "<code>/report_excel 20.06.26 26.06.26</code>",
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