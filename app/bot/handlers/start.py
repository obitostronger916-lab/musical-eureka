from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

from app.bot.keyboards.main import language_keyboard, main_keyboard
from app.bot.states import MusicSearch
from app.config import get_settings
from app.database import (
    admin_stats,
    allow_request,
    get_pool,
    get_user_language,
    is_user_blocked,
    log_request,
    save_chat,
    save_user,
    set_user_blocked,
    set_user_language,
)
from app.i18n import get_text
from app.services.media_links import identify_media_link
from app.services.music_search import search_tracks

router = Router()


async def register_activity(message: Message) -> str:
    user = message.from_user
    if user is None:
        return "uz"
    language = await save_user(
        telegram_id=user.id,
        username=user.username,
        first_name=user.first_name or "",
    )
    chat = message.chat
    await save_chat(
        chat_id=chat.id,
        chat_type=chat.type,
        title=chat.title,
        username=chat.username,
    )
    return language


@router.message(CommandStart())
async def start_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    language = await register_activity(message)
    if message.from_user is None:
        return
    if await is_user_blocked(message.from_user.id):
        await message.answer(get_text(language, "blocked"))
        return
    await message.answer(
        f"{get_text(language, 'welcome')}\n\n{get_text(language, 'choose')}",
        reply_markup=main_keyboard(language),
    )


@router.message(Command("help"))
async def help_handler(message: Message) -> None:
    language = await register_activity(message)
    await message.answer(get_text(language, "help"))


@router.message(Command("language"))
async def language_command(message: Message) -> None:
    language = await register_activity(message)
    await message.answer(
        "Tilni tanlang / Выберите язык / Choose a language:",
        reply_markup=language_keyboard(),
    )


@router.message(Command("music"))
async def music_command(message: Message, state: FSMContext) -> None:
    language = await register_activity(message)
    if message.from_user and await is_user_blocked(message.from_user.id):
        await message.answer(get_text(language, "blocked"))
        return
    await state.set_state(MusicSearch.waiting_for_query)
    await message.answer(get_text(language, "music_help"))


@router.message(Command("cancel"))
async def cancel_handler(message: Message, state: FSMContext) -> None:
    await state.clear()
    language = await register_activity(message)
    await message.answer(get_text(language, "choose"), reply_markup=main_keyboard(language))


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
    await save_user(
        callback.from_user.id,
        callback.from_user.username,
        callback.from_user.first_name or "",
    )
    if await is_user_blocked(callback.from_user.id):
        await callback.answer("Access restricted", show_alert=True)
        return
    section = callback.data.split(":", 1)[1]
    language = await get_user_language(callback.from_user.id)

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
    language = await register_activity(message)
    if await is_user_blocked(message.from_user.id):
        await message.answer(get_text(language, "blocked"))
        return
    if not await allow_request(message.from_user.id, cooldown_seconds=2):
        await message.answer(get_text(language, "rate_limit"))
        return
    query = message.text.strip()
    if not query:
        return
    if len(query) > 100:
        await message.answer(get_text(language, "music_too_long"))
        return

    await log_request(message.from_user.id, message.chat.id, "music_search")
    status = await message.answer(get_text(language, "music_searching"))
    try:
        tracks = await search_tracks(query)
    except Exception as exc:
        await log_request(message.from_user.id, message.chat.id, "music_search", "error", type(exc).__name__)
        await status.edit_text(get_text(language, "music_error"))
        return

    if not tracks:
        await status.edit_text(get_text(language, "music_empty"))
        return

    lines = []
    buttons = []
    for index, track in enumerate(tracks, start=1):
        album = f"\n   {track['album']}" if track.get("album") else ""
        lines.append(f"{index}. {track['title']} — {track['artist']}{album}")
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


@router.message(F.text)
async def media_link_handler(message: Message, state: FSMContext) -> None:
    if message.from_user is None or message.text is None:
        return
    language = await register_activity(message)
    if await is_user_blocked(message.from_user.id):
        await message.answer(get_text(language, "blocked"))
        return
    link = identify_media_link(message.text)
    if link is None:
        return
    if not await allow_request(message.from_user.id, cooldown_seconds=2):
        await message.answer(get_text(language, "rate_limit"))
        return
    await log_request(message.from_user.id, message.chat.id, "media_link", detail=link.platform)
    await message.answer(
        get_text(language, "media_found", platform=link.platform, url=link.url),
        disable_web_page_preview=False,
    )


def _is_admin(message: Message) -> bool:
    return bool(message.from_user and message.from_user.id == get_settings().admin_id)


@router.message(Command("admin"))
async def admin_handler(message: Message) -> None:
    if not _is_admin(message):
        await message.answer(get_text("uz", "admin_only"))
        return
    stats = await admin_stats()
    await message.answer(
        "Universal Media — Admin\n"
        f"Foydalanuvchilar: {stats['users']}\n"
        f"Guruhlar: {stats['groups']}\n"
        f"So‘rovlar: {stats['requests']}\n"
        f"Xatolar: {stats['errors']}\n\n"
        "/block ID — foydalanuvchini bloklash\n"
        "/unblock ID — blokdan chiqarish"
    )


@router.message(Command("block"))
async def block_handler(message: Message) -> None:
    if not _is_admin(message):
        await message.answer(get_text("uz", "admin_only"))
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /block TELEGRAM_ID")
        return
    changed = await set_user_blocked(int(parts[1]), True)
    await message.answer("Foydalanuvchi bloklandi." if changed else "Foydalanuvchi topilmadi.")


@router.message(Command("unblock"))
async def unblock_handler(message: Message) -> None:
    if not _is_admin(message):
        await message.answer(get_text("uz", "admin_only"))
        return
    parts = (message.text or "").split()
    if len(parts) != 2 or not parts[1].isdigit():
        await message.answer("Foydalanish: /unblock TELEGRAM_ID")
        return
    changed = await set_user_blocked(int(parts[1]), False)
    await message.answer("Blok olib tashlandi." if changed else "Foydalanuvchi topilmadi.")
