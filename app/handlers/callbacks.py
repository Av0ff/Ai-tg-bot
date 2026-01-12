from aiogram import F, Router
from aiogram.types import CallbackQuery


router = Router()


@router.callback_query(F.data.in_({"ticket:resolved", "ticket:needs_agent"}))
async def ticket_status_handler(callback: CallbackQuery) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return

    if callback.data == "ticket:resolved":
        status_text = "Status updated: resolved."
    else:
        status_text = "Status updated: needs a specialist."

    await callback.message.edit_text(status_text)
    await callback.answer("Updated.")
