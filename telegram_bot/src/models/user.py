from sqlalchemy import Column, Integer, String, Boolean, DateTime, JSON, ForeignKey
from sqlalchemy.orm import relationship
from datetime import datetime
from . import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String(255))
    first_name = Column(String(255))
    last_name = Column(String(255))
    joined_date = Column(DateTime, default=datetime.utcnow)
    
    # Premium related
    is_premium = Column(Boolean, default=False)
    premium_expiry = Column(DateTime, nullable=True)
    referral_count = Column(Integer, default=0)
    
    # Status flags
    is_banned = Column(Boolean, default=False)
    ban_reason = Column(String(500), nullable=True)
    is_admin = Column(Boolean, default=False)
    
    # Usage tracking
    message_count = Column(Integer, default=0)
    conversation_count = Column(Integer, default=0)
    last_activity = Column(DateTime, default=datetime.utcnow)
    
    # Settings and preferences
    settings = Column(JSON, default={})
    
    # Relationships
    conversations = relationship("Conversation", back_populates="user")
    # Remove Payment relationship until Payment model is created
    # payments = relationship("Payment", back_populates="user")
    
    def __init__(self, telegram_id, username=None, first_name=None, last_name=None):
        self.telegram_id = telegram_id
        self.username = username
        self.first_name = first_name
        self.last_name = last_name

    def is_premium_active(self) -> bool:
        """Check if user has active premium subscription"""
        if not self.is_premium:
            return False
        return self.premium_expiry and self.premium_expiry > datetime.utcnow()

    def get_remaining_messages(self) -> int:
        """Get remaining messages for current period"""
        from ..config.settings import USER_LIMITS
        limits = USER_LIMITS['premium'] if self.is_premium_active() else USER_LIMITS['normal']
        return limits['messages_per_conv'] - self.message_count

    def update_settings(self, new_settings: dict) -> bool:
        """Update user settings"""
        try:
            self.settings.update(new_settings)
            return True
        except Exception:
            return False

    def add_referral(self) -> bool:
        """Increment referral count"""
        try:
            self.referral_count += 1
            return True
        except Exception:
            return False

    def record_activity(self):
        """Update last activity timestamp"""
        self.last_activity = datetime.utcnow()
        self.message_count += 1

    def reset_usage_stats(self):
        """Reset usage statistics for new period"""
        self.message_count = 0
        self.conversation_count = 0

    @property
    def full_name(self) -> str:
        """Get user's full name"""
        return f"{self.first_name or ''} {self.last_name or ''}".strip()

    def to_dict(self) -> dict:
        """Convert user object to dictionary"""
        return {
            'id': self.id,
            'telegram_id': self.telegram_id,
            'username': self.username,
            'full_name': self.full_name,
            'is_premium': self.is_premium_active(),
            'premium_expiry': self.premium_expiry.isoformat() if self.premium_expiry else None,
            'referral_count': self.referral_count,
            'joined_date': self.joined_date.isoformat(),
            'last_activity': self.last_activity.isoformat(),
            'settings': self.settings
        }