import unittest

from app.services.audio_recognition import _safe_result_url


class AudioRecognitionSafetyTests(unittest.TestCase):
    def test_accepts_known_https_music_links(self):
        self.assertEqual(
            _safe_result_url("https://music.apple.com/us/song/example/123"),
            "https://music.apple.com/us/song/example/123",
        )

    def test_rejects_untrusted_links(self):
        self.assertIsNone(_safe_result_url("http://music.apple.com/song"))
        self.assertIsNone(_safe_result_url("https://evil.example/song"))
        self.assertIsNone(_safe_result_url("https://music.apple.com.evil.example/"))


if __name__ == "__main__":
    unittest.main()
