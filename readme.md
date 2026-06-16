# Telegram Bot for Daily Attendance and Salary (Daily Rate)

A Telegram bot built in Python to automate the process of tracking daily worker attendance, computing daily-rate salaries (where 8 hours equals 1 working day, in both Khmer Riel and USD), and generating PDF and Excel reports. It utilizes an SQLite database via SQLAlchemy, automatic multi-day parsing, and Khmer font caching for local and server execution.

---

## Features

- **Employee Management:** Register, update, and bulk-import/delete employees with custom daily rates.
- **Smart Message Parser:** Paste raw attendance sheets directly into Telegram. The bot parses multi-day blocks, matches names (handling minor typos and trailing punctuation), and reads hours (e.g., `8h`, `8.9 h`, `8 h`) and notes.
- **Currency Conversion:** Instantly convert totals between Khmer Riel (KHR) and USD ($) using a configurable exchange rate.
- **Automated Reports:** Generate PDF and Excel (.xlsx) spreadsheets for custom date ranges, complete with formatted summaries, tables, and formula-calculated totals.
- **Automatic Backups:** Safeguard data by auto-exporting PDF and Excel files before performing database resets.
- **Khmer Unicode Support:** Full integration of Khmer character parsing, timezone configurations (Cambodia UTC+7), and dynamic Khmer fonts (Noto Sans Khmer) for report generation.

---

## Bot Commands

| Command | Arguments | Description |
| :--- | :--- | :--- |
| **`/start`** | None | Welcome message and initial greeting. |
| **`/help`** | None | View detailed usage guide and data formats. |
| **`/employees`** | None | List all registered employees, daily rates, and current exchange rate. |
| **`/addemployee`** | `<name> <daily_rate>` | Register or update an employee's daily rate (in Riel/day). |
| **`/addemployees`** | `<bulk_list>` | Register multiple employees at once (separated by newlines). |
| **`/updateemployee`** | `<old_name> -> <new_name>` | Change the name of a registered employee. |
| **`/deleteemployee`** | `<name>` | Remove an employee and their attendance records. |
| **`/deleteemployees`** | `<bulk_list>` | Bulk remove employees (separated by newlines). |
| **`/setexchange`** | `[rate]` | Set or view the exchange rate (e.g., `/setexchange 4100`). |
| **`/report_pdf`** | `[start_date] [end_date]` | Generate and download a PDF report for a range or single day (format: `DD.MM.YY`). |
| **`/report_excel`** | `[start_date] [end_date]` | Generate and download an Excel spreadsheet (format: `DD.MM.YY`). |
| **`/restartcount`** | None | Reset attendance records and reports. Prompts for confirmation and auto-exports backups first. |

---

## Attendance Sheet Formats

The parser extracts information by reading indices, employee names, decimal hours, and optional notes. 

### Single-Day Format Example
To record attendance for a single day, send a message with the following format:
```text
ថ្ងៃទី: 16.06.26 (7:00am - 5:00pm)
1. ប៉ែន ទិត្យ.   8 h
2. អៀម អេន.     8.9 h
3. ធិន        8.3 h
4. សួង សុង.     8 h (MEP)
5. គុន ឡុន   2.5 h
```
*Note: The first line is treated as the Day Header. Unregistered workers will show a warning indicator (Unregistered) and be computed with a default daily rate of 0 KHR until registered.*

### Multi-Day Format Example
You can send multiple day blocks in a single message. The parser automatically detects a new block whenever the index resets to 1 or is less than or equal to the previous line's index:
```text
ថ្ងៃទី: 15.06.26
1. ប៉ែន ទិត្យ.   8 h
2. អៀម អេន.     6 h

ថ្ងៃទី: 16.06.26
1. ប៉ែន ទិត្យ.   8 h
2. អៀម អេន.     8 h
3. ធិន        8.3 h
```

---

## Installation and Setup

Follow these steps to set up the Telegram Bot on your local machine or server.

### 1. Prerequisites
- **Python:** Python 3.10 or higher installed. Check your version with:
  ```bash
  python3 --version
  ```
- **SQLite:** Pre-installed on macOS/Linux. On Windows, ensure it is available if modifying DB files directly.
- **Git:** Installed on your system to clone the repository.

### 2. Clone the Repository
Clone the repository using Git:
```bash
git clone https://github.com/phallymakara/telegram-bot.git
cd telegram-bot
```

### 3. Set Up Virtual Environment
Create and activate a virtual Python environment to isolate project dependencies:
- **On macOS/Linux:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```
- **On Windows:**
  ```cmd
  python -m venv venv
  venv\Scripts\activate
  ```

### 4. Install Dependencies
Install all required Python packages listed in `requirements.txt`:
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 5. Install Playwright Browsers
This bot generates PDF reports using Playwright to ensure proper rendering of Khmer fonts and layout alignment. You must install the Playwright Chromium browser and its system dependencies:
- **On macOS/Windows/Linux:**
  ```bash
  playwright install chromium
  ```
- **On Linux (headless servers):**
  If running on a Linux server without a desktop environment, install the required system libraries:
  ```bash
  playwright install-deps chromium
  ```

### 6. Environment Configuration
Create a `.env` configuration file in the project root:
```bash
cp .env.example .env
```

Open the `.env` file using a text editor and enter your Telegram Bot Token. 

To get a token:
1. Message [@BotFather](https://t.me/BotFather) on Telegram.
2. Send the `/newbot` command and follow the prompts to name your bot and choose a username.
3. Copy the API token provided.

Configure `.env` as follows:
```env
BOT_TOKEN=your_telegram_bot_token_here
DATABASE_URL=sqlite:///attendance.db
```

### 7. Run Database Initializations
The database is automatically initialized and tables are created when the bot starts up. No manual migrations are required.

---

## Running the Bot

### Running Locally (Interactive Mode)
To run the bot in the terminal:
```bash
python3 bot.py
```
This is useful for debugging as log output will print directly to the console.

### Running in the Background (Linux/macOS)
To run the bot in the background so it continues running after you close the terminal session, use `nohup`:
```bash
nohup python3 bot.py > bot.log 2>&1 &
```
Log outputs will be written to `bot.log`. You can monitor execution by running:
```bash
tail -f bot.log
```

### Running as a systemd Service (Production)
For production servers, configure a systemd service to automatically start the bot on system boot and handle restarts if the process crashes.

1. Create a systemd service file:
   ```bash
   sudo nano /etc/systemd/system/telegram-bot.service
   ```
2. Paste the following configuration, replacing paths and user names with your actual setup:
   ```ini
   [Unit]
   Description=Telegram Attendance and Salary Bot
   After=network.target

   [Service]
   Type=simple
   User=your-username
   WorkingDirectory=/path/to/telegram-bot
   ExecStart=/path/to/telegram-bot/venv/bin/python bot.py
   Restart=always
   RestartSec=5
   Environment=PYTHONUNBUFFERED=1

   [Install]
   WantedBy=multi-user.target
   ```
3. Enable and start the service:
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable telegram-bot.service
   sudo systemctl start telegram-bot.service
   ```
4. Check the status of your bot service:
   ```bash
   sudo systemctl status telegram-bot.service
   ```

---

## Running Tests

The project includes test files under the unit and integration testing structures. Run them to verify your installation:

```bash
# Run all tests using Python discovery
python3 -m unittest discover -s .

# Run only the parser unit tests
python3 -m unittest test_parser_unit.py

# Run only the integration tests
python3 -m unittest test_integration.py
```

---

## Project Structure

```text
├── bot.py                # Main bot application, commands, handlers, and main loop
├── database.py           # SQLAlchemy database models, utility operations, and settings management
├── parser.py             # Regular expression parsing functions for single/multi-day reports
├── report_generator.py   # PDF (HTML to PDF layout) and Excel generation scripts
├── requirements.txt      # Project dependencies
├── fonts/                # Directory containing cached ttf fonts (NotoSansKhmer)
├── attendance.db         # SQLite production database (generated automatically)
├── test_parser_unit.py   # Parser unit tests
└── test_integration.py   # System integration tests
```

---

## License

This project is open-source and available under the MIT License.
