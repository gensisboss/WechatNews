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

    def test_select_top_items_can_require_same_beijing_calendar_day(self):
        now = dt.datetime(2026, 7, 4, 2, 0, tzinfo=dt.timezone.utc)  # 2026-07-04 10:00 Asia/Shanghai
        today_item = NewsItem(
            title="AI game update today",
            url="https://example.com/today",
            source="AI Wire",
            published_at=dt.datetime(2026, 7, 3, 16, 1, tzinfo=dt.timezone.utc),
            summary="AI game production news.",
        )
        yesterday_item = NewsItem(
            title="AI game update yesterday",
            url="https://example.com/yesterday",
            source="AI Wire",
            published_at=dt.datetime(2026, 7, 3, 15, 59, tzinfo=dt.timezone.utc),
            summary="AI game production news.",
        )
        undated_item = NewsItem(
            title="AI game update without date",
            url="https://example.com/undated",
            source="AI Wire",
            published_at=None,
            summary="AI game production news.",
        )

        selected = select_top_items(
            [today_item, yesterday_item, undated_item],
            keywords=["AI", "game"],
            exclude_keywords=[],
            max_items=5,
            lookback_hours=36,
            now=now,
            published_today_only=True,
            timezone=dt.timezone(dt.timedelta(hours=8)),
        )

        self.assertEqual(selected, [today_item])

    def test_select_top_items_fills_minimum_with_today_tech_fallback(self):
        now = dt.datetime(2026, 7, 6, 2, 0, tzinfo=dt.timezone.utc)  # 2026-07-06 10:00 Asia/Shanghai
        primary_ai = NewsItem(
            title="AI model changes game production",
            url="https://example.com/ai-game",
            source="AI Wire",
            published_at=dt.datetime(2026, 7, 6, 0, 30, tzinfo=dt.timezone.utc),
            summary="AI game workflows.",
            category="ai",
        )
        primary_game = NewsItem(
            title="Unity game tooling update",
            url="https://example.com/unity-game",
            source="Game Wire",
            published_at=dt.datetime(2026, 7, 5, 18, 0, tzinfo=dt.timezone.utc),
            summary="Game production news.",
            category="game",
        )
        tech_items = [
            NewsItem(
                title="Apple device launch adds new technology platform",
                url="https://example.com/apple-device",
                source="Tech Wire",
                published_at=dt.datetime(2026, 7, 6, 1, 0, tzinfo=dt.timezone.utc),
                summary="Consumer technology update.",
                category="tech",
            ),
            NewsItem(
                title="Cloud software startup raises new funding",
                url="https://example.com/cloud-startup",
                source="Tech Wire",
                published_at=dt.datetime(2026, 7, 5, 20, 0, tzinfo=dt.timezone.utc),
                summary="Software and cloud infrastructure.",
                category="tech",
            ),
            NewsItem(
                title="Chip company expands semiconductor production",
                url="https://example.com/chip-company",
                source="Tech Wire",
                published_at=dt.datetime(2026, 7, 5, 16, 5, tzinfo=dt.timezone.utc),
                summary="Semiconductor technology.",
                category="tech",
            ),
            NewsItem(
                title="Yesterday technology platform update",
                url="https://example.com/yesterday-tech",
                source="Tech Wire",
                published_at=dt.datetime(2026, 7, 5, 15, 59, tzinfo=dt.timezone.utc),
                summary="Technology news.",
                category="tech",
            ),
        ]

        selected = select_top_items(
            [primary_ai, primary_game, *tech_items],
            keywords=["AI", "game", "Unity"],
            exclude_keywords=[],
            max_items=12,
            lookback_hours=36,
            now=now,
            published_today_only=True,
            timezone=dt.timezone(dt.timedelta(hours=8)),
            minimum_items=5,
            fallback_categories=["tech"],
            fallback_keywords=["technology", "software", "cloud", "chip", "semiconductor", "Apple", "startup"],
        )

        self.assertEqual(
            [item.title for item in selected],
            [
                "AI model changes game production",
                "Unity game tooling update",
                "Apple device launch adds new technology platform",
                "Cloud software startup raises new funding",
                "Chip company expands semiconductor production",
            ],
        )

    def test_select_top_items_deduplicates_same_event_from_different_sources(self):
        now = dt.datetime(2026, 7, 7, 2, 0, tzinfo=dt.timezone.utc)
        eurogamer_item = NewsItem(
            title='Compulsion Games and Double Fine confirm "Independence Day" from Xbox',
            url="https://www.gamesindustry.biz/compulsion-games-and-double-fine-confirm-independence-day-from-xbox",
            source="GamesIndustry.biz",
            published_at=now - dt.timedelta(minutes=30),
            summary=(
                "Compulsion Games and Double Fine 每 two formerly Xbox-owned developers now spun out "
                "from the Xbox family of studios as Microsoft enacts a deep round of cuts and divestitures "
                "每 have released statements about the changes. Read more"
            ),
            category="game",
        )
        verge_item = NewsItem(
            title="Former Xbox studios Double Fine and Compulsion will keep games after going indie",
            url="https://www.theverge.com/news/701629/double-fine-compulsion-xbox-independent",
            source="The Verge",
            published_at=now,
            summary=(
                "Microsoft is spinning off four of its Xbox game studios - Compulsion Games, "
                "Double Fine Productions, Ninja Theory, and Undead Labs - as part of the restructuring "
                "announced today. However, two that are going independent, Double Fine and Compulsion, "
                "will get to keep their franchises and games catalogs"
            ),
            category="tech",
        )

        selected = select_top_items(
            [eurogamer_item, verge_item],
            keywords=["game", "games", "gaming"],
            exclude_keywords=[],
            max_items=5,
            lookback_hours=24,
            now=now,
            minimum_items=5,
            fallback_categories=["tech"],
            fallback_keywords=["technology", "software"],
        )

        self.assertEqual(selected, [verge_item])


if __name__ == "__main__":
    unittest.main()
