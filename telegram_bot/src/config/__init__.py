import os
import json
from pathlib import Path
from dotenv import load_dotenv
from cryptography.fernet import Fernet

class Config:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(Config, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # Load environment variables
        load_dotenv()
        
        # Base paths
        self.BASE_DIR = Path(__file__).parent.parent
        self.DATA_DIR = self.BASE_DIR / 'data'
        self.BACKUP_DIR = self.DATA_DIR / 'backups'
        
        # Create necessary directories
        self.DATA_DIR.mkdir(exist_ok=True)
        self.BACKUP_DIR.mkdir(exist_ok=True)
        
        # Bot configuration
        self.BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        self.MISTRAL_API_KEY = os.getenv('MISTRAL_API_KEY')
        self.AGENT_ID = os.getenv('AGENT_ID')
        
        # Database configuration
        self.DB_PATH = str(self.DATA_DIR / 'bot_data.db')
        self.DB_BACKUP_INTERVAL = 12  # hours
        self.DB_BACKUP_RETENTION = 15  # days
        
        # Encryption setup
        self._setup_encryption()
        
        # Load premium prices and user limits
        self._load_pricing()
        
    def _setup_encryption(self):
        key_file = self.DATA_DIR / 'encryption.key'
        if not key_file.exists():
            self.ENCRYPTION_KEY = Fernet.generate_key()
            key_file.write_bytes(self.ENCRYPTION_KEY)
        else:
            self.ENCRYPTION_KEY = key_file.read_bytes()
        self.cipher_suite = Fernet(self.ENCRYPTION_KEY)
        
    def _load_pricing(self):
        self.PREMIUM_PRICES = {
            "1_month": {"price": 10, "discount": 0},
            "3_months": {"price": 25, "discount": 15},
            "6_months": {"price": 45, "discount": 25},
            "12_months": {"price": 80, "discount": 35}
        }
        
        self.USER_LIMITS = {
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

    def encrypt_data(self, data: str) -> bytes:
        return self.cipher_suite.encrypt(data.encode())
        
    def decrypt_data(self, encrypted_data: bytes) -> str:
        return self.cipher_suite.decrypt(encrypted_data).decode()

# Create global instance
config = Config()

# Export configuration
__all__ = ['config']