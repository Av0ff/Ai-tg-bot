import logging

from aiogram import F, Router
from aiogram.types import CallbackQuery

from app.db import add_ticket_message, get_session, get_ticket, update_ticket_status


router = Router()
logger = logging.getLogger(__name__)


@router.callback_query(F.data.startswith("ticket:"))
async def ticket_status_handler(callback: CallbackQuery) -> None:
    if not callback.data or not callback.message:
        await callback.answer()
        return

    parts = callback.data.split(":")
    if len(parts) != 3:
        await callback.answer("Invalid action.")
        return

    action = parts[1]
    try:
        ticket_id = int(parts[2])
    except ValueError:
        await callback.answer("Invalid ticket.")
        return

    user_id = callback.from_user.id if callback.from_user else None
    message_id = callback.message.message_id
    if user_id is None:
        await callback.answer("No user.")
        return

    if action == "resolved":
        status_text = "Status updated: resolved."
        new_status = "resolved"
        logger.info(
            "Ticket status updated: resolved user_id=%s message_id=%s",
            user_id,
            message_id,
        )
    elif action == "needs_agent":
        status_text = "Status updated: needs a specialist."
        new_status = "needs_agent"
        logger.warning(
            "Ticket status updated: needs specialist user_id=%s message_id=%s",
            user_id,
            message_id,
        )
    else:
        await callback.answer("Unknown action.")
        return

    try:
        async with get_session() as session:
            ticket = await get_ticket(session, ticket_id)
            if not ticket:
                await callback.answer("Ticket not found.")
                return
            if ticket.user_id != user_id:
                await callback.answer("Not your ticket.")
                return
            if ticket.status != "open":
                await callback.answer("Ticket already closed.")
                return
            await update_ticket_status(session, ticket_id, new_status)
            await add_ticket_message(session, ticket_id, "system", status_text)
    except Exception:
        logger.exception(
            "Failed to update ticket status: user_id=%s message_id=%s",
            user_id,
            message_id,
        )
        await callback.answer("Update failed.")
        return

    await callback.message.edit_text(status_text)
    await callback.answer("Updated.")
