import sqlite3
import schedule
import threading
import time
import zipfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional, List
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.pool import QueuePool
from ..models import Base, User, Conversation
from ..config import config
from .logger import logger

class Database:
    def __init__(self):
        self.engine = create_engine(
            f'sqlite:///{config.DB_PATH}',
            poolclass=QueuePool,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30
        )
        self.Session = scoped_session(sessionmaker(bind=self.engine))
        Base.metadata.create_all(self.engine)
        self._setup_backup_schedule()

    def _setup_backup_schedule(self):
        schedule.every(config.DB_BACKUP_INTERVAL).hours.do(self.create_backup)
        schedule.every().day.do(self.cleanup_old_backups)
        
        backup_thread = threading.Thread(target=self._run_schedule, daemon=True)
        backup_thread.start()

    def _run_schedule(self):
        while True:
            schedule.run_pending()
            time.sleep(60)

    def create_backup(self) -> bool:
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_path = config.BACKUP_DIR / f'backup_{timestamp}.db'
            
            # Create backup
            with sqlite3.connect(config.DB_PATH) as src, \
                 sqlite3.connect(str(backup_path)) as dst:
                src.backup(dst)
            
            # Compress backup
            zip_path = backup_path.with_suffix('.zip')
            with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(backup_path, arcname=backup_path.name)
            
            # Remove uncompressed backup
            backup_path.unlink()
            return True
            
        except Exception as e:
            logger.error(f"Backup creation failed: {str(e)}")
            return False

    def cleanup_old_backups(self):
        try:
            cutoff_date = datetime.now() - timedelta(days=config.DB_BACKUP_RETENTION)
            for backup_file in config.BACKUP_DIR.glob('backup_*.rar'):
                timestamp_str = backup_file.stem.split('_')[1]
                backup_date = datetime.strptime(timestamp_str, '%Y%m%d_%H%M%S')
                
                if backup_date < cutoff_date:
                    backup_file.unlink()
        except Exception as e:
            logger.error(f"Backup cleanup failed: {str(e)}")

    # User Operations
    def add_user(self, user_data: dict) -> bool:
        try:
            session = self.Session()
            user = User(**user_data)
            session.add(user)
            session.commit()
            return True
        except Exception as e:
            session.rollback()
            logger.error(f"User creation failed: {str(e)}")
            return False
        finally:
            session.close()

    def get_user(self, telegram_id: int) -> Optional[dict]:
        try:
            session = self.Session()
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            return user.to_dict() if user else None
        finally:
            session.close()

    def update_user(self, telegram_id: int, data: dict) -> bool:
        try:
            session = self.Session()
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                for key, value in data.items():
                    setattr(user, key, value)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"User update failed: {str(e)}")
            return False
        finally:
            session.close()

    def delete_user(self, telegram_id: int) -> bool:
        try:
            session = self.Session()
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                session.delete(user)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"User deletion failed: {str(e)}")
            return False
        finally:
            session.close()

    def user_exists(self, telegram_id: int) -> bool:
        """Check if user exists in database"""
        try:
            session = self.Session()
            exists = session.query(User).filter_by(telegram_id=telegram_id).first() is not None
            return exists
        except Exception as e:
            logger.error(f"Error checking user existence: {str(e)}")
            return False
        finally:
            session.close()

    # Premium Operations
    def update_premium_status(self, telegram_id: int, is_premium: bool, expiry_date: datetime) -> bool:
        try:
            session = self.Session()
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                user.is_premium = is_premium
                user.premium_expiry = expiry_date
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Premium status update failed: {str(e)}")
            return False
        finally:
            session.close()

    # Conversation Operations
    def save_conversation(self, telegram_id: int, title: str, conversation: dict) -> bool:
        try:
            session = self.Session()
            user = session.query(User).filter_by(telegram_id=telegram_id).first()
            if user:
                conv_data = {
                    'user_id': user.id,
                    'title': title,
                    'content': conversation,
                    'created_at': datetime.now()
                }
                conversation = Conversation(**conv_data)
                session.add(conversation)
                session.commit()
                return True
            return False
        except Exception as e:
            session.rollback()
            logger.error(f"Conversation save failed: {str(e)}")
            return False
        finally:
            session.close()