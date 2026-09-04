---
name: rednote-video-lens
description: Analyze Xiaohongshu/RedNote videos from a keyword, full share URL, or xhslink short URL without manual uploads, producing a timestamped transcript/structure/hook/keyframe table by default. Use for 小红书视频拆解, 对标视频研究, hook/pacing/visual/transcript analysis, or extracting reusable content patterns. This is a read-only research workflow; do not use it for publishing or engagement actions.
license: MIT
---

# RedNote Video Lens

Accept either a Xiaohongshu share URL or a keyword. Fetch the accessible source material automatically, then ground the analysis in interaction data, transcript evidence, and inspected video frames. Do not ask the user to upload the video unless every authorized URL-based route fails.

## Local tools

- Run Redbook through `scripts/redbook.ps1`; it does not depend on a global `redbook` command.
- Run the Windows-adapted downloader through `scripts/download.ps1`.
- Run `scripts/fetch_public_note.py` first for anonymous page metadata, interaction counts, and platform subtitle tracks when available. It never reads browser cookies.
- For the normal one-link workflow, run `scripts/prepare_breakdown.ps1`; it combines the anonymous metadata/subtitle fetch, the minimum necessary media download, and keyframe extraction into one command.
- Run `scripts/extract_keyframes.py` on a downloaded video before making visual or pacing claims.
- Run `scripts/doctor.ps1` when first used or when dependencies appear broken.

Resolve paths relative to this skill directory. Use a task-local working directory for media and raw JSON. Never print, export, or save browser cookies or security tokens beyond the original share URL supplied by the user.

## Input routing

### Share URL

1. Accept full Xiaohongshu discovery URLs and `xhslink.com` short URLs. The public fetcher expands short URLs before extraction. Preserve the complete resolved URL, including `xsec_token` and `xsec_source` parameters.
2. Run `scripts/prepare_breakdown.ps1 -Url <url> -OutputDirectory <work-dir>`. This is the default fast path. It runs the public evidence fetch, downloads only the video when a platform subtitle already exists, and extracts timeline frames.
3. If the orchestrator is unavailable, run `fetch_public_note.py <url> --output <work-dir>/note.json --subtitle-output <work-dir>/platform.srt`, then use `scripts/download.ps1 <url> --output <work-dir>/media --browser none` and extract frames. Prefer the platform source subtitle over OCR when it exists. Treat the helper's counts as a point-in-time public snapshot.
4. Use Redbook `analyze-viral <url> --comment-pages 1 --json` only when comment themes or author-baseline signals materially improve the requested analysis and an authorized logged-in session is available. If access requires local browser login state, explain this and obtain the user's permission before reading it.
5. If public access fails because the platform requires a session, explain that the next attempt will read the local Chrome login state and obtain the user's permission before retrying with `--browser chrome`. Never request a cookie string.

### Keyword or niche

1. Use one Redbook search: `search <keyword> --type video --sort popular --json`.
2. Default to three candidate videos unless the user requests a different count. Prefer fresh `webUrl` values returned by search.
3. Treat popularity as a candidate signal, not proof. Check each candidate with `analyze-viral` sequentially and compare it with the author's baseline when available.
4. Detail reads are never parallel. For more than five notes, follow the installed Redbook skill's paced research loop and circuit breaker.

## Media analysis

After download:

1. Read `.meta.json`, `transcript.txt`, and the platform subtitle downloaded by `fetch_public_note.py` when present.
2. Prefer a platform source subtitle track. If none exists, use `transcript.txt`; otherwise use the installed `extract-video-subtitles` skill when visible burned-in captions exist. Correct automatic subtitle errors only when the burned-in text, audio, or context supports the correction, and flag unresolved wording.
3. Extract frames:

```powershell
py -3.9 "<skill-dir>\scripts\extract_keyframes.py" "<video-path>" --output "<work-dir>\frames"
```

4. Inspect the opening frames at 0, 1, and 3 seconds plus representative middle, climax, and closing frames. Do not describe shots, edits, subtitles, products, people, or colors that were not actually inspected.
5. Use transcript timestamps and frame timestamps to reconstruct the sequence. Group the video into coherent content beats rather than making one row per subtitle cue. Preserve the complete spoken transcript across the rows.
6. For each beat, choose a representative frame that proves the visual claim. When local image rendering is supported, stage selected frames in the user-facing output area and embed them in the final table; otherwise provide the exact timestamp.

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

Return the analysis inline unless the user asks for a saved report. Include source URLs, evidence gaps, and a concise reusable template. For multiple videos, synthesize shared patterns only after reporting the meaningful differences between them.
