from app.database.repository import (
    get_accumulated_totals,
    get_all_employees,
    get_employee_rate,
    get_exchange_rate,
    save_attendance_report,
)
from app.services.salary import calculate_salary, calculate_salary_usd
from app.utils.dates import get_current_date_string, get_today_template_date, parse_header_date_time
from app.utils.formatter import get_num_emoji
from app.utils.parser import parse_report_text_by_days


def build_attendance_template() -> str:
    employees = get_all_employees()

    if not employees:
        return (
            "ℹ️ មិនទាន់មានបុគ្គលិកចុះឈ្មោះនៅឡើយទេ។\n"
            "No employees registered yet."
        )

    today = get_today_template_date()

    template_text = f"ថ្ងៃទី: {today} (7:00am - 5:00pm)\n"

    for index, name in enumerate(employees.keys(), 1):
        template_text += f"{index}. {name}.      [ 0 h ]\n"

    return template_text


def parse_attendance_message(text: str) -> list:
    return parse_report_text_by_days(text)


def build_single_day_report(day_block: dict) -> str:
    parsed_workers = day_block["workers"]
    day_header = day_block["header"]

    current_date = get_current_date_string()
    exchange_rate = get_exchange_rate()

    report_id = save_attendance_report(current_date, day_header, parsed_workers)

    running_totals = get_accumulated_totals()

    details_today_lines = []
    details_total_lines = []

    for index, worker in enumerate(parsed_workers, 1):
        name = worker["name"]
        hours = worker["hours"]
        note = worker["note"]

        daily_rate = get_employee_rate(name)
        is_unregistered = daily_rate is None
        rate = daily_rate if daily_rate is not None else 0.0

        salary_result = calculate_salary(hours, rate)

        salary = salary_result["salary"]
        days = salary_result["days"]
        ot_hours = salary_result["ot_hours"]
        ot_salary = salary_result["ot_salary"]

        salary_usd = calculate_salary_usd(salary, exchange_rate)
        ot_salary_usd = calculate_salary_usd(ot_salary, exchange_rate)

        accum_salary = running_totals.get(name, {}).get("salary", salary)
        accum_days = running_totals.get(name, {}).get("days", days)
        accum_ot_hours = running_totals.get(name, {}).get("ot_hours", ot_hours)

        accum_salary_usd = calculate_salary_usd(accum_salary, exchange_rate)

        days_text = f"{days:.2f}" if days % 1 != 0 else f"{int(days)}"
        accum_days_text = f"{accum_days:.2f}" if accum_days % 1 != 0 else f"{int(accum_days)}"

        label_suffix = ""

        if is_unregistered:
            label_suffix += " (Unregistered)"

        if note:
            label_suffix += f" ({note})"

        num_emoji = get_num_emoji(index)

        today_worker_block = (
            f"{num_emoji} <b>{name}</b>{label_suffix}\n"
            f"• ថ្ងៃធ្វើការ     : {days_text} ថ្ងៃ\n"
            f"• ថែមម៉ោង    : {ot_hours:.1f}h\n"
            f"• ប្រាក់ថែម    : {int(round(ot_salary)):,}៛ (${ot_salary_usd:.2f})\n"
            f"• សរុបថ្ងៃនេះ  : {int(round(salary)):,}៛ (${salary_usd:.2f})"
        )

        total_worker_block = (
            f"{num_emoji} <b>{name}</b>{' (Unregistered)' if is_unregistered else ''}\n"
            f"• ថ្ងៃធ្វើការ    : {accum_days_text} ថ្ងៃ\n"
            f"• ថែមម៉ោង   : {accum_ot_hours:.1f}h\n"
            f"• ប្រាក់សរុប  : {int(round(accum_salary)):,}៛ (${accum_salary_usd:.2f})"
        )

        details_today_lines.append(today_worker_block)
        details_total_lines.append(total_worker_block)

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
        + "\n\n".join(details_today_lines)
        + "\n"
    )

    total_section = (
        f"\n{separator}\n"
        f"<b>ប្រាក់សរុប</b>\n"
        f"{separator}\n"
        + "\n\n".join(details_total_lines)
        + "\n"
    )

    all_registered = get_all_employees()
    today_names = {worker["name"].strip().lower() for worker in parsed_workers}
    absent_names = [
        name for name in all_registered
        if name.strip().lower() not in today_names
    ]
    absent_text = "គ្មាន" if not absent_names else ", ".join(absent_names)

    grand_total_days = sum(info["days"] for info in running_totals.values())
    grand_total_days_text = f"{grand_total_days:.2f}" if grand_total_days % 1 != 0 else f"{int(grand_total_days)}"

    grand_total_ot = sum(info["ot_hours"] for info in running_totals.values())
    grand_total_salary_riel = sum(info["salary"] for info in running_totals.values())
    grand_total_salary_usd = calculate_salary_usd(grand_total_salary_riel, exchange_rate)

    footer_section = (
        f"\n{separator}\n"
        f"<b>សរុប</b>\n"
        f"{separator}\n"
        f"វត្តមានសរុបថ្ងៃនេះ : {len(parsed_workers)} នាក់\n"
        f"អវត្តមានថ្ងៃនេះ      : {absent_text}\n"
        f"ថ្ងៃធ្វើការសរុប       : {grand_total_days_text} ថ្ងៃ\n"
        f"ថែមម៉ោងសរុប      : {grand_total_ot:.1f}h\n\n"
        f"💰 ប្រាក់ឈ្នួលសរុប : ${grand_total_salary_usd:,.2f}\n"
        f"🇰🇭 ស្មើនឹង              : {int(round(grand_total_salary_riel)):,}៛\n\n"
        f"✅ រក្សាទុកទិន្នន័យរួចរាល់\n"
        f"🆔 Report ID: #{report_id}"
    )

    return report_header + today_section + total_section + footer_section