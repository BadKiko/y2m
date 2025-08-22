import json
import logging
from typing import Any, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.api_v1.endpoints.auth import get_current_user
from app.core.database import get_db
from app.schemas.scenario import ButtonScenario, ButtonScenarioCreate, ButtonScenarioUpdate
from app.services.scenario_service import scenario_service
from app.services.device_service import device_service
from app.services.mqtt_service import mqtt_service
from app.services.yapi_service import yapi_service
from app.services.adb_service import adb_service

logger = logging.getLogger(__name__)

router = APIRouter()

@router.get("/", response_model=List[ButtonScenario])
async def read_scenarios(
    db: AsyncSession = Depends(get_db),
    skip: int = 0,
    limit: int = 100,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Retrieve scenarios.
    """
    scenarios = await scenario_service.get_scenarios(db, skip=skip, limit=limit)
    return scenarios

@router.post("/", response_model=ButtonScenario)
async def create_scenario(
    *,
    db: AsyncSession = Depends(get_db),
    scenario_in: ButtonScenarioCreate,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Create new scenario.
    """
    # Check if device exists
    device = await device_service.get_device(db, scenario_in.device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    scenario = await scenario_service.create_scenario(db, scenario_in)
    return scenario

@router.get("/{scenario_id}", response_model=ButtonScenario)
async def read_scenario(
    *,
    db: AsyncSession = Depends(get_db),
    scenario_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Get scenario by ID.
    """
    scenario = await scenario_service.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")
    return scenario

@router.put("/{scenario_id}", response_model=ButtonScenario)
async def update_scenario(
    *,
    db: AsyncSession = Depends(get_db),
    scenario_id: int,
    scenario_in: ButtonScenarioUpdate,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Update a scenario.
    """
    scenario = await scenario_service.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = await scenario_service.update_scenario(db, scenario_id, scenario_in)
    return scenario

@router.delete("/{scenario_id}", response_model=ButtonScenario)
async def delete_scenario(
    *,
    db: AsyncSession = Depends(get_db),
    scenario_id: int,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Delete a scenario.
    """
    scenario = await scenario_service.get_scenario(db, scenario_id)
    if not scenario:
        raise HTTPException(status_code=404, detail="Scenario not found")

    scenario = await scenario_service.delete_scenario(db, scenario_id)
    return scenario

@router.post("/devices/{device_id}/buttons/{button_name}/execute")
async def execute_button_scenario(
    *,
    db: AsyncSession = Depends(get_db),
    device_id: int,
    button_name: str,
    current_user: str = Depends(get_current_user),
) -> Any:
    """
    Execute scenario for device button.
    """
    # Check if device exists
    device = await device_service.get_device(db, device_id)
    if not device:
        raise HTTPException(status_code=404, detail="Device not found")

    # Get scenarios for this button
    scenarios = await scenario_service.get_button_scenarios(db, device_id, button_name)

    if not scenarios:
        raise HTTPException(status_code=404, detail="No scenarios found for this button")

    results = []

    for scenario in scenarios:
        for action in scenario.actions:
            result = await execute_action(action)
            results.append({
                "action": action.type,
                "result": result
            })

    return {
        "device_id": device_id,
        "button_name": button_name,
        "executed_scenarios": len(scenarios),
        "results": results
    }

async def execute_action(action: dict) -> dict:
    """Execute a single action"""
    try:
        action_type = action.get("type")
        params = action.get("params", {})

        if action_type == "mqtt_publish":
            return await execute_mqtt_action(params)
        elif action_type == "yapi_call":
            return await execute_yapi_action(params)
        elif action_type == "adb_cmd":
            return await execute_adb_action(params)
        elif action_type == "delay":
            return await execute_delay_action(params)
        else:
            return {"success": False, "error": f"Unknown action type: {action_type}"}

    except Exception as e:
        logger.error(f"Error executing action {action_type}: {e}")
        return {"success": False, "error": str(e)}

async def execute_mqtt_action(params: dict) -> dict:
    """Execute MQTT publish action"""
    try:
        topic = params.get("topic")
        payload = params.get("payload")
        qos = params.get("qos", 0)

        if isinstance(payload, (dict, list)):
            payload = json.dumps(payload)

        await mqtt_service.publish(topic, payload, qos)
        return {"success": True, "topic": topic, "payload": payload}

    except Exception as e:
        return {"success": False, "error": str(e)}

async def execute_yapi_action(params: dict) -> dict:
    """Execute YAPI action"""
    try:
        command = params.get("command")
        target_station = params.get("target_station")

        result = await yapi_service.execute_command(command, target_station)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}

async def execute_adb_action(params: dict) -> dict:
    """Execute ADB action"""
    try:
        device_id = params.get("device_id")
        command = params.get("command")
        timeout = params.get("timeout", 30)

        result = await adb_service.execute_command(device_id, command, timeout)
        return result

    except Exception as e:
        return {"success": False, "error": str(e)}

async def execute_delay_action(params: dict) -> dict:
    """Execute delay action"""
    try:
        seconds = params.get("seconds", 1)
        await asyncio.sleep(seconds)
        return {"success": True, "delay": seconds}

    except Exception as e:
        return {"success": False, "error": str(e)}
