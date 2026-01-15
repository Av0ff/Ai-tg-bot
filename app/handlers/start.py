from aiogram.filters import CommandStart
from aiogram import Router
from aiogram.types import Message

from app.services.assistant_profile import load_assistant_profile


router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    profile = load_assistant_profile()
    await message.answer(profile)
