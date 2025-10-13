from fastapi import APIRouter, HTTPException
from fastapi.responses import RedirectResponse
from urllib.parse import quote
from pydantic import BaseModel

from services.oauth_yandex import build_auth_url, exchange_code, save_tokens
from settings import settings
from models.user_token import UserToken


router = APIRouter(prefix="/api/auth/yandex", tags=["auth"])


@router.get("/login")
async def yandex_login(state: str = "", return_to: str | None = None):
    # Если прилетел return_to (из /dialog/authorize), прокидываем его через state
    effective_state = return_to or state or ""
    url = build_auth_url(effective_state)
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
    await save_tokens(token_payload)

    # Определяем, нужно ли вернуться в /dialog/authorize (skill-first flow)
    if state and state.startswith(f"{settings.base_url}/dialog/authorize"):
        resp = RedirectResponse(state)
    else:
        # Возврат в веб-приложение без tokenId в URL
        resp = RedirectResponse(f"{settings.web_url}/auth/callback?ok=1")

    # Минимальная cookie-сессия (можно расширить в дальнейшем)
    resp.set_cookie(
        key="y2m_session",
        value="1",
        httponly=True,
        secure=True,
        samesite="lax",
        domain=None,
        path="/",
    )
    return resp


@router.get("/status")
async def auth_status():
    """Return whether at least one Yandex token is stored.

    This minimal implementation is user-scoped in the future; for now it
    reports authenticated if any Yandex token exists.
    """
    count = await UserToken.filter(provider="yandex").count()
    return {"authenticated": count > 0}


