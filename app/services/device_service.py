import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.models.device import Device
from app.schemas.device import DeviceCreate, DeviceUpdate
from app.core.config import settings

logger = logging.getLogger(__name__)

class DeviceService:
    @staticmethod
    async def create_device(db: AsyncSession, device: DeviceCreate) -> Device:
        """Create a new device"""
        # Generate MQTT topics
        base_topic = f"home/{settings.PROJECT_NAME}/{device.name}"
        state_topic = f"{base_topic}/state"
        command_topic = f"{base_topic}/cmd"

        db_device = Device(
            name=device.name,
            type=device.type,
            mqtt_base_topic=base_topic,
            state_topic=state_topic,
            command_topic=command_topic,
            meta=device.meta or {}
        )

        db.add(db_device)
        await db.commit()
        await db.refresh(db_device)

        logger.info(f"Created device: {device.name}")
        return db_device

    @staticmethod
    async def get_device(db: AsyncSession, device_id: int) -> Optional[Device]:
        """Get device by ID"""
        result = await db.execute(select(Device).where(Device.id == device_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_devices(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[Device]:
        """Get all devices with pagination"""
        result = await db.execute(
            select(Device).offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def get_device_by_name(db: AsyncSession, name: str) -> Optional[Device]:
        """Get device by name"""
        result = await db.execute(select(Device).where(Device.name == name))
        return result.scalar_one_or_none()

    @staticmethod
    async def update_device(db: AsyncSession, device_id: int, device_update: DeviceUpdate) -> Optional[Device]:
        """Update device"""
        result = await db.execute(select(Device).where(Device.id == device_id))
        db_device = result.scalar_one_or_none()

        if not db_device:
            return None

        update_data = device_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_device, field, value)

        await db.commit()
        await db.refresh(db_device)

        logger.info(f"Updated device: {db_device.name}")
        return db_device

    @staticmethod
    async def delete_device(db: AsyncSession, device_id: int) -> Optional[Device]:
        """Delete device"""
        result = await db.execute(select(Device).where(Device.id == device_id))
        db_device = result.scalar_one_or_none()

        if not db_device:
            return None

        await db.delete(db_device)
        await db.commit()

        logger.info(f"Deleted device: {db_device.name}")
        return db_device

    @staticmethod
    async def get_active_devices(db: AsyncSession) -> List[Device]:
        """Get all active devices"""
        result = await db.execute(
            select(Device).where(Device.is_active == True)
        )
        return result.scalars().all()

# Global device service instance
device_service = DeviceService()
