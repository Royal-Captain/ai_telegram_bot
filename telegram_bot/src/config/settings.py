import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
load_dotenv()

# Bot configuration
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
AGENT_ID = os.getenv("AGENT_ID")
AUTHORIZED_USER_ID = int(os.getenv("AUTHORIZED_USER_ID", "1242077717"))
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "@royalcaptain")

# Premium pricing (in TON)
PREMIUM_PRICES = {
    "1_month": {"price": 10, "discount": 0},
    "3_months": {"price": 25, "discount": 15},  # 15% off
    "6_months": {"price": 45, "discount": 25},  # 25% off
    "12_months": {"price": 80, "discount": 35}  # 35% off
}

# User limits
USER_LIMITS = {
    "normal": {
        "messages_per_conv": 15,
        "convs_per_week": 20,
        "saved_convs": 5
    },
    "premium": {
        "messages_per_conv": float('inf'),
        "convs_per_week": 100,
        "saved_convs": 20
    }
}

# Database settings
DB_FILE = "bot_data.db"
BACKUP_INTERVAL_HOURS = 12
BACKUP_RETENTION_DAYS = 15
BACKUP_PASSWORD = "@Sxw2z4ab7fkj"

# Rate limiting
MAX_MESSAGES_PER_MINUTE = 60
COMMAND_COOLDOWN_SECONDS = 30

# Logging settings
LOGGING_LEVEL = os.getenv("LOGGING_LEVEL", "INFO")
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/bot.log")