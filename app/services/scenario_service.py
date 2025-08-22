import logging
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import and_

from app.models.scenario import ButtonScenario
from app.schemas.scenario import ButtonScenarioCreate, ButtonScenarioUpdate

logger = logging.getLogger(__name__)

class ScenarioService:
    @staticmethod
    async def create_scenario(db: AsyncSession, scenario: ButtonScenarioCreate) -> ButtonScenario:
        """Create a new button scenario"""
        db_scenario = ButtonScenario(
            device_id=scenario.device_id,
            button_name=scenario.button_name,
            name=scenario.name,
            actions=scenario.actions
        )

        db.add(db_scenario)
        await db.commit()
        await db.refresh(db_scenario)

        logger.info(f"Created scenario: {scenario.name} for device {scenario.device_id}")
        return db_scenario

    @staticmethod
    async def get_scenario(db: AsyncSession, scenario_id: int) -> Optional[ButtonScenario]:
        """Get scenario by ID"""
        result = await db.execute(select(ButtonScenario).where(ButtonScenario.id == scenario_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_scenarios_by_device(db: AsyncSession, device_id: int) -> List[ButtonScenario]:
        """Get all scenarios for a device"""
        result = await db.execute(
            select(ButtonScenario).where(
                and_(
                    ButtonScenario.device_id == device_id,
                    ButtonScenario.is_active == True
                )
            )
        )
        return result.scalars().all()

    @staticmethod
    async def get_scenarios(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[ButtonScenario]:
        """Get all scenarios with pagination"""
        result = await db.execute(
            select(ButtonScenario).offset(skip).limit(limit)
        )
        return result.scalars().all()

    @staticmethod
    async def update_scenario(db: AsyncSession, scenario_id: int, scenario_update: ButtonScenarioUpdate) -> Optional[ButtonScenario]:
        """Update scenario"""
        result = await db.execute(select(ButtonScenario).where(ButtonScenario.id == scenario_id))
        db_scenario = result.scalar_one_or_none()

        if not db_scenario:
            return None

        update_data = scenario_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_scenario, field, value)

        await db.commit()
        await db.refresh(db_scenario)

        logger.info(f"Updated scenario: {db_scenario.name}")
        return db_scenario

    @staticmethod
    async def delete_scenario(db: AsyncSession, scenario_id: int) -> Optional[ButtonScenario]:
        """Delete scenario"""
        result = await db.execute(select(ButtonScenario).where(ButtonScenario.id == scenario_id))
        db_scenario = result.scalar_one_or_none()

        if not db_scenario:
            return None

        await db.delete(db_scenario)
        await db.commit()

        logger.info(f"Deleted scenario: {db_scenario.name}")
        return db_scenario

    @staticmethod
    async def get_button_scenarios(db: AsyncSession, device_id: int, button_name: str) -> List[ButtonScenario]:
        """Get scenarios for specific button on device"""
        result = await db.execute(
            select(ButtonScenario).where(
                and_(
                    ButtonScenario.device_id == device_id,
                    ButtonScenario.button_name == button_name,
                    ButtonScenario.is_active == True
                )
            )
        )
        return result.scalars().all()

# Global scenario service instance
scenario_service = ScenarioService()
