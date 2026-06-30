import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fetchers import NewsItem
from src.renderer import render_html, render_markdown


class RendererTests(unittest.TestCase):
    def test_render_html_escapes_content_and_links_sources(self):
        item = NewsItem(
            title="AI <Game> update",
            url="https://example.com/news",
            source="Source & Co",
            published_at=dt.datetime(2026, 6, 30, 9, 0, tzinfo=dt.timezone.utc),
            summary="A <short> summary & context.",
        )

        html = render_html([item], title="Daily <Digest>", intro="AI & games")

        self.assertIn("Daily &lt;Digest&gt;", html)
        self.assertIn("AI &lt;Game&gt; update", html)
        self.assertIn("Source &amp; Co", html)
        self.assertIn('href="https://example.com/news"', html)
        self.assertNotIn("<short>", html)

    def test_render_markdown_includes_empty_state(self):
        markdown = render_markdown([], title="Daily Digest", intro="No copied articles.")

        self.assertIn("# Daily Digest", markdown)
        self.assertIn("No matching news items", markdown)


if __name__ == "__main__":
    unittest.main()
