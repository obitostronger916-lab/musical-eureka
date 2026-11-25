from urllib.parse import urlparse

import httpx

SEARCH_URL = "https://itunes.apple.com/search"
ALLOWED_HOSTS = {"itunes.apple.com", "music.apple.com"}


def _safe_store_url(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in ALLOWED_HOSTS:
        return None
    return value


async def search_tracks(query: str, limit: int = 5) -> list[dict[str, str]]:
    """Search Apple's catalog and return metadata plus official store links.

    No audio files or previews are downloaded or redistributed.
    """
    normalized = query.strip()
    if not normalized or len(normalized) > 100:
        return []

    params = {
        "term": normalized,
        "country": "US",
        "media": "music",
        "entity": "song",
        "limit": str(max(1, min(limit, 5))),
        "explicit": "No",
    }
    timeout = httpx.Timeout(8.0, connect=4.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        response = await client.get(SEARCH_URL, params=params)
        response.raise_for_status()
        payload = response.json()

    results = []
    for item in payload.get("results", []):
        title = str(item.get("trackName") or "").strip()
        artist = str(item.get("artistName") or "").strip()
        store_url = _safe_store_url(str(item.get("trackViewUrl") or ""))
        if not title or not artist or not store_url:
            continue
        results.append({
            "title": title[:160],
            "artist": artist[:120],
            "album": str(item.get("collectionName") or "")[:160],
            "url": store_url,
        })
    return results


def _safe_musixmatch_url(value: str) -> str | None:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in {"musixmatch.com", "www.musixmatch.com"}:
        return None
    return value


def _normalize_lyrics_results(payload: dict, limit: int = 5) -> list[dict[str, str]]:
    message = payload.get("message") or {}
    header = message.get("header") or {}
    if header.get("status_code") != 200:
        raise RuntimeError("Musixmatch returned an unsuccessful status")
    body = message.get("body") or {}
    results = []
    seen = set()
    for item in body.get("track_list", []):
        track = item.get("track") or {}
        title = str(track.get("track_name") or "").strip()
        artist = str(track.get("artist_name") or "").strip()
        url = _safe_musixmatch_url(str(track.get("track_share_url") or ""))
        if not title or not artist or not url:
            continue
        key = (title.casefold(), artist.casefold())
        if key in seen:
            continue
        seen.add(key)
        results.append({
            "title": title[:160],
            "artist": artist[:120],
            "album": str(track.get("album_name") or "")[:160],
            "url": url,
        })
        if len(results) >= max(1, min(limit, 5)):
            break
    return results


async def search_tracks_by_lyrics(query: str, api_key: str | None, limit: int = 5) -> list[dict[str, str]]:
    """Search by a user-provided lyric excerpt; never return lyric text."""
    normalized = query.strip()
    if not api_key or not normalized or len(normalized) > 100:
        return []
    params = {
        "apikey": api_key,
        "q_lyrics": normalized,
        "f_has_lyrics": "1",
        "page": "1",
        "page_size": str(max(1, min(limit, 5))),
        "format": "json",
    }
    timeout = httpx.Timeout(10.0, connect=4.0)
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=False) as client:
        response = await client.get("https://api.musixmatch.com/ws/1.1/track.search", params=params)
        response.raise_for_status()
        payload = response.json()
    return _normalize_lyrics_results(payload, limit=limit)
