"""
CleanBreath AI – FastAPI application entry point.
"""
from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.routers.api import router as api_router

settings = get_settings()

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
)
logger = logging.getLogger("cleanbreath")

app = FastAPI(
    title="CleanBreath AI API",
    version="0.1.0",
    description="Air quality guidance, risk classification, and AI chat for families.",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/", tags=["health"])
async def root() -> dict:
    return {"service": "CleanBreath AI API", "status": "ok", "phase": "0 – scaffold"}


@app.get("/health", tags=["health"])
async def health() -> dict:
    return {"status": "ok"}
