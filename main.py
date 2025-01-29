import os
import sys
from pathlib import Path
from telebot import TeleBot  # Add this import

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

from telegram_bot.src.config.settings import BOT_TOKEN
from telegram_bot.src.handlers.admin_handler import AdminHandler
from telegram_bot.src.handlers.user_handler import UserHandler
from telegram_bot.src.utils import utils

def main():
    try:
        bot = TeleBot(BOT_TOKEN, parse_mode=None)
        
        # Initialize handlers
        admin_handler = AdminHandler(bot, utils.db, utils.logger)
        user_handler = UserHandler(bot, utils.db, utils.logger)
        
        utils.logger.info("Bot starting...")
        bot.infinity_polling(timeout=60)
        
    except Exception as e:
        utils.logger.error(f"Bot crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()