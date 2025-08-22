from sqlalchemy import Column, Integer, String, DateTime, JSON, Text
from sqlalchemy.sql import func

from app.core.database import Base

class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), server_default=func.now(), index=True)
    user = Column(String, index=True)
    action = Column(String, index=True)
    resource = Column(String)  # device, scenario, etc.
    resource_id = Column(Integer)
    payload = Column(JSON)  # Additional data
    ip_address = Column(String)
    user_agent = Column(Text)
