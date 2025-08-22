import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.schemas.adb import ADBDevice, ADBDeviceCreate, ADBCommand, ADBCommandResponse
from app.services.adb_device_service import adb_device_service
from app.services.adb_service import adb_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/devices", response_model=List[ADBDevice])
async def read_adb_devices(
    db: AsyncSession = Depends(get_db),
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Retrieve ADB devices.
    """
    devices = await adb_device_service.get_devices(db)
    return devices

@router.post("/devices", response_model=ADBDevice)
async def create_adb_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_in: ADBDeviceCreate,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Create new ADB device.
    """
    # Check if device with this IP already exists
    existing_device = await adb_device_service.get_device_by_ip(db, device_in.ip)
    if existing_device:
        raise HTTPException(
            status_code=400,
            detail="ADB device with this IP already exists"
        )

    device = await adb_device_service.create_device(db, device_in)
    return device

@router.get("/devices/{device_id}", response_model=ADBDevice)
async def read_adb_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Get ADB device by ID.
    """
    device = await adb_device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="ADB device not found")
    return device

@router.delete("/devices/{device_id}", response_model=ADBDevice)
async def delete_adb_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Delete ADB device.
    """
    device = await adb_device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="ADB device not found")

    device = await adb_device_service.delete_device(db, device_id)
    return device

@router.post("/devices/{device_id}/connect")
async def connect_adb_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Connect to ADB device.
    """
    device = await adb_device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="ADB device not found")

    success = await adb_device_service.connect_device(db, device_id)

    if not success:
        raise HTTPException(
            status_code=500,
            detail="Failed to connect to ADB device"
        )

    return {
        "success": True,
        "device_id": device_id,
        "message": "Connected successfully"
    }

@router.post("/devices/{device_id}/disconnect")
async def disconnect_adb_device(
    *,
    db: AsyncSession = Depends(get_db),
    device_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Disconnect from ADB device.
    """
    device = await adb_device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="ADB device not found")

    await adb_device_service.disconnect_device(db, device_id)

    return {
        "success": True,
        "device_id": device_id,
        "message": "Disconnected successfully"
    }

@router.post("/execute", response_model=ADBCommandResponse)
async def execute_adb_command(
    *,
    db: AsyncSession = Depends(get_db),
    command: ADBCommand,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Execute ADB command on device.
    """
    # Check if device exists and is connected
    device = await adb_device_service.get_device(db, command.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="ADB device not found")

    if not device.is_connected:
        raise HTTPException(
            status_code=400,
            detail="ADB device is not connected"
        )

    result = await adb_service.execute_command(
        command.device_id,
        command.command,
        command.timeout
    )

    return result

@router.get("/status")
async def get_adb_status(
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Get ADB service status.
    """
    connected_devices = adb_service.get_connected_devices()

    return {
        "service_running": True,
        "connected_devices": connected_devices,
        "total_connected": len(connected_devices)
    }
