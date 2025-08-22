from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class YandexLoginRequest(BaseModel):
    username: str
    password: str

class YandexTokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    expires_in: int

class YandexAccount(BaseModel):
    id: int
    user: str
    expires_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class YandexAccountCreate(BaseModel):
    user: str
    refresh_token: str
    access_token: str
    expires_at: datetime
