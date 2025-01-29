import sys
import os
from pathlib import Path
import pytest
from unittest.mock import MagicMock
from sqlalchemy import create_engine
from ..src.models import Base
from ..src.utils.database import Database

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.append(str(PROJECT_ROOT))

# Test configuration
TEST_CONFIG = {
    'DB_PATH': ':memory:',
    'BACKUP_DIR': PROJECT_ROOT / 'tests' / 'test_backups',
    'LOG_DIR': PROJECT_ROOT / 'tests' / 'test_logs'
}

# Mock objects
class MockBot(MagicMock):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.sent_messages = []

    def send_message(self, chat_id, text, **kwargs):
        self.sent_messages.append({
            'chat_id': chat_id,
            'text': text,
            'kwargs': kwargs
        })
        return True

@pytest.fixture
def mock_bot():
    return MockBot()

@pytest.fixture
def test_db():
    from ..src.utils.database import Database
    db = Database()
    db.engine = create_engine('sqlite:///:memory:')
    Base.metadata.create_all(db.engine)
    return db

@pytest.fixture
def test_user():
    return {
        'telegram_id': 123456789,
        'username': 'test_user',
        'first_name': 'Test',
        'last_name': 'User'
    }

# Export fixtures
__all__ = ['mock_bot', 'test_db', 'test_user', 'TEST_CONFIG']