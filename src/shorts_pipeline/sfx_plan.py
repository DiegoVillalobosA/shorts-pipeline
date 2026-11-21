"""Sound-effect placement: fewer, better, never off-topic.

Rules distilled from the owner's feedback:
* Each meme sound has a *moment* it belongs to (a tender "wow" does not belong on
  a crash). If nothing fits an event, place nothing there.
* Effects sit at least 2 s apart, after the end of a phrase, never on top of it.
* A ~35 s clip gets 4-6 effects; shorter clips proportionally fewer.
"""
from __future__ import annotations

from dataclasses import dataclass

MIN_GAP_S = 2.0

# event kind -> sound that fits it (None = leave silent). Names are the
# channel's own library; swap for yours.
SOUND_FOR_EVENT = {
    "title":        "ding",
    "reveal":       "reveal",
    "cute":         "wow",
    "impact":       "explosion",
    "awkward":      "awkward-silence",
    "punchline":    "faaah",       # the all-purpose closer
    "fail":         "fail-trombone",
    "flirt":        "rizz",
    "death":        "bell",
    "other":        None,
}


@dataclass(frozen=True)
class Event:
    t: float
    kind: str


@dataclass(frozen=True)
class Placement:
    t: float
    sound: str


def target_count(duration_s: float) -> tuple[int, int]:
    """Allowed (min, max) number of effects for a clip of this length."""
    if duration_s < 20:
        return 0, 3
    if duration_s <= 45:
        return 4, 6
    return 4, 8


def plan(events: list[Event], duration_s: float) -> list[Placement]:
    """Turn detected events into placements honouring spacing and the cap."""
    _, cap = target_count(duration_s)
    placed: list[Placement] = []
    for ev in sorted(events, key=lambda e: e.t):
        sound = SOUND_FOR_EVENT.get(ev.kind)
        if sound is None or not 0 <= ev.t < duration_s:
            continue
        if placed and ev.t - placed[-1].t < MIN_GAP_S:
            continue
        placed.append(Placement(round(ev.t, 2), sound))
        if len(placed) == cap:
            break
    return placed
