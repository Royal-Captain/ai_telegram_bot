from typing import Dict, Type
from telebot import TeleBot
from ..utils.database import Database
from ..utils.logger import Logger, logger
from ..config import config

# Import handlers
from .admin_handler import AdminHandler
from .user_handler import UserHandler
from .group_handler import GroupHandler
from .premium_handler import PremiumHandler

class HandlerFactory:
    _handlers: Dict[str, object] = {}
    
    @classmethod
    def initialize(cls, bot: TeleBot, db: Database, logger: Logger):
        """Initialize all handlers with dependencies"""
        cls._handlers = {
            'admin': AdminHandler(bot, db, logger),
            'user': UserHandler(bot, db, logger),
            'group': GroupHandler(bot, db, logger),
            'premium': PremiumHandler(bot, db, logger)
        }
    
    @classmethod
    def get_handler(cls, handler_type: str):
        """Get specific handler instance"""
        return cls._handlers.get(handler_type)
    
    @classmethod
    def get_all_handlers(cls):
        """Get all handler instances"""
        return cls._handlers.values()

# Export handlers and factory
__all__ = [
    'HandlerFactory',
    'AdminHandler',
    'UserHandler',
    'GroupHandler'
]