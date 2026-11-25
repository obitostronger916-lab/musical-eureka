import asyncio
import io
from urllib.parse import urlsplit

import httpx

from app.config import get_settings

AUDD_URL = "https://api.audd.io/"
ALLOWED_RESULT_HOSTS = {
    "music.apple.com",
    "open.spotify.com",
    "youtube.com",
    "www.youtube.com",
    "youtu.be",
    "deezer.com",
    "www.deezer.com",
}


def _safe_result_url(value: str | None) -> str | None:
    if not value:
        return None
    try:
        parsed = urlsplit(value)
        if parsed.scheme == "https" and parsed.hostname in ALLOWED_RESULT_HOSTS:
            return value
    except ValueError:
        pass
    return None


async def _extract_video_audio(data: bytes) -> bytes:
    process = await asyncio.create_subprocess_exec(
        "ffmpeg",
        "-hide_banner",
        "-loglevel", "error",
        "-i", "pipe:0",
        "-t", "30",
        "-vn",
        "-ac", "1",
        "-ar", "16000",
        "-f", "mp3",
        "pipe:1",
        stdin=asyncio.subprocess.PIPE,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
    )
    try:
        stdout, _ = await asyncio.wait_for(
            process.communicate(data),
            timeout=20,
        )
    except asyncio.TimeoutError:
        process.kill()
        await process.communicate()
        raise ValueError("Audio extraction timed out")
    if process.returncode != 0 or not stdout:
        raise ValueError("Could not extract audio from media")
    return stdout


async def recognize_audio(data: bytes, filename: str, is_video: bool = False) -> dict | None:
    settings = get_settings()
    if not settings.audd_api_token:
        raise RuntimeError("AUDD_API_TOKEN is not configured")
    if not data or len(data) > settings.max_media_file_mb * 1024 * 1024:
        raise ValueError("Media file is empty or too large")
    if is_video:
        data = await _extract_video_audio(data)
        filename = "extracted-audio.mp3"

    timeout = httpx.Timeout(25.0, connect=5.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        response = await client.post(
            AUDD_URL,
            data={"api_token": settings.audd_api_token, "return": "apple_music,spotify"},
            files={"file": (filename, io.BytesIO(data), "application/octet-stream")},
        )
        response.raise_for_status()
        payload = response.json()

    if payload.get("status") != "success":
        raise RuntimeError("Audio recognition provider returned an error")
    result = payload.get("result")
    if not isinstance(result, dict):
        return None

    title = str(result.get("title") or "").strip()
    artist = str(result.get("artist") or "").strip()
    if not title or not artist:
        return None
    links = []
    for field in ("song_link",):
        link = _safe_result_url(result.get(field))
        if link:
            links.append(link)
    return {
        "title": title[:160],
        "artist": artist[:120],
        "album": str(result.get("album") or "")[:160],
        "links": links,
    }
