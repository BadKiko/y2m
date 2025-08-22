import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

from app.core.config import settings

logger = logging.getLogger(__name__)

class EncryptionService:
    def __init__(self):
        self.key = self._derive_key(settings.ENCRYPTION_KEY)

    def _derive_key(self, password: str) -> bytes:
        """Derive encryption key from password"""
        salt = b'mqtt2yandex_salt'  # In production, use a proper salt
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=100000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(password.encode()))
        return key

    def encrypt(self, data: str) -> str:
        """Encrypt data"""
        try:
            f = Fernet(self.key)
            encrypted_data = f.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Encryption error: {e}")
            raise

    def decrypt(self, encrypted_data: str) -> str:
        """Decrypt data"""
        try:
            f = Fernet(self.key)
            decrypted_data = f.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption error: {e}")
            raise

# Global encryption service instance
encryption_service = EncryptionService()
