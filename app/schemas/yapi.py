from typing import Optional, Dict, Any
from pydantic import BaseModel

class YAPIExecuteRequest(BaseModel):
    command: str
    target_station: Optional[str] = None
    params: Optional[Dict[str, Any]] = None

class YAPIResponse(BaseModel):
    success: bool
    response: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    execution_time: float
