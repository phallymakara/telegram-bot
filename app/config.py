import os
from datetime import timezone, timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Telegram Bot Token
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Database URL
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///attendance.db")

# Allowed users
# Example in .env:
# ALLOWED_USERS=123456789,username1,username2
ALLOWED_USERS_RAW = os.getenv("ALLOWED_USERS", "")

ALLOWED_USERS = []
if ALLOWED_USERS_RAW:
    ALLOWED_USERS = [
        user.strip()
        for user in ALLOWED_USERS_RAW.split(",")
        if user.strip()
    ]

# Cambodia timezone
TZ_KH = timezone(timedelta(hours=7))

# Default exchange rate
DEFAULT_EXCHANGE_RATE = 4000.0


def is_user_allowed(user) -> bool:
    """
    Check if a Telegram user is allowed to use the bot.
    If ALLOWED_USERS is empty, everyone can use the bot.
    """
    if not ALLOWED_USERS:
        return True

    if not user:
        return False

    # Check Telegram numeric user ID
    if str(user.id) in ALLOWED_USERS:
        return True

    # Check Telegram username
    if user.username:
        allowed_lower = [u.lower() for u in ALLOWED_USERS]
        if user.username.lower() in allowed_lower:
            return True

    return False