"""FastAPI entry point for cloud deployment.

This wraps the bot with a minimal HTTP server so platforms like
fastapicloud can health-check and manage the service.
Uses HttpXProvider (no browser needed) for cloud compatibility.
"""
from __future__ import annotations

import asyncio
import logging
import os
import sys
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from config import Config
from logger import setup_logging

logger = setup_logging("INFO")
bot_task: asyncio.Task | None = None


async def run_bot() -> None:
    """Run the monitoring bot in background."""
    from services.monitor import Monitor

    config = Config.load()
    monitor = Monitor(config, logger)
    await monitor.run_continuous()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Start bot on startup, cleanup on shutdown."""
    global bot_task
    config = Config.load()

    errors = config.validate()
    if errors:
        logger.warning(f"Config invalid — bot not started: {errors}")
    elif not config.x_cookies_configured():
        logger.warning("X cookies not configured — bot not started")
    else:
        logger.info("Starting bot in background...")
        bot_task = asyncio.create_task(run_bot())

    yield

    if bot_task:
        bot_task.cancel()
        try:
            await bot_task
        except asyncio.CancelledError:
            pass


app = FastAPI(
    title="Arc NFT Whitelist Hunter",
    description="Monitor X for Arc NFT whitelist opportunities",
    version="1.0.0",
    lifespan=lifespan,
)


@app.get("/")
async def root():
    return {"status": "running", "service": "arc-nft-whitelist-hunter"}


@app.get("/health")
async def health():
    """Health check endpoint."""
    config = Config.load()
    return JSONResponse({
        "status": "healthy",
        "telegram": config.telegram_configured(),
        "discord": bool(config.discord_webhook_url),
        "x_cookies": config.x_cookies_configured(),
        "bot_running": bot_task is not None and not bot_task.done(),
    })


@app.get("/stats")
async def stats():
    """Database statistics."""
    from database.db import Database

    db = Database(Config.load(), logger)
    await db.initialize()
    data = await db.get_stats()
    await db.close()
    return data


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host="0.0.0.0", port=port)
