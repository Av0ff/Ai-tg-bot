import asyncio
import logging
import os
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher

from app.handlers.start import router as start_router
from app.handlers.messages import router as messages_router
from app.handlers.callbacks import router as callback_router


load_dotenv()


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        handlers=[
            logging.FileHandler("bot.log", encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )

    token = os.getenv("BOT_TOKEN")
    if not token:
        raise RuntimeError("BOT_TOKEN is not set")

    bot = Bot(token=token)
    dp = Dispatcher()
    dp.include_router(start_router)
    dp.include_router(messages_router)
    dp.include_router(callback_router)

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
