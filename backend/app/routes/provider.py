from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import json
import logging
import uuid

from models.device import Device
from models.user_token import UserToken
from services.crypto import decrypt
import hashlib

router = APIRouter(prefix="/v1.0", tags=["provider"])
security = HTTPBearer()

logger = logging.getLogger(__name__)


class DeviceCapability(BaseModel):
    type: str
    retrievable: bool = True
    reportable: bool = True
    parameters: Optional[Dict[str, Any]] = None


class DeviceInfo(BaseModel):
    id: str
    name: str
    type: str
    capabilities: List[DeviceCapability]
    properties: Optional[List[Dict[str, Any]]] = None
    device_info: Optional[Dict[str, str]] = None
    room: Optional[str] = None


class DeviceQuery(BaseModel):
    devices: List[Dict[str, str]]  # [{"id": "device_id"}]


class DeviceAction(BaseModel):
    devices: List[Dict[str, Any]]  # [{"id": "device_id", "capabilities": [...]}]


async def get_user_from_token(credentials: HTTPAuthorizationCredentials = Depends(security)) -> str:
    """Извлекает user_id из токена авторизации"""
    try:
        logger.info(f"Validating token: {credentials.credentials[:20]}...")
        
        # Находим токен в базе данных
        token_record = await UserToken.filter(
            provider="yandex",
            access_token__isnull=False
        ).first()
        
        if not token_record:
            logger.error("No token found in database")
            raise HTTPException(status_code=401, detail="Token not found")
        
        logger.info(f"Found token record: id={token_record.id}, user_id={token_record.user_id}")
        
        # Сопоставляем по хэшу без хранения открытого токена
        bearer = credentials.credentials
        bearer_hash = hashlib.sha256(bearer.encode("utf-8")).hexdigest()

        # Ищем по хэшу в БД
        token_record = await UserToken.filter(provider="yandex", access_token_hash=bearer_hash).first()

        # Fallback: если старые записи без hash — проверим расшифровкой и одновременно бэконим hash
        if not token_record:
            legacy = await UserToken.filter(provider="yandex").first()
            if not legacy:
                logger.error("No token found in database")
                raise HTTPException(status_code=401, detail="Token not found")
            try:
                decrypted_token = decrypt(legacy.access_token)
            except Exception:
                decrypted_token = None
            if decrypted_token != bearer:
                logger.error("Token mismatch for legacy record")
                raise HTTPException(status_code=401, detail="Invalid token")
            # backfill hash
            legacy.access_token_hash = bearer_hash
            await legacy.save()
            token_record = legacy
        
        # Возвращаем user_id из токена
        user_id = token_record.user_id
        logger.info(f"Token validated successfully for user_id: {user_id}")
        return str(user_id)
        
    except Exception as e:
        logger.error(f"Token validation error: {e}")
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.head("")
async def health_check():
    """Проверка доступности Endpoint URL провайдера"""
    logger.info("Health check called")
    return {}


@router.get("/user/devices")
async def get_devices(request: Request, user_id: str = Depends(get_user_from_token)):
    """Информация об устройствах пользователя"""
    try:
        logger.info(f"GET /user/devices called with user_id: {user_id}")
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        
        devices = await Device.all()
        logger.info(f"Found {len(devices)} devices for user {user_id}")
        
        devices_list = []
        for device in devices:
            logger.info(f"Processing device: id={device.id} (type={type(device.id)}), name={device.name}, type={device.yandex_type}")
            # Определяем тип устройства и его возможности
            device_info = DeviceInfo(
                id=str(device.id),
                name=device.name,
                type=device.yandex_type,
                capabilities=get_device_capabilities(device.yandex_type),
                device_info={
                    "manufacturer": "Y2M",
                    "model": device.name,
                    "hw_version": "1.0",
                    "sw_version": "1.0"
                }
            )
            devices_list.append(device_info.dict())
        
        return {
            "request_id": request_id,
            "payload": {
                "user_id": user_id,
                "devices": devices_list
            }
        }
        
    except Exception as e:
        logger.error(f"Error getting devices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/user/devices/query")
async def query_devices(request: Request, query: DeviceQuery, user_id: str = Depends(get_user_from_token)):
    """Информация о состояниях устройств пользователя"""
    try:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        devices = []
        
        for device_query in query.devices:
            device_id = device_query["id"]
            device = await Device.get_or_none(id=device_id)
            
            if device:
                # Получаем текущее состояние устройства
                state = await get_device_state(device)
                devices.append({
                    "id": device_id,
                    "capabilities": state
                })
        
        return {
            "request_id": request_id,
            "payload": {
                "devices": devices
            }
        }
        
    except Exception as e:
        logger.error(f"Error querying devices: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/user/devices/action")
async def device_action(request: Request, action: DeviceAction, user_id: str = Depends(get_user_from_token)):
    """Изменение состояния устройств пользователя"""
    try:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        results = []
        
        for device_action_item in action.devices:
            device_id = device_action_item["id"]
            capabilities = device_action_item.get("capabilities", [])
            
            device = await Device.get_or_none(id=device_id)
            if not device:
                results.append({
                    "id": device_id,
                    "error_code": "DEVICE_NOT_FOUND",
                    "error_message": "Device not found"
                })
                continue
            
            # Обрабатываем каждую команду
            device_result = {"id": device_id, "capabilities": []}
            
            for capability in capabilities:
                try:
                    result = await execute_device_action(device, capability)
                    device_result["capabilities"].append(result)
                except Exception as e:
                    logger.error(f"Error executing action for device {device_id}: {e}")
                    device_result["capabilities"].append({
                        "type": capability["type"],
                        "state": {
                            "instance": capability.get("state", {}).get("instance"),
                            "action_result": {
                                "status": "ERROR",
                                "error_code": "ACTION_ERROR",
                                "error_message": str(e)
                            }
                        }
                    })
            
            results.append(device_result)
        
        return {
            "request_id": request_id,
            "payload": {
                "devices": results
            }
        }
        
    except Exception as e:
        logger.error(f"Error executing device action: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.post("/user/unlink")
async def unlink_user(request: Request, user_id: str = Depends(get_user_from_token)):
    """Обработка отвязки аккаунта пользователя"""
    try:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        # Удаляем токены пользователя
        await UserToken.filter(provider="yandex", user_id=user_id).delete()
        
        return {
            "request_id": request_id,
            "payload": {
                "user_id": user_id,
                "status": "ok"
            }
        }
        
    except Exception as e:
        logger.error(f"Error unlinking user: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def get_device_capabilities(device_type: str) -> List[DeviceCapability]:
    """Возвращает список возможностей для типа устройства"""
    capabilities_map = {
        "devices.types.light": [
            DeviceCapability(
                type="devices.capabilities.on_off",
                retrievable=True,
                reportable=True
            ),
            DeviceCapability(
                type="devices.capabilities.range",
                retrievable=True,
                reportable=True,
                parameters={
                    "instance": "brightness",
                    "range": {
                        "min": 0,
                        "max": 100,
                        "precision": 1
                    },
                    "unit": "unit.percent"
                }
            )
        ],
        "devices.types.switch": [
            DeviceCapability(
                type="devices.capabilities.on_off",
                retrievable=True,
                reportable=True
            )
        ],
        "devices.types.media_device.tv": [
            DeviceCapability(
                type="devices.capabilities.on_off",
                retrievable=True,
                reportable=True
            ),
            DeviceCapability(
                type="devices.capabilities.range",
                retrievable=True,
                reportable=True,
                parameters={
                    "instance": "volume",
                    "range": {
                        "min": 0,
                        "max": 100,
                        "precision": 1
                    },
                    "unit": "unit.percent"
                }
            )
        ]
    }
    
    return capabilities_map.get(device_type, [
        DeviceCapability(
            type="devices.capabilities.on_off",
            retrievable=True,
            reportable=True
        )
    ])


async def get_device_state(device: Device) -> List[Dict[str, Any]]:
    """Получает текущее состояние устройства"""
    capabilities = get_device_capabilities(device.yandex_type)
    state = []
    
    for capability in capabilities:
        if capability.type == "devices.capabilities.on_off":
            # Здесь должна быть логика получения реального состояния
            # Для MVP возвращаем случайное состояние
            import random
            state.append({
                "type": capability.type,
                "state": {
                    "instance": "on",
                    "value": random.choice([True, False])
                }
            })
        elif capability.type == "devices.capabilities.range":
            instance = capability.parameters.get("instance", "brightness")
            import random
            state.append({
                "type": capability.type,
                "state": {
                    "instance": instance,
                    "value": random.randint(0, 100)
                }
            })
    
    return state


async def execute_device_action(device: Device, capability: Dict[str, Any]) -> Dict[str, Any]:
    """Выполняет действие с устройством"""
    capability_type = capability["type"]
    state = capability.get("state", {})
    
    if capability_type == "devices.capabilities.on_off":
        value = state.get("value", False)
        # Здесь должна быть логика управления устройством
        # Для MVP просто логируем
        logger.info(f"Device {device.id} on_off: {value}")
        
        return {
            "type": capability_type,
            "state": {
                "instance": "on",
                "action_result": {
                    "status": "DONE"
                }
            }
        }
    
    elif capability_type == "devices.capabilities.range":
        instance = state.get("instance", "brightness")
        value = state.get("value", 50)
        # Здесь должна быть логика управления устройством
        logger.info(f"Device {device.id} range {instance}: {value}")
        
        return {
            "type": capability_type,
            "state": {
                "instance": instance,
                "action_result": {
                    "status": "DONE"
                }
            }
        }
    
    else:
        raise ValueError(f"Unknown capability type: {capability_type}")
