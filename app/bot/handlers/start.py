from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.types import CallbackQuery, Message

from app.config import get_settings
from app.database import save_user, set_user_language
from app.i18n import get_text
from app.bot.keyboards.main import language_keyboard, main_keyboard

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    if message.from_user is None:
        return
    language = await save_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name or "",
    )
    await message.answer(
        f"{get_text(language, 'welcome')}\n\n{get_text(language, 'choose')}",
        reply_markup=main_keyboard(language),
    )


@router.message(Command("language"))
async def language_command(message: Message) -> None:
    if message.from_user is None:
        return
    await save_user(
        telegram_id=message.from_user.id,
        username=message.from_user.username,
        first_name=message.from_user.first_name or "",
    )
    await message.answer(
        "Tilni tanlang / Выберите язык / Choose a language:",
        reply_markup=language_keyboard(),
    )


@router.callback_query(F.data == "language:menu")
async def language_menu(callback: CallbackQuery) -> None:
    await callback.message.answer(
        "Tilni tanlang / Выберите язык / Choose a language:",
        reply_markup=language_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("language:"))
async def language_selected(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        return
    language = callback.data.split(":", 1)[1]
    if language not in {"uz", "ru", "en"}:
        await callback.answer("Unsupported language", show_alert=True)
        return
    await save_user(
        telegram_id=callback.from_user.id,
        username=callback.from_user.username,
        first_name=callback.from_user.first_name or "",
    )
    await set_user_language(callback.from_user.id, language)
    await callback.message.answer(
        f"{get_text(language, 'language_saved')}\n"
        f"{get_text(language, 'choose')}",
        reply_markup=main_keyboard(language),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("section:"))
async def section_handler(callback: CallbackQuery) -> None:
    if callback.from_user is None or callback.data is None:
        return
    section = callback.data.split(":", 1)[1]
    from app.database import get_pool

    language = await get_pool().fetchval(
        "SELECT language FROM users WHERE telegram_id = $1",
        callback.from_user.id,
    ) or "uz"
    key = "media_help" if section == "media" else "music_help"
    await callback.message.answer(get_text(language, key))
    await callback.answer()


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    if message.from_user is None:
        return
    if message.from_user.id != get_settings().admin_id:
        await message.answer(get_text("uz", "admin_only"))
        return
    from app.database import get_pool

    user_count = await get_pool().fetchval("SELECT COUNT(*) FROM users")
    await message.answer(f"Universal Media\nFoydalanuvchilar: {user_count}")
