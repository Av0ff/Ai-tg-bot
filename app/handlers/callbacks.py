import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery


router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.in_({"ticket:resolved", "ticket:needs_agent"}))
async def ticket_status_handler(callback: CallbackQuery) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return

    user_id = callback.from_user.id if callback.from_user else None
    message_id = callback.message.message_id

    if callback.data == "ticket:resolved":
        status_text = "Status updated: resolved."
        logger.info(
            "Ticket status updated: resolved user_id=%s message_id=%s",
            user_id,
            message_id,
        )
    else:
        status_text = "Status updated: needs a specialist."
        logger.warning(
            "Ticket status updated: needs specialist user_id=%s message_id=%s",
            user_id,
            message_id,
        )

    await callback.message.edit_text(status_text)
    await callback.answer("Updated.")
