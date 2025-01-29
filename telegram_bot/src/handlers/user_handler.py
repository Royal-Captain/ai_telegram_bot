import json
from telebot import TeleBot, types
from datetime import datetime, timedelta
from typing import Dict, Optional, List
from ..config.settings import USER_LIMITS, MAX_MESSAGES_PER_MINUTE
from ..utils.database import Database
from ..utils.logger import Logger

class UserHandler:
    def __init__(self, bot: TeleBot, db: Database, logger: Logger):
        self.bot = bot
        self.db = db
        self.logger = logger
        self.user_messages: Dict[int, List[datetime]] = {}  # Track message timestamps
        self.active_conversations: Dict[int, dict] = {}  # Track active conversations
        self.anonymous_users: set = set()  # Users in anonymous mode
        self._setup_handlers()

    def _setup_handlers(self):
        @self.bot.message_handler(commands=['start'])
        def start(message):
            try:
                markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
                markup.add(
                    types.KeyboardButton("New Chat"),
                    types.KeyboardButton("Settings"),
                    types.KeyboardButton("Saved Chats"),
                    types.KeyboardButton("Help")
                )
                
                welcome_text = "Welcome! How can I assist you today?"
                self.bot.reply_to(message, welcome_text, reply_markup=markup)
                
                if not self.db.user_exists(message.from_user.id):
                    user_data = {
                        'telegram_id': message.from_user.id,
                        'username': message.from_user.username,
                        'first_name': message.from_user.first_name,
                        'last_name': message.from_user.last_name
                    }
                    self.db.add_user(user_data)
                    
            except Exception as e:
                self.logger.error(f"Start command error: {str(e)}")
                self.bot.reply_to(message, "An error occurred. Please try again.")

        @self.bot.message_handler(func=lambda message: message.text in ["New Chat", "Settings", "Saved Chats", "Help"])
        def handle_buttons(message):
            try:
                if message.text == "New Chat":
                    self.bot.reply_to(message, "Starting a new chat. How can I help you?")
                elif message.text == "Settings":
                    self.show_settings(message)
                elif message.text == "Saved Chats":
                    self.show_saved_chats(message)
                elif message.text == "Help":
                    self.show_help(message)
            except Exception as e:
                self.logger.error(f"Button handler error: {str(e)}")
                self.bot.reply_to(message, "An error occurred. Please try again.")

    def show_settings(self, message):
        markup = types.InlineKeyboardMarkup()
        markup.add(
            types.InlineKeyboardButton("Language", callback_data="settings_language"),
            types.InlineKeyboardButton("Notifications", callback_data="settings_notifications")
        )
        self.bot.reply_to(message, "Settings Menu:", reply_markup=markup)

    def show_saved_chats(self, message):
        self.bot.reply_to(message, "Your saved chats will appear here.")

    def show_help(self, message):
        help_text = """
Available commands:
/start - Start the bot
/help - Show this help message
        
Button functions:
• New Chat - Start a new conversation
• Settings - Configure bot settings
• Saved Chats - View your chat history
• Help - Show help information
        """
        self.bot.reply_to(message, help_text)

    def register_user(self, user) -> bool:
        """Register new user in database"""
        try:
            user_data = {
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'joined_date': datetime.now(),
                'is_premium': False,
                'premium_expiry': None,
                'is_banned': False,
                'settings': json.dumps({
                    'anonymous_mode': False,
                    'ai_personality': 'friendly',
                    'language': 'en'
                })
            }
            self.db.add_user(user_data)
            self.logger.info(f"New user registered: {user.id}")
            return True
        except Exception as e:
            self.logger.error(f"User registration error: {str(e)}")
            return False

    def check_rate_limit(self, user_id: int) -> bool:
        """Check if user has exceeded rate limits"""
        current_time = datetime.now()
        if user_id not in self.user_messages:
            self.user_messages[user_id] = []
            
        # Remove messages older than 1 minute
        self.user_messages[user_id] = [
            msg_time for msg_time in self.user_messages[user_id]
            if current_time - msg_time < timedelta(minutes=1)
        ]
        
        # Check if user exceeded limit
        if len(self.user_messages[user_id]) >= MAX_MESSAGES_PER_MINUTE:
            return False
            
        self.user_messages[user_id].append(current_time)
        return True

    def start_conversation(self, user_id: int) -> bool:
        """Start new conversation for user"""
        try:
            limits = self.get_user_limits(user_id)
            if user_id in self.active_conversations:
                self.prompt_save_conversation(user_id)
                
            self.active_conversations[user_id] = {
                'messages': [],
                'started': datetime.now(),
                'message_count': 0
            }
            return True
        except Exception as e:
            self.logger.error(f"Error starting conversation: {str(e)}")
            return False

    def save_conversation(self, user_id: int, title: str = None) -> bool:
        """Save current conversation"""
        try:
            if user_id not in self.active_conversations:
                return False
                
            conversation = self.active_conversations[user_id]
            if not title:
                title = f"Chat {datetime.now().strftime('%Y-%m-%d %H:%M')}"
                
            self.db.save_conversation(user_id, title, conversation)
            del self.active_conversations[user_id]
            return True
        except Exception as e:
            self.logger.error(f"Error saving conversation: {str(e)}")
            return False

    def toggle_anonymous_mode(self, user_id: int) -> bool:
        """Toggle anonymous mode for user"""
        try:
            if user_id in self.anonymous_users:
                self.anonymous_users.remove(user_id)
            else:
                self.anonymous_users.add(user_id)
            
            settings = self.db.get_user_settings(user_id)
            settings['anonymous_mode'] = user_id in self.anonymous_users
            self.db.update_user_settings(user_id, settings)
            return True
        except Exception as e:
            self.logger.error(f"Error toggling anonymous mode: {str(e)}")
            return False

    def get_user_limits(self, user_id: int) -> dict:
        """Get user's current usage limits"""
        is_premium = self.db.is_premium_user(user_id)
        return USER_LIMITS['premium'] if is_premium else USER_LIMITS['normal']

    def prompt_save_conversation(self, user_id: int):
        """Prompt user to save current conversation"""
        markup = types.InlineKeyboardMarkup(row_width=2)
        buttons = [
            types.InlineKeyboardButton("Save", callback_data="save_chat"),
            types.InlineKeyboardButton("Discard", callback_data="discard_chat")
        ]
        markup.add(*buttons)
        
        self.bot.send_message(
            user_id,
            "Would you like to save the current conversation?",
            reply_markup=markup
        )

    def handle_message(self, message) -> bool:
        """Process incoming user message"""
        user_id = message.from_user.id
        
        if not self.check_rate_limit(user_id):
            self.bot.reply_to(message, "Please slow down! You're sending messages too quickly.")
            return False
            
        if user_id not in self.active_conversations:
            self.start_conversation(user_id)
            
        conv = self.active_conversations[user_id]
        limits = self.get_user_limits(user_id)
        
        if conv['message_count'] >= limits['messages_per_conv']:
            self.bot.reply_to(
                message,
                "You've reached the message limit for this conversation. "
                "Please start a new one."
            )
            return False
            
        conv['messages'].append({
            'role': 'user',
            'content': message.text,
            'timestamp': datetime.now().isoformat()
        })
        conv['message_count'] += 1
        
        return True