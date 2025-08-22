import json
import logging
from typing import Dict, Set

from fastapi import APIRouter, WebSocket, WebSocketDisconnect, Depends

from app.api.api_v1.endpoints.auth import get_current_user
from app.services.mqtt_service import mqtt_service

logger = logging.getLogger(__name__)

router = APIRouter()

# Store active WebSocket connections
active_connections: Dict[str, Set[WebSocket]] = {
    "mqtt": set(),
    "devices": set(),
    "general": set()
}

@router.websocket("/mqtt")
async def websocket_mqtt_endpoint(
    websocket: WebSocket,
    token: str = None  # Optional authentication
):
    """
    WebSocket endpoint for real-time MQTT message streaming.
    """
    await websocket.accept()

    # Basic token validation (simplified)
    if token:
        try:
            # You would validate the token here
            # For demo purposes, we'll accept any token
            pass
        except Exception:
            await websocket.close(code=1008)  # Policy violation
            return

    # Add to active connections
    active_connections["mqtt"].add(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "welcome",
            "message": "Connected to MQTT WebSocket"
        })

        # Listen for messages from client (optional)
        while True:
            data = await websocket.receive_text()
            # Handle client messages if needed
            logger.debug(f"WebSocket message received: {data}")

    except WebSocketDisconnect:
        logger.info("WebSocket MQTT connection closed")
    except Exception as e:
        logger.error(f"WebSocket MQTT error: {e}")
    finally:
        # Remove from active connections
        active_connections["mqtt"].discard(websocket)

@router.websocket("/devices")
async def websocket_devices_endpoint(
    websocket: WebSocket,
    token: str = None
):
    """
    WebSocket endpoint for real-time device status updates.
    """
    await websocket.accept()

    # Add to active connections
    active_connections["devices"].add(websocket)

    try:
        # Send welcome message
        await websocket.send_json({
            "type": "welcome",
            "message": "Connected to Devices WebSocket"
        })

        # Listen for messages from client
        while True:
            data = await websocket.receive_text()
            logger.debug(f"WebSocket devices message received: {data}")

    except WebSocketDisconnect:
        logger.info("WebSocket devices connection closed")
    except Exception as e:
        logger.error(f"WebSocket devices error: {e}")
    finally:
        # Remove from active connections
        active_connections["devices"].discard(websocket)

async def broadcast_mqtt_message(topic: str, payload: str):
    """
    Broadcast MQTT message to all connected WebSocket clients.
    """
    message = {
        "type": "mqtt_message",
        "topic": topic,
        "payload": payload,
        "timestamp": json.dumps({"topic": topic, "payload": payload})
    }

    # Broadcast to MQTT subscribers
    for connection in active_connections["mqtt"]:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send MQTT message to WebSocket: {e}")
            active_connections["mqtt"].discard(connection)

async def broadcast_device_update(device_id: int, status: Dict):
    """
    Broadcast device status update to all connected WebSocket clients.
    """
    message = {
        "type": "device_update",
        "device_id": device_id,
        "status": status,
        "timestamp": json.dumps({"device_id": device_id, "status": status})
    }

    # Broadcast to device subscribers
    for connection in active_connections["devices"]:
        try:
            await connection.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send device update to WebSocket: {e}")
            active_connections["devices"].discard(connection)

async def broadcast_general_message(message_type: str, data: Dict):
    """
    Broadcast general message to all connected WebSocket clients.
    """
    message = {
        "type": message_type,
        "data": data,
        "timestamp": json.dumps({"type": message_type, "data": data})
    }

    # Broadcast to all connections
    for connection_type, connections in active_connections.items():
        for connection in connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Failed to send general message to WebSocket: {e}")
                connections.discard(connection)

# Function to integrate with MQTT service
def setup_websocket_mqtt_integration():
    """
    Set up integration between MQTT service and WebSocket broadcasting.
    """
    async def mqtt_message_handler(topic: str, payload: str):
        # Broadcast MQTT message to WebSocket clients
        await broadcast_mqtt_message(topic, payload)

        # Also broadcast to general subscribers
        await broadcast_general_message("mqtt", {"topic": topic, "payload": payload})

    # Subscribe to all MQTT topics for WebSocket broadcasting
    # Note: In production, you might want to be more selective
    mqtt_service.subscriptions["websocket_broadcast"] = mqtt_message_handler
