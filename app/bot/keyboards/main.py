from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from app.i18n import get_text


def main_keyboard(language: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=get_text(language, "media"),
                    callback_data="section:media",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(language, "music"),
                    callback_data="section:music",
                )
            ],
            [
                InlineKeyboardButton(
                    text=get_text(language, "language"),
                    callback_data="language:menu",
                )
            ],
        ]
    )


def language_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="🇺🇿 O‘zbekcha", callback_data="language:uz"),
                InlineKeyboardButton(text="🇷🇺 Русский", callback_data="language:ru"),
            ],
            [
                InlineKeyboardButton(text="🇬🇧 English", callback_data="language:en"),
            ],
        ]
    )
