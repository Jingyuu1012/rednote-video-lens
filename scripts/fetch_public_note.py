#!/usr/bin/env python3
"""Fetch public Xiaohongshu note evidence without browser cookies."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import pathlib
import sys
import urllib.error
import urllib.request
import urllib.parse


RUNTIME_CANDIDATES = (
    pathlib.Path.home() / ".codex" / "skills" / "xiaohongshu-downloader" / "runtime" / "python",
    pathlib.Path.home() / ".claude" / "skills" / "xiaohongshu-downloader" / "runtime" / "python",
)
for runtime in RUNTIME_CANDIDATES:
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
        break

try:
    from yt_dlp import YoutubeDL
    from yt_dlp.extractor.xiaohongshu import XiaoHongShuIE
    from yt_dlp.utils import js_to_json
    from yt_dlp.utils.traversal import traverse_obj
except ImportError as exc:
    raise SystemExit(
        "yt-dlp runtime is missing. Install or repair the xiaohongshu-downloader skill in Codex or Claude Code first."
    ) from exc


def parse_count(value):
    if value in (None, ""):
        return None
    text = str(value).strip()
    multiplier = 1
    if text.endswith("万"):
        multiplier, text = 10_000, text[:-1]
    elif text.endswith("亿"):
        multiplier, text = 100_000_000, text[:-1]
    try:
        return int(float(text) * multiplier)
    except ValueError:
        return value


def iso_utc(milliseconds):
    if not milliseconds:
        return None
    return dt.datetime.fromtimestamp(milliseconds / 1000, tz=dt.timezone.utc).isoformat()


def resolve_share_url(url):
    """Expand an xhslink short URL without using browser cookies."""
    parsed = urllib.parse.urlsplit(url)
    host = (parsed.hostname or "").lower()
    if host not in {"xhslink.com", "www.xhslink.com"}:
        return url

    request = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            resolved = response.geturl()
    except urllib.error.HTTPError as exc:
        resolved = exc.geturl()

    resolved_host = (urllib.parse.urlsplit(resolved).hostname or "").lower()
    if not resolved_host.endswith("xiaohongshu.com"):
        raise SystemExit("The xhslink URL did not resolve to a Xiaohongshu note.")
    return resolved


def first_subtitle(note):
    media_v2_raw = traverse_obj(note, ("video", "mediaV2", {str}))
    if not media_v2_raw:
        return None
    try:
        media_v2 = json.loads(media_v2_raw)
    except json.JSONDecodeError:
        return None
    tracks = traverse_obj(media_v2, ("video", "subtitles", {dict})) or {}
    candidates = tracks.get("source") or tracks.get("zh-CN") or []
    if not candidates or not candidates[0].get("url"):
        return None
    return {
        "url": candidates[0]["url"],
        "language": candidates[0].get("language"),
        "format": "srt",
    }


def duration_seconds(note):
    duration_ms = traverse_obj(note, ("video", "media", "stream", "h264", 0, "duration"))
    if isinstance(duration_ms, (int, float)):
        return round(duration_ms / 1000, 3)
    duration = traverse_obj(note, ("video", "media", "video", "duration"))
    return duration if isinstance(duration, (int, float)) else None


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("url", help="Full Xiaohongshu share URL, including xsec parameters")
    parser.add_argument("--output", type=pathlib.Path, help="Optional JSON output path")
    parser.add_argument("--subtitle-output", type=pathlib.Path, help="Optional platform SRT output path")
    parser.add_argument("--quiet", action="store_true", help="Write files without printing the JSON payload")
    args = parser.parse_args()

    resolved_url = resolve_share_url(args.url)
    display_id = XiaoHongShuIE._match_id(resolved_url)
    with YoutubeDL({"quiet": True, "no_warnings": True}) as ydl:
        extractor = XiaoHongShuIE(ydl)
        webpage = extractor._download_webpage(resolved_url, display_id)
        state = extractor._search_json(
            r"window\.__INITIAL_STATE__\s*=",
            webpage,
            "initial state",
            display_id,
            transform_source=js_to_json,
        )

    note = traverse_obj(state, ("note", "noteDetailMap", display_id, "note"))
    if not isinstance(note, dict):
        raise SystemExit("Public note state was unavailable or protected.")

    interact = note.get("interactInfo") or {}
    creator = note.get("user") or {}
    subtitle = first_subtitle(note)
    result = {
        "note_id": note.get("noteId") or display_id,
        "title": note.get("title"),
        "description": note.get("desc"),
        "type": note.get("type"),
        "published_at_unix_ms": note.get("time"),
        "published_at_utc": iso_utc(note.get("time")),
        "updated_at_unix_ms": note.get("lastUpdateTime"),
        "updated_at_utc": iso_utc(note.get("lastUpdateTime")),
        "duration_seconds": duration_seconds(note),
        "creator": {
            "user_id": creator.get("userId"),
            "nickname": creator.get("nickname"),
        },
        "interactions": {
            "likes": parse_count(interact.get("likedCount")),
            "collects": parse_count(interact.get("collectedCount")),
            "comments": parse_count(interact.get("commentCount")),
            "shares": parse_count(interact.get("shareCount")),
        },
        "tags": [item.get("name") for item in note.get("tagList") or [] if item.get("name")],
        "platform_subtitle": None,
        "source_url": urllib.parse.urlunsplit((*urllib.parse.urlsplit(resolved_url)[:3], "", "")),
    }

    if args.subtitle_output and subtitle:
        request = urllib.request.Request(subtitle["url"], headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(request) as response:
            payload = response.read()
        args.subtitle_output.parent.mkdir(parents=True, exist_ok=True)
        args.subtitle_output.write_bytes(payload)
        result["platform_subtitle"] = {
            "language": subtitle.get("language"),
            "format": subtitle.get("format"),
            "path": str(args.subtitle_output.resolve()),
            "bytes": len(payload),
        }
    elif subtitle:
        result["platform_subtitle"] = {
            "language": subtitle.get("language"),
            "format": subtitle.get("format"),
            "available": True,
        }

    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(serialized + "\n", encoding="utf-8")
    if not args.quiet:
        print(serialized)


if __name__ == "__main__":
    main()
