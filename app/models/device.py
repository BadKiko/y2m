from sqlalchemy import Column, Integer, String, DateTime, JSON, Boolean
from sqlalchemy.sql import func

from app.core.database import Base

class Device(Base):
    __tablename__ = "devices"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, index=True)
    type = Column(String)  # switch, sensor, light, etc.
    mqtt_base_topic = Column(String, unique=True, index=True)
    state_topic = Column(String, unique=True, index=True)
    command_topic = Column(String, unique=True, index=True)
    is_active = Column(Boolean, default=True)
    meta = Column(JSON)  # Additional device metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
