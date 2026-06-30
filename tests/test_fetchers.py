import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fetchers import Source, parse_feed


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


if __name__ == "__main__":
    unittest.main()
