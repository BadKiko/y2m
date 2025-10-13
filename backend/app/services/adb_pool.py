import asyncio
import logging
import contextlib
from typing import Optional

from models.device import Device

logger = logging.getLogger(__name__)


async def _run_cmd(cmd: list[str], timeout: float = 15.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        return 124, "", "timeout"
    return proc.returncode, stdout.decode(errors="ignore"), stderr.decode(errors="ignore")


async def ensure_connected(host: str, port: int) -> bool:
    code, out, err = await _run_cmd(["adb", "connect", f"{host}:{port}"])
    if code == 0:
        logger.info("ADB connected to %s:%s -> %s", host, port, out.strip())
        return True
    logger.warning("ADB connect failed %s:%s -> %s %s", host, port, code, err or out)
    return False


async def background_autoconnect(stop_event: asyncio.Event, interval_sec: int = 60):
    # periodically (re)connect to all devices with adb_host
    while not stop_event.is_set():
        try:
            devices = await Device.filter(adb_host__not=None)
            for d in devices:
                if d.adb_host and d.adb_port:
                    await ensure_connected(d.adb_host, d.adb_port)
        except Exception as exc:  # pragma: no cover
            logger.exception("ADB autoconnect loop error: %s", exc)
        await asyncio.wait_for(stop_event.wait(), timeout=interval_sec)


class ADBPool:
    def __init__(self) -> None:
        self._stop_event: Optional[asyncio.Event] = None
        self._task: Optional[asyncio.Task] = None

    async def start(self):
        if self._task and not self._task.done():
            return
        self._stop_event = asyncio.Event()
        self._task = asyncio.create_task(background_autoconnect(self._stop_event))

    async def stop(self):
        if self._stop_event:
            self._stop_event.set()
        if self._task:
            try:
                await asyncio.wait_for(self._task, timeout=5.0)
            except asyncio.TimeoutError:
                self._task.cancel()
                with contextlib.suppress(Exception):
                    await self._task


adb_pool = ADBPool()


