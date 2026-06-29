import re
from datetime import date, datetime

from app.config import TZ_KH


def get_current_date_string() -> str:
    """
    Return current date using Cambodia timezone.
    Example: 26-Jun-2026
    """
    return datetime.now(TZ_KH).strftime("%d-%b-%Y")


def get_today_template_date() -> str:
    """
    Return current date for attendance template.
    Example: 26.06.26
    """
    return datetime.now(TZ_KH).strftime("%d.%m.%y")


def extract_report_day(header: str) -> str:
    """
    Extract date from report header.
    Example:
    'ថ្ងៃទី: 26.06.26 (7:00am - 5:00pm)' -> '26.06.26'
    """
    if not header:
        return ""

    match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{2,4})", header)

    if match:
        return match.group(1)

    return header.strip()


def parse_date(date_str: str):
    """
    Parse DD.MM.YY or DD.MM.YYYY date format.

    Example:
    26.06.26 -> date(2026, 6, 26)
    26.06.2026 -> date(2026, 6, 26)

    Return None if invalid.
    """
    if not date_str:
        return None

    try:
        parts = date_str.strip().split(".")

        if len(parts) != 3:
            return None

        day = int(parts[0])
        month = int(parts[1])
        year = int(parts[2])

        if year < 100:
            year += 2000

        return date(year, month, day)

    except Exception:
        return None


def parse_header_date_time(header: str):
    """
    Parse report header into date part and time part.

    Example:
    'ថ្ងៃទី: 26.06.26 (7:00am - 5:00pm)'
    returns:
    ('26.06.26', '7:00am - 5:00pm')
    """
    if not header:
        return "", None

    match = re.search(
        r"(?:ថ្ងៃទី|ងៃទី|កាលបរិច្ឆេទ)?\s*[:៖]?\s*([\d\.\-\/]+)\s*(?:\((.*?)\))?",
        header,
        re.IGNORECASE,
    )

    if match:
        date_part = match.group(1).strip()
        time_part = match.group(2).strip() if match.group(2) else None
        return date_part, time_part

    return header.strip(), None