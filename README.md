# shorts-pipeline

**An AI-operated pipeline that turns hours of live-stream video into vertical Shorts, and a calibrated "humor gate" that decides which moments deserve one.**

[![tests](https://github.com/DiegoVillalobosA/shorts-pipeline/actions/workflows/tests.yml/badge.svg)](https://github.com/DiegoVillalobosA/shorts-pipeline/actions)
![python](https://img.shields.io/badge/python-3.10%2B-blue)
![deps](https://img.shields.io/badge/dependencies-stdlib%20only-green)

I run a Shorts channel where **everything is produced with Claude**: finding
moments, judging them, subtitling, sound design, ffmpeg rendering, quality review,
scheduling and post-mortems. I only publish and rate the result. This repo holds
the engine and the lessons that came out of running it. Streamer footage is
**not** included.

```text
VOD + chat ─► peak detection ─► candidates ─► HUMOR GATE ─► 9:16 montage ─► QA gates ─► frame review ─► human: publish + rate
                (chat, audio)    (+transcript,   (scorecard    (layout, karaoke,  (blocking vs      (Claude looks     │
                                  + frames)       → decision)   sfx, ffmpeg)       warning)          at real frames)   │
                       ▲                                                                                                │
                       └──────────────  ratings + views/retention recalibrate the gate and the rules  ◄───────────────┘
```

## What is interesting here

| | |
|---|---|
| **Detect energy, then judge funniness** | Peak detectors correlate **-0.34** with human taste on a real VOD. A second stage fills an 8-criterion scorecard from frames + transcript; Python (not the model) turns it into a score and a routing decision, so the gate is auditable and recalibratable. |
| **Honest evaluation** | The judge's retrospective fit is flagged as optimistic in the docs; its first prospective test over-predicted (4.6 vs ~3.5). The bar to trust it is r >= 0.5 on 15+ blind ratings. |
| **"0 of 60" was the source, not the threshold** | The gate rejected every launch-day candidate. Instead of lowering the bar, frame review showed they were menus and cutscenes, and the fix was to change the source. |
| **Gates that block vs gates that warn** | Hard rules (size, length, captions lit during silence) block. Signals that a 59-pair study showed *don't* separate winners from losers (cut count, first-frame face) only warn. |
| **Karaoke that follows the voice** | Per-word timestamps with silence gating; highlight-in-silence went from **35 % to 0/130 words**, enforced as a < 5 % gate. |
| **Rules in layers, with provenance** | Always-on rules <= 12 lines; per-task skills with a lessons file; every lesson tagged `[OWNER]` `[MEASURED]` `[EXTERNAL]` `[HYPOTHESIS]`; a lesson broken twice becomes code. |
| **Claude as orchestrator** | One coordinator spawns short-lived parallel threads per task, picks the model tier by task, runs a daily scheduled job, and respects a kill switch, quiet hours and a human-only publish step. |

## Quick start

Requirements: Python 3.10+, and `ffmpeg`/`ffprobe` for rendering and audio peaks. No Python dependencies.

```bash
git clone https://github.com/DiegoVillalobosA/shorts-pipeline && cd shorts-pipeline
pip install -e .
python -m unittest discover -s tests          # 32 tests, no media needed

# rank chat peaks from a TwitchDownloader chat JSON
python -m shorts_pipeline chat-peaks chat.json --top 10     # or try examples/sample_chat.json (synthetic)

# loudness peaks from a VOD's audio
python -m shorts_pipeline audio-peaks vod_audio.mp4

# score a humor scorecard
python -m shorts_pipeline judge examples/one_card.json

# validate a YouTube title (26-45 chars, exactly one emoji)
python -m shorts_pipeline check-title "Streamer finds a huge secret in GTA 6 😳"
```

Example output of `chat-peaks` on the synthetic sample (it contains two real-looking bursts and one single-account spam burst):

```text
 1. 0:10:00    65 msgs  score  7.50  cut 0:09:40-0:10:20
 2. 0:16:40    85 msgs  score 10.00  cut 0:16:20-0:17:00  [possible spam]
 3. 0:21:40    65 msgs  score  7.50  cut 0:21:20-0:22:00
```

## Modules

| Module | What it does |
|---|---|
| [`chat_peaks.py`](src/shorts_pipeline/chat_peaks.py) | Windowed chat counts vs a *local* median baseline, system-message filtering, separation, spam flag, suggested cut with lead-in (chat lags the joke). |
| [`audio_peaks.py`](src/shorts_pipeline/audio_peaks.py) | RMS loudness per window via ffmpeg `astats`; requires *absolute* loudness so leaving silence isn't a "peak". |
| [`humor_judge.py`](src/shorts_pipeline/humor_judge.py) | Scorecard -> 1-5 score -> `solo` / `top_or_solo` / `top_low_slot` / `improve_edit` / `top_only_burnt` / `discard`, with vetoes and a Pearson helper for recalibration. |
| [`layout.py`](src/shorts_pipeline/layout.py) | 1080x1920 ffmpeg filter graphs: stacked (cam 40 % / game 60 %), wide-crop over blurred backdrop, and full-frame. |
| [`karaoke.py`](src/shorts_pipeline/karaoke.py) | Word-timed ASS captions, pause-aware line grouping, partial censoring (`s**t`), silence-ratio QA metric. |
| [`sfx_plan.py`](src/shorts_pipeline/sfx_plan.py) | Places sound effects by event type with a 2 s minimum gap and a per-length cap; unmatched events stay silent. |
| [`qa_gates.py`](src/shorts_pipeline/qa_gates.py) | ffprobe validation, title rules, and the blocking/warning split. |

Design write-ups:

* [Architecture and flow diagram](docs/architecture.md)
* [Claude as orchestrator: threads, layered rules, model tiers, scheduling](docs/orchestration.md)
* [The humor gate: rubric, patterns, honest validation](docs/humor-judge.md)
* [Lessons with provenance](docs/lessons.md)
* [Results so far](docs/results.md)

## Results (early, and I say so)

The channel launched on 2026-11-18, so these are baseline numbers, not a growth
story: the first four Shorts reached 49 views after three days, and retention
ranged from 37 % to 105 %. What matters is the loop: those numbers and the
owner's 1-5 ratings already changed titles, added the humor gate, and moved
the rules into code. See [docs/results.md](docs/results.md) and
[`data/results.csv`](data/results.csv).

## Scope and ethics

* Source material is public stream content from creators; the channel credits the
  streamer on every Short and aims at transformation (commentary, edit, framing),
  not re-uploads. **No third-party footage or audio is stored here** (`.gitignore`
  blocks media).
* Nothing publishes itself: a human uploads every Short.
* API keys live outside the repo in a local env file.

## Roadmap

* Prospective validation of the judge (blind ratings, target r >= 0.5).
* Add audio-event detection (laughter) as a second input to the scorecard.
* A/B harness for title and duration experiments using `data/results.csv`.
* Optional Kick and YouTube-live chat adapters (the Twitch JSON parser is the only source-specific piece).

## License

MIT. See [LICENSE](LICENSE).
