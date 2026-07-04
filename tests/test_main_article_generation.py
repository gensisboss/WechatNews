import datetime as dt
import sys
import tempfile
import textwrap
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.article_writer import GeneratedArticle
from src.fetchers import NewsItem
from src.main import main


class MainArticleGenerationTests(unittest.TestCase):
    def test_main_renders_generated_articles_when_enabled(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            root = Path(temp_dir)
            config = root / "config.yml"
            sources = root / "sources.yml"
            output = root / "output"
            config.write_text(
                textwrap.dedent(
                    """
                    title_template: "AI/游戏行业观察 {date}"
                    intro: "今日观察"
                    max_items: 1
                    lookback_hours: 24
                    published_today_only: true
                    timezone: "Asia/Shanghai"
                    timeout_seconds: 5
                    keywords:
                      - AI
                    exclude_keywords:
                    article_generation:
                      enabled: true
                      api_key: "config-key"
                      model: "deepseek-chat"
                      max_articles: 1
                    wechat:
                      create_draft: false
                    """
                ).strip(),
                encoding="utf-8",
            )
            sources.write_text(
                textwrap.dedent(
                    """
                    sources:
                      - name: Example
                        url: https://example.com/feed.xml
                        category: ai
                        enabled: true
                    """
                ).strip(),
                encoding="utf-8",
            )
            item = NewsItem(
                title="AI changes game production",
                url="https://example.com/story",
                source="Example",
                published_at=None,
                summary="AI changes workflows.",
            )

            with (
                patch("src.main.fetch_all_sources", return_value=[item]),
                patch("src.main.select_top_items", return_value=[item]) as select_top_items,
                patch("src.main.DeepSeekArticleClient") as client_class,
                patch(
                    "src.main.generate_articles",
                    return_value=[
                        GeneratedArticle(
                            title=item.title,
                            body="这是一篇约五百字中文文章的测试正文。",
                            url=item.url,
                            image_url="https://cdn.example.com/story.jpg",
                        )
                    ],
                ),
            ):
                exit_code = main(
                    [
                        "--config",
                        str(config),
                        "--sources",
                        str(sources),
                        "--output",
                        str(output),
                    ]
                )

            self.assertEqual(exit_code, 0)
            self.assertTrue(select_top_items.call_args.kwargs["published_today_only"])
            self.assertEqual(select_top_items.call_args.kwargs["timezone"], dt.timezone(dt.timedelta(hours=8)))
            client_class.assert_called_once()
            self.assertEqual(client_class.call_args.kwargs["api_key"], "config-key")
            markdown = next(output.glob("*.md")).read_text(encoding="utf-8")
            self.assertIn("这是一篇约五百字中文文章的测试正文。", markdown)
            self.assertIn("![AI changes game production](https://cdn.example.com/story.jpg)", markdown)
            self.assertNotIn("原文链接", markdown)
            self.assertNotIn("点击阅读原文", markdown)
            self.assertNotIn("这条消息来自", markdown)


if __name__ == "__main__":
    unittest.main()
