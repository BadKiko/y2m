import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.schemas.yandex import YandexAccount, YandexLoginRequest
from app.services.yandex_account_service import yandex_account_service
from app.services.yandex_service import yandex_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/accounts", response_model=List[YandexAccount])
async def read_yandex_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Retrieve Yandex accounts.
    """
    accounts = await yandex_account_service.get_accounts(db)
    return accounts

@router.get("/accounts/{account_id}", response_model=YandexAccount)
async def read_yandex_account(
    *,
    db: AsyncSession = Depends(get_db),
    account_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Get Yandex account by ID.
    """
    account = await yandex_account_service.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Yandex account not found")
    return account

@router.delete("/accounts/{account_id}", response_model=YandexAccount)
async def delete_yandex_account(
    *,
    db: AsyncSession = Depends(get_db),
    account_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Delete Yandex account.
    """
    account = await yandex_account_service.get_account(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Yandex account not found")

    account = await yandex_account_service.delete_account(db, account_id)
    return account

@router.post("/login")
async def yandex_login(
    *,
    db: AsyncSession = Depends(get_db),
    login_request: YandexLoginRequest,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Initiate Yandex OAuth login flow.
    Note: In production, this should redirect to Yandex OAuth URL.
    """
    # This is a simplified version. In production, you would:
    # 1. Redirect user to Yandex OAuth URL
    # 2. Handle the callback with authorization code
    # 3. Exchange code for tokens

    # For demo purposes, we'll simulate token retrieval
    # You would implement proper OAuth2 flow here

    return {
        "message": "Yandex login initiated",
        "redirect_url": f"https://oauth.yandex.ru/authorize?response_type=code&client_id={yandex_service.client_id}",
        "note": "In production, implement proper OAuth2 callback handling"
    }

@router.post("/register-device")
async def register_device_with_yandex(
    *,
    db: AsyncSession = Depends(get_db),
    account_id: int,
    device_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Register device with Yandex Home.
    """
    # Get account and refresh token if needed
    account = await yandex_account_service.refresh_token_if_needed(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Yandex account not found")

    # Here you would implement device registration with yandex2mqtt
    # This is a placeholder for the actual implementation

    return {
        "message": "Device registration initiated",
        "account_id": account_id,
        "device_id": device_id,
        "status": "pending"
    }

@router.post("/sync-devices")
async def sync_devices_with_yandex(
    *,
    db: AsyncSession = Depends(get_db),
    account_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Sync all devices with Yandex Home.
    """
    account = await yandex_account_service.refresh_token_if_needed(db, account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Yandex account not found")

    # Here you would implement bulk device sync with yandex2mqtt

    return {
        "message": "Device sync initiated",
        "account_id": account_id,
        "status": "pending"
    }
