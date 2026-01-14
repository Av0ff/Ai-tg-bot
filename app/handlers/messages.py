import logging
import time

from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db import (
    add_ticket_message,
    create_ticket,
    get_open_ticket,
    get_session,
    get_ticket_messages,
    update_ticket_status,
)
from app.services.faq_prompt import build_system_prompt
from app.services.gpt_client import GPTClient
from app.services.triage import needs_agent


router = Router()
logger = logging.getLogger(__name__)
last_ticket_message_id = {}
CONTEXT_MESSAGE_LIMIT = 20


def build_ticket_keyboard(ticket_id: int):
    builder = InlineKeyboardBuilder()
    builder.button(text="Resolved", callback_data=f"ticket:resolved:{ticket_id}")
    builder.button(
        text="Need specialist", callback_data=f"ticket:needs_agent:{ticket_id}"
    )
    builder.adjust(2)
    return builder.as_markup()

def build_context_text(messages) -> str:
    if not messages:
        return ""
    lines = []
    for item in messages:
        if item.role == "user":
            role = "User"
        elif item.role == "assistant":
            role = "Assistant"
        else:
            role = "System"
        lines.append(f"{role}: {item.content}")
    return "\n".join(lines)

@router.message(F.text)
async def gpt_reply_handler(message: Message) -> None:
    user_text = message.text
    if not user_text:
        await message.answer("Please send a text message.")
        return

    user_id = message.from_user.id if message.from_user else None
    if user_id is None:
        await message.answer("Please send a text message.")
        return

    message_id = message.message_id
    text_len = len(user_text)
    logger.info(
        "GPT request started: user_id=%s message_id=%s text_len=%s",
        user_id,
        message_id,
        text_len,
    )
    try:
        async with get_session() as session:
            ticket = await get_open_ticket(session, user_id)
            if not ticket:
                ticket = await create_ticket(session, user_id)
            ticket_id = ticket.id

            history = await get_ticket_messages(
                session,
                ticket_id,
                limit=CONTEXT_MESSAGE_LIMIT,
            )
            context_text = build_context_text(history)
            await add_ticket_message(session, ticket_id, "user", user_text)

        start_time = time.monotonic()
        client = GPTClient()
        system_prompt = build_system_prompt()
        if context_text:
            system_prompt = (
                f"{system_prompt}\n\nConversation history:\n{context_text}"
            )
        reply_text, meta = await client.chat(
            user_text=user_text,
            system_prompt=system_prompt,
        )
    except Exception:
        logger.exception(
            "GPT request failed: user_id=%s message_id=%s",
            user_id,
            message_id,
        )
        await message.answer(
            "Sorry, something went wrong while generating a reply."
        )
        return

    duration_ms = int((time.monotonic() - start_time) * 1000)
    logger.info(
        "GPT request completed: status=%s duration_ms=%s model=%s request_id=%s "
        "prompt_tokens=%s completion_tokens=%s total_tokens=%s user_id=%s message_id=%s",
        meta.get("status_code"),
        duration_ms,
        meta.get("model"),
        meta.get("request_id"),
        meta.get("prompt_tokens"),
        meta.get("completion_tokens"),
        meta.get("total_tokens"),
        user_id,
        message_id,
    )

    needs_specialist = needs_agent(reply_text)
    if needs_specialist:
        logger.warning(
            "Triage: needs specialist: user_id=%s message_id=%s",
            user_id,
            message_id,
        )
        reply_text = f"{reply_text}\n\nStatus: needs a specialist."
        try:
            async with get_session() as session:
                await update_ticket_status(session, ticket_id, "needs_agent")
                await add_ticket_message(
                    session,
                    ticket_id,
                    "system",
                    "Status updated: needs a specialist.",
                )
        except Exception:
            logger.exception(
                "Failed to auto-update ticket status: user_id=%s message_id=%s",
                user_id,
                message_id,
            )

    try:
        async with get_session() as session:
            await add_ticket_message(session, ticket_id, "assistant", reply_text)
    except Exception:
        logger.exception(
            "Failed to store assistant message: user_id=%s message_id=%s",
            user_id,
            message_id,
        )

    chat_id = message.chat.id
    previous_message_id = last_ticket_message_id.get(chat_id)
    if previous_message_id:
        try:
            await message.bot.edit_message_reply_markup(
                chat_id=chat_id,
                message_id=previous_message_id,
                reply_markup=None,
            )
        except Exception:
            logger.info(
                "Failed to clear previous ticket keyboard: chat_id=%s message_id=%s",
                chat_id,
                previous_message_id,
            )

    reply_markup = None
    if not needs_specialist:
        reply_markup = build_ticket_keyboard(ticket_id)
    sent = await message.answer(reply_text, reply_markup=reply_markup)
    last_ticket_message_id[chat_id] = sent.message_id
