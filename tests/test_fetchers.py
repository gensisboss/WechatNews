import datetime as dt
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fetchers import Source, fetch_feed, parse_feed


class FetcherTests(unittest.TestCase):
    def test_parse_atom_feed_with_iso_datetime(self):
        xml = b"""<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
          <entry>
            <title>AI game tooling update</title>
            <link href="https://example.com/atom-story" rel="alternate" />
            <updated>2026-06-30T09:00:00Z</updated>
            <summary>Short summary</summary>
          </entry>
        </feed>
        """

        items = parse_feed(xml, Source(name="Atom Feed", url="https://example.com/feed"))

        self.assertEqual(len(items), 1)
        self.assertEqual(items[0].title, "AI game tooling update")
        self.assertEqual(items[0].published_at.isoformat(), "2026-06-30T09:00:00+00:00")

    def test_parse_rss_feed_strips_html_from_summary(self):
        xml = b"""<?xml version="1.0" encoding="utf-8"?>
        <rss version="2.0">
          <channel>
            <item>
              <title>AI game funding update</title>
              <link>https://example.com/rss-story</link>
              <pubDate>Tue, 30 Jun 2026 09:00:00 GMT</pubDate>
              <description><![CDATA[<p>Studio raises <strong>AI</strong> funding.</p>]]></description>
            </item>
          </channel>
        </rss>
        """

        items = parse_feed(xml, Source(name="RSS Feed", url="https://example.com/feed"))

        self.assertEqual(items[0].summary, "Studio raises AI funding.")

    def test_fetch_gdelt_search_source_parses_global_news_results(self):
        source = Source(
            name="Global AI Search",
            url="gdelt://search?query=artificial%20intelligence%20gaming&category=ai&max_records=2",
            category="ai",
            enabled=True,
        )
        payload = {
            "articles": [
                {
                    "title": "AI game studio launches new model",
                    "url": "https://example.com/story",
                    "domain": "example.com",
                    "seendate": "20260704T030000Z",
                    "socialimage": "https://example.com/story.jpg",
                }
            ]
        }

        class FakeResponse:
            def __enter__(self):
                return self

            def __exit__(self, exc_type, exc, traceback):
                return False

            def read(self):
                return json.dumps(payload).encode("utf-8")

        with patch("urllib.request.urlopen", return_value=FakeResponse()) as urlopen:
            items = fetch_feed(source, timeout_seconds=5)

        request = urlopen.call_args.args[0]
        self.assertIn("api.gdeltproject.org/api/v2/doc/doc", request.full_url)
        self.assertIn("mode=ArtList", request.full_url)
        self.assertEqual(items[0].title, "AI game studio launches new model")
        self.assertEqual(items[0].url, "https://example.com/story")
        self.assertEqual(items[0].source, "Global AI Search")
        self.assertEqual(items[0].published_at, dt.datetime(2026, 7, 4, 3, 0, tzinfo=dt.timezone.utc))
        self.assertIn("example.com", items[0].summary)


if __name__ == "__main__":
    unittest.main()
