from tortoise import Tortoise
from settings import settings


TORTOISE_ORM = {
    "connections": {"default": settings.database_url},
    "apps": {
        "models": {
            "models": [
                "models.device",
                "models.binding",
                "models.user_token",
            ],
            "default_connection": "default",
        }
    },
}


async def init_db() -> None:
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_db() -> None:
    await Tortoise.close_connections()


