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
        """Выполняет команду на Яндекс Станции через yapi контейнер"""
        import logging
        logger = logging.getLogger(__name__)
        
        try:
            # Получаем параметры
            oauth_token = payload.get("oauthToken")
            device_id = payload.get("deviceId")
            command = payload.get("command")
            
            if not oauth_token or not device_id or not command:
                return {"ok": False, "error": "Missing required parameters: oauthToken, deviceId, command"}
            
            # Формируем тело запроса для yapi
            body = {"command": command}
            if command == "sendText":
                body["text"] = payload.get("text", "")
            elif command == "setVolume":
                body["volume"] = payload.get("volume", 0.5)
            elif command == "rewind":
                body["position"] = payload.get("position", 0)
            
            logger.info(f"Executing station command: {command} on device {device_id}")
            
            # Отправляем команду в yapi контейнер
            async with httpx.AsyncClient(timeout=10.0) as client:
                yapi_url = "http://yapi:8001"
                
                logger.info(f"Sending request to yapi at {yapi_url} with data: {body}")
                
                response = await client.post(yapi_url, json=body)
                
                logger.info(f"yapi response: {response.status_code} - {response.text}")
                
                if response.status_code == 200:
                    return {"ok": True, "output": f"Station command '{command}' executed successfully"}
                else:
                    return {"ok": False, "error": f"yapi error: {response.status_code} - {response.text}"}
                    
        except httpx.ConnectError:
            logger.error("yapi container not available")
            return {"ok": False, "error": "yapi container not available"}
        except httpx.TimeoutException:
            logger.error("yapi request timeout")
            return {"ok": False, "error": "yapi request timeout"}
        except Exception as e:
            logger.error(f"Station action error: {e}")
            return {"ok": False, "error": str(e)}


