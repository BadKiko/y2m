from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional

from models.binding import Binding
from models.device import Device
from models.user_token import UserToken
from services.crypto import decrypt
from settings import settings
import json
import aiomqtt


router = APIRouter(prefix="/api/bindings", tags=["bindings"])


class BindingCreate(BaseModel):
    device_id: int
    capability: str
    action_type: str  # "adb" | "station" | "mqtt"
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


class InvokePayload(BaseModel):
    payload: Optional[dict] = None


@router.post("/{binding_id}/invoke")
async def invoke_binding(binding_id: int, body: InvokePayload | None = None):
    b = await Binding.get_or_none(id=binding_id)
    if not b:
        raise HTTPException(status_code=404, detail="Binding not found")

    # Обогащаем payload в зависимости от типа действия
    payload = (body.payload if body and body.payload else {})
    
    if b.action_type == "station":
        # Берём токен провайдера из БД (любой активный для провайдера yandex)
        token_record = await UserToken.filter(provider="yandex").first()
        if not token_record:
            raise HTTPException(status_code=400, detail="No Yandex token configured")
        try:
            oauth_token = decrypt(token_record.access_token)
        except Exception:
            oauth_token = token_record.access_token

        payload = {
            **payload,
            "oauthToken": oauth_token,
            "deviceId": (b.action_config or {}).get("deviceId"),
        }
        topic = f"y2m/bindings/{binding_id}/invoke"
        message = json.dumps(payload)
        
    elif b.action_type == "mqtt":
        # Для MQTT отправляем в указанный топик
        mqtt_topic = (b.action_config or {}).get("topic")
        if not mqtt_topic:
            raise HTTPException(status_code=400, detail="MQTT topic not configured")
        
        # Подготавливаем payload с подстановкой переменных
        mqtt_payload = (b.action_config or {}).get("payload", "{}")
        
        # Подставляем переменные из payload от Яндекса
        if payload:
            # Извлекаем данные из payload Яндекса
            yandex_value = payload.get("value")
            yandex_capability = payload.get("capability", b.capability)
            yandex_instance = payload.get("instance")
            yandex_device_id = payload.get("device_id", b.device_id)
            
            # Заменяем переменные в payload
            mqtt_payload = mqtt_payload.replace("{{value}}", str(yandex_value) if yandex_value is not None else "")
            mqtt_payload = mqtt_payload.replace("{{capability}}", str(yandex_capability))
            mqtt_payload = mqtt_payload.replace("{{instance}}", str(yandex_instance) if yandex_instance else "")
            mqtt_payload = mqtt_payload.replace("{{device_id}}", str(yandex_device_id))
        
        topic = mqtt_topic
        message = mqtt_payload
        
    else:
        # Для ADB и других типов
        topic = f"y2m/bindings/{binding_id}/invoke"
        message = json.dumps(payload)

    # Публикуем в MQTT
    async with aiomqtt.Client(hostname=settings.mqtt_host, port=settings.mqtt_port) as client:
        await client.publish(topic, message, qos=0, retain=False)

    return {"ok": True}

