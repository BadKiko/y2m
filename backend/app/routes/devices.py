import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from models.device import Device
from services.adb_pool import ensure_connected


router = APIRouter(prefix="/api/devices", tags=["devices"])


class DeviceCreate(BaseModel):
    name: str
    yandex_type: str
    adb_host: Optional[str] = None
    adb_port: Optional[int] = None


class DeviceUpdate(DeviceCreate):
    pass


@router.get("")
async def list_devices():
    items = await Device.all().prefetch_related("bindings")
    return [
        {
            "id": d.id,
            "name": d.name,
            "yandex_type": d.yandex_type,
            "adb_host": d.adb_host,
            "adb_port": d.adb_port,
        }
        for d in items
    ]


@router.post("")
async def create_device(payload: DeviceCreate):
    device = await Device.create(**payload.model_dump())
    if device.adb_host and device.adb_port:
        # fire-and-forget ensure connection
        asyncio.create_task(ensure_connected(device.adb_host, device.adb_port))
    return {"id": device.id}


@router.put("/{device_id}")
async def update_device(device_id: int, payload: DeviceUpdate):
    device = await Device.get_or_none(id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    await device.update_from_dict(payload.model_dump()).save()
    if device.adb_host and device.adb_port:
        asyncio.create_task(ensure_connected(device.adb_host, device.adb_port))
    return {"ok": True}


@router.delete("/{device_id}")
async def delete_device(device_id: int):
    device = await Device.get_or_none(id=device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")
    
    # Удаляем все привязки устройства
    from models.binding import Binding
    await Binding.filter(device_id=device_id).delete()
    
    # Удаляем само устройство
    await device.delete()
    
    return {"ok": True}


