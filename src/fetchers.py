from __future__ import annotations

import datetime as dt
import email.utils
import html
import json
import logging
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Iterable


LOGGER = logging.getLogger(__name__)
USER_AGENT = "wechat-news-publisher/1.0 (+https://github.com/)"


@dataclass(frozen=True)
class Source:
    name: str
    url: str
    category: str = "general"
    enabled: bool = True


@dataclass(frozen=True)
class NewsItem:
    title: str
    url: str
    source: str
    published_at: dt.datetime | None
    summary: str = ""
    category: str = "general"


def fetch_all_sources(sources: Iterable[Source], timeout_seconds: int = 20) -> list[NewsItem]:
    items: list[NewsItem] = []
    for source in sources:
        if not source.enabled:
            continue

        try:
            items.extend(fetch_feed(source, timeout_seconds=timeout_seconds))
        except Exception as exc:  # noqa: BLE001 - keep one bad feed from breaking the digest.
            LOGGER.warning("Skipping source %s after fetch/parse failure: %s", source.name, exc)

    return items


def fetch_feed(source: Source, timeout_seconds: int = 20) -> list[NewsItem]:
    if source.url.startswith("gdelt://search"):
        request_url = _gdelt_request_url(source.url)
    else:
        request_url = source.url

    request = urllib.request.Request(request_url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        data = response.read()
    if source.url.startswith("gdelt://search"):
        return parse_gdelt_articles(data, source)
    return parse_feed(data, source)


def parse_gdelt_articles(data: bytes, source: Source) -> list[NewsItem]:
    payload = json.loads(data.decode("utf-8", errors="replace"))
    items: list[NewsItem] = []
    for article in payload.get("articles", []):
        title = str(article.get("title", "")).strip()
        url = str(article.get("url", "")).strip()
        if not title or not url:
            continue

        domain = str(article.get("domain", "")).strip()
        image = str(article.get("socialimage", "")).strip()
        summary_parts = [part for part in [domain, image] if part]
        items.append(
            NewsItem(
                title=_clean_space(title),
                url=url,
                source=source.name,
                published_at=parse_gdelt_datetime(str(article.get("seendate", ""))),
                summary=" ".join(summary_parts),
                category=source.category,
            )
        )
    return items


def parse_feed(data: bytes, source: Source) -> list[NewsItem]:
    root = ET.fromstring(data)
    if root.tag.lower().endswith("rss") or root.find("channel") is not None:
        return _parse_rss(root, source)
    return _parse_atom(root, source)


def _parse_rss(root: ET.Element, source: Source) -> list[NewsItem]:
    items: list[NewsItem] = []
    channel = root.find("channel")
    if channel is None:
        return items

    for node in channel.findall("item"):
        title = _text(node, "title")
        link = _text(node, "link")
        if not title or not link:
            continue

        items.append(
            NewsItem(
                title=_clean_space(title),
                url=link.strip(),
                source=source.name,
                published_at=parse_datetime(_text(node, "pubDate") or _text(node, "date")),
                summary=_clean_summary(_text(node, "description") or _text(node, "summary")),
                category=source.category,
            )
        )
    return items


def _parse_atom(root: ET.Element, source: Source) -> list[NewsItem]:
    ns = _namespace(root.tag)
    entry_name = f"{{{ns}}}entry" if ns else "entry"
    items: list[NewsItem] = []

    for node in root.findall(entry_name):
        title = _text(node, "title", ns)
        link = _atom_link(node, ns)
        if not title or not link:
            continue

        items.append(
            NewsItem(
                title=_clean_space(title),
                url=link.strip(),
                source=source.name,
                published_at=parse_datetime(
                    _text(node, "published", ns) or _text(node, "updated", ns)
                ),
                summary=_clean_summary(_text(node, "summary", ns) or _text(node, "content", ns)),
                category=source.category,
            )
        )
    return items


def parse_datetime(value: str | None) -> dt.datetime | None:
    if not value:
        return None

    try:
        parsed = email.utils.parsedate_to_datetime(value)
    except ValueError:
        parsed = None
    if parsed is not None:
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=dt.timezone.utc)
        return parsed.astimezone(dt.timezone.utc)

    try:
        normalized = value.strip().replace("Z", "+00:00")
        parsed = dt.datetime.fromisoformat(normalized)
    except ValueError:
        return None

    if parsed.tzinfo is None:
        return parsed.replace(tzinfo=dt.timezone.utc)
    return parsed.astimezone(dt.timezone.utc)


def parse_gdelt_datetime(value: str) -> dt.datetime | None:
    if not value:
        return None
    for fmt in ("%Y%m%dT%H%M%SZ", "%Y%m%d%H%M%S"):
        try:
            return dt.datetime.strptime(value, fmt).replace(tzinfo=dt.timezone.utc)
        except ValueError:
            continue
    return parse_datetime(value)


def _gdelt_request_url(value: str) -> str:
    parsed = urllib.parse.urlsplit(value)
    params = dict(urllib.parse.parse_qsl(parsed.query, keep_blank_values=True))
    query = params.get("query", "").strip()
    max_records = params.get("max_records", "50").strip() or "50"
    gdelt_params = {
        "query": query,
        "mode": "ArtList",
        "format": "json",
        "sort": "DateDesc",
        "maxrecords": max_records,
    }
    timespan = params.get("timespan", "1d").strip()
    if timespan:
        gdelt_params["timespan"] = timespan
    return "https://api.gdeltproject.org/api/v2/doc/doc?" + urllib.parse.urlencode(gdelt_params)


def _text(node: ET.Element, name: str, namespace: str | None = None) -> str:
    child_name = f"{{{namespace}}}{name}" if namespace else name
    child = node.find(child_name)
    if child is None or child.text is None:
        return ""
    return child.text


def _atom_link(node: ET.Element, namespace: str | None) -> str:
    link_name = f"{{{namespace}}}link" if namespace else "link"
    for link in node.findall(link_name):
        href = link.attrib.get("href", "")
        rel = link.attrib.get("rel", "alternate")
        if href and rel == "alternate":
            return href
    first = node.find(link_name)
    return "" if first is None else first.attrib.get("href", "")


def _namespace(tag: str) -> str | None:
    if tag.startswith("{") and "}" in tag:
        return tag[1:].split("}", 1)[0]
    return None


def _clean_space(value: str) -> str:
    return " ".join(value.split())


def _clean_summary(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value)
    return _clean_space(html.unescape(without_tags))
