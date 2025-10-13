from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

# For MVP we mimic yapi-like contract locally


router = APIRouter(prefix="/api/station", tags=["station"])


class StationCommand(BaseModel):
    deviceId: str
    command: str
    text: str | None = None
    volume: float | None = None
    position: int | None = None


@router.post("")
async def station_command(body: StationCommand):
    # Placeholder: integrate real LAN protocol later; for now we accept and return ok
    return {"ok": True, "echo": body.model_dump()}


