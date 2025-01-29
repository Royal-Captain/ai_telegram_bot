import logging
from logging.handlers import RotatingFileHandler
import json
from datetime import datetime
from pathlib import Path
from ..config import config

class Logger:
    def __init__(self):
        # Setup logging directory
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        
        # Initialize loggers
        self.bot_logger = self._setup_logger('bot', 'bot.log')
        self.user_logger = self._setup_logger('user', 'user.log')
        self.error_logger = self._setup_logger('error', 'error.log')
        self.admin_logger = self._setup_logger('admin', 'admin.log')

    def _setup_logger(self, name: str, filename: str) -> logging.Logger:
        logger = logging.getLogger(name)
        logger.setLevel(logging.INFO)

        # Create handlers
        file_handler = RotatingFileHandler(
            self.log_dir / filename,
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        console_handler = logging.StreamHandler()
        
        # Create formatters and add it to handlers
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        # Add handlers to the logger
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        return logger

    def info(self, message: str):
        """Log info level message"""
        self.bot_logger.info(message)

    def error(self, message: str):
        """Log error level message"""
        self.error_logger.error(message)

    def warning(self, message: str):
        """Log warning message"""
        self.bot_logger.warning(message)

    def user_action(self, user_id: int, action: str, data: dict = None):
        """Log user action"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'user_id': user_id,
            'action': action,
            'data': data or {}
        }
        self.user_logger.info(json.dumps(log_data))

    def admin_action(self, admin_id: int, action: str, data: dict = None):
        """Log admin action"""
        log_data = {
            'timestamp': datetime.now().isoformat(),
            'admin_id': admin_id,
            'action': action,
            'data': data or {}
        }
        self.admin_logger.info(json.dumps(log_data))

# Create global instance
logger = Logger()

# Export both class and instance
__all__ = ['Logger', 'logger']