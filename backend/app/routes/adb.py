import asyncio
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field


router = APIRouter(prefix="/api/adb", tags=["adb"])


class ConnectBody(BaseModel):
    host: str
    port: int = Field(5555, ge=1, le=65535)


class ExecBody(ConnectBody):
    cmd: str


class DisconnectBody(ConnectBody):
    pass


async def run_cmd(cmd: list[str], timeout: float = 20.0) -> tuple[int, str, str]:
    proc = await asyncio.create_subprocess_exec(
        *cmd, stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
    )
    try:
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
    except asyncio.TimeoutError:
        proc.kill()
        raise HTTPException(status_code=408, detail="ADB timeout")
    return proc.returncode, stdout.decode(errors="ignore"), stderr.decode(errors="ignore")


@router.post("/connect")
async def adb_connect(body: ConnectBody):
    code, out, err = await run_cmd(["adb", "connect", f"{body.host}:{body.port}"])
    if code != 0:
        raise HTTPException(status_code=500, detail=err or out or "adb connect failed")
    return {"ok": True, "output": out}


@router.post("/exec")
async def adb_exec(body: ExecBody):
    code, out, err = await run_cmd(["adb", "-s", f"{body.host}:{body.port}", "shell", body.cmd])
    if code != 0:
        raise HTTPException(status_code=500, detail=err or out or "adb shell failed")
    return {"ok": True, "output": out}


@router.post("/disconnect")
async def adb_disconnect(body: DisconnectBody):
    code, out, err = await run_cmd(["adb", "disconnect", f"{body.host}:{body.port}"])
    if code != 0:
        raise HTTPException(status_code=500, detail=err or out or "adb disconnect failed")
    return {"ok": True, "output": out}


@router.get("/devices")
async def adb_devices():
    code, out, err = await run_cmd(["adb", "devices"])
    if code != 0:
        raise HTTPException(status_code=500, detail=err or out or "adb devices failed")
    return {"ok": True, "output": out}


