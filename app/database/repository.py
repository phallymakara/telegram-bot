import re
from datetime import date, datetime, timezone, timedelta

from sqlalchemy import inspect, text

from app.config import DEFAULT_EXCHANGE_RATE
from app.database.connection import SessionLocal, engine
from app.database.models import AttendanceRecord, Employee, Report, Setting


def init_db():
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()

    # Old table cleanup
    if "worker_rates" in existing_tables:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS worker_rates"))

    # Auto-migration for old columns
    with engine.begin() as conn:
        if "employees" in existing_tables:
            columns = [c["name"] for c in inspector.get_columns("employees")]

            if "hourly_rate" in columns and "daily_rate" not in columns:
                conn.execute(text("ALTER TABLE employees RENAME COLUMN hourly_rate TO daily_rate"))

            if "gender" not in columns:
                conn.execute(text("ALTER TABLE employees ADD COLUMN gender TEXT"))

        if "attendance" in existing_tables:
            columns = [c["name"] for c in inspector.get_columns("attendance")]

            if "hourly_rate" in columns and "daily_rate" not in columns:
                conn.execute(text("ALTER TABLE attendance RENAME COLUMN hourly_rate TO daily_rate"))

            if "gender" not in columns:
                conn.execute(text("ALTER TABLE attendance ADD COLUMN gender TEXT"))

    from app.database.connection import create_tables
    create_tables()


def normalize_name(name: str) -> str:
    return re.sub(r"\s+", " ", name or "").strip()


def get_setting(key: str, default: str | None = None) -> str | None:
    db = SessionLocal()
    try:
        setting = db.query(Setting).filter(Setting.key == key).first()
        return setting.value if setting else default
    finally:
        db.close()


def set_setting(key: str, value: str):
    db = SessionLocal()
    try:
        setting = db.query(Setting).filter(Setting.key == key).first()

        if setting:
            setting.value = str(value)
        else:
            db.add(Setting(key=key, value=str(value)))

        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def get_exchange_rate() -> float:
    try:
        value = get_setting("exchange_rate", str(DEFAULT_EXCHANGE_RATE))
        return float(value)
    except ValueError:
        return DEFAULT_EXCHANGE_RATE


def set_exchange_rate(rate: float):
    set_setting("exchange_rate", str(rate))


def detect_gender(token: str) -> str:
    if not token:
        return ""

    token = token.strip().lower()

    if token in ["ប", "ប្រុស", "m", "male"]:
        return "ប"

    if token in ["ស", "ស្រី", "f", "female"]:
        return "ស"

    return ""


def add_employee(name: str, daily_rate: float, gender: str | None = None) -> bool:
    name = normalize_name(name)
    db = SessionLocal()

    try:
        employee = db.query(Employee).filter(Employee.name == name).first()

        if employee:
            employee.daily_rate = float(daily_rate)

            if gender is not None:
                employee.gender = gender
        else:
            db.add(Employee(name=name, daily_rate=float(daily_rate), gender=gender))

        # Sync old attendance records
        records = db.query(AttendanceRecord).filter(AttendanceRecord.employee_name == name).all()

        for record in records:
            record.daily_rate = float(daily_rate)

            if record.hours > 1.0:
                base_days = 1.0
                ot_hours = max(0.0, record.hours - 8.0)
            else:
                base_days = record.hours / 8.0
                ot_hours = 0.0

            record.multiplier = base_days + ot_hours / 8.0
            record.salary = record.multiplier * float(daily_rate)

            if gender is not None:
                record.gender = gender

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def update_employee_name(old_name: str, new_name: str) -> bool:
    old_name = normalize_name(old_name)
    new_name = normalize_name(new_name)
    db = SessionLocal()

    try:
        employee = db.query(Employee).filter(Employee.name == old_name).first()

        if not employee:
            return False

        existing_employee = db.query(Employee).filter(Employee.name == new_name).first()

        if existing_employee:
            return False

        employee.name = new_name

        db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_name == old_name
        ).update({AttendanceRecord.employee_name: new_name})

        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def delete_employee(name: str) -> bool:
    name = normalize_name(name)
    db = SessionLocal()

    try:
        employee = db.query(Employee).filter(Employee.name == name).first()

        if employee:
            db.delete(employee)

        deleted_records = db.query(AttendanceRecord).filter(
            AttendanceRecord.employee_name == name
        ).delete()

        db.commit()
        return employee is not None or deleted_records > 0

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_employee_rate(name: str) -> float | None:
    name = normalize_name(name)
    db = SessionLocal()

    try:
        employee = db.query(Employee).filter(Employee.name == name).first()
        return employee.daily_rate if employee else None
    finally:
        db.close()


def get_all_employees() -> dict:
    db = SessionLocal()

    try:
        employees = db.query(Employee).all()

        return {
            employee.name: {
                "rate": employee.daily_rate,
                "gender": employee.gender or "",
            }
            for employee in employees
        }

    finally:
        db.close()


def parse_note_details(note: str):
    if not note:
        return 0.0, 0.0, ""

    borrow_amount = 0.0
    borrow_match = re.search(
        r"(?:ខ្ចី|borrow|br|loan)\s*[:៖\s]?\s*(\d+(?:,\d+)?)(?:\s*៛|\s*\$)?",
        note,
        re.IGNORECASE,
    )

    if borrow_match:
        value = borrow_match.group(1).replace(",", "")

        try:
            borrow_amount = float(value)
        except ValueError:
            pass

    deduction_amount = 0.0
    deduct_match = re.search(
        r"(?:កាត់|deduct|ded)\s*[:៖\s]?\s*(\d+(?:,\d+)?)(?:\s*៛|\s*\$)?",
        note,
        re.IGNORECASE,
    )

    if deduct_match:
        value = deduct_match.group(1).replace(",", "")

        try:
            deduction_amount = float(value)
        except ValueError:
            pass

    cleaned_note = note

    if borrow_match:
        cleaned_note = cleaned_note.replace(borrow_match.group(0), "")

    if deduct_match:
        cleaned_note = cleaned_note.replace(deduct_match.group(0), "")

    cleaned_note = re.sub(r"^\s*[,，;\.\s\-\/៖:]+", "", cleaned_note)
    cleaned_note = re.sub(r"[,，;\.\s\-\/៖:]+$", "", cleaned_note).strip()

    return borrow_amount, deduction_amount, cleaned_note


def extract_report_day(header: str) -> str:
    match = re.search(r"(\d{1,2}\.\d{1,2}\.\d{2,4})", header)

    if match:
        return match.group(1)

    return header.strip()


def parse_date(date_str: str):
    try:
        parts = date_str.strip().split(".")

        if len(parts) == 3:
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])

            if year < 100:
                year += 2000

            return date(year, month, day)

    except Exception:
        pass

    return None


def save_attendance_report(date_str: str, day_header: str, workers_list: list) -> int:
    db = SessionLocal()

    try:
        new_day = extract_report_day(day_header)
        existing_reports = db.query(Report).all()

        existing_borrows = {}

        for report in existing_reports:
            if extract_report_day(report.header) == new_day:
                old_records = db.query(AttendanceRecord).filter(
                    AttendanceRecord.report_id == report.id
                ).all()

                for record in old_records:
                    if record.note:
                        borrow_value, deduct_value, _ = parse_note_details(record.note)

                        if borrow_value > 0 or deduct_value > 0:
                            existing_borrows[record.employee_name] = (
                                borrow_value,
                                deduct_value,
                            )

                db.query(AttendanceRecord).filter(
                    AttendanceRecord.report_id == report.id
                ).delete()

                db.delete(report)

        db.commit()

        report = Report(date=date_str, header=day_header)
        db.add(report)
        db.commit()
        db.refresh(report)

        for worker in workers_list:
            name = worker["name"]
            hours = worker["hours"]
            note = worker["note"]

            incoming_borrow, incoming_deduct, cleaned_note = parse_note_details(note)

            borrow_value = incoming_borrow
            deduct_value = incoming_deduct

            if borrow_value == 0 and deduct_value == 0 and name in existing_borrows:
                borrow_value, deduct_value = existing_borrows[name]

            note_parts = []

            if cleaned_note:
                note_parts.append(cleaned_note)

            if borrow_value > 0:
                note_parts.append(f"ខ្ចី {int(borrow_value)}")

            if deduct_value > 0:
                note_parts.append(f"កាត់ {int(deduct_value)}")

            note = ", ".join(note_parts) if note_parts else None

            employee = db.query(Employee).filter(Employee.name == name).first()

            rate = employee.daily_rate if employee else 0.0
            gender = employee.gender if employee else None

            if hours > 1.0:
                base_days = 1.0
                ot_hours = max(0.0, hours - 8.0)
            else:
                base_days = hours / 8.0
                ot_hours = 0.0

            multiplier = base_days + ot_hours / 8.0
            salary = multiplier * rate

            record = AttendanceRecord(
                report_id=report.id,
                employee_name=name,
                multiplier=multiplier,
                hours=hours,
                daily_rate=rate,
                salary=salary,
                note=note,
                gender=gender,
            )

            db.add(record)

        db.commit()
        return report.id

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_accumulated_totals() -> dict:
    db = SessionLocal()

    try:
        records = db.query(AttendanceRecord).all()
        totals = {}

        for record in records:
            name = record.employee_name

            if name not in totals:
                totals[name] = {
                    "days": 0.0,
                    "hours": 0.0,
                    "salary": 0.0,
                    "ot_hours": 0.0,
                    "ot_salary": 0.0,
                }

            base_days = min(8.0, record.hours) / 8.0

            totals[name]["days"] += base_days
            totals[name]["hours"] += record.hours
            totals[name]["salary"] += record.salary

            ot_hours = max(0.0, record.hours - 8.0)
            ot_salary = ot_hours * (record.daily_rate / 8.0)

            totals[name]["ot_hours"] += ot_hours
            totals[name]["ot_salary"] += ot_salary

        return totals

    finally:
        db.close()


def get_reports_by_dates(start_date_str: str | None = None, end_date_str: str | None = None) -> list:
    db = SessionLocal()

    try:
        reports = db.query(Report).all()
        matched = []

        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None

        for report in reports:
            report_day_str = extract_report_day(report.header)
            report_date = parse_date(report_day_str)

            include = True

            if report_date:
                if start_date and report_date < start_date:
                    include = False

                if end_date and report_date > end_date:
                    include = False
            else:
                if start_date or end_date:
                    include = False

            if include:
                records = db.query(AttendanceRecord).filter(
                    AttendanceRecord.report_id == report.id
                ).all()

                matched.append(
                    {
                        "report": report,
                        "records": records,
                    }
                )

        def sort_key(item):
            parsed = parse_date(extract_report_day(item["report"].header))
            return parsed if parsed else date.min

        matched.sort(key=sort_key)
        return matched

    finally:
        db.close()


def restart_attendance_count() -> bool:
    db = SessionLocal()

    try:
        db.query(AttendanceRecord).delete()
        db.query(Report).delete()
        db.commit()
        return True

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def record_borrow(employee_name: str, borrow_amount: float, deduction_amount: float) -> tuple[bool, str, str]:
    employee_name = normalize_name(employee_name)
    db = SessionLocal()

    try:
        employee = db.query(Employee).filter(Employee.name == employee_name).first()

        if not employee:
            employee = db.query(Employee).filter(Employee.name.ilike(employee_name.strip())).first()

        if not employee:
            return (
                False,
                f"Employee '<b>{employee_name}</b>' is not registered. Please register them first.",
                "",
            )

        employee_name = employee.name

        tz_kh = timezone(timedelta(hours=7))
        today_str = datetime.now(tz_kh).strftime("%d-%b-%Y")

        report = (
            db.query(Report)
            .filter(Report.date == today_str)
            .order_by(Report.id.desc())
            .first()
        )

        if not report:
            report = db.query(Report).order_by(Report.id.desc()).first()

        if not report:
            return False, "⚠️ No reports found. Please submit attendance first.", ""

        record = (
            db.query(AttendanceRecord)
            .filter(
                AttendanceRecord.report_id == report.id,
                AttendanceRecord.employee_name == employee_name,
            )
            .first()
        )

        if not record:
            record = (
                db.query(AttendanceRecord)
                .filter(
                    AttendanceRecord.report_id == report.id,
                    AttendanceRecord.employee_name.ilike(employee_name.strip()),
                )
                .first()
            )

        if not record:
            report_day = extract_report_day(report.header)
            return (
                False,
                f"⚠️ Employee '<b>{employee_name}</b>' is not in attendance list for '<b>{report_day}</b>'.",
                "",
            )

        _, _, cleaned_note = parse_note_details(record.note)

        note_parts = []

        if cleaned_note:
            note_parts.append(cleaned_note)

        if borrow_amount > 0:
            note_parts.append(f"ខ្ចី {int(borrow_amount)}")

        if deduction_amount > 0:
            note_parts.append(f"កាត់ {int(deduction_amount)}")

        record.note = ", ".join(note_parts) if note_parts else None
        db.commit()

        report_day = extract_report_day(report.header)

        return True, employee_name, report_day

    except Exception as error:
        db.rollback()
        return False, f"⚠️ Database error: {str(error)}", ""

    finally:
        db.close()