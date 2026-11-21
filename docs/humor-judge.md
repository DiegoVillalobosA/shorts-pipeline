# The humor gate

## Problem

A peak detector tells you where chat or audio spiked. It does not tell you
whether the moment is *funny*. Measured on one real VOD, the correlation between
the detector's signals and the owner's own judgement was **-0.34**: music,
applause, cutscenes and menus score high.

Running the detector on the launch-day VODs of a very hyped game produced 60
candidates and the gate passed **0**. The first instinct was "the threshold is
too strict". Looking at the frames showed the real cause: 24 reviewed
candidates were menus, cutscenes and loading screens. The fix was **change the
source, not the threshold**. That is exactly the kind of mistake a gate with
written reasons makes visible.

## The rubric

Eight criteria, each graded 0/1/2 by Claude from extracted frames plus the
transcript:

| Criterion | Weight | Measures |
|---|---|---|
| twist | 3.0 | expectation vs. outcome: inverted promise, irony, dark humour |
| reaction | 3.0 | strong visible reaction right at the punchline |
| clarity | 3.0 | understood in under 3 s with no prior context |
| visual | 2.0 | the payoff is seen, not audio-only / menu / cutscene |
| quote | 1.5 | quotable line or on-screen text underlining the joke |
| theme | 1.5 | universal theme: family, embarrassment, money, dark humour |
| ending | 1.5 | ends right after the reaction |
| fresh | 2.0 | nobody posted it yet; burnt moments are TOP-only |

`score = 1 + 4 * weighted_sum / max`, then routed to a decision
(`solo`, `top_or_solo`, `top_low_slot`, `improve_edit`, `top_only_burnt`,
`discard`). Vetoes (explicit, hateful) override everything.

## The five patterns found in the owner's favourite clips

1. Inverted promise / irony ("I drive so well" -> crash).
2. Awkward social or family situation with a live reaction.
3. Self-deprecation or a quotable line, underlined by 3-6 words on screen.
4. Dark humour / roasting between friends.
5. A game failure with commentary.

Common to all of them: understood in < 3 s, the reaction *is* the ending, and
you can see what happens.

## What it penalises

Cutting before the reaction, niche references, non-stream content, audio-only
gags, and novelty with no joke.

## Validation, honestly

The retrospective fit (see `examples/scorecards.json`) separates clips the
owner rated >= 4 from those rated <= 2.3. **That proves little**: the cards
were filled in knowing the ratings. The first prospective check was worse: the
judge predicted 4.6 for a clip the owner then rated about 3.5. The v0 judge is
optimistic, and a correlation of at least 0.5 against 15+ blind ratings is the
bar to trust it. Until then it is a *filter that removes the clearly bad*, not
an oracle.
