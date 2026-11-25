import unittest

from app.services.media_links import identify_media_link


class MediaLinkTests(unittest.TestCase):
    def test_recognizes_supported_hosts(self):
        cases = {
            "https://www.instagram.com/p/example/": "Instagram",
            "https://youtu.be/example": "YouTube",
            "https://www.youtube.com/watch?v=example": "YouTube",
            "https://www.tiktok.com/@user/video/123": "TikTok",
            "https://pin.it/example": "Pinterest",
        }
        for url, platform in cases.items():
            with self.subTest(url=url):
                result = identify_media_link(url)
                self.assertIsNotNone(result)
                self.assertEqual(result.platform, platform)

    def test_rejects_unknown_or_unsafe_hosts(self):
        for url in (
            "https://youtube.com.evil.example/watch?v=x",
            "http://youtube.com/watch?v=x",
            "https://example.com/video",
            "https://user:pass@youtube.com/watch?v=x",
            "javascript:alert(1)",
        ):
            with self.subTest(url=url):
                self.assertIsNone(identify_media_link(url))

    def test_adds_https_to_supported_bare_domain(self):
        result = identify_media_link("youtu.be/abc")
        self.assertEqual(result.url, "https://youtu.be/abc")


if __name__ == "__main__":
    unittest.main()
