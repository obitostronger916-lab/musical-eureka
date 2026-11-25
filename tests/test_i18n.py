import unittest

from app.i18n import TEXTS, get_text


class TranslationTests(unittest.TestCase):
    def test_all_supported_languages_have_required_messages(self):
        required = (
            "welcome",
            "choose",
            "media",
            "music",
            "language",
            "media_help",
            "music_help",
            "lyrics_help",
            "lyrics_unavailable",
            "lyrics_searching",
            "lyrics_empty",
            "lyrics_error",
            "lyrics_command_hint",
            "audio_searching",
            "audio_unavailable",
            "audio_file_too_large",
            "audio_too_long",
            "audio_open_track",
            "audio_error",
            "audio_not_found",
            "rate_limit",
            "blocked",
            "admin_only",
            "help",
        )
        for language in ("uz", "ru", "en"):
            for key in required:
                with self.subTest(language=language, key=key):
                    self.assertTrue(TEXTS[language].get(key))

    def test_unknown_language_falls_back_to_uzbek(self):
        self.assertEqual(
            get_text("xx", "welcome"),
            get_text("uz", "welcome"),
        )

    def test_unknown_key_falls_back_to_key(self):
        self.assertEqual(get_text("uz", "missing_key"), "missing_key")

    def test_message_templates_are_formatted(self):
        value = get_text(
            "uz",
            "media_found",
            platform="YouTube",
            url="https://youtu.be/example",
        )
        self.assertIn("YouTube", value)
        self.assertIn("https://youtu.be/example", value)


if __name__ == "__main__":
    unittest.main()
