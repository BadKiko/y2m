import asyncio
import json
import logging
from typing import Dict, Callable, Any, Optional
from asyncio_mqtt import Client, MqttError
from contextlib import asynccontextmanager

from app.core.config import settings

logger = logging.getLogger(__name__)

class MQTTService:
    def __init__(self):
        self.client: Optional[Client] = None
        self.subscriptions: Dict[str, Callable] = {}
        self.connected = False
        self._reconnect_task: Optional[asyncio.Task] = None

    async def connect(self):
        """Connect to MQTT broker"""
        try:
            self.client = Client(
                hostname=settings.MQTT_BROKER,
                port=settings.MQTT_PORT,
                username=settings.MQTT_USERNAME or None,
                password=settings.MQTT_PASSWORD or None,
            )
            await self.client.connect()
            self.connected = True
            logger.info(f"Connected to MQTT broker {settings.MQTT_BROKER}:{settings.MQTT_PORT}")

            # Start auto-reconnect task
            self._reconnect_task = asyncio.create_task(self._keep_alive())

        except Exception as e:
            logger.error(f"Failed to connect to MQTT broker: {e}")
            self.connected = False
            raise

    async def disconnect(self):
        """Disconnect from MQTT broker"""
        if self._reconnect_task:
            self._reconnect_task.cancel()
            try:
                await self._reconnect_task
            except asyncio.CancelledError:
                pass

        if self.client:
            await self.client.disconnect()
        self.connected = False
        logger.info("Disconnected from MQTT broker")

    async def _keep_alive(self):
        """Keep connection alive and reconnect on failure"""
        while True:
            try:
                await asyncio.sleep(30)  # Check connection every 30 seconds
                if not self.connected and self.client:
                    await self.connect()
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"MQTT keep-alive error: {e}")
                await asyncio.sleep(5)

    async def publish(self, topic: str, payload: Any, qos: int = 0, retain: bool = False):
        """Publish message to MQTT topic"""
        if not self.connected or not self.client:
            raise MqttError("Not connected to MQTT broker")

        try:
            if isinstance(payload, (dict, list)):
                payload = json.dumps(payload)

            await self.client.publish(topic, payload, qos=qos, retain=retain)
            logger.debug(f"Published to {topic}: {payload}")

        except Exception as e:
            logger.error(f"Failed to publish to {topic}: {e}")
            raise

    async def subscribe(self, topic: str, callback: Callable[[str, str], Any], qos: int = 0):
        """Subscribe to MQTT topic"""
        if not self.connected or not self.client:
            raise MqttError("Not connected to MQTT broker")

        try:
            await self.client.subscribe(topic, qos=qos)
            self.subscriptions[topic] = callback
            logger.info(f"Subscribed to {topic}")

        except Exception as e:
            logger.error(f"Failed to subscribe to {topic}: {e}")
            raise

    async def unsubscribe(self, topic: str):
        """Unsubscribe from MQTT topic"""
        if not self.connected or not self.client:
            raise MqttError("Not connected to MQTT broker")

        try:
            await self.client.unsubscribe(topic)
            if topic in self.subscriptions:
                del self.subscriptions[topic]
            logger.info(f"Unsubscribed from {topic}")

        except Exception as e:
            logger.error(f"Failed to unsubscribe from {topic}: {e}")
            raise

    async def listen(self):
        """Listen for incoming messages (should be run in background task)"""
        if not self.connected or not self.client:
            raise MqttError("Not connected to MQTT broker")

        try:
            async with self.client.messages() as messages:
                async for message in messages:
                    topic = message.topic
                    payload = message.payload.decode()

                    if topic in self.subscriptions:
                        try:
                            await self.subscriptions[topic](topic, payload)
                        except Exception as e:
                            logger.error(f"Error in callback for {topic}: {e}")

        except Exception as e:
            logger.error(f"Error listening for MQTT messages: {e}")
            raise

# Global MQTT service instance
mqtt_service = MQTTService()
