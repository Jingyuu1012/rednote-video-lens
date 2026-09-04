# RedNote Video Lens

RedNote Video Lens is an evidence-first Agent Skill for Codex and Claude Code. It analyzes Xiaohongshu/RedNote videos without asking the user to upload the source video manually.

Maintained by [@Jingyuu1012](https://github.com/Jingyuu1012).

Given a keyword, full Xiaohongshu share URL, or `xhslink.com` short URL, it prepares public metadata, platform subtitles when available, a local evidence copy of the video, timeline keyframes, and pacing signals. Its default deliverable is a timestamped table containing:

| Time | Verbatim transcript | Video structure | Hook / retention device | Keyframe | Visual description | On-screen text |
|---|---|---|---|---|---|---|

The analysis stays grounded in evidence that was actually retrieved and inspected. Unavailable metrics, uncertain transcript wording, and inaccessible comment themes are marked instead of guessed.

## Result you can expect

A completed report starts with a concise performance snapshot, followed by the evidence table, an explanation of why the structure works, its limitations, and a reusable content formula.

Example performance snapshot:

```text
Duration: 52.4 seconds
Public snapshot: 2,430 likes · 1,120 collects · 185 comments · 640 shares
Collect-to-like ratio: 46.1%
Detected cuts: 38 · Median shot interval: 1.1 seconds
Evidence gaps: author baseline unavailable; comment themes not fetched
```

Example table — the content below is synthetic and does not reproduce a creator's video:

| Time | Verbatim transcript | Video structure | Hook / retention device | Keyframe | Visual description | On-screen text |
|---|---|---|---|---|---|---|
| 00:00–00:03 | “Most people don't know this place exists.” | Opening promise | Information gap and local relevance | `frame_01_0000s.jpg` | Presenter enters a large warehouse; wide shot proves scale immediately. | “90% of locals don't know” |
| 00:03–00:12 | “This entire aisle is one product category.” | Scale proof | Abundance, fast product reveals, escalating specificity | `frame_04_0006s.jpg` | Close-ups alternate with wide aisle shots; cuts occur roughly once per second. | Product category and quantity labels |
| 00:12–00:31 | “The brands you see in supermarkets are supplied from here.” | Credibility and recognition | Familiar-brand recognition plus staff confirmation | `frame_07_0020s.jpg` | Interview framing alternates with recognizable packaging. | Distributor identity and retail channels |
| 00:31–00:47 | “Here is the most unusual item we found.” | Novelty climax | Pattern interrupt and product surprise | `frame_10_0038s.jpg` | Tight product demonstration with reaction shot. | Unusual ingredient or feature |
| 00:47–00:52 | “Save this address for your next visit.” | Payoff and CTA | Location reveal closes the opening information gap | `frame_13_0051s.jpg` | Final location card remains visible long enough to save. | Store name, address, opening hours |

When local image rendering is available, the Keyframe column contains the inspected frame itself rather than only the filename. The final explanation also distinguishes evidence from inference and identifies improvements such as missing price proof, unclear buying rules, or a weak CTA.

Typical reusable formula:

```text
Familiar analogy → information gap → scale proof → recognizable examples
→ authority confirmation → novelty climax → exact location/value payoff → CTA
```

## What is original here

This repository contains the RedNote Video Lens workflow, evidence schema, public-note metadata extraction, short-link normalization, pacing analysis, keyframe sampling, and safety/stopping rules. It does not bundle the source code or runtime files of its third-party dependencies.

See [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for dependency attribution.

## Requirements

- Codex or Claude Code with personal skills support
- Windows PowerShell 5.1 or PowerShell 7+
- Python 3.9 or newer; Python 3.10+ is recommended
- FFmpeg, or `imageio-ffmpeg` available to Python
- [`redbook`](https://github.com/lucasygu/redbook) for keyword discovery, comments, and author-baseline analysis
- A compatible `xiaohongshu-downloader` skill installed under the active product's personal skills directory for media acquisition and fallback transcription

The anonymous one-link workflow does not read browser cookies. If public access fails and a logged-in browser route is needed, the skill stops and requests permission first.

## Install

### Codex

Clone the repository into your personal Codex skills directory:

```powershell
git clone https://github.com/Jingyuu1012/rednote-video-lens.git "$env:USERPROFILE\.codex\skills\rednote-video-lens"
```

Install the dependencies listed above, restart or refresh Codex, then run:

```text
Use $rednote-video-lens to analyze this video: <Xiaohongshu URL>
```

### Claude Code

Clone the same repository into Claude Code's personal skills directory:

```powershell
git clone https://github.com/Jingyuu1012/rednote-video-lens.git "$env:USERPROFILE\.claude\skills\rednote-video-lens"
```

Invoke it directly in Claude Code:

```text
/rednote-video-lens <Xiaohongshu URL>
```

Claude Code can also select it automatically from a natural-language request that matches the description. The `agents/openai.yaml` file supplies Codex UI metadata and is not required by Claude Code.

In either product, you can also ask naturally:

```text
Analyze this Xiaohongshu video: <URL>
```

## Verify the installation

```powershell
.\scripts\doctor.ps1
```

For a complete anonymous URL test:

```powershell
.\scripts\prepare_breakdown.ps1 -Url "<Xiaohongshu URL>" -OutputDirectory ".\work\sample"
```

## Safety and responsible use

- Read-only research: the skill must not like, collect, comment, follow, message, publish, or delete content.
- Stop on CAPTCHA, `NeedVerify`, protected empty responses, expired sessions, or IP blocks.
- Do not commit cookies, tokens, downloaded videos, subtitles, note metadata, or generated frames.
- Download and analyze only material you are entitled to access; do not use the workflow to redistribute source media.
- Respect Xiaohongshu's terms, creator rights, privacy, and applicable local law.

## License

RedNote Video Lens is released under the [MIT License](LICENSE). Third-party components retain their own licenses.
