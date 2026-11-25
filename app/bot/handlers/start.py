from aiogram import F, Router
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from io import BytesIO

from app.bot.keyboards.main import language_keyboard, main_keyboard
from app.bot.states import MusicSearch
from app.config import get_settings
from app.database import (
    admin_stats,
    allow_request,
    get_pool,
    get_user_language,
    is_user_blocked,
    latest_requests,
    latest_users,
    log_request,
    save_chat,
    save_user,
    set_user_blocked,
    set_user_language,
)
from app.i18n import get_text
from app.services.audio_recognition import recognize_audio
from app.services.media_links import identify_media_link
from app.services.music_search import search_tracks, search_tracks_by_lyrics

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
    await state.update_data(search_mode="title")
    await message.answer(
        get_text(language, "music_help") + "\n" + get_text(language, "lyrics_command_hint")
    )


@router.message(Command("lyrics"))
async def lyrics_command(message: Message, state: FSMContext) -> None:
    language = await register_activity(message)
    if message.from_user and await is_user_blocked(message.from_user.id):
        await message.answer(get_text(language, "blocked"))
        return
    if not get_settings().musixmatch_api_key:
        await state.clear()
        await message.answer(get_text(language, "lyrics_unavailable"))
        return
    await state.set_state(MusicSearch.waiting_for_query)
    await state.update_data(search_mode="lyrics")
    await message.answer(get_text(language, "lyrics_help"))


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
        await state.update_data(search_mode="title")
        response = (
            get_text(language, "music_help")
            + "\n"
            + get_text(language, "lyrics_command_hint")
        )
    elif section == "media":
        await state.clear()
        response = get_text(language, "media_help")
    else:
        response = get_text(language, "unknown")

    if callback.message:
        await callback.message.answer(response)
    await callback.answer()


@router.message(MusicSearch.waiting_for_query, F.text & ~F.text.startswith("/"))
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

    search_mode = (await state.get_data()).get("search_mode", "title")
    is_lyrics_search = search_mode == "lyrics"
    settings = get_settings()
    if is_lyrics_search and not settings.musixmatch_api_key:
        await message.answer(get_text(language, "lyrics_unavailable"))
        return

    request_type = "lyrics_search" if is_lyrics_search else "music_search"
    status_key = "lyrics_searching" if is_lyrics_search else "music_searching"
    await log_request(message.from_user.id, message.chat.id, request_type)
    status = await message.answer(get_text(language, status_key))
    try:
        if is_lyrics_search:
            tracks = await search_tracks_by_lyrics(query, settings.musixmatch_api_key)
        else:
            tracks = await search_tracks(query)
    except Exception as exc:
        await log_request(message.from_user.id, message.chat.id, request_type, "error", type(exc).__name__)
        error_key = "lyrics_error" if is_lyrics_search else "music_error"
        await status.edit_text(get_text(language, error_key))
        return

    if not tracks:
        empty_key = "lyrics_empty" if is_lyrics_search else "music_empty"
        await status.edit_text(get_text(language, empty_key))
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


@router.message(F.voice | F.audio | F.video | F.video_note)
async def audio_recognition_handler(message: Message) -> None:
    if message.from_user is None:
        return
    language = await register_activity(message)
    if await is_user_blocked(message.from_user.id):
        await message.answer(get_text(language, "blocked"))
        return
    if not await allow_request(message.from_user.id, cooldown_seconds=3):
        await message.answer(get_text(language, "rate_limit"))
        return

    media = message.voice or message.audio or message.video or message.video_note
    if media is None:
        return
    settings = get_settings()
    if not settings.audd_api_token:
        await message.answer(get_text(language, "audio_unavailable"))
        return
    if media.file_size and media.file_size > settings.max_media_file_mb * 1024 * 1024:
        await message.answer(
            f"Fayl hajmi {settings.max_media_file_mb} MB dan oshmasligi kerak."
        )
        return
    duration = getattr(media, "duration", 0) or 0
    if duration > 180:
        await message.answer("Audio yoki video 3 daqiqadan uzun bo‘lmasin.")
        return

    status = await message.answer(get_text(language, "audio_searching"))
    try:
        telegram_file = await message.bot.get_file(media.file_id)
        if not telegram_file.file_path:
            raise ValueError("Telegram file path is missing")
        buffer = BytesIO()
        await message.bot.download_file(telegram_file.file_path, destination=buffer)
        raw = buffer.getvalue()
        if len(raw) > settings.max_media_file_mb * 1024 * 1024:
            raise ValueError("Media file exceeds configured limit")
        filename = getattr(media, "file_name", None) or (
            "video.mp4" if message.video or message.video_note else "audio.bin"
        )
        result = await recognize_audio(
            raw,
            filename=filename,
            is_video=bool(message.video or message.video_note),
        )
    except Exception as exc:
        await log_request(
            message.from_user.id, message.chat.id, "audio_recognition",
            "error", type(exc).__name__,
        )
        await status.edit_text(get_text(language, "audio_error"))
        return

    await log_request(message.from_user.id, message.chat.id, "audio_recognition")
    if not result:
        await status.edit_text(get_text(language, "audio_not_found"))
        return

    album = result.get("album") or "—"
    buttons = []
    for link in result.get("links", []):
        buttons.append([
            InlineKeyboardButton(
                text="Apple Music / Spotify / YouTube",
                url=link,
            )
        ])
    await status.edit_text(
        get_text(
            language,
            "audio_result",
            title=result["title"],
            artist=result["artist"],
            album=album,
        ),
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons) if buttons else None,
        disable_web_page_preview=True,
    )


@router.message(F.text & ~F.text.startswith("/"))
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



@router.message(Command("users"))
async def users_handler(message: Message) -> None:
    if not _is_admin(message):
        await message.answer(get_text("uz", "admin_only"))
        return
    rows = await latest_users(15)
    if not rows:
        await message.answer("Foydalanuvchilar hali yo‘q.")
        return
    lines = ["Oxirgi foydalanuvchilar:"]
    for row in rows:
        name = row["first_name"] or "—"
        username = f" (@{row['username']})" if row["username"] else ""
        status = " [BLOCK]" if row["is_blocked"] else ""
        lines.append(f"{row['telegram_id']} — {name}{username} — {row['language']}{status}")
    await message.answer("\n".join(lines))


@router.message(Command("requests"))
async def requests_handler(message: Message) -> None:
    if not _is_admin(message):
        await message.answer(get_text("uz", "admin_only"))
        return
    rows = await latest_requests(15)
    if not rows:
        await message.answer("So‘rovlar hali yo‘q.")
        return
    lines = ["Oxirgi so‘rovlar:"]
    for row in rows:
        created = row["created_at"].strftime("%d.%m %H:%M")
        detail = f" — {row['detail']}" if row["detail"] else ""
        lines.append(
            f"{created} | {row['request_type']} | {row['status']} | "
            f"user={row['telegram_id']}{detail}"
        )
    await message.answer("\n".join(lines))
