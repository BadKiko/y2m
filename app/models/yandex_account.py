from sqlalchemy import Column, Integer, String, DateTime, Text
from sqlalchemy.sql import func

from app.core.database import Base

class YandexAccount(Base):
    __tablename__ = "yandex_accounts"

    id = Column(Integer, primary_key=True, index=True)
    user = Column(String, unique=True, index=True)
    refresh_token = Column(Text)  # Encrypted refresh token
    access_token = Column(Text)  # Encrypted access token
    expires_at = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
