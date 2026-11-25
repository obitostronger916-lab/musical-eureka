import asyncio
import logging
from contextlib import asynccontextmanager

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
    bot: Bot | None = None
    polling_task: asyncio.Task | None = None
    try:
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
        yield
    finally:
        if polling_task is not None:
            if not polling_task.done():
                polling_task.cancel()
            try:
                await polling_task
            except asyncio.CancelledError:
                pass
            except Exception:
                logger.exception("Telegram polling task stopped with an error")
        if bot is not None:
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
    if polling_task is None or polling_task.done():
        raise HTTPException(status_code=503, detail="Telegram polling is not running")
    return {"status": "ok", "service": "Universal Media"}


@app.get("/")
async def root():
    return {
        "name": "Universal Media",
        "status": "running",
        "health": "/health",
    }
