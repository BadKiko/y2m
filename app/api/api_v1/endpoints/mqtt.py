import logging
from typing import Any

from fastapi import APIRouter, Depends, HTTPException

from app.api.api_v1.endpoints.auth import get_current_user
from app.schemas.mqtt import MQTTPublishRequest
from app.services.mqtt_service import mqtt_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.post("/publish")
async def publish_mqtt_message(
    *,
    publish_request: MQTTPublishRequest,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Publish message to MQTT topic.
    """
    try:
        await mqtt_service.publish(
            publish_request.topic,
            publish_request.payload,
            publish_request.qos,
            publish_request.retain
        )

        return {
            "success": True,
            "topic": publish_request.topic,
            "message": "Message published successfully"
        }

    except Exception as e:
        logger.error(f"Failed to publish MQTT message: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to publish message: {str(e)}"
        )

@router.get("/status")
async def get_mqtt_status(
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Get MQTT broker connection status.
    """
    return {
        "connected": mqtt_service.connected,
        "broker": mqtt_service.client.hostname if mqtt_service.client else None,
        "port": mqtt_service.client.port if mqtt_service.client else None
    }

@router.post("/subscribe")
async def subscribe_mqtt_topic(
    *,
    topic: str,
    qos: int = 0,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Subscribe to MQTT topic.
    """
    try:
        await mqtt_service.subscribe(topic, lambda t, p: logger.info(f"MQTT: {t} -> {p}"), qos)

        return {
            "success": True,
            "topic": topic,
            "message": "Subscribed successfully"
        }

    except Exception as e:
        logger.error(f"Failed to subscribe to MQTT topic: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to subscribe: {str(e)}"
        )

@router.post("/unsubscribe")
async def unsubscribe_mqtt_topic(
    *,
    topic: str,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Unsubscribe from MQTT topic.
    """
    try:
        await mqtt_service.unsubscribe(topic)

        return {
            "success": True,
            "topic": topic,
            "message": "Unsubscribed successfully"
        }

    except Exception as e:
        logger.error(f"Failed to unsubscribe from MQTT topic: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to unsubscribe: {str(e)}"
        )
