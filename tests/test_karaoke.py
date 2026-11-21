import unittest

from shorts_pipeline.karaoke import Word, censor, group_lines, highlight_in_silence_ratio, to_ass

WORDS = [Word("no", 0.0, 0.3), Word("way", 0.35, 0.7), Word("that", 2.5, 2.8), Word("worked", 2.85, 3.4)]


class KaraokeTests(unittest.TestCase):
    def test_pause_splits_lines(self):
        lines = group_lines(WORDS)
        self.assertEqual([[w.text for w in l] for l in lines], [["no", "way"], ["that", "worked"]])

    def test_aligned_captions_have_no_silent_highlight(self):
        speech = [(0.0, 0.8), (2.4, 3.6)]
        self.assertLess(highlight_in_silence_ratio(WORDS, speech), 0.05)

    def test_naive_captions_are_caught(self):
        # same words, but the speech detector says the speaker only talked at the end
        self.assertGreater(highlight_in_silence_ratio(WORDS, [(2.4, 3.6)]), 0.3)

    def test_partial_censor_keeps_ends(self):
        self.assertEqual(censor("shit!", {"shit"}), "s**t!")
        self.assertEqual(censor("hello", {"shit"}), "hello")

    def test_ass_output(self):
        ass = to_ass(WORDS, strong={"worked"})
        self.assertIn("[Events]", ass)
        self.assertEqual(ass.count("Dialogue:"), 2)
        self.assertIn("w****d", ass)
        self.assertIn("\\kf", ass)


if __name__ == "__main__":
    unittest.main()
