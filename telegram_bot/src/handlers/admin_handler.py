from telebot import TeleBot, types
from datetime import datetime, timedelta
from typing import Dict, Optional
from ..config.settings import PREMIUM_PRICES, AUTHORIZED_USER_ID, ADMIN_USERNAME
from ..utils.database import Database
from ..utils.logger import Logger

def is_admin(message):
    return (
        message.from_user.id == AUTHORIZED_USER_ID or
        message.from_user.username == ADMIN_USERNAME.lstrip('@')
    )

class AdminHandler:
    def __init__(self, bot: TeleBot, db: Database, logger: Logger):
        self.bot = bot
        self.db = db
        self.logger = logger
        self.stealth_mode = False
        self._setup_handlers()

    def _setup_handlers(self):
        @self.bot.message_handler(commands=['admin'])
        def admin_panel(message):
            if not is_admin(message):
                self.bot.reply_to(message, "Unauthorized access.")
                return
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            buttons = [
                types.InlineKeyboardButton("User Management", callback_data="admin_users"),
                types.InlineKeyboardButton("Premium Control", callback_data="admin_premium"),
                types.InlineKeyboardButton("Group Management", callback_data="admin_groups"),
                types.InlineKeyboardButton("Set Discounts", callback_data="admin_discounts"),
                types.InlineKeyboardButton("Stealth Mode", callback_data="admin_stealth"),
                types.InlineKeyboardButton("View Logs", callback_data="admin_logs")
            ]
            markup.add(*buttons)
            self.bot.reply_to(message, "Admin Control Panel:", reply_markup=markup)

    def promote_to_premium(self, user_id: int, duration: str) -> bool:
        """
        Promote a user to premium status
        duration: '1_month', '3_months', '6_months', '12_months'
        """
        try:
            months_map = {
                '1_month': 1,
                '3_months': 3,
                '6_months': 6,
                '12_months': 12
            }
            
            months = months_map.get(duration)
            if not months:
                return False
                
            expiry_date = datetime.now() + timedelta(days=30*months)
            self.db.update_user_premium_status(user_id, True, expiry_date)
            self.logger.info(f"User {user_id} promoted to premium for {duration}")
            return True
        except Exception as e:
            self.logger.error(f"Error promoting user {user_id}: {str(e)}")
            return False

    def set_discount(self, duration: str, discount_percent: float) -> bool:
        """Set discount for a premium duration"""
        if duration not in PREMIUM_PRICES:
            return False
        try:
            PREMIUM_PRICES[duration]['discount'] = min(100, max(0, discount_percent))
            self.logger.info(f"Set {discount_percent}% discount for {duration}")
            return True
        except Exception as e:
            self.logger.error(f"Error setting discount: {str(e)}")
            return False

    def toggle_stealth_mode(self) -> bool:
        """Toggle admin stealth mode"""
        try:
            self.stealth_mode = not self.stealth_mode
            self.logger.info(f"Stealth mode {'enabled' if self.stealth_mode else 'disabled'}")
            return True
        except Exception as e:
            self.logger.error(f"Error toggling stealth mode: {str(e)}")
            return False

    def ban_user(self, user_id: int, reason: str) -> bool:
        """Ban a user from using the bot"""
        try:
            self.db.update_user_ban_status(user_id, True, reason)
            self.logger.warning(f"User {user_id} banned. Reason: {reason}")
            return True
        except Exception as e:
            self.logger.error(f"Error banning user {user_id}: {str(e)}")
            return False

    @property
    def is_stealth_mode(self) -> bool:
        return self.stealth_mode