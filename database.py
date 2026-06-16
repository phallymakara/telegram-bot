import os
import re
from datetime import datetime
from sqlalchemy import create_engine, Column, String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///attendance.db")

Base = declarative_base()

class Employee(Base):
    __tablename__ = 'employees'
    name = Column(String, primary_key=True)
    daily_rate = Column(Float, nullable=False)
    gender = Column(String, nullable=True)

class Setting(Base):
    __tablename__ = 'settings'
    key = Column(String, primary_key=True)
    value = Column(String, nullable=False)

class Report(Base):
    __tablename__ = 'reports'
    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(String, nullable=False)
    header = Column(String, nullable=False)
    submitted_at = Column(DateTime, default=datetime.utcnow)

class AttendanceRecord(Base):
    __tablename__ = 'attendance'
    id = Column(Integer, primary_key=True, autoincrement=True)
    report_id = Column(Integer, ForeignKey('reports.id', ondelete='CASCADE'), nullable=False)
    employee_name = Column(String, nullable=False)
    multiplier = Column(Float, nullable=False)
    hours = Column(Float, nullable=False)
    daily_rate = Column(Float, nullable=False)
    salary = Column(Float, nullable=False)
    note = Column(String, nullable=True)
    gender = Column(String, nullable=True)

# Create engine and session
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

def init_db():
    from sqlalchemy import inspect, text
    inspector = inspect(engine)
    existing_tables = inspector.get_table_names()
    # If old tables from previous feature removal exist, drop them
    if 'worker_rates' in existing_tables:
        with engine.begin() as conn:
            conn.execute(text("DROP TABLE IF EXISTS worker_rates"))
            
    # Auto-migration: rename columns from hourly_rate to daily_rate if they exist
    with engine.begin() as conn:
        if 'employees' in existing_tables:
            columns = [c['name'] for c in inspector.get_columns('employees')]
            if 'hourly_rate' in columns and 'daily_rate' not in columns:
                conn.execute(text("ALTER TABLE employees RENAME COLUMN hourly_rate TO daily_rate"))
            if 'gender' not in columns:
                conn.execute(text("ALTER TABLE employees ADD COLUMN gender TEXT"))
        if 'attendance' in existing_tables:
            columns = [c['name'] for c in inspector.get_columns('attendance')]
            if 'hourly_rate' in columns and 'daily_rate' not in columns:
                conn.execute(text("ALTER TABLE attendance RENAME COLUMN hourly_rate TO daily_rate"))
            if 'gender' not in columns:
                conn.execute(text("ALTER TABLE attendance ADD COLUMN gender TEXT"))
                
    Base.metadata.create_all(bind=engine)

# Settings utilities
def get_setting(key: str, default: str = None) -> str:
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
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_exchange_rate() -> float:
    try:
        val = get_setting('exchange_rate', '4000')
        return float(val)
    except ValueError:
        return 4000.0

def set_exchange_rate(rate: float):
    set_setting('exchange_rate', str(rate))

# Utility functions
def add_employee(name: str, daily_rate: float, gender: str = None) -> bool:
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.name == name).first()
        if employee:
            employee.daily_rate = float(daily_rate)
            if gender is not None:
                employee.gender = gender
        else:
            db.add(Employee(name=name, daily_rate=float(daily_rate), gender=gender))
        
        # Sync legacy attendance records
        records = db.query(AttendanceRecord).filter(AttendanceRecord.employee_name == name).all()
        for rec in records:
            rec.daily_rate = float(daily_rate)
            rec.salary = (rec.hours / 8.0) * float(daily_rate)
            if gender is not None:
                rec.gender = gender
            
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def update_employee_name(old_name: str, new_name: str) -> bool:
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.name == old_name).first()
        if employee:
            new_emp = db.query(Employee).filter(Employee.name == new_name).first()
            if new_emp:
                return False
            
            employee.name = new_name
            
            # Sync legacy attendance records name
            db.query(AttendanceRecord).filter(AttendanceRecord.employee_name == old_name).update(
                {AttendanceRecord.employee_name: new_name}
            )
            
            db.commit()
            return True
        return False
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def delete_employee(name: str) -> bool:
    db = SessionLocal()
    try:
        employee = db.query(Employee).filter(Employee.name == name).first()
        if employee:
            db.delete(employee)
            
        # Sync legacy attendance records removal (works for unregistered too)
        deleted_records = db.query(AttendanceRecord).filter(AttendanceRecord.employee_name == name).delete()
        
        db.commit()
        return (employee is not None) or (deleted_records > 0)
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def restart_attendance_count() -> bool:
    db = SessionLocal()
    try:
        db.query(AttendanceRecord).delete()
        db.query(Report).delete()
        db.commit()
        return True
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_employee_rate(name: str) -> float:
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
        return {e.name: {'rate': e.daily_rate, 'gender': e.gender or ""} for e in employees}
    finally:
        db.close()

def detect_gender(token: str) -> str:
    if not token:
        return ""
    t = token.strip().lower()
    if t in ["ប", "ប្រុស", "m", "male"]:
        return "ប"
    if t in ["ស", "ស្រី", "f", "female"]:
        return "ស"
    return ""

def parse_note_details(note: str):
    import re
    if not note:
        return 0.0, 0.0, ""
    
    # Extract borrow amount
    borrow_amount = 0.0
    borrow_match = re.search(r'(?:ខ្ចី|borrow|br|loan)\s*[:៖\s]?\s*(\d+(?:,\d+)?)(?:\s*៛|\s*\$)?', note, re.IGNORECASE)
    if borrow_match:
        val_str = borrow_match.group(1).replace(',', '')
        try:
            borrow_amount = float(val_str)
        except ValueError:
            pass

    # Extract deduction amount
    deduction_amount = 0.0
    deduct_match = re.search(r'(?:កាត់|deduct|ded)\s*[:៖\s]?\s*(\d+(?:,\d+)?)(?:\s*៛|\s*\$)?', note, re.IGNORECASE)
    if deduct_match:
        val_str = deduct_match.group(1).replace(',', '')
        try:
            deduction_amount = float(val_str)
        except ValueError:
            pass

    # Clean note string by removing the matched segments
    cleaned_note = note
    if borrow_match:
        cleaned_note = cleaned_note.replace(borrow_match.group(0), "")
    if deduct_match:
        cleaned_note = cleaned_note.replace(deduct_match.group(0), "")
    
    cleaned_note = re.sub(r'^\s*[,，;\.\s\-\/៖:]+', '', cleaned_note)
    cleaned_note = re.sub(r'[,，;\.\s\-\/៖:]+$', '', cleaned_note).strip()
    
    return borrow_amount, deduction_amount, cleaned_note

def extract_report_day(header: str) -> str:
    # Look for date pattern like DD.MM.YY or D.M.YY (e.g. 16.06.26 or 1.06.26)
    match = re.search(r'(\d{1,2}\.\d{1,2}\.\d{2,4})', header)
    if match:
        return match.group(1)
    # Fall back to entire header (cleaned)
    return header.strip()

def save_attendance_report(date_str: str, day_header: str, workers_list: list) -> int:
    db = SessionLocal()
    try:
        # Check if a report for the same day already exists and delete it
        new_day = extract_report_day(day_header)
        existing_reports = db.query(Report).all()
        
        # Keep track of existing borrow/deduct notes to carry over
        existing_borrows = {}
        for rep in existing_reports:
            if extract_report_day(rep.header) == new_day:
                old_records = db.query(AttendanceRecord).filter(AttendanceRecord.report_id == rep.id).all()
                for r in old_records:
                    if r.note:
                        borrow_val, deduct_val, _ = parse_note_details(r.note)
                        if borrow_val > 0 or deduct_val > 0:
                            existing_borrows[r.employee_name] = (borrow_val, deduct_val)
                
                db.query(AttendanceRecord).filter(AttendanceRecord.report_id == rep.id).delete()
                db.delete(rep)
        db.commit()

        # 1. Create Report
        report = Report(date=date_str, header=day_header)
        db.add(report)
        db.commit()
        db.refresh(report)
        
        # 2. Add Attendance Records
        for w in workers_list:
            name = w['name']
            hours = w['hours']
            note = w['note']
            
            # Clean and parse incoming note
            incoming_b, incoming_d, cleaned_note = parse_note_details(note)
            
            # Carry over database values if incoming values are not specified (both 0)
            b_val = incoming_b
            d_val = incoming_d
            if b_val == 0 and d_val == 0 and name in existing_borrows:
                b_val, d_val = existing_borrows[name]
                
            note_parts = []
            if cleaned_note:
                note_parts.append(cleaned_note)
            if b_val > 0:
                note_parts.append(f"ខ្ចី {int(b_val)}")
            if d_val > 0:
                note_parts.append(f"កាត់ {int(d_val)}")
            
            note = ", ".join(note_parts) if note_parts else None
            
            # Resolve daily rate and gender
            employee = db.query(Employee).filter(Employee.name == name).first()
            rate = employee.daily_rate if employee else 0.0
            gender = employee.gender if employee else None
            
            mult = hours / 8.0
            salary = mult * rate
            
            record = AttendanceRecord(
                report_id=report.id,
                employee_name=name,
                multiplier=mult,
                hours=hours,
                daily_rate=rate,
                salary=salary,
                note=note,
                gender=gender
            )
            db.add(record)
            
        db.commit()
        return report.id
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def get_accumulated_totals() -> dict:
    db = SessionLocal()
    try:
        records = db.query(AttendanceRecord).all()
        totals = {}
        for rec in records:
            name = rec.employee_name
            if name not in totals:
                totals[name] = {
                    'hours': 0.0,
                    'salary': 0.0,
                    'ot_hours': 0.0,
                    'ot_salary': 0.0
                }
            totals[name]['hours'] += rec.hours
            totals[name]['salary'] += rec.salary
            
            ot_h = max(0.0, rec.hours - 8.0)
            ot_s = ot_h * (rec.daily_rate / 8.0)
            totals[name]['ot_hours'] += ot_h
            totals[name]['ot_salary'] += ot_s
        return totals
    finally:
        db.close()

def parse_date(date_str: str):
    """Parse a DD.MM.YY date string into a date object. Returns None on failure."""
    try:
        parts = date_str.strip().split('.')
        if len(parts) == 3:
            day = int(parts[0])
            month = int(parts[1])
            year = int(parts[2])
            if year < 100:
                year += 2000
            from datetime import date
            return date(year, month, day)
    except Exception:
        pass
    return None

def get_reports_by_dates(start_date_str: str = None, end_date_str: str = None) -> list:
    """Return reports (with their attendance records) filtered by date range.
    
    If both arguments are None, all reports are returned.
    If only start_date_str is given, only that single day is matched.
    """
    db = SessionLocal()
    try:
        reports = db.query(Report).all()
        matched = []

        from datetime import date
        start_date = parse_date(start_date_str) if start_date_str else None
        end_date = parse_date(end_date_str) if end_date_str else None

        for rep in reports:
            rep_day_str = extract_report_day(rep.header)
            rep_date = parse_date(rep_day_str)

            include = True
            if rep_date:
                if start_date and rep_date < start_date:
                    include = False
                if end_date and rep_date > end_date:
                    include = False
            else:
                # If we can't parse the date and a filter is active, exclude
                if start_date or end_date:
                    include = False

            if include:
                records = db.query(AttendanceRecord).filter(
                    AttendanceRecord.report_id == rep.id
                ).all()
                matched.append({'report': rep, 'records': records})

        # Sort by date ascending
        def sort_key(item):
            from datetime import date
            d = parse_date(extract_report_day(item['report'].header))
            return d if d else date.min

        matched.sort(key=sort_key)
        return matched
    finally:
        db.close()

def record_borrow(employee_name: str, borrow_amount: float, deduction_amount: float) -> tuple[bool, str, str]:
    """
    Records a borrow for an employee.
    Finds today's report (or fallback to the most recent report).
    Clears any prior borrow/deduct annotations and adds the new ones.
    Returns (success, status_message, report_date).
    """
    db = SessionLocal()
    try:
        # Check if employee is registered in system (case-insensitive fallback)
        employee = db.query(Employee).filter(Employee.name == employee_name).first()
        if not employee:
            employee = db.query(Employee).filter(Employee.name.ilike(employee_name.strip())).first()
            
        if not employee:
            return False, f"Employee '<b>{employee_name}</b>' is not registered. Please register them first using <code>/addemployee</code>.", ""
            
        # Update name to correct registered case/spelling
        employee_name = employee.name

        # Try to find today's report
        from datetime import timezone, timedelta, datetime
        tz_kh = timezone(timedelta(hours=7))
        today_str = datetime.now(tz_kh).strftime("%d-%b-%Y")

        report = db.query(Report).filter(Report.date == today_str).order_by(Report.id.desc()).first()
        if not report:
            # Fallback to the most recent report in the system
            report = db.query(Report).order_by(Report.id.desc()).first()

        if not report:
            return False, "⚠️ No reports found in the system. Please submit an attendance report first.", ""

        # Find employee's attendance record in this report
        record = db.query(AttendanceRecord).filter(
            AttendanceRecord.report_id == report.id,
            AttendanceRecord.employee_name == employee_name
        ).first()
        if not record:
            record = db.query(AttendanceRecord).filter(
                AttendanceRecord.report_id == report.id,
                AttendanceRecord.employee_name.ilike(employee_name.strip())
            ).first()

        if not record:
            report_day = extract_report_day(report.header)
            return False, f"⚠️ Employee '<b>{employee_name}</b>' is not in the attendance list for the report on date '<b>{report_day}</b>'.", ""

        # Clean old borrow/deduct entries from the note
        _, _, cleaned_note = parse_note_details(record.note)

        # Build new note
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
    except Exception as e:
        db.rollback()
        return False, f"⚠️ Database error: {str(e)}", ""
    finally:
        db.close()
