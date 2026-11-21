"""Chat-activity peak detection for Twitch VODs.

Input is the JSON produced by TwitchDownloader's ``chatdownload`` command. The
detector buckets messages into fixed windows, compares each window against a
*local* median baseline (so a loud stream does not drown out a quiet one), and
returns the strongest, well-separated peaks together with a suggested cut range.

Design notes
------------
* Chat reacts *after* the joke, so the cut starts well before the peak.
* System messages (subs, gifts, raids, cheers) are not audience reactions and are
  dropped before counting.
* Windows with fewer than ``min_messages`` messages never qualify: a jump from
  1 to 3 messages is noise, not a moment.
* Distinct chatters per window are reported so a spammer cannot fake a peak.
"""
from __future__ import annotations

import json
import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from typing import Iterable, Sequence

SYSTEM_MESSAGE = re.compile(
    r"(subscribed (with Prime|at Tier)|gifted a Tier|is gifting|gifted \d+|"
    r"just gifted|Gift Sub|^cheer\d+|raided)",
    re.IGNORECASE,
)


@dataclass(frozen=True)
class ChatMessage:
    t: float            # seconds from VOD start
    text: str
    user_id: str | None


@dataclass
class Peak:
    start_s: int
    messages: int
    distinct_users: int | None
    score: float
    cut_from_s: float
    cut_to_s: float
    baseline: float
    top_words: list[str] = field(default_factory=list)

    @property
    def timestamp(self) -> str:
        return hhmmss(self.start_s)

    def to_dict(self) -> dict:
        d = self.__dict__.copy()
        d["timestamp"] = self.timestamp
        return d


def hhmmss(seconds: float) -> str:
    s = int(max(0, seconds))
    return f"{s // 3600:d}:{s % 3600 // 60:02d}:{s % 60:02d}"


def load_chat(path: str) -> tuple[list[ChatMessage], float]:
    """Load a TwitchDownloader chat JSON. Returns (messages, covered_seconds)."""
    with open(path, encoding="utf-8") as fh:
        raw = json.load(fh)
    return parse_chat(raw.get("comments", []))


def parse_chat(comments: Iterable[dict]) -> tuple[list[ChatMessage], float]:
    out: list[ChatMessage] = []
    for c in comments:
        t = c.get("content_offset_seconds")
        if t is None:
            continue
        message = c.get("message", {})
        body = message.get("body", "") if isinstance(message, dict) else str(message)
        bits = message.get("bits_spent", 0) if isinstance(message, dict) else 0
        if SYSTEM_MESSAGE.search(body) or (bits or 0) > 0:
            continue
        author = c.get("commenter") or {}
        out.append(ChatMessage(float(t), body, author.get("_id") or author.get("id")))
    out.sort(key=lambda m: m.t)
    # Old VODs may have a chat replay shorter than the video itself, so the
    # *chat's* last timestamp, not the VOD length, bounds the analysis.
    covered = out[-1].t if out else 0.0
    return out, covered


def detect_peaks(
    messages: Sequence[ChatMessage],
    covered_s: float,
    *,
    window_s: int = 10,
    top: int = 10,
    min_separation_s: int = 60,
    baseline_radius_s: int = 300,
    lead_in_s: int = 20,
    tail_s: int = 10,
    min_messages: int = 5,
) -> list[Peak]:
    n = int(covered_s // window_s) + 1
    counts = [0] * n
    for m in messages:
        counts[min(int(m.t // window_s), n - 1)] += 1

    radius = max(1, baseline_radius_s // window_s)
    scores = []
    baselines = []
    for i, c in enumerate(counts):
        base = statistics.median(counts[max(0, i - radius): i + radius + 1])
        baselines.append(base)
        # (excess over baseline) / (baseline + 3): the +3 keeps quiet stretches
        # from producing enormous ratios out of two or three messages.
        scores.append((c - base) / (base + 3.0) if c >= min_messages else 0.0)

    chosen: list[int] = []
    for i in sorted(range(n), key=scores.__getitem__, reverse=True):
        if scores[i] <= 0 or len(chosen) >= top:
            break
        if all(abs(i - j) * window_s >= min_separation_s for j in chosen):
            chosen.append(i)

    peaks = []
    for i in sorted(chosen):
        t0, t1 = i * window_s, (i + 1) * window_s
        inside = [m for m in messages if t0 <= m.t < t1]
        words = Counter(
            w.lower() for m in inside for w in re.findall(r"\w+", m.text) if len(w) > 1
        )
        users = {m.user_id for m in inside if m.user_id}
        peaks.append(
            Peak(
                start_s=t0,
                messages=counts[i],
                distinct_users=len(users) if users else None,
                score=round(scores[i], 2),
                cut_from_s=max(0, t0 - lead_in_s),
                cut_to_s=min(covered_s, t1 + tail_s),
                baseline=baselines[i],
                top_words=[w for w, _ in words.most_common(6)],
            )
        )
    return peaks


def looks_like_spam(peak: Peak, *, min_users: int = 4, min_user_ratio: float = 0.25) -> bool:
    """Many messages from very few accounts is a bot or a copy-paste raid.

    A real reaction has roughly one message per chatter; a peak where distinct
    users are under a quarter of the message count is treated as suspicious.
    """
    if peak.distinct_users is None:
        return False
    return peak.distinct_users < max(min_users, min_user_ratio * peak.messages)
