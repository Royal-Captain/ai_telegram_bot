from .database import Database
from .encryption import EncryptionManager
from .logger import Logger, logger
from ..config import config

class Utils:
    def __init__(self):
        self.logger = logger
        self.db = Database()
        
    def startup_check(self) -> bool:
        """Verify all utilities are properly initialized"""
        try:
            # Check database connection
            self.db.engine.connect()
            
            self.logger.info("Utilities initialized successfully")
            
            return True
        except Exception as e:
            print(f"Startup check failed: {str(e)}")
            return False

# Create global instance
utils = Utils()

# Export utilities
__all__ = [
    'utils',
    'Database',
    'Logger'
]