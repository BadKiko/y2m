from fastapi import APIRouter, HTTPException

from modules.actions.adb import ADBAction
from modules.actions.station import StationAction


router = APIRouter(prefix="/api/actions", tags=["actions"])


@router.get("")
async def list_actions():
    actions = [ADBAction(), StationAction()]
    return {
        "actions": [
            {"type": a.type, "configSchema": a.config_schema()} for a in actions
        ]
    }


@router.post("/test")
async def test_action(payload: dict):
    action_type = payload.get("type")
    config = payload.get("config", {})
    if action_type == "adb":
        return await ADBAction().execute(config)
    if action_type == "station":
        return await StationAction().execute(config)
    raise HTTPException(status_code=400, detail="Unknown action type")


