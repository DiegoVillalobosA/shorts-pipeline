"""Loudness-peak detection from a VOD's audio track.

Complements chat peaks when the chat replay is incomplete (old VODs) or when the
event is loud in the room (crowds, commentators shouting).

A window only counts when it is both loud relative to its *local* median and
loud in *absolute* terms; otherwise "coming out of silence" would look like a
peak.
"""
from __future__ import annotations

import re
import statistics
import subprocess
from dataclasses import dataclass
from typing import Sequence


def measure_levels(audio_path: str, window_s: float = 5.0) -> list[float]:
    """RMS level in dB per window, via ffmpeg's ``astats`` filter."""
    n = int(16000 * window_s)
    af = (
        f"aresample=16000,aformat=channel_layouts=mono,asetnsamples=n={n}:p=0,"
        "astats=metadata=1:reset=1,"
        "ametadata=print:key=lavfi.astats.Overall.RMS_level:file=-"
    )
    out = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", audio_path, "-vn", "-af", af, "-f", "null", "-"],
        capture_output=True, text=True, check=True,
    ).stdout
    levels = []
    for m in re.finditer(r"lavfi\.astats\.Overall\.RMS_level=(\S+)", out):
        v = m.group(1)
        levels.append(-90.0 if v in ("-inf", "inf", "nan") else max(-90.0, float(v)))
    return levels


@dataclass
class LoudPeak:
    start_s: float
    level_db: float
    db_over_local_median: float

    @property
    def amplitude_ratio(self) -> float:
        return round(10 ** (self.db_over_local_median / 20), 2)


def find_loud_peaks(
    levels_db: Sequence[float],
    window_s: float = 5.0,
    *,
    top: int = 8,
    min_separation_s: int = 90,
    baseline_s: int = 300,
    min_over_global_db: float = -3.0,
) -> list[LoudPeak]:
    if not levels_db:
        return []
    radius = max(1, int(baseline_s // window_s))
    global_median = statistics.median(levels_db)
    scores = []
    for i, level in enumerate(levels_db):
        local = statistics.median(levels_db[max(0, i - radius): i + radius + 1])
        strong = level > -60 and level >= global_median + min_over_global_db
        scores.append(level - local if strong else 0.0)

    chosen: list[int] = []
    for i in sorted(range(len(levels_db)), key=scores.__getitem__, reverse=True):
        if scores[i] <= 0 or len(chosen) >= top:
            break
        if all(abs(i - j) * window_s >= min_separation_s for j in chosen):
            chosen.append(i)
    return [
        LoudPeak(i * window_s, round(levels_db[i], 1), round(scores[i], 1))
        for i in sorted(chosen)
    ]
