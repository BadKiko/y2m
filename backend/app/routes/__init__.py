from fastapi import APIRouter

from .adb import router as adb_router
from .devices import router as devices_router
from .device_types import router as device_types_router
from .bindings import router as bindings_router
from .actions import router as actions_router
from .auth import router as auth_router
from .station_proxy import router as station_router
from .provider import router as provider_router
from .oauth import router as oauth_router


api_router = APIRouter()
api_router.include_router(adb_router)
api_router.include_router(devices_router)
api_router.include_router(device_types_router)
api_router.include_router(bindings_router)
api_router.include_router(actions_router)
api_router.include_router(auth_router)
api_router.include_router(station_router)
api_router.include_router(provider_router)
api_router.include_router(oauth_router)


