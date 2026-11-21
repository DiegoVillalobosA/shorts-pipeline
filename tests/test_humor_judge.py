import json
import unittest
from pathlib import Path

from shorts_pipeline.humor_judge import Decision, Scorecard, correlation, score

EXAMPLES = Path(__file__).resolve().parent.parent / "examples" / "scorecards.json"


class JudgeTests(unittest.TestCase):
    def test_veto_beats_everything(self):
        card = Scorecard(twist=2, reaction=2, clarity=2, visual=2, quote=2, theme=2,
                         ending=2, fresh=2, explicit=True)
        v = score(card)
        self.assertEqual((v.score, v.decision), (1.0, Decision.DISCARD))

    def test_perfect_fresh_clip_is_solo(self):
        card = Scorecard(*[""], twist=2, reaction=2, clarity=2, visual=2, quote=2,
                         theme=2, ending=2, fresh=2)
        self.assertEqual(score(card).decision, Decision.SOLO)
        self.assertEqual(score(card).score, 5.0)

    def test_burnt_moment_never_standalone(self):
        card = Scorecard(twist=2, reaction=2, clarity=2, visual=2, quote=2, theme=1,
                         ending=1, fresh=0)
        self.assertEqual(score(card).decision, Decision.TOP_ONLY_BURNT)

    def test_audio_only_gag_scores_low(self):
        card = Scorecard(twist=1, reaction=1, ending=1)  # no clarity, no visual
        self.assertEqual(score(card).decision, Decision.DISCARD)

    def test_ratings_are_clamped(self):
        wild = Scorecard(twist=9, reaction=-4, clarity=2, visual=2, fresh=2)
        self.assertTrue(1.0 <= score(wild).score <= 5.0)

    def test_calibration_set_separates_good_from_bad(self):
        data = json.loads(EXAMPLES.read_text())
        good = [score(Scorecard.from_dict(c)).score for c in data["rated_high"]]
        bad = [score(Scorecard.from_dict(c)).score for c in data["rated_low"]]
        self.assertGreater(min(good), max(bad))

    def test_correlation(self):
        self.assertAlmostEqual(correlation([1, 2, 3], [2, 4, 6]), 1.0)
        with self.assertRaises(ValueError):
            correlation([1, 1, 1], [1, 2, 3])


if __name__ == "__main__":
    unittest.main()
