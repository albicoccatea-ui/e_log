#!/usr/bin/env python3
import calendar
import datetime as dt
import hashlib
import html
import json
import re
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from xml.etree import ElementTree as ET

TIMEOUT = 20
MAX_ITEMS = 6
CALENDAR_LOOKAHEAD_MONTHS = 6
KST = dt.timezone(dt.timedelta(hours=9))
USER_AGENT = "MasaakiPulseWidget/1.0 (personal dashboard)"
CALENDAR_SOURCE_IDS = {"calendar_endoh", "calendar_jam"}
STOP_TOKENS = {
    "live",
    "news",
    "official",
    "update",
    "event",
    "the",
    "and",
    "for",
    "with",
    "you",
    "from",
    "project",
    "jam",
    "info",
    "media",
    "공지",
    "안내",
    "정보",
    "開催",
    "決定",
    "出演",
    "更新",
    "配信",
    "公演",
}


def now_kst():
    return dt.datetime.now(KST)


def add_months(base, months):
    total_month = (base.year * 12 + (base.month - 1)) + months
    year = total_month // 12
    month = (total_month % 12) + 1
    last_day = calendar.monthrange(year, month)[1]
    day = min(base.day, last_day)
    return base.replace(year=year, month=month, day=day)


def clean_text(value):
    if value is None:
        return ""
    no_tags = re.sub(r"<[^>]+>", " ", value)
    return re.sub(r"\s+", " ", html.unescape(no_tags)).strip()


def normalize_for_match(value):
    normalized = clean_text(value).lower()
    return re.sub(r"[^0-9a-z가-힣ぁ-んァ-ヶ一-龥]", "", normalized)


def extract_tokens(value):
    tokens = re.findall(r"[0-9a-z가-힣ぁ-んァ-ヶ一-龥]{2,}", clean_text(value).lower())
    return [token for token in tokens if token not in STOP_TOKENS and not token.isdigit()]


def fetch_text(url):
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=TIMEOUT) as response:
        raw = response.read()
        charset = response.headers.get_content_charset() or "utf-8"
    try:
        return raw.decode(charset, errors="replace")
    except LookupError:
        return raw.decode("utf-8", errors="replace")


def normalize_date(value):
    if not value:
        return ""
    value = value.strip()
    for fmt in ("%Y-%m-%dT%H:%M:%S%z", "%Y-%m-%dT%H:%M:%S"):
        try:
            parsed = dt.datetime.strptime(value, fmt)
            if parsed.tzinfo is None:
                parsed = parsed.replace(tzinfo=KST)
            return parsed.astimezone(KST).strftime("%Y-%m-%d %H:%M")
        except ValueError:
            continue
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=KST)
        return parsed.astimezone(KST).strftime("%Y-%m-%d %H:%M")
    except Exception:
        return value


def parse_rss(text):
    root = ET.fromstring(text)
    channel = root.find("channel")
    if channel is None:
        return []

    items = []
    for item in channel.findall("item"):
        title = clean_text(item.findtext("title", ""))
        link = clean_text(item.findtext("link", ""))
        date = normalize_date(clean_text(item.findtext("pubDate", "")))
        if title and link:
            items.append({"title": title, "link": link, "date": date})
    return items[:MAX_ITEMS]


def parse_atom_youtube(text):
    ns = {
        "a": "http://www.w3.org/2005/Atom",
    }
    root = ET.fromstring(text)
    items = []
    for entry in root.findall("a:entry", ns):
        title = clean_text(entry.findtext("a:title", "", ns))
        date = normalize_date(clean_text(entry.findtext("a:published", "", ns)))
        link = ""
        for link_node in entry.findall("a:link", ns):
            rel = link_node.attrib.get("rel")
            href = link_node.attrib.get("href", "")
            if rel in (None, "alternate") and href:
                link = href
                break
        if title and link:
            items.append({"title": title, "link": link, "date": date})
    return items[:MAX_ITEMS]


def unfold_ics_lines(text):
    lines = []
    for line in text.splitlines():
        if line.startswith((" ", "\t")) and lines:
            lines[-1] += line[1:]
        else:
            lines.append(line.rstrip("\r"))
    return lines


def parse_ics_datetime(raw_value):
    value = raw_value.strip()
    if not value:
        return None
    if "T" in value:
        if value.endswith("Z"):
            parsed = dt.datetime.strptime(value, "%Y%m%dT%H%M%SZ").replace(
                tzinfo=dt.timezone.utc
            )
            return parsed.astimezone(KST)
        for fmt in ("%Y%m%dT%H%M%S%z", "%Y%m%dT%H%M%S"):
            try:
                parsed = dt.datetime.strptime(value, fmt)
                if parsed.tzinfo is None:
                    parsed = parsed.replace(tzinfo=KST)
                return parsed.astimezone(KST)
            except ValueError:
                continue
        return None
    parsed = dt.datetime.strptime(value, "%Y%m%d").replace(tzinfo=KST)
    return parsed


def parse_ics(text):
    lines = unfold_ics_lines(text)
    now = now_kst()
    window_end = add_months(now, CALENDAR_LOOKAHEAD_MONTHS)
    today = now.date()
    events = []
    active = False
    current = {}

    for line in lines:
        if line == "BEGIN:VEVENT":
            active = True
            current = {}
            continue
        if line == "END:VEVENT":
            active = False
            start_raw = current.get("DTSTART", "")
            start_dt = parse_ics_datetime(start_raw) if start_raw else None
            if start_dt and start_dt.date() >= today and start_dt <= window_end:
                summary = clean_text(current.get("SUMMARY", ""))
                url = clean_text(current.get("URL", ""))
                location = clean_text(current.get("LOCATION", ""))
                subtitle = start_dt.strftime("%Y-%m-%d %H:%M")
                events.append(
                    {
                        "title": summary or "(제목 없음)",
                        "link": url or "",
                        "date": subtitle,
                        "location": location,
                        "event_at": start_dt.isoformat(),
                        "_start": start_dt,
                    }
                )
            current = {}
            continue
        if not active or ":" not in line:
            continue
        field, value = line.split(":", 1)
        key = field.split(";", 1)[0]
        current[key] = value

    events.sort(key=lambda item: item["_start"])
    simplified = []
    for event in events:
        event.pop("_start", None)
        simplified.append(event)
    return simplified


def parse_highway_news(text):
    rows = json.loads(text)
    items = []
    for row in rows:
        title_html = row.get("title", {}).get("rendered", "")
        title = clean_text(title_html)
        link = clean_text(row.get("link", ""))
        date = normalize_date(clean_text(row.get("date", "")))
        if title and link:
            items.append({"title": title, "link": link, "date": date})
    return items[:MAX_ITEMS]


def parse_fanclub_news(text):
    pattern = re.compile(
        r'<li class="fadein">.*?<a href="(?P<link>/contents/\d+)">.*?<time[^>]*>(?P<date>.*?)</time>.*?<h3>(?P<title>.*?)</h3>',
        re.S,
    )
    items = []
    for match in pattern.finditer(text):
        title = clean_text(match.group("title"))
        link = f"https://endohmasaaki-fc.com{match.group('link')}"
        date = clean_text(match.group("date")).replace(".", "-")
        if title:
            items.append({"title": title, "link": link, "date": date})
        if len(items) >= MAX_ITEMS:
            break
    return items


def _extract(pattern, block):
    match = re.search(pattern, block, re.S)
    return clean_text(match.group(1)) if match else ""


def parse_jam_feed(text):
    article_pattern = re.compile(
        r'<article class="p-feedList__item[^"]*"[^>]*data-id="(\d+)".*?</article>',
        re.S,
    )
    items = []
    for match in article_pattern.finditer(text):
        article_id = match.group(1)
        block = match.group(0)
        title = _extract(r'<div class="p-feedList__item__title">\s*<a href="[^"]+">(.*?)</a>', block)
        if not title:
            title = _extract(r'<div class="p-feedList__item__authorized__title[^"]*">(.*?)</div>', block)
        date = _extract(r'<div class="p-feedList__item__owner__date">(.*?)</div>', block)
        if not title:
            continue
        items.append(
            {
                "title": title,
                "link": f"https://jamjamsite.com/feed/{article_id}",
                "date": date,
            }
        )
        if len(items) >= MAX_ITEMS:
            break
    return items


def make_event_id(source_id, title, event_at):
    key = f"{source_id}|{title}|{event_at}"
    return hashlib.sha1(key.encode("utf-8")).hexdigest()[:16]


def build_info_pool(results):
    pool = []
    for source in results:
        if source.get("status") != "ok":
            continue
        if source.get("id") in CALENDAR_SOURCE_IDS:
            continue
        for item in source.get("items", []):
            title = clean_text(item.get("title", ""))
            if not title:
                continue
            pool.append(
                {
                    "source": source.get("name", ""),
                    "title": title,
                    "link": clean_text(item.get("link", "")),
                    "date": clean_text(item.get("date", "")),
                    "norm": normalize_for_match(title),
                    "tokens": extract_tokens(title),
                }
            )
    return pool


def find_related_updates(event_title, pool):
    event_norm = normalize_for_match(event_title)
    event_tokens = extract_tokens(event_title)
    candidates = []

    for info in pool:
        score = 0
        info_norm = info.get("norm", "")

        if len(event_norm) >= 8 and event_norm in info_norm:
            score += 60
        elif len(info_norm) >= 8 and info_norm in event_norm:
            score += 30

        shared = 0
        for token in event_tokens:
            if len(token) < 3:
                continue
            if token in info_norm:
                shared += 1
        if shared >= 2:
            score += 40 + (shared * 6)
        elif shared == 1:
            score += 10

        if score >= 40:
            candidates.append(
                {
                    "score": score,
                    "source": info.get("source", ""),
                    "title": info.get("title", ""),
                    "link": info.get("link", ""),
                    "date": info.get("date", ""),
                }
            )

    candidates.sort(key=lambda row: row["score"], reverse=True)
    return [
        {
            "source": row["source"],
            "title": row["title"],
            "link": row["link"],
            "date": row["date"],
        }
        for row in candidates[:2]
    ]


def attach_calendar_meta(results):
    info_pool = build_info_pool(results)
    for source in results:
        if source.get("status") != "ok":
            continue
        source_id = source.get("id")
        if source_id not in CALENDAR_SOURCE_IDS:
            continue

        enriched = []
        for item in source.get("items", []):
            title = clean_text(item.get("title", ""))
            event_at = clean_text(item.get("event_at", ""))
            event_id = make_event_id(source_id, title, event_at or item.get("date", ""))
            related = find_related_updates(title, info_pool)

            next_item = dict(item)
            next_item["event_id"] = event_id
            next_item["has_update"] = len(related) > 0
            next_item["related"] = related
            enriched.append(next_item)

        source["items"] = enriched
        source["count"] = len(enriched)

    return results


def collect(source):
    try:
        text = fetch_text(source["url"])
        items = source["parser"](text)
        return {
            "id": source["id"],
            "name": source["name"],
            "url": source["url"],
            "status": "ok",
            "count": len(items),
            "items": items,
        }
    except Exception as exc:
        return {
            "id": source["id"],
            "name": source["name"],
            "url": source["url"],
            "status": "error",
            "count": 0,
            "error": str(exc),
            "items": [],
        }


def main():
    highway_params = urllib.parse.urlencode(
        {
            "search": "遠藤正明",
            "per_page": "20",
            "_fields": "id,date,title,link",
        },
        quote_via=urllib.parse.quote,
    )

    sources = [
        {
            "id": "official_news",
            "name": "공식 News",
            "url": "https://endoh-masaaki.com/news/feed/",
            "parser": parse_rss,
        },
        {
            "id": "official_blog",
            "name": "공식 Blog",
            "url": "https://endoh-masaaki.com/blog/feed/",
            "parser": parse_rss,
        },
        {
            "id": "calendar_endoh",
            "name": "공식 일정 캘린더",
            "url": "https://calendar.google.com/calendar/ical/enchannel.official%40gmail.com/public/basic.ics",
            "parser": parse_ics,
        },
        {
            "id": "calendar_jam",
            "name": "JAM Project 캘린더",
            "url": "https://calendar.google.com/calendar/ical/fvhub94et61j7luforfdj9nhjo%40group.calendar.google.com/public/basic.ics",
            "parser": parse_ics,
        },
        {
            "id": "youtube",
            "name": "공식 YouTube",
            "url": "https://www.youtube.com/feeds/videos.xml?channel_id=UCBnCeOigma9Cv6eI5_QleQQ",
            "parser": parse_atom_youtube,
        },
        {
            "id": "highway_news",
            "name": "HIGHWAY STAR News API",
            "url": f"https://highwaystar.co.jp/wp-json/wp/v2/news?{highway_params}",
            "parser": parse_highway_news,
        },
        {
            "id": "fanclub_news",
            "name": "팬클럽 NEWS",
            "url": "https://endohmasaaki-fc.com/contents/news",
            "parser": parse_fanclub_news,
        },
        {
            "id": "jam_feed",
            "name": "JAM Project Feed",
            "url": "https://jamjamsite.com/feed/contents",
            "parser": parse_jam_feed,
        },
        {
            "id": "google_news",
            "name": "Google News (키워드)",
            "url": "https://news.google.com/rss/search?q=%E9%81%A0%E8%97%A4%E6%AD%A3%E6%98%8E&hl=ja&gl=JP&ceid=JP:ja",
            "parser": parse_rss,
        },
    ]

    collected_sources = [collect(source) for source in sources]
    result = {
        "updated_at": now_kst().strftime("%Y-%m-%d %H:%M:%S"),
        "timezone": "Asia/Seoul",
        "refresh_minutes": 60,
        "sources": attach_calendar_meta(collected_sources),
    }
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
