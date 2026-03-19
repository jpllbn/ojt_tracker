# OJT Tracker Bot

A Telegram bot that lets OJT (On-the-Job Training) students log their daily work hours and gives coordinators a single place to monitor compliance — no spreadsheets, no group-chat follow-ups.

## Prerequisites

- Python 3.11 or later
- A Telegram bot token from [@BotFather](https://t.me/BotFather)
- The coordinator's Telegram user ID (numeric)

## Getting started

1. Clone the repository:

   ```bash
   git clone https://github.com/<your-org>/ojt_tracker.git
   cd ojt_tracker
   ```

2. Create and activate a virtual environment:

   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file and fill in your values:

   ```bash
   cp .env.example .env
   ```

5. Start the bot:

   ```bash
   python -m bot
   ```

## Usage

### Student commands

| Command   | Description                                  |
|-----------|----------------------------------------------|
| `/start`  | Register your name and section (first time)  |
| `/timein` | Record the start of your shift               |
| `/timeout`| Record the end of your shift                 |
| `/status` | View hours rendered, required, and remaining |
| `/cancel` | Cancel the current operation                 |

### Coordinator commands

These commands are restricted to the Telegram user ID set in `COORDINATOR_CHAT_ID`.

| Command                  | Description                                      |
|--------------------------|--------------------------------------------------|
| `/report`                | List students who logged hours today             |
| `/missing`               | List students who have not logged today          |
| `/hours @studentname`    | View a specific student's full session log       |

> **Note:** `/timein`, `/timeout`, `/status`, and the coordinator commands are planned but not yet implemented. Only the `/start` registration flow is functional in the current build.

## Configuration

All configuration is read from environment variables. Copy `.env.example` to `.env` and set the values listed below.

| Variable             | Required | Default            | Description                                     |
|----------------------|----------|--------------------|-------------------------------------------------|
| `BOT_TOKEN`          | Yes      | —                  | Telegram bot token from @BotFather              |
| `COORDINATOR_CHAT_ID`| Yes      | —                  | Telegram user ID of the OJT coordinator         |
| `REQUIRED_HOURS`     | No       | `500`              | Total OJT hours each student must complete      |
| `DATABASE_PATH`      | No       | `ojt_tracker.db`   | Path to the SQLite database file                |

## Project structure

```
ojt_tracker/
├── bot/
│   ├── __init__.py
│   ├── __main__.py          # Entry point (python -m bot)
│   ├── config.py            # Environment variable loading
│   ├── db.py                # SQLite schema and data-access functions
│   ├── main.py              # Application setup and polling
│   └── handlers/
│       ├── __init__.py
│       ├── common.py        # Decorators (require_registration, coordinator_only) and unknown-command handler
│       └── start.py         # /start registration conversation
├── .env.example             # Template for environment variables
├── requirements.txt         # Python dependencies
└── README.md
```

## Database schema

The bot creates two tables on first run:

**students**

| Column          | Type    | Description                          |
|-----------------|---------|--------------------------------------|
| `telegram_id`   | INTEGER | Primary key — Telegram user ID       |
| `full_name`     | TEXT    | Student's registered name            |
| `section`       | TEXT    | Academic section (e.g. BSIT-3A)      |
| `required_hours`| REAL    | Total hours the student must render   |
| `created_at`    | TEXT    | ISO 8601 timestamp (PHT / UTC+8)    |

**time_logs**

| Column        | Type    | Description                                |
|---------------|---------|--------------------------------------------|
| `id`          | INTEGER | Auto-increment primary key                 |
| `telegram_id` | INTEGER | Foreign key → `students.telegram_id`       |
| `date`        | TEXT    | Log date (YYYY-MM-DD)                      |
| `time_in`     | TEXT    | ISO 8601 timestamp of shift start          |
| `time_out`    | TEXT    | ISO 8601 timestamp of shift end            |
| `hours`       | REAL    | Computed hours for the session             |
| `created_at`  | TEXT    | ISO 8601 timestamp (PHT / UTC+8)          |

## License

This project is not yet licensed. Add a `LICENSE` file before distributing.
