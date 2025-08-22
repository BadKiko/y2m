import logging
from typing import Optional
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.yandex_account import YandexAccount
from app.schemas.yandex import YandexAccountCreate
from app.services.encryption_service import encryption_service
from app.services.yandex_service import yandex_service

logger = logging.getLogger(__name__)

class YandexAccountService:
    @staticmethod
    async def create_account(db: AsyncSession, account: YandexAccountCreate) -> YandexAccount:
        """Create a new Yandex account"""
        # Encrypt tokens
        encrypted_refresh_token = encryption_service.encrypt(account.refresh_token)
        encrypted_access_token = encryption_service.encrypt(account.access_token)

        db_account = YandexAccount(
            user=account.user,
            refresh_token=encrypted_refresh_token,
            access_token=encrypted_access_token,
            expires_at=account.expires_at
        )

        db.add(db_account)
        await db.commit()
        await db.refresh(db_account)

        logger.info(f"Created Yandex account: {account.user}")
        return db_account

    @staticmethod
    async def get_account(db: AsyncSession, account_id: int) -> Optional[YandexAccount]:
        """Get account by ID"""
        result = await db.execute(select(YandexAccount).where(YandexAccount.id == account_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_account_by_user(db: AsyncSession, user: str) -> Optional[YandexAccount]:
        """Get account by username"""
        result = await db.execute(select(YandexAccount).where(YandexAccount.user == user))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_accounts(db: AsyncSession):
        """Get all accounts"""
        result = await db.execute(select(YandexAccount))
        return result.scalars().all()

    @staticmethod
    async def update_tokens(db: AsyncSession, account_id: int, access_token: str, refresh_token: str, expires_in: int):
        """Update account tokens"""
        result = await db.execute(select(YandexAccount).where(YandexAccount.id == account_id))
        db_account = result.scalar_one_or_none()

        if not db_account:
            return None

        # Encrypt new tokens
        encrypted_access_token = encryption_service.encrypt(access_token)
        encrypted_refresh_token = encryption_service.encrypt(refresh_token)

        # Update account
        db_account.access_token = encrypted_access_token
        db_account.refresh_token = encrypted_refresh_token
        db_account.expires_at = datetime.utcnow() + timedelta(seconds=expires_in)

        await db.commit()
        await db.refresh(db_account)

        logger.info(f"Updated tokens for Yandex account: {db_account.user}")
        return db_account

    @staticmethod
    async def refresh_token_if_needed(db: AsyncSession, account_id: int) -> Optional[YandexAccount]:
        """Refresh access token if expired"""
        account = await YandexAccountService.get_account(db, account_id)
        if not account:
            return None

        if yandex_service.is_token_expired(account.expires_at):
            # Token expired, refresh it
            token_response = await yandex_service.get_access_token(account.refresh_token)

            if token_response:
                return await YandexAccountService.update_tokens(
                    db, account_id,
                    token_response.access_token,
                    token_response.refresh_token,
                    token_response.expires_in
                )

        return account

    @staticmethod
    async def delete_account(db: AsyncSession, account_id: int) -> Optional[YandexAccount]:
        """Delete account"""
        result = await db.execute(select(YandexAccount).where(YandexAccount.id == account_id))
        db_account = result.scalar_one_or_none()

        if not db_account:
            return None

        await db.delete(db_account)
        await db.commit()

        logger.info(f"Deleted Yandex account: {db_account.user}")
        return db_account

# Global Yandex account service instance
yandex_account_service = YandexAccountService()
