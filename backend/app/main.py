from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from settings import settings
from db import init_db, close_db
from services.adb_pool import adb_pool
from services.mqtt_service import mqtt_service
from routes import api_router

# Настройка логирования
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(title="y2m", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.on_event("startup")
async def on_startup():
    await init_db()
    app.include_router(api_router)
    await adb_pool.start()
    await mqtt_service.start()


@app.on_event("shutdown")
async def on_shutdown():
    await adb_pool.stop()
    await mqtt_service.stop()
    await close_db()


