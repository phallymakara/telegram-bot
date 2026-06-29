from app.database.repository import (
    add_employee,
    delete_employee,
    detect_gender,
    get_all_employees,
    get_exchange_rate,
    update_employee_name,
)


def parse_employee_line(line: str) -> tuple[bool, str, float | None, str, str]:
    """
    Parse one employee line.

    Expected format:
    name gender daily_rate
    name daily_rate

    Examples:
    ប៉ែន ទិត្យ ប 80000
    អៀម អេន ស 64000
    សុខា 70000
    """
    cleaned = line.strip()

    if not cleaned:
        return False, "", None, "", "Empty line"

    parts = cleaned.split()

    if len(parts) < 2:
        return False, "", None, "", "Invalid format"

    try:
        daily_rate = float(parts[-1])
    except ValueError:
        return False, "", None, "", "Rate must be a number"

    gender = ""
    name_parts = parts[:-1]

    if len(parts) >= 3:
        possible_gender = parts[-2].strip()
        normalized_gender = detect_gender(possible_gender)

        if normalized_gender:
            gender = normalized_gender
            name_parts = parts[:-2]

    name = " ".join(name_parts).strip()

    if not name:
        return False, "", None, "", "Name cannot be empty"

    return True, name, daily_rate, gender, ""


def add_employees_from_text(text: str) -> dict:
    """
    Add or update multiple employees from multiline text.
    """
    success_list = []
    error_list = []

    lines = text.splitlines()

    for line in lines:
        cleaned = line.strip()

        if not cleaned:
            continue

        is_valid, name, daily_rate, gender, error = parse_employee_line(cleaned)

        if not is_valid:
            error_list.append(f"• {cleaned} ({error})")
            continue

        try:
            add_employee(name, daily_rate, gender)
            gender_text = f" ({gender})" if gender else ""
            success_list.append(f"• {name}{gender_text}: {daily_rate:,.0f}៛/day")

        except Exception as error:
            error_list.append(f"• {name} (Database error: {error})")

    return {
        "success": success_list,
        "errors": error_list,
    }


def rename_employee(old_name: str, new_name: str) -> tuple[bool, str]:
    """
    Rename employee.
    """
    old_name = " ".join(old_name.split()).strip()
    new_name = " ".join(new_name.split()).strip()

    if not old_name or not new_name:
        return False, "Old name and new name cannot be empty."

    try:
        success = update_employee_name(old_name, new_name)

        if success:
            return True, f"Employee {old_name} renamed to {new_name}."

        return False, f"Employee {old_name} not found, or {new_name} already exists."

    except Exception as error:
        return False, f"Database error: {error}"


def delete_employees_from_text(text: str) -> dict:
    """
    Delete multiple employees from multiline text.
    """
    success_list = []
    error_list = []

    lines = text.splitlines()

    for line in lines:
        name = " ".join(line.split()).strip()

        if not name:
            continue

        try:
            success = delete_employee(name)

            if success:
                success_list.append(f"• {name}")
            else:
                error_list.append(f"• {name} (Not found)")

        except Exception as error:
            error_list.append(f"• {name} (Database error: {error})")

    return {
        "success": success_list,
        "errors": error_list,
    }


def get_employee_list_text() -> str:
    """
    Return formatted employee list text.
    """
    employees = get_all_employees()

    if not employees:
        return "ℹ️ No employees registered yet."

    exchange_rate = get_exchange_rate()

    text = "📋 បញ្ជីឈ្មោះបុគ្គលិក និងតម្លៃថ្ងៃ / Registered Employees & Daily Rates:\n"
    text += f"💵 Current Exchange Rate: 1$ = {exchange_rate:,.0f}៛\n\n"

    for index, (name, info) in enumerate(employees.items(), 1):
        rate = info["rate"]
        gender = info["gender"]

        if gender:
            text += f"{index}. {name}: {gender} -> {rate:,.0f}៛/day\n"
        else:
            text += f"{index}. {name}: {rate:,.0f}៛/day\n"

    return text