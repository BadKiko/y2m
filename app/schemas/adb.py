from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class ADBDeviceBase(BaseModel):
    name: str
    ip: str
    port: int = 5555

class ADBDeviceCreate(ADBDeviceBase):
    pass

class ADBDeviceUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    port: Optional[int] = None
    is_connected: Optional[bool] = None

class ADBDevice(ADBDeviceBase):
    id: int
    is_connected: bool
    last_seen: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class ADBCommand(BaseModel):
    device_id: int
    command: str
    timeout: int = 30

class ADBCommandResponse(BaseModel):
    success: bool
    output: str
    error: Optional[str] = None
    execution_time: float
