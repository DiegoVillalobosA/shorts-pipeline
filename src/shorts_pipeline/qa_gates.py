"""Quality gates that run before a Short is handed to a human.

Two tiers, learned the hard way:

* BLOCKING gates stop the pipeline: something is objectively broken or breaks a
  hard rule (wrong size, too long, captions lit during silence...).
* WARNING gates only annotate. A study of 59 same-channel pairs (winner vs loser
  within +-7 days) showed these did *not* separate winners from losers, so
  blocking on them would just reject good clips. See docs/lessons.md.
"""
from __future__ import annotations

import json
import math
import re
import subprocess
from dataclasses import dataclass, field

EMOJI_END = re.compile(r"[\U0001F300-\U0001FAFF☀-➿]$")


class GateError(ValueError):
    """A blocking gate failed."""


@dataclass
class Report:
    blocking: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return not self.blocking


def probe(path: str) -> dict:
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_streams", "-show_format", "-of", "json", path],
        capture_output=True, check=True, timeout=30,
    ).stdout
    return json.loads(out)


def check_probe(data: dict, expected_duration: float, *,
                size: tuple[int, int] = (1080, 1920), max_len: float = 60.0) -> float:
    """Validate ffprobe output. Raises GateError; returns the duration."""
    streams = data.get("streams", [])
    video = [s for s in streams if s.get("codec_type") == "video"]
    if len(video) != 1 or (video[0].get("width"), video[0].get("height")) != size:
        raise GateError(f"expected exactly one {size[0]}x{size[1]} video stream")
    if not any(s.get("codec_type") == "audio" for s in streams):
        raise GateError("no audio stream")
    try:
        duration = float(data["format"]["duration"])
        container = data["format"]["format_name"].split(",")
    except (KeyError, ValueError, TypeError) as exc:
        raise GateError("ffprobe did not report format and duration") from exc
    if "mp4" not in container:
        raise GateError("not an MP4 container")
    if not math.isfinite(duration) or not 0 < duration <= max_len:
        raise GateError(f"duration must be in (0, {max_len:g}] s, got {duration:.2f}")
    if abs(duration - expected_duration) > 0.25:
        raise GateError(f"duration {duration:.2f}s does not match the cut ({expected_duration:.2f}s)")
    return duration


def check_youtube_title(title: str) -> list[str]:
    """26-45 characters, specific, ends in exactly one emoji."""
    problems = []
    if not 26 <= len(title) <= 45:
        problems.append(f"length {len(title)} outside 26-45")
    if not EMOJI_END.search(title):
        problems.append("must end with an emoji")
    if len(re.findall(r"[\U0001F300-\U0001FAFF☀-➿]", title)) != 1:
        problems.append("use exactly one emoji")
    if re.search(r"\b(MOMENT|THING|CLIP)\b", title, re.IGNORECASE):
        problems.append("too generic")
    return problems


def check_onscreen_title(title: str, *, max_chars: int = 40) -> list[str]:
    return [f"on-screen title is {len(title)} chars (max {max_chars})"] if len(title) > max_chars else []


def run_gates(*, probe_data: dict, expected_duration: float,
              silence_ratio: float, youtube_title: str, onscreen_title: str,
              first_frame_has_face: bool | None = None, cuts: int | None = None) -> Report:
    r = Report()
    try:
        check_probe(probe_data, expected_duration)
    except GateError as exc:
        r.blocking.append(str(exc))
    if silence_ratio >= 0.05:
        r.blocking.append(f"captions lit during silence: {silence_ratio:.1%} (limit 5%)")
    r.blocking += [f"YouTube title: {p}" for p in check_youtube_title(youtube_title)]
    r.blocking += check_onscreen_title(onscreen_title)
    if first_frame_has_face is False:
        r.warnings.append("no face in the first frame")
    if cuts is not None and cuts > 3:
        r.warnings.append(f"{cuts} cuts (> 3)")
    return r
