import os
os.environ["DATABASE_URL"] = "sqlite:///test_attendance.db"
import unittest
from database import (
    init_db,
    add_employee,
    update_employee_name,
    delete_employee,
    get_employee_rate,
    get_all_employees,
    save_attendance_report,
    get_accumulated_totals,
    get_reports_by_dates,
    restart_attendance_count,
    Report,
    AttendanceRecord,
    SessionLocal,
    Base
)
from parser import parse_report_text_by_days
from report_generator import generate_excel_report, generate_pdf_report
from openpyxl import load_workbook

class TestIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        init_db()

    def setUp(self):
        # Clean up database tables before each test
        db = SessionLocal()
        try:
            db.execute(Base.metadata.tables['employees'].delete())
            db.execute(Base.metadata.tables['reports'].delete())
            db.execute(Base.metadata.tables['attendance'].delete())
            db.execute(Base.metadata.tables['settings'].delete())
            db.commit()
        finally:
            db.close()

    def test_employee_crud(self):
        # Add employee
        success = add_employee("ប៉ែន ទិត្យ", 10000)
        self.assertTrue(success)
        self.assertEqual(get_employee_rate("ប៉ែន ទិត្យ"), 10000)

        # Update employee rate
        success = add_employee("ប៉ែន ទិត្យ", 12000)
        self.assertTrue(success)
        self.assertEqual(get_employee_rate("ប៉ែន ទិត្យ"), 12000)

        # Rename employee
        success = update_employee_name("ប៉ែន ទិត្យ", "ប៉ែន ទិត្យថ្មី")
        self.assertTrue(success)
        self.assertIsNone(get_employee_rate("ប៉ែន ទិត្យ"))
        self.assertEqual(get_employee_rate("ប៉ែន ទិត្យថ្មី"), 12000)

        # Rename to already existing name (should fail)
        add_employee("អៀម អេន", 8000)
        success = update_employee_name("ប៉ែន ទិត្យថ្មី", "អៀម អេន")
        self.assertFalse(success)
        self.assertEqual(get_employee_rate("ប៉ែន ទិត្យថ្មី"), 12000)

        # List all
        all_emps = get_all_employees()
        self.assertEqual(len(all_emps), 2)
        self.assertEqual(all_emps["ប៉ែន ទិត្យថ្មី"], 12000)
        self.assertEqual(all_emps["អៀម អេន"], 8000)

        # Delete employee
        success = delete_employee("អៀម អេន")
        self.assertTrue(success)
        self.assertIsNone(get_employee_rate("អៀម អេន"))
        self.assertEqual(len(get_all_employees()), 1)

    def test_bulk_add_parsing_logic(self):
        content = """
        ប៉ែន ទិត្យ 10000
        អៀម អេន 8000
        """
        lines = content.split("\n")
        parsed = []
        for line in lines:
            cleaned = line.strip()
            if not cleaned:
                continue
            parts = cleaned.split()
            rate = float(parts[-1])
            name = " ".join(parts[:-1]).strip()
            add_employee(name, rate)
            parsed.append((name, rate))
            
        self.assertEqual(len(parsed), 2)
        self.assertEqual(parsed[0], ("ប៉ែន ទិត្យ", 10000.0))
        self.assertEqual(parsed[1], ("អៀម អេន", 8000.0))
        
        all_emps = get_all_employees()
        self.assertEqual(all_emps["ប៉ែន ទិត្យ"], 10000.0)
        self.assertEqual(all_emps["អៀម អេន"], 8000.0)

    def test_report_processing(self):
        # Register workers with hourly rates
        add_employee("ប៉ែន ទិត្យ", 10000) # 10000៛/h
        add_employee("អៀម អេន", 8000)   # 8000៛/h
        
        test_data = """
        1. ប៉ែន ទិត្យ.   8 h MEP
        2. អៀម អេន.     8.9 h
        3. ម៉ាច សិន 4 h
        """
        
        blocks = parse_report_text_by_days(test_data)
        self.assertEqual(len(blocks), 1)
        workers = blocks[0]['workers']
        self.assertEqual(len(workers), 3)
        
        results = {}
        for w in workers:
            name = w['name']
            hours = w['hours']
            
            hourly_rate = get_employee_rate(name)
            rate = hourly_rate if hourly_rate is not None else 0.0
            
            salary = hours * rate
            results[name] = {"hours": hours, "salary": salary}
            
        self.assertEqual(results["ប៉ែន ទិត្យ"]["hours"], 8.0)
        self.assertEqual(results["ប៉ែន ទិត្យ"]["salary"], 80000.0)
        self.assertEqual(results["អៀម អេន"]["hours"], 8.9)
        self.assertEqual(results["អៀម អេន"]["salary"], 71200.0)
        self.assertEqual(results["ម៉ាច សិន"]["hours"], 4.0)
        self.assertEqual(results["ម៉ាច សិន"]["salary"], 0.0)

    def test_multi_day_report_processing(self):
        add_employee("ប៉ែន ទិត្យ", 10000)
        add_employee("អៀម អេន", 8000)
        
        test_data = """
        Monday
        1. ប៉ែន ទិត្យ.   8 h MEP
        2. អៀម អេន.     8.9 h
        
        Tuesday
        1. ម៉ាច សិន 4 h
        2. ប៉ែន ទិត្យ.   8 h
        """
        
        blocks = parse_report_text_by_days(test_data)
        self.assertEqual(len(blocks), 2)
        
        worker_totals = {}
        for block in blocks:
            for w in block['workers']:
                name = w['name']
                hours = w['hours']
                
                hourly_rate = get_employee_rate(name)
                rate = hourly_rate if hourly_rate is not None else 0.0
                
                salary = hours * rate
                
                if name not in worker_totals:
                    worker_totals[name] = {'hours': 0.0, 'salary': 0.0}
                    
                worker_totals[name]['hours'] += hours
                worker_totals[name]['salary'] += salary
                
        self.assertEqual(worker_totals["ប៉ែន ទិត្យ"]["hours"], 16.0)
        self.assertEqual(worker_totals["ប៉ែន ទិត្យ"]["salary"], 160000.0)
        self.assertEqual(worker_totals["អៀម អេន"]["hours"], 8.9)
        self.assertEqual(worker_totals["អៀម អេន"]["salary"], 71200.0)
        self.assertEqual(worker_totals["ម៉ាច សិន"]["hours"], 4.0)
        self.assertEqual(worker_totals["ម៉ាច សិន"]["salary"], 0.0)

    def test_save_attendance_report_db(self):
        add_employee("ប៉ែន ទិត្យ", 10000)
        
        workers = [
            {'index': 1, 'name': "ប៉ែន ទិត្យ", 'hours': 8.0, 'note': "MEP"},
            {'index': 2, 'name': "ម៉ាច សិន", 'hours': 4.0, 'note': None}
        ]
        
        report_id = save_attendance_report("16-Jun-2026", "Monday", workers)
        self.assertIsNotNone(report_id)
        
        db = SessionLocal()
        try:
            report = db.query(Report).filter(Report.id == report_id).first()
            self.assertIsNotNone(report)
            self.assertEqual(report.date, "16-Jun-2026")
            self.assertEqual(report.header, "Monday")
            
            records = db.query(AttendanceRecord).filter(AttendanceRecord.report_id == report_id).all()
            self.assertEqual(len(records), 2)
            
            rec1 = next(r for r in records if r.employee_name == "ប៉ែន ទិត្យ")
            self.assertEqual(rec1.multiplier, 1.0)
            self.assertEqual(rec1.hours, 8.0)
            self.assertEqual(rec1.hourly_rate, 10000.0)
            self.assertEqual(rec1.salary, 80000.0)
            self.assertEqual(rec1.note, "MEP")
            
            rec2 = next(r for r in records if r.employee_name == "ម៉ាច សិន")
            self.assertEqual(rec2.multiplier, 0.5)
            self.assertEqual(rec2.hours, 4.0)
            self.assertEqual(rec2.hourly_rate, 0.0)
            self.assertEqual(rec2.salary, 0.0)
            self.assertIsNone(rec2.note)
        finally:
            db.close()

    def test_get_accumulated_totals(self):
        add_employee("ប៉ែន ទិត្យ", 10000)
        add_employee("អៀម អេន", 8000)
        
        workers1 = [
            {'index': 1, 'name': "ប៉ែន ទិត្យ", 'hours': 8.0, 'note': None},
            {'index': 2, 'name': "អៀម អេន", 'hours': 8.0, 'note': None}
        ]
        save_attendance_report("15-Jun-2026", "Monday", workers1)
        
        workers2 = [
            {'index': 1, 'name': "ប៉ែន ទិត្យ", 'hours': 4.0, 'note': None},
            {'index': 2, 'name': "អៀម អេន", 'hours': 10.0, 'note': None}
        ]
        save_attendance_report("16-Jun-2026", "Tuesday", workers2)
        
        totals = get_accumulated_totals()
        self.assertEqual(len(totals), 2)
        
        self.assertEqual(totals["ប៉ែន ទិត្យ"]["hours"], 12.0)
        self.assertEqual(totals["ប៉ែន ទិត្យ"]["salary"], 120000.0)
        self.assertEqual(totals["អៀម អេន"]["hours"], 18.0)
        self.assertEqual(totals["អៀម អេន"]["salary"], 144000.0)

    def test_report_overwrite_same_day(self):
        add_employee("ប៉ែន ទិត្យ", 10000)
        
        workers1 = [
            {'index': 1, 'name': "ប៉ែន ទិត្យ", 'hours': 8.0, 'note': None}
        ]
        id1 = save_attendance_report("16-Jun-2026", "ថ្ងៃទី: 16.06.26 (7:00am - 5:00pm)", workers1)
        
        workers2 = [
            {'index': 1, 'name': "ប៉ែន ទិត្យ", 'hours': 10.0, 'note': "Updated"}
        ]
        id2 = save_attendance_report("16-Jun-2026", "ថ្ងៃទី: 16.06.26 (8:00am - 6:00pm)", workers2)
        
        db = SessionLocal()
        try:
            reports = db.query(Report).all()
            self.assertEqual(len(reports), 1)
            self.assertEqual(reports[0].id, id2)
            self.assertEqual(reports[0].header, "ថ្ងៃទី: 16.06.26 (8:00am - 6:00pm)")
            
            records = db.query(AttendanceRecord).all()
            self.assertEqual(len(records), 1)
            self.assertEqual(records[0].report_id, id2)
            self.assertEqual(records[0].hours, 10.0)
            self.assertEqual(records[0].note, "Updated")
        finally:
            db.close()

    def test_generate_excel_layout(self):
        # Add employee
        add_employee("ប៉ែន ទិត្យ", 10000)
        add_employee("អៀម អេន", 8000)
        
        # Save two days of reports
        workers_day1 = [
            {'index': 1, 'name': "ប៉ែន ទិត្យ", 'hours': 8.0, 'note': "MEP"},
            {'index': 2, 'name': "អៀម អេន", 'hours': 7.5, 'note': None}
        ]
        save_attendance_report("01-Jun-2026", "ថ្ងៃទី: 1.06.26 (7:00am - 5:00pm)", workers_day1)
        
        workers_day2 = [
            {'index': 1, 'name': "ប៉ែន ទិត្យ", 'hours': 6.0, 'note': "Half day"},
        ]
        save_attendance_report("02-Jun-2026", "ថ្ងៃទី: 2.06.26", workers_day2)
        
        # Retrieve reports
        reports_data = get_reports_by_dates("1.06.26", "2.06.26")
        self.assertEqual(len(reports_data), 2)
        
        output_path = "tmp/test_report.xlsx"
        os.makedirs("tmp", exist_ok=True)
        if os.path.exists(output_path):
            os.remove(output_path)
            
        generate_excel_report(reports_data, output_path, 4000.0)
        
        self.assertTrue(os.path.exists(output_path))
        
        # Load workbook and check sheet contents
        wb = load_workbook(output_path)
        self.assertIn("Summary", wb.sheetnames)
        self.assertIn("Details", wb.sheetnames)
        
        ws = wb["Details"]
        
        # Check title
        self.assertEqual(ws["A1"].value, "ព័ត៌មានលម្អិតប្រចាំថ្ងៃ")
        
        # Check header row (row 3)
        headers = [ws.cell(row=3, column=col).value for col in range(1, 8)]
        self.assertEqual(headers[0], "ល.រ")
        self.assertEqual(headers[1], "ឈ្មោះបុគ្គលិក")
        self.assertEqual(headers[2], "1") # Day 1
        self.assertEqual(headers[3], "2") # Day 2
        self.assertEqual(headers[4], "ម៉ោងសរុប")
        self.assertEqual(headers[5], "ប្រាក់ត្រូវបើក (USD)")
        self.assertEqual(headers[6], "ប្រាក់ត្រូវបើក (KHR)")
        
        # Check employee names
        emp1_name = ws.cell(row=4, column=2).value
        emp2_name = ws.cell(row=5, column=2).value
        
        names = [emp1_name, emp2_name]
        self.assertIn("ប៉ែន ទិត្យ", names)
        self.assertIn("អៀម អេន", names)
        
        # Verify font and bold style for names and values
        self.assertEqual(ws.cell(row=4, column=2).font.name, "Times New Roman")
        self.assertFalse(ws.cell(row=4, column=2).font.bold)
        self.assertEqual(ws.cell(row=5, column=2).font.name, "Times New Roman")
        self.assertFalse(ws.cell(row=5, column=2).font.bold)
        
        self.assertEqual(ws.cell(row=4, column=3).font.name, "Times New Roman")
        
        pen_row = 4 if emp1_name == "ប៉ែន ទិត្យ" else 5
        iam_row = 5 if pen_row == 4 else 4
        
        # Check values
        self.assertEqual(ws.cell(row=pen_row, column=3).value, 8.0)
        self.assertEqual(ws.cell(row=pen_row, column=4).value, 6.0)
        self.assertEqual(ws.cell(row=pen_row, column=5).value, f"=SUM(C{pen_row}:D{pen_row})")
        self.assertEqual(ws.cell(row=pen_row, column=6).value, f"=G{pen_row}/4000.0")
        self.assertEqual(ws.cell(row=pen_row, column=7).value, 140000.0)
        
        self.assertEqual(ws.cell(row=iam_row, column=3).value, 7.5)
        self.assertIn(ws.cell(row=iam_row, column=4).value, [None, ""])
        self.assertEqual(ws.cell(row=iam_row, column=5).value, f"=SUM(C{iam_row}:D{iam_row})")
        self.assertEqual(ws.cell(row=iam_row, column=6).value, f"=G{iam_row}/4000.0")
        self.assertEqual(ws.cell(row=iam_row, column=7).value, 60000.0)
        
        # Total Row (row 6)
        self.assertEqual(ws.cell(row=6, column=1).value, "សរុប")
        self.assertEqual(ws.cell(row=6, column=3).value, "=SUM(C4:C5)")
        self.assertEqual(ws.cell(row=6, column=4).value, "=SUM(D4:D5)")
        self.assertEqual(ws.cell(row=6, column=5).value, "=SUM(E4:E5)")
        self.assertEqual(ws.cell(row=6, column=6).value, "=SUM(F4:F5)")
        self.assertEqual(ws.cell(row=6, column=7).value, "=SUM(G4:G5)")
 
        # Verify summary sheet font properties
        ws_sum = wb["Summary"]
        self.assertEqual(ws_sum["A1"].font.name, "Times New Roman")
        self.assertEqual(ws_sum["A2"].font.name, "Times New Roman")
        self.assertEqual(ws_sum.cell(row=4, column=1).font.name, "Times New Roman")
        self.assertEqual(ws_sum.cell(row=5, column=1).font.name, "Times New Roman")
        self.assertFalse(ws_sum.cell(row=5, column=1).font.bold)
        
        # Cleanup
        if os.path.exists(output_path):
            os.remove(output_path)

    def test_generate_pdf_layout(self):
        if os.getenv("SKIP_PDF_TEST"):
            raise unittest.SkipTest("Skipping PDF test in sandbox environment")
        import asyncio
        add_employee("ប៉ែន ទិត្យ", 10000)
        
        workers = [{'index': 1, 'name': "ប៉ែន ទិត្យ", 'hours': 8.0, 'note': "MEP"}]
        save_attendance_report("15-Jun-2026", "ថ្ងៃទី: 15.06.26", workers)
        
        reports_data = get_reports_by_dates("15.06.26", "15.06.26")
        output_path = "tmp/test_report.pdf"
        os.makedirs("tmp", exist_ok=True)
        if os.path.exists(output_path):
            os.remove(output_path)
            
        asyncio.run(generate_pdf_report(reports_data, "15.06.26", output_path, 4000.0))
        self.assertTrue(os.path.exists(output_path))
        if os.path.exists(output_path):
            os.remove(output_path)

    def test_exchange_rate_crud(self):
        from database import get_exchange_rate, set_exchange_rate
        # Default rate should be 4000
        self.assertEqual(get_exchange_rate(), 4000.0)

        # Set new rate
        set_exchange_rate(4100.0)
        self.assertEqual(get_exchange_rate(), 4100.0)

        # Reset rate
        set_exchange_rate(4000.0)

    def test_employee_cascade_sync(self):
        # 1. Add employee
        add_employee("ប៉ែន ទិត្យ", 10000)
        
        # 2. Add attendance record for employee
        workers = [
            {'index': 1, 'name': "ប៉ែន ទិត្យ", 'hours': 8.0, 'note': "Test"}
        ]
        save_attendance_report("16-Jun-2026", "Monday", workers)
        
        # Verify it has KHR rate and 80000 salary
        db = SessionLocal()
        try:
            rec = db.query(AttendanceRecord).filter(AttendanceRecord.employee_name == "ប៉ែន ទិត្យ").first()
            self.assertEqual(rec.hourly_rate, 10000.0)
            self.assertEqual(rec.salary, 80000.0)
        finally:
            db.close()
            
        # 3. Update hourly rate of employee
        add_employee("ប៉ែន ទិត្យ", 12000)
        
        # Verify attendance record updated
        db = SessionLocal()
        try:
            rec = db.query(AttendanceRecord).filter(AttendanceRecord.employee_name == "ប៉ែន ទិត្យ").first()
            self.assertEqual(rec.hourly_rate, 12000.0)
            self.assertEqual(rec.salary, 96000.0)
        finally:
            db.close()

        # 4. Rename employee
        update_employee_name("ប៉ែន ទិត្យ", "ប៉ែន ទិត្យថ្មី")
        
        # Verify attendance record name is renamed
        db = SessionLocal()
        try:
            rec_old = db.query(AttendanceRecord).filter(AttendanceRecord.employee_name == "ប៉ែន ទិត្យ").first()
            rec_new = db.query(AttendanceRecord).filter(AttendanceRecord.employee_name == "ប៉ែន ទិត្យថ្មី").first()
            self.assertIsNone(rec_old)
            self.assertIsNotNone(rec_new)
            self.assertEqual(rec_new.hourly_rate, 12000.0)
        finally:
            db.close()

        # 5. Delete employee
        delete_employee("ប៉ែន ទិត្យថ្មី")
        
        # Verify attendance record is deleted
        db = SessionLocal()
        try:
            rec = db.query(AttendanceRecord).filter(AttendanceRecord.employee_name == "ប៉ែន ទិត្យថ្មី").first()
            self.assertIsNone(rec)
        finally:
            db.close()

    def test_bulk_delete_logic(self):
        add_employee("ប៉ែន ទិត្យ", 10000)
        add_employee("អៀម អេន", 8000)
        
        # Verify they exist
        self.assertEqual(len(get_all_employees()), 2)
        
        # Bulk delete
        names_to_delete = ["ប៉ែន ទិត្យ", "អៀម អេន", "ម៉ាច សិន"]
        deleted = []
        for name in names_to_delete:
            if delete_employee(name):
                deleted.append(name)
                
        self.assertEqual(len(deleted), 2)
        self.assertIn("ប៉ែន ទិត្យ", deleted)
        self.assertIn("អៀម អេន", deleted)
        self.assertEqual(len(get_all_employees()), 0)

    def test_restart_attendance_count(self):
        # 1. Add employee (this should NOT be deleted)
        add_employee("ប៉ែន ទិត្យ", 10000)
        
        # 2. Add attendance reports (these SHOULD be deleted)
        workers = [
            {'index': 1, 'name': "ប៉ែន ទិត្យ", 'hours': 8.0, 'note': "Test"}
        ]
        save_attendance_report("16-Jun-2026", "Monday", workers)
        
        # Verify db has records and reports
        db = SessionLocal()
        try:
            self.assertEqual(db.query(Report).count(), 1)
            self.assertEqual(db.query(AttendanceRecord).count(), 1)
            self.assertEqual(len(get_all_employees()), 1)
        finally:
            db.close()
            
        # 3. Call restart_attendance_count
        success = restart_attendance_count()
        self.assertTrue(success)
        
        # Verify reports and attendance are empty, but employee remains
        db = SessionLocal()
        try:
            self.assertEqual(db.query(Report).count(), 0)
            self.assertEqual(db.query(AttendanceRecord).count(), 0)
            self.assertEqual(len(get_all_employees()), 1)
        finally:
            db.close()

if __name__ == '__main__':
    unittest.main()
