import unittest

from app.services.music_search import _safe_store_url, search_tracks


class MusicSearchTests(unittest.IsolatedAsyncioTestCase):
    def test_accepts_only_official_https_store_urls(self):
        self.assertEqual(
            _safe_store_url("https://music.apple.com/us/album/example/123"),
            "https://music.apple.com/us/album/example/123",
        )
        self.assertEqual(
            _safe_store_url("https://itunes.apple.com/track?id=123"),
            "https://itunes.apple.com/track?id=123",
        )

    def test_rejects_untrusted_or_non_https_urls(self):
        self.assertIsNone(_safe_store_url("http://itunes.apple.com/track?id=1"))
        self.assertIsNone(_safe_store_url("https://example.com/track"))
        self.assertIsNone(_safe_store_url("https://itunes.apple.com.example.org/"))

    async def test_empty_or_oversized_query_does_not_call_network(self):
        self.assertEqual(await search_tracks("   "), [])
        self.assertEqual(await search_tracks("x" * 101), [])


if __name__ == "__main__":
    unittest.main()
