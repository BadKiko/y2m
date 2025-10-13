from fastapi import APIRouter
import json
from pathlib import Path


router = APIRouter(prefix="/api/device-types", tags=["device-types"])

DATA_PATH = Path(__file__).resolve().parents[1] / "data" / "yandex_device_types.json"


@router.get("")
async def list_device_types():
    with DATA_PATH.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return data


