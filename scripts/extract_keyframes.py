#!/usr/bin/env python3
"""Extract evidence frames from a local video using FFmpeg."""

from __future__ import annotations

import argparse
import json
import re
import shutil
import statistics
import subprocess
import sys
from pathlib import Path


RUNTIME_CANDIDATES = (
    Path.home() / ".codex" / "skills" / "xiaohongshu-downloader" / "runtime" / "python",
    Path.home() / ".claude" / "skills" / "xiaohongshu-downloader" / "runtime" / "python",
)
for runtime in RUNTIME_CANDIDATES:
    if runtime.is_dir():
        sys.path.insert(0, str(runtime))
        break


def ffmpeg_executable() -> str:
    executable = shutil.which("ffmpeg")
    if executable:
        return executable
    try:
        from imageio_ffmpeg import get_ffmpeg_exe

        return get_ffmpeg_exe()
    except (ImportError, RuntimeError) as exc:
        raise RuntimeError("FFmpeg is unavailable; run scripts/doctor.ps1") from exc


def duration_seconds(video: Path, ffmpeg: str) -> float:
    result = subprocess.run(
        [ffmpeg, "-i", str(video)], capture_output=True, text=True, check=False
    )
    match = re.search(r"Duration:\s*(\d+):(\d+):(\d+(?:\.\d+)?)", result.stderr)
    if not match:
        raise RuntimeError("Unable to determine video duration")
    hours, minutes, seconds = match.groups()
    return int(hours) * 3600 + int(minutes) * 60 + float(seconds)


def unique_times(duration: float) -> list[float]:
    requested = [0.0, 1.0, 3.0]
    requested.extend(duration * fraction for fraction in (0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.97))
    bounded = [min(max(value, 0.0), max(duration - 0.05, 0.0)) for value in requested]
    return sorted({round(value, 3) for value in bounded})


def scene_analysis(video: Path, ffmpeg: str, threshold: float = 0.25) -> dict:
    result = subprocess.run(
        [
            ffmpeg,
            "-hide_banner",
            "-i",
            str(video),
            "-vf",
            f"select='gt(scene,{threshold})',showinfo",
            "-an",
            "-f",
            "null",
            "-",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    timestamps = [float(value) for value in re.findall(r"pts_time:([0-9.]+)", result.stderr)]
    intervals = [later - earlier for earlier, later in zip(timestamps, timestamps[1:])]
    return {
        "scene_threshold": threshold,
        "detected_cuts": len(timestamps),
        "cut_timestamps": [round(value, 3) for value in timestamps],
        "mean_interval_seconds": round(statistics.mean(intervals), 3) if intervals else None,
        "median_interval_seconds": round(statistics.median(intervals), 3) if intervals else None,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Extract representative video frames")
    parser.add_argument("video", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()

    video = args.video.expanduser().resolve()
    if not video.is_file():
        parser.error(f"video not found: {video}")

    output = args.output.expanduser().resolve()
    output.mkdir(parents=True, exist_ok=True)
    ffmpeg = ffmpeg_executable()
    duration = duration_seconds(video, ffmpeg)
    frames = []

    for index, timestamp in enumerate(unique_times(duration), 1):
        target = output / f"frame_{index:02d}_{timestamp:08.3f}s.jpg"
        subprocess.run(
            [
                ffmpeg,
                "-hide_banner",
                "-loglevel",
                "error",
                "-ss",
                str(timestamp),
                "-i",
                str(video),
                "-frames:v",
                "1",
                "-q:v",
                "2",
                "-y",
                str(target),
            ],
            check=True,
        )
        frames.append({"timestamp": timestamp, "path": str(target)})

    manifest = {
        "video": str(video),
        "duration_seconds": duration,
        "frames": frames,
        "pacing": scene_analysis(video, ffmpeg),
    }
    manifest_path = output / "frames.json"
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    print(manifest_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
