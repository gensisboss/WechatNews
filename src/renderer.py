from __future__ import annotations

import datetime as dt
import html

from .fetchers import NewsItem


def render_html(items: list[NewsItem], title: str, intro: str) -> str:
    today = dt.datetime.now().strftime("%Y-%m-%d")
    chunks = [
        '<section style="font-size:16px;line-height:1.75;color:#222;">',
        f"<h1>{html.escape(title)}</h1>",
        f'<p style="color:#57606a;">{html.escape(intro)}</p>',
        f'<p style="color:#8c8c8c;font-size:13px;">{today}</p>',
    ]

    if not items:
        chunks.append("<p>No matching news items were found for this run.</p>")
    else:
        for index, item in enumerate(items, start=1):
            chunks.append(_render_html_item(index, item))

    chunks.append(
        '<p style="color:#8c8c8c;font-size:13px;">'
        "Sources are linked for reading the original posts. This digest only summarizes public metadata."
        "</p>"
    )
    chunks.append("</section>")
    return "\n".join(chunks)


def render_markdown(items: list[NewsItem], title: str, intro: str) -> str:
    lines = [f"# {title}", "", intro, ""]

    if not items:
        lines.append("No matching news items were found for this run.")
        return "\n".join(lines) + "\n"

    for index, item in enumerate(items, start=1):
        published = _format_date(item.published_at)
        lines.extend(
            [
                f"## {index}. {item.title}",
                "",
                f"- Source: {item.source}",
                f"- Published: {published}",
                f"- Link: {item.url}",
            ]
        )
        if item.summary:
            lines.append(f"- Summary: {_shorten(item.summary, 220)}")
        lines.append("")

    return "\n".join(lines)


def _render_html_item(index: int, item: NewsItem) -> str:
    summary = _shorten(item.summary, 220) if item.summary else "No summary provided by the source feed."
    return "\n".join(
        [
            '<section style="margin:20px 0;padding:14px 0;border-top:1px solid #eaecef;">',
            f"<h2>{index}. {html.escape(item.title)}</h2>",
            (
                '<p style="color:#57606a;font-size:14px;">'
                f"{html.escape(item.source)} · {html.escape(_format_date(item.published_at))}"
                "</p>"
            ),
            f"<p>{html.escape(summary)}</p>",
            f'<p><a href="{html.escape(item.url, quote=True)}">Read original source</a></p>',
            "</section>",
        ]
    )


def _format_date(value: dt.datetime | None) -> str:
    if value is None:
        return "Unknown"
    return value.astimezone(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")


def _shorten(value: str, limit: int) -> str:
    normalized = " ".join(value.split())
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 1].rstrip() + "..."
