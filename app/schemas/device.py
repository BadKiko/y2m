from typing import Optional, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class DeviceBase(BaseModel):
    name: str
    type: str
    meta: Optional[Dict[str, Any]] = {}

class DeviceCreate(DeviceBase):
    pass

class DeviceUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    is_active: Optional[bool] = None
    meta: Optional[Dict[str, Any]] = None

class Device(DeviceBase):
    id: int
    mqtt_base_topic: str
    state_topic: str
    command_topic: str
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

class DeviceState(BaseModel):
    power: Optional[str] = None
    brightness: Optional[int] = None
    color: Optional[str] = None
    temperature: Optional[float] = None
    humidity: Optional[float] = None
    timestamp: Optional[datetime] = None
