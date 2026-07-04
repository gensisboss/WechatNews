from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from .fetchers import NewsItem


TRACKING_PREFIXES = ("utm_",)
TRACKING_PARAMS = {"spm", "fbclid", "gclid", "yclid"}


@dataclass(frozen=True)
class ScoredItem:
    item: NewsItem
    score: int


def select_top_items(
    items: list[NewsItem],
    keywords: list[str],
    exclude_keywords: list[str],
    max_items: int,
    lookback_hours: int,
    now: dt.datetime | None = None,
    published_today_only: bool = False,
    timezone: dt.tzinfo = dt.timezone.utc,
) -> list[NewsItem]:
    now = now or dt.datetime.now(dt.timezone.utc)
    cutoff = now - dt.timedelta(hours=lookback_hours)
    local_today = now.astimezone(timezone).date()
    seen: set[str] = set()
    scored: list[ScoredItem] = []

    for item in items:
        if item.published_at is not None and item.published_at < cutoff:
            continue
        if published_today_only and not _is_published_on_date(item, local_today, timezone):
            continue

        haystack = f"{item.title} {item.summary} {item.source}".casefold()
        if _contains_any(haystack, exclude_keywords):
            continue

        score = score_item(item, keywords)
        if score <= 0:
            continue

        fingerprint = _fingerprint(item)
        if fingerprint in seen:
            continue
        seen.add(fingerprint)
        scored.append(ScoredItem(item=item, score=score))

    scored.sort(
        key=lambda entry: (
            entry.score,
            entry.item.published_at or dt.datetime.min.replace(tzinfo=dt.timezone.utc),
        ),
        reverse=True,
    )
    return [entry.item for entry in scored[:max_items]]


def _is_published_on_date(item: NewsItem, local_date: dt.date, timezone: dt.tzinfo) -> bool:
    if item.published_at is None:
        return False
    return item.published_at.astimezone(timezone).date() == local_date


def score_item(item: NewsItem, keywords: list[str]) -> int:
    title = item.title.casefold()
    summary = item.summary.casefold()
    score = 0

    for keyword in keywords:
        needle = keyword.casefold()
        if not needle:
            continue
        if needle in title:
            score += 3
        if needle in summary:
            score += 1

    return score


def normalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query, keep_blank_values=True)
        if not key.casefold().startswith(TRACKING_PREFIXES)
        and key.casefold() not in TRACKING_PARAMS
    ]
    normalized_query = urlencode(query, doseq=True)
    return urlunsplit(
        (
            parts.scheme.casefold(),
            parts.netloc.casefold(),
            parts.path.rstrip("/"),
            normalized_query,
            "",
        )
    )


def _fingerprint(item: NewsItem) -> str:
    normalized_title = re.sub(r"\W+", "", item.title.casefold())
    return normalize_url(item.url) or normalized_title


def _contains_any(haystack: str, needles: list[str]) -> bool:
    return any(needle.casefold() in haystack for needle in needles if needle)
