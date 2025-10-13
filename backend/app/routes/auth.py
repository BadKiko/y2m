from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from services.oauth_yandex import build_auth_url, exchange_code, save_tokens
from settings import settings
from models.user_token import UserToken


router = APIRouter(prefix="/api/auth/yandex", tags=["auth"])


@router.get("/login")
async def yandex_login(state: str = ""):
    url = build_auth_url(state)
    return RedirectResponse(url)


class CallbackQuery(BaseModel):
    code: str
    state: str | None = None


@router.get("/callback")
async def yandex_callback(code: str, state: str | None = None):
    try:
        token_payload = await exchange_code(code)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"oauth error: {e}")
    token_id = await save_tokens(token_payload)
    # redirect back to web UI
    redirect_url = f"{settings.web_url}/auth/callback?ok=1&tokenId={token_id}"
    return RedirectResponse(redirect_url)


@router.get("/status")
async def auth_status():
    """Return whether at least one Yandex token is stored.

    This minimal implementation is user-scoped in the future; for now it
    reports authenticated if any Yandex token exists.
    """
    count = await UserToken.filter(provider="yandex").count()
    return {"authenticated": count > 0}


