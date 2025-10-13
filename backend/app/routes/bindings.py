from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from models.binding import Binding
from models.device import Device


router = APIRouter(prefix="/api/bindings", tags=["bindings"])


class BindingCreate(BaseModel):
    device_id: int
    capability: str
    action_type: str  # "adb" | "station"
    action_config: dict


class BindingUpdate(BaseModel):
    capability: Optional[str] = None
    action_type: Optional[str] = None
    action_config: Optional[dict] = None


@router.get("")
async def list_bindings():
    items = await Binding.all().prefetch_related("device")
    return [
        {
            "id": b.id,
            "device_id": b.device_id,
            "capability": b.capability,
            "action_type": b.action_type,
            "action_config": b.action_config,
        }
        for b in items
    ]


@router.post("")
async def create_binding(payload: BindingCreate):
    if not await Device.exists(id=payload.device_id):
        raise HTTPException(status_code=404, detail="Device not found")
    b = await Binding.create(
        device_id=payload.device_id,
        capability=payload.capability,
        action_type=payload.action_type,
        action_config=payload.action_config,
    )
    return {"id": b.id}


@router.put("/{binding_id}")
async def update_binding(binding_id: int, payload: BindingUpdate):
    b = await Binding.get_or_none(id=binding_id)
    if not b:
        raise HTTPException(status_code=404, detail="Binding not found")
    update_dict = {k: v for k, v in payload.model_dump().items() if v is not None}
    await b.update_from_dict(update_dict).save()
    return {"ok": True}


@router.delete("/{binding_id}")
async def delete_binding(binding_id: int):
    deleted = await Binding.filter(id=binding_id).delete()
    if not deleted:
        raise HTTPException(status_code=404, detail="Binding not found")
    return {"ok": True}


