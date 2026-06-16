import unittest
from parser import parse_report_line, parse_report_text, parse_report_text_by_days

class TestParser(unittest.TestCase):
    def test_standard_line(self):
        line = "1. ប៉ែន ទិត្យ.   8 h MEP"
        parsed = parse_report_line(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['index'], 1)
        self.assertEqual(parsed['name'], "ប៉ែន ទិត្យ")
        self.assertEqual(parsed['hours'], 8.0)
        self.assertEqual(parsed['note'], "MEP")

    def test_line_no_note(self):
        line = "2. អៀម អេន.     8.9 h"
        parsed = parse_report_line(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['index'], 2)
        self.assertEqual(parsed['name'], "អៀម អេន")
        self.assertEqual(parsed['hours'], 8.9)
        self.assertIsNone(parsed['note'])

    def test_line_with_spaces_in_hours(self):
        line = "3. ធិន        8.3 h "
        parsed = parse_report_line(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['index'], 3)
        self.assertEqual(parsed['name'], "ធិន")
        self.assertEqual(parsed['hours'], 8.3)

    def test_line_tight_hours(self):
        line = "4. សួង សុង 8h"
        parsed = parse_report_line(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['index'], 4)
        self.assertEqual(parsed['name'], "សួង សុង")
        self.assertEqual(parsed['hours'], 8.0)

    def test_line_with_trailing_colon(self):
        line = "1. ប៉ែន ទិត្យ: 8 h"
        parsed = parse_report_line(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['name'], "ប៉ែន ទិត្យ")
        self.assertEqual(parsed['hours'], 8.0)

    def test_line_with_decimal_hours(self):
        line = "6. ម៉ាច សិន 2.5 h"
        parsed = parse_report_line(line)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed['index'], 6)
        self.assertEqual(parsed['name'], "ម៉ាច សិន")
        self.assertEqual(parsed['hours'], 2.5)

    def test_non_attendance_line(self):
        line = "Hello world this is not a report line"
        parsed = parse_report_line(line)
        self.assertIsNone(parsed)

    def test_full_text(self):
        text = """
        Some header info
        1. ប៉ែន ទិត្យ.   8 h MEP
        2. អៀម អេន.     8.9 h
        6. ម៉ាច សិន 2.5 h
        
        Some footer info
        """
        results = parse_report_text(text)
        self.assertEqual(len(results), 3)
        self.assertEqual(results[0]['name'], "ប៉ែន ទិត្យ")
        self.assertEqual(results[1]['name'], "អៀម អេន")
        self.assertEqual(results[2]['name'], "ម៉ាច សិន")
        self.assertEqual(results[2]['hours'], 2.5)

    def test_parse_by_days_single(self):
        text = """
        1. ប៉ែន ទិត្យ.   8 h MEP
        2. អៀម អេន.     8.9 h
        """
        blocks = parse_report_text_by_days(text)
        self.assertEqual(len(blocks), 1)
        self.assertEqual(blocks[0]['header'], "Day 1")
        self.assertEqual(len(blocks[0]['workers']), 2)
        self.assertEqual(blocks[0]['workers'][0]['name'], "ប៉ែន ទិត្យ")

    def test_parse_by_days_multiple_with_headers(self):
        text = """
        Monday
        1. ប៉ែន ទិត្យ.   8 h
        2. អៀម អេន.     8.9 h
        
        Tuesday
        1. ម៉ាច សិន 2.5 h
        2. ប៉ែន ទិត្យ.   8 h
        """
        blocks = parse_report_text_by_days(text)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]['header'], "Monday")
        self.assertEqual(blocks[1]['header'], "Tuesday")
        self.assertEqual(len(blocks[0]['workers']), 2)
        self.assertEqual(len(blocks[1]['workers']), 2)

    def test_parse_by_days_multiple_no_headers(self):
        text = """
        1. ប៉ែន ទិត្យ.   8 h
        2. អៀម អេន.     8.9 h
        
        1. ប៉ែន ទិត្យ.   8 h
        2. អៀម អេន.     8.9 h
        """
        blocks = parse_report_text_by_days(text)
        self.assertEqual(len(blocks), 2)
        self.assertEqual(blocks[0]['header'], "Day 1")
        self.assertEqual(blocks[1]['header'], "Day 2")

    def test_parse_header_date_time(self):
        from bot import parse_header_date_time
        
        # Test Khmer date patterns with time range
        d, t = parse_header_date_time("ថ្ងៃទី: 20.06.26 (07:00 AM - 05:00 PM)")
        self.assertEqual(d, "20.06.26")
        self.assertEqual(t, "07:00 AM - 05:00 PM")
        
        d, t = parse_header_date_time("ងៃទី: 20.06.26 (7:00am - 5:00pm)")
        self.assertEqual(d, "20.06.26")
        self.assertEqual(t, "7:00am - 5:00pm")

        # Test patterns without time range
        d, t = parse_header_date_time("ថ្ងៃទី: 20.06.26")
        self.assertEqual(d, "20.06.26")
        self.assertIsNone(t)

        # Test standard text header fallback
        d, t = parse_header_date_time("Monday")
        self.assertEqual(d, "Monday")
        self.assertIsNone(t)

if __name__ == '__main__':
    unittest.main()
