from fastapi import APIRouter

from app.api.api_v1.endpoints import (
    auth, devices, scenarios, yandex, mqtt, yapi, adb, websocket
)

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(devices.router, prefix="/devices", tags=["devices"])
api_router.include_router(scenarios.router, prefix="/scenarios", tags=["scenarios"])
api_router.include_router(yandex.router, prefix="/yandex", tags=["yandex"])
api_router.include_router(mqtt.router, prefix="/mqtt", tags=["mqtt"])
api_router.include_router(yapi.router, prefix="/yapi", tags=["yapi"])
api_router.include_router(adb.router, prefix="/adb", tags=["adb"])
api_router.include_router(websocket.router, prefix="/ws", tags=["websocket"])
