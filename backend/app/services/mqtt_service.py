import asyncio
import json
from typing import Callable

import aiomqtt

from settings import settings
from models.binding import Binding
from modules.actions.adb import ADBAction
from modules.actions.station import StationAction


async def run_mqtt(stop_event: asyncio.Event):
    async with aiomqtt.Client(hostname=settings.mqtt_host, port=settings.mqtt_port) as client:
        topic = "y2m/bindings/+/invoke"
        await client.subscribe(topic)

        async with client.messages() as messages:
            async for message in messages:
                if stop_event.is_set():
                    break
                payload = message.payload.decode("utf-8", errors="ignore")
                try:
                    data = json.loads(payload) if payload else {}
                except Exception:
                    data = {}

                # bindingId from topic
                parts = message.topic.value.split("/")
                binding_id = int(parts[2]) if len(parts) >= 4 else None
                if not binding_id:
                    continue
                b = await Binding.get_or_none(id=binding_id)
                if not b:
                    continue

                result = {"ok": False}
                if b.action_type == "adb":
                    result = await ADBAction().execute({**(b.action_config or {}), **data})
                elif b.action_type == "station":
                    result = await StationAction().execute({**(b.action_config or {}), **data})

                state_topic = f"y2m/devices/{b.device_id}/state"
                await client.publish(state_topic, json.dumps({
                    "bindingId": b.id,
                    "capability": b.capability,
                    "result": result
                }), qos=0, retain=False)


class MQTTService:
    def __init__(self) -> None:
        self._stop: asyncio.Event | None = None
        self._task: asyncio.Task | None = None

    async def start(self) -> None:
        if self._task and not self._task.done():
            return
        self._stop = asyncio.Event()
        self._task = asyncio.create_task(run_mqtt(self._stop))

    async def stop(self) -> None:
        if self._stop:
            self._stop.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5)
            except asyncio.TimeoutError:
                self._task.cancel()


mqtt_service = MQTTService()


