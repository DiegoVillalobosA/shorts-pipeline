"""The "humor gate": a calibrated rubric that decides whether a moment is worth a Short.

Peak detectors measure *energy*, not *funniness*. On one real VOD the correlation
between detector signals and the owner's judgement was -0.34: music, applause and
cutscenes score high. So every candidate goes through this rubric first.

How it works
------------
An LLM (Claude) inspects extracted frames and the transcript of a candidate and
fills in a *scorecard*: eight criteria graded 0-2. This module turns the
scorecard into a 1-5 score and a routing decision. Keeping the arithmetic in
deterministic code (rather than asking the model for a number) makes the gate
auditable, testable and recalibratable from a handful of human ratings.

Criteria and weights were derived from ~40 ratings and "best of" clips supplied
by the channel owner; see docs/humor-judge.md for the patterns behind them.
"""
from __future__ import annotations

from dataclasses import dataclass, field, fields
from enum import Enum


class Decision(str, Enum):
    SOLO = "solo"                      # publish as a standalone Short
    TOP_OR_SOLO = "top_or_solo"        # good enough standalone, or a strong TOP entry
    TOP_LOW_SLOT = "top_low_slot"      # only as a lower slot in a compilation
    IMPROVE_EDIT = "improve_edit"      # borderline: try a tighter cut / better framing
    TOP_ONLY_BURNT = "top_only_burnt"  # already viral: never standalone, fine in a TOP
    DISCARD = "discard"


# criterion -> (weight, what it measures)
CRITERIA: dict[str, tuple[float, str]] = {
    "twist":    (3.0, "expectation vs. outcome: inverted promise, irony, dark humour"),
    "reaction": (3.0, "strong *visible* reaction (face, jump, scream) right at the punchline"),
    "clarity":  (3.0, "understood in under 3 s without knowing the game/sport/streamer"),
    "visual":   (2.0, "the payoff is *seen*, not audio-only or a menu/cutscene"),
    "quote":    (1.5, "quotable line, or on-screen text that underlines the joke"),
    "theme":    (1.5, "universal theme: family, embarrassment, money, exes, dark humour"),
    "ending":   (1.5, "clip ends right after the reaction: not cut short, not dragged"),
    "fresh":    (2.0, "2 = nobody posted it, 1 = a few copies, 0 = viral/burnt"),
}
VETOES = ("explicit", "hateful")  # any True -> discard, whatever the score


@dataclass
class Scorecard:
    id: str = ""
    twist: int = 0
    reaction: int = 0
    clarity: int = 0
    visual: int = 0
    quote: int = 0
    theme: int = 0
    ending: int = 0
    fresh: int = 1          # unknown freshness is treated as "a few copies"
    explicit: bool = False
    hateful: bool = False

    @classmethod
    def from_dict(cls, data: dict) -> "Scorecard":
        known = {f.name for f in fields(cls)}
        return cls(**{k: v for k, v in data.items() if k in known})


@dataclass
class Verdict:
    score: float
    decision: Decision
    reason: str
    weak: list[str] = field(default_factory=list)


def _clamp(v: int) -> int:
    return min(max(int(v), 0), 2)


def score(card: Scorecard) -> Verdict:
    vetoed = [v for v in VETOES if getattr(card, v)]
    if vetoed:
        return Verdict(1.0, Decision.DISCARD, "veto: " + ", ".join(vetoed))

    total = sum(w * _clamp(getattr(card, k)) for k, (w, _) in CRITERIA.items())
    best = sum(2 * w for w, _ in CRITERIA.values())
    value = round(1 + 4 * total / best, 1)
    weak = [k for k in CRITERIA if _clamp(getattr(card, k)) == 0]

    if _clamp(card.fresh) == 0:
        # Burnt moments are still good raw material for a compilation.
        decision = Decision.TOP_ONLY_BURNT if value >= 3.5 else Decision.DISCARD
        return Verdict(value, decision, "burnt: never standalone, may anchor a TOP", weak)

    standalone_ok = (
        value >= 4
        and _clamp(card.clarity) >= 1
        and (_clamp(card.reaction) >= 1 or _clamp(card.twist) == 2)
    )
    if value >= 4.5 and _clamp(card.fresh) == 2:
        decision = Decision.SOLO
    elif standalone_ok:
        decision = Decision.TOP_OR_SOLO
    elif value >= 3.5:
        decision = Decision.TOP_LOW_SLOT
    elif value >= 3:
        decision = Decision.IMPROVE_EDIT
    else:
        decision = Decision.DISCARD
    return Verdict(value, decision, "weak on: " + (", ".join(weak) or "nothing"), weak)


def correlation(xs: list[float], ys: list[float]) -> float:
    """Pearson r, used to recalibrate against the owner's ratings."""
    n = len(xs)
    if n < 2 or n != len(ys):
        raise ValueError("need two equally long series of length >= 2")
    mx, my = sum(xs) / n, sum(ys) / n
    sx = sum((x - mx) ** 2 for x in xs) ** 0.5
    sy = sum((y - my) ** 2 for y in ys) ** 0.5
    if sx == 0 or sy == 0:
        raise ValueError("a series has zero variance")
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (sx * sy)
