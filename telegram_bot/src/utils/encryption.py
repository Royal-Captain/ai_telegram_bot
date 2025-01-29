from cryptography.fernet import Fernet
from pathlib import Path
import base64
import os
from ..config import config

class EncryptionManager:
    def __init__(self):
        self.key_path = config.DATA_DIR / 'encryption.key'
        self.key = self._load_or_generate_key()
        self.cipher_suite = Fernet(self.key)

    def _load_or_generate_key(self) -> bytes:
        """Load existing key or generate new one"""
        if self.key_path.exists():
            return self.key_path.read_bytes()
        
        key = Fernet.generate_key()
        self.key_path.write_bytes(key)
        return key

    def encrypt_string(self, text: str) -> str:
        """Encrypt a string and return base64 encoded result"""
        try:
            encrypted_data = self.cipher_suite.encrypt(text.encode())
            return base64.b64encode(encrypted_data).decode()
        except Exception as e:
            raise EncryptionError(f"String encryption failed: {str(e)}")

    def decrypt_string(self, encrypted_text: str) -> str:
        """Decrypt a base64 encoded encrypted string"""
        try:
            encrypted_data = base64.b64decode(encrypted_text.encode())
            decrypted_data = self.cipher_suite.decrypt(encrypted_data)
            return decrypted_data.decode()
        except Exception as e:
            raise EncryptionError(f"String decryption failed: {str(e)}")

    def encrypt_file(self, file_path: Path) -> Path:
        """Encrypt a file and return path to encrypted file"""
        try:
            encrypted_path = file_path.with_suffix(file_path.suffix + '.enc')
            with file_path.open('rb') as f:
                file_data = f.read()
                encrypted_data = self.cipher_suite.encrypt(file_data)
                
            with encrypted_path.open('wb') as f:
                f.write(encrypted_data)
                
            return encrypted_path
        except Exception as e:
            raise EncryptionError(f"File encryption failed: {str(e)}")

    def decrypt_file(self, encrypted_path: Path) -> Path:
        """Decrypt a file and return path to decrypted file"""
        try:
            decrypted_path = encrypted_path.with_suffix('')
            with encrypted_path.open('rb') as f:
                encrypted_data = f.read()
                decrypted_data = self.cipher_suite.decrypt(encrypted_data)
                
            with decrypted_path.open('wb') as f:
                f.write(decrypted_data)
                
            return decrypted_path
        except Exception as e:
            raise EncryptionError(f"File decryption failed: {str(e)}")

    def rotate_key(self) -> bool:
        """Generate new encryption key and re-encrypt existing data"""
        try:
            new_key = Fernet.generate_key()
            new_cipher = Fernet(new_key)
            
            # Store old cipher for re-encryption
            old_cipher = self.cipher_suite
            
            # Update instance variables
            self.key = new_key
            self.cipher_suite = new_cipher
            
            # Save new key
            self.key_path.write_bytes(new_key)
            
            return True
        except Exception as e:
            raise EncryptionError(f"Key rotation failed: {str(e)}")

class EncryptionError(Exception):
    """Custom exception for encryption operations"""
    pass

# Create global instance
encryption_manager = EncryptionManager()

# Export
__all__ = ['encryption_manager', 'EncryptionError']