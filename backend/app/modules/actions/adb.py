from .base import Action, ActionResult
from typing import Literal
import asyncio


class ADBAction(Action):
    type: Literal["adb"] = "adb"

    def config_schema(self) -> dict:
        return {
            "type": "object",
            "properties": {
                "host": {"type": "string"},
                "port": {"type": "integer", "default": 5555},
                "command": {"type": "string"}
            },
            "required": ["host", "port", "command"]
        }

    async def execute(self, payload: dict) -> ActionResult:
        host = payload.get("host")
        port = int(payload.get("port", 5555))
        cmd = payload.get("command")
        if not host or not cmd:
            return {"ok": False, "error": "invalid config"}
        proc = await asyncio.create_subprocess_exec(
            "adb", "-s", f"{host}:{port}", "shell", cmd,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            return {"ok": False, "error": (stderr or stdout).decode(errors="ignore")}
        return {"ok": True, "output": stdout.decode(errors="ignore")}


