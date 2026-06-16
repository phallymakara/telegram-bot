import os
import logging
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Khmer Font — cached locally so PDF generation works offline after first run
# ---------------------------------------------------------------------------
_FONTS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")
_FONT_PATH = os.path.join(_FONTS_DIR, "NotoSansKhmer-Regular.ttf")

_FONT_URLS = [
    # Noto Sans Khmer — best Khmer coverage from Google Fonts
    "https://fonts.gstatic.com/s/notosanskhmer/v18/ijw3s5roRME5LLRxjsRb-gssOmMaue_tpFE.ttf",
    # Fallback: Nokora
    "https://fonts.gstatic.com/s/nokora/v32/hESw6XVnNCxEvkbMpheEZo_H_w.ttf",
]

async def ensure_khmer_font_async() -> str:
    """Check if Khmer font is cached locally. Returns path to font or empty string."""
    if os.path.exists(_FONT_PATH):
        return _FONT_PATH
    return ""


def _ensure_khmer_font() -> str:
    """Check if Khmer font is cached locally. Returns path to font or empty string."""
    if os.path.exists(_FONT_PATH):
        return _FONT_PATH
    return ""


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def get_report_period_string(reports_data: list) -> str:
    if not reports_data:
        return "N/A"
    from database import extract_report_day
    start_day = extract_report_day(reports_data[0]['report'].header)
    end_day = extract_report_day(reports_data[-1]['report'].header)
    return start_day if start_day == end_day else f"{start_day}_to_{end_day}"


def aggregate_summary_data(reports_data: list) -> dict:
    summary = {}
    for data in reports_data:
        for record in data['records']:
            name = record.employee_name
            if name not in summary:
                summary[name] = {'hours': 0.0, 'salary': 0.0, 'rate': record.daily_rate}
            summary[name]['hours'] += record.hours
            summary[name]['salary'] += record.salary
            if record.daily_rate > 0:
                summary[name]['rate'] = record.daily_rate
    return summary


# ---------------------------------------------------------------------------
# Excel Report
# ---------------------------------------------------------------------------

def generate_excel_report(reports_data: list, output_path: str, exchange_rate: float = 4000.0):
    wb = Workbook()

    thin_border = Border(
        left=Side(style='thin', color='D3D3D3'),
        right=Side(style='thin', color='D3D3D3'),
        top=Side(style='thin', color='D3D3D3'),
        bottom=Side(style='thin', color='D3D3D3')
    )

    # ---- 1. Summary Sheet ----
    ws_summary = wb.active
    ws_summary.title = "Summary"

    ws_summary.merge_cells("A1:E1")
    ws_summary["A1"] = "សរុបប្រាក់ឈ្នួល និងវត្តមាន"
    ws_summary["A1"].font = Font(name="Times New Roman", size=16, bold=True, color="1F497D")
    ws_summary["A1"].alignment = Alignment(horizontal="center")

    ws_summary["A2"] = f"រយៈពេល: {get_report_period_string(reports_data)}"
    ws_summary["A2"].font = Font(name="Times New Roman", size=11, italic=True)

    headers_summary = [
        "ឈ្មោះបុគ្គលិក",
        "ម៉ោងការងារសរុប",
        "តម្លៃថ្ងៃ",
        "ប្រាក់ឈ្នួលសរុប (USD)",
        "ប្រាក់ឈ្នួលសរុប (KHR)"
    ]
    for col_idx, header in enumerate(headers_summary, 1):
        cell = ws_summary.cell(row=4, column=col_idx, value=header)
        cell.font = Font(name="Times New Roman", size=11, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    summary_data = aggregate_summary_data(reports_data)
    row_idx = 5
    for name, stats in sorted(summary_data.items()):
        ws_summary.cell(row=row_idx, column=1, value=name)
        ws_summary.cell(row=row_idx, column=2, value=stats['hours']).number_format = '#,##0.0'
        ws_summary.cell(row=row_idx, column=3, value=stats['rate']).number_format = '#,##0" ៛/ថ្ងៃ"'
        
        # USD Column (Column 4): Formula = E{row_idx} / exchange_rate
        usd_formula = f"=E{row_idx}/{exchange_rate}"
        ws_summary.cell(row=row_idx, column=4, value=usd_formula).number_format = '$#,##0.00'
        
        # KHR Column (Column 5): stats['salary']
        ws_summary.cell(row=row_idx, column=5, value=stats['salary']).number_format = '#,##0" ៛"'
        
        for c in range(1, 6):
            cell = ws_summary.cell(row=row_idx, column=c)
            cell.border = thin_border
            if c > 1:
                cell.font = Font(name="Times New Roman")
                cell.alignment = Alignment(horizontal="right")
            else:
                cell.font = Font(name="Times New Roman", bold=False)
        row_idx += 1

    ws_summary.cell(row=row_idx, column=1, value="សរុប").font = Font(name="Times New Roman", bold=True, size=11)
    ws_summary.cell(row=row_idx, column=2, value=f"=SUM(B5:B{row_idx-1})").font = Font(name="Times New Roman", bold=True)
    ws_summary.cell(row=row_idx, column=2).number_format = '#,##0.0'
    ws_summary.cell(row=row_idx, column=3).font = Font(name="Times New Roman", bold=True)
    ws_summary.cell(row=row_idx, column=4, value=f"=SUM(D5:D{row_idx-1})").font = Font(name="Times New Roman", bold=True)
    ws_summary.cell(row=row_idx, column=4).number_format = '$#,##0.00'
    ws_summary.cell(row=row_idx, column=5, value=f"=SUM(E5:E{row_idx-1})").font = Font(name="Times New Roman", bold=True)
    ws_summary.cell(row=row_idx, column=5).number_format = '#,##0" ៛"'
    
    double_bottom = Border(top=Side(style='thin', color='000000'), bottom=Side(style='double', color='000000'))
    for c in range(1, 6):
        cell = ws_summary.cell(row=row_idx, column=c)
        cell.border = double_bottom
        if c > 1:
            cell.alignment = Alignment(horizontal="right")

    for col in ws_summary.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_summary.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # ---- 2. Details Sheet ----
    ws_details = wb.create_sheet(title="Details")

    from database import extract_report_day, parse_date

    # Determine unique date columns from reports_data
    date_columns = []
    for item in reports_data:
        rep = item['report']
        day_str = extract_report_day(rep.header)
        d = parse_date(day_str)
        col_header = str(d.day) if d else day_str
        date_columns.append({
            'report_id': rep.id,
            'header': col_header,
            'full_date': day_str
        })

    total_columns_count = 5 + len(date_columns)
    last_col_letter = get_column_letter(total_columns_count)

    ws_details.merge_cells(f"A1:{last_col_letter}1")
    ws_details["A1"] = "ព័ត៌មានលម្អិតប្រចាំថ្ងៃ"
    ws_details["A1"].font = Font(name="Times New Roman", size=16, bold=True, color="1F497D")
    ws_details["A1"].alignment = Alignment(horizontal="center")

    headers_details = [
        "ល.រ",
        "ឈ្មោះបុគ្គលិក"
    ]
    for col in date_columns:
        headers_details.append(col['header'])
    headers_details.extend([
        "ម៉ោងសរុប",
        "ប្រាក់ត្រូវបើក (USD)",
        "ប្រាក់ត្រូវបើក (KHR)"
    ])

    for col_idx, header in enumerate(headers_details, 1):
        cell = ws_details.cell(row=3, column=col_idx, value=header)
        cell.font = Font(name="Times New Roman", size=10, bold=True, color="FFFFFF")
        cell.fill = PatternFill(start_color="4F81BD", end_color="4F81BD", fill_type="solid")
        cell.alignment = Alignment(horizontal="center", vertical="center", wrap_text=True)

    # Collect unique employee names
    employees = sorted(list(set(
        record.employee_name
        for item in reports_data
        for record in item['records']
    )))

    # Map hours and salary to (employee_name, report_id)
    hours_map = {}
    salary_map = {}
    for item in reports_data:
        rep_id = item['report'].id
        for record in item['records']:
            key = (record.employee_name, rep_id)
            hours_map[key] = hours_map.get(key, 0.0) + record.hours
            salary_map[key] = salary_map.get(key, 0.0) + record.salary

    det_row = 4
    for idx, name in enumerate(employees, 1):
        ws_details.cell(row=det_row, column=1, value=idx)
        ws_details.cell(row=det_row, column=2, value=name)

        for col_idx, date_col in enumerate(date_columns, 3):
            rep_id = date_col['report_id']
            hours = hours_map.get((name, rep_id), None)
            if hours is not None:
                ws_details.cell(row=det_row, column=col_idx, value=hours).number_format = '#,##0.0'
            else:
                ws_details.cell(row=det_row, column=col_idx, value="")

        total_hours_col = 3 + len(date_columns)
        first_date_col_letter = get_column_letter(3)
        last_date_col_letter = get_column_letter(total_hours_col - 1)

        hours_formula = f"=SUM({first_date_col_letter}{det_row}:{last_date_col_letter}{det_row})"
        ws_details.cell(row=det_row, column=total_hours_col, value=hours_formula).number_format = '#,##0.0'

        total_salary_usd_col = total_hours_col + 1
        total_salary_khr_col = total_hours_col + 2
        
        emp_salary_khr = sum(salary_map.get((name, col['report_id']), 0.0) for col in date_columns)
        ws_details.cell(row=det_row, column=total_salary_khr_col, value=emp_salary_khr).number_format = '#,##0" ៛"'

        khr_col_letter = get_column_letter(total_salary_khr_col)
        usd_formula = f"={khr_col_letter}{det_row}/{exchange_rate}"
        ws_details.cell(row=det_row, column=total_salary_usd_col, value=usd_formula).number_format = '$#,##0.00'

        for c in range(1, total_columns_count + 1):
            cell = ws_details.cell(row=det_row, column=c)
            cell.border = thin_border
            if c == 2:
                cell.font = Font(name="Times New Roman", bold=False)
            else:
                cell.font = Font(name="Times New Roman")
            if c == 1:
                cell.alignment = Alignment(horizontal="center")
            elif c == 2:
                cell.alignment = Alignment(horizontal="left")
            elif c >= 3:
                cell.alignment = Alignment(horizontal="right")

        det_row += 1

    # Total/Summary row at the bottom
    ws_details.cell(row=det_row, column=1, value="សរុប").font = Font(name="Times New Roman", bold=True, size=11)
    ws_details.cell(row=det_row, column=1).alignment = Alignment(horizontal="center")

    for col_idx in range(3, total_columns_count + 1):
        col_letter = get_column_letter(col_idx)
        sum_formula = f"=SUM({col_letter}4:{col_letter}{det_row-1})"
        cell = ws_details.cell(row=det_row, column=col_idx, value=sum_formula)
        cell.font = Font(name="Times New Roman", bold=True)
        if col_idx == total_salary_usd_col:
            cell.number_format = '$#,##0.00'
        elif col_idx == total_salary_khr_col:
            cell.number_format = '#,##0" ៛"'
        else:
            cell.number_format = '#,##0.0'

    double_bottom = Border(top=Side(style='thin', color='000000'), bottom=Side(style='double', color='000000'))
    for c in range(1, total_columns_count + 1):
        cell = ws_details.cell(row=det_row, column=c)
        cell.border = double_bottom
        if c <= 2:
            cell.font = Font(name="Times New Roman", bold=True, size=11)
        if c >= 3:
            cell.alignment = Alignment(horizontal="right")

    # Column Widths
    for col in ws_details.columns:
        col_idx = col[0].column
        if col_idx == 1:
            ws_details.column_dimensions[get_column_letter(col_idx)].width = 8
        elif col_idx == 2:
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws_details.column_dimensions[get_column_letter(col_idx)].width = max(max_len + 3, 20)
        elif 3 <= col_idx < total_hours_col:
            ws_details.column_dimensions[get_column_letter(col_idx)].width = 8
        else:
            ws_details.column_dimensions[get_column_letter(col_idx)].width = 16

    wb.save(output_path)


# ---------------------------------------------------------------------------
# PDF Report (WeasyPrint — proper Khmer shaping via Pango)
# ---------------------------------------------------------------------------

def _build_report_html(reports_data: list, period_str: str, font_path: str, exchange_rate: float = 4000.0) -> str:
    """Build a complete HTML document for the report."""
    summary_data = aggregate_summary_data(reports_data)
    total_hours = sum(v['hours'] for v in summary_data.values())
    total_salary = sum(v['salary'] for v in summary_data.values())

    # Font URI: use embedded base64 if file exists for guaranteed portability
    font_css = ""
    if font_path and os.path.exists(font_path):
        import base64
        with open(font_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("ascii")
        font_css = f"""@font-face {{
            font-family: 'KhmerFont';
            src: url('data:font/truetype;base64,{b64}');
        }}"""
    else:
        # If the downloaded font is missing, do NOT request external google fonts to prevent Playwright timeouts on offline servers
        font_css = ""

    # Summary table rows
    summary_rows = ""
    for i, (name, stats) in enumerate(sorted(summary_data.items()), 1):
        row_class = "even" if i % 2 == 0 else ""
        summary_rows += f"""
            <tr class="{row_class}">
                <td>{i}</td>
                <td class="name">{name}</td>
                <td class="num">{stats['hours']:.1f} ម៉ោង</td>
                <td class="num">{stats['rate']:,.0f} ៛/ថ្ងៃ</td>
                <td class="num">${stats['salary'] / exchange_rate:.2f}</td>
                <td class="num">{int(round(stats['salary'])):,} ៛</td>
            </tr>"""

    # Daily breakdown sections
    daily_sections = ""
    for day_data in reports_data:
        report = day_data['report']
        records = day_data['records']
        day_total_h = sum(r.hours for r in records)
        day_total_s = sum(r.salary for r in records)

        rows = ""
        for i, rec in enumerate(records, 1):
            row_class = "even" if i % 2 == 0 else ""
            rows += f"""
                <tr class="{row_class}">
                    <td class="center">{i}</td>
                    <td class="name">{rec.employee_name}</td>
                    <td class="num">{rec.hours:.1f} ម៉ោង</td>
                    <td class="num">{rec.daily_rate:,.0f} ៛/ថ្ងៃ</td>
                    <td class="num">${rec.salary / exchange_rate:.2f}</td>
                    <td class="num">{int(round(rec.salary)):,} ៛</td>
                    <td>{rec.note or ''}</td>
                </tr>"""

        daily_sections += f"""
            <div class="day-block">
                <h3>{report.header}</h3>
                <table>
                    <thead>
                        <tr>
                            <th style="width:30px">ល.រ</th>
                            <th>ឈ្មោះបុគ្គលិក</th>
                            <th class="num">ម៉ោងសរុប</th>
                            <th class="num">តម្លៃថ្ងៃ</th>
                            <th class="num">ប្រាក់ (USD)</th>
                            <th class="num">ប្រាក់ (រៀល)</th>
                            <th>សម្គាល់</th>
                        </tr>
                    </thead>
                    <tbody>{rows}</tbody>
                    <tfoot>
                        <tr class="subtotal">
                            <td colspan="2">សរុបថ្ងៃ</td>
                            <td class="num">{day_total_h:.1f} ម៉ោង</td>
                            <td></td>
                            <td class="num">${day_total_s / exchange_rate:.2f}</td>
                            <td class="num">{int(round(day_total_s)):,} ៛</td>
                            <td></td>
                        </tr>
                    </tfoot>
                </table>
            </div>"""

    display_period = period_str.replace("_to_", " ដល់ ")

    return f"""<!DOCTYPE html>
<html lang="km">
<head>
<meta charset="utf-8">
<title>របាយការណ៍វត្តមាន — {display_period}</title>
<style>
{font_css}

* {{ box-sizing: border-box; margin: 0; padding: 0; }}

body {{
    font-family: 'KhmerFont', 'Noto Sans Khmer', 'Khmer MN', 'Khmer Sangam MN', sans-serif;
    font-size: 10pt;
    color: #222;
    padding: 24px 28px;
    line-height: 1.5;
}}

/* ---- Header ---- */
.report-title {{
    text-align: center;
    margin-bottom: 4px;
}}
.report-title h1 {{
    font-size: 16pt;
    color: #1F497D;
    font-weight: bold;
}}
.report-title .period {{
    font-size: 10pt;
    color: #666;
    margin-top: 2px;
}}

/* ---- Section headings ---- */
h2 {{
    color: #366092;
    font-size: 12pt;
    margin: 18px 0 6px 0;
    padding-bottom: 3px;
    border-bottom: 2px solid #366092;
}}
h3 {{
    color: #4F81BD;
    font-size: 10pt;
    margin: 14px 0 4px 0;
}}

/* ---- Tables ---- */
table {{
    width: 100%;
    border-collapse: collapse;
    margin-bottom: 8px;
    font-size: 9.5pt;
}}
th {{
    background: #366092;
    color: #fff;
    padding: 5px 7px;
    font-weight: bold;
}}
.day-block table th {{
    background: #4F81BD;
}}
td {{
    padding: 4px 7px;
    border-bottom: 1px solid #e8e8e8;
}}
tr.even td {{ background: #F5F8FC; }}
tr.subtotal td {{
    background: #e2ecf4;
    font-weight: bold;
    border-top: 1.5px solid #366092;
}}

/* Summary total row */
tfoot.grand-total td {{
    background: #D9E5F0;
    font-weight: bold;
    border-top: 2px solid #1F497D;
    border-bottom: 2px solid #1F497D;
}}

/* Alignment helpers */
.num  {{ text-align: right; white-space: nowrap; }}
.name {{ min-width: 120px; }}
.center {{ text-align: center; }}

</style>
</head>
<body>

<div class="report-title">
    <h1>របាយការណ៍វត្តមាន និងប្រាក់ឈ្នួលបុគ្គលិក</h1>
    <p class="period">កាលបរិច្ឆេទ: {display_period}</p>
</div>

<h2>សរុបប្រាក់ឈ្នួល</h2>
<table>
    <thead>
        <tr>
            <th style="width:30px">ល.រ</th>
            <th>ឈ្មោះបុគ្គលិក</th>
            <th class="num">ម៉ោងសរុប</th>
            <th class="num">តម្លៃថ្ងៃ</th>
            <th class="num">ប្រាក់សរុប (USD)</th>
            <th class="num">ប្រាក់សរុប (រៀល)</th>
        </tr>
    </thead>
    <tbody>{summary_rows}</tbody>
    <tfoot class="grand-total">
        <tr>
            <td colspan="2">សរុប</td>
            <td class="num">{total_hours:.1f} ម៉ោង</td>
            <td></td>
            <td class="num">${total_salary / exchange_rate:.2f}</td>
            <td class="num">{int(round(total_salary)):,} ៛</td>
        </tr>
    </tfoot>
</table>

<h2>បំណែងចែកតាមថ្ងៃ</h2>
{daily_sections}

</body>
</html>"""


async def generate_pdf_report(reports_data: list, period_str: str, output_path: str, exchange_rate: float = 4000.0):
    """Generate a PDF report using Playwright (Chromium) for perfect Khmer text rendering.
    
    Playwright uses Chromium which has full HarfBuzz-based Khmer shaping.
    One-time setup: pip install playwright && playwright install chromium
    """
    try:
        from playwright.async_api import async_playwright
    except ImportError:
        raise RuntimeError(
            "playwright is not installed.\n"
            "Run:\n"
            "  pip install playwright\n"
            "  playwright install chromium"
        )

    font_path = await ensure_khmer_font_async()
    html_content = _build_report_html(reports_data, period_str, font_path, exchange_rate)

    logger.info(f"Generating PDF with Playwright: {output_path}")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu"
            ]
        )
        page = await browser.new_page()
        await page.set_content(html_content, wait_until="domcontentloaded")
        await page.pdf(
            path=output_path,
            format="A4",
            print_background=True,
            margin={"top": "15mm", "bottom": "15mm", "left": "15mm", "right": "15mm"},
        )
        await browser.close()
    logger.info("PDF report generated successfully.")





