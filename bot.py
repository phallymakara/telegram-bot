import os
import logging
import asyncio
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
from telegram import Update, BotCommand, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackQueryHandler
)

from database import (
    init_db,
    add_employee,
    update_employee_name,
    delete_employee,
    get_all_employees,
    get_employee_rate,
    save_attendance_report,
    get_accumulated_totals,
    get_reports_by_dates,
    parse_date,
    get_exchange_rate,
    set_exchange_rate,
    restart_attendance_count
)
from parser import parse_report_text_by_days

# Try importing report generation libraries
try:
    from report_generator import generate_excel_report, generate_pdf_report, get_report_period_string
    REPORT_LIBS_AVAILABLE = True
except ImportError as _import_err:
    REPORT_LIBS_AVAILABLE = False
    print(f"[WARNING] Report libs not available: {_import_err}")

# Load environment variables
load_dotenv()

# Enable logging
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# Cambodia Timezone (UTC+7)
tz_kh = timezone(timedelta(hours=7))

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "👋 <b>សូមស្វាគមន៍មកកាន់ Telegram Bot គណនាវត្តមាន និងប្រាក់ឈ្នួល (Hourly Rate)!</b>\n"
        "<b>Welcome to Daily Attendance & Salary Bot!</b>\n\n"
        "ផ្ញើបញ្ជីឈ្មោះបុគ្គលិកប្រចាំថ្ងៃមកខ្ញុំ ដើម្បីគណនាម៉ោងការងារ និងប្រាក់ឈ្នួលសរុប។\n"
        "Send me your daily worker list to calculate working hours and salaries automatically.\n\n"
        "ℹ️ ផ្ញើ /help ដើម្បីមើលរបៀបប្រើប្រាស់ និងការគ្រប់គ្រងបុគ្គលិក។\n"
        "ℹ️ Send /help to see usage and employee management commands."
    )
    await update.message.reply_html(welcome_text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = (
        "📖 <b>របៀបប្រើប្រាស់ / How to Use:</b>\n\n"
        "👥 <b>ការគ្រប់គ្រងឈ្មោះបុគ្គលិក / Employee Management:</b>\n"
        "• /addemployee &lt;ឈ្មោះ&gt; &lt;តម្លៃថ្ងៃ&gt; - ចុះឈ្មោះ ឬកែសម្រួលតម្លៃថ្ងៃបុគ្គលិក\n"
        "  (ឧទា. <code>/addemployee ប៉ែន ទិត្យ 80000</code>)\n"
        "• /addemployees - ចុះឈ្មោះបុគ្គលិកច្រើននាក់ក្នុងពេលតែមួយ (បំបែកដោយចុះបន្ទាត់)\n"
        "  (ឧទា. <code>/addemployees\n"
        "  ប៉ែន ទិត្យ 80000\n"
        "  អៀម អេន 64000</code>)\n"
        "• /updateemployee &lt;ឈ្មោះចាស់&gt; -&gt; &lt;ឈ្មោះថ្មី&gt; - កែប្រែឈ្មោះបុគ្គលិក\n"
        "  (ឧទា. <code>/updateemployee ប៉ែន ទិត្យ -&gt; ប៉ែន ទិត្យថ្មី</code>)\n"
        "• /deleteemployee &lt;ឈ្មោះ&gt; - លុបឈ្មោះបុគ្គលិកចេញពីប្រព័ន្ធ\n"
        "  (ឧទា. <code>/deleteemployee ប៉ែន ទិត្យ</code>)\n"
        "• /deleteemployees - លុបឈ្មោះបុគ្គលិកច្រើននាក់ក្នុងពេលតែមួយ (បំបែកដោយចុះបន្ទាត់)\n"
        "  (ឧទា. <code>/deleteemployees\n"
        "  ប៉ែន ទិត្យ\n"
        "  អៀម អេន</code>)\n"
        "• /employees - បង្ហាញបញ្ជីឈ្មោះបុគ្គលិក និងតម្លៃថ្ងៃ\n"
        "• /setexchange &lt;អត្រា&gt; - កំណត់អត្រាប្តូរប្រាក់ (រៀល/USD)\n"
        "  (ឧទា. <code>/setexchange 4100</code>)\n"
        "• /restartcount - កំណត់ការរាប់សារជាថ្មី (លុបវត្តមាន និងរបាយការណ៍ទាំងអស់) / Restart attendance count (delete all attendance records and reports)\n\n"
        "📥 <b>ទាញយករបាយការណ៍ / Download Reports:</b>\n"
        "• /report_pdf [ថ្ងៃចាប់ផ្ដើម] [ថ្ងៃបញ្ចប់] - ទាញយករបាយការណ៍ជា PDF\n"
        "  (ឧទា. <code>/report_pdf 11.06.26 16.06.26</code> ឬ <code>/report_pdf 16.06.26</code> ឬ <code>/report_pdf</code> សម្រាប់ទាញយកទាញៀសង)\n"
        "• /report_excel [ថ្ងៃចាប់ផ្ដើម] [ថ្ងៃបញ្ចប់] - ទាញយករបាយការណ៍ជា Excel\n"
        "  (ឧទា. <code>/report_excel 11.06.26 16.06.26</code>)\n\n"
        "📋 <b>ទម្រង់ផ្ញើរបាយការណ៍ / Sending Attendance Reports:</b>\n"
        "សូមចម្លង និងកែសម្រួលទិន្នន័យខាងក្រោមរួចផ្ញើមកកាន់ Bot:\n"
        "Please copy and edit the data format below, then send it to the Bot:\n\n"
        "<code>"
        "ថ្ងៃទី: 11.06.26 (7:00am - 5:00pm)\n"
        "1. ប៉ែន ទិត្យ.   8 h\n"
        "2. អៀម អេន.     8.9 h\n"
        "3. ធិន        8.3 h\n"
        "4. សួង សុង 8h\n"
        "5. គុន ឡុន   2.5 h\n"
        "6. ម៉ាច សិន 6 h\n"
        "7. សេង សុីណាត 7 h\n"
        "8. ម៉ៅ ម៉ាច 9.1 h\n"
        "9. ផូ បុផា 8 h\n"
        "</code>\n\n"
        "💡 <b>ចំណាំ / Rules:</b>\n"
        "• បញ្ជីនីមួយៗត្រូវផ្តើមដោយលេខលំដាប់ (ឧទា. <code>1.</code>)\n"
        "• ចំនួនម៉ោងធ្វើការត្រូវដាក់នៅចុងបញ្ចប់នៃបន្ទាត់ (ឧទា. <code>8 h</code> ឬ <code>8.9 h</code> ឬ <code>8h</code>)\n"
        "• តម្លៃថ្ងៃរបស់បុគ្គលិកដែលមិនទាន់ចុះឈ្មោះគឺ 0៛ (នឹងបង្ហាញសញ្ញាព្រមាន ⚠️)\n"
        "• ប្រាក់ឈ្នួល = (ម៉ោងធ្វើការសរុប ÷ 8) × តម្លៃថ្ងៃ"
    )
    await update.message.reply_html(help_text)

async def addemployee_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if len(args) < 2:
        await update.message.reply_html(
            "⚠️ Usage: <code>/addemployee &lt;name&gt; &lt;daily_rate&gt;</code>\n"
            "Example: <code>/addemployee ប៉ែន ទិត្យ 80000</code>"
        )
        return

    try:
        daily_rate = float(args[-1])
    except ValueError:
        await update.message.reply_html("⚠️ Error: daily_rate must be a number.")
        return

    name = " ".join(args[:-1]).strip()
    add_employee(name, daily_rate)
    await update.message.reply_html(
        f"✅ Employee <b>{name}</b> added/updated with daily rate <b>{daily_rate:,.0f}៛/day</b>."
    )

async def addemployees_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    command_prefix = "/addemployees"
    if not message_text.startswith(command_prefix):
        return

    content = message_text[len(command_prefix):].strip()
    if not content:
        await update.message.reply_html(
            "⚠️ Usage:\n"
            "<code>/addemployees\n"
            "ប៉ែន ទិត្យ 80000\n"
            "អៀម អេន 64000</code>"
        )
        return

    lines = content.split("\n")
    success_list = []
    error_list = []

    for line in lines:
        cleaned = line.strip()
        if not cleaned:
            continue
        
        parts = cleaned.split()
        if len(parts) < 2:
            error_list.append(f"• <code>{cleaned}</code> (Invalid format)")
            continue

        try:
            rate = float(parts[-1])
            name = " ".join(parts[:-1]).strip()
            add_employee(name, rate)
            success_list.append(f"• <b>{name}</b>: {rate:,.0f}៛/day")
        except ValueError:
            error_list.append(f"• <code>{cleaned}</code> (Rate must be a number)")

    response_text = ""
    if success_list:
        response_text += "✅ <b>Added/Updated Employees:</b>\n" + "\n".join(success_list)
    if error_list:
        if response_text:
            response_text += "\n\n"
        response_text += "⚠️ <b>Errors:</b>\n" + "\n".join(error_list)

    if not response_text:
        response_text = "⚠️ No valid employees parsed."

    await update.message.reply_html(response_text)

async def updateemployee_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Parse update.message.text to handle spaces and arrows
    message_text = update.message.text
    command_prefix = "/updateemployee"
    if not message_text.startswith(command_prefix):
        return

    command_args = message_text[len(command_prefix):].strip()
    if "->" not in command_args:
        await update.message.reply_html(
            "⚠️ Usage: <code>/updateemployee &lt;old_name&gt; -&gt; &lt;new_name&gt;</code>\n"
            "Example: <code>/updateemployee ប៉ែន ទិត្យ -&gt; ប៉ែន ទិត្យថ្មី</code>"
        )
        return

    parts = command_args.split("->", 1)
    old_name = parts[0].strip()
    new_name = parts[1].strip()

    if not old_name or not new_name:
        await update.message.reply_html("⚠️ Error: Old name and new name cannot be empty.")
        return

    success = update_employee_name(old_name, new_name)
    if success:
        await update.message.reply_html(
            f"✅ Employee <b>{old_name}</b> renamed to <b>{new_name}</b>."
        )
    else:
        await update.message.reply_html(
            f"⚠️ Error: Employee <b>{old_name}</b> not found, or name <b>{new_name}</b> is already registered."
        )

async def deleteemployee_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        await update.message.reply_html(
            "⚠️ Usage: <code>/deleteemployee &lt;name&gt;</code>\n"
            "Example: <code>/deleteemployee ប៉ែន ទិត្យ</code>"
        )
        return

    name = " ".join(args).strip()
    success = delete_employee(name)
    if success:
        await update.message.reply_html(f"✅ Employee <b>{name}</b> deleted successfully.")
    else:
        await update.message.reply_html(f"⚠️ Error: Employee <b>{name}</b> not found.")

async def deleteemployees_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text
    command_prefix = "/deleteemployees"
    if not message_text.startswith(command_prefix):
        return

    content = message_text[len(command_prefix):].strip()
    if not content:
        await update.message.reply_html(
            "⚠️ Usage:\n"
            "<code>/deleteemployees\n"
            "ប៉ែន ទិត្យ\n"
            "អៀម អេន</code>"
        )
        return

    lines = content.split("\n")
    success_list = []
    error_list = []

    for line in lines:
        name = line.strip()
        if not name:
            continue
        
        success = delete_employee(name)
        if success:
            success_list.append(f"• <b>{name}</b>")
        else:
            error_list.append(f"• <code>{name}</code> (Not found)")

    response_text = ""
    if success_list:
        response_text += "✅ <b>Deleted Employees & History:</b>\n" + "\n".join(success_list)
    if error_list:
        if response_text:
            response_text += "\n\n"
        response_text += "⚠️ <b>Errors / Not Found:</b>\n" + "\n".join(error_list)

    if not response_text:
        response_text = "⚠️ No valid employee names parsed."

    await update.message.reply_html(response_text)

async def employees_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    employees = get_all_employees()
    if not employees:
        await update.message.reply_html(
            "ℹ️ No employees registered yet. Register employees using <code>/addemployee &lt;name&gt; &lt;daily_rate&gt;</code>."
        )
        return

    exchange_rate = get_exchange_rate()
    text = "📋 <b>បញ្ជីឈ្មោះបុគ្គលិក និងតម្លៃថ្ងៃ / Registered Employees & Daily Rates:</b>\n"
    text += f"💵 <i>អត្រាប្តូរប្រាក់បច្ចុប្បន្ន / Current Exchange Rate: 1$ = {exchange_rate:,.0f}៛</i>\n\n"
    for idx, (name, rate) in enumerate(employees.items(), 1):
        text += f"{idx}. <b>{name}</b>: {rate:,.0f}៛/day\n"
    await update.message.reply_html(text)

def format_usd(val: float) -> str:
    if val == int(val):
        return f"{int(val)}$"
    s = f"{val:.2f}"
    if s.endswith('0'):
        s = s[:-1]
    return f"{s}$"

def format_riel(val: float) -> str:
    riel = int(round(val))
    if riel >= 1000 and riel % 1000 == 0:
        return f"{riel // 1000}k"
    return f"{riel}"

def get_num_emoji(idx: int) -> str:
    emojis = {
        1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣", 5: "5️⃣",
        6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣", 10: "🔟"
    }
    if idx in emojis:
        return emojis[idx]
    res = ""
    for char in str(idx):
        res += char + "️⃣"
    return res

def parse_header_date_time(header: str):
    import re
    # Matches "ថ្ងៃទី: 20.06.26 (07:00 AM - 05:00 PM)" or similar
    # Khmer text "ថ្ងៃទី" or "ងៃទី" followed by optional colon and spaces
    match = re.search(r'(?:ថ្ងៃទី|ងៃទី|កាលបរិច្ឆេទ)?\s*[:៖]?\s*([\d\.\-\/]+)\s*(?:\((.*?)\))?', header, re.IGNORECASE)
    if match:
        date_part = match.group(1).strip()
        time_part = match.group(2).strip() if match.group(2) else None
        return date_part, time_part
    return header.strip(), None

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text
    if not text:
        return

    day_blocks = parse_report_text_by_days(text)
    if not day_blocks:
        if update.message.chat.type == "private":
            reply_text = (
                "<b>សុំទោស ខ្ញុំមិនយល់ពីទម្រង់ទិន្នន័យនេះទេ។</b>\n"
                "Sorry, I couldn't parse the format of your message.\n\n"
                "សូមផ្ញើជាបញ្ជីវត្តមាន ឬវាយបញ្ជា /help ដើម្បីមើលឧទាហរណ៍។\n"
                "Please send the attendance list or type /help for details."
            )
            await update.message.reply_html(reply_text)
        return

    current_date = datetime.now(tz_kh).strftime("%d-%b-%Y")
    exchange_rate = get_exchange_rate()
    default_hours_per_day = 8.0

    if len(day_blocks) == 1:
        # Single Day Block
        parsed_workers = day_blocks[0]['workers']
        day_header = day_blocks[0]['header']
        total_staff = len(parsed_workers)
        details_today_lines = []
        details_total_lines = []

        # Save to database
        db_status = ""
        try:
            report_id = save_attendance_report(current_date, day_header, parsed_workers)
            db_status = (
                f"✅ រក្សាទុកទិន្នន័យរួចរាល់\n"
                f"🆔 Report ID: #{report_id}"
            )
        except Exception as e:
            logger.error(f"Error saving report to database: {e}")

        # Fetch cumulative running totals from database
        running_totals = get_accumulated_totals()

        for idx, w in enumerate(parsed_workers, 1):
            name = w['name']
            hours = w['hours']
            note = w['note']

            daily_rate = get_employee_rate(name)
            is_unregistered = daily_rate is None
            rate = daily_rate if daily_rate is not None else 0.0

            salary = (hours / 8.0) * rate

            accum_hours = running_totals.get(name, {}).get('hours', hours)
            accum_salary = running_totals.get(name, {}).get('salary', salary)

            salary_usd = salary / exchange_rate
            accum_salary_usd = accum_salary / exchange_rate

            ot_hours = max(0.0, hours - 8.0)
            ot_salary = ot_hours * (rate / 8.0)
            ot_salary_usd = ot_salary / exchange_rate

            accum_ot_hours = running_totals.get(name, {}).get('ot_hours', ot_hours)
            accum_ot_salary = running_totals.get(name, {}).get('ot_salary', ot_salary)
            accum_ot_salary_usd = accum_ot_salary / exchange_rate

            # Build lines for today
            label_suffix = ""
            if is_unregistered:
                label_suffix += " (Unregistered)"
            if note:
                label_suffix += f" ({note})"

            num_emoji = get_num_emoji(idx)
            today_worker_block = (
                f"{num_emoji} <b>{name}</b>{label_suffix}\n"
                f"• ម៉ោងធ្វើការ : {hours:.1f}h\n"
                f"• ម៉ោងថែម    : {ot_hours:.1f}h\n"
                f"• ប្រាក់ថែម   : {int(round(ot_salary)):,}៛ (${ot_salary_usd:.2f})\n"
                f"• សរុបថ្ងៃនេះ : {int(round(salary)):,}៛ (${salary_usd:.2f})"
            )
            details_today_lines.append(today_worker_block)

            # Build lines for total
            total_label_suffix = ""
            if is_unregistered:
                total_label_suffix += " (Unregistered)"

            total_worker_block = (
                f"{num_emoji} <b>{name}</b>{total_label_suffix}\n"
                f"• ម៉ោងសរុប : {accum_hours:.1f}h\n"
                f"• ម៉ោងថែម : {accum_ot_hours:.1f}h\n"
                f"• ប្រាក់សរុប : {int(round(accum_salary)):,}៛ (${accum_salary_usd:.2f})"
            )
            details_total_lines.append(total_worker_block)

        # Parse header
        date_part, time_part = parse_header_date_time(day_header)
        report_header = "📋 <b>របាយការណ៍វត្តមាន និងប្រាក់ឈ្នួល</b>\n\n"
        report_header += f"ថ្ងៃទី: {date_part}\n"
        if time_part:
            report_header += f"ម៉ោងការងារ: {time_part}\n"

        separator = "━━━━━━━━━━━━━━━━━━━━"

        today_section = (
            f"\n{separator}\n"
            f"<b>ការងារថ្ងៃនេះ</b>\n"
            f"{separator}\n"
            + "\n\n".join(details_today_lines) + "\n"
        )

        total_section = (
            f"\n{separator}\n"
            f"<b>ប្រាក់សរុប</b>\n"
            f"{separator}\n"
            + "\n\n".join(details_total_lines) + "\n"
        )

        # Totals for all employees in running totals database
        total_hours_day_one = sum(info['hours'] for info in running_totals.values())
        total_salary_day_one_riel = sum(info['salary'] for info in running_totals.values())
        total_salary_day_one_usd = total_salary_day_one_riel / exchange_rate

        footer_section = (
            f"\n{separator}\n"
            f"<b>សរុប</b>\n"
            f"{separator}\n"
            f"👥 វត្តមានសរុប      : {total_staff} នាក់\n"
            f"⏱️ ម៉ោងការងារសរុប  : {total_hours_day_one:.1f}h\n"
            f"💰 ប្រាក់ឈ្នួលសរុប : ${total_salary_day_one_usd:.2f}\n"
            f"🇰🇭 ស្មើនឹង        : {int(round(total_salary_day_one_riel)):,}៛"
        )

        if db_status:
            footer_section += f"\n\n{db_status}"

        full_report = report_header + today_section + total_section + footer_section
        await update.message.reply_html(full_report)

    else:
        # Multi-Day Blocks
        grand_total_hours = 0.0
        grand_total_salary = 0.0
        daily_breakdown_lines = []
        worker_totals = {}
        saved_ids = []

        for block in day_blocks:
            day_header = block['header']
            day_workers = block['workers']

            # Save each day block to DB
            try:
                report_id = save_attendance_report(current_date, day_header, day_workers)
                saved_ids.append(report_id)
            except Exception as e:
                logger.error(f"Error saving report block to database: {e}")

            day_hours = 0.0
            day_salary = 0.0
            day_staff_count = len(day_workers)

            for w in day_workers:
                name = w['name']
                hours = w['hours']
                note = w['note']

                daily_rate = get_employee_rate(name)
                is_unregistered = daily_rate is None
                rate = daily_rate if daily_rate is not None else 0.0

                salary = (hours / 8.0) * rate

                day_hours += hours
                day_salary += salary

                ot_hours = max(0.0, hours - 8.0)
                ot_salary = ot_hours * (rate / 8.0)

                if name not in worker_totals:
                    worker_totals[name] = {
                        'days': 0.0,
                        'hours': 0.0,
                        'salary': 0.0,
                        'ot_hours': 0.0,
                        'ot_salary': 0.0,
                        'notes': set(),
                        'unregistered': is_unregistered,
                        'rate': rate
                    }

                worker_totals[name]['days'] += hours / default_hours_per_day
                worker_totals[name]['hours'] += hours
                worker_totals[name]['salary'] += salary
                worker_totals[name]['ot_hours'] += ot_hours
                worker_totals[name]['ot_salary'] += ot_salary
                if note:
                    worker_totals[name]['notes'].add(note)

            grand_total_hours += day_hours
            grand_total_salary += day_salary

            day_salary_usd = day_salary / exchange_rate
            daily_breakdown_lines.append(
                f"• <b>{day_header}</b>: {day_staff_count} នាក់/workers | <b>{day_hours:.1f}h</b> | <b>${day_salary_usd:.2f} ({int(round(day_salary)):,}៛)</b>"
            )

        # Fetch cumulative running totals from database
        running_totals = get_accumulated_totals()

        details_report_lines = []
        details_total_lines = []
        for i, (name, stats) in enumerate(worker_totals.items(), 1):
            days_val = stats['days']
            days_str = f"{days_val:.2f}" if days_val % 1 != 0 else f"{int(days_val)}"

            accum_hours = running_totals.get(name, {}).get('hours', 0.0)
            accum_salary = running_totals.get(name, {}).get('salary', 0.0)
            accum_ot_hours = running_totals.get(name, {}).get('ot_hours', 0.0)
            accum_ot_salary = running_totals.get(name, {}).get('ot_salary', 0.0)

            stats_salary_usd = stats['salary'] / exchange_rate
            accum_salary_usd = accum_salary / exchange_rate
            stats_ot_salary_usd = stats['ot_salary'] / exchange_rate
            accum_ot_salary_usd = accum_ot_salary / exchange_rate

            label_suffix = ""
            if stats['unregistered']:
                label_suffix += " (Unregistered)"
            if stats['notes']:
                notes_str = ", ".join(sorted(list(stats['notes'])))
                label_suffix += f" ({notes_str})"

            num_emoji = get_num_emoji(i)
            # Today's report block details line
            report_str = (
                f"{num_emoji} <b>{name}</b>{label_suffix}\n"
                f"• ចំនួនថ្ងៃ   : {days_str} ថ្ងៃ\n"
                f"• ម៉ោងសរុប  : {stats['hours']:.1f}h\n"
                f"• ម៉ោងថែម   : {stats['ot_hours']:.1f}h\n"
                f"• ប្រាក់ថែម  : {int(round(stats['ot_salary'])):,}៛ (${stats_ot_salary_usd:.2f})\n"
                f"• ប្រាក់សរុប : {int(round(stats['salary'])):,}៛ (${stats_salary_usd:.2f})"
            )
            details_report_lines.append(report_str)

            # Total line
            total_label_suffix = ""
            if stats['unregistered']:
                total_label_suffix += " (Unregistered)"

            total_str = (
                f"{num_emoji} <b>{name}</b>{total_label_suffix}\n"
                f"• ម៉ោងសរុប : {accum_hours:.1f}h\n"
                f"• ម៉ោងថែម : {accum_ot_hours:.1f}h\n"
                f"• ប្រាក់សរុប : {int(round(accum_salary)):,}៛ (${accum_salary_usd:.2f})"
            )
            details_total_lines.append(total_str)

        total_hours_day_one = sum(info['hours'] for info in running_totals.values())
        total_salary_day_one_riel = sum(info['salary'] for info in running_totals.values())
        total_salary_day_one_usd = total_salary_day_one_riel / exchange_rate

        report_header = (
            f"📋 <b>របាយការណ៍ការងារច្រើនថ្ងៃ / Multi-day Work Report</b>\n"
            f"កាលបរិច្ឆេទគណនា: {current_date}\n"
        )

        separator = "━━━━━━━━━━━━━━━━━━━━"

        breakdown_section = (
            f"\n{separator}\n"
            f"<b>បំណែងចែកតាមថ្ងៃ / Daily Breakdown</b>\n"
            f"{separator}\n"
            + "\n".join(daily_breakdown_lines) + "\n"
        )

        today_section = (
            f"\n{separator}\n"
            f"<b>ចំនួនម៉ោង និង ប្រាក់ ធ្វើការក្នុងរបាយការណ៍នេះ</b>\n"
            f"{separator}\n"
            + "\n\n".join(details_report_lines) + "\n"
        )

        total_section = (
            f"\n{separator}\n"
            f"<b>ចំនួនម៉ោង និង ប្រាក់សរុប</b>\n"
            f"{separator}\n"
            + "\n\n".join(details_total_lines) + "\n"
        )

        footer_section = (
            f"\n{separator}\n"
            f"<b>សរុប</b>\n"
            f"{separator}\n"
            f"👥 បុគ្គលិកសរុប    : {len(worker_totals)} នាក់\n"
            f"📅 ចំនួនថ្ងៃសរុប   : {len(day_blocks)} ថ្ងៃ\n"
            f"⏱️ ម៉ោងការងារសរុប : {total_hours_day_one:.1f}h\n"
            f"💰 ប្រាក់ឈ្នួលសរុប : ${total_salary_day_one_usd:.2f}\n"
            f"🇰🇭 ស្មើនឹង        : {int(round(total_salary_day_one_riel)):,}៛"
        )

        db_status = ""
        if saved_ids:
            ids_str = ", ".join(map(str, saved_ids))
            db_status = (
                f"✅ រក្សាទុកទិន្នន័យរួចរាល់\n"
                f"🆔 Report IDs: #{ids_str}"
            )
            footer_section += f"\n\n{db_status}"

        full_report = report_header + breakdown_section + today_section + total_section + footer_section
        await update.message.reply_html(full_report)

async def report_pdf_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not REPORT_LIBS_AVAILABLE:
        await update.message.reply_html(
            "⚠️ <b>មិនអាចបង្កើត បញ្ហា openpyxl និង reportlab មិនត្រូវបានតិតក័លទេ៴</b>\n"
            "Please install required packages first:\n"
            "<code>pip install openpyxl reportlab</code>"
        )
        return

    args = context.args
    start_date = None
    end_date = None

    if len(args) == 1:
        if not parse_date(args[0]):
            await update.message.reply_html(
                "⚠️ <b>ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ!</b>\n"
                "Invalid date format. Please use DD.MM.YY\n"
                "(ឧទា. <code>/report_pdf 16.06.26</code>)"
            )
            return
        start_date = args[0]
        end_date = args[0]
    elif len(args) >= 2:
        if not parse_date(args[0]) or not parse_date(args[1]):
            await update.message.reply_html(
                "⚠️ <b>ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ!</b>\n"
                "Invalid date format. Please use DD.MM.YY\n"
                "(ឧទា. <code>/report_pdf 11.06.26 16.06.26</code>)"
            )
            return
        start_date = args[0]
        end_date = args[1]

    reports_data = await asyncio.to_thread(get_reports_by_dates, start_date, end_date)
    if not reports_data:
        await update.message.reply_html(
            "⚠️ <b>មិនមានទិន្នន័យសម្រាប់កាលបរិច្ឆេទនេះទេ៴</b>\n"
            "No data found for the specified period."
        )
        return

    period_str = get_report_period_string(reports_data)
    os.makedirs("tmp", exist_ok=True)
    file_path = os.path.join("tmp", f"report_{period_str}.pdf")
    status_msg = await update.message.reply_html("⏳ <b>កំពុងបង្កើតរបាយការណ៍ PDF... / Generating PDF report...</b>")
    try:
        exchange_rate = await asyncio.to_thread(get_exchange_rate)
        await generate_pdf_report(reports_data, period_str, file_path, exchange_rate)
        with open(file_path, "rb") as f:
            pdf_bytes = f.read()
        await update.message.reply_document(
            document=pdf_bytes,
            filename=f"report_{period_str}.pdf",
            caption=f"របាយការណ៍ PDF សម្រាប់ថ្ងៃទី / PDF Report for: {period_str.replace('_to_', ' ដល់ ')}",
            read_timeout=120,
            write_timeout=120
        )
        try:
            await status_msg.delete()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        try:
            await status_msg.delete()
        except Exception:
            pass
        await update.message.reply_html(
            f"⚠️ <b>មានបញ្ហាក្នុងការបង្កើតឯកសារ PDF!</b>\nError: {e}"
        )
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

async def report_excel_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not REPORT_LIBS_AVAILABLE:
        await update.message.reply_html(
            "⚠️ <b>មិនអាចបង្កើត បញ្ហា openpyxl និង reportlab មិនត្រូវបានតិតក័លទេ៴</b>\n"
            "Please install required packages first:\n"
            "<code>pip install openpyxl reportlab</code>"
        )
        return

    args = context.args
    start_date = None
    end_date = None

    if len(args) == 1:
        if not parse_date(args[0]):
            await update.message.reply_html(
                "⚠️ <b>ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ!</b>\n"
                "Invalid date format. Please use DD.MM.YY\n"
                "(ឧទា. <code>/report_excel 16.06.26</code>)"
            )
            return
        start_date = args[0]
        end_date = args[0]
    elif len(args) >= 2:
        if not parse_date(args[0]) or not parse_date(args[1]):
            await update.message.reply_html(
                "⚠️ <b>ទម្រង់កាលបរិច្ឆេទមិនត្រឹមត្រូវ!</b>\n"
                "Invalid date format. Please use DD.MM.YY\n"
                "(ឧទា. <code>/report_excel 11.06.26 16.06.26</code>)"
            )
            return
        start_date = args[0]
        end_date = args[1]

    reports_data = await asyncio.to_thread(get_reports_by_dates, start_date, end_date)
    if not reports_data:
        await update.message.reply_html(
            "⚠️ <b>មិនមានទិន្នន័យសម្រាប់កាលបរិច្ឆេទនេះទេ៴</b>\n"
            "No data found for the specified period."
        )
        return

    period_str = get_report_period_string(reports_data)
    os.makedirs("tmp", exist_ok=True)
    file_path = os.path.join("tmp", f"report_{period_str}.xlsx")
    status_msg = await update.message.reply_html("⏳ <b>កំពុងបង្កើតរបាយការណ៍ Excel... / Generating Excel report...</b>")
    try:
        exchange_rate = await asyncio.to_thread(get_exchange_rate)
        await asyncio.to_thread(generate_excel_report, reports_data, file_path, exchange_rate)
        with open(file_path, "rb") as f:
            excel_bytes = f.read()
        await update.message.reply_document(
            document=excel_bytes,
            filename=f"report_{period_str}.xlsx",
            caption=f"របាយការណ៍ Excel សម្រាប់ថ្ងៃទី / Excel Report for: {period_str.replace('_to_', ' ដល់ ')}",
            read_timeout=120,
            write_timeout=120
        )
        try:
            await status_msg.delete()
        except Exception:
            pass
    except Exception as e:
        logger.error(f"Error generating Excel report: {e}")
        try:
            await status_msg.delete()
        except Exception:
            pass
        await update.message.reply_html(
            f"⚠️ <b>មានបញ្ហាក្នុងការបង្កើតឯកសារ Excel!</b>\nError: {e}"
        )
    finally:
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

async def setexchange_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    args = context.args
    if not args:
        current_rate = get_exchange_rate()
        await update.message.reply_html(
            f"💵 <b>អត្រាប្តូរប្រាក់បច្ចុប្បន្ន / Current Exchange Rate:</b> 1$ = <b>{current_rate:,.0f}៛</b>\n\n"
            "Usage: <code>/setexchange &lt;rate&gt;</code>\n"
            "Example: <code>/setexchange 4100</code>"
        )
        return

    try:
        rate = float(args[0])
        if rate <= 0:
            raise ValueError()
    except ValueError:
        await update.message.reply_html("⚠️ Error: Exchange rate must be a positive number.")
        return

    set_exchange_rate(rate)
    await update.message.reply_html(
        f"✅ <b>បានកែប្រែអត្រាប្តូរប្រាក់ជោគជ័យ / Exchange rate updated successfully:</b>\n"
        f"1$ = <b>{rate:,.0f}៛</b>"
    )

async def restartcount_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Check if there is any data to reset
    reports_data = get_reports_by_dates(None, None)
    if not reports_data:
        await update.message.reply_html(
            "ℹ️ <b>មិនមានទិន្នន័យវត្តមានសម្រាប់លុបទេ!</b>\n"
            "There is no attendance data to restart."
        )
        return

    # Prompt with warning and inline keyboard
    keyboard = [
        [
            InlineKeyboardButton("⚠️ បញ្ជាក់លុប / Confirm Reset", callback_data="confirm_restart"),
            InlineKeyboardButton("❌ បោះបង់ / Cancel", callback_data="cancel_restart")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    warning_text = (
        "⚠️ <b>ការព្រមាន / Warning:</b>\n\n"
        "តើអ្នកពិតជាចង់កំណត់ការរាប់ឡើងវិញមែនទេ? រាល់វត្តមាន និងរបាយការណ៍ទាំងអស់នឹងត្រូវបានលុបចេញពីប្រព័ន្ធ! "
        "ប្រព័ន្ធនឹងធ្វើការទាញយកឯកសាររបាយការណ៍ជា PDF និង Excel ជូនអ្នកដោយស្វ័យប្រវត្តិកាលពីមុនពេលលុប។\n\n"
        "Are you sure you want to restart the count? All attendance logs and reports will be deleted! "
        "The system will automatically export both PDF and Excel reports as a backup before clearing."
    )
    await update.message.reply_html(warning_text, reply_markup=reply_markup)

async def restartcount_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "cancel_restart":
        await query.edit_message_text(
            text="❌ <b>បានបោះបង់ការកំណត់ការរាប់ឡើងវិញ!</b>\n"
                 "The restart count operation has been cancelled.",
            parse_mode="HTML"
        )
        return
        
    if query.data == "confirm_restart":
        await query.edit_message_text(
            text="⏳ <b>កំពុងបង្កើតឯកសារបម្រុងទុក និងកំណត់ការរាប់ឡើងវិញ...</b>\n"
                 "Generating backup reports and restarting count...",
            parse_mode="HTML"
        )
        
        # 1. Fetch reports data
        reports_data = await asyncio.to_thread(get_reports_by_dates, None, None)
        if not reports_data:
            await query.edit_message_text(
                text="ℹ️ <b>មិនមានទិន្នន័យសម្រាប់លុបទេ!</b>\n"
                     "There is no attendance data to restart.",
                parse_mode="HTML"
            )
            return

        period_str = get_report_period_string(reports_data)
        os.makedirs("tmp", exist_ok=True)
        
        excel_path = os.path.join("tmp", f"backup_report_{period_str}.xlsx")
        pdf_path = os.path.join("tmp", f"backup_report_{period_str}.pdf")
        
        exchange_rate = await asyncio.to_thread(get_exchange_rate)
        
        # 2. Generate Excel Backup
        excel_success = False
        try:
            await asyncio.to_thread(generate_excel_report, reports_data, excel_path, exchange_rate)
            excel_success = True
        except Exception as e:
            logger.error(f"Error generating backup Excel: {e}")
            await query.message.reply_html(f"⚠️ Error generating Excel backup: {e}")
            
        # 3. Generate PDF Backup
        pdf_success = False
        if REPORT_LIBS_AVAILABLE:
            try:
                await generate_pdf_report(reports_data, period_str, pdf_path, exchange_rate)
                pdf_success = True
            except Exception as e:
                logger.error(f"Error generating backup PDF: {e}")
                await query.message.reply_html(f"⚠️ Error generating PDF backup: {e}")
        
        # 4. Send files to the user
        if excel_success and os.path.exists(excel_path):
            with open(excel_path, "rb") as f:
                excel_bytes = f.read()
            await query.message.reply_document(
                document=excel_bytes,
                filename=f"backup_report_{period_str}.xlsx",
                caption="📂 <b>ឯកសារបម្រុងទុក Excel / Excel Backup File</b>",
                read_timeout=120,
                write_timeout=120
            )
            try:
                os.remove(excel_path)
            except Exception:
                pass
                
        if pdf_success and os.path.exists(pdf_path):
            with open(pdf_path, "rb") as f:
                    pdf_bytes = f.read()
            await query.message.reply_document(
                document=pdf_bytes,
                filename=f"backup_report_{period_str}.pdf",
                caption="📂 <b>ឯកសារបម្រុងទុក PDF / PDF Backup File</b>",
                read_timeout=120,
                write_timeout=120
            )
            try:
                os.remove(pdf_path)
            except Exception:
                pass
                
        # 5. Clear reports from database
        try:
            await asyncio.to_thread(restart_attendance_count)
            await query.edit_message_text(
                text="✅ <b>បានកំណត់ការរាប់ឡើងវិញដោយជោគជ័យ!</b>\n"
                     "រាល់ទិន្នន័យវត្តមាន និងរបាយការណ៍ទាំងអស់ត្រូវបានលុបចេញពីប្រព័ន្ធ។ ការរាប់វត្តមាន និងប្រាក់សរុបនឹងចាប់ផ្ដើមពីថ្ងៃទី ១ ឡើងវិញ។\n\n"
                     "✅ <b>Successfully restarted attendance count!</b>\n"
                     "All attendance records and reports have been deleted. Calculation of hours and salaries will start over from Day 1.",
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Error clearing database in callback: {e}")
            await query.message.reply_html(f"⚠️ Error clearing database: {e}")

async def post_init(application: Application) -> None:
    try:
        await application.bot.set_my_commands([
            BotCommand("start", "Start the bot / ផ្ដើមដំណើរការ"),
            BotCommand("help", "Show help and templates / បង្ហាញជំនួយ"),
            BotCommand("addemployee", "Add/update employee hourly rate / បន្ថែមឬកែតម្លៃម៉ោងបុគ្គលិក"),
            BotCommand("addemployees", "Add multiple employees / បន្ថែមឈ្មោះបុគ្គលិកច្រើន"),
            BotCommand("updateemployee", "Rename employee / កែប្រែឈ្មោះបុគ្គលិក"),
            BotCommand("deleteemployee", "Delete employee / លុបឈ្មោះបុគ្គលិក"),
            BotCommand("deleteemployees", "Delete multiple employees / លុបឈ្មោះបុគ្គលិកច្រើន"),
            BotCommand("employees", "List all registered employees / បញ្ជីឈ្មោះបុគ្គលិក"),
            BotCommand("setexchange", "Set KHR to USD exchange rate / កំណត់អត្រាប្តូរប្រាក់"),
            BotCommand("restartcount", "Restart attendance count / កំណត់ការរាប់សារជាថ្មី"),
            BotCommand("report_pdf", "Export report as PDF / ទាញយករបាយការណ៍ជា PDF"),
            BotCommand("report_excel", "Export report as Excel / ទាញយករបាយការណ៍ជា Excel")
        ])
        logger.info("Successfully set bot commands.")
    except Exception as e:
        logger.error(f"Failed to set bot commands during post_init: {e}")

    if REPORT_LIBS_AVAILABLE:
        try:
            from report_generator import ensure_khmer_font_async
            asyncio.create_task(ensure_khmer_font_async())
        except Exception as e:
            logger.error(f"Error starting background font download: {e}")

def main():
    # Initialize Database
    init_db()

    # Get token
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.error("BOT_TOKEN is not set in environmental variables or .env file.")
        print("BOT_TOKEN is missing!")
        return

    logger.info("Starting Daily Attendance & Salary Telegram Bot (Simplified)...")

    # Build the application with increased global timeouts for slow networks
    app = (
        Application.builder()
        .token(token)
        .post_init(post_init)
        .connect_timeout(30.0)
        .read_timeout(30.0)
        .write_timeout(120.0)
        .pool_timeout(30.0)
        .build()
    )

    # Add Command Handlers
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("addemployee", addemployee_command))
    app.add_handler(CommandHandler("addemployees", addemployees_command))
    app.add_handler(CommandHandler("updateemployee", updateemployee_command))
    app.add_handler(CommandHandler("deleteemployee", deleteemployee_command))
    app.add_handler(CommandHandler("deleteemployees", deleteemployees_command))
    app.add_handler(CommandHandler("employees", employees_command))
    app.add_handler(CommandHandler("setexchange", setexchange_command))
    app.add_handler(CommandHandler("restartcount", restartcount_command))
    app.add_handler(CommandHandler("report_pdf", report_pdf_command))
    app.add_handler(CommandHandler("report_excel", report_excel_command))

    # Add Callback Query Handler for restart confirmation
    app.add_handler(CallbackQueryHandler(restartcount_callback, pattern="^(confirm_restart|cancel_restart)$"))

    # Add Message Handler for incoming attendance reports
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Run the bot
    app.run_polling()

if __name__ == "__main__":
    main()
