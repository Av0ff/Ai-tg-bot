import logging
import time

from aiogram import F, Router
from aiogram.types import Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.services.faq_prompt import build_system_prompt
from app.services.gpt_client import GPTClient
from app.services.triage import needs_agent


router = Router()
logger = logging.getLogger(__name__)
last_ticket_message_id = {}


def build_ticket_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="Resolved", callback_data="ticket:resolved")
    builder.button(text="Need specialist", callback_data="ticket:needs_agent")
    builder.adjust(2)
    return builder.as_markup()


@router.message(F.text)
async def gpt_reply_handler(message: Message) -> None:
    user_text = message.text
    if not user_text:
        await message.answer("Please send a text message.")
        return

    user_id = message.from_user.id if message.from_user else None
    message_id = message.message_id
    text_len = len(user_text)
    logger.info(
        "GPT request started: user_id=%s message_id=%s text_len=%s",
        user_id,
        message_id,
        text_len,
    )
    try:
        start_time = time.monotonic()
        client = GPTClient()
        system_prompt = build_system_prompt()
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

    if needs_agent(reply_text):
        logger.warning(
            "Triage: needs specialist: user_id=%s message_id=%s",
            user_id,
            message_id,
        )
        reply_text = f"{reply_text}\n\nStatus: needs a specialist."

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

    sent = await message.answer(reply_text, reply_markup=build_ticket_keyboard())
    last_ticket_message_id[chat_id] = sent.message_id
