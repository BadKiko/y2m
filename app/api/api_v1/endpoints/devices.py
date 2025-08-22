import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.schemas.device import Device, DeviceCreate, DeviceUpdate
from app.services.device_service import device_service
from app.services.mqtt_service import mqtt_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[Device])
async def read_devices(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Retrieve devices.
    """
    devices = await device_service.get_devices(db, skip=skip, limit=limit)
    return devices

@router.post("/", response_model=Device)
async def create_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_in: DeviceCreate,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Create new device.
    """
    # Check if device with this name already exists
    existing_device = await device_service.get_device_by_name(db, device_in.name)
    if existing_device:
        raise HTTPException(
            status_code=400,
            detail="Device with this name already exists"
        )

    device = await device_service.create_device(db, device_in)

    # Create MQTT topics for the device
    try:
        # Subscribe to command topic
        await mqtt_service.subscribe(
            device.command_topic,
            lambda topic, payload: handle_device_command(topic, payload, device.id)
        )
        logger.info(f"Created MQTT topics for device: {device.name}")
    except Exception as e:
        logger.error(f"Failed to create MQTT topics for device {device.name}: {e}")
        # Don't fail device creation if MQTT setup fails

    return device

@router.get("/{device_id}", response_model=Device)
async def read_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Get device by ID.
    """
    device = await device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    return device

@router.put("/{device_id}", response_model=Device)
async def update_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_id: int,
    device_in: DeviceUpdate,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Update a device.
    """
    device = await device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    device = await device_service.update_device(db, device_id, device_in)
    return device

@router.delete("/{device_id}", response_model=Device)
async def delete_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Delete a device.
    """
    device = await device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Unsubscribe from MQTT topics
    try:
        await mqtt_service.unsubscribe(device.command_topic)
        await mqtt_service.unsubscribe(device.state_topic)
    except Exception as e:
        logger.error(f"Failed to unsubscribe from MQTT topics for device {device.name}: {e}")

    device = await device_service.delete_device(db, device_id)
    return device

async def handle_device_command(topic: str, payload: str, device_id: int):
    """
    Handle incoming MQTT command for device
    """
    logger.info(f"Received command for device {device_id}: {topic} -> {payload}")

    # Here you could implement device-specific command handling
    # For example, toggle power, set brightness, etc.

    # You could also emit WebSocket updates to connected clients
