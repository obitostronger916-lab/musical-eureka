import unittest

from app.services.music_search import (\n    _normalize_lyrics_results, _safe_musixmatch_url, _safe_store_url,\n    search_tracks, search_tracks_by_lyrics,\n)


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

    def test_musixmatch_result_normalization_and_url_allowlist(self):
        self.assertIsNone(_safe_musixmatch_url("http://www.musixmatch.com/song"))
        self.assertIsNone(_safe_musixmatch_url("https://example.com/song"))
        payload = {"message": {"header": {"status_code": 200}, "body": {"track_list": [
            {"track": {"track_name": "Example", "artist_name": "Artist",
                       "album_name": "Album",
                       "track_share_url": "https://www.musixmatch.com/lyrics/example"}}
        ]}}}
        results = _normalize_lyrics_results(payload)
        self.assertEqual(results[0]["title"], "Example")
        self.assertEqual(results[0]["artist"], "Artist")
        self.assertNotIn("lyrics", results[0])

    async def test_lyrics_search_without_key_or_valid_query_does_not_call_network(self):
        self.assertEqual(await search_tracks_by_lyrics("some line", None), [])
        self.assertEqual(await search_tracks_by_lyrics("   ", "key"), [])
        self.assertEqual(await search_tracks_by_lyrics("x" * 101, "key"), [])

    async def test_empty_or_oversized_query_does_not_call_network(self):
        self.assertEqual(await search_tracks("   "), [])
        self.assertEqual(await search_tracks("x" * 101), [])


if __name__ == "__main__":
    unittest.main()
