from dataclasses import dataclass
from urllib.parse import urlsplit, urlunsplit


@dataclass(frozen=True)
class MediaLink:
    platform: str
    url: str


HOSTS = {
    "instagram.com": "Instagram",
    "www.instagram.com": "Instagram",
    "m.instagram.com": "Instagram",
    "youtube.com": "YouTube",
    "www.youtube.com": "YouTube",
    "m.youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "tiktok.com": "TikTok",
    "www.tiktok.com": "TikTok",
    "vm.tiktok.com": "TikTok",
    "vt.tiktok.com": "TikTok",
    "pinterest.com": "Pinterest",
    "www.pinterest.com": "Pinterest",
    "pin.it": "Pinterest",
}


def identify_media_link(value: str) -> MediaLink | None:
    """Recognize supported public URLs without fetching or downloading them."""
    candidate = value.strip().strip("<>()[]{}.,!?")
    if not candidate or len(candidate) > 2048:
        return None
    if "://" not in candidate:
        candidate = "https://" + candidate
    try:
        parsed = urlsplit(candidate)
        host = (parsed.hostname or "").lower().rstrip(".")
        if parsed.scheme.lower() != "https":
            return None
        if parsed.username or parsed.password or parsed.port not in (None, 443):
            return None
        platform = HOSTS.get(host)
        if not platform or not parsed.path:
            return None
        safe_url = urlunsplit(("https", parsed.netloc, parsed.path, parsed.query, ""))
        return MediaLink(platform=platform, url=safe_url)
    except ValueError:
        return None
