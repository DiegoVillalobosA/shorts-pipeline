import random
import unittest

from shorts_pipeline import chat_peaks as cp


def synthetic_chat(seed=1, duration=1800, spike_at=(600, 1300)):
    """Quiet chat (~1 msg / 2 s) with two obvious bursts and one spam burst."""
    rnd = random.Random(seed)
    comments = []
    for t in range(0, duration, 2):
        comments.append({"content_offset_seconds": t + rnd.random(),
                         "commenter": {"_id": f"u{rnd.randint(1, 200)}"},
                         "message": {"body": "hola"}})
    for centre in spike_at:
        for k in range(60):
            comments.append({"content_offset_seconds": centre + rnd.random() * 9,
                             "commenter": {"_id": f"v{k}"},
                             "message": {"body": "KEKW jajaja"}})
    for k in range(80):  # one account spamming
        comments.append({"content_offset_seconds": 1000 + rnd.random() * 9,
                         "commenter": {"_id": "bot"}, "message": {"body": "spam"}})
    comments.append({"content_offset_seconds": 100, "message": {"body": "X just gifted 5 subs"}})
    return comments


class ChatPeakTests(unittest.TestCase):
    def setUp(self):
        self.msgs, self.covered = cp.parse_chat(synthetic_chat())

    def test_system_messages_are_dropped(self):
        self.assertFalse(any("gifted" in m.text for m in self.msgs))

    def test_finds_both_bursts_and_ranks_them_first(self):
        peaks = cp.detect_peaks(self.msgs, self.covered, top=3)
        starts = {p.start_s // 100 * 100 for p in peaks}
        self.assertIn(600, starts)
        self.assertIn(1300, starts)

    def test_peaks_are_separated(self):
        peaks = cp.detect_peaks(self.msgs, self.covered, top=10, min_separation_s=60)
        starts = [p.start_s for p in peaks]
        self.assertTrue(all(b - a >= 60 for a, b in zip(starts, starts[1:])))

    def test_cut_starts_before_the_peak(self):
        p = cp.detect_peaks(self.msgs, self.covered, top=1)[0]
        self.assertEqual(p.cut_from_s, max(0, p.start_s - 20))

    def test_spam_is_flagged(self):
        peaks = cp.detect_peaks(self.msgs, self.covered, top=5)
        spam = [p for p in peaks if 990 <= p.start_s <= 1010]
        self.assertTrue(spam and all(cp.looks_like_spam(p) for p in spam))

    def test_quiet_chat_has_no_peaks(self):
        quiet = [{"content_offset_seconds": t, "message": {"body": "x"}} for t in range(0, 600, 2)]
        msgs, covered = cp.parse_chat(quiet)
        self.assertEqual(cp.detect_peaks(msgs, covered), [])


if __name__ == "__main__":
    unittest.main()
