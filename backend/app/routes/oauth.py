from fastapi import APIRouter, HTTPException, Request, Query, Form
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from typing import Optional
import httpx
import secrets
import hashlib
import base64
import logging
from urllib.parse import urlencode

from services.oauth_yandex import exchange_code, save_tokens
from settings import settings
from models.user_token import UserToken

logger = logging.getLogger(__name__)

router = APIRouter(tags=["oauth"])

# Хранилище временных кодов авторизации (в продакшене использовать Redis)
auth_codes = {}


class TokenRequest(BaseModel):
    grant_type: str
    code: Optional[str] = None
    refresh_token: Optional[str] = None
    client_id: Optional[str] = None
    client_secret: Optional[str] = None
    redirect_uri: Optional[str] = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: Optional[int] = None
    refresh_token: Optional[str] = None
    scope: Optional[str] = None


@router.get("/dialog/authorize")
async def authorize(
    response_type: str = Query(..., description="Тип ответа"),
    client_id: str = Query(..., description="Идентификатор клиента"),
    redirect_uri: str = Query(..., description="URI перенаправления"),
    scope: Optional[str] = Query(None, description="Область доступа"),
    state: Optional[str] = Query(None, description="Состояние для защиты от CSRF"),
    force_confirm: Optional[str] = Query(None, description="Принудительное подтверждение")
):
    """OAuth 2.0 Authorization Endpoint для навыка Яндекс.Умный дом"""
    
    logger.info(f"Authorize request: client_id={client_id}, redirect_uri={redirect_uri}, state={state}")
    
    # Проверяем параметры
    if response_type != "code":
        logger.error(f"Unsupported response type: {response_type}")
        raise HTTPException(
            status_code=400, 
            detail="Unsupported response type. Only 'code' is supported."
        )
    
    if client_id != settings.yandex_skill_client_id:
        logger.error(f"Invalid client_id: {client_id}, expected: {settings.yandex_skill_client_id}")
        raise HTTPException(
            status_code=400, 
            detail="Invalid client_id"
        )
    
    # Проверяем, есть ли уже авторизованный пользователь
    token_record = await UserToken.filter(
        provider="yandex",
        access_token__isnull=False
    ).first()
    
    if not token_record:
        # Если пользователь не авторизован, перенаправляем на авторизацию
        logger.info("User not authenticated, redirecting to web app")
        auth_url = f"{settings.web_url}/auth/yandex/login?state={state or ''}"
        return RedirectResponse(url=auth_url)
    
    # Пользователь уже авторизован, генерируем код авторизации
    logger.info(f"User authenticated, generating auth code for user_token_id={token_record.id}")
    auth_code = secrets.token_urlsafe(32)
    
    # Сохраняем код авторизации с параметрами
    auth_codes[auth_code] = {
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": scope,
        "state": state,
        "user_token_id": token_record.id,
        "expires_at": None
    }
    
    # Перенаправляем обратно в навык с кодом авторизации
    redirect_url = f"{redirect_uri}?code={auth_code}&state={state or ''}"
    logger.info(f"Redirecting to: {redirect_url}")
    return RedirectResponse(url=redirect_url)


@router.post("/oauth/token")
async def token(
    grant_type: str = Form(...),
    code: Optional[str] = Form(None),
    refresh_token: Optional[str] = Form(None),
    client_id: Optional[str] = Form(None),
    client_secret: Optional[str] = Form(None),
    redirect_uri: Optional[str] = Form(None)
):
    """OAuth 2.0 Token Endpoint"""
    
    logger.info(f"Token request: grant_type={grant_type}, client_id={client_id}, code={'***' if code else None}")
    
    if grant_type == "authorization_code":
        return await handle_authorization_code_grant(
            grant_type, code, refresh_token, client_id, client_secret, redirect_uri
        )
    elif grant_type == "refresh_token":
        return await handle_refresh_token_grant(
            grant_type, code, refresh_token, client_id, client_secret, redirect_uri
        )
    else:
        logger.error(f"Unsupported grant type: {grant_type}")
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported grant type: {grant_type}"
        )


async def handle_authorization_code_grant(
    grant_type: str, code: Optional[str], refresh_token: Optional[str], 
    client_id: Optional[str], client_secret: Optional[str], redirect_uri: Optional[str]
) -> TokenResponse:
    """Обработка Authorization Code Grant"""
    
    if not code:
        raise HTTPException(
            status_code=400,
            detail="Authorization code is required"
        )
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail="Client credentials are required"
        )
    
    # Проверяем client credentials навыка
    if (client_id != settings.yandex_skill_client_id or 
        client_secret != settings.yandex_skill_client_secret):
        raise HTTPException(
            status_code=401,
            detail="Invalid client credentials"
        )
    
    # Проверяем код авторизации
    if code not in auth_codes:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired authorization code"
        )
    
    auth_code_data = auth_codes[code]
    
    # Получаем существующий токен пользователя
    try:
        user_token_record = await UserToken.get(id=auth_code_data["user_token_id"])
        
        # Расшифровываем существующий токен
        from services.crypto import decrypt
        access_token = decrypt(user_token_record.access_token)
        refresh_token_decrypted = decrypt(user_token_record.refresh_token) if user_token_record.refresh_token else None
        
        # Удаляем использованный код авторизации
        del auth_codes[code]
        
        return TokenResponse(
            access_token=access_token,
            token_type="Bearer",
            expires_in=3600,  # 1 час
            refresh_token=refresh_token_decrypted,
            scope="smart-home"
        )
        
    except Exception as e:
        logger.error(f"Token exchange error: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to exchange code for token: {str(e)}"
        )


async def handle_refresh_token_grant(
    grant_type: str, code: Optional[str], refresh_token: Optional[str], 
    client_id: Optional[str], client_secret: Optional[str], redirect_uri: Optional[str]
) -> TokenResponse:
    """Обработка Refresh Token Grant"""
    
    if not refresh_token:
        raise HTTPException(
            status_code=400,
            detail="Refresh token is required"
        )
    
    if not client_id or not client_secret:
        raise HTTPException(
            status_code=400,
            detail="Client credentials are required"
        )
    
    # Проверяем client credentials навыка
    if (client_id != settings.yandex_skill_client_id or 
        client_secret != settings.yandex_skill_client_secret):
        raise HTTPException(
            status_code=401,
            detail="Invalid client credentials"
        )
    
    # Находим токен в базе данных
    token_record = await UserToken.filter(
        provider="yandex",
        refresh_token__isnull=False
    ).first()
    
    if not token_record:
        raise HTTPException(
            status_code=400,
            detail="Invalid refresh token"
        )
    
    # Обновляем токен через Яндекс OAuth
    try:
        from services.crypto import decrypt
        decrypted_refresh_token = decrypt(token_record.refresh_token)
        
        async with httpx.AsyncClient(timeout=15) as client:
            data = {
                "grant_type": "refresh_token",
                "refresh_token": decrypted_refresh_token,
                "client_id": settings.ya_client_id,
                "client_secret": settings.ya_client_secret,
            }
            resp = await client.post("https://oauth.yandex.ru/token", data=data)
            resp.raise_for_status()
            token_data = resp.json()
            
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Failed to refresh token: {e.response.text}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Internal error: {str(e)}"
        )
    
    # Обновляем токены в базе данных
    try:
        from services.crypto import encrypt
        token_record.access_token = encrypt(token_data["access_token"])
        if token_data.get("refresh_token"):
            token_record.refresh_token = encrypt(token_data["refresh_token"])
        await token_record.save()
        
        return TokenResponse(
            access_token=token_data["access_token"],
            token_type="Bearer",
            expires_in=token_data.get("expires_in"),
            refresh_token=token_data.get("refresh_token"),
            scope=token_data.get("scope")
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update tokens: {str(e)}"
        )


@router.get("/oauth/authorize")
async def oauth_authorize(
    response_type: str = Query(..., description="Тип ответа"),
    client_id: str = Query(..., description="Идентификатор клиента"),
    redirect_uri: str = Query(..., description="URI перенаправления"),
    scope: Optional[str] = Query(None, description="Область доступа"),
    state: Optional[str] = Query(None, description="Состояние для защиты от CSRF")
):
    """Альтернативный endpoint для авторизации"""
    return await authorize(response_type, client_id, redirect_uri, scope, state)


@router.get("/.well-known/oauth-authorization-server")
async def oauth_discovery():
    """OAuth 2.0 Discovery Endpoint"""
    return {
        "issuer": settings.base_url,
        "authorization_endpoint": f"{settings.base_url}/dialog/authorize",
        "token_endpoint": f"{settings.base_url}/oauth/token",
        "response_types_supported": ["code"],
        "grant_types_supported": ["authorization_code", "refresh_token"],
        "token_endpoint_auth_methods_supported": ["client_secret_post"],
        "scopes_supported": ["smart-home"]
    }
