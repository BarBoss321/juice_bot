from aiogram.exceptions import TelegramBadRequest
from aiogram.types import Message, InlineKeyboardMarkup


async def safe_edit_text(
    message: Message,
    text: str,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str = "HTML",
    **kwargs
):
    try:
        await message.edit_text(
            text,
            reply_markup=reply_markup,
            parse_mode=parse_mode,
            **kwargs
        )
    except TelegramBadRequest as e:
        if "message is not modified" in str(e):
            return
        raise