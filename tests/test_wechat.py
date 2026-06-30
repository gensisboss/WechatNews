import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wechat import build_draft_payload


class WeChatTests(unittest.TestCase):
    def test_build_draft_payload_uses_draft_only_article_shape(self):
        payload = build_draft_payload(
            title="AI Game Daily",
            author="Automation",
            digest="Today's AI and game news.",
            html="<section>hello</section>",
            thumb_media_id="media123",
            source_url="https://example.com/daily",
        )

        self.assertEqual(len(payload["articles"]), 1)
        article = payload["articles"][0]
        self.assertEqual(article["title"], "AI Game Daily")
        self.assertEqual(article["thumb_media_id"], "media123")
        self.assertEqual(article["content"], "<section>hello</section>")
        self.assertEqual(article["need_open_comment"], 0)
        self.assertEqual(article["only_fans_can_comment"], 0)
        self.assertEqual(article["content_source_url"], "https://example.com/daily")


if __name__ == "__main__":
    unittest.main()
