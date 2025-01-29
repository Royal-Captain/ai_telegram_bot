from telebot import TeleBot, types
from datetime import datetime, timedelta
import schedule
import threading
import time
from typing import Dict, List, Optional
from ..config.settings import AUTHORIZED_USER_ID
from ..utils.database import Database
from ..utils.logger import Logger
from ..models.user import User

class GroupHandler:
    def __init__(self, bot: TeleBot, db: Database, logger: Logger):
        self.bot = bot
        self.db = db
        self.logger = logger
        self.pending_groups: Dict[int, dict] = {}
        self.scheduled_posts: Dict[int, List[dict]] = {}
        self.warning_counts: Dict[int, Dict[int, int]] = {}  # {group_id: {user_id: warning_count}}
        self._setup_handlers()
        self._start_scheduler()

    def _setup_handlers(self):
        @self.bot.message_handler(func=lambda message: message.chat.type in ['group', 'supergroup'])
        def handle_group_message(message):
            if self._is_toxic_content(message.text):
                self.warn_user(message.chat.id, message.from_user.id, "Inappropriate content")
                self.bot.delete_message(message.chat.id, message.message_id)

        @self.bot.message_handler(commands=['schedule_post'])
        def schedule_post(message):
            if not self._is_admin(message.chat.id, message.from_user.id):
                return
            
            markup = types.InlineKeyboardMarkup(row_width=2)
            times = ["00:00", "06:00", "12:00", "18:00"]
            buttons = [types.InlineKeyboardButton(time, callback_data=f"schedule_{time}") 
                      for time in times]
            markup.add(*buttons)
            self.bot.reply_to(message, "Select posting time:", reply_markup=markup)

    def _start_scheduler(self):
        def run_scheduler():
            while True:
                schedule.run_pending()
                time.sleep(60)

        scheduler_thread = threading.Thread(target=run_scheduler)
        scheduler_thread.daemon = True
        scheduler_thread.start()

    def _is_toxic_content(self, text: str) -> bool:
        # AI-powered content moderation
        toxic_keywords = ['spam', 'abuse', 'hate']  # Basic implementation
        return any(keyword in text.lower() for keyword in toxic_keywords)

    def _is_admin(self, chat_id: int, user_id: int) -> bool:
        try:
            chat_member = self.bot.get_chat_member(chat_id, user_id)
            return chat_member.status in ['creator', 'administrator']
        except:
            return False

    def warn_user(self, chat_id: int, user_id: int, reason: str):
        if chat_id not in self.warning_counts:
            self.warning_counts[chat_id] = {}
        
        if user_id not in self.warning_counts[chat_id]:
            self.warning_counts[chat_id][user_id] = 0
        
        self.warning_counts[chat_id][user_id] += 1
        warnings = self.warning_counts[chat_id][user_id]
        
        warning_msg = f"⚠️ Warning {warnings}/3: {reason}"
        self.bot.send_message(chat_id, warning_msg)
        
        if warnings >= 3:
            self.mute_user(chat_id, user_id, duration=24)  # 24 hour mute
            self.warning_counts[chat_id][user_id] = 0

    def mute_user(self, chat_id: int, user_id: int, duration: int):
        until_date = datetime.now() + timedelta(hours=duration)
        try:
            self.bot.restrict_chat_member(
                chat_id, 
                user_id,
                until_date=until_date,
                permissions=types.ChatPermissions(
                    can_send_messages=False,
                    can_send_media_messages=False,
                    can_send_other_messages=False
                )
            )
            self.bot.send_message(
                chat_id,
                f"User has been muted for {duration} hours due to multiple warnings."
            )
            self.logger.warning(f"User {user_id} muted in group {chat_id}")
        except Exception as e:
            self.logger.error(f"Failed to mute user: {str(e)}")

    def schedule_group_post(self, chat_id: int, time: str, content: str):
        if chat_id not in self.scheduled_posts:
            self.scheduled_posts[chat_id] = []
        
        schedule.every().day.at(time).do(
            lambda: self.bot.send_message(chat_id, content)
        )
        
        self.scheduled_posts[chat_id].append({
            'time': time,
            'content': content
        })
        self.logger.info(f"Scheduled post for group {chat_id} at {time}")

    def verify_group_join(self, chat_id: int) -> bool:
        """Verify if the bot should join a group"""
        if chat_id in self.pending_groups:
            return False
            
        markup = types.InlineKeyboardMarkup()
        markup.row(
            types.InlineKeyboardButton("Approve", callback_data=f"approve_group_{chat_id}"),
            types.InlineKeyboardButton("Deny", callback_data=f"deny_group_{chat_id}")
        )
        
        self.bot.send_message(
            AUTHORIZED_USER_ID,
            f"Bot was added to group {chat_id}. Approve?",
            reply_markup=markup
        )
        
        self.pending_groups[chat_id] = {
            'status': 'pending',
            'timestamp': datetime.now()
        }
        return True

    def get_group_stats(self, chat_id: int) -> dict:
        """Get group activity statistics"""
        try:
            stats = {
                'member_count': self.bot.get_chat_member_count(chat_id),
                'warnings': len(self.warning_counts.get(chat_id, {})),
                'scheduled_posts': len(self.scheduled_posts.get(chat_id, [])),
            }
            return stats
        except Exception as e:
            self.logger.error(f"Failed to get group stats: {str(e)}")
            return {}

# Example of how to initialize the GroupHandler in main.py
# from src.handlers.group_handler import GroupHandler
# group_handler = GroupHandler(bot)
# bot.message_handler(func=lambda message: message.chat.type == 'group')(group_handler.handle_group_commands)