import httpx
from urllib.parse import urlencode
from settings import settings
from services.crypto import encrypt
from models.user_token import UserToken


AUTH_URL = "https://oauth.yandex.ru/authorize"
TOKEN_URL = "https://oauth.yandex.ru/token"


def build_auth_url(state: str = "") -> str:
    params = {
        "response_type": "code",
        "client_id": settings.ya_client_id,
        "redirect_uri": settings.ya_redirect_uri,
        "force_confirm": "true",
        "state": state,
    }
    return f"{AUTH_URL}?{urlencode(params)}"


async def exchange_code(code: str) -> dict:
    async with httpx.AsyncClient(timeout=15) as client:
        data = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": settings.ya_client_id,
            "client_secret": settings.ya_client_secret,
            "redirect_uri": settings.ya_redirect_uri,
        }
        resp = await client.post(TOKEN_URL, data=data)
        resp.raise_for_status()
        return resp.json()


async def get_user_info(access_token: str) -> dict:
    """Получает информацию о пользователе из Яндекс OAuth API"""
    async with httpx.AsyncClient(timeout=15) as client:
        headers = {"Authorization": f"OAuth {access_token}"}
        resp = await client.get("https://login.yandex.ru/info", headers=headers)
        resp.raise_for_status()
        return resp.json()


async def save_tokens(token_payload: dict) -> int:
    access_token = token_payload.get("access_token", "")
    refresh_token = token_payload.get("refresh_token")
    expires_in = token_payload.get("expires_in")
    
    # Получаем информацию о пользователе
    try:
        user_info = await get_user_info(access_token)
        user_id = user_info.get("id", "unknown")
    except Exception as e:
        # Если не удалось получить user_id, используем fallback
        user_id = "unknown"
    
    # For MVP we store one record
    rec = await UserToken.create(
        user_id=user_id,
        provider="yandex",
        access_token=encrypt(access_token),
        refresh_token=encrypt(refresh_token) if refresh_token else None,
        expires_at=None,
    )
    return rec.id


