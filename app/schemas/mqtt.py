from typing import Optional, Dict, Any
from pydantic import BaseModel

class MQTTPublishRequest(BaseModel):
    topic: str
    payload: str
    qos: int = 0
    retain: bool = False

class MQTTMessage(BaseModel):
    topic: str
    payload: str
    timestamp: Optional[float] = None

class MQTTSubscribeRequest(BaseModel):
    topic: str
    qos: int = 0
