import logging
import httpx
from typing import Optional, Dict, Any
from datetime import datetime, timedelta

from app.core.config import settings
from app.services.encryption_service import encryption_service
from app.schemas.yandex import YandexTokenResponse

logger = logging.getLogger(__name__)

class YandexService:
    def __init__(self):
        self.client_id = settings.YANDEX_CLIENT_ID
        self.client_secret = settings.YANDEX_CLIENT_SECRET
        self.redirect_uri = settings.YANDEX_REDIRECT_URI
        self.token_url = "https://oauth.yandex.ru/token"
        self.device_url = "https://api.iot.yandex.net/v1.0"

    async def get_access_token(self, refresh_token: str) -> Optional[YandexTokenResponse]:
        """Get new access token using refresh token"""
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.token_url,
                    data={
                        "grant_type": "refresh_token",
                        "refresh_token": encryption_service.decrypt(refresh_token),
                        "client_id": self.client_id,
                        "client_secret": self.client_secret,
                    }
                )
                response.raise_for_status()
                data = response.json()

                return YandexTokenResponse(
                    access_token=data["access_token"],
                    refresh_token=data["refresh_token"],
                    expires_in=data["expires_in"]
                )

        except Exception as e:
            logger.error(f"Failed to refresh Yandex token: {e}")
            return None

    async def register_device(self, access_token: str, device_data: Dict[str, Any]) -> bool:
        """Register device with Yandex"""
        try:
            headers = {
                "Authorization": f"Bearer {encryption_service.decrypt(access_token)}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.device_url}/devices",
                    headers=headers,
                    json=device_data
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to register device with Yandex: {e}")
            return False

    async def update_device_state(self, access_token: str, device_id: str, state: Dict[str, Any]) -> bool:
        """Update device state in Yandex"""
        try:
            headers = {
                "Authorization": f"Bearer {encryption_service.decrypt(access_token)}",
                "Content-Type": "application/json"
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{self.device_url}/devices/{device_id}/state",
                    headers=headers,
                    json=state
                )
                response.raise_for_status()
                return True

        except Exception as e:
            logger.error(f"Failed to update device state in Yandex: {e}")
            return False

    def is_token_expired(self, expires_at: datetime) -> bool:
        """Check if token is expired (with 5 minute buffer)"""
        return datetime.utcnow() + timedelta(minutes=5) > expires_at

# Global Yandex service instance
yandex_service = YandexService()
