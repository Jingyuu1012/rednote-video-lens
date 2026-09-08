---
name: rednote-video-lens
description: 从关键词、小红书完整分享链接或 xhslink 短链接自动获取并拆解视频，无需用户手动上传；默认生成含时间、逐字稿、结构、钩子、真实关键帧、画面描述和画面提示词的中文表格。Use for 小红书视频拆解、爆款视频分析、对标研究, hook/pacing/visual/transcript analysis, or reusable content patterns. Read-only; do not use for publishing or engagement actions.
license: MIT
---

# RedNote Video Lens

Accept either a Xiaohongshu share URL or a keyword. Fetch the accessible source material automatically, then ground the analysis in interaction data, transcript evidence, and inspected video frames. Do not ask the user to upload the video unless every authorized URL-based route fails. Default to Chinese for Xiaohongshu requests unless the user asks for another language.

## Local tools

- Use `scripts/rednote_video_lens.py` as the primary cross-platform entry point on macOS, Linux, and Windows.
- On macOS/Linux, prefer `<skill-dir>/.venv/bin/python` when it exists; otherwise use `python3`. On Windows, prefer `<skill-dir>\.venv\Scripts\python.exe` when it exists; otherwise use `py -3` or `python`.
- Run `rednote_video_lens.py doctor` when first used or when dependencies appear broken.
- Run optional Redbook commands through `rednote_video_lens.py redbook -- <arguments>`; it locates the installed Redbook skill without requiring a global `redbook` command.
- The `.ps1` files are compatibility wrappers for existing Windows installations and are not required on macOS/Linux.
- Run `scripts/fetch_public_note.py` first for anonymous page metadata, interaction counts, and platform subtitle tracks when available. It never reads browser cookies.
- For the normal one-link workflow, run `rednote_video_lens.py prepare`; it combines the anonymous metadata/subtitle fetch, minimum necessary media download, and keyframe extraction into one command.
- Run `scripts/extract_keyframes.py` on a downloaded video before making visual or pacing claims.

Resolve paths relative to this skill directory. Use a task-local working directory for media and raw JSON. Never print, export, or save browser cookies or security tokens beyond the original share URL supplied by the user.

## Input routing

### Share URL

1. Accept full Xiaohongshu discovery URLs and `xhslink.com` short URLs. The public fetcher expands short URLs before extraction. Preserve the complete resolved URL, including `xsec_token` and `xsec_source` parameters.
2. Run `<python> scripts/rednote_video_lens.py prepare --url <url> --output-dir <work-dir>`. This is the default fast path on every supported operating system. Here `<python>` means the skill-local virtual-environment interpreter when installed, otherwise `python3` on macOS/Linux or `py -3` on Windows.
3. If the orchestrator is unavailable, run `fetch_public_note.py <url> --output <work-dir>/note.json --subtitle-output <work-dir>/platform.srt`, download anonymously with yt-dlp, and run `extract_keyframes.py`. Prefer the platform source subtitle over OCR when it exists. Treat the helper's counts as a point-in-time public snapshot.
4. Use Redbook `analyze-viral <url> --comment-pages 1 --json` only when comment themes or author-baseline signals materially improve the requested analysis and an authorized logged-in session is available. If access requires local browser login state, explain this and obtain the user's permission before reading it.
5. If public access fails because the platform requires a session, explain that the next attempt will read the local Chrome login state and obtain the user's permission before retrying with `--browser chrome`. Never request a cookie string.

### Keyword or niche

1. Use one Redbook search through the cross-platform wrapper: `<python> scripts/rednote_video_lens.py redbook -- search <keyword> --type video --sort popular --json`.
2. Default to three candidate videos unless the user requests a different count. Prefer fresh `webUrl` values returned by search.
3. Treat popularity as a candidate signal, not proof. Check each candidate with `analyze-viral` sequentially and compare it with the author's baseline when available.
4. Detail reads are never parallel. For more than five notes, follow the installed Redbook skill's paced research loop and circuit breaker.

## Media analysis

After download:

1. Read `.meta.json`, `transcript.txt`, and the platform subtitle downloaded by `fetch_public_note.py` when present.
2. Prefer a platform source subtitle track. If none exists, use `transcript.txt`; otherwise use the installed `extract-video-subtitles` skill when visible burned-in captions exist. Correct automatic subtitle errors only when the burned-in text, audio, or context supports the correction, and flag unresolved wording.
3. Extract frames:

```shell
<python> scripts/rednote_video_lens.py extract "<video-path>" --output-dir "<work-dir>/frames"
```

4. Inspect the opening frames at 0, 1, and 3 seconds plus representative middle, climax, and closing frames. Do not describe shots, edits, subtitles, products, people, or colors that were not actually inspected.
5. Use transcript timestamps and frame timestamps to reconstruct the sequence. Group the video into coherent content beats rather than making one row per subtitle cue. Preserve the complete spoken transcript across the rows.
6. For each beat, choose a representative frame that proves the visual claim. When local image rendering is supported, stage selected frames in the user-facing output area and embed the actual image in the final table; a filename alone is not sufficient. Otherwise provide the exact timestamp and state that image rendering is unavailable.

## Analysis standard

For a deep breakdown, read [references/report-schema.md](references/report-schema.md). Cover:

- objective performance evidence and whether the note is a true outlier;
- first-three-second hook, promise, audience, and tension;
- transcript structure, information density, proof, memorable lines, and CTA;
- framing, subject, on-screen text, cuts, pattern interrupts, and visual progression;
- pacing and retention devices across the timeline;
- comment themes and collect/comment/share ratios;
- a reusable formula plus elements that must not be copied literally.

For a single-video breakdown, the timestamped evidence table in the report schema is the default deliverable, not an optional appendix.

Never present platform folklore as an established algorithm rule. Attribute causal explanations as reasoned inferences. If a metric, timestamp, or visual element is unavailable, mark it unavailable instead of estimating it.

## Safety and stopping conditions

- This workflow is read-only. Do not like, collect, comment, follow, message, publish, or delete anything.
- Stop on the first `NeedVerify`, CAPTCHA, empty protected response, expired session, or IP block. Do not automate around verification.
- Do not run high-frequency or parallel note reads. Preserve Redbook's steady pacing and daily budget.
- Download only material the user is entitled to access and use it for analysis, not redistribution.

## Completion

Return the analysis inline unless the user asks for a saved report. For Xiaohongshu requests, use Chinese field names and Chinese analysis by default while preserving brand names and quoted source text accurately. Include source URLs, evidence gaps, and a concise reusable template. For multiple videos, synthesize shared patterns only after reporting the meaningful differences between them.
