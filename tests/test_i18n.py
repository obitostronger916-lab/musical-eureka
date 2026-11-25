import unittest

from app.i18n import get_text


class TranslationTests(unittest.TestCase):
    def test_all_supported_languages_have_welcome(self):
        for language in ("uz", "ru", "en"):
            with self.subTest(language=language):
                self.assertTrue(get_text(language, "welcome"))

    def test_unknown_language_falls_back_to_uzbek(self):
        self.assertEqual(
            get_text("xx", "welcome"),
            get_text("uz", "welcome"),
        )

    def test_unknown_key_falls_back_to_key(self):
        self.assertEqual(get_text("uz", "missing_key"), "missing_key")


if __name__ == "__main__":
    unittest.main()
