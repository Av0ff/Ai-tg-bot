from aiogram.filters import CommandStart
from aiogram import Router
from aiogram.types import Message


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        "Hi! I am the stationery store assistant. Ask about orders, delivery, "
        "returns, or product availability."
    )
