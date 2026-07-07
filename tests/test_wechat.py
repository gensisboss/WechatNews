import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.wechat import build_draft_payload, submit_freepublish


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

    def test_submit_freepublish_posts_draft_media_id(self):
        with patch("src.wechat._request_json", return_value={"publish_id": "publish123"}) as request_json:
            publish_id = submit_freepublish("token123", "draft-media-123")

        self.assertEqual(publish_id, "publish123")
        request_json.assert_called_once_with(
            "POST",
            "https://api.weixin.qq.com/cgi-bin/freepublish/submit?access_token=token123",
            {"media_id": "draft-media-123"},
        )


if __name__ == "__main__":
    unittest.main()
