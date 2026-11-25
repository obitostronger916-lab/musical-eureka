from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.keyboards.main import language_keyboard, main_keyboard
from app.bot.states import MusicSearch
from app.config import get_settings
from app.database import get_pool, save_user, set_user_language
from app.i18n import get_text
from app.services.music_search import search_tracks

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
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
    if callback.message:
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
    if callback.message:
        await callback.message.answer(
            f"{get_text(language, 'language_saved')}\n"
            f"{get_text(language, 'choose')}",
            reply_markup=main_keyboard(language),
        )
    await callback.answer()


@router.callback_query(F.data.startswith("section:"))
async def section_handler(callback: CallbackQuery, state: FSMContext) -> None:
    if callback.from_user is None or callback.data is None:
        return
    section = callback.data.split(":", 1)[1]
    language = await get_pool().fetchval(
        "SELECT language FROM users WHERE telegram_id = $1",
        callback.from_user.id,
    ) or "uz"

    if section == "music":
        await state.set_state(MusicSearch.waiting_for_query)
        response = get_text(language, "music_help")
    elif section == "media":
        await state.clear()
        response = get_text(language, "media_help")
    else:
        response = get_text(language, "unknown")

    if callback.message:
        await callback.message.answer(response)
    await callback.answer()


@router.message(MusicSearch.waiting_for_query, F.text)
async def music_query_handler(message: Message, state: FSMContext) -> None:
    if message.from_user is None or message.text is None:
        return
    language = await get_pool().fetchval(
        "SELECT language FROM users WHERE telegram_id = $1",
        message.from_user.id,
    ) or "uz"
    query = message.text.strip()
    if not query:
        return
    if len(query) > 100:
        await message.answer(get_text(language, "music_too_long"))
        return

    status = await message.answer(get_text(language, "music_searching"))
    try:
        tracks = await search_tracks(query)
    except Exception:
        await status.edit_text(get_text(language, "music_error"))
        return

    if not tracks:
        await status.edit_text(get_text(language, "music_empty"))
        return

    lines = []
    buttons = []
    for index, track in enumerate(tracks, start=1):
        lines.append(
            f"{index}. {track['title']} — {track['artist']}\n"
            f"   {track.get('album') or ''}".rstrip()
        )
        buttons.append([
            InlineKeyboardButton(
                text=f"{index}. Tinglash / Слушать / Listen",
                url=track["url"],
            )
        ])

    await status.edit_text(
        "\n\n".join(lines),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        disable_web_page_preview=True,
    )


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    if message.from_user is None:
        return
    if message.from_user.id != get_settings().admin_id:
        await message.answer(get_text("uz", "admin_only"))
        return

    user_count = await get_pool().fetchval("SELECT COUNT(*) FROM users")
    await message.answer(f"Universal Media\nFoydalanuvchilar: {user_count}")
