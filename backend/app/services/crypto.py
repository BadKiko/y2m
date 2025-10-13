from cryptography.fernet import Fernet, InvalidToken
from settings import settings


def _get_fernet() -> Fernet | None:
    if not settings.y2m_enc_key:
        return None
    key = settings.y2m_enc_key.encode()
    return Fernet(key)


def encrypt(text: str) -> str:
    f = _get_fernet()
    if not f:
        return text
    return f.encrypt(text.encode()).decode()


def decrypt(token: str) -> str:
    f = _get_fernet()
    if not f:
        return token
    try:
        return f.decrypt(token.encode()).decode()
    except InvalidToken:
        return token


