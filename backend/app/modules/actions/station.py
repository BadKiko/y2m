from .base import Action, ActionResult
from typing import Literal
import httpx


class StationAction(Action):
    type: Literal["station"] = "station"

    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "oauthToken": {"type": "string"},
                "deviceId": {"type": "string"},
                "command": {"type": "string", "enum": [
                    "sendText", "setVolume", "play", "stop", "next", "prev", "rewind"
                ]},
                "text": {"type": "string"},
                "volume": {"type": "number"},
                "position": {"type": "integer"}
            },
            "required": ["oauthToken", "deviceId", "command"]
        }

    async def execute(self, payload: dict) -> ActionResult:
        # Minimal HTTP mimic of yapi API contract
        token = payload.get("oauthToken")
        device_id = payload.get("deviceId")
        command = payload.get("command")
        body: dict = {"deviceId": device_id, "command": command}
        if command == "sendText":
            body["text"] = payload.get("text", "")
        if command == "setVolume":
            body["volume"] = payload.get("volume", 0.5)
        if command == "rewind":
            body["position"] = payload.get("position", 0)

        # In real device, endpoints differ; for MVP we expose backend's own proxy endpoint later.
        # Here we just return payload to indicate execution placeholder.
        # To align with https://github.com/ebuyan/yapi contract, we'd POST to local service.
        # For now, simulate success.
        return {"ok": True, "output": f"station command {command} prepared"}


