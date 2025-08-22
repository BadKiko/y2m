from sqlalchemy import Column, Integer, String, DateTime, JSON, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship

from app.core.database import Base

class ButtonScenario(Base):
    __tablename__ = "button_scenarios"

    id = Column(Integer, primary_key=True, index=True)
    device_id = Column(Integer, ForeignKey("devices.id"))
    button_name = Column(String)  # button1, button2, etc.
    name = Column(String)  # Human readable name
    actions = Column(JSON)  # List of actions to execute
    is_active = Column(Integer, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationship
    device = relationship("Device")
