import os
import sys
from pathlib import Path
import telebot
from telebot import types, TeleBot
from datetime import datetime

# Add project root to Python path
PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.append(str(PROJECT_ROOT))

# Set environment variable for config location
os.environ['BOT_CONFIG_DIR'] = str(PROJECT_ROOT / 'config')

# Import project modules
from config import config
from utils import utils
from handlers import HandlerFactory
from .config.settings import settings
from .handlers import AdminHandler, UserHandler
from .utils.database import Database
from .utils.logger import logger
from .config.settings import (
    BOT_TOKEN, 
    MISTRAL_API_KEY, 
    AGENT_ID, 
    AUTHORIZED_USER_ID, 
    ADMIN_USERNAME
)
from .handlers.admin_handler import AdminHandler
from .handlers.user_handler import UserHandler
from .utils import utils

# Create directory structure if doesn't exist
for dir_path in [
    PROJECT_ROOT / 'data',
    PROJECT_ROOT / 'data/logs',
    PROJECT_ROOT / 'data/backups',
    PROJECT_ROOT / 'config'
]:
    dir_path.mkdir(exist_ok=True)

def verify_credentials():
    required_vars = {
        "BOT_TOKEN": BOT_TOKEN,
        "MISTRAL_API_KEY": MISTRAL_API_KEY,
        "AGENT_ID": AGENT_ID,
        "AUTHORIZED_USER_ID": AUTHORIZED_USER_ID,
        "ADMIN_USERNAME": ADMIN_USERNAME
    }
    
    missing = [k for k, v in required_vars.items() if not v]
    if missing:
        utils.logger.error(f"Missing variables: {', '.join(missing)}")
        raise ValueError(f"Missing variables: {', '.join(missing)}")

def run_bot():
    try:
        verify_credentials()
        bot = TeleBot(BOT_TOKEN)
        
        # Initialize handlers
        admin_handler = AdminHandler(bot, utils.db, utils.logger)
        user_handler = UserHandler(bot, utils.db, utils.logger)
        
        utils.logger.info("Bot starting...")
        bot.polling(none_stop=True)
        
    except Exception as e:
        utils.logger.error(f"Bot crashed: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    run_bot()