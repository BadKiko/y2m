import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from app.models.adb_device import ADBDevice
from app.schemas.adb import ADBDeviceCreate, ADBDeviceUpdate
from app.services.adb_service import adb_service

logger = logging.getLogger(__name__)

class ADBDeviceService:
    @staticmethod
    async def create_device(db: AsyncSession, device: ADBDeviceCreate) -> ADBDevice:
        """Create a new ADB device"""
        db_device = ADBDevice(
            name=device.name,
            ip=device.ip,
            port=device.port
        )

        db.add(db_device)
        await db.commit()
        await db.refresh(db_device)

        logger.info(f"Created ADB device: {device.name} ({device.ip}:{device.port})")
        return db_device

    @staticmethod
    async def get_device(db: AsyncSession, device_id: int) -> Optional[ADBDevice]:
        """Get device by ID"""
        result = await db.execute(select(ADBDevice).where(ADBDevice.id == device_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_devices(db: AsyncSession) -> List[ADBDevice]:
        """Get all ADB devices"""
        result = await db.execute(select(ADBDevice))
        return result.scalars().all()

    @staticmethod
    async def get_device_by_ip(db: AsyncSession, ip: str) -> Optional[ADBDevice]:
        """Get device by IP address"""
        result = await db.execute(select(ADBDevice).where(ADBDevice.ip == ip))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_device(db: AsyncSession, device_id: int, device_update: ADBDeviceUpdate) -> Optional[ADBDevice]:
        """Update ADB device"""
        result = await db.execute(select(ADBDevice).where(ADBDevice.id == device_id))
        db_device = result.scalar_one_or_none()

        if not db_device:
            return None

        update_data = device_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_device, field, value)

        await db.commit()
        await db.refresh(db_device)

        logger.info(f"Updated ADB device: {db_device.name}")
        return db_device

    @staticmethod
    async def update_connection_status(db: AsyncSession, device_id: int, is_connected: bool):
        """Update device connection status"""
        result = await db.execute(select(ADBDevice).where(ADBDevice.id == device_id))
        db_device = result.scalar_one_or_none()

        if db_device:
            db_device.is_connected = is_connected
            if is_connected:
                db_device.last_seen = datetime.utcnow()
            await db.commit()
            await db.refresh(db_device)

    @staticmethod
    async def connect_device(db: AsyncSession, device_id: int) -> bool:
        """Connect to ADB device"""
        device = await ADBDeviceService.get_device(db, device_id)
        if not device:
            return False

        success = await adb_service.connect_device(device_id, device.ip, device.port)

        if success:
            await ADBDeviceService.update_connection_status(db, device_id, True)

        return success

    @staticmethod
    async def disconnect_device(db: AsyncSession, device_id: int):
        """Disconnect from ADB device"""
        await adb_service.disconnect_device(device_id)
        await ADBDeviceService.update_connection_status(db, device_id, False)

    @staticmethod
    async def delete_device(db: AsyncSession, device_id: int) -> Optional[ADBDevice]:
        """Delete ADB device"""
        # Disconnect first
        await adb_service.disconnect_device(device_id)

        result = await db.execute(select(ADBDevice).where(ADBDevice.id == device_id))
        db_device = result.scalar_one_or_none()

        if not db_device:
            return None

        await db.delete(db_device)
        await db.commit()

        logger.info(f"Deleted ADB device: {db_device.name}")
        return db_device

# Global ADB device service instance
adb_device_service = ADBDeviceService()
