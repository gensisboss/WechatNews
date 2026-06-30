import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.fetchers import NewsItem
from src.ranker import select_top_items


class RankerTests(unittest.TestCase):
    def test_select_top_items_filters_scores_and_deduplicates(self):
        now = dt.datetime(2026, 6, 30, 9, 0, tzinfo=dt.timezone.utc)
        items = [
            NewsItem(
                title="OpenAI releases new game AI agent",
                url="https://example.com/story?utm_source=feed",
                source="AI Wire",
                published_at=now,
                summary="OpenAI and Unity game workflows.",
            ),
            NewsItem(
                title="OpenAI releases new game AI agent",
                url="https://example.com/story",
                source="Mirror",
                published_at=now - dt.timedelta(hours=1),
                summary="Duplicate story.",
            ),
            NewsItem(
                title="Cooking tools update",
                url="https://example.com/cooking",
                source="Other",
                published_at=now,
                summary="No matching terms.",
            ),
            NewsItem(
                title="Tencent game studio launches AI NPC tooling",
                url="https://example.com/tencent-ai-npc",
                source="Game Biz",
                published_at=now - dt.timedelta(minutes=30),
                summary="Game production news.",
            ),
        ]

        selected = select_top_items(
            items,
            keywords=["AI", "OpenAI", "game", "Unity", "Tencent"],
            exclude_keywords=["cooking"],
            max_items=5,
            lookback_hours=24,
            now=now,
        )

        self.assertEqual([item.title for item in selected], [
            "OpenAI releases new game AI agent",
            "Tencent game studio launches AI NPC tooling",
        ])

    def test_select_top_items_ignores_stale_items(self):
        now = dt.datetime(2026, 6, 30, 9, 0, tzinfo=dt.timezone.utc)
        old_item = NewsItem(
            title="AI game update",
            url="https://example.com/old",
            source="Archive",
            published_at=now - dt.timedelta(days=3),
            summary="Old but relevant.",
        )

        selected = select_top_items(
            [old_item],
            keywords=["AI", "game"],
            exclude_keywords=[],
            max_items=5,
            lookback_hours=24,
            now=now,
        )

        self.assertEqual(selected, [])


if __name__ == "__main__":
    unittest.main()
