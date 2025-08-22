from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.config import settings

# For SQLite (development)
if "sqlite" in settings.DATABASE_URL:
    engine = create_async_engine(
        settings.DATABASE_URL,
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
        echo=True,
    )
else:
    # For PostgreSQL (production)
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=True,
    )

AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

Base = declarative_base()

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()

async def create_db_and_tables():
    """Create database tables"""
    async with engine.begin() as conn:
        # Import all models here to ensure they are registered with SQLAlchemy
        from app.models import device, scenario, yandex_account, adb_device, audit_log
        await conn.run_sync(Base.metadata.create_all)
