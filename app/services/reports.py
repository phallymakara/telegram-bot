import asyncio
import os

from app.database.repository import get_exchange_rate, get_reports_by_dates, parse_date
from app.reports.excel import generate_excel_report
from app.reports.generator import get_report_period_string
from app.reports.pdf import generate_pdf_report


def validate_report_dates(args: list[str]) -> tuple[bool, str | None, str | None, str]:
    """
    Validate command args for report export.

    Supported:
    /report_pdf
    /report_pdf 26.06.26
    /report_pdf 20.06.26 26.06.26
    """
    start_date = None
    end_date = None

    if len(args) == 1:
        if not parse_date(args[0]):
            return False, None, None, "Invalid date format. Please use DD.MM.YY"

        start_date = args[0]
        end_date = args[0]

    elif len(args) >= 2:
        if not parse_date(args[0]) or not parse_date(args[1]):
            return False, None, None, "Invalid date format. Please use DD.MM.YY"

        start_date = args[0]
        end_date = args[1]

    return True, start_date, end_date, ""


async def get_report_data(start_date: str | None, end_date: str | None):
    return await asyncio.to_thread(get_reports_by_dates, start_date, end_date)


async def create_excel_report_file(reports_data: list) -> tuple[str, str]:
    os.makedirs("tmp", exist_ok=True)

    period = get_report_period_string(reports_data)
    file_path = os.path.join("tmp", f"report_{period}.xlsx")

    exchange_rate = await asyncio.to_thread(get_exchange_rate)

    await asyncio.to_thread(
        generate_excel_report,
        reports_data,
        file_path,
        exchange_rate,
    )

    return file_path, period


async def create_pdf_report_file(reports_data: list) -> tuple[str, str]:
    os.makedirs("tmp", exist_ok=True)

    period = get_report_period_string(reports_data)
    file_path = os.path.join("tmp", f"report_{period}.pdf")

    exchange_rate = await asyncio.to_thread(get_exchange_rate)

    await generate_pdf_report(
        reports_data,
        period,
        file_path,
        exchange_rate,
    )

    return file_path, period