from typing import Optional, List, Dict, Any
from pydantic import BaseModel
from datetime import datetime

class ActionBase(BaseModel):
    type: str  # mqtt_publish, yapi_call, adb_cmd, delay
    params: Dict[str, Any]

class ButtonScenarioBase(BaseModel):
    button_name: str
    name: str
    actions: List[ActionBase]

class ButtonScenarioCreate(ButtonScenarioBase):
    device_id: int

class ButtonScenarioUpdate(BaseModel):
    button_name: Optional[str] = None
    name: Optional[str] = None
    actions: Optional[List[ActionBase]] = None
    is_active: Optional[bool] = None

class ButtonScenario(ButtonScenarioBase):
    id: int
    device_id: int
    is_active: bool
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        orm_mode = True

# MQTT Action
class MQTTPublishAction(BaseModel):
    type: str = "mqtt_publish"
    params: Dict[str, Any]  # topic, payload

# YAPI Action
class YAPICallAction(BaseModel):
    type: str = "yapi_call"
    params: Dict[str, Any]  # command, target_station

# ADB Action
class ADBCommandAction(BaseModel):
    type: str = "adb_cmd"
    params: Dict[str, Any]  # device_id, command

# Delay Action
class DelayAction(BaseModel):
    type: str = "delay"
    params: Dict[str, Any]  # seconds
