import asyncio
import logging
from contextlib import asynccontextmanager, suppress

from aiogram import Bot, Dispatcher
from fastapi import FastAPI

from app.bot.handlers.start import router
from app.config import get_settings
from app.database import close, connect


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    logging.basicConfig(level=settings.log_level.upper())

    await connect()
    bot = Bot(token=settings.bot_token)
    dispatcher = Dispatcher()
    dispatcher.include_router(router)

    polling_task = asyncio.create_task(
        dispatcher.start_polling(bot, handle_signals=False)
    )
    app.state.bot = bot

    try:
        yield
    finally:
        await dispatcher.stop_polling()
        polling_task.cancel()
        with suppress(asyncio.CancelledError):
            await polling_task
        await bot.session.close()
        await close()


app = FastAPI(title="Universal Media API", lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok", "service": "Universal Media"}


@app.get("/")
async def root():
    return {"name": "Universal Media", "status": "running"}
