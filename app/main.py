import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from aiogram import Bot, Dispatcher
from fastapi import FastAPI, HTTPException

from app.bot.handlers.start import router
from app.config import get_settings
from app.database import close, connect, get_pool


logger = logging.getLogger("universal_media")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    await connect()
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    # This service uses long polling; remove any stale webhook configuration.
    await bot.delete_webhook(drop_pending_updates=False)
    polling_task = asyncio.create_task(
        dispatcher.start_polling(
            bot,
            handle_signals=False,
            allowed_updates=dispatcher.resolve_used_update_types(),
        ),
        name="telegram-polling",
    )
    app.state.bot = bot
    app.state.polling_task = polling_task
    logger.info("Universal Media started")

    try:
        yield
    finally:
        polling_task.cancel()
        with suppress(asyncio.CancelledError):
            await polling_task
        await bot.session.close()
        await close()
        logger.info("Universal Media stopped")


app = FastAPI(title="Universal Media API", lifespan=lifespan)


@app.get("/health")
async def health():
    try:
        await get_pool().fetchval("SELECT 1")
    except Exception as exc:
        raise HTTPException(status_code=503, detail="Database unavailable") from exc

    polling_task = getattr(app.state, "polling_task", None)
    if polling_task is not None and polling_task.done():
        if not polling_task.cancelled() and polling_task.exception() is not None:
            raise HTTPException(status_code=503, detail="Telegram polling stopped")
    return {"status": "ok", "service": "Universal Media"}


@app.get("/")
async def root():
    return {
        "name": "Universal Media",
        "status": "running",
        "health": "/health",
    }
