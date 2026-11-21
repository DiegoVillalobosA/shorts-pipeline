# Selected lessons (with provenance)

The full list is 55 items; these show how the system learns.

* **Detector != funny.** Peak signals correlate -0.34 with human judgement on one VOD. -> humor gate. `[MEASURED]`
* **0 of 60 was the source, not the threshold.** Launch-day VODs are menus and cutscenes. Change the source. `[MEASURED]`
* **Karaoke must follow the voice.** The first cut had 35 % of highlight time in silence; the adaptive version had 0/130 words. -> blocking gate < 5 %. `[MEASURED]`
* **Views of a source clip are not a signal.** A 142k-view community clip got 1/5: audio-only gag, no visual payoff. `[OWNER]`
* **Show how it happens.** A "chair breaks" clip rated ~3.5: the viewer needs the setup, a physical payoff at the end, and no duplicated face when the camera is already full screen. `[OWNER]`
* **Menus: show the whole screen.** When the joke lives in a menu, use the wide layout (whole screen over blurred backdrop), never a portrait crop. `[OWNER]`
* **Burnt moments are TOP material.** A famous clip is never a standalone Short but is a good TOP entry; mediocre clips take the low slots. `[OWNER]`
* **Fewer sounds beat wrong sounds.** Every meme sound has a moment; if none fits, place none. `[OWNER]`
* **Duration is a hypothesis, not a rule.** Across 59 same-channel pairs the winner was longer in 38, but winners also carry more content; A/B it. `[MEASURED]`
* **Cuts, volume, first-frame face don't separate winners from losers**, so they warn instead of block. `[MEASURED]`
* **Chat reacts to the joke, not the action** and lags 2-8 s: start 6-8 s before the event, end <= 3 s after the reaction. `[HYPOTHESIS]`
* **Check chat coverage.** A chat replay can cover 1h24 of a 5h39 VOD; sub/gift notices also distort peaks. `[MEASURED]`
* **Whisper timestamps drift 0.5-1.5 s** between runs; confirm ends with audio energy. `[MEASURED]`
* **Downloads of the same VOD in parallel corrupt each other.** Serialise per VOD. `[MEASURED]`
