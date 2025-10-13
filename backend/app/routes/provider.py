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
    description: Optional[str] = None


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


@router.post("/user/devices/unlink")
async def unlink_device(request: Request, device_query: DeviceQuery, user_id: str = Depends(get_user_from_token)):
    """Обработка отвязки конкретного устройства от Яндекс Дома"""
    try:
        request_id = request.headers.get("X-Request-Id") or str(uuid.uuid4())
        results = []
        
        for device_query_item in device_query.devices:
            device_id = device_query_item["id"]
            device = await Device.get_or_none(id=device_id)
            
            if device:
                # Удаляем все привязки устройства
                from models.binding import Binding
                await Binding.filter(device_id=device_id).delete()
                
                # Удаляем само устройство
                await device.delete()
                
                results.append({
                    "id": device_id,
                    "status": "unlinked"
                })
            else:
                results.append({
                    "id": device_id,
                    "error_code": "DEVICE_NOT_FOUND",
                    "error_message": "Device not found"
                })
        
        return {
            "request_id": request_id,
            "payload": {
                "devices": results
            }
        }
        
    except Exception as e:
        logger.error(f"Error unlinking device: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


def get_capability_description(capability_type: str, instance: str = None) -> str:
    """Возвращает описание capability на русском языке"""
    descriptions = {
        "devices.capabilities.on_off": "Включение/выключение",
        "devices.capabilities.range": {
            "brightness": "Яркость",
            "volume": "Громкость", 
            "temperature": "Температура",
            "channel": "Канал",
            "humidity": "Влажность",
            "pressure": "Давление",
            "co2_level": "Уровень CO2",
            "pm1_density": "Плотность PM1",
            "pm2.5_density": "Плотность PM2.5",
            "pm10_density": "Плотность PM10",
            "tvoc": "Летучие органические соединения",
            "water_level": "Уровень воды",
            "open": "Открытие",
            "battery_level": "Уровень заряда",
            "co_level": "Уровень CO",
            "smoke_level": "Уровень дыма",
            "ammonia": "Аммиак",
            "butane": "Бутан",
            "propane": "Пропан",
            "methane": "Метан",
            "hydrogen": "Водород",
            "oxygen": "Кислород",
            "ozone": "Озон",
            "formaldehyde": "Формальдегид",
            "heater": "Нагрев",
            "current": "Ток",
            "voltage": "Напряжение",
            "power": "Мощность",
            "electricity_meter": "Счетчик электроэнергии",
            "gas_meter": "Счетчик газа",
            "water_meter": "Счетчик воды",
            "heat_meter": "Счетчик тепла"
        },
        "devices.capabilities.mode": {
            "work_mode": "Режим работы",
            "thermostat": "Термостат",
            "fan_speed": "Скорость вентилятора",
            "heat": "Нагрев",
            "swing": "Качание",
            "input_source": "Источник сигнала",
            "tea_mode": "Режим заваривания чая",
            "program": "Программа",
            "tank_filled": "Заполнение бака",
            "pause": "Пауза",
            "fan_mode": "Режим вентилятора",
            "ionization": "Ионизация",
            "backlight": "Подсветка",
            "child_lock": "Блокировка от детей",
            "sound": "Звук",
            "oscillation": "Колебание",
            "humidity": "Влажность",
            "buzzer": "Зуммер",
            "led": "Светодиод",
            "keep_warm": "Подогрев",
            "boil": "Кипячение",
            "controls_locked": "Блокировка управления",
            "mute": "Отключение звука"
        },
        "devices.capabilities.toggle": {
            "backlight": "Подсветка",
            "controls_locked": "Блокировка управления",
            "mute": "Отключение звука",
            "pause": "Пауза",
            "keep_warm": "Подогрев",
            "sound": "Звук",
            "boil": "Кипячение",
            "ionization": "Ионизация",
            "oscillation": "Колебание",
            "buzzer": "Зуммер",
            "led": "Светодиод",
            "child_lock": "Блокировка от детей",
            "night_light": "Ночной режим",
            "swing": "Качание",
            "tank_filled": "Заполнение бака"
        },
        "devices.capabilities.color_setting": "Настройка цвета",
        "devices.capabilities.video_stream": "Видеопоток"
    }
    
    if capability_type in descriptions:
        if isinstance(descriptions[capability_type], dict) and instance:
            return descriptions[capability_type].get(instance, instance)
        elif isinstance(descriptions[capability_type], str):
            return descriptions[capability_type]
    
    return capability_type.split('.')[-1].replace('_', ' ').title()


def get_device_capabilities(device_type: str) -> List[DeviceCapability]:
    """Возвращает список возможностей для типа устройства"""
    try:
        # Загружаем типы устройств из JSON файла
        import os
        current_dir = os.path.dirname(os.path.abspath(__file__))
        json_path = os.path.join(current_dir, "..", "data", "yandex_device_types.json")
        
        with open(json_path, "r", encoding="utf-8") as f:
            device_types_data = json.load(f)
        
        # Ищем нужный тип устройства
        for device_type_info in device_types_data["types"]:
            if device_type_info["type"] == device_type:
                capabilities = []
                
                # Обрабатываем capabilities из JSON
                for cap in device_type_info.get("capabilities", []):
                    if isinstance(cap, dict) and "type" in cap:
                        cap_type = cap["type"]
                        parameters = None
                        
                        # Добавляем parameters для capabilities с instances
                        if "instances" in cap and cap["instances"]:
                            for instance in cap["instances"]:
                                if isinstance(instance, dict) and "function" in instance:
                                    function = instance["function"]
                                    
                                    # Создаем parameters в зависимости от типа capability
                                    if cap_type == "devices.capabilities.range":
                                        if function == "brightness":
                                            parameters = {
                                                "instance": "brightness",
                                                "range": {"min": 0, "max": 100, "precision": 1},
                                                "unit": "unit.percent"
                                            }
                                        elif function == "volume":
                                            parameters = {
                                                "instance": "volume", 
                                                "range": {"min": 0, "max": 100, "precision": 1},
                                                "unit": "unit.percent"
                                            }
                                        elif function == "temperature":
                                            parameters = {
                                                "instance": "temperature",
                                                "range": {"min": 0, "max": 100, "precision": 1},
                                                "unit": "unit.temperature.celsius"
                                            }
                                        elif function == "channel":
                                            parameters = {
                                                "instance": "channel",
                                                "range": {"min": 1, "max": 999, "precision": 1}
                                            }
                                        else:
                                            parameters = {"instance": function}
                                    
                                    elif cap_type == "devices.capabilities.mode":
                                        if "values" in instance and instance["values"]:
                                            parameters = {
                                                "instance": function,
                                                "modes": [{"value": v} for v in instance["values"]]
                                            }
                                        else:
                                            parameters = {"instance": function}
                                    
                                    elif cap_type == "devices.capabilities.toggle":
                                        parameters = {"instance": function}
                                    
                                    elif cap_type == "devices.capabilities.color_setting":
                                        parameters = {
                                            "color_model": "rgb",
                                            "temperature_k": {"min": 2000, "max": 9000}
                                        }
                                    
                                    break  # Берем первый instance
                        
                        # Получаем описание capability
                        description = get_capability_description(cap_type, parameters.get("instance") if parameters else None)
                        
                        capabilities.append(DeviceCapability(
                            type=cap_type,
                            retrievable=True,
                            reportable=True,
                            parameters=parameters,
                            description=description
                        ))
                
                return capabilities
        
        # Если тип устройства не найден, возвращаем базовый on_off
        return [
            DeviceCapability(
                type="devices.capabilities.on_off",
                retrievable=True,
                reportable=True
            )
        ]
        
    except Exception as e:
        logger.error(f"Error loading device capabilities for {device_type}: {e}")
        # Fallback к базовому on_off
        return [
            DeviceCapability(
                type="devices.capabilities.on_off",
                retrievable=True,
                reportable=True
            )
        ]


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
    
    elif capability_type == "devices.capabilities.mode":
        instance = state.get("instance", "work_mode")
        value = state.get("value", "auto")
        logger.info(f"Device {device.id} mode {instance}: {value}")
        
        return {
            "type": capability_type,
            "state": {
                "instance": instance,
                "action_result": {
                    "status": "DONE"
                }
            }
        }
    
    elif capability_type == "devices.capabilities.toggle":
        instance = state.get("instance", "pause")
        value = state.get("value", False)
        logger.info(f"Device {device.id} toggle {instance}: {value}")
        
        return {
            "type": capability_type,
            "state": {
                "instance": instance,
                "action_result": {
                    "status": "DONE"
                }
            }
        }
    
    elif capability_type == "devices.capabilities.color_setting":
        # Поддерживаем как RGB, так и temperature_k
        if "rgb" in state:
            rgb = state["rgb"]
            logger.info(f"Device {device.id} color_setting rgb: {rgb}")
            return {
                "type": capability_type,
                "state": {
                    "instance": "rgb",
                    "action_result": {
                        "status": "DONE"
                    }
                }
            }
        elif "temperature_k" in state:
            temp = state["temperature_k"]
            logger.info(f"Device {device.id} color_setting temperature_k: {temp}")
            return {
                "type": capability_type,
                "state": {
                    "instance": "temperature_k",
                    "action_result": {
                        "status": "DONE"
                    }
                }
            }
        else:
            raise ValueError("color_setting requires either 'rgb' or 'temperature_k' in state")
    
    elif capability_type == "devices.capabilities.video_stream":
        # Для камер
        logger.info(f"Device {device.id} video_stream action")
        return {
            "type": capability_type,
            "state": {
                "instance": "stream",
                "action_result": {
                    "status": "DONE"
                }
            }
        }
    
    else:
        logger.warning(f"Unknown capability type: {capability_type}, treating as on_off")
        # Fallback для неизвестных типов
        return {
            "type": capability_type,
            "state": {
                "instance": "on",
                "action_result": {
                    "status": "DONE"
                }
            }
        }
