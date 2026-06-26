def calculate_salary(hours: float, daily_rate: float) -> dict:
    """
    Calculate salary from working hours and daily rate.

    Rule:
    - 8 hours = 1 full working day
    - more than 8 hours = overtime
    """
    rate = daily_rate or 0.0

    salary = (hours / 8.0) * rate
    ot_hours = max(0.0, hours - 8.0)
    ot_salary = ot_hours * (rate / 8.0)

    days = min(8.0, hours) / 8.0

    return {
        "hours": hours,
        "days": days,
        "salary": salary,
        "ot_hours": ot_hours,
        "ot_salary": ot_salary,
    }


def calculate_salary_usd(amount_riel: float, exchange_rate: float) -> float:
    """
    Convert KHR amount to USD.
    """
    if exchange_rate <= 0:
        return 0.0

    return amount_riel / exchange_rate


def calculate_borrow_deduction(borrow_amount: float) -> float:
    """
    Borrow rule:
    - If borrow >= 100,000៛, deduction = 10%
    - Otherwise, deduction = 0
    """
    if borrow_amount >= 100000:
        return borrow_amount * 0.10

    return 0.0


def calculate_debt(borrow_amount: float, deduction_amount: float) -> float:
    """
    Debt rule:
    debt = borrow + interest - deduction

    Interest:
    - 10% if borrow >= 100,000៛
    - 0 otherwise
    """
    interest = borrow_amount * 0.10 if borrow_amount >= 100000 else 0.0
    return borrow_amount + interest - deduction_amount