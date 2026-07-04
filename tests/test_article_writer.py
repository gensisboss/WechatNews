import unittest

from src.article_writer import (
    ArticleContent,
    GeneratedArticle,
    build_article_prompt,
    extract_article_content,
    extract_article_text,
    generate_articles,
)
from src.fetchers import NewsItem


class ArticleWriterTests(unittest.TestCase):
    def test_extract_article_text_keeps_article_content_and_drops_noise(self):
        html = b"""
        <html>
          <head>
            <script>window.analytics = true;</script>
            <style>body { color: red; }</style>
          </head>
          <body>
            <nav>Subscribe now</nav>
            <article>
              <h1>AI tools enter game production</h1>
              <p>Game studios are adopting AI tools for prototyping and training.</p>
              <p>The important shift is a move from one-off experiments to production workflows.</p>
            </article>
          </body>
        </html>
        """

        text = extract_article_text(html)

        self.assertIn("AI tools enter game production", text)
        self.assertIn("production workflows", text)
        self.assertNotIn("analytics", text)
        self.assertNotIn("Subscribe now", text)

    def test_extract_article_content_returns_first_article_image(self):
        html = b"""
        <html>
          <head>
            <meta property="og:image" content="https://cdn.example.com/og.jpg">
          </head>
          <body>
            <nav>
              <img src="https://cdn.example.com/logo.png">
            </nav>
            <article>
              <h1>AI tools enter game production</h1>
              <img src="/images/story.jpg" alt="Story image">
              <p>Game studios are adopting AI tools for prototyping and training.</p>
            </article>
          </body>
        </html>
        """

        content = extract_article_content(html, "https://example.com/news/story")

        self.assertIn("AI tools enter game production", content.text)
        self.assertEqual(content.image_url, "https://example.com/images/story.jpg")

    def test_build_article_prompt_requests_long_chinese_article_without_metadata(self):
        item = NewsItem(
            title="AI tools enter game production",
            url="https://example.com/story",
            source="Example",
            published_at=None,
            summary="Studios are adopting AI tools.",
        )

        prompt = build_article_prompt(item, article_text="Full article text")

        self.assertIn("约500字", prompt)
        self.assertIn("说明文或议论文", prompt)
        self.assertIn("不要写来源", prompt)
        self.assertIn("发布时间", prompt)
        self.assertIn("Full article text", prompt)

    def test_generate_articles_uses_client_output(self):
        item = NewsItem(
            title="AI tools enter game production",
            url="https://example.com/story",
            source="Example",
            published_at=None,
            summary="Studios are adopting AI tools.",
        )

        def fake_fetch(url: str, timeout_seconds: int) -> str:
            self.assertEqual(url, "https://example.com/story")
            self.assertEqual(timeout_seconds, 7)
            return "Full article text for the model."

        test_case = self

        class FakeClient:
            def write_article(self, item: NewsItem, article_text: str) -> str:
                test_case.assertEqual(article_text, "Full article text for the model.")
                return "这是一篇围绕 AI 工具进入游戏制作流程展开的中文说明文。"

        articles = generate_articles([item], client=FakeClient(), fetch_text=fake_fetch, timeout_seconds=7)

        self.assertEqual(
            articles,
            [
                GeneratedArticle(
                    title="AI tools enter game production",
                    body="这是一篇围绕 AI 工具进入游戏制作流程展开的中文说明文。",
                    url="https://example.com/story",
                    image_url=None,
                )
            ],
        )

    def test_generate_articles_keeps_image_from_fetched_article(self):
        item = NewsItem(
            title="AI tools enter game production",
            url="https://example.com/story",
            source="Example",
            published_at=None,
            summary="Studios are adopting AI tools.",
        )

        def fake_fetch(url: str, timeout_seconds: int):
            self.assertEqual(url, "https://example.com/story")
            self.assertEqual(timeout_seconds, 7)
            return ArticleContent(
                text="Full article text for the model.",
                image_url="https://cdn.example.com/story.jpg",
            )

        class FakeClient:
            def write_article(self, item: NewsItem, article_text: str) -> str:
                return "这是一篇围绕 AI 工具进入游戏制作流程展开的中文说明文。"

        articles = generate_articles([item], client=FakeClient(), fetch_text=fake_fetch, timeout_seconds=7)

        self.assertEqual(articles[0].image_url, "https://cdn.example.com/story.jpg")


if __name__ == "__main__":
    unittest.main()
