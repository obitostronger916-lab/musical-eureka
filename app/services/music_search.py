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
