#!/usr/bin/env python3
"""Cross-platform CLI for RedNote Video Lens (macOS, Linux, and Windows)."""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
from typing import Optional, Tuple


for stream in (sys.stdout, sys.stderr):
    if hasattr(stream, "reconfigure"):
        stream.reconfigure(encoding="utf-8", errors="replace")


SKILL_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = SKILL_ROOT / "scripts"
VIDEO_SUFFIXES = {".mp4", ".mkv", ".webm", ".mov"}
SKILL_HOMES = (
    Path.home() / ".codex" / "skills",
    Path.home() / ".claude" / "skills",
)
RUNTIME_CANDIDATES = tuple(
    home / "xiaohongshu-downloader" / "runtime" / "python" for home in SKILL_HOMES
)
for runtime in RUNTIME_CANDIDATES:
    if runtime.is_dir() and str(runtime) not in sys.path:
        sys.path.insert(0, str(runtime))


class LensError(RuntimeError):
    """A user-actionable workflow error."""


def first_file(relative_path: str) -> Optional[Path]:
    for home in SKILL_HOMES:
        candidate = home / relative_path
        if candidate.is_file():
            return candidate
    return None


def yt_dlp_command() -> list[str]:
    executable = shutil.which("yt-dlp")
    if executable:
        return [executable]
    try:
        import yt_dlp
    except ImportError:
        return []
    package_root = str(Path(yt_dlp.__file__).resolve().parent.parent)
    bootstrap = (
        "import sys; "
        f"sys.path.insert(0, {package_root!r}); "
        "import yt_dlp; yt_dlp.main()"
    )
    return [sys.executable, "-c", bootstrap]


def ffmpeg_executable() -> Optional[str]:
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        return get_ffmpeg_exe()
    except (ImportError, RuntimeError):
        return None


def downloader_script() -> Optional[Path]:
    return first_file("xiaohongshu-downloader/scripts/download_xiaohongshu.py")


def redbook_cli() -> Optional[Path]:
    return first_file("redbook/dist/cli.js")


def run(command: list[str], *, capture: bool = False) -> subprocess.CompletedProcess[str]:
    env = os.environ.copy()
    env.setdefault("PYTHONUTF8", "1")
    return subprocess.run(
        command,
        check=False,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=capture,
        env=env,
    )


def require_success(result: subprocess.CompletedProcess[str], message: str) -> None:
    if result.returncode == 0:
        return
    details = (result.stderr or result.stdout or "").strip().splitlines()[-20:]
    if details:
        print("\n".join(details), file=sys.stderr)
    raise LensError(message)


def download_video(url: str, output_dir: Path, *, full: bool = False) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    helper = downloader_script()
    if full and helper:
        command = [
            sys.executable,
            str(helper),
            url,
            "--output",
            str(output_dir),
            "--browser",
            "none",
            "--full",
        ]
    else:
        command = yt_dlp_command()
        if not command:
            raise LensError(
                "yt-dlp is unavailable. Run `python3 -m pip install -r requirements.txt`."
            )
        command += [
            "--no-playlist",
            "--format",
            "bestvideo*+bestaudio/best",
            "--merge-output-format",
            "mp4",
            "--output",
            str(output_dir / "%(title).120B [%(id)s].%(ext)s"),
            url,
        ]
    result = run(command, capture=True)
    require_success(
        result,
        "Anonymous video download failed. Stop before attempting any browser-cookie route.",
    )
    videos = sorted(
        (
            path
            for path in output_dir.rglob("*")
            if path.is_file() and path.suffix.lower() in VIDEO_SUFFIXES
        ),
        key=lambda path: path.stat().st_size,
        reverse=True,
    )
    if not videos:
        raise LensError(f"No downloaded video was found under {output_dir}")
    return videos[0].resolve()


def fetch_public(url: str, output_dir: Path) -> Tuple[dict, Optional[Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    fetcher = SCRIPTS_DIR / "fetch_public_note.py"
    note_json = output_dir / "note.json"
    subtitle = output_dir / "platform.zh-CN.srt"
    result = run(
        [
            sys.executable,
            str(fetcher),
            url,
            "--output",
            str(note_json),
            "--subtitle-output",
            str(subtitle),
            "--quiet",
        ],
        capture=True,
    )
    require_success(
        result,
        "Anonymous public-note fetch failed. Stop before attempting any browser-cookie route.",
    )
    note = json.loads(note_json.read_text(encoding="utf-8"))
    return note, subtitle.resolve() if subtitle.is_file() else None


def extract_frames(video: Path, output_dir: Path) -> Path:
    extractor = SCRIPTS_DIR / "extract_keyframes.py"
    result = run(
        [sys.executable, str(extractor), str(video), "--output", str(output_dir)],
        capture=True,
    )
    require_success(result, "Keyframe extraction failed.")
    manifest = output_dir / "frames.json"
    if not manifest.is_file():
        raise LensError("Keyframe extraction finished without a frames manifest.")
    return manifest.resolve()


def fallback_transcript(media_dir: Path) -> Optional[Path]:
    candidates = list(media_dir.rglob("transcript.txt")) + list(media_dir.rglob("*.srt"))
    return candidates[0].resolve() if candidates else None


def prepare(url: str, output_dir: Path) -> Path:
    output_dir = output_dir.expanduser().resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    note, platform_subtitle = fetch_public(url, output_dir)
    media_dir = output_dir / "media"
    video = download_video(url, media_dir, full=platform_subtitle is None)
    frames_manifest = extract_frames(video, output_dir / "frames")
    transcript = platform_subtitle or fallback_transcript(media_dir)
    if platform_subtitle:
        transcript_source = "xiaohongshu-platform-source"
    elif transcript:
        transcript_source = "downloader-fallback"
    else:
        transcript_source = "unavailable"
    manifest = {
        "prepared_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "source_url": note.get("source_url"),
        "note_json": str((output_dir / "note.json").resolve()),
        "title": note.get("title"),
        "creator": note.get("creator"),
        "interactions": note.get("interactions"),
        "duration_seconds": note.get("duration_seconds"),
        "transcript": str(transcript) if transcript else None,
        "transcript_source": transcript_source,
        "video": str(video),
        "frames_manifest": str(frames_manifest),
    }
    manifest_path = output_dir / "evidence-manifest.json"
    manifest_path.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return manifest_path.resolve()


def doctor() -> int:
    python_ok = sys.version_info >= (3, 9)
    checks = {
        "platform": sys.platform,
        "python_3_9_plus": python_ok,
        "skill_root": (SKILL_ROOT / "SKILL.md").is_file(),
        "public_fetch_script": (SCRIPTS_DIR / "fetch_public_note.py").is_file(),
        "keyframe_script": (SCRIPTS_DIR / "extract_keyframes.py").is_file(),
        "yt_dlp": bool(yt_dlp_command()),
        "ffmpeg": bool(ffmpeg_executable()),
        "redbook_cli_optional": bool(redbook_cli()),
        "xiaohongshu_downloader_optional": bool(downloader_script()),
    }
    for name, value in checks.items():
        print(f"{name}: {value}")
    required = (
        "python_3_9_plus",
        "skill_root",
        "public_fetch_script",
        "keyframe_script",
        "yt_dlp",
        "ffmpeg",
    )
    return 0 if all(checks[name] is True for name in required) else 1


def run_redbook(arguments: list[str]) -> int:
    node = shutil.which("node")
    cli = redbook_cli()
    if not node or not cli:
        raise LensError(
            "Keyword discovery requires Node.js and the optional redbook skill under ~/.codex/skills or ~/.claude/skills."
        )
    if arguments[:1] == ["--"]:
        arguments = arguments[1:]
    return run([node, str(cli), *arguments]).returncode


def parser() -> argparse.ArgumentParser:
    root = argparse.ArgumentParser(description=__doc__)
    subcommands = root.add_subparsers(dest="command", required=True)
    subcommands.add_parser("doctor", help="Check the cross-platform runtime")

    prepare_parser = subcommands.add_parser("prepare", help="Prepare evidence from a share URL")
    prepare_parser.add_argument("--url", required=True)
    prepare_parser.add_argument("--output-dir", type=Path, required=True)

    fetch_parser = subcommands.add_parser("fetch", help="Fetch public note metadata and subtitles")
    fetch_parser.add_argument("--url", required=True)
    fetch_parser.add_argument("--output-dir", type=Path, required=True)

    extract_parser = subcommands.add_parser("extract", help="Extract keyframes from a local video")
    extract_parser.add_argument("video", type=Path)
    extract_parser.add_argument("--output-dir", type=Path, required=True)

    download_parser = subcommands.add_parser("download", help="Download the video anonymously")
    download_parser.add_argument("--url", required=True)
    download_parser.add_argument("--output-dir", type=Path, required=True)
    download_parser.add_argument("--full", action="store_true")

    redbook_parser = subcommands.add_parser("redbook", help="Run the optional Redbook CLI")
    redbook_parser.add_argument("redbook_args", nargs=argparse.REMAINDER)
    return root


def main() -> int:
    args = parser().parse_args()
    try:
        if args.command == "doctor":
            return doctor()
        if args.command == "prepare":
            prepare(args.url, args.output_dir)
            return 0
        if args.command == "fetch":
            note, subtitle = fetch_public(args.url, args.output_dir.expanduser().resolve())
            print(json.dumps({"note": note, "subtitle": str(subtitle) if subtitle else None}, ensure_ascii=False, indent=2))
            return 0
        if args.command == "extract":
            print(extract_frames(args.video.expanduser().resolve(), args.output_dir.expanduser().resolve()))
            return 0
        if args.command == "download":
            print(download_video(args.url, args.output_dir.expanduser().resolve(), full=args.full))
            return 0
        if args.command == "redbook":
            return run_redbook(args.redbook_args)
    except LensError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
