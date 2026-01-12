from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder


router = Router()


def build_ticket_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Resolved", callback_data="ticket:resolved")
    builder.button(text="Need specialist", callback_data="ticket:needs_agent")
    builder.adjust(2)
    return builder.as_markup()


@router.message(F.text)
async def echo_handler(message: Message) -> None:
    await message.answer(
        f"Got it: {message.text}",
        reply_markup=build_ticket_keyboard(),
    )
