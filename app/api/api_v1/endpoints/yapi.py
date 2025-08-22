import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.api_v1.endpoints.auth import get_current_user
from app.schemas.yapi import YAPIExecuteRequest
from app.services.yapi_service import yapi_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/execute")
async def execute_yapi_command(
    *,
    execute_request: YAPIExecuteRequest,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Execute silent command on Yandex Station via YAPI.
    """
    try:
        result = await yapi_service.execute_command(
            execute_request.command,
            execute_request.target_station,
            execute_request.params
        )

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Unknown error")
            )

        return result

    except Exception as e:
        logger.error(f"Failed to execute YAPI command: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute command: {str(e)}"
        )

@router.get("/stations")
async def get_yandex_stations(
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Get list of available Yandex stations.
    """
    try:
        result = await yapi_service.get_stations()

        if not result["success"]:
            raise HTTPException(
                status_code=500,
                detail=result.get("error", "Failed to get stations")
            )

        return result

    except Exception as e:
        logger.error(f"Failed to get Yandex stations: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to get stations: {str(e)}"
        )

@router.get("/status")
async def get_yapi_status(
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Get YAPI service connection status.
    """
    try:
        is_connected = await yapi_service.test_connection()

        return {
            "connected": is_connected,
            "service_url": yapi_service.base_url
        }

    except Exception as e:
        logger.error(f"Failed to test YAPI connection: {e}")
        return {
            "connected": False,
            "service_url": yapi_service.base_url,
            "error": str(e)
        }
