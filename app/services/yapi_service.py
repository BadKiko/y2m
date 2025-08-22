import logging
import httpx
from typing import Optional, Dict, Any

from app.core.config import settings

logger = logging.getLogger(__name__)

class YAPIService:
    def __init__(self):
        self.base_url = settings.YAPI_URL

    async def execute_command(self, command: str, target_station: Optional[str] = None, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Execute silent command on Yandex Station via YAPI"""
        try:
            url = f"{self.base_url}/api/voice/silent"

            payload = {
                "command": command,
                "target_station": target_station,
                "params": params or {}
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, json=payload)
                response.raise_for_status()

                return {
                    "success": True,
                    "response": response.json(),
                    "execution_time": response.elapsed.total_seconds()
                }

        except httpx.TimeoutException:
            logger.error("YAPI command execution timeout")
            return {
                "success": False,
                "error": "Command execution timeout",
                "execution_time": 30.0
            }

        except Exception as e:
            logger.error(f"YAPI command execution error: {e}")
            return {
                "success": False,
                "error": str(e),
                "execution_time": 0.0
            }

    async def get_stations(self) -> Dict[str, Any]:
        """Get list of available Yandex stations"""
        try:
            url = f"{self.base_url}/api/stations"

            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                response.raise_for_status()

                return {
                    "success": True,
                    "stations": response.json()
                }

        except Exception as e:
            logger.error(f"Failed to get Yandex stations: {e}")
            return {
                "success": False,
                "error": str(e)
            }

    async def test_connection(self) -> bool:
        """Test connection to YAPI service"""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200

        except Exception:
            return False

# Global YAPI service instance
yapi_service = YAPIService()
